"""Reverse, pointing-image, and distinctness diagnostics for 1D fibers.

Conventions
-----------
Reverse starts at the accepted forward endpoint with the transported tangent.
Pointing differences are ordinary Euclidean differences of unit vectors.
A curved spherical image may span a plane globally; local ``∂d/∂σ`` rank 1
and a noncollapsed image are the H4 gates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .chart_diagnostics import REVERSE_JOINT_TOL_RAD
from .continuation import MAX_MICROSTEP, wrap_joint_delta
from .fiber_constraints import PRIMARY_N, pointing_scalar
from .fiber_continuation import (
    FIBER_STEP_SIZE,
    FIBER_STEPS,
    FiberPath,
    FiberStep,
    continue_fiber_ray,
)
from .jacobians import matrix_rank_report
from .serial_chain import SerialRevoluteChain

Vec = NDArray[np.floating]

# Chart reverse used 1e-8. The extra scalar corrector on IP/n' accumulates
# ~1.4e-8 pointing return error on the 4×0.03 benchmark; accept 5e-8.
FIBER_REVERSE_POINTING_TOL = 5e-8
POINTING_COLLAPSE_TOL = 1e-6
POINTING_TANGENT_TOL = 1e-8
JOINT_FREEZE_DISTINCT_TOL = 1e-3


@dataclass(frozen=True, slots=True)
class FiberReverseReport:
    architecture: str
    n: tuple[float, float, float]
    n_steps: int
    step_size: float
    epsilon_q: float
    epsilon_p: float
    epsilon_d: float
    epsilon_h: float
    forward_accepted: int
    reverse_accepted: int
    started_from_endpoint: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class PointingImageReport:
    n_samples: int
    max_pointing_delta: float
    min_tangent_norm: float
    n_interior: int
    n_rank_one: int
    collapsed: bool
    local_rank_one: bool
    passed: bool


def fiber_forward_reverse(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    n: tuple[float, ...] | Vec = PRIMARY_N,
    *,
    n_steps: int = FIBER_STEPS,
    step_size: float = FIBER_STEP_SIZE,
    architecture: str = "",
    max_microstep: float | None = MAX_MICROSTEP,
    joint_tol: float = REVERSE_JOINT_TOL_RAD,
    pointing_tol: float = FIBER_REVERSE_POINTING_TOL,
) -> FiberReverseReport:
    """Forward ``+σ`` then reverse from the accepted endpoint."""
    n_hat = tuple(float(x) for x in np.asarray(n, dtype=float).reshape(3))
    state0 = chain.evaluate(q0)
    c = pointing_scalar(chain, q0, n_hat)
    forward, tangent_end = continue_fiber_ray(
        chain,
        q0,
        n_hat,
        direction=1.0,
        n_steps=n_steps,
        step_size=step_size,
        path_id="fwd_sigma",
        max_microstep=max_microstep,
    )
    accepted_fwd = [step for step in forward.accepted if step.step_index > 0]
    if not accepted_fwd or accepted_fwd[-1].q is None:
        return FiberReverseReport(
            architecture=architecture,
            n=n_hat,
            n_steps=n_steps,
            step_size=step_size,
            epsilon_q=float("inf"),
            epsilon_p=float("inf"),
            epsilon_d=float("inf"),
            epsilon_h=float("inf"),
            forward_accepted=len(accepted_fwd),
            reverse_accepted=0,
            started_from_endpoint=False,
            passed=False,
        )
    endpoint = accepted_fwd[-1]
    reverse, _ = continue_fiber_ray(
        chain,
        endpoint.q,
        n_hat,
        direction=-1.0,
        n_steps=n_steps,
        step_size=step_size,
        p0=state0.p,
        c=c,
        q6_star=q0[-1],
        seed_tangent=tangent_end,
        path_id="rev_sigma",
        sigma0=endpoint.sigma,
        max_microstep=max_microstep,
    )
    accepted_rev = [step for step in reverse.accepted if step.step_index > 0]
    q_ret = accepted_rev[-1].q if accepted_rev and accepted_rev[-1].q is not None else None
    if q_ret is None:
        return FiberReverseReport(
            architecture=architecture,
            n=n_hat,
            n_steps=n_steps,
            step_size=step_size,
            epsilon_q=float("inf"),
            epsilon_p=float("inf"),
            epsilon_d=float("inf"),
            epsilon_h=float("inf"),
            forward_accepted=len(accepted_fwd),
            reverse_accepted=len(accepted_rev),
            started_from_endpoint=True,
            passed=False,
        )
    state_ret = chain.evaluate(q_ret)
    eps_q = float(np.linalg.norm(wrap_joint_delta(q_ret, q0)))
    eps_p = float(np.linalg.norm(state_ret.p - state0.p))
    eps_d = float(np.linalg.norm(state_ret.d - state0.d))
    eps_h = abs(float(np.asarray(n_hat) @ state_ret.d) - c)
    return FiberReverseReport(
        architecture=architecture,
        n=n_hat,
        n_steps=n_steps,
        step_size=step_size,
        epsilon_q=eps_q,
        epsilon_p=eps_p,
        epsilon_d=eps_d,
        epsilon_h=eps_h,
        forward_accepted=len(accepted_fwd),
        reverse_accepted=len(accepted_rev),
        started_from_endpoint=True,
        passed=(
            eps_q <= joint_tol
            and eps_d <= pointing_tol
            and eps_p <= 1e-10
            and len(accepted_fwd) == n_steps
            and len(accepted_rev) == n_steps
        ),
    )


def pointing_image_report(
    steps: tuple[FiberStep, ...] | list[FiberStep],
    *,
    collapse_tol: float = POINTING_COLLAPSE_TOL,
    tangent_tol: float = POINTING_TANGENT_TOL,
) -> PointingImageReport:
    """H4: noncollapsed pointing image with local ``∂d/∂σ`` rank 1."""
    accepted = [step for step in steps if step.accepted and step.d is not None]
    accepted = sorted(accepted, key=lambda step: step.sigma)
    if not accepted:
        return PointingImageReport(0, 0.0, 0.0, 0, 0, True, False, False)
    d0 = np.asarray(accepted[0].d, dtype=float)
    deltas = [float(np.linalg.norm(np.asarray(step.d, dtype=float) - d0)) for step in accepted]
    max_delta = max(deltas)
    interior = 0
    rank_one = 0
    tangent_norms: list[float] = []
    for i in range(1, len(accepted) - 1):
        ds = accepted[i + 1].sigma - accepted[i - 1].sigma
        if abs(ds) <= 1e-15:
            continue
        dd = (np.asarray(accepted[i + 1].d, dtype=float) - np.asarray(accepted[i - 1].d, dtype=float)) / ds
        interior += 1
        tangent_norms.append(float(np.linalg.norm(dd)))
        report = matrix_rank_report(dd.reshape(3, 1))
        if report.rank == 1 and tangent_norms[-1] > tangent_tol:
            rank_one += 1
    min_tn = min(tangent_norms) if tangent_norms else 0.0
    collapsed = max_delta <= collapse_tol
    local_rank_one = interior > 0 and rank_one == interior
    return PointingImageReport(
        n_samples=len(accepted),
        max_pointing_delta=max_delta,
        min_tangent_norm=min_tn,
        n_interior=interior,
        n_rank_one=rank_one,
        collapsed=collapsed,
        local_rank_one=local_rank_one,
        passed=not collapsed and local_rank_one,
    )


def fiber_paths_distinct(
    task_path: FiberPath,
    control_path: FiberPath,
    *,
    tol: float = JOINT_FREEZE_DISTINCT_TOL,
) -> dict[str, float | int | bool]:
    """Compare accepted samples at shared ``|σ|`` stations."""
    task = {round(abs(step.sigma), 12): step for step in task_path.accepted if step.q is not None}
    control = {round(abs(step.sigma), 12): step for step in control_path.accepted if step.q is not None}
    shared = sorted(set(task) & set(control) - {0.0})
    max_q = 0.0
    max_d = 0.0
    for key in shared:
        assert task[key].q is not None and control[key].q is not None
        max_q = max(max_q, float(np.linalg.norm(wrap_joint_delta(task[key].q, control[key].q))))
        assert task[key].d is not None and control[key].d is not None
        max_d = max(max_d, float(np.linalg.norm(np.asarray(task[key].d) - np.asarray(control[key].d))))
    return {
        "n_shared": len(shared),
        "max_joint_delta": max_q,
        "max_pointing_delta": max_d,
        "distinct": len(shared) > 0 and max_q > tol,
    }


def shared_sigma_agreement(
    coarse: FiberPath,
    fine: FiberPath,
    *,
    joint_tol: float = 1e-4,
    pointing_tol: float = 1e-6,
) -> dict[str, float | int | bool]:
    """Compare accepted samples that share a rounded ``σ`` value."""
    coarse_map = {round(step.sigma, 12): step for step in coarse.accepted if step.q is not None}
    fine_map = {round(step.sigma, 12): step for step in fine.accepted if step.q is not None}
    shared = sorted(set(coarse_map) & set(fine_map))
    max_q = 0.0
    max_d = 0.0
    for key in shared:
        max_q = max(max_q, float(np.linalg.norm(wrap_joint_delta(coarse_map[key].q, fine_map[key].q))))
        max_d = max(
            max_d,
            float(np.linalg.norm(np.asarray(coarse_map[key].d) - np.asarray(fine_map[key].d))),
        )
    return {
        "n_shared": len(shared),
        "max_joint_delta": max_q,
        "max_pointing_delta": max_d,
        "passed": len(shared) > 0 and max_q <= joint_tol and max_d <= pointing_tol,
    }
