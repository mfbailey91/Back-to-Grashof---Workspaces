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
CLUSTER_RADIUS_FACTOR = 1.5
VERTEX_DEDUP_FACTOR = 0.25
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
    CHART_SEAM = "CHART_SEAM"


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
class StitchedVertex:
    vertex_id: int
    q: tuple[float, ...]
    chart_ids: tuple[str, ...]
    on_chart_ring: bool
    global_frontier: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "vertex_id": self.vertex_id,
            "q": list(self.q),
            "chart_ids": list(self.chart_ids),
            "on_chart_ring": self.on_chart_ring,
            "global_frontier": self.global_frontier,
        }


@dataclass(frozen=True, slots=True)
class StitchedParentMesh:
    """Globally deduplicated vertices and faces. Not a closed parent."""

    vertices: tuple[StitchedVertex, ...]
    faces: tuple[tuple[int, int, int], ...]
    chart_seam_count: int
    global_frontier_count: int
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "vertex_count": len(self.vertices),
            "face_count": len(self.faces),
            "chart_seam_count": self.chart_seam_count,
            "global_frontier_count": self.global_frontier_count,
            "vertices": [v.to_json_dict() for v in self.vertices],
            "faces": [list(f) for f in self.faces],
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
    stitch: StitchedParentMesh | None
    chart_components: tuple[tuple[str, str], ...]
    declared_chart_radius: float
    joint_limits: str
    seed_q: tuple[float, ...]
    seed_fd_jp_error: float
    seed_fd_verified: bool
    max_p_residual_m: float | None
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_object({
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
            "stitch": None if self.stitch is None else self.stitch.to_json_dict(),
            "chart_components": [list(pair) for pair in self.chart_components],
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


def _json_object(obj: dict[str, Any]) -> dict[str, Any]:
    payload = _json_safe(obj)
    if not isinstance(payload, dict):
        raise TypeError("expected a JSON object")
    return payload


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


def _union_find_components(chart_ids: tuple[str, ...], overlaps: tuple[ChartOverlapRecord, ...]) -> list[list[str]]:
    parent = {cid: cid for cid in chart_ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for rec in overlaps:
        if rec.chart_a not in parent or rec.chart_b not in parent:
            continue
        ra, rb = find(rec.chart_a), find(rec.chart_b)
        if ra != rb:
            parent[rb] = ra
    groups: dict[str, list[str]] = {}
    for cid in chart_ids:
        groups.setdefault(find(cid), []).append(cid)
    return [groups[k] for k in sorted(groups)]


def _cluster_projected(
    qs: list[Array],
    periodic: tuple[bool, ...],
    radius: float,
) -> list[Array]:
    reps: list[Array] = []
    for q in qs:
        if any(ambient_distance(q, r, periodic) <= radius for r in reps):
            continue
        reps.append(q)
    return reps


def _collect_unattached(
    problem: FixedPositionParentProblem,
    charts: list[ChartRecord],
    banks: tuple[Array, ...],
    attach_tol: float,
) -> tuple[int, list[Array]]:
    centers = [np.asarray(c.center, dtype=float) for c in charts]
    projected = 0
    far: list[Array] = []
    for bank in banks:
        for row in bank:
            q_hat, success = project_to_parent(problem, row)
            if not success:
                continue
            projected += 1
            q_hat = wrap_periodic(q_hat, problem.periodic_coordinates)
            if not centers:
                far.append(q_hat)
                continue
            dmin = min(ambient_distance(q_hat, c, problem.periodic_coordinates) for c in centers)
            if dmin > attach_tol:
                far.append(q_hat)
    return projected, far


def stitch_parent_mesh(
    problem: FixedPositionParentProblem,
    charts: tuple[ChartRecord, ...],
    *,
    radius: float,
) -> StitchedParentMesh:
    periodic = problem.periodic_coordinates
    dedup = VERTEX_DEDUP_FACTOR * radius
    qs: list[Array] = []
    chart_ids: list[set[str]] = []
    ring_flags: list[bool] = []
    local_to_global: dict[tuple[str, int], int] = {}

    def _find(q: Array) -> int | None:
        for i, existing in enumerate(qs):
            if ambient_distance(q, existing, periodic) <= dedup:
                return i
        return None

    for chart in charts:
        for sample in chart.samples:
            if not sample.correction.accepted or sample.correction.x is None:
                continue
            q = np.asarray(sample.correction.x, dtype=float)
            idx = _find(q)
            on_ring = sample.local_index != 0
            if idx is None:
                local_to_global[(chart.chart_id, sample.local_index)] = len(qs)
                qs.append(q)
                chart_ids.append({chart.chart_id})
                ring_flags.append(on_ring)
            else:
                local_to_global[(chart.chart_id, sample.local_index)] = idx
                chart_ids[idx].add(chart.chart_id)
                ring_flags[idx] = ring_flags[idx] or on_ring

    vertices: list[StitchedVertex] = []
    seam = 0
    frontier = 0
    for i, q in enumerate(qs):
        multi = len(chart_ids[i]) > 1
        global_front = ring_flags[i] and not multi
        if ring_flags[i] and multi:
            seam += 1
        if global_front:
            frontier += 1
        vertices.append(
            StitchedVertex(
                vertex_id=i,
                q=tuple(float(v) for v in q),
                chart_ids=tuple(sorted(chart_ids[i])),
                on_chart_ring=ring_flags[i],
                global_frontier=global_front,
            )
        )
    faces: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for chart in charts:
        for face in chart.triangles:
            ids = []
            skip = False
            for loc in face:
                gid = local_to_global.get((chart.chart_id, loc))
                if gid is None:
                    skip = True
                    break
                ids.append(gid)
            if skip or len(set(ids)) < 3:
                continue
            ordered = tuple(sorted(ids))
            key = (ordered[0], ordered[1], ordered[2])
            if key in seen:
                continue
            seen.add(key)
            faces.append((ids[0], ids[1], ids[2]))
    return StitchedParentMesh(
        vertices=tuple(vertices),
        faces=tuple(faces),
        chart_seam_count=seam,
        global_frontier_count=frontier,
        notes=(
            "Vertices merged in wrapped joint space; chart-ring ≠ global frontier.",
            "Stitched mesh is not a closed parent component (ADR-046).",
        ),
    )


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
    scaled = (u * (2.0 * pi)) - pi
    return np.asarray(scaled, dtype=float)


def _grow_charts(
    problem: FixedPositionParentProblem,
    seed: Array,
    *,
    radius: float,
    max_charts: int,
    existing: list[ChartRecord] | None = None,
) -> tuple[list[ChartRecord], list[FrontierRecord], bool]:
    dup_tol = 0.7 * radius
    charts: list[ChartRecord] = list(existing or [])
    frontiers: list[FrontierRecord] = []
    if len(charts) >= max_charts:
        return charts, frontiers, True
    start_n = len(charts)
    seed_chart = _try_chart(
        problem, seed, chart_id=f"chart_{start_n:03d}", radius=radius, n_ref=None
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
    try:
        n_seed = orthonormal_tangent_basis(problem.jacobian(seed), expected_nullity=2)
    except ValueError:
        n_seed = np.eye(problem.ambient_dimension)[:, :2]
    if charts and _is_duplicate(problem, np.asarray(seed_chart.center), n_seed, charts, dup_tol):
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
        centers = tuple(np.asarray(c.center, dtype=float) for c in charts)

        def _min_d(p: Array, _centers: tuple[Array, ...] = centers) -> float:
            return min(ambient_distance(p, c, problem.periodic_coordinates) for c in _centers)

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
        centers = tuple(np.asarray(c.center, dtype=float) for c in charts)
        kept: list[Array] = []
        for p in frontier:
            if _min_d(p, centers) <= dup_tol:
                continue
            kept.append(p)
        frontier = kept
    return charts, frontiers, budget_hit


def _discover_components(
    *,
    discovery_bank: int,
    confirmation_bank: int,
    budget_limited: bool,
    grown_extra: int,
    remaining_unattached: int,
    projected: int,
    component_count: int,
) -> ComponentDiscoveryRecord:
    if remaining_unattached > 0 and budget_limited:
        status = ComponentDiscoveryStatus.UNRESOLVED_COMPONENT_DISCOVERY
    elif remaining_unattached > 0 and grown_extra == 0:
        status = ComponentDiscoveryStatus.NEW_COMPONENT_FOUND_ON_CONFIRMATION
    elif remaining_unattached > 0:
        status = ComponentDiscoveryStatus.UNRESOLVED_COMPONENT_DISCOVERY
    elif grown_extra > 0:
        status = ComponentDiscoveryStatus.NEW_COMPONENT_FOUND_ON_CONFIRMATION
    elif projected > 0:
        status = ComponentDiscoveryStatus.MULTISTART_STABLE_AT_DECLARED_RESOLUTION
    else:
        status = ComponentDiscoveryStatus.ONE_SEED_ONLY
    notes = (
        "Sobol banks clustered in wrapped joint space before attachment (ADR-046).",
        "Unattached cluster representatives may grow extra atlas components within the chart budget.",
        "Component ids come from chart-overlap connectivity, not from seed count.",
        "Even MULTISTART_STABLE_AT_DECLARED_RESOLUTION is not a closed parent component.",
    )
    return ComponentDiscoveryRecord(
        status=status,
        bank_id="sobol_unscrambled_seed1_seed2",
        bank_size=discovery_bank,
        confirmation_bank_size=confirmation_bank,
        projected_seed_count=projected,
        unattached_seed_count=remaining_unattached,
        component_count=component_count,
        notes=notes,
    )


def build_generic_5r_parent_atlas(
    entry: Spatial5RCorpusEntry | None = None,
    *,
    radius: float = LOCAL_CHART_RADIUS_RAD,
    max_charts: int = DEFAULT_MAX_CHARTS,
    discovery_bank: int = DISCOVERY_BANK,
    confirmation_bank: int = CONFIRM_BANK,
    max_total_charts: int | None = None,
) -> ParentAtlasResult:
    corpus = entry or build_generic_5r()
    model = corpus.model
    q0 = corpus.regular_q
    problem = FixedPositionParentProblem.from_model(model, q0)
    jp0 = position_jacobian(model.chain, q0)
    jp_fd, _jd = central_difference_jacobians(model.chain, q0, JACOBIAN_FD_STEP_RAD)
    fd_error = float(np.linalg.norm(jp0 - jp_fd, ord="fro"))
    fd_ok = fd_error <= JACOBIAN_FD_ERROR_TOL
    total_cap = max_total_charts if max_total_charts is not None else 2 * max_charts

    charts, frontiers, budget_hit = _grow_charts(
        problem, np.asarray(q0, dtype=float), radius=radius, max_charts=max_charts
    )
    dim = problem.ambient_dimension
    primary = _sobol_bank(discovery_bank, dim, seed=1)
    confirm = _sobol_bank(confirmation_bank, dim, seed=2)
    attach_tol = ATTACH_RADIUS_FACTOR * radius
    projected, unattached = _collect_unattached(problem, charts, (primary, confirm), attach_tol)
    cluster_r = CLUSTER_RADIUS_FACTOR * radius
    grown_extra = 0
    for rep in _cluster_projected(unattached, problem.periodic_coordinates, cluster_r):
        if len(charts) >= total_cap:
            budget_hit = True
            break
        before = len(charts)
        extra, extra_frontiers, extra_budget = _grow_charts(
            problem,
            rep,
            radius=radius,
            max_charts=total_cap,
            existing=charts,
        )
        charts = extra
        frontiers.extend(extra_frontiers)
        budget_hit = budget_hit or extra_budget
        if len(charts) > before:
            grown_extra += 1
    _, remaining_far = _collect_unattached(problem, charts, (primary, confirm), attach_tol)

    overlaps = _chart_adjacency(problem, tuple(charts), overlap_tol=1.2 * radius)
    groups = _union_find_components(tuple(c.chart_id for c in charts), overlaps)
    chart_components: list[tuple[str, str]] = []
    component_ids: list[str] = []
    for i, group in enumerate(groups):
        cid = f"{model.architecture_id}_component_{i}"
        component_ids.append(cid)
        for chart_id in group:
            chart_components.append((chart_id, cid))
    stitch = stitch_parent_mesh(problem, tuple(charts), radius=radius) if charts else None
    if stitch is not None and stitch.chart_seam_count:
        frontiers.append(
            FrontierRecord(
                FrontierKind.CHART_SEAM,
                None,
                None,
                f"{stitch.chart_seam_count} chart-ring vertices lie in overlap seams",
            )
        )

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
        discovery_bank=discovery_bank,
        confirmation_bank=confirmation_bank,
        budget_limited=budget_hit,
        grown_extra=grown_extra,
        remaining_unattached=len(remaining_far),
        projected=projected,
        component_count=len(component_ids),
    )
    accepted_res = [v.p_residual_m for v in vertices if v.accepted and v.p_residual_m is not None]
    open_n = sum(1 for f in frontiers if f.kind is FrontierKind.OPEN)
    sing_n = sum(1 for f in frontiers if f.kind is FrontierKind.SINGULAR)
    budg_n = sum(1 for f in frontiers if f.kind is FrontierKind.BUDGET_LIMITED)

    if not charts:
        status = ParentRepresentationStatus.REJECTED
        component_ids = []
    elif budget_hit or budg_n:
        status = ParentRepresentationStatus.BUDGET_LIMITED
    elif discovery.unattached_seed_count > 0:
        status = ParentRepresentationStatus.MULTICOMPONENT_UNRESOLVED
    elif sing_n and not open_n:
        status = ParentRepresentationStatus.SINGULAR_BOUNDARY
    elif len(charts) == 1:
        status = ParentRepresentationStatus.LOCAL_PATCH
        component_ids = []
        chart_components = []
    else:
        status = ParentRepresentationStatus.ATLAS_OPEN_FRONTIER

    return ParentAtlasResult(
        architecture_id=model.architecture_id,
        p_star=problem.p_star,
        representation_status=status,
        component_ids=tuple(component_ids),
        fiber_ids=(),
        charts=tuple(charts),
        overlaps=overlaps,
        vertices=tuple(vertices),
        frontiers=tuple(frontiers),
        discovery=discovery,
        stitch=stitch,
        chart_components=tuple(chart_components),
        declared_chart_radius=radius,
        joint_limits="not_modeled",
        seed_q=tuple(float(v) for v in q0),
        seed_fd_jp_error=fd_error,
        seed_fd_verified=fd_ok,
        max_p_residual_m=max(accepted_res) if accepted_res else None,
        notes=(
            "V06A2/H5 parent atlas: overlap components and clustered unattached growth (ADR-046).",
            f"open_frontiers={open_n}; singular={sing_n}; budget_limited={budg_n}; seams={sum(1 for f in frontiers if f.kind is FrontierKind.CHART_SEAM)}.",
            f"discovery={discovery.status.value}; projected={discovery.projected_seed_count}; extra_grown={grown_extra}.",
            "Not a complete parent, not S^2 coverage, and not a DecompositionCertificate.",
            "No fibers or closed-mechanism children are emitted from the atlas builder.",
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
        "stitched_vertex_count": 0 if result.stitch is None else len(result.stitch.vertices),
        "stitched_face_count": 0 if result.stitch is None else len(result.stitch.faces),
        "max_p_residual_m": result.max_p_residual_m,
        "joint_limits": result.joint_limits,
    }
