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


@dataclass(frozen=True, slots=True)
class WorkspaceTopology:
    """Structured dexterous topology separating finite and zero-width sets."""

    finite_components: tuple[str, ...]
    degenerate_components: tuple[str, ...]

    def summary(self) -> str:
        parts = list(self.finite_components) + list(self.degenerate_components)
        if not parts:
            return "empty"
        if self.finite_components == ("empty",) and not self.degenerate_components:
            return "empty"
        filtered = [part for part in parts if part != "empty"]
        return "+".join(filtered) if filtered else "empty"


@dataclass(frozen=True, slots=True)
class RadialMechanismState:
    """Mechanism and workspace state at a single Cartesian radius."""

    rho: float
    rho_bar: float
    reachable: bool
    assemblable: bool
    assembly_margin: float
    grashof_margin: float
    grashof_class: str
    inversion_type: str
    input_can_fully_rotate: bool
    dexterous: bool


def classify_workspace_topology(
    intervals: tuple[RadialInterval, ...], *, tol: float = DEFAULT_TOL
) -> WorkspaceTopology:
    """Classify finite-area and degenerate dexterous radial components."""
    if not intervals:
        return WorkspaceTopology(("empty",), ())

    finite: list[RadialInterval] = []
    degenerate: list[str] = []
    for inner, outer in intervals:
        if outer - inner <= tol:
            if inner <= tol:
                degenerate.append("origin_point")
            else:
                degenerate.append("boundary_circle")
        else:
            finite.append((inner, outer))

    if not finite and not degenerate:
        return WorkspaceTopology(("empty",), ())

    finite_label: tuple[str, ...]
    if not finite:
        finite_label = ()
    elif len(finite) == 1:
        inner, _outer = finite[0]
        finite_label = ("disk",) if inner <= tol else ("annulus",)
    elif (
        len(finite) == 2
        and finite[0][0] <= tol
        and finite[1][0] > tol
    ):
        finite_label = ("disk_and_annulus",)
    else:
        finite_label = ("special",)

    return WorkspaceTopology(finite_label, tuple(degenerate))


def dexterous_topology(
    intervals: tuple[RadialInterval, ...], *, tol: float = DEFAULT_TOL
) -> str:
    """Human-readable topology summary for CLI and CSV compatibility."""
    return classify_workspace_topology(intervals, tol=tol).summary()


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

    def is_reachable_radius(self, rho: float, *, tol: float = DEFAULT_TOL) -> bool:
        if rho < 0.0:
            raise ValueError("rho must be nonnegative")
        inner, outer = self.reachable_radial_interval()
        return inner - tol <= rho <= outer + tol

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

    def workspace_topology(self, *, tol: float = DEFAULT_TOL) -> WorkspaceTopology:
        """Structured topology of the closed-form dexterous radial set."""
        return classify_workspace_topology(
            self.dexterous_radial_intervals(tol=tol), tol=tol
        )

    def dexterous_topology(self, *, tol: float = DEFAULT_TOL) -> str:
        """Topology summary string for the closed-form dexterous radial set."""
        return self.workspace_topology(tol=tol).summary()

    def mechanism_state(
        self, rho: float, *, tol: float = DEFAULT_TOL
    ) -> RadialMechanismState:
        """Evaluate assemblability, Grashof state, rotatability, and dexterity."""
        if rho < 0.0:
            raise ValueError("rho must be nonnegative")
        linkage = self.fourbar_at_radius(rho)
        rotatable = linkage.input_can_fully_rotate(tol=tol)
        dexterous = self.is_dexterous_radius(rho, tol=tol)
        return RadialMechanismState(
            rho=rho,
            rho_bar=rho / self.l1,
            reachable=self.is_reachable_radius(rho, tol=tol),
            assemblable=linkage.is_assemblable(tol=tol),
            assembly_margin=linkage.assembly_margin,
            grashof_margin=linkage.grashof_margin,
            grashof_class=linkage.grashof_class(tol=tol),
            inversion_type=linkage.inversion_type(tol=tol),
            input_can_fully_rotate=rotatable,
            dexterous=dexterous,
        )

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

        The sample set always includes the wrist-distance extrema ``phi=0`` and
        ``phi=pi`` in addition to a uniform grid.
        """
        if samples < 4:
            raise ValueError("samples must be at least 4")

        lower = self.two_link_inner_radius
        upper = self.two_link_outer_radius

        angles = [2.0 * pi * index / samples for index in range(samples)]
        for required in (0.0, pi):
            if not any(abs(angle - required) <= tol for angle in angles):
                angles.append(required)

        reachable = 0
        for phi in angles:
            wrist_x = x - self.l3 * cos(phi)
            wrist_y = y - self.l3 * sin(phi)
            distance = hypot(wrist_x, wrist_y)
            if lower - tol <= distance <= upper + tol:
                reachable += 1

        return reachable / len(angles)
