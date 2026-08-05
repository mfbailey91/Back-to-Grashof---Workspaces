"""Predictor-corrector continuation of the fixed-position roll-quotiented 6R.

Conventions
-----------
Constraint::

    F(q) = p(q) - p0 ∈ R³
    q6 = q6*

Predictor steps use the chart-fixed ``N_red`` basis at ``q0``. The corrector is
Newton on ``p(q)=p0`` with ``q6`` frozen. This is a local 2D patch, not a fiber
and not a spherical four-bar solver.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .compound_joints import correct_position
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
        and p_res <= POSITION_RESIDUAL_TOL_M
    )
    if p_res > POSITION_RESIDUAL_TOL_M:
        label = "failed"
    elif regular:
        label = "regular"
    else:
        label = "singular"
    dist_ua = dist_ub = None
    if include_pairs:
        dist_ua, dist_ub = pair_intersection_distances(chain, q)
    return ManifoldSample(
        s=float(s),
        t=float(t),
        q=q,
        p_residual_m=p_res,
        rank_jp=rp.rank,
        rank_jpd=rpd.rank,
        rank_jd_nred=rank_jd_nred,
        regular=regular,
        label=label,
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
    """Return a local ``(s,t)`` predictor-corrector patch about ``q0``."""
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
