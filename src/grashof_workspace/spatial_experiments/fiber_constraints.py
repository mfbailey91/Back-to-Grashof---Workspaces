"""Task-space scalar fiber constraints on the aligned-terminal pointing parent.

Conventions
-----------
Joint order is ``(q1,...,q6)`` in radians. Pointing ``d`` is the unit terminal
axis in the world/space frame. The primary scalar is::

    h(q) = n · d(q)

with a fixed world-frame unit direction ``n``. The analytical gradient is::

    dh/dqi = n · (w_i × d) = (n^T J_d)_i

Under aligned terminal roll (``p`` on ``R6``, ``d ∥ w6``), ``dh/dq6 = 0``.

The reduced stacked constraint on ``q1…q5`` is::

    F(q) = [p(q) - p0; h(q) - c] ∈ R^4

with Jacobian ``J_F`` of shape ``(4, 5)``. At a regular independent seed,
``rank(J_F) = 4`` and ``nullity(J_F) = 1``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .jacobians import (
    ABS_RANK_TOL,
    REL_RANK_TOL,
    matrix_rank_report,
    nullspace,
    pointing_jacobian,
    position_jacobian,
)
from .serial_chain import SerialRevoluteChain

Mat = NDArray[np.floating]
Vec = NDArray[np.floating]

PRIMARY_N: tuple[float, float, float] = (0.0, 1.0, 0.0)
ALTERNATE_N: tuple[float, float, float] = (1.0, 0.0, 0.0)
DH_DQ6_TOL = 1e-12
SCALAR_RESIDUAL_TOL = 1e-12
N_PARALLEL_CROSS_TOL = 1e-8
JOINT_FREEZE_INDEX = 1


@dataclass(frozen=True, slots=True)
class FiberIndependenceReport:
    n: tuple[float, float, float]
    c: float
    n_dot_d: float
    n_cross_d_norm: float
    grad_h: tuple[float, ...]
    dh_dq6: float
    singular_values: tuple[float, ...]
    rank: int
    nullity: int
    threshold: float
    independent: bool
    dh_dq6_vanishes: bool


def _as_unit_n(n: tuple[float, ...] | Vec) -> Vec:
    arr = np.asarray(n, dtype=float).reshape(3)
    norm = float(np.linalg.norm(arr))
    if norm == 0.0:
        raise ValueError("fiber direction n must be nonzero")
    return arr / norm


def pointing_scalar(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    n: tuple[float, ...] | Vec,
) -> float:
    """Return ``h(q) = n · d(q)``."""
    n_hat = _as_unit_n(n)
    state = chain.evaluate(tuple(float(x) for x in np.asarray(q, dtype=float).reshape(-1)))
    return float(n_hat @ state.d)


def pointing_scalar_gradient(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    n: tuple[float, ...] | Vec,
) -> Vec:
    """Return analytical ``∇h = n^T J_d`` with shape ``(6,)``."""
    n_hat = _as_unit_n(n)
    jd = pointing_jacobian(chain, q)
    return jd.T @ n_hat


def position_scalar_jacobian(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    n: tuple[float, ...] | Vec,
) -> Mat:
    """Return stacked ``[J_p; ∇h]`` with shape ``(4, n)``."""
    jp = position_jacobian(chain, q)
    grad = pointing_scalar_gradient(chain, q, n)
    return np.vstack([jp, grad.reshape(1, -1)])


def reduced_fiber_jacobian(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    n: tuple[float, ...] | Vec,
) -> Mat:
    """Return the ``(4, 5)`` Jacobian of ``(p, h)`` on ``q1…q5``."""
    return position_scalar_jacobian(chain, q, n)[:, :5]


def fiber_independence_report(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    n: tuple[float, ...] | Vec,
    *,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
    dh_dq6_tol: float = DH_DQ6_TOL,
) -> FiberIndependenceReport:
    """Rank/nullity and roll-independence diagnostics for one scalar ``h``."""
    n_hat = _as_unit_n(n)
    q_t = tuple(float(x) for x in np.asarray(q, dtype=float).reshape(-1))
    state = chain.evaluate(q_t)
    n_dot_d = float(n_hat @ state.d)
    n_cross = float(np.linalg.norm(np.cross(n_hat, state.d)))
    grad = pointing_scalar_gradient(chain, q_t, n_hat)
    jf = reduced_fiber_jacobian(chain, q_t, n_hat)
    rank_report = matrix_rank_report(jf, abs_tol=abs_tol, rel_tol=rel_tol)
    dh_dq6 = float(grad[-1])
    independent = rank_report.rank == 4 and rank_report.nullity == 1 and n_cross > N_PARALLEL_CROSS_TOL
    return FiberIndependenceReport(
        n=tuple(float(x) for x in n_hat),
        c=n_dot_d,
        n_dot_d=n_dot_d,
        n_cross_d_norm=n_cross,
        grad_h=tuple(float(x) for x in grad),
        dh_dq6=dh_dq6,
        singular_values=rank_report.singular_values,
        rank=rank_report.rank,
        nullity=rank_report.nullity,
        threshold=rank_report.threshold,
        independent=independent,
        dh_dq6_vanishes=abs(dh_dq6) <= dh_dq6_tol,
    )


def reduced_fiber_tangent(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    n: tuple[float, ...] | Vec,
    *,
    previous: Vec | tuple[float, ...] | None = None,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
) -> Vec:
    """Return a unit ``R^6`` fiber tangent with zero ``q6`` component.

    If ``previous`` is given, the sign is chosen so the inner product is
    nonnegative. Otherwise the entry of largest magnitude is made positive.
    """
    jf = reduced_fiber_jacobian(chain, q, n)
    ker = nullspace(jf, abs_tol=abs_tol, rel_tol=rel_tol)
    tangent = np.zeros(6, dtype=float)
    if ker.shape[1] == 0:
        return tangent
    col = ker[:, 0].copy()
    if ker.shape[1] > 1:
        if previous is None:
            col = ker[:, 0].copy()
        else:
            prev5 = np.asarray(previous, dtype=float).reshape(-1)[:5]
            scores = ker.T @ prev5
            col = ker[:, int(np.argmax(np.abs(scores)))].copy()
    tangent[:5] = col
    norm = float(np.linalg.norm(tangent))
    if norm == 0.0:
        return tangent
    tangent = tangent / norm
    if previous is not None:
        prev = np.asarray(previous, dtype=float).reshape(-1)
        if float(np.dot(tangent, prev)) < 0.0:
            tangent = -tangent
    else:
        idx = int(np.argmax(np.abs(tangent)))
        if tangent[idx] < 0.0:
            tangent = -tangent
    return tangent
