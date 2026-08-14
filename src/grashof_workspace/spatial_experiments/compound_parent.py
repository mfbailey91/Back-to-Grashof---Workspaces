"""V06B independent S_v-U_phys-U_phys-R compound parent.

Eight scalar coordinates, six closure equations, mobility two. This is not a
UUUR child, not U_v, and not a complete-component certificate.
"""

from __future__ import annotations

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
from .decomposition_certificate import DecompositionCertificate
from .fixed_position import JACOBIAN_FD_STEP_RAD, pose_fixed_position_problem
from .implicit_manifold import (
    ChartRecord,
    TaskEvaluation,
    ambient_distance,
    build_hexagonal_chart,
    orthonormal_tangent_basis,
    projector_frobenius,
)
from .jacobians import matrix_rank_report, pointing_jacobian, position_jacobian
from .open_chain import OpenChainModel
from .orientation_image import _pointing_geodesic, _rotation_geodesic
from .parent_atlas import build_generic_5r_parent_atlas
from .parent_local import LOCAL_CHART_RADIUS_RAD, FixedPositionParentProblem
from .rotations import axis_angle_from_rotation, rotation_about_axis
from .serial_chain import SerialRevoluteChain
from .v06_corpus import Spatial5RCorpusEntry, build_exact_two_u_5r, build_generic_5r, build_near_two_u_5r

Array = NDArray[np.floating]

REDUCED_DIM = 8
CONSTRAINT_DIM = 6
ORIENTATION_ERR_TOL = 1e-6
POINTING_ERR_TOL = 1e-6
TANGENT_ERR_TOL = 1e-3
JOINT_MAP_TOL = 1e-8


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float) and not isfinite(obj):
        return None
    return obj


def _copy_chain(chain: SerialRevoluteChain) -> SerialRevoluteChain:
    return SerialRevoluteChain(
        home_axes=chain.home_axes,
        p0=chain.p0,
        d0=chain.d0,
        R0=chain.R0,
    )


def _rotvec_compose(R0: Array, sv: Array) -> Array:
    rx, ry, rz = (float(v) for v in np.asarray(sv, dtype=float).reshape(3))
    return np.asarray(
        R0 @ rotation_about_axis((1.0, 0.0, 0.0), rx)
        @ rotation_about_axis((0.0, 1.0, 0.0), ry)
        @ rotation_about_axis((0.0, 0.0, 1.0), rz),
        dtype=float,
    )


def _rotation_error_vec(Ra: Array, Rb: Array) -> Array:
    axis, angle = axis_angle_from_rotation(Ra.T @ Rb)
    return np.asarray(axis * float(angle), dtype=float)


@dataclass(frozen=True, slots=True)
class ClosedCompoundParentProblem:
    """Independent SUUR loop F(x)=0 in R^8. Distinct chain object from source."""

    source: OpenChainModel
    independent_chain: SerialRevoluteChain
    p_star: tuple[float, float, float]
    q_seed_source: tuple[float, ...]
    R_seed: tuple[tuple[float, float, float], ...]
    problem_id: str
    ambient_dimension: int = REDUCED_DIM
    constraint_dimension: int = CONSTRAINT_DIM
    intrinsic_dimension: int = 2
    coordinate_names: tuple[str, ...] = (
        "sv_x",
        "sv_y",
        "sv_z",
        "u1a",
        "u1b",
        "u2a",
        "u2b",
        "r",
    )
    periodic_coordinates: tuple[bool, ...] = (True,) * REDUCED_DIM

    def __post_init__(self) -> None:
        if id(self.independent_chain) == id(self.source.chain):
            raise ValueError("independent chain must be a distinct object from the source chain")
        if "U_v" in self.source.joint_role_sequence:
            raise ValueError("U_v is forbidden on the V06B SUUR parent")

    @classmethod
    def from_entry(cls, entry: Spatial5RCorpusEntry) -> ClosedCompoundParentProblem:
        model = entry.model
        q0 = entry.regular_q
        posed = pose_fixed_position_problem(model, q0)
        state = model.chain.evaluate(q0)
        independent = _copy_chain(model.chain)
        return cls(
            source=model,
            independent_chain=independent,
            p_star=posed.p_star,
            q_seed_source=q0,
            R_seed=tuple(tuple(float(v) for v in row) for row in np.asarray(state.R, dtype=float)),
            problem_id=f"{model.architecture_id}_suur_closed_parent",
        )

    def physical_q(self, x: Array) -> tuple[float, ...]:
        delta = np.asarray(x, dtype=float).reshape(-1)
        if delta.shape[0] != REDUCED_DIM:
            raise ValueError("reduced x must have eight coordinates")
        seed = np.asarray(self.q_seed_source, dtype=float)
        return embed_suur_physical_to_source(tuple(float(v) for v in (seed + delta[3:8])))

    def residual(self, x: Array) -> Array:
        q = self.physical_q(x)
        state = self.independent_chain.evaluate(q)
        r_pos = np.asarray(state.p, dtype=float) - np.asarray(self.p_star, dtype=float)
        r_seed = np.asarray(self.R_seed, dtype=float)
        r_sv = _rotvec_compose(r_seed, np.asarray(x, dtype=float)[:3])
        r_ori = _rotation_error_vec(r_sv, np.asarray(state.R, dtype=float))
        return np.concatenate([r_pos, r_ori])

    def jacobian(self, x: Array) -> Array:
        x0 = np.asarray(x, dtype=float).reshape(-1)
        r0 = self.residual(x0)
        jac = np.zeros((CONSTRAINT_DIM, REDUCED_DIM), dtype=float)
        eps = JACOBIAN_FD_STEP_RAD
        for i in range(REDUCED_DIM):
            xp = x0.copy()
            xp[i] += eps
            jac[:, i] = (self.residual(xp) - r0) / eps
        return jac

    def evaluate_task(self, x: Array) -> TaskEvaluation:
        q = self.physical_q(x)
        state = self.independent_chain.evaluate(q)
        rflat = tuple(float(v) for v in np.asarray(state.R, dtype=float).reshape(-1))
        d = tuple(float(v) for v in np.asarray(state.d, dtype=float).reshape(-1))
        return TaskEvaluation(
            values=rflat + d,
            labels=tuple(f"R{i}" for i in range(9)) + ("dx", "dy", "dz"),
            notes=("SUUR task map; not coverage and not UUUR",),
        )


def grow_compound_parent_atlas(
    problem: ClosedCompoundParentProblem,
    *,
    radius: float = LOCAL_CHART_RADIUS_RAD,
    max_charts: int = 6,
) -> tuple[ChartRecord, ...]:
    """Hexagonal charts of the independent SUUR manifold. Not 1D continuation."""

    seed = np.zeros(REDUCED_DIM, dtype=float)
    charts: list[ChartRecord] = []
    chart = build_hexagonal_chart(problem, seed, chart_id="suur_chart_000", radius=radius, n_rings=1)
    if chart.accepted:
        charts.append(chart)
    while len(charts) < max_charts:
        frontier = []
        for existing in charts:
            for sample in existing.samples:
                if sample.local_index == 0 or not sample.correction.accepted:
                    continue
                if sample.correction.x is None:
                    continue
                frontier.append(np.asarray(sample.correction.x, dtype=float))
        if not frontier:
            break
        centers = [np.asarray(c.center, dtype=float) for c in charts]

        def _min_d(p: Array) -> float:
            return min(ambient_distance(p, c, problem.periodic_coordinates) for c in centers)

        frontier.sort(key=_min_d)
        cand = frontier[-1]
        if _min_d(cand) <= 0.7 * radius:
            break
        n_ref = np.asarray(charts[-1].tangent_basis, dtype=float).T
        nxt = build_hexagonal_chart(
            problem,
            cand,
            chart_id=f"suur_chart_{len(charts):03d}",
            radius=radius,
            n_rings=1,
            n_ref=n_ref,
        )
        if not nxt.accepted:
            break
        charts.append(nxt)
    return tuple(charts)


@dataclass(frozen=True, slots=True)
class CompoundParentComparison:
    max_closure_residual: float
    max_position_error_m: float
    max_orientation_error_rad: float
    max_pointing_error: float
    max_joint_map_error_rad: float
    source_to_reduced_distance: float
    reduced_to_source_distance: float
    tangent_subspace_error: float
    sample_count: int
    component_correspondence_complete: bool
    joint_limit_correspondence: str
    accepted_local: bool
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_safe(
            {
                "max_closure_residual": self.max_closure_residual,
                "max_position_error_m": self.max_position_error_m,
                "max_orientation_error_rad": self.max_orientation_error_rad,
                "max_pointing_error": self.max_pointing_error,
                "max_joint_map_error_rad": self.max_joint_map_error_rad,
                "source_to_reduced_distance": self.source_to_reduced_distance,
                "reduced_to_source_distance": self.reduced_to_source_distance,
                "tangent_subspace_error": self.tangent_subspace_error,
                "sample_count": self.sample_count,
                "component_correspondence_complete": self.component_correspondence_complete,
                "joint_limit_correspondence": self.joint_limit_correspondence,
                "accepted_local": self.accepted_local,
                "notes": list(self.notes),
            }
        )


def compare_source_and_reduced(
    entry: Spatial5RCorpusEntry,
    problem: ClosedCompoundParentProblem,
    reduced_charts: tuple[ChartRecord, ...],
) -> CompoundParentComparison:
    source_problem = FixedPositionParentProblem.from_model(entry.model, entry.regular_q)
    samples: list[Array] = [np.zeros(REDUCED_DIM, dtype=float)]
    for chart in reduced_charts:
        for sample in chart.samples:
            if sample.correction.accepted and sample.correction.x is not None:
                samples.append(np.asarray(sample.correction.x, dtype=float))
    closures = []
    pos_err = []
    ori_err = []
    pnt_err = []
    joint_err = []
    src_red = []
    red_src = []
    q_seed = np.asarray(entry.regular_q, dtype=float)
    for x in samples[:24]:
        res = problem.residual(x)
        closures.append(float(np.linalg.norm(res)))
        q = np.asarray(problem.physical_q(x), dtype=float)
        state_i = problem.independent_chain.evaluate(tuple(float(v) for v in q))
        state_s = entry.model.chain.evaluate(tuple(float(v) for v in q))
        pos_err.append(float(np.linalg.norm(np.asarray(state_s.p) - np.asarray(problem.p_star))))
        ori_err.append(_rotation_geodesic(np.asarray(state_s.R), np.asarray(state_i.R)))
        pnt_err.append(_pointing_geodesic(np.asarray(state_s.d), np.asarray(state_i.d)))
        mapped = np.asarray(lift_source_to_suur_physical(tuple(float(v) for v in q)), dtype=float)
        expected = q_seed + x[3:8]
        joint_err.append(float(np.linalg.norm(mapped - expected)))
        src_red.append(ambient_distance(q, expected, (True,) * 5))
        red_src.append(ambient_distance(expected, q, (True,) * 5))
    n_src = orthonormal_tangent_basis(source_problem.jacobian(q_seed), expected_nullity=2)
    n_red = orthonormal_tangent_basis(problem.jacobian(np.zeros(REDUCED_DIM)), expected_nullity=2)
    n_red_phys = n_red[3:8, :]
    # Orthonormalize mapped columns for projector comparison.
    q_map, _ = np.linalg.qr(n_red_phys)
    tangent_err = projector_frobenius(n_src, q_map[:, :2])
    max_pos = max(pos_err) if pos_err else float("inf")
    max_cl = max(closures) if closures else float("inf")
    accepted = (
        max_cl <= 1e-6
        and max_pos <= 1e-8
        and max(ori_err) <= ORIENTATION_ERR_TOL
        and max(pnt_err) <= POINTING_ERR_TOL
        and max(joint_err) <= JOINT_MAP_TOL
    )
    return CompoundParentComparison(
        max_closure_residual=max_cl,
        max_position_error_m=max_pos,
        max_orientation_error_rad=max(ori_err) if ori_err else float("inf"),
        max_pointing_error=max(pnt_err) if pnt_err else float("inf"),
        max_joint_map_error_rad=max(joint_err) if joint_err else float("inf"),
        source_to_reduced_distance=max(src_red) if src_red else float("inf"),
        reduced_to_source_distance=max(red_src) if red_src else float("inf"),
        tangent_subspace_error=tangent_err,
        sample_count=len(samples[:24]),
        component_correspondence_complete=False,
        joint_limit_correspondence="not_modeled",
        accepted_local=accepted,
        notes=(
            "Bidirectional sample comparison on a budget-limited atlas is not component completeness.",
            "Independent chain object id differs from the source chain.",
        ),
    )


def issue_suur_certificate(
    entry: Spatial5RCorpusEntry,
    aggregation: MultiAggregationRecord,
    comparison: CompoundParentComparison | None,
) -> DecompositionCertificate:
    posed = pose_fixed_position_problem(entry.model, entry.regular_q)
    jp = position_jacobian(entry.model.chain, entry.regular_q)
    jd = pointing_jacobian(entry.model.chain, entry.regular_q)
    report_p = matrix_rank_report(jp)
    n_p = orthonormal_tangent_basis(jp, expected_nullity=2) if report_p.nullity == 2 else np.zeros((5, 2))
    report_d = matrix_rank_report(jd @ n_p) if n_p.size else matrix_rank_report(np.zeros((3, 2)))
    kinds, roles = aggregation.joint_kind_sequence, aggregation.joint_role_sequence
    if "U_v" in roles:
        raise ValueError("U_v is forbidden on SUUR certificates")
    rank_checks = {
        "rank_jp": report_p.rank,
        "nullity_jp": report_p.nullity,
        "rank_jd_np": report_d.rank,
        "p_star": list(posed.p_star),
    }
    axis_status = aggregation.axis_aggregation_status
    if axis_status != "EXACT_GLOBAL" or comparison is None:
        closed = "REJECTED"
        status = "REJECTED"
        reason = "SUUR closed parent is not issued without exact two-pair aggregation and a local comparison."
        if axis_status != "EXACT_GLOBAL":
            reason = "Near or unstructured source: exact two-pair U_phys aggregation rejected."
        return DecompositionCertificate(
            source_chain_id=entry.model.architecture_id,
            fixed_position_problem_id=f"{entry.model.architecture_id}_pstar",
            source_component_id=f"{entry.model.architecture_id}_component_seed0",
            source_mobility=2,
            joint_kind_sequence=kinds,
            joint_role_sequence=roles,
            cyclic_origin_role="S_v",
            designated_task_joint_role="tool_frame",
            reduction_operations=("axis_aggregation", "closed_mechanism_decomposition"),
            reduced_topology=aggregation.family_label,
            coordinate_map="physical deltas of U1,U2,R plus S_v chart; identity on 5R joints",
            inverse_or_reconstruction_map="physical 5-vector embeds to source q; S_v tracks R(q)",
            task_map="tool orientation and pointing on p(q)=p*",
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
            closed_mechanism_status=closed,
            status=status,
            failure_or_scope_reason=reason,
            candidates=aggregation.candidates,
            aggregated=None,
            evidence={"multi_aggregation": aggregation.to_json_dict()},
        )
    closed = "LOCAL_ONLY" if comparison.accepted_local else "REJECTED"
    status = closed
    reason = (
        "Independent SUUR parent matches the source locally on a budget-limited atlas. "
        "component_correspondence_complete is false; not EXACT_ON_COMPONENT."
        if comparison.accepted_local
        else f"Local SUUR/source comparison failed (closure={comparison.max_closure_residual:.3e})."
    )
    return DecompositionCertificate(
        source_chain_id=entry.model.architecture_id,
        fixed_position_problem_id=f"{entry.model.architecture_id}_pstar",
        source_component_id=f"{entry.model.architecture_id}_component_seed0",
        source_mobility=2,
        joint_kind_sequence=kinds,
        joint_role_sequence=roles,
        cyclic_origin_role="S_v",
        designated_task_joint_role="tool_frame",
        reduction_operations=("axis_aggregation", "closed_mechanism_decomposition"),
        reduced_topology=aggregation.family_label,
        coordinate_map="physical deltas of U1,U2,R plus S_v chart; identity on 5R joints",
        inverse_or_reconstruction_map="physical 5-vector embeds to source q; S_v tracks R(q)",
        task_map="tool orientation and pointing on p(q)=p*",
        rank_and_nullity_checks=rank_checks,
        coordinate_regrouping_residuals=aggregation.fk_identity_residuals,
        closure_residuals={"max_closure_residual": comparison.max_closure_residual},
        tangent_subspace_error=comparison.tangent_subspace_error,
        trajectory_position_error_m=comparison.max_position_error_m,
        trajectory_pointing_error=comparison.max_pointing_error,
        trajectory_joint_map_error_rad=comparison.max_joint_map_error_rad,
        component_correspondence="local_on_budget_limited_atlas",
        joint_limit_correspondence="not_modeled",
        axis_aggregation_status="EXACT_GLOBAL",
        closed_mechanism_status=closed,
        status=status,
        failure_or_scope_reason=reason,
        candidates=aggregation.candidates,
        aggregated=None,
        evidence={
            "multi_aggregation": aggregation.to_json_dict(),
            "comparison": comparison.to_json_dict(),
            "independent_chain_distinct": True,
            "component_correspondence_complete": False,
        },
    )


@dataclass(frozen=True, slots=True)
class V06BArchitectureResult:
    architecture_id: str
    aggregation: MultiAggregationRecord
    certificate: DecompositionCertificate
    comparison: CompoundParentComparison | None
    reduced_chart_count: int
    source_chart_count: int
    seed_closure_residual: float | None
    independent_chain_id: int | None
    source_chain_id: int

    def to_json_dict(self) -> dict[str, Any]:
        return _json_safe(
            {
                "architecture_id": self.architecture_id,
                "aggregation": self.aggregation.to_json_dict(),
                "certificate": self.certificate.to_json_dict(),
                "comparison": None if self.comparison is None else self.comparison.to_json_dict(),
                "reduced_chart_count": self.reduced_chart_count,
                "source_chart_count": self.source_chart_count,
                "seed_closure_residual": self.seed_closure_residual,
                "independent_chain_id": self.independent_chain_id,
                "source_chain_id": self.source_chain_id,
            }
        )


def evaluate_v06b_architecture(
    entry: Spatial5RCorpusEntry,
    *,
    grow_atlases: bool = True,
    max_charts: int = 6,
) -> V06BArchitectureResult:
    aggregation = build_suur_multi_aggregation(entry.model, entry.regular_q)
    source_charts = 0
    reduced_charts: tuple[ChartRecord, ...] = ()
    comparison = None
    seed_res = None
    independent_id = None
    if aggregation.axis_aggregation_status == "EXACT_GLOBAL":
        problem = ClosedCompoundParentProblem.from_entry(entry)
        independent_id = id(problem.independent_chain)
        seed_res = float(np.linalg.norm(problem.residual(np.zeros(REDUCED_DIM))))
        if grow_atlases:
            source = build_generic_5r_parent_atlas(
                entry, max_charts=max_charts, discovery_bank=8, confirmation_bank=8
            )
            source_charts = len(source.charts)
            reduced_charts = grow_compound_parent_atlas(problem, max_charts=max_charts)
        comparison = compare_source_and_reduced(entry, problem, reduced_charts)
    certificate = issue_suur_certificate(entry, aggregation, comparison)
    return V06BArchitectureResult(
        architecture_id=entry.model.architecture_id,
        aggregation=aggregation,
        certificate=certificate,
        comparison=comparison,
        reduced_chart_count=len(reduced_charts),
        source_chart_count=source_charts,
        seed_closure_residual=seed_res,
        independent_chain_id=independent_id,
        source_chain_id=id(entry.model.chain),
    )


def v06b_program_summary(*, grow_atlases: bool = False) -> dict[str, Any]:
    generic = evaluate_v06b_architecture(build_generic_5r(), grow_atlases=False)
    near = evaluate_v06b_architecture(build_near_two_u_5r(), grow_atlases=False)
    exact = evaluate_v06b_architecture(build_exact_two_u_5r(), grow_atlases=grow_atlases, max_charts=6)
    return {
        "generic_5r": generic.to_json_dict(),
        "near_two_u_5r": near.to_json_dict(),
        "exact_two_u_5r": exact.to_json_dict(),
        "notes": [
            "V06B SUUR parent is not UUUR and not U_v.",
            "Exact two-pair aggregation may be EXACT_GLOBAL while closed status stays LOCAL_ONLY.",
        ],
    }
