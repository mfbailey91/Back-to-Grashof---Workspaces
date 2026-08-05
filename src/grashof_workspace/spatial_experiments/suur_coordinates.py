"""Discriminating SUUR coordinate map and pair-persistence tests.

Conventions
-----------
Workshop grouping::

    UA = (R1, R2)   UB = (R3, R4)   RC = R5   roll = R6
    θ = (α1, α2, β1, β2, γ)
    φ(θ; q6*) = (α1, α2, β1, β2, γ, q6*)

``φ`` is defined only when current-axis pairwise distances satisfy
``dist(R1,R2)=0`` and ``dist(R3,R4)=0``. Axes are those returned by
``SerialRevoluteChain.current_axes`` at the candidate configuration.
This is independent of ``ker(J_p[:, :5])`` / ``N_red``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .axis_geometry import line_line_distance
from .serial_chain import SerialRevoluteChain

PAIR_DISTANCE_TOL_M = 1e-12
CLOSURE_POS_TOL_M = 1e-14
CLOSURE_DIR_TOL = 1e-14


@dataclass(frozen=True, slots=True)
class SuurMapResult:
    """Result of attempting ``φ(θ; q6*)``."""

    defined: bool
    q: tuple[float, ...] | None
    dist_ua_m: float
    dist_ub_m: float
    reason: str


@dataclass(frozen=True, slots=True)
class SuurClosureReport:
    defined: bool
    dist_ua_m: float
    dist_ub_m: float
    position_residual_m: float
    pointing_residual: float
    inverse_residual: float
    closed: bool


def pair_intersection_distances(
    chain: SerialRevoluteChain,
    q: tuple[float, ...],
) -> tuple[float, float]:
    """Return ``(dist(R1,R2), dist(R3,R4))`` at the current axes of ``q``."""
    if chain.n_joints < 4:
        raise ValueError("pair distances require at least four revolute axes")
    axes = chain.current_axes(q)
    return line_line_distance(axes[0], axes[1]), line_line_distance(axes[2], axes[3])


def suur_map(
    chain: SerialRevoluteChain,
    theta: tuple[float, float, float, float, float],
    q6_star: float,
    *,
    tol_m: float = PAIR_DISTANCE_TOL_M,
) -> SuurMapResult:
    """Return ``φ(θ; q6*)`` if and only if both intersecting pairs persist.

    Interior: intersecting-pair chains at regular ``θ`` are defined.
    Exterior: skew / nonintersecting pairs leave ``φ`` undefined.
    Boundary: a pair distance equal to ``tol_m`` is accepted; larger is not.
    """
    if chain.n_joints != 6:
        raise ValueError("SUUR map is defined for 6R chains")
    if len(theta) != 5:
        raise ValueError("θ must contain five reduced coordinates")
    q = (float(theta[0]), float(theta[1]), float(theta[2]), float(theta[3]), float(theta[4]), float(q6_star))
    dist_ua, dist_ub = pair_intersection_distances(chain, q)
    if dist_ua > tol_m or dist_ub > tol_m:
        return SuurMapResult(
            defined=False,
            q=None,
            dist_ua_m=dist_ua,
            dist_ub_m=dist_ub,
            reason="intersecting-axis pairs are not concurrent",
        )
    return SuurMapResult(
        defined=True,
        q=q,
        dist_ua_m=dist_ua,
        dist_ub_m=dist_ub,
        reason="defined",
    )


def closure_report(
    chain: SerialRevoluteChain,
    theta: tuple[float, float, float, float, float],
    q6_star: float,
    *,
    tol_m: float = PAIR_DISTANCE_TOL_M,
    pos_tol_m: float = CLOSURE_POS_TOL_M,
    dir_tol: float = CLOSURE_DIR_TOL,
) -> SuurClosureReport:
    """Check geometric closure of a defined ``φ(θ)`` against serial FK.

    When defined, ``φ`` is the identity embedding of ``θ``, so FK agreement is
    exact; the discriminating residuals are pair distances and invertibility
    ``θ = q[:5]``.
    """
    mapped = suur_map(chain, theta, q6_star, tol_m=tol_m)
    if not mapped.defined or mapped.q is None:
        return SuurClosureReport(
            defined=False,
            dist_ua_m=mapped.dist_ua_m,
            dist_ub_m=mapped.dist_ub_m,
            position_residual_m=float("inf"),
            pointing_residual=float("inf"),
            inverse_residual=float("inf"),
            closed=False,
        )
    q = mapped.q
    state_map = chain.evaluate(q)
    state_serial = chain.evaluate(
        (theta[0], theta[1], theta[2], theta[3], theta[4], q6_star)
    )
    pos_res = float(np.linalg.norm(state_map.p - state_serial.p))
    dir_res = float(np.linalg.norm(state_map.d - state_serial.d))
    inv_res = float(np.linalg.norm(np.asarray(q[:5]) - np.asarray(theta)))
    closed = (
        mapped.dist_ua_m <= tol_m
        and mapped.dist_ub_m <= tol_m
        and pos_res <= pos_tol_m
        and dir_res <= dir_tol
        and inv_res <= pos_tol_m
    )
    return SuurClosureReport(
        defined=True,
        dist_ua_m=mapped.dist_ua_m,
        dist_ub_m=mapped.dist_ub_m,
        position_residual_m=pos_res,
        pointing_residual=dir_res,
        inverse_residual=inv_res,
        closed=closed,
    )
