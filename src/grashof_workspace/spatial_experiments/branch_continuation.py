"""Shared one-dimensional pseudo-arclength continuation (V06H3).

Infrastructure only. This module does not migrate V06D1/D2, does not issue
a ``DecompositionCertificate``, and does not reconstruct a parent.

At state ``x_k``, unit tangent ``t_k``, and step ``ds``::

    x_pred = x_k + ds t_k
    G(x) = [F(x); t_k^T Δ(x, x_pred)] = 0

where ``Δ`` is the wrapped ambient displacement. Position-only return
detection is forbidden: a loop requires minimum arclength, wrapped-state
proximity, tangent alignment, and matching branch identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

from .implicit_manifold import ambient_distance, orthonormal_tangent_basis, wrapped_delta
from .jacobians import matrix_rank_report

Array = NDArray[np.floating]

RESIDUAL_TOL = 1e-10
GAUGE_TOL = 1e-10
NEWTON_MAX_ITERS = 25
AUGMENTED_CONDITION_LIMIT = 1e12
MAX_CORRECTION_TO_DS = 2.0
MAX_TANGENT_ROTATION = 0.5
MAX_STEP_REDUCTIONS = 6
EASY_STEPS_BEFORE_GROW = 4
GROW_FACTOR = 1.5
DEFAULT_DS = 0.08
MIN_DS = 1e-4
MAX_DS = 0.25
DEFAULT_MAX_STEPS = 80
RETURN_MIN_ARC = 1.5
RETURN_STATE_TOL = 0.08
RETURN_TANGENT_DOT = 0.85


class ImplicitBranchProblem(Protocol):
    """One-dimensional implicit branch ``F(x)=0`` in ambient coordinates."""

    problem_id: str
    ambient_dimension: int
    constraint_dimension: int
    periodic_coordinates: tuple[bool, ...]

    def residual(self, x: Array) -> Array: ...

    def jacobian(self, x: Array) -> Array: ...


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float) and not isfinite(obj):
        return None
    return obj


def wrap_state(x: Array, periodic: tuple[bool, ...]) -> Array:
    y = np.asarray(x, dtype=float).reshape(-1).copy()
    if y.size != len(periodic):
        raise ValueError("periodic_coordinates length must match ambient dimension")
    for i, flag in enumerate(periodic):
        if flag:
            y[i] = float(np.arctan2(np.sin(y[i]), np.cos(y[i])))
    return y


def branch_tangent(problem: ImplicitBranchProblem, x: Array, previous: Array | None = None) -> Array:
    jac = np.asarray(problem.jacobian(x), dtype=float)
    basis = orthonormal_tangent_basis(jac, expected_nullity=1)[:, 0]
    t = np.asarray(basis, dtype=float).reshape(-1)
    nrm = float(np.linalg.norm(t))
    if nrm <= 0.0:
        raise ValueError("null tangent is zero")
    t = t / nrm
    if previous is not None and float(np.dot(t, np.asarray(previous, dtype=float).reshape(-1))) < 0.0:
        t = -t
    return t


def detect_branch_return(
    *,
    seed_x: Array,
    seed_t: Array,
    x: Array,
    t: Array,
    accumulated_arclength: float,
    periodic: tuple[bool, ...],
    seed_branch_id: str,
    branch_id: str,
    min_arc: float = RETURN_MIN_ARC,
    state_tol: float = RETURN_STATE_TOL,
    tangent_dot_tol: float = RETURN_TANGENT_DOT,
) -> bool:
    """Conjunctive loop return. Position-only proximity is not sufficient."""

    if branch_id != seed_branch_id:
        return False
    if abs(float(accumulated_arclength)) < min_arc:
        return False
    if ambient_distance(x, seed_x, periodic) > state_tol:
        return False
    aligned = abs(float(np.dot(np.asarray(t, dtype=float), np.asarray(seed_t, dtype=float))))
    return aligned >= tangent_dot_tol


@dataclass(frozen=True, slots=True)
class BranchStep:
    s: float
    x_pred: tuple[float, ...]
    x: tuple[float, ...] | None
    constraint_residual: float
    gauge_residual: float
    correction_norm: float
    step_size: float
    newton_iterations: int
    condition_number: float | None
    rank: int | None
    nullity: int | None
    tangent_alignment: float | None
    accepted: bool
    rejection_reason: str | None

    def to_json_dict(self) -> dict[str, Any]:
        payload = _json_safe(
            {
                "s": self.s,
                "x_pred": list(self.x_pred),
                "x": None if self.x is None else list(self.x),
                "constraint_residual": self.constraint_residual,
                "gauge_residual": self.gauge_residual,
                "correction_norm": self.correction_norm,
                "step_size": self.step_size,
                "newton_iterations": self.newton_iterations,
                "condition_number": self.condition_number,
                "rank": self.rank,
                "nullity": self.nullity,
                "tangent_alignment": self.tangent_alignment,
                "accepted": self.accepted,
                "rejection_reason": self.rejection_reason,
            }
        )
        if not isinstance(payload, dict):
            raise TypeError("expected a JSON object")
        return payload


@dataclass(frozen=True, slots=True)
class BranchTrace:
    problem_id: str
    branch_id: str
    x_seed: tuple[float, ...]
    steps: tuple[BranchStep, ...]
    branch_status: str
    returned: bool
    notes: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "branch_id": self.branch_id,
            "x_seed": list(self.x_seed),
            "steps": [s.to_json_dict() for s in self.steps],
            "accepted_step_count": sum(1 for s in self.steps if s.accepted),
            "branch_status": self.branch_status,
            "returned": self.returned,
            "notes": list(self.notes),
        }


def correct_pseudo_arclength(
    problem: ImplicitBranchProblem,
    x_pred: Array,
    tangent: Array,
    *,
    max_iter: int = NEWTON_MAX_ITERS,
    residual_tol: float = RESIDUAL_TOL,
    gauge_tol: float = GAUGE_TOL,
) -> BranchStep:
    """Newton-correct ``G(x)=[F(x); t^T Δ(x,x_pred)]`` from the predictor."""

    x_pred_arr = wrap_state(np.asarray(x_pred, dtype=float).reshape(-1), problem.periodic_coordinates)
    t_ref = np.asarray(tangent, dtype=float).reshape(-1)
    t_norm = float(np.linalg.norm(t_ref))
    if t_norm <= 0.0:
        raise ValueError("pseudo-arclength tangent must be nonzero")
    t_ref = t_ref / t_norm
    x_arr = x_pred_arr.copy()
    pred_tuple = tuple(float(v) for v in x_pred_arr)
    constraint_res = float("inf")
    gauge_res = float("inf")
    max_cond = 0.0
    rank = None
    nullity = None
    iters = 0
    accepted = False
    reason: str | None = "corrector_budget"
    for iters in range(1, max_iter + 1):
        f = np.asarray(problem.residual(x_arr), dtype=float).reshape(-1)
        delta = wrapped_delta(x_arr, x_pred_arr, problem.periodic_coordinates)
        gauge = float(np.dot(t_ref, delta))
        constraint_res = float(np.linalg.norm(f))
        gauge_res = abs(gauge)
        jac = np.asarray(problem.jacobian(x_arr), dtype=float)
        report = matrix_rank_report(jac)
        rank, nullity = report.rank, report.nullity
        augmented = np.vstack((jac, t_ref.reshape(1, -1)))
        cond = float(np.linalg.cond(augmented))
        max_cond = max(max_cond, cond)
        if constraint_res <= residual_tol and gauge_res <= gauge_tol:
            accepted = True
            reason = None
            break
        rhs = -np.concatenate((f, np.array((gauge,), dtype=float)))
        dx, *_ = np.linalg.lstsq(augmented, rhs, rcond=None)
        x_arr = wrap_state(x_arr + dx, problem.periodic_coordinates)
    else:
        f = np.asarray(problem.residual(x_arr), dtype=float).reshape(-1)
        delta = wrapped_delta(x_arr, x_pred_arr, problem.periodic_coordinates)
        constraint_res = float(np.linalg.norm(f))
        gauge_res = abs(float(np.dot(t_ref, delta)))
        reason = "corrector_failed"
    corr = float(np.linalg.norm(wrapped_delta(x_arr, x_pred_arr, problem.periodic_coordinates)))
    return BranchStep(
        s=0.0,
        x_pred=pred_tuple,
        x=tuple(float(v) for v in x_arr) if accepted else None,
        constraint_residual=constraint_res,
        gauge_residual=gauge_res,
        correction_norm=corr,
        step_size=0.0,
        newton_iterations=iters,
        condition_number=max_cond,
        rank=rank,
        nullity=nullity,
        tangent_alignment=None,
        accepted=accepted,
        rejection_reason=reason,
    )


def _rejected(
    *,
    s: float,
    x_pred: Array,
    step: BranchStep,
    ds: float,
    reason: str,
    tangent_alignment: float | None,
) -> BranchStep:
    return BranchStep(
        s=s,
        x_pred=tuple(float(v) for v in np.asarray(x_pred, dtype=float).reshape(-1)),
        x=step.x,
        constraint_residual=step.constraint_residual,
        gauge_residual=step.gauge_residual,
        correction_norm=step.correction_norm,
        step_size=ds,
        newton_iterations=step.newton_iterations,
        condition_number=step.condition_number,
        rank=step.rank,
        nullity=step.nullity,
        tangent_alignment=tangent_alignment,
        accepted=False,
        rejection_reason=reason,
    )


def take_branch_step(
    problem: ImplicitBranchProblem,
    x_k: Array,
    t_k: Array,
    ds: float,
    *,
    s0: float,
    max_reductions: int = MAX_STEP_REDUCTIONS,
) -> tuple[BranchStep | None, Array, tuple[BranchStep, ...]]:
    """Advance one signed pseudo-arclength step, shrinking ``ds`` on failure."""

    if ds == 0.0:
        raise ValueError("ds must be nonzero")
    x_cur = wrap_state(x_k, problem.periodic_coordinates)
    t_cur = np.asarray(t_k, dtype=float).reshape(-1)
    t_cur = t_cur / float(np.linalg.norm(t_cur))
    rejected: list[BranchStep] = []
    sign = 1.0 if ds > 0.0 else -1.0
    mag0 = abs(float(ds))

    for reduction in range(max_reductions + 1):
        mag = mag0 * (0.5**reduction)
        if mag < MIN_DS:
            break
        ds_try = sign * mag
        x_pred = wrap_state(x_cur + ds_try * t_cur, problem.periodic_coordinates)
        corr = correct_pseudo_arclength(problem, x_pred, t_cur)
        if not corr.accepted or corr.x is None:
            rejected.append(
                _rejected(s=s0, x_pred=x_pred, step=corr, ds=ds_try, reason="corrector_failed", tangent_alignment=None)
            )
            continue
        if corr.correction_norm > MAX_CORRECTION_TO_DS * mag:
            rejected.append(
                _rejected(
                    s=s0,
                    x_pred=x_pred,
                    step=corr,
                    ds=ds_try,
                    reason="large_correction",
                    tangent_alignment=None,
                )
            )
            continue
        if corr.condition_number is not None and corr.condition_number > AUGMENTED_CONDITION_LIMIT:
            rejected.append(
                _rejected(
                    s=s0,
                    x_pred=x_pred,
                    step=corr,
                    ds=ds_try,
                    reason="ill_conditioned",
                    tangent_alignment=None,
                )
            )
            continue
        if corr.rank != problem.constraint_dimension or corr.nullity != 1:
            rejected.append(
                _rejected(
                    s=s0,
                    x_pred=x_pred,
                    step=corr,
                    ds=ds_try,
                    reason="singular",
                    tangent_alignment=None,
                )
            )
            continue
        x_hat = np.asarray(corr.x, dtype=float)
        try:
            t_new = branch_tangent(problem, x_hat, previous=t_cur)
        except ValueError:
            rejected.append(
                _rejected(
                    s=s0,
                    x_pred=x_pred,
                    step=corr,
                    ds=ds_try,
                    reason="singular",
                    tangent_alignment=None,
                )
            )
            continue
        alignment = float(np.dot(t_cur, t_new))
        rotation = float(np.arccos(min(1.0, max(-1.0, alignment))))
        if rotation > MAX_TANGENT_ROTATION:
            rejected.append(
                _rejected(
                    s=s0,
                    x_pred=x_pred,
                    step=corr,
                    ds=ds_try,
                    reason="tangent_rotation",
                    tangent_alignment=alignment,
                )
            )
            continue
        actual = float(np.linalg.norm(wrapped_delta(x_hat, x_cur, problem.periodic_coordinates)))
        accepted = BranchStep(
            s=float(s0 + sign * actual),
            x_pred=tuple(float(v) for v in x_pred),
            x=tuple(float(v) for v in x_hat),
            constraint_residual=corr.constraint_residual,
            gauge_residual=corr.gauge_residual,
            correction_norm=corr.correction_norm,
            step_size=ds_try,
            newton_iterations=corr.newton_iterations,
            condition_number=corr.condition_number,
            rank=corr.rank,
            nullity=corr.nullity,
            tangent_alignment=alignment,
            accepted=True,
            rejection_reason=None,
        )
        return accepted, t_new, tuple(rejected)
    return None, t_cur, tuple(rejected)


def continue_implicit_branch(
    problem: ImplicitBranchProblem,
    x_seed: Array,
    *,
    branch_id: str | None = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    step_size: float = DEFAULT_DS,
) -> BranchTrace:
    """Continue ± rays from one seed. One seed is not component completeness."""

    x0 = wrap_state(x_seed, problem.periodic_coordinates)
    bid = branch_id or f"{problem.problem_id}_branch0"
    t0 = branch_tangent(problem, x0)
    seed = BranchStep(
        s=0.0,
        x_pred=tuple(float(v) for v in x0),
        x=tuple(float(v) for v in x0),
        constraint_residual=float(np.linalg.norm(problem.residual(x0))),
        gauge_residual=0.0,
        correction_norm=0.0,
        step_size=0.0,
        newton_iterations=0,
        condition_number=None,
        rank=matrix_rank_report(problem.jacobian(x0)).rank,
        nullity=1,
        tangent_alignment=1.0,
        accepted=True,
        rejection_reason=None,
    )
    steps: list[BranchStep] = [seed]
    notes = (
        "V06H3 shared pseudo-arclength engine; not a D1/D2 migration (ADR-044).",
        "Plus/minus rays from one seed are not component completeness.",
        "Return requires arclength, wrapped state, tangent alignment, and branch identity.",
    )
    status = "open"
    returned = False
    ds_mag = abs(float(step_size))
    easy = 0

    for sign in (1.0, -1.0):
        x_cur = x0.copy()
        t_cur = t0.copy() if sign > 0.0 else -t0.copy()
        s_cur = 0.0
        ds_local = sign * ds_mag
        easy = 0
        for _ in range(max_steps):
            step, t_next, rejected = take_branch_step(
                problem, x_cur, t_cur, ds_local, s0=s_cur
            )
            steps.extend(rejected)
            if step is None or not step.accepted or step.x is None:
                last_reason = rejected[-1].rejection_reason if rejected else "unresolved"
                if last_reason == "singular":
                    status = "singular"
                elif status != "returned":
                    status = "unresolved" if last_reason == "corrector_failed" else "open"
                break
            steps.append(step)
            x_cur = np.asarray(step.x, dtype=float)
            t_cur = t_next
            s_cur = step.s
            if abs(step.step_size) >= 0.99 * abs(ds_local) and step.correction_norm <= 0.25 * abs(step.step_size):
                easy += 1
                if easy >= EASY_STEPS_BEFORE_GROW:
                    ds_local = sign * min(MAX_DS, abs(ds_local) * GROW_FACTOR)
                    easy = 0
            else:
                easy = 0
                if step.newton_iterations > 8:
                    ds_local = sign * max(MIN_DS, abs(ds_local) * 0.5)
            if detect_branch_return(
                seed_x=x0,
                seed_t=t0,
                x=x_cur,
                t=t_cur if sign > 0.0 else -t_cur,
                accumulated_arclength=s_cur,
                periodic=problem.periodic_coordinates,
                seed_branch_id=bid,
                branch_id=bid,
            ):
                returned = True
                status = "returned"
                break
        if returned:
            break

    steps.sort(key=lambda s: s.s)
    return BranchTrace(
        problem_id=problem.problem_id,
        branch_id=bid,
        x_seed=tuple(float(v) for v in x0),
        steps=tuple(steps),
        branch_status=status,
        returned=returned,
        notes=notes,
    )


@dataclass(frozen=True, slots=True)
class UnitCircleProblem:
    """Analytical circle ``x·x-1=0`` in ``R^2`` (software fixture, not a robot)."""

    problem_id: str = "analytical_unit_circle"
    ambient_dimension: int = 2
    constraint_dimension: int = 1
    periodic_coordinates: tuple[bool, ...] = (False, False)

    def residual(self, x: Array) -> Array:
        vec = np.asarray(x, dtype=float).reshape(-1)
        return np.array([float(vec @ vec) - 1.0], dtype=float)

    def jacobian(self, x: Array) -> Array:
        vec = np.asarray(x, dtype=float).reshape(-1)
        return 2.0 * vec.reshape(1, -1)


@dataclass(frozen=True, slots=True)
class ParabolaProblem:
    """Open 1D branch ``y - x^2 = 0`` (no loop return)."""

    problem_id: str = "analytical_parabola"
    ambient_dimension: int = 2
    constraint_dimension: int = 1
    periodic_coordinates: tuple[bool, ...] = (False, False)

    def residual(self, x: Array) -> Array:
        vec = np.asarray(x, dtype=float).reshape(-1)
        return np.array([float(vec[1] - vec[0] * vec[0])], dtype=float)

    def jacobian(self, x: Array) -> Array:
        vec = np.asarray(x, dtype=float).reshape(-1)
        return np.array([[-2.0 * float(vec[0]), 1.0]], dtype=float)
