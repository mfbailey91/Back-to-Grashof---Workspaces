"""Explicit drive semantics for a two-coordinate universal joint on a 1-DOF loop.

A universal joint has two local coordinates, ``alpha`` and ``beta``. A closed
four-bar child nevertheless has only one global degree of freedom. Therefore
``alpha`` and ``beta`` are not independent commands on the closed mechanism:

    alpha = alpha(s)
    beta  = beta(s)

where ``s`` is the branch/continuation parameter. The canonical solver advances
``s`` and reads both U coordinates. Prescribing one U coordinate is an optional
local chart that is valid only where its derivative with respect to ``s`` does
not vanish.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .models import DriveMode, UDriveContract

Array = NDArray[np.floating]


@dataclass(frozen=True, slots=True)
class UBranchSample:
    """One conceptual or solved point on a one-DOF branch."""

    s: float
    alpha: float
    beta: float
    pointing: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class UBranchSummary:
    """Compact coordinate behavior over a returned branch."""

    sample_count: int
    alpha_winding: int
    beta_winding: int
    alpha_range: float
    beta_range: float
    interpretation: str


def free_branch_contract() -> UDriveContract:
    """Return the canonical, coordinate-neutral continuation contract."""

    return UDriveContract(
        mode=DriveMode.FREE_BRANCH,
        branch_parameter="s (pseudo-arclength)",
        commanded_coordinate=None,
        solved_coordinates=("alpha(s)", "beta(s)", "all remaining loop coordinates"),
        valid_when="the closure Jacobian has a regular one-dimensional nullspace",
        fallback="reduce step size, change chart, or stop/branch at a singular point",
        interpretation=(
            "The solver moves the whole closed mechanism along its one-dimensional branch. "
            "Neither U coordinate is independently prescribed."
        ),
    )


def task_derived_fiber_contract() -> UDriveContract:
    """Return the source-parent fiber contract used before child compression."""

    return UDriveContract(
        mode=DriveMode.TASK_DERIVED_FIBER,
        branch_parameter="s on {p(q)=p*, h(T(q))=c}",
        commanded_coordinate="the scalar slice value c is fixed for the entire fiber",
        solved_coordinates=(
            "source joint coordinates q(s)",
            "derived alpha(s)",
            "derived beta(s)",
        ),
        valid_when="the combined source constraint has rank n-1 and nullity one",
        fallback="choose another regular slice chart or mark the fiber critical/unresolved",
        interpretation=(
            "The task slice selects which one-dimensional fiber is being solved. "
            "It does not independently drive alpha and beta."
        ),
    )


def prescribed_coordinate_contract(coordinate: str) -> UDriveContract:
    """Return a local prescribed-alpha or prescribed-beta solve contract."""

    normalized = coordinate.casefold()
    if normalized not in {"alpha", "beta"}:
        raise ValueError("coordinate must be 'alpha' or 'beta'")
    mode = (
        DriveMode.PRESCRIBED_ALPHA
        if normalized == "alpha"
        else DriveMode.PRESCRIBED_BETA
    )
    other = "beta" if normalized == "alpha" else "alpha"
    return UDriveContract(
        mode=mode,
        branch_parameter=f"prescribed {normalized}",
        commanded_coordinate=normalized,
        solved_coordinates=(other, "all remaining loop coordinates"),
        valid_when=f"d{normalized}/ds is nonzero on the local branch chart",
        fallback=(
            f"switch to {other} or pseudo-arclength s when d{normalized}/ds approaches zero"
        ),
        interpretation=(
            f"Commanding {normalized} means adding {normalized}=command as one equation and "
            "solving loop closure for every other coordinate. It is a local chart, not a "
            "second independent mechanism DOF."
        ),
    )


def choose_local_drive_coordinate(
    dalpha_ds: float,
    dbeta_ds: float,
    *,
    derivative_tol: float = 1e-8,
) -> UDriveContract:
    """Select the better-conditioned local U coordinate, or use free branch.

    The coordinate with the larger absolute derivative is preferred. If both
    derivatives vanish within tolerance, neither coordinate is a valid local
    drive chart and pseudo-arclength is required.
    """

    if derivative_tol <= 0.0:
        raise ValueError("derivative_tol must be positive")
    alpha_speed = abs(float(dalpha_ds))
    beta_speed = abs(float(dbeta_ds))
    if max(alpha_speed, beta_speed) <= derivative_tol:
        return free_branch_contract()
    return prescribed_coordinate_contract(
        "alpha" if alpha_speed >= beta_speed else "beta"
    )


def _rotation_x(angle: float) -> Array:
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array(
        ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c)),
        dtype=float,
    )


def _rotation_y(angle: float) -> Array:
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array(
        ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c)),
        dtype=float,
    )


def u_rotation_matrix(alpha: float, beta: float) -> Array:
    """Return the ordered local U chart ``R_x(alpha) R_y(beta)``."""

    return _rotation_x(float(alpha)) @ _rotation_y(float(beta))


def u_pointing(alpha: float, beta: float) -> tuple[float, float, float]:
    """Return the rotated local z-axis for the conceptual U chart."""

    d = u_rotation_matrix(alpha, beta) @ np.array((0.0, 0.0, 1.0), dtype=float)
    return (float(d[0]), float(d[1]), float(d[2]))


def conceptual_branch_samples(sample_count: int = 121) -> tuple[UBranchSample, ...]:
    """Return a clearly labeled conceptual branch for explanatory readouts.

    ``alpha`` completes one turn while ``beta`` rocks. These are not research
    results and are never used as mechanism evidence.
    """

    if sample_count < 3:
        raise ValueError("sample_count must be at least 3")
    s_values = np.linspace(0.0, 2.0 * math.pi, sample_count)
    samples: list[UBranchSample] = []
    for s in s_values:
        alpha = float(s)
        beta = 0.55 * math.sin(float(s))
        samples.append(
            UBranchSample(
                s=float(s),
                alpha=alpha,
                beta=beta,
                pointing=u_pointing(alpha, beta),
            )
        )
    return tuple(samples)


def coordinate_winding(values: Array | tuple[float, ...]) -> int:
    """Return integer winding from a continuous sampled angular coordinate."""

    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size < 2:
        raise ValueError("at least two values are required")
    unwrapped = np.unwrap(arr)
    return round(float(unwrapped[-1] - unwrapped[0]) / (2.0 * math.pi))


def summarize_branch(samples: tuple[UBranchSample, ...]) -> UBranchSummary:
    """Summarize alpha/beta behavior on a returned conceptual or solved branch."""

    if len(samples) < 2:
        raise ValueError("at least two samples are required")
    alpha = np.asarray([sample.alpha for sample in samples], dtype=float)
    beta = np.asarray([sample.beta for sample in samples], dtype=float)
    alpha_winding = coordinate_winding(alpha)
    beta_winding = coordinate_winding(beta)
    interpretation = (
        "alpha circulates while beta rocks"
        if abs(alpha_winding) >= 1 and beta_winding == 0
        else "both U coordinates must be interpreted from their returned-cycle behavior"
    )
    return UBranchSummary(
        sample_count=len(samples),
        alpha_winding=alpha_winding,
        beta_winding=beta_winding,
        alpha_range=float(np.max(alpha) - np.min(alpha)),
        beta_range=float(np.max(beta) - np.min(beta)),
        interpretation=interpretation,
    )


def simple_drive_explanation() -> str:
    """Return the user-facing compact explanation shared by readouts."""

    return (
        "A U joint has two coordinates, alpha and beta, but the closed child mechanism "
        "has only one global DOF. We therefore drive the branch parameter s. Loop closure "
        "forces alpha and beta to move together as alpha(s) and beta(s). Prescribing alpha "
        "is only a local convenience: set alpha to a command and solve every other coordinate. "
        "At an alpha turning point, switch to beta or return to pseudo-arclength s."
    )
