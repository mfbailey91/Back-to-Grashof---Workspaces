"""Predictor-corrector continuation of the fixed-position roll-quotiented 6R.

Conventions
-----------
Constraint::

    F(q) = p(q) - p0 ∈ R³
    q6 = q6*

Sprint 04B sequential continuation predicts from the last accepted ``q_k``
using a Procrustes-aligned reduced tangent frame ``B_k`` recomputed at that
sample. The seed-frozen grid ``continue_fixed_position_patch`` is retained
only for Sprint 04 regression.

The general continuation API does not accept ``include_pairs`` or ``suur_map``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .compound_joints import correct_position, principal_angles
from .continuation_paths import (
    ChartSample,
    ContinuationPath,
    ContinuationStep,
    TransportedTangentFrame,
)
from .jacobians import (
    matrix_rank_report,
    pointing_jacobian,
    position_jacobian,
    reduced_pointing_basis,
)
from .serial_chain import SerialRevoluteChain
from .suur_coordinates import pair_intersection_distances

Mat = NDArray[np.floating]
Vec = NDArray[np.floating]

PATCH_NS = 9
PATCH_NT = 9
PATCH_DS = 0.03
PATCH_DT = 0.03
POSITION_RESIDUAL_TOL_M = 1e-10
E6_COL_TOL = 1e-9
MAX_CORRECTOR_ITERS = 20
MAX_STEP_REDUCTIONS = 3
MAX_TANGENT_PRINCIPAL_ANGLE_RAD = 0.5
MAX_CORRECTION_NORM_RAD = 0.5
CORRECTOR_NEWTON_TOL_M = 1e-14
MAX_MICROSTEP = 0.005


@dataclass(frozen=True, slots=True)
class ManifoldSample:
    s: float
    t: float
    q: tuple[float, ...]
    p_residual_m: float
    rank_jp: int
    rank_jpd: int
    rank_jd_nred: int
    regular: bool
    label: str
    d: tuple[float, float, float]
    dist_ua_m: float | None
    dist_ub_m: float | None


@dataclass(frozen=True, slots=True)
class ManifoldPatch:
    q0: tuple[float, ...]
    p0: tuple[float, float, float]
    q6_star: float
    chart_basis: tuple[tuple[float, ...], tuple[float, ...]]
    samples: tuple[ManifoldSample, ...]
    reverse_samples: tuple[ManifoldSample, ...]
    reverse_return_error: float


@dataclass(frozen=True, slots=True)
class SequentialChart:
    q0: tuple[float, ...]
    p0: tuple[float, float, float]
    d0: tuple[float, float, float]
    q6_star: float
    seed_frame: TransportedTangentFrame
    samples: tuple[ChartSample, ...]
    paths: tuple[ContinuationPath, ...]
    rejected_steps: tuple[ContinuationStep, ...]


def wrap_angle(delta: float) -> float:
    return float((delta + np.pi) % (2.0 * np.pi) - np.pi)


def wrap_joint_delta(q_a: tuple[float, ...] | Vec, q_b: tuple[float, ...] | Vec) -> Vec:
    delta = np.asarray(q_a, dtype=float).reshape(-1) - np.asarray(q_b, dtype=float).reshape(-1)
    return np.array([wrap_angle(float(x)) for x in delta], dtype=float)


def procrustes_align_frame(n_new: Mat, b_prev: Mat) -> tuple[Mat, Vec]:
    """Align ``N`` to ``B_prev`` by orthogonal Procrustes: ``B = N (U V^T)``."""
    n_mat = np.asarray(n_new, dtype=float)
    b_mat = np.asarray(b_prev, dtype=float)
    if n_mat.shape != b_mat.shape:
        raise ValueError("aligned frames must have matching shape")
    u, _sigma, vt = np.linalg.svd(n_mat.T @ b_mat, full_matrices=False)
    rotation = u @ vt
    aligned = n_mat @ rotation
    angles = principal_angles(n_mat, b_mat)
    return aligned, angles


def seed_tangent_frame(chain: SerialRevoluteChain, q0: tuple[float, ...]) -> TransportedTangentFrame:
    nred = reduced_pointing_basis(position_jacobian(chain, q0))
    if nred.shape[1] != 2:
        raise ValueError("seed requires a two-column N_red")
    return TransportedTangentFrame(
        q=q0,
        basis=(tuple(float(x) for x in nred[:, 0]), tuple(float(x) for x in nred[:, 1])),
        principal_angles_rad=(0.0, 0.0),
    )


def correct_position_detailed(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    p0: Vec,
    *,
    freeze_roll: bool = True,
    max_iter: int = MAX_CORRECTOR_ITERS,
    tol_m: float = CORRECTOR_NEWTON_TOL_M,
) -> tuple[tuple[float, ...], int, float, float]:
    """Newton-correct ``p(q)=p0`` and return ``(q, iters, residual, correction_norm)``."""
    q_arr = np.asarray(q, dtype=float).copy()
    q_start = q_arr.copy()
    p_target = np.asarray(p0, dtype=float).reshape(3)
    iters = 0
    residual = float(np.linalg.norm(chain.evaluate(tuple(float(x) for x in q_arr)).p - p_target))
    for iters in range(1, max_iter + 1):
        state = chain.evaluate(tuple(float(x) for x in q_arr))
        err = state.p - p_target
        residual = float(np.linalg.norm(err))
        if residual <= tol_m:
            break
        jp = position_jacobian(chain, tuple(float(x) for x in q_arr))
        if freeze_roll:
            dq, *_ = np.linalg.lstsq(jp[:, :5], -err, rcond=None)
            q_arr[:5] = q_arr[:5] + dq
        else:
            dq, *_ = np.linalg.lstsq(jp, -err, rcond=None)
            q_arr = q_arr + dq
    else:
        state = chain.evaluate(tuple(float(x) for x in q_arr))
        residual = float(np.linalg.norm(state.p - p_target))
    q_corr = tuple(float(x) for x in q_arr)
    correction_norm = float(np.linalg.norm(wrap_joint_delta(q_corr, q_start)))
    return q_corr, iters, residual, correction_norm


def _rank_bundle(chain: SerialRevoluteChain, q: tuple[float, ...], p_residual_m: float) -> dict[str, object]:
    jp = position_jacobian(chain, q)
    jd = pointing_jacobian(chain, q)
    jpd = np.vstack([jp, jd])
    rp = matrix_rank_report(jp)
    rpd = matrix_rank_report(jpd)
    nred = reduced_pointing_basis(jp)
    rank_jd_nred = 0 if nred.shape[1] == 0 else matrix_rank_report(jd @ nred).rank
    e6 = np.zeros(chain.n_joints)
    e6[-1] = 1.0
    regular = (
        rp.rank == 3
        and rpd.rank == 5
        and rpd.nullity == 1
        and rank_jd_nred == 2
        and nred.shape[1] == 2
        and float(np.linalg.norm(jp @ e6)) <= E6_COL_TOL
        and p_residual_m <= POSITION_RESIDUAL_TOL_M
    )
    if p_residual_m > POSITION_RESIDUAL_TOL_M:
        label = "failed"
    elif regular:
        label = "regular"
    else:
        label = "singular"
    return {
        "rank_jp": rp.rank,
        "rank_jpd": rpd.rank,
        "rank_jd_nred": rank_jd_nred,
        "nred": nred,
        "regular": regular,
        "label": label,
        "jp_sigmas": rp.singular_values,
        "jpd_sigmas": rpd.singular_values,
    }


def sequential_predictor_step(
    chain: SerialRevoluteChain,
    q_k: tuple[float, ...],
    frame: TransportedTangentFrame,
    ds: float,
    dt: float,
    p0: Vec,
    q6_star: float,
    *,
    path_id: str,
    step_index: int,
    s0: float,
    t0: float,
    max_reductions: int = MAX_STEP_REDUCTIONS,
    max_iter: int = MAX_CORRECTOR_ITERS,
    max_principal_angle: float = MAX_TANGENT_PRINCIPAL_ANGLE_RAD,
    max_correction_norm: float = MAX_CORRECTION_NORM_RAD,
    position_tol_m: float = POSITION_RESIDUAL_TOL_M,
    max_microstep: float | None = MAX_MICROSTEP,
) -> tuple[ContinuationStep | None, TransportedTangentFrame, tuple[ContinuationStep, ...]]:
    """Advance one sequential step from ``q_k``, halving up to ``max_reductions`` times.

    Returns ``(accepted_step_or_None, next_or_same_frame, rejected_attempts)``.
    """
    q_k_arr = np.asarray(q_k, dtype=float).reshape(6)
    b_start = frame.as_matrix()
    rejected: list[ContinuationStep] = []
    for reduction in range(max_reductions + 1):
        scale = 0.5**reduction
        ds_r = float(ds) * scale
        dt_r = float(dt) * scale
        length = float(np.hypot(ds_r, dt_r))
        n_micro = 1
        if max_microstep is not None and max_microstep > 0.0 and length > max_microstep:
            n_micro = int(np.ceil(length / max_microstep))
        q_cur = q_k_arr.copy()
        frame_cur = frame
        b_cur = b_start.copy()
        q_pred_first: tuple[float, ...] | None = None
        iters_total = 0
        corr_norm = 0.0
        residual = float("inf")
        q_corr = tuple(float(x) for x in q_cur)
        state = chain.evaluate(q_corr)
        bundle: dict[str, object] = {}
        angles = np.array([float("nan"), float("nan")])
        failed_label = None
        for _micro in range(n_micro):
            du = np.array([ds_r, dt_r], dtype=float) / float(n_micro)
            q_pred_arr = q_cur + b_cur @ du
            q_pred_arr[-1] = q6_star
            if q_pred_first is None:
                q_pred_first = tuple(float(x) for x in q_pred_arr)
            q_corr, iters, residual, corr_norm = correct_position_detailed(
                chain, tuple(float(x) for x in q_pred_arr), p0, freeze_roll=True, max_iter=max_iter
            )
            q_corr = (*q_corr[:5], q6_star)
            iters_total += iters
            state = chain.evaluate(q_corr)
            residual = float(np.linalg.norm(state.p - np.asarray(p0, dtype=float).reshape(3)))
            bundle = _rank_bundle(chain, q_corr, residual)
            nred = bundle["nred"]
            if residual > position_tol_m:
                failed_label = "failed"
                break
            if corr_norm > max_correction_norm:
                failed_label = "trust_radius"
                break
            if not isinstance(nred, np.ndarray) or nred.shape[1] != 2 or not bool(bundle["regular"]):
                failed_label = "rank_lost" if not bool(bundle["regular"]) else str(bundle["label"])
                break
            aligned, angles = procrustes_align_frame(nred, b_cur)
            if float(np.max(angles)) > max_principal_angle:
                failed_label = "tangent_jump"
                break
            q_cur = np.asarray(q_corr, dtype=float)
            b_cur = aligned
            frame_cur = TransportedTangentFrame(
                q=q_corr,
                basis=(tuple(float(x) for x in aligned[:, 0]), tuple(float(x) for x in aligned[:, 1])),
                principal_angles_rad=tuple(float(x) for x in angles),
            )
        accepted = failed_label is None
        label = "regular" if accepted else str(failed_label or bundle.get("label", "failed"))
        step = ContinuationStep(
            s=float(s0 + ds_r),
            t=float(t0 + dt_r),
            path_id=path_id,
            step_index=step_index,
            q_pred=q_pred_first,
            q=q_corr,
            d=tuple(float(x) for x in state.d),
            p_residual_m=residual,
            corrector_iterations=iters_total,
            correction_norm=corr_norm,
            step_reductions=reduction,
            rank_jp=int(bundle.get("rank_jp", 0)),  # type: ignore[arg-type]
            rank_jpd=int(bundle.get("rank_jpd", 0)),  # type: ignore[arg-type]
            rank_jd_nred=int(bundle.get("rank_jd_nred", 0)),  # type: ignore[arg-type]
            tangent_principal_angle_1=float(angles[0]) if angles.size else float("nan"),
            tangent_principal_angle_2=float(angles[1]) if angles.size > 1 else float("nan"),
            regular=bool(bundle.get("regular", False)) and accepted,
            label=label,
            accepted=accepted,
        )
        if accepted:
            return step, frame_cur, tuple(rejected)
        rejected.append(step)
    return None, frame, tuple(rejected)


def continue_sequential_ray(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    axis: str,
    direction: float,
    n_steps: int,
    step_size: float,
    p0: Vec | None = None,
    q6_star: float | None = None,
    seed_frame: TransportedTangentFrame | None = None,
    path_id: str | None = None,
    s0: float = 0.0,
    t0: float = 0.0,
    max_microstep: float | None = MAX_MICROSTEP,
) -> tuple[ContinuationPath, TransportedTangentFrame, dict[tuple[float, float], TransportedTangentFrame]]:
    """Continue ``n_steps`` along one chart axis from an accepted seed."""
    if axis not in {"s", "t"}:
        raise ValueError("axis must be 's' or 't'")
    if chain.n_joints != 6:
        raise ValueError("sequential continuation expects a 6R chain")
    q_arr = np.asarray(q0, dtype=float).reshape(6)
    q6 = float(q_arr[-1] if q6_star is None else q6_star)
    q_arr[-1] = q6
    q_cur = tuple(float(x) for x in q_arr)
    state0 = chain.evaluate(q_cur)
    p_target = state0.p.copy() if p0 is None else np.asarray(p0, dtype=float).reshape(3)
    frame = seed_frame if seed_frame is not None else seed_tangent_frame(chain, q_cur)
    pid = path_id or f"{axis}{'+' if direction > 0 else '-'}"
    steps: list[ContinuationStep] = []
    frames: dict[tuple[float, float], TransportedTangentFrame] = {}
    s_cur, t_cur = float(s0), float(t0)
    seed_residual = float(np.linalg.norm(state0.p - p_target))
    seed_bundle = _rank_bundle(chain, q_cur, seed_residual)
    seed_step = ContinuationStep(
        s=s_cur,
        t=t_cur,
        path_id=pid,
        step_index=0,
        q_pred=q_cur,
        q=q_cur,
        d=tuple(float(x) for x in state0.d),
        p_residual_m=seed_residual,
        corrector_iterations=0,
        correction_norm=0.0,
        step_reductions=0,
        rank_jp=int(seed_bundle["rank_jp"]),  # type: ignore[arg-type]
        rank_jpd=int(seed_bundle["rank_jpd"]),  # type: ignore[arg-type]
        rank_jd_nred=int(seed_bundle["rank_jd_nred"]),  # type: ignore[arg-type]
        tangent_principal_angle_1=0.0,
        tangent_principal_angle_2=0.0,
        regular=bool(seed_bundle["regular"]),
        label="seed" if seed_bundle["regular"] else str(seed_bundle["label"]),
        accepted=True,
    )
    steps.append(seed_step)
    frames[(round(s_cur, 12), round(t_cur, 12))] = frame
    ds = step_size * float(np.sign(direction) or 1.0) if axis == "s" else 0.0
    dt = step_size * float(np.sign(direction) or 1.0) if axis == "t" else 0.0
    for index in range(1, n_steps + 1):
        accepted, frame, rejected = sequential_predictor_step(
            chain,
            q_cur,
            frame,
            ds,
            dt,
            p_target,
            q6,
            path_id=pid,
            step_index=index,
            s0=s_cur,
            t0=t_cur,
            max_microstep=max_microstep,
        )
        steps.extend(rejected)
        if accepted is None:
            break
        steps.append(accepted)
        assert accepted.q is not None
        q_cur = accepted.q
        s_cur, t_cur = accepted.s, accepted.t
        frames[(round(s_cur, 12), round(t_cur, 12))] = frame
    return ContinuationPath(path_id=pid, steps=tuple(steps)), frame, frames


def continue_sequential_chart(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    ns: int = PATCH_NS,
    nt: int = PATCH_NT,
    ds: float = PATCH_DS,
    dt: float = PATCH_DT,
    q6: float | None = None,
) -> SequentialChart:
    """Row-wise sequential chart: centerline in ``s``, then ``±t`` from each node."""
    if chain.n_joints != 6:
        raise ValueError("sequential chart expects a 6R chain")
    q0_arr = np.asarray(q0, dtype=float).reshape(6)
    q6_star = float(q0_arr[-1] if q6 is None else q6)
    q0_arr[-1] = q6_star
    q0_t = tuple(float(x) for x in q0_arr)
    state0 = chain.evaluate(q0_t)
    p0 = state0.p.copy()
    d0 = tuple(float(x) for x in state0.d)
    seed_frame = seed_tangent_frame(chain, q0_t)
    samples: dict[tuple[float, float], ChartSample] = {}
    paths: list[ContinuationPath] = []
    rejected: list[ContinuationStep] = []

    def _record(step: ContinuationStep) -> None:
        if not step.accepted or step.q is None or step.d is None:
            rejected.append(step)
            return
        key = (round(step.s, 12), round(step.t, 12))
        samples[key] = ChartSample(
            s=step.s,
            t=step.t,
            path_id=step.path_id,
            step_index=step.step_index,
            q=step.q,
            d=step.d,
            p_residual_m=step.p_residual_m,
            corrector_iterations=step.corrector_iterations,
            correction_norm=step.correction_norm,
            step_reductions=step.step_reductions,
            rank_jp=step.rank_jp,
            rank_jpd=step.rank_jpd,
            rank_jd_nred=step.rank_jd_nred,
            tangent_principal_angle_1=step.tangent_principal_angle_1,
            tangent_principal_angle_2=step.tangent_principal_angle_2,
            regular=step.regular,
            label=step.label,
        )

    plus_s, _frame_plus_s, frames_plus = continue_sequential_ray(
        chain, q0_t, axis="s", direction=1.0, n_steps=ns // 2, step_size=ds, p0=p0, q6_star=q6_star,
        seed_frame=seed_frame, path_id="+s",
    )
    minus_s, _frame_minus_s, frames_minus = continue_sequential_ray(
        chain, q0_t, axis="s", direction=-1.0, n_steps=ns // 2, step_size=ds, p0=p0, q6_star=q6_star,
        seed_frame=seed_frame, path_id="-s",
    )
    paths.extend([plus_s, minus_s])
    for path in (plus_s, minus_s):
        for step in path.steps:
            _record(step)
    centerline_frames = {**frames_minus, **frames_plus}

    centerline = sorted(
        (sample for sample in samples.values() if abs(sample.t) <= 1e-15),
        key=lambda sample: sample.s,
    )
    for node in centerline:
        node_frame = centerline_frames[(round(node.s, 12), round(node.t, 12))]
        plus_t, _, _ = continue_sequential_ray(
            chain,
            node.q,
            axis="t",
            direction=1.0,
            n_steps=nt // 2,
            step_size=dt,
            p0=p0,
            q6_star=q6_star,
            seed_frame=node_frame,
            path_id=f"row_s={node.s:+.6f}_+t",
            s0=node.s,
            t0=0.0,
        )
        minus_t, _, _ = continue_sequential_ray(
            chain,
            node.q,
            axis="t",
            direction=-1.0,
            n_steps=nt // 2,
            step_size=dt,
            p0=p0,
            q6_star=q6_star,
            seed_frame=node_frame,
            path_id=f"row_s={node.s:+.6f}_-t",
            s0=node.s,
            t0=0.0,
        )
        paths.extend([plus_t, minus_t])
        for path in (plus_t, minus_t):
            for step in path.steps:
                if abs(step.t) <= 1e-15 and step.step_index == 0:
                    continue
                _record(step)

    return SequentialChart(
        q0=q0_t,
        p0=tuple(float(x) for x in p0),
        d0=d0,
        q6_star=q6_star,
        seed_frame=seed_frame,
        samples=tuple(sorted(samples.values(), key=lambda sample: (sample.s, sample.t))),
        paths=tuple(paths),
        rejected_steps=tuple(rejected),
    )


def _sample_at(
    chain: SerialRevoluteChain,
    q: tuple[float, ...],
    p0: Vec,
    s: float,
    t: float,
    *,
    include_pairs: bool,
) -> ManifoldSample:
    state = chain.evaluate(q)
    p_res = float(np.linalg.norm(state.p - p0))
    bundle = _rank_bundle(chain, q, p_res)
    dist_ua = dist_ub = None
    if include_pairs:
        dist_ua, dist_ub = pair_intersection_distances(chain, q)
    return ManifoldSample(
        s=float(s),
        t=float(t),
        q=q,
        p_residual_m=p_res,
        rank_jp=int(bundle["rank_jp"]),  # type: ignore[arg-type]
        rank_jpd=int(bundle["rank_jpd"]),  # type: ignore[arg-type]
        rank_jd_nred=int(bundle["rank_jd_nred"]),  # type: ignore[arg-type]
        regular=bool(bundle["regular"]),
        label=str(bundle["label"]),
        d=tuple(float(x) for x in state.d),
        dist_ua_m=None if dist_ua is None else float(dist_ua),
        dist_ub_m=None if dist_ub is None else float(dist_ub),
    )


def continue_fixed_position_patch(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    ns: int = PATCH_NS,
    nt: int = PATCH_NT,
    ds: float = PATCH_DS,
    dt: float = PATCH_DT,
    q6: float | None = None,
    include_pairs: bool = False,
) -> ManifoldPatch:
    """Sprint 04 seed-frozen local ``(s,t)`` patch. Prefer sequential continuation."""
    if chain.n_joints != 6:
        raise ValueError("fixed-position patch expects a 6R chain")
    q0_arr = np.asarray(q0, dtype=float).reshape(6)
    q6_star = float(q0_arr[-1] if q6 is None else q6)
    q0_arr[-1] = q6_star
    q0_t = tuple(float(x) for x in q0_arr)
    state0 = chain.evaluate(q0_t)
    p0 = state0.p.copy()
    nred0 = reduced_pointing_basis(position_jacobian(chain, q0_t))
    if nred0.shape[1] != 2:
        raise ValueError("chart requires a two-column N_red at q0")
    v1 = nred0[:, 0]
    v2 = nred0[:, 1]
    s_vals = np.linspace(-(ns // 2) * ds, (ns // 2) * ds, ns)
    t_vals = np.linspace(-(nt // 2) * dt, (nt // 2) * dt, nt)
    samples: list[ManifoldSample] = []
    for s in s_vals:
        for t in t_vals:
            q_pred = q0_arr + float(s) * v1 + float(t) * v2
            q_pred[-1] = q6_star
            q_corr = correct_position(chain, tuple(float(x) for x in q_pred), p0, freeze_roll=True)
            q_corr = (*q_corr[:5], q6_star)
            samples.append(_sample_at(chain, q_corr, p0, float(s), float(t), include_pairs=include_pairs))

    reverse: list[ManifoldSample] = []
    q_cur = q0_arr.copy()
    ray_steps = list(range(1, ns // 2 + 1)) + list(range(ns // 2 - 1, -1, -1))
    for k in ray_steps:
        s = k * ds
        q_pred = q0_arr + s * v1
        q_pred[-1] = q6_star
        q_corr = correct_position(chain, tuple(float(x) for x in q_pred), p0, freeze_roll=True)
        q_corr = (*q_corr[:5], q6_star)
        reverse.append(_sample_at(chain, q_corr, p0, float(s), 0.0, include_pairs=include_pairs))
        q_cur = np.asarray(q_corr, dtype=float)
    return_err = float(np.linalg.norm(q_cur[:5] - q0_arr[:5]))
    return ManifoldPatch(
        q0=q0_t,
        p0=tuple(float(x) for x in p0),
        q6_star=q6_star,
        chart_basis=(tuple(float(x) for x in v1), tuple(float(x) for x in v2)),
        samples=tuple(samples),
        reverse_samples=tuple(reverse),
        reverse_return_error=return_err,
    )
