"""Chart-rank, reverse, loop, alternate-path, and duplicate diagnostics.

Conventions
-----------
Interior central differences wrap joint coordinates before division.
Pointing differences are ordinary Euclidean differences of unit vectors.
Rectangular loops are numerical integration diagnostics, not exact closure
tests on a curved manifold.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .continuation import (
    SequentialChart,
    continue_sequential_chart,
    continue_sequential_ray,
    seed_tangent_frame,
    wrap_joint_delta,
)
from .continuation_paths import ChartSample, TransportedTangentFrame
from .jacobians import matrix_rank_report
from .serial_chain import SerialRevoluteChain

Mat = NDArray[np.floating]

REVERSE_JOINT_TOL_RAD = 1e-6
REVERSE_POINTING_TOL = 1e-8
DUPLICATE_TOL_RAD = 1e-6
SHARED_NODE_JOINT_TOL_RAD = 1e-4
SHARED_NODE_POINTING_TOL = 1e-6


@dataclass(frozen=True, slots=True)
class ChartDifferential:
    s: float
    t: float
    singular_values: tuple[float, ...]
    rank: int
    condition: float
    angle_st_rad: float


@dataclass(frozen=True, slots=True)
class PointingDifferential:
    s: float
    t: float
    singular_values: tuple[float, ...]
    rank: int
    condition: float


@dataclass(frozen=True, slots=True)
class ReverseDiagnostics:
    architecture: str
    axis: str
    n_steps: int
    step_size: float
    epsilon_q: float
    epsilon_p: float
    epsilon_d: float
    forward_accepted: int
    reverse_accepted: int
    started_from_endpoint: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class LoopDiagnostics:
    n_steps: int
    step_size: float
    epsilon_q: float
    epsilon_p: float
    epsilon_d: float
    accepted_legs: int


@dataclass(frozen=True, slots=True)
class AlternatePathDiagnostics:
    s: float
    t: float
    step_size: float
    epsilon_q: float
    epsilon_p: float
    epsilon_d: float


@dataclass(frozen=True, slots=True)
class DuplicateReport:
    n_pairs_checked: int
    n_duplicates: int
    duplicate_pairs: tuple[tuple[tuple[float, float], tuple[float, float], float], ...]
    min_nn_distance: float
    collapsed_row: bool
    collapsed_column: bool


@dataclass(frozen=True, slots=True)
class ChartDiagnostics:
    chart_differentials: tuple[ChartDifferential, ...]
    pointing_differentials: tuple[PointingDifferential, ...]
    n_interior: int
    n_rank_q_two: int
    n_rank_d_two: int
    all_rank_two: bool


@dataclass(frozen=True, slots=True)
class RefinementComparison:
    n_shared: int
    max_joint_delta: float
    max_pointing_delta: float
    rank_classifications_match: bool
    passed: bool


def _sample_map(chart: SequentialChart) -> dict[tuple[float, float], ChartSample]:
    return {(round(sample.s, 12), round(sample.t, 12)): sample for sample in chart.samples}


def _svd_condition(sigmas: tuple[float, ...]) -> float:
    if len(sigmas) < 2 or sigmas[1] <= 0.0:
        return float("inf")
    return float(sigmas[0] / sigmas[1])


def chart_differentials(
    chart: SequentialChart,
    *,
    ds: float,
    dt: float,
) -> ChartDiagnostics:
    """Interior central-difference ranks of ``Q=[Qs Qt]`` and ``D=[Ds Dt]``."""
    lookup = _sample_map(chart)
    q_diffs: list[ChartDifferential] = []
    d_diffs: list[PointingDifferential] = []
    for sample in chart.samples:
        key_sp = (round(sample.s + ds, 12), round(sample.t, 12))
        key_sm = (round(sample.s - ds, 12), round(sample.t, 12))
        key_tp = (round(sample.s, 12), round(sample.t + dt, 12))
        key_tm = (round(sample.s, 12), round(sample.t - dt, 12))
        if not all(key in lookup for key in (key_sp, key_sm, key_tp, key_tm)):
            continue
        qs = wrap_joint_delta(lookup[key_sp].q, lookup[key_sm].q) / (2.0 * ds)
        qt = wrap_joint_delta(lookup[key_tp].q, lookup[key_tm].q) / (2.0 * dt)
        q_mat = np.column_stack([qs, qt])
        q_report = matrix_rank_report(q_mat)
        cosang = float(np.clip(np.dot(qs, qt) / (np.linalg.norm(qs) * np.linalg.norm(qt) + 1e-30), -1.0, 1.0))
        q_diffs.append(
            ChartDifferential(
                s=sample.s,
                t=sample.t,
                singular_values=q_report.singular_values,
                rank=q_report.rank,
                condition=_svd_condition(q_report.singular_values),
                angle_st_rad=float(np.arccos(cosang)),
            )
        )
        ds_vec = (np.asarray(lookup[key_sp].d) - np.asarray(lookup[key_sm].d)) / (2.0 * ds)
        dt_vec = (np.asarray(lookup[key_tp].d) - np.asarray(lookup[key_tm].d)) / (2.0 * dt)
        d_mat = np.column_stack([ds_vec, dt_vec])
        d_report = matrix_rank_report(d_mat)
        d_diffs.append(
            PointingDifferential(
                s=sample.s,
                t=sample.t,
                singular_values=d_report.singular_values,
                rank=d_report.rank,
                condition=_svd_condition(d_report.singular_values),
            )
        )
    n_q2 = sum(1 for item in q_diffs if item.rank == 2)
    n_d2 = sum(1 for item in d_diffs if item.rank == 2)
    return ChartDiagnostics(
        chart_differentials=tuple(q_diffs),
        pointing_differentials=tuple(d_diffs),
        n_interior=len(q_diffs),
        n_rank_q_two=n_q2,
        n_rank_d_two=n_d2,
        all_rank_two=len(q_diffs) > 0 and n_q2 == len(q_diffs) and n_d2 == len(d_diffs),
    )


def true_forward_reverse(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    axis: str,
    n_steps: int,
    step_size: float,
    architecture: str,
    joint_tol: float = REVERSE_JOINT_TOL_RAD,
    pointing_tol: float = REVERSE_POINTING_TOL,
) -> ReverseDiagnostics:
    """Continue ``m`` steps forward, then ``m`` reverse steps from the endpoint."""
    state0 = chain.evaluate(q0)
    forward, frame_end, _frames = continue_sequential_ray(
        chain, q0, axis=axis, direction=1.0, n_steps=n_steps, step_size=step_size, path_id=f"fwd_{axis}"
    )
    accepted_fwd = [step for step in forward.accepted if step.step_index > 0]
    if not accepted_fwd or accepted_fwd[-1].q is None:
        return ReverseDiagnostics(
            architecture=architecture,
            axis=axis,
            n_steps=n_steps,
            step_size=step_size,
            epsilon_q=float("inf"),
            epsilon_p=float("inf"),
            epsilon_d=float("inf"),
            forward_accepted=len(accepted_fwd),
            reverse_accepted=0,
            started_from_endpoint=False,
            passed=False,
        )
    endpoint = accepted_fwd[-1]
    reverse, _, _ = continue_sequential_ray(
        chain,
        endpoint.q,
        axis=axis,
        direction=-1.0,
        n_steps=n_steps,
        step_size=step_size,
        p0=state0.p,
        q6_star=q0[-1],
        seed_frame=frame_end,
        path_id=f"rev_{axis}",
        s0=endpoint.s,
        t0=endpoint.t,
    )
    accepted_rev = [step for step in reverse.accepted if step.step_index > 0]
    q_ret = accepted_rev[-1].q if accepted_rev and accepted_rev[-1].q is not None else None
    if q_ret is None:
        return ReverseDiagnostics(
            architecture=architecture,
            axis=axis,
            n_steps=n_steps,
            step_size=step_size,
            epsilon_q=float("inf"),
            epsilon_p=float("inf"),
            epsilon_d=float("inf"),
            forward_accepted=len(accepted_fwd),
            reverse_accepted=len(accepted_rev),
            started_from_endpoint=True,
            passed=False,
        )
    state_ret = chain.evaluate(q_ret)
    eps_q = float(np.linalg.norm(wrap_joint_delta(q_ret, q0)))
    eps_p = float(np.linalg.norm(state_ret.p - state0.p))
    eps_d = float(np.linalg.norm(state_ret.d - state0.d))
    return ReverseDiagnostics(
        architecture=architecture,
        axis=axis,
        n_steps=n_steps,
        step_size=step_size,
        epsilon_q=eps_q,
        epsilon_p=eps_p,
        epsilon_d=eps_d,
        forward_accepted=len(accepted_fwd),
        reverse_accepted=len(accepted_rev),
        started_from_endpoint=True,
        passed=eps_q <= joint_tol and eps_d <= pointing_tol and eps_p <= 1e-10,
    )


def rectangular_loop(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    n_steps: int,
    step_size: float,
) -> LoopDiagnostics:
    """Sequential ``+s +t -s -t`` commutator starting at ``q0``."""
    state0 = chain.evaluate(q0)
    q_cur = q0
    frame = seed_tangent_frame(chain, q0)
    s_cur = t_cur = 0.0
    accepted_legs = 0
    schedule = (("s", 1.0), ("t", 1.0), ("s", -1.0), ("t", -1.0))
    for axis, direction in schedule:
        path, frame, _ = continue_sequential_ray(
            chain,
            q_cur,
            axis=axis,
            direction=direction,
            n_steps=n_steps,
            step_size=step_size,
            p0=state0.p,
            q6_star=q0[-1],
            seed_frame=frame,
            path_id=f"loop_{axis}{'+' if direction > 0 else '-'}",
            s0=s_cur,
            t0=t_cur,
            max_microstep=None,
        )
        accepted = [step for step in path.accepted if step.step_index > 0]
        if len(accepted) < n_steps or accepted[-1].q is None:
            break
        accepted_legs += 1
        q_cur = accepted[-1].q
        s_cur, t_cur = accepted[-1].s, accepted[-1].t
        # Re-seed alignment at the corner from the arriving frame.
        frame = TransportedTangentFrame(
            q=q_cur,
            basis=frame.basis,
            principal_angles_rad=frame.principal_angles_rad,
        )
    state_end = chain.evaluate(q_cur)
    return LoopDiagnostics(
        n_steps=n_steps,
        step_size=step_size,
        epsilon_q=float(np.linalg.norm(wrap_joint_delta(q_cur, q0))),
        epsilon_p=float(np.linalg.norm(state_end.p - state0.p)),
        epsilon_d=float(np.linalg.norm(state_end.d - state0.d)),
        accepted_legs=accepted_legs,
    )


def alternate_path_to_target(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    s_target: float,
    t_target: float,
    step_size: float,
) -> AlternatePathDiagnostics:
    """Compare ``s``-then-``t`` versus ``t``-then-``s`` arrivals."""
    state0 = chain.evaluate(q0)
    n_s = int(round(abs(s_target) / step_size))
    n_t = int(round(abs(t_target) / step_size))
    seed = seed_tangent_frame(chain, q0)

    path_s, frame_s, _ = continue_sequential_ray(
        chain, q0, axis="s", direction=float(np.sign(s_target) or 1.0), n_steps=n_s,
        step_size=step_size, p0=state0.p, q6_star=q0[-1], seed_frame=seed, path_id="alt_s",
        max_microstep=None,
    )
    q_s = path_s.accepted[-1].q if path_s.accepted else None
    if q_s is None:
        return AlternatePathDiagnostics(s_target, t_target, step_size, float("inf"), float("inf"), float("inf"))
    path_st, _, _ = continue_sequential_ray(
        chain, q_s, axis="t", direction=float(np.sign(t_target) or 1.0), n_steps=n_t,
        step_size=step_size, p0=state0.p, q6_star=q0[-1], seed_frame=frame_s,
        path_id="alt_st", s0=path_s.accepted[-1].s, t0=0.0, max_microstep=None,
    )
    q_st = path_st.accepted[-1].q if path_st.accepted else None

    path_t, frame_t, _ = continue_sequential_ray(
        chain, q0, axis="t", direction=float(np.sign(t_target) or 1.0), n_steps=n_t,
        step_size=step_size, p0=state0.p, q6_star=q0[-1], seed_frame=seed, path_id="alt_t",
        max_microstep=None,
    )
    q_t = path_t.accepted[-1].q if path_t.accepted else None
    if q_t is None:
        return AlternatePathDiagnostics(s_target, t_target, step_size, float("inf"), float("inf"), float("inf"))
    path_ts, _, _ = continue_sequential_ray(
        chain, q_t, axis="s", direction=float(np.sign(s_target) or 1.0), n_steps=n_s,
        step_size=step_size, p0=state0.p, q6_star=q0[-1], seed_frame=frame_t,
        path_id="alt_ts", s0=0.0, t0=path_t.accepted[-1].t, max_microstep=None,
    )
    q_ts = path_ts.accepted[-1].q if path_ts.accepted else None
    if q_st is None or q_ts is None:
        return AlternatePathDiagnostics(s_target, t_target, step_size, float("inf"), float("inf"), float("inf"))
    state_st = chain.evaluate(q_st)
    state_ts = chain.evaluate(q_ts)
    return AlternatePathDiagnostics(
        s=s_target,
        t=t_target,
        step_size=step_size,
        epsilon_q=float(np.linalg.norm(wrap_joint_delta(q_st, q_ts))),
        epsilon_p=float(np.linalg.norm(state_st.p - state_ts.p)),
        epsilon_d=float(np.linalg.norm(np.asarray(state_st.d) - np.asarray(state_ts.d))),
    )


def duplicate_report(
    samples: tuple[ChartSample, ...] | list[ChartSample],
    *,
    tol_rad: float = DUPLICATE_TOL_RAD,
) -> DuplicateReport:
    rows: dict[float, list[ChartSample]] = {}
    cols: dict[float, list[ChartSample]] = {}
    items = list(samples)
    pairs: list[tuple[tuple[float, float], tuple[float, float], float]] = []
    nn = float("inf")
    checked = 0
    for i, a in enumerate(items):
        rows.setdefault(round(a.s, 12), []).append(a)
        cols.setdefault(round(a.t, 12), []).append(a)
        for b in items[i + 1 :]:
            checked += 1
            dist = float(np.linalg.norm(wrap_joint_delta(a.q, b.q)))
            nn = min(nn, dist)
            distinct_chart = abs(a.s - b.s) > 1e-12 or abs(a.t - b.t) > 1e-12
            if distinct_chart and dist < tol_rad:
                pairs.append(((a.s, a.t), (b.s, b.t), dist))
    collapsed_row = any(len(group) >= 3 and all(
        float(np.linalg.norm(wrap_joint_delta(group[0].q, item.q))) < tol_rad for item in group[1:]
    ) for group in rows.values())
    collapsed_col = any(len(group) >= 3 and all(
        float(np.linalg.norm(wrap_joint_delta(group[0].q, item.q))) < tol_rad for item in group[1:]
    ) for group in cols.values())
    return DuplicateReport(
        n_pairs_checked=checked,
        n_duplicates=len(pairs),
        duplicate_pairs=tuple(pairs),
        min_nn_distance=0.0 if not items else (0.0 if len(items) < 2 else nn),
        collapsed_row=collapsed_row,
        collapsed_column=collapsed_col,
    )


def compare_shared_nodes(
    coarse: SequentialChart,
    fine: SequentialChart,
    *,
    joint_tol: float = SHARED_NODE_JOINT_TOL_RAD,
    pointing_tol: float = SHARED_NODE_POINTING_TOL,
) -> RefinementComparison:
    fine_map = _sample_map(fine)
    deltas_q: list[float] = []
    deltas_d: list[float] = []
    rank_match = True
    for sample in coarse.samples:
        key = (round(sample.s, 12), round(sample.t, 12))
        other = fine_map.get(key)
        if other is None:
            continue
        deltas_q.append(float(np.linalg.norm(wrap_joint_delta(sample.q, other.q))))
        deltas_d.append(float(np.linalg.norm(np.asarray(sample.d) - np.asarray(other.d))))
        if sample.regular != other.regular or sample.rank_jd_nred != other.rank_jd_nred:
            rank_match = False
    max_q = max(deltas_q) if deltas_q else float("inf")
    max_d = max(deltas_d) if deltas_d else float("inf")
    return RefinementComparison(
        n_shared=len(deltas_q),
        max_joint_delta=max_q,
        max_pointing_delta=max_d,
        rank_classifications_match=rank_match,
        passed=bool(deltas_q) and max_q <= joint_tol and max_d <= pointing_tol and rank_match,
    )


def build_chart(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    ns: int,
    nt: int,
    ds: float,
    dt: float,
) -> SequentialChart:
    return continue_sequential_chart(chain, q0, ns=ns, nt=nt, ds=ds, dt=dt)


def synthetic_collapsed_chart(seed: ChartSample) -> tuple[ChartSample, ...]:
    """Deliberate rank-1 / duplicate fixture for diagnostic tests."""
    samples = []
    for i, s in enumerate((-0.03, 0.0, 0.03)):
        for j, t in enumerate((-0.03, 0.0, 0.03)):
            samples.append(
                ChartSample(
                    s=s,
                    t=t,
                    path_id="collapsed",
                    step_index=i * 3 + j,
                    q=seed.q,
                    d=seed.d,
                    p_residual_m=0.0,
                    corrector_iterations=0,
                    correction_norm=0.0,
                    step_reductions=0,
                    rank_jp=3,
                    rank_jpd=5,
                    rank_jd_nred=2,
                    tangent_principal_angle_1=0.0,
                    tangent_principal_angle_2=0.0,
                    regular=True,
                    label="collapsed",
                )
            )
    return tuple(samples)
