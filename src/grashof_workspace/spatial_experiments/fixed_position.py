"""Fixed-position problem and seed audit for spatial open chains.

Conventions
-----------
At seed ``q0`` set ``p* = p(q0)`` and consider the constraint ``p(q) - p* = 0``.
For a spatial ``nR`` chain at a regular configuration::

    dim F_{p*} = n - rank(J_p)

For spatial 4R with full translational rank::

    rank(J_p) = 3,  nullity = 1,  M = 1

Virtual closure metadata records an exact ``S_v`` at ``p*``; it is not a
four-bar decomposition certificate.

The seed audit also records a *motion signature*.  This prevents a regular
rank-three source from being mistaken for a nontrivial spatial self-motion when
the nullspace is merely the explicit terminal-roll direction.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import as_vec3, point_axis_distance
from .jacobians import (
    ABS_RANK_TOL,
    REL_RANK_TOL,
    central_difference_jacobians,
    matrix_rank_report,
    nullspace,
    pointing_jacobian,
    position_jacobian,
)
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

Vec = NDArray[np.floating]

POSITION_RESIDUAL_TOL_M = 1e-10
EXPECTED_SPATIAL_RANK = 3
JACOBIAN_FD_STEP_RAD = 1e-6
JACOBIAN_FD_ERROR_TOL = 1e-7
TERMINAL_AXIS_DISTANCE_TOL_M = 1e-10
TERMINAL_TANGENT_ALIGNMENT_TOL = 1e-8
POINTING_SPEED_TOL = 1e-8
UPSTREAM_TANGENT_TOL = 1e-8


@dataclass(frozen=True, slots=True)
class VirtualClosureResult:
    """Exact virtual spherical closure metadata at the task point."""

    kind: str
    center: tuple[float, float, float]
    mobility_formula: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FixedPositionProblem:
    """Fixed Cartesian task posed on an open chain."""

    architecture_id: str
    chain: SerialRevoluteChain
    q0: tuple[float, ...]
    p_star: tuple[float, float, float]
    virtual_closure: VirtualClosureResult


@dataclass(frozen=True, slots=True)
class FixedPositionSeedAudit:
    """Rank/nullity and source-motion diagnostics at a fixed-position seed."""

    architecture_id: str
    q0: tuple[float, ...]
    p_star: tuple[float, float, float]
    p_residual_m: float
    singular_values: tuple[float, ...]
    rank_jp: int
    nullity_jp: int
    threshold: float
    regular: bool
    status: str
    virtual_closure_kind: str
    jp_column_norms: tuple[float, ...]
    terminal_axis_distance_m: float
    tangent: tuple[float, ...] | None
    terminal_tangent_alignment_error: float | None
    upstream_tangent_norm: float | None
    pointing_speed: float | None
    finite_difference_jp_error_fro: float
    finite_difference_verified: bool
    motion_signature: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def pose_fixed_position_problem(
    model: OpenChainModel,
    q0: tuple[float, ...],
) -> FixedPositionProblem:
    """Build ``p* = p(q0)`` with virtual ``S_v`` closure metadata."""
    q_t = tuple(float(x) for x in np.asarray(q0, dtype=float).reshape(-1))
    if len(q_t) != model.n_joints:
        raise ValueError(f"q0 length {len(q_t)} != n_joints {model.n_joints}")
    state = model.chain.evaluate(q_t)
    p_star = as_vec3(state.p)
    n = model.n_joints
    closure = VirtualClosureResult(
        kind="S_v",
        center=p_star,
        mobility_formula=f"M = {n} - 3 = {n - 3} at regular full-rank seeds",
        notes=(
            "Virtual spherical closure is exact for the fixed-position constraint.",
            "Not a spatial-four-bar decomposition certificate.",
        ),
    )
    return FixedPositionProblem(
        architecture_id=model.architecture_id,
        chain=model.chain,
        q0=q_t,
        p_star=p_star,
        virtual_closure=closure,
    )


def _terminal_alignment_error(tangent: Vec) -> float:
    e_terminal = np.zeros_like(tangent)
    e_terminal[-1] = 1.0
    return float(
        min(
            np.linalg.norm(tangent - e_terminal),
            np.linalg.norm(tangent + e_terminal),
        )
    )


def _motion_signature(
    *,
    regular: bool,
    terminal_axis_distance_m: float,
    terminal_alignment_error: float | None,
    upstream_tangent_norm: float | None,
    pointing_speed: float | None,
) -> str:
    if not regular:
        return "SINGULAR_OR_EMPTY"
    assert terminal_alignment_error is not None
    assert upstream_tangent_norm is not None
    assert pointing_speed is not None
    if (
        terminal_axis_distance_m <= TERMINAL_AXIS_DISTANCE_TOL_M
        and terminal_alignment_error <= TERMINAL_TANGENT_ALIGNMENT_TOL
        and upstream_tangent_norm <= UPSTREAM_TANGENT_TOL
        and pointing_speed <= POINTING_SPEED_TOL
    ):
        return "PURE_TERMINAL_ROLL"
    if pointing_speed > POINTING_SPEED_TOL:
        return "NONTRIVIAL_POINTING_CURVE"
    return "NONTRIVIAL_FIXED_POSITION_ORIENTATION_CURVE"


def audit_fixed_position_seed(
    problem: FixedPositionProblem,
    *,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
    position_tol_m: float = POSITION_RESIDUAL_TOL_M,
    expected_rank: int = EXPECTED_SPATIAL_RANK,
    fd_step_rad: float = JACOBIAN_FD_STEP_RAD,
    fd_error_tol: float = JACOBIAN_FD_ERROR_TOL,
) -> FixedPositionSeedAudit:
    """Report regularity and whether the source motion is terminal-roll-only.

    The analytical position Jacobian is independently cross-checked against a
    central finite-difference derivative of the forward-kinematics function.
    """
    chain = problem.chain
    q0 = problem.q0
    state = chain.evaluate(q0)
    p_star = np.asarray(problem.p_star, dtype=float)
    residual = float(np.linalg.norm(state.p - p_star))
    jp = position_jacobian(chain, q0)
    report = matrix_rank_report(jp, abs_tol=abs_tol, rel_tol=rel_tol)
    expected_nullity = int(chain.n_joints - expected_rank)
    regular = (
        residual <= position_tol_m
        and report.rank == expected_rank
        and report.nullity == expected_nullity
    )

    jp_fd, _jd_fd = central_difference_jacobians(chain, q0, fd_step_rad)
    fd_error = float(np.linalg.norm(jp - jp_fd, ord="fro"))
    fd_verified = fd_error <= fd_error_tol

    terminal_axis = state.axes[-1]
    terminal_distance = point_axis_distance(state.p, terminal_axis)
    column_norms = tuple(float(np.linalg.norm(jp[:, i])) for i in range(jp.shape[1]))

    tangent_tuple: tuple[float, ...] | None = None
    alignment_error: float | None = None
    upstream_norm: float | None = None
    pointing_speed: float | None = None
    if regular:
        tangent = fixed_position_tangent(chain, q0, abs_tol=abs_tol, rel_tol=rel_tol)
        tangent_tuple = tuple(float(x) for x in tangent)
        alignment_error = _terminal_alignment_error(tangent)
        upstream_norm = float(np.linalg.norm(tangent[:-1]))
        pointing_speed = float(np.linalg.norm(pointing_jacobian(chain, q0) @ tangent))

    signature = _motion_signature(
        regular=regular,
        terminal_axis_distance_m=terminal_distance,
        terminal_alignment_error=alignment_error,
        upstream_tangent_norm=upstream_norm,
        pointing_speed=pointing_speed,
    )

    if regular and fd_verified:
        status = "PASS"
    elif report.rank < expected_rank or not fd_verified:
        status = "FAIL"
    else:
        status = "REVIEW"

    return FixedPositionSeedAudit(
        architecture_id=problem.architecture_id,
        q0=q0,
        p_star=problem.p_star,
        p_residual_m=residual,
        singular_values=report.singular_values,
        rank_jp=report.rank,
        nullity_jp=report.nullity,
        threshold=report.threshold,
        regular=regular,
        status=status,
        virtual_closure_kind=problem.virtual_closure.kind,
        jp_column_norms=column_norms,
        terminal_axis_distance_m=terminal_distance,
        tangent=tangent_tuple,
        terminal_tangent_alignment_error=alignment_error,
        upstream_tangent_norm=upstream_norm,
        pointing_speed=pointing_speed,
        finite_difference_jp_error_fro=fd_error,
        finite_difference_verified=fd_verified,
        motion_signature=signature,
    )


def fixed_position_tangent(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    *,
    previous: Vec | tuple[float, ...] | None = None,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
) -> Vec:
    """Return a unit null tangent of ``J_p`` (one-DOF fiber chart)."""
    jp = position_jacobian(chain, q)
    ker = nullspace(jp, abs_tol=abs_tol, rel_tol=rel_tol)
    if ker.shape[1] == 0:
        return np.zeros(chain.n_joints, dtype=float)
    col = ker[:, 0].copy()
    if ker.shape[1] > 1 and previous is not None:
        prev = np.asarray(previous, dtype=float).reshape(-1)
        scores = ker.T @ prev
        col = ker[:, int(np.argmax(np.abs(scores)))].copy()
    norm = float(np.linalg.norm(col))
    if norm == 0.0:
        return col
    tangent = col / norm
    if previous is not None:
        prev = np.asarray(previous, dtype=float).reshape(-1)
        if float(np.dot(tangent, prev)) < 0.0:
            tangent = -tangent
    else:
        idx = int(np.argmax(np.abs(tangent)))
        if tangent[idx] < 0.0:
            tangent = -tangent
    return tangent
