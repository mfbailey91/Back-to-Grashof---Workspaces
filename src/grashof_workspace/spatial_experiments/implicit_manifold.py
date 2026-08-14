"""Generic two-dimensional implicit-manifold atlas engine (V06A0).

Software validation only. This module does not construct a spatial-5R parent,
issue a ``DecompositionCertificate``, or change L5 reconstruction status.

The first implemented problem is the analytical unit sphere
``F(x) = x·x - 1``. ``FixedPositionParentProblem`` is reserved for V06A1.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import ConvexHull

from .jacobians import matrix_rank_report, nullspace

Array = NDArray[np.floating]

RESIDUAL_TOL = 1e-10
GAUGE_TOL = 1e-10
NEWTON_MAX_ITERS = 25
TANGENT_ORTH_TOL = 1e-10
DEFAULT_CHART_RADIUS = 0.45
DEFAULT_N_RINGS = 1


class ProcessSoftwareStatus(str, Enum):
    """Process/scaffold label; not a DecompositionCertificate status."""

    SOFTWARE_VALIDATION = "SOFTWARE_VALIDATION"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class TaskEvaluation:
    """Optional task map evaluated at a manifold sample (problem-defined)."""

    values: tuple[float, ...]
    labels: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "values": list(self.values),
            "labels": list(self.labels),
            "notes": list(self.notes),
        }


class ImplicitManifoldProblem(Protocol):
    """Dimension-independent implicit manifold F(x)=0 of intrinsic dimension 2."""

    problem_id: str
    ambient_dimension: int
    constraint_dimension: int
    intrinsic_dimension: int
    coordinate_names: tuple[str, ...]
    periodic_coordinates: tuple[bool, ...]

    def residual(self, x: Array) -> Array: ...

    def jacobian(self, x: Array) -> Array: ...

    def evaluate_task(self, x: Array) -> TaskEvaluation: ...


@dataclass(frozen=True, slots=True)
class AnalyticalSphereProblem:
    """Unit sphere ``x·x - 1 = 0`` in ``R^3`` (V06A0 fixture)."""

    problem_id: str = "analytical_unit_sphere"
    ambient_dimension: int = 3
    constraint_dimension: int = 1
    intrinsic_dimension: int = 2
    coordinate_names: tuple[str, ...] = ("x", "y", "z")
    periodic_coordinates: tuple[bool, ...] = (False, False, False)

    def residual(self, x: Array) -> Array:
        vec = np.asarray(x, dtype=float).reshape(-1)
        return np.array([float(vec @ vec) - 1.0], dtype=float)

    def jacobian(self, x: Array) -> Array:
        vec = np.asarray(x, dtype=float).reshape(-1)
        return 2.0 * vec.reshape(1, -1)

    def evaluate_task(self, x: Array) -> TaskEvaluation:
        vec = np.asarray(x, dtype=float).reshape(-1)
        return TaskEvaluation(
            values=tuple(float(v) for v in vec),
            labels=self.coordinate_names,
            notes=("embedding coordinates; not a kinematic task map",),
        )


def wrapped_delta(
    a: Array,
    b: Array,
    periodic: tuple[bool, ...],
) -> Array:
    """Componentwise ``a - b`` with ``atan2`` wrapping on periodic coordinates."""

    xa = np.asarray(a, dtype=float).reshape(-1)
    xb = np.asarray(b, dtype=float).reshape(-1)
    if xa.size != xb.size:
        raise ValueError("wrapped_delta requires matching lengths")
    if len(periodic) != xa.size:
        raise ValueError("periodic_coordinates length must match ambient dimension")
    out = np.empty_like(xa)
    for i, flag in enumerate(periodic):
        raw = float(xa[i] - xb[i])
        if flag:
            out[i] = float(np.arctan2(np.sin(raw), np.cos(raw)))
        else:
            out[i] = raw
    return out


def ambient_distance(a: Array, b: Array, periodic: tuple[bool, ...]) -> float:
    delta = wrapped_delta(a, b, periodic)
    return float(np.linalg.norm(delta))


def projector_frobenius(na: Array, nb: Array) -> float:
    pa = na @ na.T
    pb = nb @ nb.T
    return float(np.linalg.norm(pa - pb, ord="fro"))


def align_tangent_basis(n_ref: Array, n_new: Array) -> Array:
    """Orthogonal Procrustes: rotate ``n_new`` columns to match ``n_ref``."""

    ref = np.asarray(n_ref, dtype=float)
    new = np.asarray(n_new, dtype=float)
    if ref.shape != new.shape:
        raise ValueError("tangent bases must have matching shape")
    if ref.size == 0:
        return new
    c = new.T @ ref
    u, _s, vt = np.linalg.svd(c)
    det = float(np.linalg.det(u @ vt))
    if det < 0.0:
        u = u.copy()
        u[:, -1] *= -1.0
    q = u @ vt
    return new @ q


def orthonormal_tangent_basis(jacobian: Array, *, expected_nullity: int | None = None) -> Array:
    basis = nullspace(jacobian)
    if expected_nullity is not None and int(basis.shape[1]) != expected_nullity:
        raise ValueError(
            f"expected nullity {expected_nullity}, got {basis.shape[1]} "
            f"for jacobian shape {jacobian.shape}"
        )
    return basis


@dataclass(frozen=True, slots=True)
class ChartCorrection:
    """One augmented Newton correction of a predicted chart sample."""

    u: tuple[float, ...]
    x_pred: tuple[float, ...]
    x: tuple[float, ...] | None
    constraint_residual: float
    gauge_residual: float
    correction_norm: float
    iterations: int
    condition_number: float | None
    rank: int | None
    nullity: int | None
    accepted: bool
    rejection_reason: str | None
    tangent_change: float | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "u": list(self.u),
            "x_pred": list(self.x_pred),
            "x": None if self.x is None else list(self.x),
            "constraint_residual": self.constraint_residual,
            "gauge_residual": self.gauge_residual,
            "correction_norm": self.correction_norm,
            "iterations": self.iterations,
            "condition_number": self.condition_number,
            "rank": self.rank,
            "nullity": self.nullity,
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
            "tangent_change": self.tangent_change,
        }


def correct_chart_point(
    problem: ImplicitManifoldProblem,
    x_c: Array,
    n_c: Array,
    u: Array,
    *,
    residual_tol: float = RESIDUAL_TOL,
    gauge_tol: float = GAUGE_TOL,
    max_iters: int = NEWTON_MAX_ITERS,
) -> ChartCorrection:
    """Solve the augmented predictor-corrector system at local coordinate ``u``."""

    u_vec = np.asarray(u, dtype=float).reshape(-1)
    x_c_vec = np.asarray(x_c, dtype=float).reshape(-1)
    n_c_mat = np.asarray(n_c, dtype=float)
    x_pred = x_c_vec + n_c_mat @ u_vec
    x = x_pred.copy()
    condition: float | None = None
    rank: int | None = None
    nullity: int | None = None
    last_f = problem.residual(x)
    last_g = n_c_mat.T @ wrapped_delta(x, x_pred, problem.periodic_coordinates)
    rejection: str | None = None
    accepted = False
    it = 0
    for it in range(1, max_iters + 1):
        f = problem.residual(x)
        jac = problem.jacobian(x)
        gauge = n_c_mat.T @ wrapped_delta(x, x_pred, problem.periodic_coordinates)
        last_f, last_g = f, gauge
        g = np.concatenate([f.reshape(-1), gauge.reshape(-1)])
        if float(np.linalg.norm(f)) <= residual_tol and float(np.linalg.norm(gauge)) <= gauge_tol:
            accepted = True
            rejection = None
            report = matrix_rank_report(jac)
            rank, nullity = report.rank, report.nullity
            dg_top = jac
            dg = np.vstack([dg_top, n_c_mat.T])
            s = np.linalg.svd(dg, compute_uv=False)
            condition = float(s[0] / s[-1]) if s.size and float(s[-1]) > 0.0 else None
            break
        dg = np.vstack([jac, n_c_mat.T])
        s = np.linalg.svd(dg, compute_uv=False)
        condition = float(s[0] / s[-1]) if s.size and float(s[-1]) > 0.0 else None
        try:
            step, *_rest = np.linalg.lstsq(dg, -g, rcond=None)
        except np.linalg.LinAlgError:
            rejection = "newton_linear_solve_failed"
            break
        x = x + step
        report = matrix_rank_report(jac)
        rank, nullity = report.rank, report.nullity
    else:
        rejection = "newton_max_iters"
        it = max_iters

    if not accepted and rejection is None:
        rejection = "residual_or_gauge_unmet"

    tangent_change: float | None = None
    x_tuple = None
    if accepted:
        n_new = orthonormal_tangent_basis(
            problem.jacobian(x),
            expected_nullity=problem.intrinsic_dimension,
        )
        n_aligned = align_tangent_basis(n_c_mat, n_new)
        tangent_change = projector_frobenius(n_c_mat, n_aligned)
        x_tuple = tuple(float(v) for v in x)

    return ChartCorrection(
        u=tuple(float(v) for v in u_vec),
        x_pred=tuple(float(v) for v in x_pred),
        x=x_tuple,
        constraint_residual=float(np.linalg.norm(last_f)),
        gauge_residual=float(np.linalg.norm(last_g)),
        correction_norm=float(np.linalg.norm(x - x_pred)),
        iterations=it,
        condition_number=condition,
        rank=rank,
        nullity=nullity,
        accepted=accepted,
        rejection_reason=rejection,
        tangent_change=tangent_change,
    )


def hexagonal_offsets(radius: float, n_rings: int = DEFAULT_N_RINGS) -> tuple[tuple[float, float], ...]:
    if radius <= 0.0:
        raise ValueError("chart radius must be positive")
    if n_rings < 1:
        raise ValueError("n_rings must be at least 1")
    points: list[tuple[float, float]] = [(0.0, 0.0)]
    for ring in range(1, n_rings + 1):
        for k in range(6):
            angle0 = k * pi / 3.0
            angle1 = ((k + 1) % 6) * pi / 3.0
            p0 = np.array((np.cos(angle0), np.sin(angle0))) * radius * ring
            p1 = np.array((np.cos(angle1), np.sin(angle1))) * radius * ring
            for j in range(ring):
                t = j / ring
                p = (1.0 - t) * p0 + t * p1
                points.append((float(p[0]), float(p[1])))
    return tuple(points)


def hexagonal_triangles(n_rings: int = DEFAULT_N_RINGS) -> tuple[tuple[int, int, int], ...]:
    """Fan triangulation of the first ring; extra rings use consecutive hex edges."""

    if n_rings < 1:
        raise ValueError("n_rings must be at least 1")
    tris: list[tuple[int, int, int]] = []
    first_ring = list(range(1, 7))
    for i, idx in enumerate(first_ring):
        nxt = first_ring[(i + 1) % 6]
        tris.append((0, idx, nxt))
    if n_rings == 1:
        return tuple(tris)
    # Additional rings: index layout matches hexagonal_offsets (ring-major, 6*ring pts).
    offset = 1
    for ring in range(1, n_rings):
        inner_count = 6 * ring
        outer_count = 6 * (ring + 1)
        inner_start = offset
        outer_start = offset + inner_count
        inner = list(range(inner_start, inner_start + inner_count))
        outer = list(range(outer_start, outer_start + outer_count))
        # Walk 6 sectors; each sector has `ring` inner edges and `ring+1` outer points.
        inner_i = 0
        outer_i = 0
        for _sector in range(6):
            for _step in range(ring):
                a = inner[inner_i % inner_count]
                b = inner[(inner_i + 1) % inner_count]
                c = outer[outer_i % outer_count]
                d = outer[(outer_i + 1) % outer_count]
                tris.append((a, c, d))
                tris.append((a, d, b))
                inner_i += 1
                outer_i += 1
            # extra outer vertex at sector corner
            outer_i += 1
        offset = outer_start
    return tuple(tris)


@dataclass(frozen=True, slots=True)
class ChartSample:
    local_index: int
    u: tuple[float, float]
    correction: ChartCorrection

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "local_index": self.local_index,
            "u": list(self.u),
            "correction": self.correction.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class ChartRecord:
    chart_id: str
    center: tuple[float, ...]
    tangent_basis: tuple[tuple[float, ...], ...]
    radius: float
    samples: tuple[ChartSample, ...]
    triangles: tuple[tuple[int, int, int], ...]
    accepted: bool
    notes: tuple[str, ...] = ()

    def accepted_points(self) -> tuple[Array, ...]:
        pts = []
        for sample in self.samples:
            if sample.correction.accepted and sample.correction.x is not None:
                pts.append(np.asarray(sample.correction.x, dtype=float))
        return tuple(pts)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "center": list(self.center),
            "tangent_basis": [list(col) for col in self.tangent_basis],
            "radius": self.radius,
            "samples": [sample.to_json_dict() for sample in self.samples],
            "triangles": [list(tri) for tri in self.triangles],
            "accepted": self.accepted,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class ChartOverlapRecord:
    chart_a: str
    chart_b: str
    max_center_distance: float
    overlapping_sample_count: int
    max_sample_distance: float | None
    duplicate_rejected: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "chart_a": self.chart_a,
            "chart_b": self.chart_b,
            "max_center_distance": self.max_center_distance,
            "overlapping_sample_count": self.overlapping_sample_count,
            "max_sample_distance": self.max_sample_distance,
            "duplicate_rejected": self.duplicate_rejected,
        }


@dataclass(frozen=True, slots=True)
class ManifoldAtlasResult:
    problem_id: str
    process_status: ProcessSoftwareStatus
    charts: tuple[ChartRecord, ...]
    overlaps: tuple[ChartOverlapRecord, ...]
    rejected_duplicate_centers: tuple[tuple[float, ...], ...]
    component_count: int
    closed_component: bool
    approximate_area: float | None
    area_target: float | None
    declared_chart_radius: float
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "process_status": self.process_status.value,
            "certificate_status": None,
            "charts": [chart.to_json_dict() for chart in self.charts],
            "overlaps": [item.to_json_dict() for item in self.overlaps],
            "rejected_duplicate_centers": [list(c) for c in self.rejected_duplicate_centers],
            "component_count": self.component_count,
            "closed_component": self.closed_component,
            "approximate_area": self.approximate_area,
            "area_target": self.area_target,
            "declared_chart_radius": self.declared_chart_radius,
            "notes": list(self.notes),
        }


def build_hexagonal_chart(
    problem: ImplicitManifoldProblem,
    seed: Array,
    *,
    chart_id: str,
    radius: float = DEFAULT_CHART_RADIUS,
    n_rings: int = DEFAULT_N_RINGS,
    n_ref: Array | None = None,
) -> ChartRecord:
    x0 = np.asarray(seed, dtype=float).reshape(-1)
    # Snap the seed onto the manifold with a trivial chart corrector at u=0
    # using a temporary tangent from the seed Jacobian.
    n_seed = orthonormal_tangent_basis(
        problem.jacobian(x0),
        expected_nullity=problem.intrinsic_dimension,
    )
    if n_ref is not None:
        n_seed = align_tangent_basis(n_ref, n_seed)
    origin = correct_chart_point(problem, x0, n_seed, np.zeros(problem.intrinsic_dimension))
    if not origin.accepted or origin.x is None:
        return ChartRecord(
            chart_id=chart_id,
            center=tuple(float(v) for v in x0),
            tangent_basis=tuple(tuple(float(v) for v in col) for col in n_seed.T),
            radius=radius,
            samples=(),
            triangles=(),
            accepted=False,
            notes=(f"seed correction failed: {origin.rejection_reason}",),
        )
    x_c = np.asarray(origin.x, dtype=float)
    n_c = orthonormal_tangent_basis(
        problem.jacobian(x_c),
        expected_nullity=problem.intrinsic_dimension,
    )
    n_c = align_tangent_basis(n_seed, n_c)
    offsets = hexagonal_offsets(radius, n_rings)
    triangles = hexagonal_triangles(n_rings)
    samples: list[ChartSample] = []
    for i, (u1, u2) in enumerate(offsets):
        corr = correct_chart_point(problem, x_c, n_c, np.array((u1, u2), dtype=float))
        samples.append(ChartSample(local_index=i, u=(u1, u2), correction=corr))
    accepted = all(s.correction.accepted for s in samples)
    return ChartRecord(
        chart_id=chart_id,
        center=tuple(float(v) for v in x_c),
        tangent_basis=tuple(tuple(float(v) for v in col) for col in n_c.T),
        radius=radius,
        samples=tuple(samples),
        triangles=triangles,
        accepted=accepted,
        notes=("hexagonal chart; V06A0 software validation",),
    )


def _union_find_components(n: int, edges: list[tuple[int, int]]) -> int:
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i, j in edges:
        union(i, j)
    return len({find(i) for i in range(n)})


def _chart_overlap(
    problem: ImplicitManifoldProblem,
    a: ChartRecord,
    b: ChartRecord,
    *,
    overlap_factor: float = 1.6,
) -> ChartOverlapRecord:
    ca = np.asarray(a.center, dtype=float)
    cb = np.asarray(b.center, dtype=float)
    d_centers = ambient_distance(ca, cb, problem.periodic_coordinates)
    pts_a = a.accepted_points()
    pts_b = b.accepted_points()
    count = 0
    max_d: float | None = None
    threshold = overlap_factor * min(a.radius, b.radius)
    for pa in pts_a:
        for pb in pts_b:
            dist = ambient_distance(pa, pb, problem.periodic_coordinates)
            if dist <= threshold * 0.35:
                count += 1
                max_d = dist if max_d is None else max(max_d, dist)
    return ChartOverlapRecord(
        chart_a=a.chart_id,
        chart_b=b.chart_id,
        max_center_distance=d_centers,
        overlapping_sample_count=count,
        max_sample_distance=max_d,
        duplicate_rejected=False,
    )


def _unique_accepted_vertices(atlas_charts: tuple[ChartRecord, ...], *, cluster_tol: float) -> Array:
    pts: list[Array] = []
    for chart in atlas_charts:
        pts.extend(chart.accepted_points())
    if not pts:
        return np.zeros((0, 0))
    clustered: list[Array] = []
    for p in pts:
        if any(float(np.linalg.norm(p - q)) <= cluster_tol for q in clustered):
            continue
        clustered.append(p)
    return np.vstack(clustered)


def _convex_hull_area(points: Array) -> float | None:
    if points.shape[0] < 4:
        return None
    hull = ConvexHull(points)
    return float(hull.area)


def grow_manifold_atlas(
    problem: ImplicitManifoldProblem,
    seed: Array,
    *,
    radius: float = DEFAULT_CHART_RADIUS,
    n_rings: int = DEFAULT_N_RINGS,
    max_charts: int = 80,
    duplicate_center_tol: float | None = None,
) -> ManifoldAtlasResult:
    """Grow hexagonal charts from a seed until no new non-duplicate centers remain."""

    dup_tol = duplicate_center_tol if duplicate_center_tol is not None else 0.55 * radius
    charts: list[ChartRecord] = []
    rejected: list[tuple[float, ...]] = []
    seed_chart = build_hexagonal_chart(
        problem, seed, chart_id="chart_000", radius=radius, n_rings=n_rings
    )
    if not seed_chart.accepted:
        return ManifoldAtlasResult(
            problem_id=problem.problem_id,
            process_status=ProcessSoftwareStatus.REJECTED,
            charts=(seed_chart,),
            overlaps=(),
            rejected_duplicate_centers=(),
            component_count=0,
            closed_component=False,
            approximate_area=None,
            area_target=None,
            declared_chart_radius=radius,
            notes=("seed chart rejected",),
        )
    charts.append(seed_chart)

    def _ring_vertices(chart: ChartRecord) -> list[Array]:
        pts: list[Array] = []
        for sample in chart.samples:
            if sample.local_index == 0:
                continue
            if sample.correction.accepted and sample.correction.x is not None:
                pts.append(np.asarray(sample.correction.x, dtype=float))
        return pts

    frontier: list[Array] = _ring_vertices(seed_chart)
    while frontier and len(charts) < max_charts:
        centers = [np.asarray(c.center, dtype=float) for c in charts]

        def _min_center_dist(p: Array) -> float:
            return min(ambient_distance(p, c, problem.periodic_coordinates) for c in centers)

        frontier.sort(key=_min_center_dist)
        candidate = frontier.pop()
        if _min_center_dist(candidate) <= dup_tol:
            rejected.append(tuple(float(v) for v in candidate))
            continue
        n_prev = np.asarray(charts[-1].tangent_basis, dtype=float).T
        chart = build_hexagonal_chart(
            problem,
            candidate,
            chart_id=f"chart_{len(charts):03d}",
            radius=radius,
            n_rings=n_rings,
            n_ref=n_prev,
        )
        if not chart.accepted:
            continue
        if any(
            ambient_distance(
                np.asarray(chart.center), np.asarray(c.center), problem.periodic_coordinates
            )
            <= dup_tol
            for c in charts
        ):
            rejected.append(chart.center)
            continue
        charts.append(chart)
        frontier.extend(_ring_vertices(chart))
        centers = [np.asarray(c.center, dtype=float) for c in charts]
        kept: list[Array] = []
        for p in frontier:
            if min(ambient_distance(p, c, problem.periodic_coordinates) for c in centers) <= dup_tol:
                rejected.append(tuple(float(v) for v in p))
            else:
                kept.append(p)
        frontier = kept

    overlaps: list[ChartOverlapRecord] = []
    uf_edges: list[tuple[int, int]] = []
    for i, a in enumerate(charts):
        for j, b in enumerate(charts):
            if j <= i:
                continue
            rec = _chart_overlap(problem, a, b)
            if rec.overlapping_sample_count > 0:
                overlaps.append(rec)
                uf_edges.append((i, j))
    overlaps.sort(key=lambda r: (r.chart_a, r.chart_b))
    unique_rejected: list[tuple[float, ...]] = []
    for center in rejected:
        p = np.asarray(center, dtype=float)
        if any(
            ambient_distance(p, np.asarray(q), problem.periodic_coordinates) <= dup_tol
            for q in unique_rejected
        ):
            continue
        unique_rejected.append(center)
    n_comp = _union_find_components(len(charts), uf_edges) if charts else 0
    verts = _unique_accepted_vertices(tuple(charts), cluster_tol=0.08 * radius)
    area = _convex_hull_area(verts) if verts.size else None
    closed = n_comp == 1 and len(charts) >= 6
    notes = (
        "V06A0 SOFTWARE_VALIDATION: analytical unit-sphere fixture.",
        "Not a FixedPositionParentResult and not a DecompositionCertificate.",
        "Duplicate chart centers rejected by wrapped ambient distance.",
    )
    return ManifoldAtlasResult(
        problem_id=problem.problem_id,
        process_status=ProcessSoftwareStatus.SOFTWARE_VALIDATION,
        charts=tuple(charts),
        overlaps=tuple(overlaps),
        rejected_duplicate_centers=tuple(unique_rejected),
        component_count=n_comp,
        closed_component=closed,
        approximate_area=area,
        area_target=4.0 * pi,
        declared_chart_radius=radius,
        notes=notes,
    )


def build_sphere_atlas(
    *,
    seed: tuple[float, ...] = (0.0, 0.0, 1.0),
    radius: float = DEFAULT_CHART_RADIUS,
    max_charts: int = 80,
) -> ManifoldAtlasResult:
    problem = AnalyticalSphereProblem()
    return grow_manifold_atlas(
        problem,
        np.asarray(seed, dtype=float),
        radius=radius,
        max_charts=max_charts,
    )
