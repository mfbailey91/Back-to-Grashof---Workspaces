"""Predictor-corrector continuation of a one-DOF fixed-position fiber.

Conventions
-----------
Constraint (spatial)::

    F(q) = p(q) - p* = 0 ∈ R^3

For a regular spatial 4R seed, ``rank(J_p)=3`` and ``nullity=1``. Prediction
uses the last accepted configuration and a sign-aligned unit fiber tangent.
No pointing scalar ``h=n·d`` and no terminal-roll freeze — those belong to
aligned-terminal 5R/6R pointing fibers, not the complete 4R source fiber.

Multi-component discovery beyond ± rays from one seed is **unverified**.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

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

CORRECTOR_NEWTON_TOL_M = 1e-14
FIBER_STEPS = 40
FIBER_STEP_SIZE = 0.04
RETURN_JOINT_TOL_RAD = 0.05
RETURN_MIN_ARC_RAD = 0.5


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
    corrector_iterations: int
    correction_norm: float
    step_reductions: int
    rank_jp: int
    nullity_jp: int
    tangent_dot: float
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
    """One-seed ± ray continuation of a fixed-position component (unverified completeness)."""

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
    """Newton-correct ``p(q)=p*``; return ``(q, iters, residual, wrap_correction)``."""
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
    max_reductions: int = MAX_STEP_REDUCTIONS,
    max_iter: int = MAX_CORRECTOR_ITERS,
    max_correction_norm: float = MAX_CORRECTION_NORM_RAD,
    position_tol_m: float = POSITION_RESIDUAL_TOL_M,
    max_microstep: float | None = MAX_MICROSTEP,
) -> tuple[FixedPositionStep | None, Vec, tuple[FixedPositionStep, ...]]:
    """Advance one signed fixed-position step from ``q_k``, halving on failure."""
    q_k_arr = np.asarray(q_k, dtype=float).reshape(-1)
    t_start = np.asarray(tangent, dtype=float).reshape(-1)
    rejected: list[FixedPositionStep] = []
    p_target = np.asarray(p_star, dtype=float).reshape(3)
    for reduction in range(max_reductions + 1):
        dsig = float(dsigma) * (0.5**reduction)
        n_micro = 1
        if max_microstep is not None and max_microstep > 0.0 and abs(dsig) > max_microstep:
            n_micro = int(np.ceil(abs(dsig) / max_microstep))
        q_pred_full = q_k_arr + t_start * dsig
        q_pred_tuple = tuple(float(x) for x in q_pred_full)
        q_cur = q_k_arr.copy()
        t_cur = t_start.copy()
        iters_total = 0
        max_corr = 0.0
        residual_p = float("inf")
        q_corr = tuple(float(x) for x in q_cur)
        bundle: dict[str, object] = {}
        tangent_dot = 1.0
        failed_label = None
        for _micro in range(n_micro):
            du = dsig / float(n_micro)
            q_pred_arr = q_cur + t_cur * du
            q_corr, iters, residual_p, corr_norm = correct_position(
                chain,
                tuple(float(x) for x in q_pred_arr),
                p_target,
                max_iter=max_iter,
            )
            iters_total += iters
            max_corr = max(max_corr, corr_norm)
            state = chain.evaluate(q_corr)
            residual_p = float(np.linalg.norm(state.p - p_target))
            bundle = _regularity(chain, q_corr, residual_p, position_tol_m=position_tol_m)
            if residual_p > position_tol_m:
                failed_label = "failed"
                break
            if max_corr > max_correction_norm:
                failed_label = "large_correction"
                break
            if not bool(bundle["regular"]):
                failed_label = str(bundle["label"])
                break
            next_t = fixed_position_tangent(chain, q_corr, previous=t_cur)
            tangent_dot = float(np.dot(t_cur, next_t))
            q_cur = np.asarray(q_corr, dtype=float)
            t_cur = next_t
        state = chain.evaluate(q_corr)
        step = FixedPositionStep(
            sigma=float(sigma0 + dsig),
            path_id=path_id,
            step_index=step_index,
            q_pred=q_pred_tuple,
            q=q_corr if failed_label is None else None,
            d=tuple(float(x) for x in state.d) if failed_label is None else None,
            R=tuple(tuple(float(state.R[i, j]) for j in range(3)) for i in range(3))
            if failed_label is None
            else None,
            p_residual_m=residual_p,
            corrector_iterations=iters_total,
            correction_norm=max_corr,
            step_reductions=reduction,
            rank_jp=int(bundle.get("rank_jp", -1)),
            nullity_jp=int(bundle.get("nullity_jp", -1)),
            tangent_dot=tangent_dot,
            regular=bool(bundle.get("regular", False)),
            label="accepted" if failed_label is None else failed_label,
            accepted=failed_label is None,
        )
        if step.accepted:
            return step, t_cur, tuple(rejected)
        rejected.append(step)
    return None, t_start, tuple(rejected)


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
    """Continue one signed ray along the fixed-position fiber."""
    q_cur = tuple(float(x) for x in q0)
    p_arr = np.asarray(p_star, dtype=float).reshape(3)
    if seed_tangent is None:
        tangent = fixed_position_tangent(chain, q_cur)
    else:
        tangent = np.asarray(seed_tangent, dtype=float).reshape(-1)
        if float(np.dot(tangent, fixed_position_tangent(chain, q_cur))) < 0.0:
            tangent = -tangent
    if direction < 0.0:
        tangent = -tangent
    steps: list[FixedPositionStep] = [
        FixedPositionStep(
            sigma=0.0,
            path_id=path_id,
            step_index=0,
            q_pred=None,
            q=q_cur,
            d=tuple(float(x) for x in chain.evaluate(q_cur).d),
            R=tuple(tuple(float(chain.evaluate(q_cur).R[i, j]) for j in range(3)) for i in range(3)),
            p_residual_m=float(np.linalg.norm(chain.evaluate(q_cur).p - p_arr)),
            corrector_iterations=0,
            correction_norm=0.0,
            step_reductions=0,
            rank_jp=matrix_rank_report(position_jacobian(chain, q_cur)).rank,
            nullity_jp=matrix_rank_report(position_jacobian(chain, q_cur)).nullity,
            tangent_dot=1.0,
            regular=True,
            label="seed",
            accepted=True,
        )
    ]
    sigma = 0.0
    for index in range(1, n_steps + 1):
        step, tangent, rejected = sequential_fixed_position_step(
            chain,
            q_cur,
            tangent,
            step_size if direction >= 0.0 else -step_size,
            p_arr,
            path_id=path_id,
            step_index=index,
            sigma0=sigma,
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
            p_star=tuple(float(x) for x in p_arr),
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
    """Heuristic loop return: some non-seed sample is near ``q0`` in wrap norm."""
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
    """Audit seed and continue ± rays of the fixed-position fiber."""
    problem = pose_fixed_position_problem(model, q0)
    audit = audit_fixed_position_seed(problem)
    notes = [
        "± rays from one seed do not certify full multi-component fiber completeness.",
        *model.notes,
    ]
    cid = component_id or f"{model.architecture_id}_component0"
    if not audit.regular:
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
            notes=tuple([*notes, "Seed failed fixed-position regularity audit."]),
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
    plus_budget = len(plus.accepted) >= n_steps
    minus_budget = len(minus.accepted) >= n_steps
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
