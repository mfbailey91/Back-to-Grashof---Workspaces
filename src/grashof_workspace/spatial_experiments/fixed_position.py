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
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .jacobians import ABS_RANK_TOL, REL_RANK_TOL, matrix_rank_report, nullspace, position_jacobian
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

Vec = NDArray[np.floating]

POSITION_RESIDUAL_TOL_M = 1e-10
EXPECTED_SPATIAL_RANK = 3


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
    """Rank/nullity diagnostics at a fixed-position seed."""

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
    p_star = tuple(float(x) for x in state.p)
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


def audit_fixed_position_seed(
    problem: FixedPositionProblem,
    *,
    abs_tol: float = ABS_RANK_TOL,
    rel_tol: float = REL_RANK_TOL,
    position_tol_m: float = POSITION_RESIDUAL_TOL_M,
    expected_rank: int = EXPECTED_SPATIAL_RANK,
) -> FixedPositionSeedAudit:
    """Report whether the seed is a regular one-DOF fixed-position configuration."""
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
    if regular:
        status = "PASS"
    elif report.rank < expected_rank:
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
