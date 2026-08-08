"""DecompositionCertificate issuer for exact axis aggregation (V05D).

Statuses follow ADR-012 / ``docs/DECISIONS.md``::

    EXACT_GLOBAL | EXACT_ON_COMPONENT | LOCAL_ONLY | APPROXIMATE | REJECTED | UNRESOLVED

This MVP issues ``EXACT_ON_COMPONENT`` for a proximal exact ``RR→U`` pair after
FK/tangent/fiber checks on the scoped ±-ray component. Multi-component
completeness remains **unverified**, so ``EXACT_GLOBAL`` is not claimed.
``generic_4r`` yields ``REJECTED`` with geometric residuals recorded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

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
from .fixed_position import fixed_position_tangent, pose_fixed_position_problem
from .fixed_position_continuation import continue_fixed_position_fiber
from .open_chain import OpenChainModel

CERTIFICATE_STATUSES = (
    "EXACT_GLOBAL",
    "EXACT_ON_COMPONENT",
    "LOCAL_ONLY",
    "APPROXIMATE",
    "REJECTED",
    "UNRESOLVED",
)

FK_POSITION_TOL_M = 1e-12
FK_ROTATION_TOL = 1e-12
TANGENT_AGREEMENT_TOL = 1e-10
FIBER_POSITION_TOL_M = 1e-9
FIBER_POINTING_TOL = 1e-9


@dataclass(frozen=True, slots=True)
class DecompositionCertificate:
    """Provenance record for one proposed source→reduced mapping."""

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
    closure_residuals: dict[str, float]
    tangent_subspace_error: float
    trajectory_reconstruction_error: float
    component_correspondence: str
    joint_limit_correspondence: str
    status: str
    failure_or_scope_reason: str
    candidates: tuple[AggregationCandidate, ...]
    aggregated: AggregatedMechanismModel | None
    evidence: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
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
            "closure_residuals": self.closure_residuals,
            "tangent_subspace_error": self.tangent_subspace_error,
            "trajectory_reconstruction_error": self.trajectory_reconstruction_error,
            "component_correspondence": self.component_correspondence,
            "joint_limit_correspondence": self.joint_limit_correspondence,
            "status": self.status,
            "failure_or_scope_reason": self.failure_or_scope_reason,
            "candidates": [c.to_json_dict() for c in self.candidates],
            "aggregated": None if self.aggregated is None else self.aggregated.to_json_dict(),
            "evidence": self.evidence,
        }


def _best_exact_candidate(
    candidates: tuple[AggregationCandidate, ...],
) -> AggregationCandidate | None:
    exact = [c for c in candidates if c.exact_u_candidate]
    if not exact:
        return None
    exact.sort(key=lambda c: c.pair_index)
    return exact[0]


def _tangent_agreement(
    aggregated: AggregatedMechanismModel,
    q0: tuple[float, ...],
) -> float:
    """Identity chart: reduced and source share the same J_p null tangent."""
    t_source = fixed_position_tangent(aggregated.chain, q0)
    q_red = aggregated.lift_source_to_reduced(q0)
    q_emb = aggregated.embed_reduced_to_source(q_red)
    t_reduced = fixed_position_tangent(aggregated.chain, q_emb)
    return float(min(np.linalg.norm(t_source - t_reduced), np.linalg.norm(t_source + t_reduced)))


def _fiber_compare(
    model: OpenChainModel,
    aggregated: AggregatedMechanismModel,
    q0: tuple[float, ...],
    *,
    n_steps: int,
    step_size: float,
) -> dict[str, Any]:
    fiber = continue_fixed_position_fiber(
        model,
        q0,
        n_steps=n_steps,
        step_size=step_size,
        component_id=f"{model.architecture_id}_agg_component0",
    )
    p_star = np.asarray(fiber.p_star, dtype=float)
    max_p = 0.0
    max_pointing = 0.0
    max_map = 0.0
    n_ok = 0
    for step in fiber.accepted_samples:
        if step.q is None:
            continue
        q_s = step.q
        q_r = aggregated.lift_source_to_reduced(q_s)
        q_e = aggregated.embed_reduced_to_source(q_r)
        max_map = max(max_map, float(np.linalg.norm(np.asarray(q_s) - np.asarray(q_e))))
        state_s = aggregated.chain.evaluate(q_s)
        state_r = aggregated.chain.evaluate(q_e)
        max_p = max(max_p, float(np.linalg.norm(state_s.p - p_star)))
        max_p = max(max_p, float(np.linalg.norm(state_r.p - p_star)))
        max_pointing = max(max_pointing, float(np.linalg.norm(state_s.d - state_r.d)))
        n_ok += 1
    return {
        "fiber": fiber,
        "accepted_samples": n_ok,
        "branch_status": fiber.branch_status,
        "max_position_residual_m": max_p,
        "max_pointing_residual": max_pointing,
        "max_joint_map_residual": max_map,
        "seed_rank": fiber.seed_audit.rank_jp,
        "seed_nullity": fiber.seed_audit.nullity_jp,
        "seed_regular": fiber.seed_audit.regular,
    }


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
    """Detect exact RR→U aggregation and certify the proximal chart when present."""
    problem = pose_fixed_position_problem(model, q0)
    home_cands = detect_exact_u_pairs(
        model,
        q=None,
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    seed_cands = detect_exact_u_pairs(
        model,
        q=q0,
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    candidate = _best_exact_candidate(home_cands) or _best_exact_candidate(seed_cands)

    base_kinds = ("S_v",) + model.joint_kind_sequence
    base_roles = ("S_v",) + model.joint_role_sequence
    problem_id = f"{model.architecture_id}_pstar"
    component_id = f"{model.architecture_id}_component0"

    if candidate is None:
        best = min(home_cands, key=lambda c: (c.distance_m, c.orthogonality_abs_dot))
        return DecompositionCertificate(
            source_chain_id=model.architecture_id,
            fixed_position_problem_id=problem_id,
            source_component_id=component_id,
            source_mobility=1,
            joint_kind_sequence=base_kinds,
            joint_role_sequence=base_roles,
            cyclic_origin_role="S_v",
            designated_task_joint_role="none",
            reduction_operations=("axis_aggregation",),
            reduced_topology="none",
            coordinate_map="none",
            inverse_or_reconstruction_map="none",
            task_map="p(q)=p*",
            rank_and_nullity_checks={},
            closure_residuals={
                "best_pair_distance_m": best.distance_m,
                "best_pair_orthogonality_abs_dot": best.orthogonality_abs_dot,
                "best_pair_parallelism_residual": best.parallelism_residual,
            },
            tangent_subspace_error=float("nan"),
            trajectory_reconstruction_error=float("nan"),
            component_correspondence="none",
            joint_limit_correspondence="not_modeled",
            status="REJECTED",
            failure_or_scope_reason=(
                "No consecutive exact intersecting orthogonal RR pair "
                f"(distance_tol={distance_tol_m}, orthogonality_tol={orthogonality_tol})."
            ),
            candidates=home_cands,
            aggregated=None,
            evidence={
                "home_candidates": [c.to_json_dict() for c in home_cands],
                "seed_candidates": [c.to_json_dict() for c in seed_cands],
            },
        )

    if candidate.pair_index != 0:
        return DecompositionCertificate(
            source_chain_id=model.architecture_id,
            fixed_position_problem_id=problem_id,
            source_component_id=component_id,
            source_mobility=1,
            joint_kind_sequence=base_kinds,
            joint_role_sequence=base_roles,
            cyclic_origin_role="S_v",
            designated_task_joint_role="none",
            reduction_operations=("axis_aggregation",),
            reduced_topology=f"pair_{candidate.pair_index}",
            coordinate_map="unverified_non_proximal",
            inverse_or_reconstruction_map="unverified_non_proximal",
            task_map="p(q)=p*",
            rank_and_nullity_checks={},
            closure_residuals={
                "pair_distance_m": candidate.distance_m,
                "orthogonality_abs_dot": candidate.orthogonality_abs_dot,
            },
            tangent_subspace_error=float("nan"),
            trajectory_reconstruction_error=float("nan"),
            component_correspondence="unverified",
            joint_limit_correspondence="not_modeled",
            status="UNRESOLVED",
            failure_or_scope_reason=(
                "Exact U candidate found at non-proximal pair; "
                "S_v-U_phys-R-R embedding MVP only supports pair_index=0."
            ),
            candidates=home_cands,
            aggregated=None,
            evidence={"candidate": candidate.to_json_dict()},
        )

    aggregated = build_aggregated_mechanism(model, candidate)
    fk = fk_identity_residuals(aggregated, q0)
    tangent_err = _tangent_agreement(aggregated, q0)

    fiber_info = _fiber_compare(
        model,
        aggregated,
        q0,
        n_steps=n_fiber_steps,
        step_size=fiber_step_size,
    )
    fiber = fiber_info.pop("fiber")
    traj_err = float(
        max(
            fiber_info["max_position_residual_m"],
            fiber_info["max_pointing_residual"],
            fiber_info["max_joint_map_residual"],
        )
    )

    fk_ok = (
        fk["position_residual_m"] <= FK_POSITION_TOL_M
        and fk["rotation_frobenius"] <= FK_ROTATION_TOL
        and fk["joint_map_residual"] <= FK_POSITION_TOL_M
    )
    tangent_ok = tangent_err <= TANGENT_AGREEMENT_TOL
    fiber_ok = (
        fiber_info["seed_regular"]
        and fiber_info["accepted_samples"] >= 3
        and fiber_info["max_position_residual_m"] <= FIBER_POSITION_TOL_M
        and fiber_info["max_pointing_residual"] <= FIBER_POINTING_TOL
        and fiber_info["max_joint_map_residual"] <= FK_POSITION_TOL_M
    )

    if fk_ok and tangent_ok and fiber_ok:
        status = "EXACT_ON_COMPONENT"
        reason = (
            "Proximal exact RR→U aggregation certified on the scoped ±-ray fiber component. "
            "Multi-component completeness and EXACT_GLOBAL remain unverified."
        )
    elif fk_ok and tangent_ok:
        status = "LOCAL_ONLY"
        reason = (
            "FK/tangent identity holds at the seed, but scoped fiber comparison "
            f"did not meet tolerances (branch={fiber_info['branch_status']})."
        )
    else:
        status = "REJECTED"
        reason = (
            "Exact geometric U candidate failed FK/tangent/fiber residual gates "
            f"(fk_ok={fk_ok}, tangent_ok={tangent_ok}, fiber_ok={fiber_ok})."
        )

    return DecompositionCertificate(
        source_chain_id=model.architecture_id,
        fixed_position_problem_id=problem_id,
        source_component_id=fiber.component_id,
        source_mobility=1 if fiber_info["seed_nullity"] == 1 else fiber_info["seed_nullity"],
        joint_kind_sequence=aggregated.joint_kind_sequence,
        joint_role_sequence=aggregated.joint_role_sequence,
        cyclic_origin_role="S_v",
        designated_task_joint_role="U_phys",
        reduction_operations=("axis_aggregation",),
        reduced_topology=aggregated.family_label,
        coordinate_map="q_source=(α,β,q3,q4)=q_reduced (identity proximal chart)",
        inverse_or_reconstruction_map="identity",
        task_map="p(q)=p*",
        rank_and_nullity_checks={
            "rank_jp": fiber_info["seed_rank"],
            "nullity_jp": fiber_info["seed_nullity"],
            "regular": fiber_info["seed_regular"],
            "p_star": list(problem.p_star),
        },
        closure_residuals=fk,
        tangent_subspace_error=tangent_err,
        trajectory_reconstruction_error=traj_err,
        component_correspondence="scoped_pm_ray_identity_chart",
        joint_limit_correspondence="not_modeled",
        status=status,
        failure_or_scope_reason=reason,
        candidates=home_cands,
        aggregated=aggregated,
        evidence={
            "fk": fk,
            "fiber_compare": fiber_info,
            "home_candidates": [c.to_json_dict() for c in home_cands],
            "seed_candidates": [c.to_json_dict() for c in seed_cands],
            "roles_guard": {
                "has_S_v": "S_v" in aggregated.joint_role_sequence,
                "has_U_phys": "U_phys" in aggregated.joint_role_sequence,
                "forbids_U_v": "U_v" not in aggregated.joint_role_sequence,
                "forbids_tool_a": "tool_a" not in aggregated.joint_role_sequence,
            },
        },
    )
