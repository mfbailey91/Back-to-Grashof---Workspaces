"""Sequential predictor-corrector continuation of a 1D pointing fiber.

Conventions
-----------
Constraint::

    p(q) = p0
    h(q) = n · d(q) = c
    q6 = q6*

Prediction uses the last accepted configuration and a sign-aligned 1D fiber
tangent. The general fiber API does not accept ``include_pairs`` or ``suur_map``.

Stored ``q_pred`` is the full-``Δσ`` prediction from the accepted parent step.
``correction_norm`` is the maximum wrap-norm correction over microsteps.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import as_vec3


def _as_int(value: object, default: int = 0) -> int:
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
from .fiber_constraints import (
    SCALAR_RESIDUAL_TOL,
    pointing_scalar,
    pointing_scalar_gradient,
    reduced_fiber_jacobian,
    reduced_fiber_tangent,
)
from .jacobians import matrix_rank_report, pointing_jacobian, position_jacobian
from .serial_chain import SerialRevoluteChain

Mat = NDArray[np.floating]
Vec = NDArray[np.floating]

CORRECTOR_NEWTON_TOL_M = 1e-14
CORRECTOR_NEWTON_TOL_H = 1e-14
FIBER_STEPS = 4
FIBER_STEP_SIZE = 0.03
E6_COL_TOL = 1e-9


@dataclass(frozen=True, slots=True)
class FiberStep:
    sigma: float
    path_id: str
    step_index: int
    q_pred: tuple[float, ...] | None
    q: tuple[float, ...] | None
    d: tuple[float, float, float] | None
    p_residual_m: float
    h_residual: float
    corrector_iterations: int
    correction_norm: float
    step_reductions: int
    rank_jf: int
    nullity_jf: int
    tangent_dot: float
    regular: bool
    label: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class FiberPath:
    path_id: str
    n: tuple[float, float, float]
    c: float
    q0: tuple[float, ...]
    p0: tuple[float, float, float]
    q6_star: float
    steps: tuple[FiberStep, ...]

    @property
    def accepted(self) -> tuple[FiberStep, ...]:
        return tuple(step for step in self.steps if step.accepted)

    @property
    def rejected(self) -> tuple[FiberStep, ...]:
        return tuple(step for step in self.steps if not step.accepted)


@dataclass(frozen=True, slots=True)
class FiberSegment:
    q0: tuple[float, ...]
    p0: tuple[float, float, float]
    d0: tuple[float, float, float]
    q6_star: float
    n: tuple[float, float, float]
    c: float
    plus: FiberPath
    minus: FiberPath

    @property
    def accepted_samples(self) -> tuple[FiberStep, ...]:
        seen: dict[float, FiberStep] = {}
        for path in (self.minus, self.plus):
            for step in path.accepted:
                seen[round(step.sigma, 12)] = step
        return tuple(sorted(seen.values(), key=lambda step: step.sigma))


def correct_position_scalar(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    p0: Vec,
    n: tuple[float, ...] | Vec,
    c: float,
    *,
    freeze_roll: bool = True,
    max_iter: int = MAX_CORRECTOR_ITERS,
    tol_m: float = CORRECTOR_NEWTON_TOL_M,
    tol_h: float = CORRECTOR_NEWTON_TOL_H,
) -> tuple[tuple[float, ...], int, float, float, float]:
    """Newton-correct ``(p,h)=(p0,c)`` and return residuals plus wrap correction."""
    q_arr = np.asarray(q, dtype=float).copy()
    q_start = q_arr.copy()
    p_target = np.asarray(p0, dtype=float).reshape(3)
    n_hat = np.asarray(n, dtype=float).reshape(3)
    n_hat = n_hat / float(np.linalg.norm(n_hat))
    iters = 0
    residual_p = float("inf")
    residual_h = float("inf")
    for iters in range(1, max_iter + 1):
        state = chain.evaluate(tuple(float(x) for x in q_arr))
        err_p = state.p - p_target
        residual_p = float(np.linalg.norm(err_p))
        residual_h = float(n_hat @ state.d) - float(c)
        if residual_p <= tol_m and abs(residual_h) <= tol_h:
            break
        jp = position_jacobian(chain, tuple(float(x) for x in q_arr))
        grad = pointing_jacobian(chain, tuple(float(x) for x in q_arr)).T @ n_hat
        err = np.concatenate([err_p, np.array([residual_h], dtype=float)])
        if freeze_roll:
            jac = np.vstack([jp[:, :5], grad[:5]])
            dq, *_ = np.linalg.lstsq(jac, -err, rcond=None)
            q_arr[:5] = q_arr[:5] + dq
        else:
            jac = np.vstack([jp, grad.reshape(1, -1)])
            dq, *_ = np.linalg.lstsq(jac, -err, rcond=None)
            q_arr = q_arr + dq
    else:
        state = chain.evaluate(tuple(float(x) for x in q_arr))
        residual_p = float(np.linalg.norm(state.p - p_target))
        residual_h = float(n_hat @ state.d) - float(c)
    q_corr = tuple(float(x) for x in q_arr)
    correction_norm = float(np.linalg.norm(wrap_joint_delta(q_corr, q_start)))
    return q_corr, iters, residual_p, abs(residual_h), correction_norm


def _fiber_regularity(
    chain: SerialRevoluteChain,
    q: tuple[float, ...],
    n: tuple[float, ...] | Vec,
    p_residual_m: float,
    h_residual: float,
    *,
    position_tol_m: float,
    scalar_tol: float,
) -> dict[str, object]:
    jf = reduced_fiber_jacobian(chain, q, n)
    report = matrix_rank_report(jf)
    jp = position_jacobian(chain, q)
    e6 = np.zeros(chain.n_joints)
    e6[-1] = 1.0
    grad = pointing_scalar_gradient(chain, q, n)
    regular = (
        report.rank == 4
        and report.nullity == 1
        and p_residual_m <= position_tol_m
        and h_residual <= scalar_tol
        and float(np.linalg.norm(jp @ e6)) <= E6_COL_TOL
        and abs(float(grad[-1])) <= 1e-9
    )
    if p_residual_m > position_tol_m or h_residual > scalar_tol:
        label = "failed"
    elif regular:
        label = "regular"
    else:
        label = "singular"
    return {
        "rank_jf": report.rank,
        "nullity_jf": report.nullity,
        "regular": regular,
        "label": label,
        "singular_values": report.singular_values,
    }


def sequential_fiber_step(
    chain: SerialRevoluteChain,
    q_k: tuple[float, ...],
    tangent: Vec,
    dsigma: float,
    p0: Vec,
    n: tuple[float, ...] | Vec,
    c: float,
    q6_star: float,
    *,
    path_id: str,
    step_index: int,
    sigma0: float,
    max_reductions: int = MAX_STEP_REDUCTIONS,
    max_iter: int = MAX_CORRECTOR_ITERS,
    max_correction_norm: float = MAX_CORRECTION_NORM_RAD,
    position_tol_m: float = POSITION_RESIDUAL_TOL_M,
    scalar_tol: float = SCALAR_RESIDUAL_TOL,
    max_microstep: float | None = MAX_MICROSTEP,
) -> tuple[FiberStep | None, Vec, tuple[FiberStep, ...]]:
    """Advance one signed fiber step from ``q_k``, halving on failure."""
    q_k_arr = np.asarray(q_k, dtype=float).reshape(6)
    t_start = np.asarray(tangent, dtype=float).reshape(6)
    rejected: list[FiberStep] = []
    n_hat = tuple(float(x) for x in np.asarray(n, dtype=float).reshape(3))
    for reduction in range(max_reductions + 1):
        dsig = float(dsigma) * (0.5**reduction)
        n_micro = 1
        if max_microstep is not None and max_microstep > 0.0 and abs(dsig) > max_microstep:
            n_micro = int(np.ceil(abs(dsig) / max_microstep))
        q_pred_full = q_k_arr + t_start * dsig
        q_pred_full[-1] = q6_star
        q_pred_tuple = tuple(float(x) for x in q_pred_full)
        q_cur = q_k_arr.copy()
        t_cur = t_start.copy()
        iters_total = 0
        max_corr = 0.0
        residual_p = float("inf")
        residual_h = float("inf")
        q_corr = tuple(float(x) for x in q_cur)
        state = chain.evaluate(q_corr)
        bundle: dict[str, object] = {}
        tangent_dot = 1.0
        failed_label = None
        for _micro in range(n_micro):
            du = dsig / float(n_micro)
            q_pred_arr = q_cur + t_cur * du
            q_pred_arr[-1] = q6_star
            q_corr, iters, residual_p, residual_h, corr_norm = correct_position_scalar(
                chain,
                tuple(float(x) for x in q_pred_arr),
                p0,
                n_hat,
                c,
                freeze_roll=True,
                max_iter=max_iter,
            )
            q_corr = (*q_corr[:5], q6_star)
            iters_total += iters
            max_corr = max(max_corr, corr_norm)
            state = chain.evaluate(q_corr)
            residual_p = float(np.linalg.norm(state.p - np.asarray(p0, dtype=float).reshape(3)))
            residual_h = abs(float(np.asarray(n_hat) @ state.d) - float(c))
            bundle = _fiber_regularity(
                chain, q_corr, n_hat, residual_p, residual_h, position_tol_m=position_tol_m, scalar_tol=scalar_tol
            )
            if residual_p > position_tol_m or residual_h > scalar_tol:
                failed_label = "failed"
                break
            if max_corr > max_correction_norm:
                failed_label = "trust_radius"
                break
            if not bool(bundle["regular"]):
                failed_label = "rank_lost" if str(bundle["label"]) == "singular" else str(bundle["label"])
                break
            t_new = reduced_fiber_tangent(chain, q_corr, n_hat, previous=t_cur)
            tangent_dot = float(np.dot(t_new, t_cur))
            q_cur = np.asarray(q_corr, dtype=float)
            t_cur = t_new
        accepted = failed_label is None
        label = "regular" if accepted else str(failed_label or bundle.get("label", "failed"))
        step = FiberStep(
            sigma=float(sigma0 + dsig),
            path_id=path_id,
            step_index=step_index,
            q_pred=q_pred_tuple,
            q=q_corr,
            d=as_vec3(state.d),
            p_residual_m=residual_p,
            h_residual=residual_h,
            corrector_iterations=iters_total,
            correction_norm=max_corr,
            step_reductions=reduction,
            rank_jf=_as_int(bundle.get("rank_jf"), 0),
            nullity_jf=_as_int(bundle.get("nullity_jf"), 0),
            tangent_dot=tangent_dot,
            regular=bool(bundle.get("regular", False)) and accepted,
            label=label,
            accepted=accepted,
        )
        if accepted:
            return step, t_cur, tuple(rejected)
        rejected.append(step)
    return None, t_start, tuple(rejected)


def continue_fiber_ray(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    n: tuple[float, ...] | Vec,
    *,
    direction: float,
    n_steps: int = FIBER_STEPS,
    step_size: float = FIBER_STEP_SIZE,
    p0: Vec | None = None,
    c: float | None = None,
    q6_star: float | None = None,
    seed_tangent: Vec | None = None,
    path_id: str | None = None,
    sigma0: float = 0.0,
    max_microstep: float | None = MAX_MICROSTEP,
) -> tuple[FiberPath, Vec]:
    """Continue ``n_steps`` along the signed fiber from an accepted seed."""
    if chain.n_joints != 6:
        raise ValueError("fiber continuation expects a 6R chain")
    q_arr = np.asarray(q0, dtype=float).reshape(6)
    q6 = float(q_arr[-1] if q6_star is None else q6_star)
    q_arr[-1] = q6
    q_cur = tuple(float(x) for x in q_arr)
    n_hat = tuple(float(x) for x in np.asarray(n, dtype=float).reshape(3))
    n_norm = float(np.linalg.norm(n_hat))
    n_hat = tuple(float(x) / n_norm for x in n_hat)
    state0 = chain.evaluate(q_cur)
    p_target = state0.p.copy() if p0 is None else np.asarray(p0, dtype=float).reshape(3)
    c_val = float(pointing_scalar(chain, q_cur, n_hat) if c is None else c)
    tangent = (
        np.asarray(seed_tangent, dtype=float).reshape(6)
        if seed_tangent is not None
        else reduced_fiber_tangent(chain, q_cur, n_hat)
    )
    pid = path_id or ("+sigma" if direction > 0 else "-sigma")
    steps: list[FiberStep] = []
    seed_p = float(np.linalg.norm(state0.p - p_target))
    seed_h = abs(float(np.asarray(n_hat) @ state0.d) - c_val)
    seed_bundle = _fiber_regularity(
        chain, q_cur, n_hat, seed_p, seed_h, position_tol_m=POSITION_RESIDUAL_TOL_M, scalar_tol=SCALAR_RESIDUAL_TOL
    )
    steps.append(
        FiberStep(
            sigma=float(sigma0),
            path_id=pid,
            step_index=0,
            q_pred=q_cur,
            q=q_cur,
            d=as_vec3(state0.d),
            p_residual_m=seed_p,
            h_residual=seed_h,
            corrector_iterations=0,
            correction_norm=0.0,
            step_reductions=0,
            rank_jf=_as_int(seed_bundle.get("rank_jf"), 0),
            nullity_jf=_as_int(seed_bundle.get("nullity_jf"), 0),
            tangent_dot=1.0,
            regular=bool(seed_bundle["regular"]),
            label="seed" if seed_bundle["regular"] else str(seed_bundle["label"]),
            accepted=True,
        )
    )
    dsigma = step_size * float(np.sign(direction) or 1.0)
    sigma_cur = float(sigma0)
    for index in range(1, n_steps + 1):
        accepted, tangent, rejected = sequential_fiber_step(
            chain,
            q_cur,
            tangent,
            dsigma,
            p_target,
            n_hat,
            c_val,
            q6,
            path_id=pid,
            step_index=index,
            sigma0=sigma_cur,
            max_microstep=max_microstep,
        )
        steps.extend(rejected)
        if accepted is None:
            break
        steps.append(accepted)
        assert accepted.q is not None
        q_cur = accepted.q
        sigma_cur = accepted.sigma
    return (
        FiberPath(
            path_id=pid,
            n=as_vec3(n_hat),
            c=c_val,
            q0=tuple(float(x) for x in q_arr),
            p0=as_vec3(p_target),
            q6_star=q6,
            steps=tuple(steps),
        ),
        tangent,
    )


def continue_fiber(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    n: tuple[float, ...] | Vec,
    *,
    n_steps: int = FIBER_STEPS,
    step_size: float = FIBER_STEP_SIZE,
    max_microstep: float | None = MAX_MICROSTEP,
) -> FiberSegment:
    """Continue both ``±σ`` rays from the seed."""
    q_arr = np.asarray(q0, dtype=float).reshape(6)
    q0_t = tuple(float(x) for x in q_arr)
    n_hat = tuple(float(x) for x in np.asarray(n, dtype=float).reshape(3))
    n_norm = float(np.linalg.norm(n_hat))
    n_hat = tuple(float(x) / n_norm for x in n_hat)
    state0 = chain.evaluate(q0_t)
    seed_tangent = reduced_fiber_tangent(chain, q0_t, n_hat)
    plus, _ = continue_fiber_ray(
        chain,
        q0_t,
        n_hat,
        direction=1.0,
        n_steps=n_steps,
        step_size=step_size,
        seed_tangent=seed_tangent,
        path_id="+sigma",
        max_microstep=max_microstep,
    )
    minus, _ = continue_fiber_ray(
        chain,
        q0_t,
        n_hat,
        direction=-1.0,
        n_steps=n_steps,
        step_size=step_size,
        seed_tangent=seed_tangent,
        path_id="-sigma",
        max_microstep=max_microstep,
    )
    return FiberSegment(
        q0=q0_t,
        p0=as_vec3(state0.p),
        d0=as_vec3(state0.d),
        q6_star=q0_t[-1],
        n=as_vec3(n_hat),
        c=float(pointing_scalar(chain, q0_t, n_hat)),
        plus=plus,
        minus=minus,
    )


def continue_joint_freeze_ray(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    freeze_index: int,
    direction: float,
    n_steps: int = FIBER_STEPS,
    step_size: float = FIBER_STEP_SIZE,
    max_microstep: float | None = MAX_MICROSTEP,
) -> FiberPath:
    """Negative-control 1D path: ``p=p0`` with ``q_i`` and ``q6`` frozen.

    This is not a task-space fiber. It exists only to show that a joint freeze
    is distinct from ``h = n · d``.
    """
    if freeze_index < 0 or freeze_index >= 5:
        raise ValueError("freeze_index must be one of q1…q5")
    q_arr = np.asarray(q0, dtype=float).reshape(6)
    q6_star = float(q_arr[-1])
    q_i_star = float(q_arr[freeze_index])
    q_cur = tuple(float(x) for x in q_arr)
    state0 = chain.evaluate(q_cur)
    p0 = state0.p.copy()
    free = [i for i in range(5) if i != freeze_index]
    pid = f"freeze_q{freeze_index + 1}{'+' if direction > 0 else '-'}"

    def _tangent(q: tuple[float, ...], previous: Vec | None) -> Vec:
        jp = position_jacobian(chain, q)[:, free]
        report = matrix_rank_report(jp)
        _, _, vt = np.linalg.svd(jp, full_matrices=True)
        tangent = np.zeros(6)
        if report.nullity <= 0:
            return tangent
        col = vt[-1]
        for local, joint in enumerate(free):
            tangent[joint] = col[local]
        norm = float(np.linalg.norm(tangent))
        if norm == 0.0:
            return tangent
        tangent = tangent / norm
        if previous is not None and float(np.dot(tangent, previous)) < 0.0:
            tangent = -tangent
        elif previous is None:
            idx = int(np.argmax(np.abs(tangent)))
            if tangent[idx] < 0.0:
                tangent = -tangent
        return tangent

    def _correct(q: tuple[float, ...] | Vec) -> tuple[tuple[float, ...], int, float, float]:
        q_work = np.asarray(q, dtype=float).copy()
        q_start = q_work.copy()
        iters = 0
        residual = float("inf")
        for iters in range(1, MAX_CORRECTOR_ITERS + 1):
            state = chain.evaluate(tuple(float(x) for x in q_work))
            err = state.p - p0
            residual = float(np.linalg.norm(err))
            if residual <= CORRECTOR_NEWTON_TOL_M:
                break
            jp = position_jacobian(chain, tuple(float(x) for x in q_work))[:, free]
            dq, *_ = np.linalg.lstsq(jp, -err, rcond=None)
            for local, joint in enumerate(free):
                q_work[joint] += dq[local]
            q_work[freeze_index] = q_i_star
            q_work[-1] = q6_star
        q_corr = tuple(float(x) for x in q_work)
        return q_corr, iters, residual, float(np.linalg.norm(wrap_joint_delta(q_corr, q_start)))

    tangent = _tangent(q_cur, None)
    steps: list[FiberStep] = [
        FiberStep(
            sigma=0.0,
            path_id=pid,
            step_index=0,
            q_pred=q_cur,
            q=q_cur,
            d=as_vec3(state0.d),
            p_residual_m=0.0,
            h_residual=0.0,
            corrector_iterations=0,
            correction_norm=0.0,
            step_reductions=0,
            rank_jf=0,
            nullity_jf=1,
            tangent_dot=1.0,
            regular=True,
            label="seed",
            accepted=True,
        )
    ]
    dsigma = step_size * float(np.sign(direction) or 1.0)
    sigma_cur = 0.0
    for index in range(1, n_steps + 1):
        n_micro = 1
        if max_microstep is not None and max_microstep > 0.0 and abs(dsigma) > max_microstep:
            n_micro = int(np.ceil(abs(dsigma) / max_microstep))
        q_pred_full = np.asarray(q_cur, dtype=float) + tangent * dsigma
        q_pred_full[freeze_index] = q_i_star
        q_pred_full[-1] = q6_star
        q_work = np.asarray(q_cur, dtype=float)
        t_cur = tangent.copy()
        iters_total = 0
        max_corr = 0.0
        residual = float("inf")
        q_corr = q_cur
        state = chain.evaluate(q_corr)
        failed = False
        for _micro in range(n_micro):
            q_pred = q_work + t_cur * (dsigma / float(n_micro))
            q_pred[freeze_index] = q_i_star
            q_pred[-1] = q6_star
            q_corr, iters, residual, corr = _correct(q_pred)
            iters_total += iters
            max_corr = max(max_corr, corr)
            if residual > POSITION_RESIDUAL_TOL_M:
                failed = True
                break
            t_new = _tangent(q_corr, t_cur)
            q_work = np.asarray(q_corr, dtype=float)
            t_cur = t_new
            state = chain.evaluate(q_corr)
        step = FiberStep(
            sigma=sigma_cur + dsigma,
            path_id=pid,
            step_index=index,
            q_pred=tuple(float(x) for x in q_pred_full),
            q=q_corr,
            d=as_vec3(state.d),
            p_residual_m=residual,
            h_residual=0.0,
            corrector_iterations=iters_total,
            correction_norm=max_corr,
            step_reductions=0,
            rank_jf=0,
            nullity_jf=1,
            tangent_dot=float(np.dot(t_cur, tangent)),
            regular=not failed,
            label="regular" if not failed else "failed",
            accepted=not failed,
        )
        steps.append(step)
        if failed:
            break
        q_cur = q_corr
        tangent = t_cur
        sigma_cur = step.sigma
    return FiberPath(
        path_id=pid,
        n=(float("nan"), float("nan"), float("nan")),
        c=float("nan"),
        q0=tuple(float(x) for x in q_arr),
        p0=as_vec3(p0),
        q6_star=q6_star,
        steps=tuple(steps),
    )
