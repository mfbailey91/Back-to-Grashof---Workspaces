"""Analytical workspace model for a planar 3R serial manipulator.

Coordinate and joint conventions
--------------------------------
- The base pivot is at the origin of the plane.
- Link lengths ``l1``, ``l2``, ``l3`` are positive and ordered from base to tip.
- Joint angles are unrestricted planar revolute angles; workspace membership is
  therefore invariant under global rotation about the base and depends only on
  the polar radius ``rho = ||p||`` of the end-effector position ``p``.
- Terminal orientation ``phi`` is the absolute planar heading of the tip link.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, hypot, pi, sin

from .fourbar import FourBar

RadialInterval = tuple[float, float]

# Documented numerical tolerance for analytical predicates and sampling checks.
DEFAULT_TOL = 1e-12
# Orientation-sampling coverage must equal 1.0 for a dexterous interior point.
FULL_COVERAGE = 1.0


def _merge_intervals(
    intervals: list[RadialInterval], *, tol: float = DEFAULT_TOL
) -> tuple[RadialInterval, ...]:
    valid = sorted((a, b) for a, b in intervals if b >= a - tol)
    if not valid:
        return ()

    merged: list[list[float]] = [[valid[0][0], valid[0][1]]]
    for start, end in valid[1:]:
        if start <= merged[-1][1] + tol:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return tuple((max(0.0, a), max(0.0, b)) for a, b in merged)


def dexterous_topology(
    intervals: tuple[RadialInterval, ...], *, tol: float = DEFAULT_TOL
) -> str:
    """Classify dexterous radial components into a stable topology label.

    Labels follow ``docs/MATH_NOTES.md`` §4:
    ``empty``, ``disk``, ``annulus``, ``disk_and_annulus``, ``degenerate``.
    Zero-width (change-point) circles are preserved and reported as
    ``degenerate`` whenever present.
    """
    if not intervals:
        return "empty"

    has_degenerate = any(outer - inner <= tol for inner, outer in intervals)
    if has_degenerate:
        return "degenerate"

    if len(intervals) == 1:
        inner, _outer = intervals[0]
        return "disk" if inner <= tol else "annulus"

    if (
        len(intervals) == 2
        and intervals[0][0] <= tol
        and intervals[1][0] > tol
    ):
        return "disk_and_annulus"

    return "special"


@dataclass(frozen=True, slots=True)
class Planar3R:
    """Rigid planar 3R manipulator with unrestricted revolute joints."""

    l1: float
    l2: float
    l3: float

    def __post_init__(self) -> None:
        for name, value in (("l1", self.l1), ("l2", self.l2), ("l3", self.l3)):
            if value <= 0.0:
                raise ValueError(f"{name} must be positive")

    @property
    def two_link_inner_radius(self) -> float:
        return abs(self.l1 - self.l2)

    @property
    def two_link_outer_radius(self) -> float:
        return self.l1 + self.l2

    def reachable_radial_interval(self) -> RadialInterval:
        """Position workspace of the complete 3R chain."""
        lengths = (self.l1, self.l2, self.l3)
        longest = max(lengths)
        total = sum(lengths)
        inner = max(0.0, longest - (total - longest))
        return (inner, total)

    def wrist_distance_bounds(self, rho: float) -> RadialInterval:
        """Base-to-wrist distance over every desired terminal orientation."""
        if rho < 0.0:
            raise ValueError("rho must be nonnegative")
        return (abs(rho - self.l3), rho + self.l3)

    def fourbar_at_radius(self, rho: float) -> FourBar:
        """Equivalent loop for a fixed end-effector position at radius rho.

        Loop order is ``(ground, input, coupler, output) = (rho, l3, l2, l1)``.
        """
        if rho < 0.0:
            raise ValueError("rho must be nonnegative")
        return FourBar(
            ground=rho,
            input=self.l3,
            coupler=self.l2,
            output=self.l1,
        )

    def is_dexterous_radius(self, rho: float, *, tol: float = DEFAULT_TOL) -> bool:
        """Whether every planar terminal orientation is reachable at radius rho."""
        return self.fourbar_at_radius(rho).input_can_fully_rotate(tol=tol)

    def is_dexterous_position(
        self, x: float, y: float, *, tol: float = DEFAULT_TOL
    ) -> bool:
        return self.is_dexterous_radius(hypot(x, y), tol=tol)

    def dexterous_radial_intervals(
        self, *, tol: float = DEFAULT_TOL
    ) -> tuple[RadialInterval, ...]:
        """Closed-form radial components of the planar dexterous workspace.

        Conditions (``docs/MATH_NOTES.md`` §3):

            |rho - l3| >= |l1 - l2|
            rho + l3 <= l1 + l2

        Degenerate (zero-width) intervals are retained.
        """
        inner_2r = self.two_link_inner_radius
        outer_2r = self.two_link_outer_radius
        max_rho = outer_2r - self.l3
        if max_rho < -tol:
            return ()

        candidates: list[RadialInterval] = []

        # Branch 1: rho <= l3 - inner_2r
        branch_1_end = min(self.l3 - inner_2r, max_rho)
        if branch_1_end >= -tol:
            candidates.append((0.0, max(0.0, branch_1_end)))

        # Branch 2: rho >= l3 + inner_2r
        branch_2_start = self.l3 + inner_2r
        if branch_2_start <= max_rho + tol:
            candidates.append((branch_2_start, max_rho))

        return _merge_intervals(candidates, tol=tol)

    def dexterous_topology(self, *, tol: float = DEFAULT_TOL) -> str:
        """Topology label for the closed-form dexterous radial set."""
        return dexterous_topology(self.dexterous_radial_intervals(tol=tol), tol=tol)

    def sampled_orientation_coverage(
        self,
        x: float,
        y: float,
        *,
        samples: int = 720,
        tol: float = DEFAULT_TOL,
    ) -> float:
        """Numerically validate the fraction of terminal orientations reachable.

        This is a validation helper, not the primary workspace definition.
        A dexterous interior point must return ``FULL_COVERAGE`` (1.0).
        """
        if samples < 4:
            raise ValueError("samples must be at least 4")

        lower = self.two_link_inner_radius
        upper = self.two_link_outer_radius
        reachable = 0

        for index in range(samples):
            phi = 2.0 * pi * index / samples
            wrist_x = x - self.l3 * cos(phi)
            wrist_y = y - self.l3 * sin(phi)
            distance = hypot(wrist_x, wrist_y)
            if lower - tol <= distance <= upper + tol:
                reachable += 1

        return reachable / samples
