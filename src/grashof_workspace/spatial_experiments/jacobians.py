"""Analytical and numerical Jacobians plus rank diagnostics for serial chains.

Conventions
-----------
For ``q in R^n``::

    J_p[:, i] = w_i(q) × (p(q) - r_i(q))
    J_d[:, i] = w_i(q) × d(q)
    J_pd = [J_p; J_d]

Joint index ``i`` is zero-based (``e6`` is the last standard-basis vector when
``n = 6``). Rank uses::

    threshold = max(abs_tol, rel_tol * σ_max)
    abs_tol = 1e-10
    rel_tol = 1e-9
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .serial_chain import SerialRevoluteChain

Mat = NDArray[np.floating]

ABS_RANK_TOL = 1e-10
REL_RANK_TOL = 1e-9


@dataclass(frozen=True, slots=True)
class RankReport:
    """SVD rank report with explicit thresholds and all singular values."""

    singular_values: tuple[float, ...]
    abs_tol: float
    rel_tol: float
    threshold: float
    rank: int
    nullity: int
    matrix_shape: tuple[int, int]
    frobenius_norm: float


def position_jacobian(chain: SerialRevoluteChain, q: tuple[float, ...] | NDArray[np.floating]) -> Mat:
    """Return analytical ``J_p`` with shape ``(3, n)``."""
    state = chain.evaluate(q)
    cols = []
    for axis in state.axes:
        cols.append(np.cross(axis.w_array, state.p - axis.r_array))
    return np.column_stack(cols)


def pointing_jacobian(chain: SerialRevoluteChain, q: tuple[float, ...] | NDArray[np.floating]) -> Mat:
    """Return analytical ``J_d`` with shape ``(3, n)``."""
    state = chain.evaluate(q)
    cols = []
    for axis in state.axes:
        cols.append(np.cross(axis.w_array, state.d))
    return np.column_stack(cols)


def position_pointing_jacobian(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | NDArray[np.floating],
) -> Mat:
    """Return stacked ``J_pd`` with shape ``(6, n)``."""
    return np.vstack([position_jacobian(chain, q), pointing_jacobian(chain, q)])


def central_difference_jacobians(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | NDArray[np.floating],
    h: float,
) -> tuple[Mat, Mat]:
    """Central finite-difference estimates of ``J_p`` and ``J_d``."""
    if h <= 0.0:
        raise ValueError("finite-difference step h must be positive")
    q0 = np.asarray(q, dtype=float).reshape(-1)
    n = q0.size
    jp = np.zeros((3, n))
    jd = np.zeros((3, n))
    for i in range(n):
        qp = q0.copy()
        qm = q0.copy()
        qp[i] += h
        qm[i] -= h
        sp = chain.evaluate(tuple(float(x) for x in qp))
        sm = chain.evaluate(tuple(float(x) for x in qm))
        jp[:, i] = (sp.p - sm.p) / (2.0 * h)
        jd[:, i] = (sp.d - sm.d) / (2.0 * h)
    return jp, jd


def matrix_rank_report(
    A: Mat,
    *,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
) -> RankReport:
    """Return SVD rank, nullity, threshold, and all singular values."""
    mat = np.asarray(A, dtype=float)
    if mat.ndim != 2:
        raise ValueError("rank report requires a 2D matrix")
    s = np.linalg.svd(mat, compute_uv=False)
    sigma_max = float(s[0]) if s.size else 0.0
    threshold = max(abs_tol, rel_tol * sigma_max)
    rank = int(np.sum(s > threshold))
    nullity = int(mat.shape[1] - rank)
    return RankReport(
        singular_values=tuple(float(x) for x in s),
        abs_tol=abs_tol,
        rel_tol=rel_tol,
        threshold=threshold,
        rank=rank,
        nullity=nullity,
        matrix_shape=(int(mat.shape[0]), int(mat.shape[1])),
        frobenius_norm=float(np.linalg.norm(mat)),
    )


def nullspace(A: Mat, *, abs_tol: float = ABS_RANK_TOL, rel_tol: float = REL_RANK_TOL) -> Mat:
    """Return an orthonormal basis for ``ker(A)`` as columns."""
    mat = np.asarray(A, dtype=float)
    report = matrix_rank_report(mat, abs_tol=abs_tol, rel_tol=rel_tol)
    _, _, vt = np.linalg.svd(mat, full_matrices=True)
    if report.nullity <= 0:
        return np.zeros((mat.shape[1], 0))
    return vt[-report.nullity :, :].T


def reduced_pointing_basis(
    J_p: Mat,
    *,
    roll_index: int = -1,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
) -> Mat:
    """Return ``N_red``: ``ker(J_p)`` with the terminal-roll direction removed.

    The roll direction is the standard-basis vector ``e_{roll_index}`` in joint
    space (default: last joint). Remaining null vectors are orthonormalized.
    """
    ker = nullspace(J_p, abs_tol=abs_tol, rel_tol=rel_tol)
    n = int(J_p.shape[1])
    idx = roll_index if roll_index >= 0 else n + roll_index
    if ker.shape[1] == 0:
        return ker
    e_roll = np.zeros(n)
    e_roll[idx] = 1.0
    coords = ker.T @ e_roll
    u = ker @ coords
    un = float(np.linalg.norm(u))
    if un <= abs_tol:
        return ker
    u = u / un
    remainder = ker - np.outer(u, u @ ker)
    left, s, _vt = np.linalg.svd(remainder, full_matrices=False)
    sigma_max = float(s[0]) if s.size else 0.0
    threshold = max(abs_tol, rel_tol * sigma_max)
    keep = s > threshold
    if not np.any(keep):
        return np.zeros((n, 0))
    return left[:, keep]


def kernel_alignment_to_unit(vector: NDArray[np.floating], e: NDArray[np.floating]) -> float:
    """Return ``sin(theta)`` between ``vector`` and ``e`` (0 iff parallel)."""
    v = np.asarray(vector, dtype=float).reshape(-1)
    ev = np.asarray(e, dtype=float).reshape(-1)
    vn = float(np.linalg.norm(v))
    en = float(np.linalg.norm(ev))
    if vn == 0.0 or en == 0.0:
        raise ValueError("cannot align a zero vector")
    cos_theta = abs(float(np.dot(v, ev))) / (vn * en)
    cos_theta = min(1.0, cos_theta)
    return float(np.sqrt(max(0.0, 1.0 - cos_theta * cos_theta)))
