"""V06A2: grow a generic_5r fixed-position parent atlas and audit components.

A multi-chart atlas from one seed is not a complete parent. Component discovery
uses a deterministic Sobol bank and damped minimum-normal projection. Fibers
and closed-mechanism children are not emitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite, pi
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.stats.qmc import Sobol

from .fixed_position import (
    JACOBIAN_FD_ERROR_TOL,
    JACOBIAN_FD_STEP_RAD,
    POSITION_RESIDUAL_TOL_M,
)
from .implicit_manifold import (
    ChartOverlapRecord,
    ChartRecord,
    ambient_distance,
    build_hexagonal_chart,
    orthonormal_tangent_basis,
    projector_frobenius,
)
from .jacobians import central_difference_jacobians, matrix_rank_report, position_jacobian
from .parent_local import (
    LOCAL_CHART_RADIUS_RAD,
    FixedPositionParentProblem,
    ParentRepresentationStatus,
    ParentVertexDiagnostics,
    _vertex_diagnostics,
)
from .v06_corpus import Spatial5RCorpusEntry, build_generic_5r

Array = NDArray[np.floating]

DEFAULT_MAX_CHARTS = 10
MIN_CHART_RADIUS_RAD = 0.06
ATTACH_RADIUS_FACTOR = 2.2
DISCOVERY_BANK = 32
CONFIRM_BANK = 64
PROJECTION_ITERS = 25
PROJECTION_LAMBDA = 1e-6
PROJECTION_TOL_M = 1e-8


class ComponentDiscoveryStatus(str, Enum):
    """How completely extra components were searched. Not a certificate."""

    ONE_SEED_ONLY = "ONE_SEED_ONLY"
    MULTISTART_STABLE_AT_DECLARED_RESOLUTION = "MULTISTART_STABLE_AT_DECLARED_RESOLUTION"
    NEW_COMPONENT_FOUND_ON_CONFIRMATION = "NEW_COMPONENT_FOUND_ON_CONFIRMATION"
    UNRESOLVED_COMPONENT_DISCOVERY = "UNRESOLVED_COMPONENT_DISCOVERY"


class FrontierKind(str, Enum):
    OPEN = "OPEN"
    SINGULAR = "SINGULAR"
    BUDGET_LIMITED = "BUDGET_LIMITED"


@dataclass(frozen=True, slots=True)
class FrontierRecord:
    kind: FrontierKind
    chart_id: str | None
    q: tuple[float, ...] | None
    reason: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "chart_id": self.chart_id,
            "q": None if self.q is None else list(self.q),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ComponentDiscoveryRecord:
    status: ComponentDiscoveryStatus
    bank_id: str
    bank_size: int
    confirmation_bank_size: int
    projected_seed_count: int
    unattached_seed_count: int
    component_count: int
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "bank_id": self.bank_id,
            "bank_size": self.bank_size,
            "confirmation_bank_size": self.confirmation_bank_size,
            "projected_seed_count": self.projected_seed_count,
            "unattached_seed_count": self.unattached_seed_count,
            "component_count": self.component_count,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class ParentAtlasResult:
    """Multi-chart source-parent atlas. Not a DecompositionCertificate."""

    architecture_id: str
    p_star: tuple[float, float, float]
    representation_status: ParentRepresentationStatus
    component_ids: tuple[str, ...]
    fiber_ids: tuple[str, ...]
    charts: tuple[ChartRecord, ...]
    overlaps: tuple[ChartOverlapRecord, ...]
    vertices: tuple[ParentVertexDiagnostics, ...]
    frontiers: tuple[FrontierRecord, ...]
    discovery: ComponentDiscoveryRecord
    declared_chart_radius: float
    joint_limits: str
    seed_q: tuple[float, ...]
    seed_fd_jp_error: float
    seed_fd_verified: bool
    max_p_residual_m: float | None
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_safe({
            "architecture_id": self.architecture_id,
            "p_star": list(self.p_star),
            "representation_status": self.representation_status.value,
            "certificate_status": None,
            "component_ids": list(self.component_ids),
            "fiber_ids": list(self.fiber_ids),
            "charts": [chart.to_json_dict() for chart in self.charts],
            "overlaps": [item.to_json_dict() for item in self.overlaps],
            "vertices": [v.to_json_dict() for v in self.vertices],
            "frontiers": [item.to_json_dict() for item in self.frontiers],
            "discovery": self.discovery.to_json_dict(),
            "declared_chart_radius": self.declared_chart_radius,
            "joint_limits": self.joint_limits,
            "seed_q": list(self.seed_q),
            "seed_fd_jp_error": self.seed_fd_jp_error,
            "seed_fd_verified": self.seed_fd_verified,
            "max_p_residual_m": self.max_p_residual_m,
            "notes": list(self.notes),
        })


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: _json_safe(val) for key, val in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(val) for val in obj]
    if isinstance(obj, float) and not isfinite(obj):
        return None
    return obj


def wrap_periodic(x: Array, periodic: tuple[bool, ...]) -> Array:
    y = np.asarray(x, dtype=float).reshape(-1).copy()
    for i, flag in enumerate(periodic):
        if flag:
            y[i] = float(((y[i] + pi) % (2.0 * pi)) - pi)
    return y


def _ring_vertices(chart: ChartRecord) -> list[Array]:
    pts: list[Array] = []
    for sample in chart.samples:
        if sample.local_index == 0:
            continue
        if sample.correction.accepted and sample.correction.x is not None:
            pts.append(np.asarray(sample.correction.x, dtype=float))
    return pts


def _adaptive_radius(chart: ChartRecord, base: float) -> float:
    conds = [
        s.correction.condition_number
        for s in chart.samples
        if s.correction.condition_number is not None
    ]
    corr = [s.correction.correction_norm for s in chart.samples if s.correction.accepted]
    radius = base
    if conds and max(conds) > 1e8:
        radius *= 0.7
    if corr and max(corr) > 0.5 * base:
        radius *= 0.8
    return max(MIN_CHART_RADIUS_RAD, float(radius))


def _try_chart(
    problem: FixedPositionParentProblem,
    seed: Array,
    *,
    chart_id: str,
    radius: float,
    n_ref: Array | None,
) -> ChartRecord:
    r = radius
    try:
        last = build_hexagonal_chart(
            problem, seed, chart_id=chart_id, radius=r, n_rings=1, n_ref=n_ref
        )
    except ValueError as exc:
        return ChartRecord(
            chart_id=chart_id,
            center=tuple(float(v) for v in np.asarray(seed, dtype=float)),
            tangent_basis=(),
            radius=r,
            samples=(),
            triangles=(),
            accepted=False,
            notes=(f"chart construction failed: {exc}",),
        )
    for _ in range(2):
        if last.accepted:
            return last
        r = max(MIN_CHART_RADIUS_RAD, 0.6 * r)
        try:
            last = build_hexagonal_chart(
                problem, seed, chart_id=chart_id, radius=r, n_rings=1, n_ref=n_ref
            )
        except ValueError as exc:
            return ChartRecord(
                chart_id=chart_id,
                center=tuple(float(v) for v in np.asarray(seed, dtype=float)),
                tangent_basis=(),
                radius=r,
                samples=(),
                triangles=(),
                accepted=False,
                notes=(f"chart construction failed: {exc}",),
            )
    return last


def _is_duplicate(
    problem: FixedPositionParentProblem,
    center: Array,
    n_new: Array,
    charts: list[ChartRecord],
    dup_tol: float,
) -> bool:
    periodic = problem.periodic_coordinates
    for chart in charts:
        d = ambient_distance(center, np.asarray(chart.center), periodic)
        if d > dup_tol:
            continue
        n_old = np.asarray(chart.tangent_basis, dtype=float).T
        if projector_frobenius(n_old, n_new) < 0.35:
            return True
        if d <= 0.35 * dup_tol:
            return True
    return False


def _chart_adjacency(
    problem: FixedPositionParentProblem,
    charts: tuple[ChartRecord, ...],
    overlap_tol: float,
) -> tuple[ChartOverlapRecord, ...]:
    recs: list[ChartOverlapRecord] = []
    periodic = problem.periodic_coordinates
    for i, a in enumerate(charts):
        for b in charts[i + 1 :]:
            d = ambient_distance(np.asarray(a.center), np.asarray(b.center), periodic)
            pts_a = a.accepted_points()
            pts_b = b.accepted_points()
            count = 0
            max_d: float | None = None
            for pa in pts_a:
                for pb in pts_b:
                    dist = ambient_distance(pa, pb, periodic)
                    if dist <= overlap_tol:
                        count += 1
                        max_d = dist if max_d is None else max(max_d, dist)
            if count > 0:
                recs.append(
                    ChartOverlapRecord(
                        chart_a=a.chart_id,
                        chart_b=b.chart_id,
                        max_center_distance=d,
                        overlapping_sample_count=count,
                        max_sample_distance=max_d,
                        duplicate_rejected=False,
                    )
                )
    recs.sort(key=lambda r: (r.chart_a, r.chart_b))
    return tuple(recs)


def project_to_parent(
    problem: FixedPositionParentProblem,
    q: Array,
    *,
    lam: float = PROJECTION_LAMBDA,
    max_iters: int = PROJECTION_ITERS,
    tol_m: float = PROJECTION_TOL_M,
) -> tuple[Array, bool]:
    """Damped minimum-normal step onto ``p(q)=p*``."""

    x = np.asarray(q, dtype=float).reshape(-1).copy()
    eye = np.eye(problem.constraint_dimension)
    for _ in range(max_iters):
        r = problem.residual(x)
        if float(np.linalg.norm(r)) <= tol_m:
            return x, True
        jac = problem.jacobian(x)
        gram = jac @ jac.T + lam * eye
        try:
            y = np.linalg.solve(gram, r)
        except np.linalg.LinAlgError:
            return x, False
        x = wrap_periodic(x - jac.T @ y, problem.periodic_coordinates)
    return x, float(np.linalg.norm(problem.residual(x))) <= tol_m


def _sobol_bank(n: int, dim: int, *, seed: int) -> Array:
    engine = Sobol(d=dim, scramble=False, seed=seed)
    u = engine.random(n)
    return (u * (2.0 * pi)) - pi


def _grow_charts(
    problem: FixedPositionParentProblem,
    seed: Array,
    *,
    radius: float,
    max_charts: int,
) -> tuple[list[ChartRecord], list[FrontierRecord], bool]:
    dup_tol = 0.7 * radius
    charts: list[ChartRecord] = []
    frontiers: list[FrontierRecord] = []
    seed_chart = _try_chart(
        problem, seed, chart_id="chart_000", radius=radius, n_ref=None
    )
    if not seed_chart.accepted:
        frontiers.append(
            FrontierRecord(
                FrontierKind.OPEN,
                seed_chart.chart_id,
                tuple(float(v) for v in seed),
                "seed chart rejected after radius shrinks",
            )
        )
        return charts, frontiers, False
    charts.append(seed_chart)
    radius_now = _adaptive_radius(seed_chart, radius)
    frontier = _ring_vertices(seed_chart)
    budget_hit = False
    while frontier:
        if len(charts) >= max_charts:
            budget_hit = True
            for p in frontier:
                frontiers.append(
                    FrontierRecord(
                        FrontierKind.BUDGET_LIMITED,
                        None,
                        tuple(float(v) for v in p),
                        f"max_charts={max_charts}",
                    )
                )
            break
        centers = [np.asarray(c.center, dtype=float) for c in charts]

        def _min_d(p: Array) -> float:
            return min(ambient_distance(p, c, problem.periodic_coordinates) for c in centers)

        frontier.sort(key=_min_d)
        candidate = frontier.pop()
        n_prev = np.asarray(charts[-1].tangent_basis, dtype=float).T
        try:
            n_cand = orthonormal_tangent_basis(
                problem.jacobian(candidate), expected_nullity=2
            )
        except ValueError:
            frontiers.append(
                FrontierRecord(
                    FrontierKind.SINGULAR,
                    None,
                    tuple(float(v) for v in candidate),
                    "tangent basis missing expected nullity 2",
                )
            )
            continue
        if _is_duplicate(problem, candidate, n_cand, charts, dup_tol):
            continue
        chart = _try_chart(
            problem,
            candidate,
            chart_id=f"chart_{len(charts):03d}",
            radius=radius_now,
            n_ref=n_prev,
        )
        if not chart.accepted:
            report = matrix_rank_report(problem.jacobian(candidate))
            kind = FrontierKind.SINGULAR if report.rank < 3 else FrontierKind.OPEN
            frontiers.append(
                FrontierRecord(
                    kind,
                    chart.chart_id,
                    tuple(float(v) for v in candidate),
                    chart.notes[0] if chart.notes else "chart rejected",
                )
            )
            continue
        if _is_duplicate(problem, np.asarray(chart.center), n_cand, charts, dup_tol):
            continue
        charts.append(chart)
        radius_now = _adaptive_radius(chart, radius)
        frontier.extend(_ring_vertices(chart))
        centers = [np.asarray(c.center, dtype=float) for c in charts]
        kept: list[Array] = []
        for p in frontier:
            if _min_d(p) <= dup_tol:
                continue
            kept.append(p)
        frontier = kept
    return charts, frontiers, budget_hit


def _discover_components(
    problem: FixedPositionParentProblem,
    charts: list[ChartRecord],
    *,
    attach_tol: float,
    discovery_bank: int,
    confirmation_bank: int,
    budget_limited: bool,
) -> ComponentDiscoveryRecord:
    dim = problem.ambient_dimension
    primary = _sobol_bank(discovery_bank, dim, seed=1)
    confirm = _sobol_bank(confirmation_bank, dim, seed=2)
    centers = [np.asarray(c.center, dtype=float) for c in charts]

    def _attach_count(bank: Array) -> tuple[int, int]:
        ok = 0
        far = 0
        for row in bank:
            q_hat, success = project_to_parent(problem, row)
            if not success:
                continue
            ok += 1
            q_hat = wrap_periodic(q_hat, problem.periodic_coordinates)
            if not centers:
                far += 1
                continue
            dmin = min(
                ambient_distance(q_hat, c, problem.periodic_coordinates) for c in centers
            )
            if dmin > attach_tol:
                far += 1
        return ok, far

    p0, u0 = _attach_count(primary)
    p1, u1 = _attach_count(confirm)
    projected = p0 + p1
    unattached = u0 + u1
    if unattached > 0 and budget_limited:
        status = ComponentDiscoveryStatus.UNRESOLVED_COMPONENT_DISCOVERY
    elif u1 > 0:
        status = ComponentDiscoveryStatus.NEW_COMPONENT_FOUND_ON_CONFIRMATION
    elif u0 > 0:
        status = ComponentDiscoveryStatus.UNRESOLVED_COMPONENT_DISCOVERY
    elif projected > 0:
        status = ComponentDiscoveryStatus.MULTISTART_STABLE_AT_DECLARED_RESOLUTION
    else:
        status = ComponentDiscoveryStatus.ONE_SEED_ONLY
    notes = (
        "Sobol banks projected by damped minimum-normal steps.",
        "Unattached projections are not grown into additional atlases in V06A2.",
        "Unattached seeds on a budget-limited atlas are not proven extra components.",
        "Even MULTISTART_STABLE_AT_DECLARED_RESOLUTION is not a closed parent component.",
    )
    return ComponentDiscoveryRecord(
        status=status,
        bank_id="sobol_unscrambled_seed1_seed2",
        bank_size=discovery_bank,
        confirmation_bank_size=confirmation_bank,
        projected_seed_count=projected,
        unattached_seed_count=unattached,
        component_count=1 if charts else 0,
        notes=notes,
    )


def build_generic_5r_parent_atlas(
    entry: Spatial5RCorpusEntry | None = None,
    *,
    radius: float = LOCAL_CHART_RADIUS_RAD,
    max_charts: int = DEFAULT_MAX_CHARTS,
    discovery_bank: int = DISCOVERY_BANK,
    confirmation_bank: int = CONFIRM_BANK,
) -> ParentAtlasResult:
    corpus = entry or build_generic_5r()
    model = corpus.model
    q0 = corpus.regular_q
    problem = FixedPositionParentProblem.from_model(model, q0)
    jp0 = position_jacobian(model.chain, q0)
    jp_fd, _jd = central_difference_jacobians(model.chain, q0, JACOBIAN_FD_STEP_RAD)
    fd_error = float(np.linalg.norm(jp0 - jp_fd, ord="fro"))
    fd_ok = fd_error <= JACOBIAN_FD_ERROR_TOL

    charts, frontiers, budget_hit = _grow_charts(
        problem, np.asarray(q0, dtype=float), radius=radius, max_charts=max_charts
    )
    overlaps = _chart_adjacency(problem, tuple(charts), overlap_tol=1.2 * radius)
    vertices: list[ParentVertexDiagnostics] = []
    for chart in charts:
        for sample in chart.samples:
            if sample.correction.x is None:
                continue
            vertices.append(
                _vertex_diagnostics(
                    problem,
                    np.asarray(sample.correction.x, dtype=float),
                    sample.u,
                    condition_number=sample.correction.condition_number,
                    accepted=sample.correction.accepted,
                    rejection_reason=sample.correction.rejection_reason,
                )
            )
            if vertices[-1].rank_jp < 3:
                frontiers.append(
                    FrontierRecord(
                        FrontierKind.SINGULAR,
                        chart.chart_id,
                        vertices[-1].q,
                        "rank(Jp)<3 at accepted chart vertex",
                    )
                )

    discovery = _discover_components(
        problem,
        charts,
        attach_tol=ATTACH_RADIUS_FACTOR * radius,
        discovery_bank=discovery_bank,
        confirmation_bank=confirmation_bank,
        budget_limited=budget_hit,
    )
    accepted_res = [v.p_residual_m for v in vertices if v.accepted and v.p_residual_m is not None]
    open_n = sum(1 for f in frontiers if f.kind is FrontierKind.OPEN)
    sing_n = sum(1 for f in frontiers if f.kind is FrontierKind.SINGULAR)
    budg_n = sum(1 for f in frontiers if f.kind is FrontierKind.BUDGET_LIMITED)

    if not charts:
        status = ParentRepresentationStatus.REJECTED
        component_ids: tuple[str, ...] = ()
    elif budget_hit or budg_n:
        status = ParentRepresentationStatus.BUDGET_LIMITED
        component_ids = (f"{model.architecture_id}_component_seed0",)
    elif discovery.unattached_seed_count > 0:
        status = ParentRepresentationStatus.MULTICOMPONENT_UNRESOLVED
        component_ids = (f"{model.architecture_id}_component_seed0",)
    elif sing_n and not open_n:
        status = ParentRepresentationStatus.SINGULAR_BOUNDARY
        component_ids = (f"{model.architecture_id}_component_seed0",)
    elif len(charts) == 1:
        status = ParentRepresentationStatus.LOCAL_PATCH
        component_ids = ()
    else:
        status = ParentRepresentationStatus.ATLAS_OPEN_FRONTIER
        component_ids = (f"{model.architecture_id}_component_seed0",)

    return ParentAtlasResult(
        architecture_id=model.architecture_id,
        p_star=problem.p_star,
        representation_status=status,
        component_ids=component_ids,
        fiber_ids=(),
        charts=tuple(charts),
        overlaps=overlaps,
        vertices=tuple(vertices),
        frontiers=tuple(frontiers),
        discovery=discovery,
        declared_chart_radius=radius,
        joint_limits="not_modeled",
        seed_q=tuple(float(v) for v in q0),
        seed_fd_jp_error=fd_error,
        seed_fd_verified=fd_ok,
        max_p_residual_m=max(accepted_res) if accepted_res else None,
        notes=(
            "V06A2 parent atlas grown from one regular generic_5r seed.",
            f"open_frontiers={open_n}; singular={sing_n}; budget_limited={budg_n}.",
            f"discovery={discovery.status.value}; projected={discovery.projected_seed_count}.",
            "Not a complete parent, not S^2 coverage, not a DecompositionCertificate.",
            "No fibers or closed-mechanism children are emitted.",
        ),
    )


def parent_atlas_summary(result: ParentAtlasResult) -> dict[str, Any]:
    return {
        "architecture_id": result.architecture_id,
        "representation_status": result.representation_status.value,
        "chart_count": len(result.charts),
        "component_ids": list(result.component_ids),
        "fiber_ids": list(result.fiber_ids),
        "discovery_status": result.discovery.status.value,
        "open_frontier_count": sum(1 for f in result.frontiers if f.kind is FrontierKind.OPEN),
        "singular_frontier_count": sum(
            1 for f in result.frontiers if f.kind is FrontierKind.SINGULAR
        ),
        "budget_limited_frontier_count": sum(
            1 for f in result.frontiers if f.kind is FrontierKind.BUDGET_LIMITED
        ),
        "unattached_seed_count": result.discovery.unattached_seed_count,
        "max_p_residual_m": result.max_p_residual_m,
        "joint_limits": result.joint_limits,
    }
