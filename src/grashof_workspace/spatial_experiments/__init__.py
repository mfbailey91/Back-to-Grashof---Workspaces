"""Isolated spatial experiment kernel for aligned-terminal fiber studies.

Restored for Sprint V05A from the ``spherical_framework`` ATR stack. This
package is intentionally separate from the planar Grashof kernel and from the
standalone spatial-4bar explorer.

Conventions
-----------
- lengths in metres, angles in radians;
- revolute axis ``A = (r, w)`` with unit direction ``w`` and right-hand rule;
- task point ``p`` and pointing direction ``d`` are expressed in world frame ``W``.
"""

from .aligned_6r import GenericAligned6R, frame_from_pointing, generic_home_axes
from .axis_geometry import AxisLine, parallelism_residual, point_axis_distance, unit_vector
from .fiber_constraints import (
    FiberIndependenceReport,
    fiber_independence_report,
    pointing_scalar,
    reduced_fiber_jacobian,
    reduced_fiber_tangent,
)
from .rotations import (
    axis_angle_from_rotation,
    rotate_point_about_axis,
    rotate_vector_about_axis,
    rotation_about_axis,
)
from .serial_chain import SerialRevoluteChain

__all__ = [
    "AxisLine",
    "FiberIndependenceReport",
    "GenericAligned6R",
    "SerialRevoluteChain",
    "axis_angle_from_rotation",
    "fiber_independence_report",
    "frame_from_pointing",
    "generic_home_axes",
    "parallelism_residual",
    "point_axis_distance",
    "pointing_scalar",
    "reduced_fiber_jacobian",
    "reduced_fiber_tangent",
    "rotate_point_about_axis",
    "rotate_vector_about_axis",
    "rotation_about_axis",
    "unit_vector",
]
