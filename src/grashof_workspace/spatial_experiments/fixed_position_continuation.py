"""Pseudo-arclength continuation of a one-DOF fixed-position fiber.

Conventions
-----------
Constraint (spatial)::

    F(q) = p(q) - p* = 0 ∈ R^3

For a regular spatial 4R seed, ``rank(J_p)=3`` and ``nullity=1``.  A predictor
alone does not select a unique corrected point because the position equations
contain three constraints in four coordinates.  The corrector therefore solves
the augmented pseudo-arclength system::

    G(q) = [p(q)-p*;
            t_kᵀ(q-q_pred)] = 0

with Newton matrix ``[J_p; t_kᵀ]``.  This prevents the correction from drifting
along the null direction and allows the continuation to pass folds where a
single joint is not a valid global parameter.

No pointing scalar and no terminal-roll freeze are added: those belong to the
later aligned-terminal pointing problem, not the complete 4R source fiber.

Multi-component discovery beyond ± rays from one seed remains unverified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import as_mat3, as_vec3


def _as_int(value: object, default: int = -1) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return default

from .continuation import (
    MAX_CORRECTION_NORM_RAD,
    MAX_CORRECTOR_ITERS,
    MAX_MICROSTEP,
    MAX_STEP_REDUCTIONS,
    POSITION_RESIDUAL_TOL_M,
    wrap_joint_delta,
)
from .fixed_position import (
    FixedPositionSeedAudit,
    audit_fixed_position_seed,
    fixed_position_tangent,
    pose_fixed_position_problem,
)
from .jacobians import matrix_rank_report, position_jacobian
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

Vec = NDArray[np.floating]

CORRECTOR_NEWTON_TOL_M = 1e-13
CORRECTOR_ARCLENGTH_TOL_RAD = 1e-12
FIBER_STEPS = 80
FIBER_STEP_SIZE = 0.04
RETURN_JOINT_TOL_RAD = 0.05
RETURN_TANGENT_TOL = 0.1
RETURN_MIN_ARC_RAD = 0.5
AUGMENTED_CONDITION_LIMIT = 1e12


@dataclass(frozen=True, slots=True)
class FixedPositionStep:
    sigma: float
    path_id: str
    step_index: int
    q_pred: tuple[float, ...] | None
    q: tuple[float, ...] | None
    d: tuple[float, float, float] | None
    R: tuple[tuple[float, float, float], ...] | None
    p_residual_m: float
    arclength_residual_rad: float
    corrector_iterations: int
    correction_norm: float
    actual_step_norm: float
    step_reductions: int
    rank_jp: int
    nullity_jp: int
    tangent_dot: float
    augmented_condition: float
    regular: bool
    label: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class FixedPositionPath:
    path_id: str
    q0: tuple[float, ...]
    p_star: tuple[float, float, float]
    steps: tuple[FixedPositionStep, ...]

    @property
    def accepted(self) -> tuple[FixedPositionStep, ...]:
        return tuple(step for step in self.steps if step.accepted)


@dataclass(frozen=True, slots=True)
class FixedPositionFiberResult:
    """One-seed ±-ray continuation of one fixed-position component."""

    architecture_id: str
    component_id: str
    q0: tuple[float, ...]
    p_star: tuple[float, float, float]
    virtual_closure_kind: str
    seed_audit: FixedPositionSeedAudit
    plus: FixedPositionPath
    minus: FixedPositionPath
    branch_status: str
    returned: bool
    notes: tuple[str, ...]

    @property
    def accepted_samples(self) -> tuple[FixedPositionStep, ...]:
        # Separate rays may contain the same seed.  Deduplicate only by signed
        # continuation coordinate, not by configuration, so genuine returns are
        # retained for return/cycle diagnostics.
        seen: dict[float, FixedPositionStep] = {}
        for path in (self.minus, self.plus):
            for step in path.accepted:
                seen[round(step.sigma, 12)] = step
        return tuple(sorted(seen.values(), key=lambda step: step.sigma))

    def to_json_dict(self) -> dict[str, Any]:
        samples = []
        for step in self.accepted_samples:
            samples.append(
                {
                    "sigma": step.sigma,
                    "path_id": step.path_id,
                    "q": step.q,
                    "d": step.d,
                    "R": step.R,
                    "p_residual_m": step.p_residual_m,
                    "arclength_residual_rad": step.arclength_residual_rad,
                    "actual_step_norm": step.actual_step_norm,
                    "augmented_condition": step.augmented_condition,
                    "rank_jp": step.rank_jp,
                    "nullity_jp": step.nullity_jp,
                    "regular": step.regular,
                    "label": step.label,
                }
            )
        return {
            "architecture_id": self.architecture_id,
            "component_id": self.component_id,
            "q0": self.q0,
            "p_star": self.p_star,
            "virtual_closure_kind": self.virtual_closure_kind,
            "seed_audit": self.seed_audit.to_json_dict(),
            "branch_status": self.branch_status,
            "returned": self.returned,
            "accepted_sample_count": len(samples),
            "accepted_samples": samples,
            "notes": list(self.notes),
            "plus_accepted": len(self.plus.accepted),
            "minus_accepted": len(self.minus.accepted),
        }


def correct_position(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    p_star: Vec,
    *,
    max_iter: int = MAX_CORRECTOR_ITERS,
    tol_m: float = CORRECTOR_NEWTON_TOL_M,
) -> tuple[tuple[float, ...], int, float, float]:
    """Minimum-norm position projection retained for diagnostic callers.

    This function does **not** define the continuation method because three
    position equations do not select a unique point in four joint coordinates.
    Active V05 continuation uses :func:`correct_pseudo_arclength`.
    """
    q_arr = np.asarray(q, dtype=float).copy()
    q_start = q_arr.copy()
    p_target = np.asarray(p_star, dtype=float).reshape(3)
    residual = float("inf")
    iters = 0
    for iters in range(1, max_iter + 1):
        state = chain.evaluate(tuple(float(x) for x in q_arr))
        err = state.p - p_target
        residual = float(np.linalg.norm(err))
        if residual <= tol_m:
            break
        jp = position_jacobian(chain, tuple(float(x) for x in q_arr))
        dq, *_ = np.linalg.lstsq(jp, -err, rcond=None)
        q_arr = q_arr + dq
    else:
        state = chain.evaluate(tuple(float(x) for x in q_arr))
        residual = float(np.linalg.norm(state.p - p_target))
    q_corr = tuple(float(x) for x in q_arr)
    correction_norm = float(np.linalg.norm(wrap_joint_delta(q_corr, q_start)))
    return q_corr, iters, residual, correction_norm


def correct_pseudo_arclength(
    chain: SerialRevoluteChain,
    q_initial: tuple[float, ...] | Vec,
    p_star: Vec,
    q_pred: tuple[float, ...] | Vec,
    tangent: tuple[float, ...] | Vec,
    *,
    max_iter: int = MAX_CORRECTOR_ITERS,
    tol_m: float = CORRECTOR_NEWTON_TOL_M,
    arclength_tol_rad: float = CORRECTOR_ARCLENGTH_TOL_RAD,
) -> tuple[tuple[float, ...], int, float, float, float, float]:
    """Correct a predictor with the augmented pseudo-arclength equations.

    Returns ``(q, iterations, position_residual, arclength_residual,
    correction_norm, max_augmented_condition)``.
    """
    q_arr = np.asarray(q_initial, dtype=float).reshape(-1).copy()
    q_start = q_arr.copy()
    q_pred_arr = np.asarray(q_pred, dtype=float).reshape(-1)
    t_ref = np.asarray(tangent, dtype=float).reshape(-1)
    t_norm = float(np.linalg.norm(t_ref))
    if t_norm <= 0.0:
        raise ValueError("pseudo-arclength tangent must be nonzero")
    t_ref = t_ref / t_norm
    p_target = np.asarray(p_star, dtype=float).reshape(3)

    p_residual = float("inf")
    arc_residual = float("inf")
    max_condition = 0.0
    iters = 0
    for iters in range(1, max_iter + 1):
        q_t = tuple(float(x) for x in q_arr)
        state = chain.evaluate(q_t)
        p_error = state.p - p_target
        arc_error = float(np.dot(t_ref, q_arr - q_pred_arr))
        p_residual = float(np.linalg.norm(p_error))
        arc_residual = abs(arc_error)
        if p_residual <= tol_m and arc_residual <= arclength_tol_rad:
            break
        jp = position_jacobian(chain, q_t)
        augmented = np.vstack((jp, t_ref.reshape(1, -1)))
        condition = float(np.linalg.cond(augmented))
        max_condition = max(max_condition, condition)
        rhs = -np.concatenate((p_error, np.array((arc_error,), dtype=float)))
        dq, *_ = np.linalg.lstsq(augmented, rhs, rcond=None)
        q_arr = q_arr + dq
    else:
        q_t = tuple(float(x) for x in q_arr)
        state = chain.evaluate(q_t)
        p_residual = float(np.linalg.norm(state.p - p_target))
        arc_residual = abs(float(np.dot(t_ref, q_arr - q_pred_arr)))

    q_corr = tuple(float(x) for x in q_arr)
    correction_norm = float(np.linalg.norm(wrap_joint_delta(q_corr, q_start)))
    return (
        q_corr,
        iters,
        p_residual,
        arc_residual,
        correction_norm,
        max_condition,
    )


def _regularity(
    chain: SerialRevoluteChain,
    q: tuple[float, ...],
    p_residual_m: float,
    *,
    position_tol_m: float,
) -> dict[str, object]:
    jp = position_jacobian(chain, q)
    report = matrix_rank_report(jp)
    expected_nullity = chain.n_joints - 3
    regular = (
        report.rank == 3
        and report.nullity == expected_nullity
        and p_residual_m <= position_tol_m
    )
    label = "regular" if regular else ("singular" if report.rank < 3 else "failed")
    return {
        "rank_jp": report.rank,
        "nullity_jp": report.nullity,
        "regular": regular,
        "label": label,
        "singular_values": report.singular_values,
    }


def sequential_fixed_position_step(
    chain: SerialRevoluteChain,
    q_k: tuple[float, ...],
    tangent: Vec,
    dsigma: float,
    p_star: Vec,
    *,
    path_id: str,
    step_index: int,
    sigma0: float,
    sigma_direction: float = 1.0,
    max_reductions: int = MAX_STEP_REDUCTIONS,
    max_iter: int = MAX_CORRECTOR_ITERS,
    max_correction_norm: float = MAX_CORRECTION_NORM_RAD,
    position_tol_m: float = POSITION_RESIDUAL_TOL_M,
    max_microstep: float | None = MAX_MICROSTEP,
) -> tuple[FixedPositionStep | None, Vec, tuple[FixedPositionStep, ...]]:
    """Advance one pseudo-arclength step, halving on failure."""
    if dsigma <= 0.0:
        raise ValueError("dsigma must be positive; reverse the tangent for the minus ray")
    if sigma_direction == 0.0:
        raise ValueError("sigma_direction must be nonzero")

    q_k_arr = np.asarray(q_k, dtype=float).reshape(-1)
    t_start = np.asarray(tangent, dtype=float).reshape(-1)
    rejected: list[FixedPositionStep] = []
    p_target = np.asarray(p_star, dtype=float).reshape(3)

    for reduction in range(max_reductions + 1):
        dsig = float(dsigma) * (0.5**reduction)
        n_micro = 1
        if max_microstep is not None and max_microstep > 0.0 and dsig > max_microstep:
            n_micro = int(np.ceil(dsig / max_microstep))
        q_pred_full = q_k_arr + t_start * dsig
        q_pred_tuple = tuple(float(x) for x in q_pred_full)
        q_cur = q_k_arr.copy()
        t_cur = t_start.copy()
        iters_total = 0
        max_corr = 0.0
        max_arc_residual = 0.0
        max_condition = 0.0
        residual_p = float("inf")
        q_corr = tuple(float(x) for x in q_cur)
        bundle: dict[str, object] = {}
        tangent_dot = 1.0
        failed_label: str | None = None
        actual_step_total = 0.0

        for _micro in range(n_micro):
            du = dsig / float(n_micro)
            q_pred_arr = q_cur + t_cur * du
            (
                q_corr,
                iters,
                residual_p,
                arc_residual,
                corr_norm,
                condition,
            ) = correct_pseudo_arclength(
                chain,
                tuple(float(x) for x in q_pred_arr),
                p_target,
                tuple(float(x) for x in q_pred_arr),
                t_cur,
                max_iter=max_iter,
            )
            iters_total += iters
            max_corr = max(max_corr, corr_norm)
            max_arc_residual = max(max_arc_residual, arc_residual)
            max_condition = max(max_condition, condition)
            state = chain.evaluate(q_corr)
            residual_p = float(np.linalg.norm(state.p - p_target))
            bundle = _regularity(chain, q_corr, residual_p, position_tol_m=position_tol_m)
            if residual_p > position_tol_m or arc_residual > CORRECTOR_ARCLENGTH_TOL_RAD:
                failed_label = "failed_corrector"
                break
            if max_corr > max_correction_norm:
                failed_label = "large_correction"
                break
            if max_condition > AUGMENTED_CONDITION_LIMIT:
                failed_label = "ill_conditioned_corrector"
                break
            if not bool(bundle["regular"]):
                failed_label = str(bundle["label"])
                break
            q_next_arr = np.asarray(q_corr, dtype=float)
            actual_step_total += float(np.linalg.norm(wrap_joint_delta(q_next_arr, q_cur)))
            next_t = fixed_position_tangent(chain, q_corr, previous=t_cur)
            tangent_dot = float(np.dot(t_cur, next_t))
            q_cur = q_next_arr
            t_cur = next_t

        state = chain.evaluate(q_corr)
        signed_actual = float(np.sign(sigma_direction) * actual_step_total)
        step = FixedPositionStep(
            sigma=float(sigma0 + signed_actual),
            path_id=path_id,
            step_index=step_index,
            q_pred=q_pred_tuple,
            q=q_corr if failed_label is None else None,
            d=as_vec3(state.d) if failed_label is None else None,
            R=(
                as_mat3(state.R)
                if failed_label is None
                else None
            ),
            p_residual_m=residual_p,
            arclength_residual_rad=max_arc_residual,
            corrector_iterations=iters_total,
            correction_norm=max_corr,
            actual_step_norm=actual_step_total,
            step_reductions=reduction,
            rank_jp=_as_int(bundle.get("rank_jp"), -1),
            nullity_jp=_as_int(bundle.get("nullity_jp"), -1),
            tangent_dot=tangent_dot,
            augmented_condition=max_condition,
            regular=bool(bundle.get("regular", False)),
            label="accepted" if failed_label is None else failed_label,
            accepted=failed_label is None,
        )
        if step.accepted:
            return step, t_cur, tuple(rejected)
        rejected.append(step)
    return None, t_start, tuple(rejected)


def _seed_step(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    p_star: np.ndarray,
    path_id: str,
    tangent: Vec,
) -> FixedPositionStep:
    state = chain.evaluate(q0)
    report = matrix_rank_report(position_jacobian(chain, q0))
    augmented = np.vstack((position_jacobian(chain, q0), tangent.reshape(1, -1)))
    return FixedPositionStep(
        sigma=0.0,
        path_id=path_id,
        step_index=0,
        q_pred=None,
        q=q0,
        d=as_vec3(state.d),
        R=as_mat3(state.R),
        p_residual_m=float(np.linalg.norm(state.p - p_star)),
        arclength_residual_rad=0.0,
        corrector_iterations=0,
        correction_norm=0.0,
        actual_step_norm=0.0,
        step_reductions=0,
        rank_jp=report.rank,
        nullity_jp=report.nullity,
        tangent_dot=1.0,
        augmented_condition=float(np.linalg.cond(augmented)),
        regular=report.rank == 3 and report.nullity == chain.n_joints - 3,
        label="seed",
        accepted=True,
    )


def continue_fixed_position_ray(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    p_star: tuple[float, float, float] | Vec,
    *,
    direction: float,
    n_steps: int = FIBER_STEPS,
    step_size: float = FIBER_STEP_SIZE,
    seed_tangent: Vec | None = None,
    path_id: str = "+sigma",
    max_microstep: float | None = MAX_MICROSTEP,
) -> tuple[FixedPositionPath, Vec]:
    """Continue one signed ray along the fixed-position fiber.

    The tangent is reversed for the minus ray; the step size remains positive.
    This avoids the prior double-sign reversal that could send both rays in the
    same configuration-space direction.
    """
    if direction == 0.0:
        raise ValueError("direction must be nonzero")
    if n_steps < 0:
        raise ValueError("n_steps must be nonnegative")
    if step_size <= 0.0:
        raise ValueError("step_size must be positive")

    q_cur = tuple(float(x) for x in q0)
    p_arr = np.asarray(p_star, dtype=float).reshape(3)
    reference_tangent = fixed_position_tangent(chain, q_cur)
    if seed_tangent is None:
        tangent = reference_tangent
    else:
        tangent = np.asarray(seed_tangent, dtype=float).reshape(-1)
        if float(np.dot(tangent, reference_tangent)) < 0.0:
            tangent = -tangent
    sigma_direction = 1.0
    if direction < 0.0:
        tangent = -tangent
        sigma_direction = -1.0

    steps: list[FixedPositionStep] = [
        _seed_step(chain, q_cur, p_arr, path_id, tangent)
    ]
    sigma = 0.0
    for index in range(1, n_steps + 1):
        step, tangent, rejected = sequential_fixed_position_step(
            chain,
            q_cur,
            tangent,
            step_size,
            p_arr,
            path_id=path_id,
            step_index=index,
            sigma0=sigma,
            sigma_direction=sigma_direction,
            max_microstep=max_microstep,
        )
        steps.extend(rejected)
        if step is None or not step.accepted or step.q is None:
            break
        steps.append(step)
        q_cur = step.q
        sigma = step.sigma
    return (
        FixedPositionPath(
            path_id=path_id,
            q0=tuple(float(x) for x in q0),
            p_star=as_vec3(p_arr),
            steps=tuple(steps),
        ),
        tangent,
    )


def _detect_return(
    q0: tuple[float, ...],
    samples: tuple[FixedPositionStep, ...],
    *,
    joint_tol: float = RETURN_JOINT_TOL_RAD,
    min_arc: float = RETURN_MIN_ARC_RAD,
) -> bool:
    """Heuristic loop return: a non-seed sample is near ``q0`` in wrap norm."""
    q0_arr = np.asarray(q0, dtype=float)
    for step in samples:
        if step.q is None or abs(step.sigma) < min_arc:
            continue
        delta = wrap_joint_delta(step.q, q0_arr)
        if float(np.linalg.norm(delta)) <= joint_tol:
            return True
    return False


def continue_fixed_position_fiber(
    model: OpenChainModel,
    q0: tuple[float, ...],
    *,
    n_steps: int = FIBER_STEPS,
    step_size: float = FIBER_STEP_SIZE,
    max_microstep: float | None = MAX_MICROSTEP,
    component_id: str | None = None,
) -> FixedPositionFiberResult:
    """Audit a seed and continue plus/minus pseudo-arclength rays."""
    problem = pose_fixed_position_problem(model, q0)
    audit = audit_fixed_position_seed(problem)
    notes = [
        "Plus/minus rays from one seed do not certify multi-component fiber completeness.",
        "Pseudo-arclength correction uses [p(q)-p*; t^T(q-q_pred)]=0.",
        *model.notes,
    ]
    cid = component_id or f"{model.architecture_id}_component0"
    if not audit.regular or audit.status != "PASS":
        empty = FixedPositionPath(
            path_id="+sigma",
            q0=problem.q0,
            p_star=problem.p_star,
            steps=(),
        )
        empty_m = FixedPositionPath(
            path_id="-sigma",
            q0=problem.q0,
            p_star=problem.p_star,
            steps=(),
        )
        return FixedPositionFiberResult(
            architecture_id=model.architecture_id,
            component_id=cid,
            q0=problem.q0,
            p_star=problem.p_star,
            virtual_closure_kind=problem.virtual_closure.kind,
            seed_audit=audit,
            plus=empty,
            minus=empty_m,
            branch_status="rejected_seed",
            returned=False,
            notes=(*notes, "Seed failed fixed-position or finite-difference audit."),
        )

    seed_tangent = fixed_position_tangent(problem.chain, problem.q0)
    plus, _ = continue_fixed_position_ray(
        problem.chain,
        problem.q0,
        problem.p_star,
        direction=1.0,
        n_steps=n_steps,
        step_size=step_size,
        seed_tangent=seed_tangent,
        path_id="+sigma",
        max_microstep=max_microstep,
    )
    minus, _ = continue_fixed_position_ray(
        problem.chain,
        problem.q0,
        problem.p_star,
        direction=-1.0,
        n_steps=n_steps,
        step_size=step_size,
        seed_tangent=seed_tangent,
        path_id="-sigma",
        max_microstep=max_microstep,
    )
    result = FixedPositionFiberResult(
        architecture_id=model.architecture_id,
        component_id=cid,
        q0=problem.q0,
        p_star=problem.p_star,
        virtual_closure_kind=problem.virtual_closure.kind,
        seed_audit=audit,
        plus=plus,
        minus=minus,
        branch_status="open",
        returned=False,
        notes=tuple(notes),
    )
    samples = result.accepted_samples
    returned = _detect_return(problem.q0, samples)
    plus_budget = len(plus.accepted) >= n_steps + 1
    minus_budget = len(minus.accepted) >= n_steps + 1
    if returned:
        branch_status = "returned"
    elif plus_budget or minus_budget:
        branch_status = "budget_limited"
    else:
        branch_status = "open"
    return FixedPositionFiberResult(
        architecture_id=result.architecture_id,
        component_id=result.component_id,
        q0=result.q0,
        p_star=result.p_star,
        virtual_closure_kind=result.virtual_closure_kind,
        seed_audit=result.seed_audit,
        plus=result.plus,
        minus=result.minus,
        branch_status=branch_status,
        returned=returned,
        notes=result.notes,
    )
