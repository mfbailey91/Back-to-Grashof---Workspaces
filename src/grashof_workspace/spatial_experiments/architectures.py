"""Synthetic aligned-terminal 6R architectures for Sprint 03.

Conventions
-----------
Both models use ``SerialRevoluteChain`` with home axes in world frame ``W``,
task point ``p*`` on home ``R6``, and ``d0`` parallel to ``w6``. Joint order is
base ``R1`` through terminal ``R6``. Intersections and parallelisms are exact
by construction, not approximate.

``IntersectingPairsAligned6R``
    Exact ``R1 ∩ R2`` and ``R3 ∩ R4``; leftover ``R5``; aligned ``R6``.
    This is the literal compound-joint parent: ``UA=(R1,R2)``, ``UB=(R3,R4)``,
    ``RC=R5``, roll ``R6``.

``URLikeAligned6R``
    Synthetic shoulder–elbow–wrist ordering: ``R2 ∥ R3``, spherical wrist
    ``R4 ∩ R5 ∩ R6``, TCP on ``R6`` beyond the wrist, ``d0 ∥ w6``.
    Not an exact UR / URDF model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .aligned_6r import frame_from_pointing
from .axis_geometry import (
    AxisLine,
    line_line_distance,
    parallelism_residual,
    point_axis_distance,
    unit_vector,
)
from .serial_chain import SerialRevoluteChain

INTERSECTING_PAIRS_REGULAR_Q = (0.35, -0.42, 0.55, 0.28, -0.33, 0.70)
URLIKE_REGULAR_Q = (0.35, -0.42, 0.55, 0.28, -0.33, 0.70)

UA_CENTER = (0.00, 0.00, 0.28)
UB_CENTER = (0.32, 0.06, 0.52)
R5_POINT = (0.48, -0.10, 0.66)
R6_POINT_IP = (0.60, 0.04, 0.82)

SHOULDER = (0.00, 0.00, 0.152)
ELBOW = (0.244, 0.00, 0.152)
WRIST = (0.457, 0.00, 0.152)
TOOL_OFFSET_M = 0.082


def intersecting_pairs_home_axes() -> tuple[AxisLine, ...]:
    """Return home axes with exact pair intersections and aligned terminal roll."""
    return (
        AxisLine(UA_CENTER, (0.00, 0.00, 1.00)),
        AxisLine(UA_CENTER, (1.00, 0.25, 0.08)),
        AxisLine(UB_CENTER, (0.18, 1.00, 0.12)),
        AxisLine(UB_CENTER, (-0.15, 0.28, 1.00)),
        AxisLine(R5_POINT, (1.00, -0.20, 0.18)),
        AxisLine(R6_POINT_IP, (0.10, 0.08, 1.00)),
    )


def urlike_home_axes() -> tuple[AxisLine, ...]:
    """Return synthetic UR-like home axes with parallel elbow and spherical wrist."""
    return (
        AxisLine((0.00, 0.00, 0.00), (0.00, 0.00, 1.00)),
        AxisLine(SHOULDER, (0.00, 1.00, 0.00)),
        AxisLine(ELBOW, (0.00, 1.00, 0.00)),
        AxisLine(WRIST, (1.00, 0.00, 0.00)),
        AxisLine(WRIST, (0.00, 1.00, 0.00)),
        AxisLine(WRIST, (0.00, 0.00, 1.00)),
    )


@dataclass(frozen=True, slots=True)
class IntersectingPairsAligned6R:
    """Aligned-terminal 6R with exact intersecting axis pairs."""

    chain: SerialRevoluteChain
    task_point: tuple[float, float, float]
    is_aligned: bool

    @classmethod
    def aligned(cls) -> IntersectingPairsAligned6R:
        axes = intersecting_pairs_home_axes()
        w6 = np.asarray(axes[5].w, dtype=float)
        p0 = tuple(float(x) for x in (np.asarray(axes[5].r, dtype=float) + 0.05 * w6))
        d0 = tuple(float(x) for x in w6)
        chain = SerialRevoluteChain(home_axes=axes, p0=p0, d0=d0, R0=frame_from_pointing(d0))
        return cls(chain=chain, task_point=p0, is_aligned=True)

    def home_alignment_residuals(self) -> tuple[float, float]:
        axis6 = self.chain.home_axes[5]
        return point_axis_distance(self.task_point, axis6), parallelism_residual(self.chain.d0, axis6.w)

    def pair_intersection_distances(self) -> tuple[float, float]:
        axes = self.chain.home_axes
        return line_line_distance(axes[0], axes[1]), line_line_distance(axes[2], axes[3])


@dataclass(frozen=True, slots=True)
class URLikeAligned6R:
    """Synthetic UR-like aligned-terminal 6R (not exact UR geometry)."""

    chain: SerialRevoluteChain
    task_point: tuple[float, float, float]
    is_aligned: bool

    @classmethod
    def aligned(cls) -> URLikeAligned6R:
        axes = urlike_home_axes()
        w6 = unit_vector(axes[5].w, name="w6")
        p0 = tuple(float(x) for x in (np.asarray(WRIST, dtype=float) + TOOL_OFFSET_M * w6))
        d0 = tuple(float(x) for x in w6)
        chain = SerialRevoluteChain(home_axes=axes, p0=p0, d0=d0, R0=frame_from_pointing(d0))
        return cls(chain=chain, task_point=p0, is_aligned=True)

    def home_alignment_residuals(self) -> tuple[float, float]:
        axis6 = self.chain.home_axes[5]
        return point_axis_distance(self.task_point, axis6), parallelism_residual(self.chain.d0, axis6.w)

    def elbow_parallelism_residual(self) -> float:
        axes = self.chain.home_axes
        return parallelism_residual(axes[1].w, axes[2].w)

    def wrist_concurrency_distances(self) -> tuple[float, float, float]:
        axes = self.chain.home_axes
        return (
            line_line_distance(axes[3], axes[4]),
            line_line_distance(axes[4], axes[5]),
            line_line_distance(axes[3], axes[5]),
        )
