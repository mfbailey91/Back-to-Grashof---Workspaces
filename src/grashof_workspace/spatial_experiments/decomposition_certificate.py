"""Certificates for V05 axis aggregation and closed-mechanism decomposition.

The audit requires two claims to remain separate:

1. ``RR → U_phys`` may be an exact global regrouping of two consecutive
   physical revolute coordinates;
2. an independently instantiated ``S_v-U_phys-R-R`` closed mechanism may or
   may not reproduce a complete fixed-position source component.

V05 now certifies claim (1) and leaves claim (2) ``UNRESOLVED`` until the
reduced closure is built and continued independently.  Identity comparisons of
a serial chain with itself are retained only as coordinate-regrouping
sanity diagnostics and cannot promote the closed-mechanism status.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .axis_aggregation import (
    ORTHOGONALITY_DOT_TOL,
    PAIR_DISTANCE_TOL_M,
    PARALLEL_CROSS_TOL,
    AggregatedMechanismModel,
    AggregationCandidate,
    build_aggregated_mechanism,
    detect_exact_u_pairs,
    fk_identity_residuals,
)
from .fixed_position import audit_fixed_position_seed, pose_fixed_position_problem
from .open_chain import OpenChainModel

CERTIFICATE_STATUSES = (
    "EXACT_GLOBAL",
    "EXACT_ON_COMPONENT",
    "LOCAL_ONLY",
    "APPROXIMATE",
    "REJECTED",
    "UNRESOLVED",
)


@dataclass(frozen=True, slots=True)
class DecompositionCertificate:
    """Provenance record for source→reduced claims.

    ``status`` is the overall closed-mechanism decomposition disposition.
    ``axis_aggregation_status`` reports the narrower physical-axis regrouping.
    """

    source_chain_id: str
    fixed_position_problem_id: str
    source_component_id: str
    source_mobility: int
    joint_kind_sequence: tuple[str, ...]
    joint_role_sequence: tuple[str, ...]
    cyclic_origin_role: str
    designated_task_joint_role: str
    reduction_operations: tuple[str, ...]
    reduced_topology: str
    coordinate_map: str
    inverse_or_reconstruction_map: str
    task_map: str
    rank_and_nullity_checks: dict[str, Any]
    coordinate_regrouping_residuals: dict[str, float]
    closure_residuals: dict[str, float]
    tangent_subspace_error: float | None
    trajectory_position_error_m: float | None
    trajectory_pointing_error: float | None
    trajectory_joint_map_error_rad: float | None
    component_correspondence: str
    joint_limit_correspondence: str
    axis_aggregation_status: str
    closed_mechanism_status: str
    status: str
    failure_or_scope_reason: str
    candidates: tuple[AggregationCandidate, ...]
    aggregated: AggregatedMechanismModel | None
    evidence: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
        """Return strict-JSON-compatible data; unresolved numbers use ``None``."""
        return {
            "source_chain_id": self.source_chain_id,
            "fixed_position_problem_id": self.fixed_position_problem_id,
            "source_component_id": self.source_component_id,
            "source_mobility": self.source_mobility,
            "joint_kind_sequence": list(self.joint_kind_sequence),
            "joint_role_sequence": list(self.joint_role_sequence),
            "cyclic_origin_role": self.cyclic_origin_role,
            "designated_task_joint_role": self.designated_task_joint_role,
            "reduction_operations": list(self.reduction_operations),
            "reduced_topology": self.reduced_topology,
            "coordinate_map": self.coordinate_map,
            "inverse_or_reconstruction_map": self.inverse_or_reconstruction_map,
            "task_map": self.task_map,
            "rank_and_nullity_checks": self.rank_and_nullity_checks,
            "coordinate_regrouping_residuals": self.coordinate_regrouping_residuals,
            "closure_residuals": self.closure_residuals,
            "tangent_subspace_error": self.tangent_subspace_error,
            "trajectory_position_error_m": self.trajectory_position_error_m,
            "trajectory_pointing_error": self.trajectory_pointing_error,
            "trajectory_joint_map_error_rad": self.trajectory_joint_map_error_rad,
            "component_correspondence": self.component_correspondence,
            "joint_limit_correspondence": self.joint_limit_correspondence,
            "axis_aggregation_status": self.axis_aggregation_status,
            "closed_mechanism_status": self.closed_mechanism_status,
            "status": self.status,
            "failure_or_scope_reason": self.failure_or_scope_reason,
            "candidates": [candidate.to_json_dict() for candidate in self.candidates],
            "aggregated": None if self.aggregated is None else self.aggregated.to_json_dict(),
            "evidence": self.evidence,
        }


def _best_exact_candidate(
    candidates: tuple[AggregationCandidate, ...],
) -> AggregationCandidate | None:
    exact = sorted(
        (candidate for candidate in candidates if candidate.exact_u_candidate),
        key=lambda candidate: candidate.pair_index,
    )
    return exact[0] if exact else None


def issue_axis_aggregation_certificate(
    model: OpenChainModel,
    q0: tuple[float, ...],
    *,
    n_fiber_steps: int = 24,
    fiber_step_size: float = 0.04,
    distance_tol_m: float = PAIR_DISTANCE_TOL_M,
    parallel_tol: float = PARALLEL_CROSS_TOL,
    orthogonality_tol: float = ORTHOGONALITY_DOT_TOL,
) -> DecompositionCertificate:
    """Certify exact axis regrouping without overstating loop equivalence.

    ``n_fiber_steps`` and ``fiber_step_size`` are accepted for API compatibility
    but are not used to promote the certificate.  Independent reduced-closure
    continuation is a separate implementation gate.
    """
    _ = (n_fiber_steps, fiber_step_size)
    problem = pose_fixed_position_problem(model, q0)
    seed_audit = audit_fixed_position_seed(problem)
    home_candidates = detect_exact_u_pairs(
        model,
        q=None,
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    seed_candidates = detect_exact_u_pairs(
        model,
        q=q0,
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    candidate = _best_exact_candidate(home_candidates)

    base_kinds = ("S_v",) + model.joint_kind_sequence
    base_roles = ("S_v",) + model.joint_role_sequence
    problem_id = f"{model.architecture_id}_pstar"
    component_id = f"{model.architecture_id}_component0"
    rank_checks = {
        "rank_jp": seed_audit.rank_jp,
        "nullity_jp": seed_audit.nullity_jp,
        "regular": seed_audit.regular,
        "seed_status": seed_audit.status,
        "motion_signature": seed_audit.motion_signature,
        "finite_difference_jp_error_fro": seed_audit.finite_difference_jp_error_fro,
        "finite_difference_verified": seed_audit.finite_difference_verified,
        "p_star": list(problem.p_star),
    }

    if candidate is None:
        best = min(
            home_candidates,
            key=lambda item: (item.distance_m, item.orthogonality_abs_dot),
        )
        return DecompositionCertificate(
            source_chain_id=model.architecture_id,
            fixed_position_problem_id=problem_id,
            source_component_id=component_id,
            source_mobility=max(0, seed_audit.nullity_jp),
            joint_kind_sequence=base_kinds,
            joint_role_sequence=base_roles,
            cyclic_origin_role="S_v",
            designated_task_joint_role="tool_frame",
            reduction_operations=("axis_aggregation",),
            reduced_topology="none",
            coordinate_map="none",
            inverse_or_reconstruction_map="none",
            task_map="tool orientation R(q) on p(q)=p*",
            rank_and_nullity_checks=rank_checks,
            coordinate_regrouping_residuals={
                "best_pair_distance_m": best.distance_m,
                "best_pair_orthogonality_abs_dot": best.orthogonality_abs_dot,
                "best_pair_parallelism_residual": best.parallelism_residual,
            },
            closure_residuals={},
            tangent_subspace_error=None,
            trajectory_position_error_m=None,
            trajectory_pointing_error=None,
            trajectory_joint_map_error_rad=None,
            component_correspondence="not_applicable",
            joint_limit_correspondence="not_modeled",
            axis_aggregation_status="REJECTED",
            closed_mechanism_status="UNRESOLVED",
            status="REJECTED",
            failure_or_scope_reason=(
                "No consecutive exact intersecting orthogonal RR pair; "
                "there is no exact U_phys aggregation candidate."
            ),
            candidates=home_candidates,
            aggregated=None,
            evidence={
                "home_candidates": [candidate.to_json_dict() for candidate in home_candidates],
                "seed_candidates": [candidate.to_json_dict() for candidate in seed_candidates],
            },
        )

    aggregated = build_aggregated_mechanism(model, candidate)
    regrouping_residuals: dict[str, float] = {}
    if candidate.pair_index == 0:
        regrouping_residuals = fk_identity_residuals(aggregated, q0)

    topology = aggregated.family_label
    reason = (
        "Exact global physical-axis regrouping is established for the consecutive RR pair. "
        "Independent closed-loop construction, continuation, tangent comparison, and complete "
        "component correspondence have not yet been performed; the closed-mechanism "
        "decomposition therefore remains UNRESOLVED."
    )
    return DecompositionCertificate(
        source_chain_id=model.architecture_id,
        fixed_position_problem_id=problem_id,
        source_component_id=component_id,
        source_mobility=max(0, seed_audit.nullity_jp),
        joint_kind_sequence=aggregated.joint_kind_sequence,
        joint_role_sequence=aggregated.joint_role_sequence,
        cyclic_origin_role="S_v",
        designated_task_joint_role="tool_frame",
        reduction_operations=("axis_aggregation", "closed_mechanism_decomposition"),
        reduced_topology=topology,
        coordinate_map=(
            "exact scalar regrouping of consecutive physical RR coordinates as ordered U_phys"
        ),
        inverse_or_reconstruction_map="identity scalar-coordinate expansion for axis regrouping",
        task_map="tool orientation R(q) on p(q)=p*",
        rank_and_nullity_checks=rank_checks,
        coordinate_regrouping_residuals=regrouping_residuals,
        closure_residuals={},
        tangent_subspace_error=None,
        trajectory_position_error_m=None,
        trajectory_pointing_error=None,
        trajectory_joint_map_error_rad=None,
        component_correspondence="not_evaluated_with_independent_reduced_mechanism",
        joint_limit_correspondence=(
            "not_modeled; exact regrouping assumes original coordinate order and identical limits"
        ),
        axis_aggregation_status="EXACT_GLOBAL",
        closed_mechanism_status="UNRESOLVED",
        status="UNRESOLVED",
        failure_or_scope_reason=reason,
        candidates=home_candidates,
        aggregated=aggregated,
        evidence={
            "home_candidates": [item.to_json_dict() for item in home_candidates],
            "seed_candidates": [item.to_json_dict() for item in seed_candidates],
            "coordinate_regrouping_diagnostic_only": regrouping_residuals,
            "independent_reduced_solve_present": False,
            "roles_guard": {
                "has_S_v": "S_v" in aggregated.joint_role_sequence,
                "has_U_phys": "U_phys" in aggregated.joint_role_sequence,
                "forbids_U_v": "U_v" not in aggregated.joint_role_sequence,
                "designated_task_is_not_U_phys": True,
            },
        },
    )
