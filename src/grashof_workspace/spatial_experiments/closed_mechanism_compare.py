"""Independent continuation and source-fiber comparison for V05 closed mechanisms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial4bar_explorer.closure import (
    closure_jacobian,
    null_tangent,
)
from grashof_workspace.spatial4bar_explorer.continuation import continue_branch
from grashof_workspace.spatial_experiments.closed_mechanism_sv_uphys import (
    PHYSICAL_COORD_COUNT,
    IndependentClosedMechanism,
)
from grashof_workspace.spatial_experiments.fixed_position import fixed_position_tangent
from grashof_workspace.spatial_experiments.fixed_position_continuation import (
    FixedPositionFiberResult,
    continue_fixed_position_fiber,
)
from grashof_workspace.spatial_experiments.open_chain import OpenChainModel

Array = NDArray[np.floating]

CLOSURE_TOL = 1e-8
POSITION_TOL_M = 1e-9
POINTING_TOL = 5e-2
TANGENT_ALIGN_TOL = 1e-6
MIN_COMPARE_SAMPLES = 8

ComparisonMode = Literal["independent_closed_loop", "identity_same_chain"]


@dataclass(frozen=True, slots=True)
class ClosedMechanismComparison:
    """Numeric comparison of an independent reduced loop against a source fiber."""

    architecture_id: str
    component_id: str
    comparison_mode: ComparisonMode
    independent_reduced_solve_present: bool
    scope: str
    source_branch_status: str
    source_returned: bool
    reduced_step_count: int
    source_sample_count: int
    max_closure_residual: float
    max_position_error_m: float
    max_pointing_error: float
    max_joint_map_error_rad: float | None
    seed_tangent_misalignment: float
    accepted: bool
    failure_or_scope_reason: str
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "component_id": self.component_id,
            "comparison_mode": self.comparison_mode,
            "independent_reduced_solve_present": self.independent_reduced_solve_present,
            "scope": self.scope,
            "source_branch_status": self.source_branch_status,
            "source_returned": self.source_returned,
            "reduced_step_count": self.reduced_step_count,
            "source_sample_count": self.source_sample_count,
            "max_closure_residual": self.max_closure_residual,
            "max_position_error_m": self.max_position_error_m,
            "max_pointing_error": self.max_pointing_error,
            "max_joint_map_error_rad": self.max_joint_map_error_rad,
            "seed_tangent_misalignment": self.seed_tangent_misalignment,
            "accepted": self.accepted,
            "failure_or_scope_reason": self.failure_or_scope_reason,
            "notes": list(self.notes),
        }


def _seed_tangent_misalignment(
    mechanism: IndependentClosedMechanism,
    model: OpenChainModel,
) -> float:
    q0 = np.asarray(mechanism.q_seed_reduced, dtype=float)
    jacobian = closure_jacobian(mechanism.geometry, q0)
    reduced_tangent, _ = null_tangent(jacobian)
    physical = np.asarray(reduced_tangent[:PHYSICAL_COORD_COUNT], dtype=float)
    physical_norm = float(np.linalg.norm(physical))
    if physical_norm <= 1e-15:
        return 1.0
    physical = physical / physical_norm
    source = np.asarray(
        fixed_position_tangent(model.chain, mechanism.q_seed_source),
        dtype=float,
    )
    source = source / float(np.linalg.norm(source))
    return float(1.0 - abs(float(np.dot(physical, source))))


def compare_independent_closed_mechanism(
    model: OpenChainModel,
    mechanism: IndependentClosedMechanism,
    *,
    source_fiber: FixedPositionFiberResult | None = None,
    n_steps: int = 40,
    step_size: float = 0.03,
    closure_tol: float = CLOSURE_TOL,
    position_tol_m: float = POSITION_TOL_M,
    pointing_tol: float = POINTING_TOL,
    tangent_tol: float = TANGENT_ALIGN_TOL,
) -> ClosedMechanismComparison:
    """Continue the independent loop and compare it to the source fiber component."""

    if mechanism.architecture_id != model.architecture_id:
        raise ValueError("mechanism/source architecture mismatch")
    if id(mechanism.geometry) == id(model.chain):
        raise ValueError("refusing identity-on-same-chain comparison")

    fiber = source_fiber or continue_fixed_position_fiber(
        model,
        mechanism.q_seed_source,
        n_steps=n_steps,
        step_size=step_size,
        component_id=mechanism.component_id,
    )
    reduced_trace = continue_branch(
        mechanism.geometry,
        step_size=step_size,
        steps=n_steps,
        direction=1,
    )

    fiber_pointings = [
        np.asarray(sample.d, dtype=float)
        for sample in fiber.accepted_samples
        if sample.d is not None
    ]
    if not fiber_pointings:
        return ClosedMechanismComparison(
            architecture_id=mechanism.architecture_id,
            component_id=mechanism.component_id,
            comparison_mode="independent_closed_loop",
            independent_reduced_solve_present=True,
            scope="rejected_empty_source_fiber",
            source_branch_status=fiber.branch_status,
            source_returned=fiber.returned,
            reduced_step_count=len(reduced_trace.points),
            source_sample_count=0,
            max_closure_residual=float("inf"),
            max_position_error_m=float("inf"),
            max_pointing_error=float("inf"),
            max_joint_map_error_rad=None,
            seed_tangent_misalignment=1.0,
            accepted=False,
            failure_or_scope_reason="source fiber produced no accepted pointing samples",
        )

    p_star = np.asarray(mechanism.p_star, dtype=float)
    closure_errors: list[float] = []
    position_errors: list[float] = []
    pointing_errors: list[float] = []
    for point in reduced_trace.points:
        if not point.converged:
            continue
        closure_errors.append(float(point.closure_norm))
        q_source = mechanism.source_q_from_reduced(point.q)
        state = model.chain.evaluate(q_source)
        position_errors.append(float(np.linalg.norm(state.p - p_star)))
        pointing_errors.append(
            min(float(np.linalg.norm(state.d - fiber_d)) for fiber_d in fiber_pointings)
        )

    if len(closure_errors) < MIN_COMPARE_SAMPLES:
        return ClosedMechanismComparison(
            architecture_id=mechanism.architecture_id,
            component_id=mechanism.component_id,
            comparison_mode="independent_closed_loop",
            independent_reduced_solve_present=True,
            scope="rejected_insufficient_reduced_samples",
            source_branch_status=fiber.branch_status,
            source_returned=fiber.returned,
            reduced_step_count=len(reduced_trace.points),
            source_sample_count=len(fiber.accepted_samples),
            max_closure_residual=max(closure_errors) if closure_errors else float("inf"),
            max_position_error_m=max(position_errors) if position_errors else float("inf"),
            max_pointing_error=max(pointing_errors) if pointing_errors else float("inf"),
            max_joint_map_error_rad=None,
            seed_tangent_misalignment=_seed_tangent_misalignment(mechanism, model),
            accepted=False,
            failure_or_scope_reason=(
                f"need at least {MIN_COMPARE_SAMPLES} converged reduced samples"
            ),
        )

    max_closure = max(closure_errors)
    max_position = max(position_errors)
    max_pointing = max(pointing_errors)
    tangent_mis = _seed_tangent_misalignment(mechanism, model)

    if fiber.returned:
        scope = "returned_component"
    else:
        scope = f"open_budget_{n_steps}"

    accepted = (
        max_closure <= closure_tol
        and max_position <= position_tol_m
        and max_pointing <= pointing_tol
        and tangent_mis <= tangent_tol
        and reduced_trace.converged_fraction >= 0.95
    )
    if accepted:
        reason = (
            f"Independent closed loop matches the scoped source component "
            f"({scope}): closure≤{closure_tol}, position≤{position_tol_m}, "
            f"pointing≤{pointing_tol}, seed tangent misalignment≤{tangent_tol}."
        )
    else:
        reason = (
            "Independent closed-loop comparison failed tolerance checks: "
            f"closure={max_closure}, position={max_position}, "
            f"pointing={max_pointing}, tangent_misalignment={tangent_mis}, "
            f"scope={scope}."
        )

    return ClosedMechanismComparison(
        architecture_id=mechanism.architecture_id,
        component_id=mechanism.component_id,
        comparison_mode="independent_closed_loop",
        independent_reduced_solve_present=True,
        scope=scope,
        source_branch_status=fiber.branch_status,
        source_returned=fiber.returned,
        reduced_step_count=len(reduced_trace.points),
        source_sample_count=len(fiber.accepted_samples),
        max_closure_residual=max_closure,
        max_position_error_m=max_position,
        max_pointing_error=max_pointing,
        max_joint_map_error_rad=None,
        seed_tangent_misalignment=tangent_mis,
        accepted=accepted,
        failure_or_scope_reason=reason,
        notes=(
            "Physical reduced angles are seed deltas mapped to source joint space.",
            "Pointing error is nearest-neighbor distance into the source fiber image.",
            "Explorer tool_alpha/tool_beta labels are not used as V05 task evidence.",
            *mechanism.notes,
        ),
    )


def forged_identity_comparison(
    mechanism: IndependentClosedMechanism,
) -> ClosedMechanismComparison:
    """Diagnostic object that must never promote a closed-mechanism certificate."""

    return ClosedMechanismComparison(
        architecture_id=mechanism.architecture_id,
        component_id=mechanism.component_id,
        comparison_mode="identity_same_chain",
        independent_reduced_solve_present=False,
        scope="forged_identity",
        source_branch_status="n/a",
        source_returned=False,
        reduced_step_count=0,
        source_sample_count=0,
        max_closure_residual=0.0,
        max_position_error_m=0.0,
        max_pointing_error=0.0,
        max_joint_map_error_rad=0.0,
        seed_tangent_misalignment=0.0,
        accepted=False,
        failure_or_scope_reason=(
            "Identity-on-same-chain residuals are coordinate-regrouping diagnostics only "
            "and cannot promote closed_mechanism_status."
        ),
        notes=("ADR-021 / audit F-03 false-pass guard.",),
    )
