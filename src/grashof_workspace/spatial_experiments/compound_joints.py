"""Deprecated non-discriminating compound-tangent probes.

These helpers compare ``ker(J_p[:, :5])`` to ``N_red``. That comparison is the
terminal-roll quotient and does **not** test ``UA``/``UB`` intersection
geometry (Check-in 3 / ADR 002). Keep them only as a negative-control
oracle showing that skew chains still produce zero principal angles.

Discriminating SUUR tests live in ``suur_coordinates.py``. Predictor-corrector
continuation lives in ``continuation.py``.
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
    position_jacobian,
    reduced_pointing_basis,
)
from .serial_chain import SerialRevoluteChain

Mat = NDArray[np.floating]
Vec = NDArray[np.floating]

COMPOUND_GROUPS = {
    "UA": (0, 1),
    "UB": (2, 3),
    "RC": (4,),
    "roll": (5,),
}

PRINCIPAL_ANGLE_TOL_RAD = 1e-8
STEP_DT = 1e-3
N_LOCAL_STEPS = 3
POSITION_RESIDUAL_TOL_M = 1e-10
POINTING_AGREE_TOL = 1e-8


@dataclass(frozen=True, slots=True)
class PrincipalAngleReport:
    angles_rad: tuple[float, ...]
    max_angle_rad: float
    within_tolerance: bool


def embed_compound_tangent(v: Vec | tuple[float, ...]) -> Vec:
    """Embed a 5-vector into ``R^6`` with ``q6=0``, stripping residual ``e6``."""
    arr = np.asarray(v, dtype=float).reshape(-1)
    out = np.zeros(6)
    if arr.size == 5:
        out[:5] = arr
    elif arr.size == 6:
        out[:5] = arr[:5]
    else:
        raise ValueError("compound tangent must have 5 or 6 components")
    return out


def compound_reduced_basis(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    *,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
) -> Mat:
    """Return embedded ``ker(J_p[:, :5])`` as orthonormal columns in ``R^6``."""
    jp = position_jacobian(chain, q)
    ker5 = nullspace(jp[:, :5], abs_tol=abs_tol, rel_tol=rel_tol)
    if ker5.shape[1] == 0:
        return np.zeros((6, 0))
    embedded = np.zeros((6, ker5.shape[1]))
    for j in range(ker5.shape[1]):
        embedded[:, j] = embed_compound_tangent(ker5[:, j])
    q_orth, _r = np.linalg.qr(embedded, mode="reduced")
    report = matrix_rank_report(q_orth, abs_tol=abs_tol, rel_tol=rel_tol)
    return q_orth[:, : report.rank]


def principal_angles(a: Mat, b: Mat) -> Vec:
    """Return principal angles between the column spaces of ``a`` and ``b``.

    Interior: identical subspaces yield angles ``0``.
    Exterior: orthogonal subspaces of equal dimension yield ``π/2``.
    Boundary: mixed shared / orthogonal directions yield ``(0, π/2)``.
    """
    a_mat = np.asarray(a, dtype=float)
    b_mat = np.asarray(b, dtype=float)
    if a_mat.ndim != 2 or b_mat.ndim != 2:
        raise ValueError("principal angles require 2D bases")
    if a_mat.shape[0] != b_mat.shape[0]:
        raise ValueError("bases must live in the same ambient dimension")
    if a_mat.shape[1] == 0 or b_mat.shape[1] == 0:
        raise ValueError("cannot compare an empty subspace")
    qa, _ = np.linalg.qr(a_mat, mode="reduced")
    qb, _ = np.linalg.qr(b_mat, mode="reduced")
    s = np.linalg.svd(qa.T @ qb, compute_uv=False)
    return np.arccos(np.clip(s, 0.0, 1.0))


def compare_reduced_tangents(
    chain: SerialRevoluteChain,
    q: tuple[float, ...],
    *,
    tol_rad: float = PRINCIPAL_ANGLE_TOL_RAD,
) -> PrincipalAngleReport:
    """Compare physical ``N_red`` with the embedded compound reduced basis."""
    n_phys = reduced_pointing_basis(position_jacobian(chain, q))
    n_comp = compound_reduced_basis(chain, q)
    angles = principal_angles(n_phys, n_comp)
    max_angle = float(np.max(angles)) if angles.size else float("inf")
    return PrincipalAngleReport(
        angles_rad=tuple(float(x) for x in angles),
        max_angle_rad=max_angle,
        within_tolerance=max_angle <= tol_rad,
    )


def correct_position(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    p0: Vec,
    *,
    freeze_roll: bool = True,
    max_iter: int = 12,
    tol_m: float = 1e-14,
) -> tuple[float, ...]:
    """Newton corrector on ``p(q)=p0`` only, optionally freezing ``q6``."""
    q_arr = np.asarray(q, dtype=float).copy()
    p_target = np.asarray(p0, dtype=float).reshape(3)
    for _ in range(max_iter):
        state = chain.evaluate(tuple(float(x) for x in q_arr))
        err = state.p - p_target
        if float(np.linalg.norm(err)) <= tol_m:
            break
        jp = position_jacobian(chain, tuple(float(x) for x in q_arr))
        if freeze_roll:
            dq, *_ = np.linalg.lstsq(jp[:, :5], -err, rcond=None)
            q_arr[:5] = q_arr[:5] + dq
        else:
            dq, *_ = np.linalg.lstsq(jp, -err, rcond=None)
            q_arr = q_arr + dq
    return tuple(float(x) for x in q_arr)


def _align_basis_column(basis: Mat, previous: Vec | None) -> Vec:
    if basis.shape[1] == 0:
        raise ValueError("empty reduced basis")
    if previous is None:
        col = basis[:, 0].copy()
    else:
        scores = basis.T @ previous
        col = basis[:, int(np.argmax(np.abs(scores)))].copy()
        if float(np.dot(col, previous)) < 0.0:
            col = -col
    n = float(np.linalg.norm(col))
    if n == 0.0:
        raise ValueError("zero reduced direction")
    return col / n


def local_nred_steps(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    *,
    n_steps: int = N_LOCAL_STEPS,
    dt: float = STEP_DT,
    correct: bool = True,
    compound: bool = False,
    seed_direction: Vec | tuple[float, ...] | None = None,
) -> list[dict[str, float | int | tuple[float, ...]]]:
    """Take short Euler steps along a unit ``N_red`` (or compound) direction."""
    q = np.asarray(q0, dtype=float).copy()
    s0 = chain.evaluate(tuple(float(x) for x in q))
    p0 = s0.p.copy()
    d0 = s0.d.copy()
    previous: Vec | None = None
    if seed_direction is not None:
        previous = np.asarray(seed_direction, dtype=float).reshape(-1).copy()
        if compound:
            previous = embed_compound_tangent(previous)
        n = float(np.linalg.norm(previous))
        if n == 0.0:
            raise ValueError("zero seed direction")
        previous = previous / n
    records: list[dict[str, float | int | tuple[float, ...]]] = []
    for step in range(1, n_steps + 1):
        if compound:
            basis = compound_reduced_basis(chain, tuple(float(x) for x in q))
        else:
            basis = reduced_pointing_basis(position_jacobian(chain, tuple(float(x) for x in q)))
        direction = _align_basis_column(basis, previous)
        q = q + dt * direction
        if correct:
            q = np.asarray(correct_position(chain, tuple(float(x) for x in q), p0), dtype=float)
        state = chain.evaluate(tuple(float(x) for x in q))
        records.append(
            {
                "step": step,
                "q": tuple(float(x) for x in q),
                "p_residual_m": float(np.linalg.norm(state.p - p0)),
                "pointing_delta": float(np.linalg.norm(state.d - d0)),
                "d": tuple(float(x) for x in state.d),
            }
        )
        previous = direction
    return records
