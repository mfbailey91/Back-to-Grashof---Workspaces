"""Isolated spatial experiment kernel for aligned terminal-roll studies.

This package is intentionally separate from the trusted planar kernel and from
``sixr_grashof``. Sprint 01 covers only an isolated terminal-revolute fixture.

Conventions
-----------
- lengths in metres, angles in radians;
- frames ``W`` (world), ``B`` (base), ``F`` (flange after R6), ``T`` (tool);
- revolute axis ``A = (r, w)`` with unit direction ``w`` and right-hand rule;
- task point ``p`` and pointing direction ``d`` are expressed in ``W``.
"""

from .axis_geometry import (
    AxisLine,
    parallelism_residual,
    point_axis_distance,
    unit_vector,
)
from .rotations import (
    axis_angle_from_rotation,
    rotate_point_about_axis,
    rotate_vector_about_axis,
    rotation_about_axis,
)
from .terminal_roll_fixture import TerminalRollFixture, TerminalRollState

__all__ = [
    "AxisLine",
    "TerminalRollFixture",
    "TerminalRollState",
    "axis_angle_from_rotation",
    "parallelism_residual",
    "point_axis_distance",
    "rotate_point_about_axis",
    "rotate_vector_about_axis",
    "rotation_about_axis",
    "unit_vector",
]
