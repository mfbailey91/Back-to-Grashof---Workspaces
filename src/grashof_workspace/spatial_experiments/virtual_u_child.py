"""V06D2: local task-derived U_v chart and one independent UUUR child.

SUUR parent (exact_two_u_5r) -> h=c fiber -> UUUR. Not a six-family sweep
and not reconstruction.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .axis_aggregation import (
    MultiAggregationRecord,
    build_suur_multi_aggregation,
    embed_suur_physical_to_source,
    lift_source_to_suur_physical,
)
from .axis_geometry import as_mat3, as_vec3
from .branch_continuation import continue_implicit_branch
from .continuation import wrap_joint_delta
from .decomposition_certificate import DecompositionCertificate
from .fixed_position import JACOBIAN_FD_STEP_RAD, pose_fixed_position_problem
from .implicit_manifold import ambient_distance, orthonormal_tangent_basis
from .jacobians import matrix_rank_report, position_jacobian
from .open_chain import OpenChainModel
from .orientation_image import _pointing_geodesic, _rotation_geodesic
from .parent_atlas import ParentAtlasResult, build_generic_5r_parent_atlas, wrap_periodic
from .parent_level_sets import (
    SourceLevelSetFiber,
    build_parent_level_sets,
    levelset_jacobian,
    pointing_scalar,
)
from .rotations import rotation_about_axis
from .serial_chain import SerialRevoluteChain
from .v06_corpus import (
    Spatial5RCorpusEntry,
    build_exact_two_u_5r,
    build_generic_5r,
    build_near_two_u_5r,
)

Array = NDArray[np.floating]

CHILD_DIM = 7
CONSTRAINT_DIM = 6
LOCAL_COMPARISON_RADIUS_RAD = 0.5
MIN_LOCAL_COMPARISON_SAMPLES = 3
TOL_CLOSURE_RESIDUAL = 1e-6
TOL_POSITION_M = 1e-8
TOL_H_C = 1e-5
TOL_ORIENTATION_RAD = 1e-6
TOL_POINTING = 1e-6
TOL_JOINT_MAP_RAD = 1e-8
TOL_DIRECTED_SET = 5e-2
TOL_TANGENT = 5e-2
CHILD_STEPS = 24
CHILD_STEP = 0.05
NEWTON_ITERS = 20
CHART_LOCAL = "LOCAL_CANDIDATE"


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float) and not isfinite(obj):
        return None
    return obj


def _json_object(obj: dict[str, Any]) -> dict[str, Any]:
    payload = _json_safe(obj)
    if not isinstance(payload, dict):
        raise TypeError("expected a JSON object")
    return payload


def _copy_chain(chain: SerialRevoluteChain) -> SerialRevoluteChain:
    return SerialRevoluteChain(
        home_axes=chain.home_axes,
        p0=chain.p0,
        d0=chain.d0,
        R0=chain.R0,
    )


def _rotation_error_vec(Ra: Array, Rb: Array) -> Array:
    from .rotations import axis_angle_from_rotation

    axis, angle = axis_angle_from_rotation(Ra.T @ Rb)
    return np.asarray(axis * float(angle), dtype=float)


def local_virtual_u_axes(
    d: tuple[float, float, float] | Array,
    n: tuple[float, float, float] | Array,
) -> tuple[tuple[float, float, float], tuple[float, float, float], Array]:
    """Orthonormal a,b spanning ker((d×n)^T). Local chart only."""

    dv = np.asarray(d, dtype=float).reshape(3)
    nv = np.asarray(n, dtype=float).reshape(3)
    k = np.cross(dv, nv)
    kn = float(np.linalg.norm(k))
    if kn <= 1e-8:
        raise ValueError("d×n is degenerate; virtual-U chart unresolved")
    k = k / kn
    helper = np.array((0.0, 0.0, 1.0)) if abs(k[2]) < 0.9 else np.array((1.0, 0.0, 0.0))
    a = np.cross(helper, k)
    a = a / float(np.linalg.norm(a))
    b = np.cross(k, a)
    b = b / float(np.linalg.norm(b))
    return (
        as_vec3(a),
        as_vec3(b),
        np.asarray(k, dtype=float),
    )


@dataclass(frozen=True, slots=True)
class VirtualUChart:
    a: tuple[float, float, float]
    b: tuple[float, float, float]
    p_star: tuple[float, float, float]
    n: tuple[float, float, float]
    c: float
    d_seed: tuple[float, float, float]
    status: str
    notes: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "a": list(self.a),
            "b": list(self.b),
            "p_star": list(self.p_star),
            "n": list(self.n),
            "c": self.c,
            "d_seed": list(self.d_seed),
            "status": self.status,
            "notes": list(self.notes),
        }


def build_virtual_u_chart(
    d_seed: tuple[float, float, float],
    n: tuple[float, float, float],
    c: float,
    p_star: tuple[float, float, float],
) -> VirtualUChart:
    a, b, k = local_virtual_u_axes(d_seed, n)
    return VirtualUChart(
        a=a,
        b=b,
        p_star=p_star,
        n=n,
        c=c,
        d_seed=d_seed,
        status=CHART_LOCAL,
        notes=(
            "Local candidate U_v: a,b span ker((d×n)^T) at p*. Not a global child certificate.",
            f"||d×n||={float(np.linalg.norm(k)):.6f}",
        ),
    )


@dataclass(frozen=True, slots=True)
class ClosedUUURProblem:
    """Independent UUUR loop F(x)=0 in R^7. Distinct chain from the source."""

    source: OpenChainModel
    independent_chain: SerialRevoluteChain
    chart: VirtualUChart
    p_star: tuple[float, float, float]
    q_seed_source: tuple[float, ...]
    R_seed: tuple[tuple[float, float, float], ...]
    problem_id: str
    joint_kind_sequence: tuple[str, ...] = ("U", "U", "U", "R")
    joint_role_sequence: tuple[str, ...] = ("U_v", "U_phys", "U_phys", "R_phys")
    ambient_dimension: int = CHILD_DIM
    constraint_dimension: int = CONSTRAINT_DIM
    intrinsic_dimension: int = 1
    coordinate_names: tuple[str, ...] = (
        "uv_a",
        "uv_b",
        "u1a",
        "u1b",
        "u2a",
        "u2b",
        "r",
    )
    periodic_coordinates: tuple[bool, ...] = (True,) * CHILD_DIM
    drive_mode: str = "free_branch_s"

    def __post_init__(self) -> None:
        if id(self.independent_chain) == id(self.source.chain):
            raise ValueError("independent chain must be a distinct object from the source chain")
        if self.joint_role_sequence != ("U_v", "U_phys", "U_phys", "R_phys"):
            raise ValueError("V06D2 instantiates only UUUR")

    @classmethod
    def from_seed(
        cls,
        entry: Spatial5RCorpusEntry,
        chart: VirtualUChart,
        q_seed: tuple[float, ...],
    ) -> ClosedUUURProblem:
        model = entry.model
        posed = pose_fixed_position_problem(model, entry.regular_q)
        state = model.chain.evaluate(q_seed)
        return cls(
            source=model,
            independent_chain=_copy_chain(model.chain),
            chart=chart,
            p_star=posed.p_star,
            q_seed_source=q_seed,
            R_seed=as_mat3(state.R),
            problem_id=f"{model.architecture_id}_uuur_child",
        )

    def physical_q(self, x: Array) -> tuple[float, ...]:
        delta = np.asarray(x, dtype=float).reshape(-1)
        if delta.shape[0] != CHILD_DIM:
            raise ValueError("reduced x must have seven coordinates")
        seed = np.asarray(self.q_seed_source, dtype=float)
        return embed_suur_physical_to_source(tuple(float(v) for v in (seed + delta[2:7])))

    def uv_rotation(self, x: Array) -> Array:
        alpha, beta = float(x[0]), float(x[1])
        r_seed = np.asarray(self.R_seed, dtype=float)
        return np.asarray(
            r_seed
            @ rotation_about_axis(self.chart.a, alpha)
            @ rotation_about_axis(self.chart.b, beta),
            dtype=float,
        )

    def residual(self, x: Array) -> Array:
        q = self.physical_q(x)
        state = self.independent_chain.evaluate(q)
        r_pos = np.asarray(state.p, dtype=float) - np.asarray(self.p_star, dtype=float)
        r_ori = _rotation_error_vec(self.uv_rotation(x), np.asarray(state.R, dtype=float))
        return np.concatenate([r_pos, r_ori])

    def jacobian(self, x: Array) -> Array:
        x0 = np.asarray(x, dtype=float).reshape(-1)
        r0 = self.residual(x0)
        jac = np.zeros((CONSTRAINT_DIM, CHILD_DIM), dtype=float)
        eps = JACOBIAN_FD_STEP_RAD
        for i in range(CHILD_DIM):
            xp = x0.copy()
            xp[i] += eps
            jac[:, i] = (self.residual(xp) - r0) / eps
        return jac


def correct_uuur(problem: ClosedUUURProblem, x: Array) -> tuple[Array, bool, float]:
    y = np.asarray(x, dtype=float).copy()
    for _ in range(NEWTON_ITERS):
        r = problem.residual(y)
        nr = float(np.linalg.norm(r))
        if nr <= 1e-10:
            return y, True, nr
        jac = problem.jacobian(y)
        dq, *_ = np.linalg.lstsq(jac, -r, rcond=None)
        y = wrap_periodic(y + dq, problem.periodic_coordinates)
    nr = float(np.linalg.norm(problem.residual(y)))
    return y, False, nr


@dataclass(frozen=True, slots=True)
class UUURSample:
    s: float
    x: tuple[float, ...]
    alpha: float
    beta: float
    q_source: tuple[float, ...]
    pointing: tuple[float, float, float]
    residual: float
    rank_j: int
    nullity_j: int

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "s": self.s,
            "x": list(self.x),
            "alpha": self.alpha,
            "beta": self.beta,
            "q_source": list(self.q_source),
            "pointing": list(self.pointing),
            "residual": self.residual,
            "rank_j": self.rank_j,
            "nullity_j": self.nullity_j,
        }


def _sample(problem: ClosedUUURProblem, x: Array, s: float) -> UUURSample:
    xt = tuple(float(v) for v in np.asarray(x, dtype=float))
    q = problem.physical_q(x)
    state = problem.independent_chain.evaluate(q)
    jac = problem.jacobian(x)
    report = matrix_rank_report(jac)
    return UUURSample(
        s=s,
        x=xt,
        alpha=xt[0],
        beta=xt[1],
        q_source=q,
        pointing=as_vec3(state.d),
        residual=float(np.linalg.norm(problem.residual(x))),
        rank_j=report.rank,
        nullity_j=report.nullity,
    )


def continue_uuur(
    problem: ClosedUUURProblem,
    *,
    n_steps: int = CHILD_STEPS,
    step: float = CHILD_STEP,
) -> tuple[tuple[UUURSample, ...], str, bool]:
    x0, ok, _ = correct_uuur(problem, np.zeros(CHILD_DIM))
    if not ok:
        return (), "unresolved", False
    jac0 = problem.jacobian(x0)
    report0 = matrix_rank_report(jac0)
    if report0.rank != 6 or report0.nullity != 1:
        return (_sample(problem, x0, 0.0),), "singular", False
    trace = continue_implicit_branch(
        problem,
        x0,
        branch_id=f"{problem.problem_id}_uuur",
        max_steps=n_steps,
        step_size=step,
    )
    samples = [
        _sample(problem, np.asarray(step.x, dtype=float), step.s)
        for step in trace.steps
        if step.accepted and step.x is not None
    ]
    samples.sort(key=lambda s: s.s)
    return tuple(samples), trace.branch_status, trace.returned


def directed_wrapped_set_distance(
    src: Sequence[Array],
    dst: Sequence[Array],
    periodic: tuple[bool, ...],
) -> float:
    """Hausdorff one-way: max over src of min wrapped distance into dst."""

    if not src or not dst:
        return float("inf")
    worst = 0.0
    for q in src:
        best = min(ambient_distance(q, p, periodic) for p in dst)
        worst = max(worst, best)
    return worst


def _scoped_joint_samples(
    qs: Sequence[Array],
    seed: Array,
    radius: float,
    periodic: tuple[bool, ...],
) -> list[Array]:
    return [q for q in qs if ambient_distance(q, seed, periodic) <= radius]


@dataclass(frozen=True, slots=True)
class UUURComparison:
    max_closure_residual: float
    max_position_error_m: float
    max_h_c_error: float
    max_orientation_error_rad: float
    max_pointing_error: float
    max_joint_map_error_rad: float
    source_to_child_distance: float
    child_to_source_distance: float
    tangent_error: float
    sample_count: int
    source_sample_count: int
    comparison_scope_radius_rad: float
    metric_acceptance: tuple[tuple[str, bool], ...]
    failed_metrics: tuple[str, ...]
    component_correspondence_complete: bool
    accepted_local: bool
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_object(
            {
                "max_closure_residual": self.max_closure_residual,
                "max_position_error_m": self.max_position_error_m,
                "max_h_c_error": self.max_h_c_error,
                "max_orientation_error_rad": self.max_orientation_error_rad,
                "max_pointing_error": self.max_pointing_error,
                "max_joint_map_error_rad": self.max_joint_map_error_rad,
                "source_to_child_distance": self.source_to_child_distance,
                "child_to_source_distance": self.child_to_source_distance,
                "tangent_error": self.tangent_error,
                "sample_count": self.sample_count,
                "source_sample_count": self.source_sample_count,
                "comparison_scope_radius_rad": self.comparison_scope_radius_rad,
                "metric_acceptance": dict(self.metric_acceptance),
                "failed_metrics": list(self.failed_metrics),
                "component_correspondence_complete": self.component_correspondence_complete,
                "accepted_local": self.accepted_local,
                "notes": list(self.notes),
            }
        )


def compare_fiber_and_child(
    entry: Spatial5RCorpusEntry,
    problem: ClosedUUURProblem,
    fiber: SourceLevelSetFiber,
    samples: tuple[UUURSample, ...],
) -> UUURComparison:
    periodic5 = (True,) * 5
    q_seed = np.asarray(problem.q_seed_source, dtype=float)
    radius = LOCAL_COMPARISON_RADIUS_RAD
    source_all = [np.asarray(s.q, dtype=float) for s in fiber.samples]
    child_all = [np.asarray(s.q_source, dtype=float) for s in samples]
    source_qs = _scoped_joint_samples(source_all, q_seed, radius, periodic5)
    child_qs = _scoped_joint_samples(child_all, q_seed, radius, periodic5)
    scoped_samples = [
        s
        for s in samples
        if ambient_distance(np.asarray(s.q_source, dtype=float), q_seed, periodic5) <= radius
    ]
    closures = []
    pos_err = []
    hc_err = []
    ori_err = []
    pnt_err = []
    joint_err = []
    n = problem.chart.n
    c = problem.chart.c
    for sample in scoped_samples:
        x = np.asarray(sample.x, dtype=float)
        closures.append(sample.residual)
        q = np.asarray(sample.q_source, dtype=float)
        state_i = problem.independent_chain.evaluate(tuple(float(v) for v in q))
        state_s = entry.model.chain.evaluate(tuple(float(v) for v in q))
        pos_err.append(float(np.linalg.norm(np.asarray(state_s.p) - np.asarray(problem.p_star))))
        hc_err.append(abs(pointing_scalar(state_s.d, n) - c))
        ori_err.append(_rotation_geodesic(np.asarray(state_s.R), np.asarray(state_i.R)))
        pnt_err.append(_pointing_geodesic(np.asarray(state_s.d), np.asarray(state_i.d)))
        mapped = np.asarray(lift_source_to_suur_physical(tuple(float(v) for v in q)), dtype=float)
        expected = q_seed + x[2:7]
        joint_err.append(float(np.linalg.norm(wrap_joint_delta(mapped, expected))))
    s2c = directed_wrapped_set_distance(source_qs, child_qs, periodic5)
    c2s = directed_wrapped_set_distance(child_qs, source_qs, periodic5)
    seed_src = min(fiber.samples, key=lambda s: abs(s.sigma)) if fiber.samples else None
    tangent_err = float("inf")
    if seed_src is not None:
        j_src = levelset_jacobian(entry.model, seed_src.q, n)
        t_src = orthonormal_tangent_basis(j_src, expected_nullity=1)[:, 0]
        j_ch = problem.jacobian(np.zeros(CHILD_DIM))
        t_ch = orthonormal_tangent_basis(j_ch, expected_nullity=1)[:, 0]
        phys = t_ch[2:7]
        pn = float(np.linalg.norm(phys))
        if pn > 1e-12:
            phys = phys / pn
            tangent_err = float(min(np.linalg.norm(phys - t_src), np.linalg.norm(phys + t_src)))
    max_cl = max(closures) if closures else float("inf")
    max_pos = max(pos_err) if pos_err else float("inf")
    max_hc = max(hc_err) if hc_err else float("inf")
    max_ori = max(ori_err) if ori_err else float("inf")
    max_pnt = max(pnt_err) if pnt_err else float("inf")
    max_joint = max(joint_err) if joint_err else float("inf")
    metric_acceptance = (
        ("sample_support", len(source_qs) >= MIN_LOCAL_COMPARISON_SAMPLES and len(child_qs) >= MIN_LOCAL_COMPARISON_SAMPLES),
        ("closure", max_cl <= TOL_CLOSURE_RESIDUAL),
        ("position", max_pos <= TOL_POSITION_M),
        ("h_c", max_hc <= TOL_H_C),
        ("orientation", max_ori <= TOL_ORIENTATION_RAD),
        ("pointing", max_pnt <= TOL_POINTING),
        ("joint_map", max_joint <= TOL_JOINT_MAP_RAD),
        ("source_to_child", s2c <= TOL_DIRECTED_SET),
        ("child_to_source", c2s <= TOL_DIRECTED_SET),
        ("tangent", tangent_err <= TOL_TANGENT),
    )
    failed = tuple(name for name, ok in metric_acceptance if not ok)
    accepted = all(ok for _, ok in metric_acceptance)
    return UUURComparison(
        max_closure_residual=max_cl,
        max_position_error_m=max_pos,
        max_h_c_error=max_hc,
        max_orientation_error_rad=max_ori,
        max_pointing_error=max_pnt,
        max_joint_map_error_rad=max_joint,
        source_to_child_distance=s2c,
        child_to_source_distance=c2s,
        tangent_error=tangent_err,
        sample_count=len(child_qs),
        source_sample_count=len(source_qs),
        comparison_scope_radius_rad=radius,
        metric_acceptance=metric_acceptance,
        failed_metrics=failed,
        component_correspondence_complete=False,
        accepted_local=accepted,
        notes=(
            "Bidirectional sample comparison on a budget-limited fiber is not component completeness.",
            "Drive is pseudo-arclength s from the H3 augmented corrector (ADR-044/ADR-045).",
            "alpha(s) and beta(s) remain coupled outputs of the same branch.",
            "LOCAL_ONLY requires every named metric (ADR-043); do not initialize accepted.",
        ),
    )


def issue_uuur_certificate(
    entry: Spatial5RCorpusEntry,
    aggregation: MultiAggregationRecord,
    chart: VirtualUChart | None,
    comparison: UUURComparison | None,
    *,
    parent_slice_status: str,
    child_branch_status: str,
) -> DecompositionCertificate:
    posed = pose_fixed_position_problem(entry.model, entry.regular_q)
    jp = position_jacobian(entry.model.chain, entry.regular_q)
    report_p = matrix_rank_report(jp)
    kinds = ("U", "U", "U", "R")
    roles = ("U_v", "U_phys", "U_phys", "R_phys")
    rank_checks = {
        "rank_jp": report_p.rank,
        "nullity_jp": report_p.nullity,
        "parent_slice_status": parent_slice_status,
        "virtual_u_chart_status": None if chart is None else chart.status,
        "child_branch_status": child_branch_status,
        "p_star": list(posed.p_star),
    }
    axis_status = aggregation.axis_aggregation_status
    if axis_status != "EXACT_GLOBAL" or comparison is None or chart is None:
        return DecompositionCertificate(
            source_chain_id=entry.model.architecture_id,
            fixed_position_problem_id=f"{entry.model.architecture_id}_pstar",
            source_component_id=f"{entry.model.architecture_id}_component_seed0",
            source_mobility=1,
            joint_kind_sequence=kinds,
            joint_role_sequence=roles,
            cyclic_origin_role="U_v",
            designated_task_joint_role="U_v",
            reduction_operations=("pointing_level_set", "virtual_u_chart", "closed_mechanism_decomposition"),
            reduced_topology="U_v-U_phys-U_phys-R",
            coordinate_map="unresolved: UUUR child requires exact two-pair SUUR geometry",
            inverse_or_reconstruction_map="unresolved",
            task_map="h(d)=n·d=c on p(q)=p*",
            rank_and_nullity_checks=rank_checks,
            coordinate_regrouping_residuals=aggregation.fk_identity_residuals,
            closure_residuals={},
            tangent_subspace_error=None,
            trajectory_position_error_m=None,
            trajectory_pointing_error=None,
            trajectory_joint_map_error_rad=None,
            component_correspondence="not_applicable",
            joint_limit_correspondence="not_modeled",
            axis_aggregation_status=axis_status,
            closed_mechanism_status="REJECTED",
            status="REJECTED",
            failure_or_scope_reason=(
                "UUUR closed child is not issued without exact two-pair aggregation "
                "and an independent comparison."
            ),
            candidates=aggregation.candidates,
            aggregated=None,
            evidence={
                "multi_aggregation": aggregation.to_json_dict(),
                "virtual_u_chart": None if chart is None else chart.to_json_dict(),
                "initialized_accepted": False,
            },
        )
    closed = "REJECTED"
    if comparison.component_correspondence_complete and comparison.accepted_local:
        closed = "EXACT_ON_COMPONENT"
    elif comparison.accepted_local:
        closed = "LOCAL_ONLY"
    if closed == "LOCAL_ONLY":
        reason = (
            "Independent UUUR child matches the source fiber locally on every named metric. "
            "Not a complete component and not reconstruction."
        )
    elif closed == "EXACT_ON_COMPONENT":
        reason = "Independent UUUR child matches the source fiber on a complete component."
    else:
        failed = ", ".join(comparison.failed_metrics) or "unnamed"
        reason = f"UUUR/source comparison failed on: {failed}."
    return DecompositionCertificate(
        source_chain_id=entry.model.architecture_id,
        fixed_position_problem_id=f"{entry.model.architecture_id}_pstar",
        source_component_id=f"{entry.model.architecture_id}_component_seed0",
        source_mobility=1,
        joint_kind_sequence=kinds,
        joint_role_sequence=roles,
        cyclic_origin_role="U_v",
        designated_task_joint_role="U_v",
        reduction_operations=("pointing_level_set", "virtual_u_chart", "closed_mechanism_decomposition"),
        reduced_topology="U_v-U_phys-U_phys-R",
        coordinate_map="U_v(alpha,beta) at p* plus physical SUUR deltas; identity on 5R joints",
        inverse_or_reconstruction_map="physical 5-vector embeds to source q; U_v tracks R(q) on the slice",
        task_map="h(d)=n·d=c on p(q)=p*",
        rank_and_nullity_checks=rank_checks,
        coordinate_regrouping_residuals=aggregation.fk_identity_residuals,
        closure_residuals={"max_closure_residual": comparison.max_closure_residual},
        tangent_subspace_error=comparison.tangent_error,
        trajectory_position_error_m=comparison.max_position_error_m,
        trajectory_pointing_error=comparison.max_pointing_error,
        trajectory_joint_map_error_rad=comparison.max_joint_map_error_rad,
        component_correspondence="local_on_budget_limited_fiber",
        joint_limit_correspondence="not_modeled",
        axis_aggregation_status="EXACT_GLOBAL",
        closed_mechanism_status=closed,
        status=closed,
        failure_or_scope_reason=reason,
        candidates=aggregation.candidates,
        aggregated=None,
        evidence={
            "multi_aggregation": aggregation.to_json_dict(),
            "virtual_u_chart": chart.to_json_dict(),
            "comparison": comparison.to_json_dict(),
            "initialized_accepted": False,
            "component_correspondence_complete": False,
            "drive_mode": "free_branch_s",
        },
    )


@dataclass(frozen=True, slots=True)
class V06D2ArchitectureResult:
    architecture_id: str
    aggregation: MultiAggregationRecord
    chart: VirtualUChart | None
    fiber_id: str | None
    samples: tuple[UUURSample, ...]
    branch_status: str
    returned: bool
    comparison: UUURComparison | None
    certificate: DecompositionCertificate
    parent_slice_status: str

    def to_json_dict(self) -> dict[str, Any]:
        return _json_object(
            {
                "architecture_id": self.architecture_id,
                "aggregation": self.aggregation.to_json_dict(),
                "chart": None if self.chart is None else self.chart.to_json_dict(),
                "fiber_id": self.fiber_id,
                "sample_count": len(self.samples),
                "samples": [s.to_json_dict() for s in self.samples[:24]],
                "branch_status": self.branch_status,
                "returned": self.returned,
                "comparison": None if self.comparison is None else self.comparison.to_json_dict(),
                "certificate": self.certificate.to_json_dict(),
                "parent_slice_status": self.parent_slice_status,
                "curve_type": None,
            }
        )


def evaluate_v06d2_architecture(
    entry: Spatial5RCorpusEntry,
    *,
    grow_source: bool = True,
    max_charts: int = 6,
    discovery_bank: int = 16,
    confirmation_bank: int = 16,
    atlas: ParentAtlasResult | None = None,
) -> V06D2ArchitectureResult:
    aggregation = build_suur_multi_aggregation(entry.model, entry.regular_q)
    state0 = entry.model.chain.evaluate(entry.regular_q)
    posed = pose_fixed_position_problem(entry.model, entry.regular_q)
    chart: VirtualUChart | None = None
    fiber: SourceLevelSetFiber | None = None
    fiber_seed_q: tuple[float, ...] | None = None
    parent_slice = "UNRESOLVED"
    samples: tuple[UUURSample, ...] = ()
    branch = "unresolved"
    returned = False
    comparison = None
    if grow_source or atlas is not None:
        atlas_obj = atlas or build_generic_5r_parent_atlas(
            entry,
            max_charts=max_charts,
            discovery_bank=discovery_bank,
            confirmation_bank=confirmation_bank,
        )
        level = build_parent_level_sets(atlas_obj, entry.model)
        fiber = next((f for f in level.fibers if f.samples), None)
        if fiber is not None:
            parent_slice = fiber.branch_status
            seed = min(fiber.samples, key=lambda s: abs(s.sigma))
            fiber_seed_q = seed.q
            chart = build_virtual_u_chart(seed.pointing, fiber.n, fiber.c, atlas_obj.p_star)
    if chart is None:
        try:
            n = (0.0, 0.0, 1.0)
            d = as_vec3(state0.d)
            if abs(float(np.dot(d, n))) > 0.95:
                n = (1.0, 0.0, 0.0)
            chart = build_virtual_u_chart(d, n, pointing_scalar(d, n), posed.p_star)
        except ValueError:
            chart = None
    if (
        aggregation.axis_aggregation_status == "EXACT_GLOBAL"
        and chart is not None
        and fiber is not None
        and fiber_seed_q is not None
    ):
        problem = ClosedUUURProblem.from_seed(entry, chart, fiber_seed_q)
        samples, branch, returned = continue_uuur(problem)
        if samples:
            comparison = compare_fiber_and_child(entry, problem, fiber, samples)
    certificate = issue_uuur_certificate(
        entry,
        aggregation,
        chart,
        comparison,
        parent_slice_status=parent_slice,
        child_branch_status=branch,
    )
    return V06D2ArchitectureResult(
        architecture_id=entry.model.architecture_id,
        aggregation=aggregation,
        chart=chart,
        fiber_id=None if fiber is None else fiber.fiber_id,
        samples=samples,
        branch_status=branch,
        returned=returned,
        comparison=comparison,
        certificate=certificate,
        parent_slice_status=parent_slice,
    )


def v06d2_program_summary(*, grow_exact: bool = True) -> dict[str, Any]:
    exact = evaluate_v06d2_architecture(build_exact_two_u_5r(), grow_source=grow_exact, max_charts=6)
    near = evaluate_v06d2_architecture(build_near_two_u_5r(), grow_source=False)
    generic = evaluate_v06d2_architecture(build_generic_5r(), grow_source=False)
    return {
        "exact_two_u_5r": exact.to_json_dict(),
        "near_two_u_5r": near.to_json_dict(),
        "generic_5r": generic.to_json_dict(),
        "notes": [
            "V06D2 instantiates one UUUR child only; not a six-family sweep.",
            "Local U_v chart is not a global child certificate (ADR-041).",
        ],
    }
