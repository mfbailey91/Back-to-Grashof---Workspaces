"""Homogeneous-transform forward kinematics for the visual probe.

Conventions
-----------
Space-form product of exponentials implemented with SE(3) screw rotations
about home axes. Joint order is ``R1`` (base) through ``R6`` (terminal).
The task point lies on ``R6`` by construction when the home ``R6`` point and
tool offset are collinear with the home ``R6`` direction; the selected
pointing direction is parallel to the world ``R6`` axis.
"""

from __future__ import annotations

from itertools import pairwise

from .model import ForwardKinematicsResult, JointPose, ProbeConfig, Vec3
from .transforms import (
    as_axis_line,
    frame_from_axis,
    identity4,
    matmul,
    normalize,
    screw_rotation,
    transform_direction,
    transform_point,
)


def forward_kinematics(
    config: ProbeConfig,
    q: tuple[float, float, float, float, float, float] | None = None,
) -> ForwardKinematicsResult:
    """Evaluate world-frame joint axes, links, and tool pose."""
    angles = q if q is not None else config.default_q
    if len(angles) != 6:
        raise ValueError("q must contain six joint angles")

    # Partial products e^[S1]q1 ... e^[S{i-1}]q{i-1} map home joint i to world.
    partial = identity4()
    joints: list[JointPose] = []
    for i, spec in enumerate(config.joints):
        origin = transform_point(partial, spec.home_point)
        direction = normalize(
            transform_direction(partial, spec.home_direction),
            name=f"{spec.label} direction",
        )
        axis = as_axis_line(origin, direction)
        frame = frame_from_axis(origin, direction, length=config.frame_length)
        joints.append(
            JointPose(index=spec.index, label=spec.label, origin=origin, axis=axis, frame=frame)
        )
        home_axis = as_axis_line(spec.home_point, spec.home_direction)
        partial = matmul(partial, screw_rotation(home_axis, float(angles[i])))

    # Tool: home offset along home R6, mapped by full product.
    r6_home = config.joints[5]
    home_tool = (
        r6_home.home_point[0] + config.tool_offset_along_r6 * r6_home.home_direction[0],
        r6_home.home_point[1] + config.tool_offset_along_r6 * r6_home.home_direction[1],
        r6_home.home_point[2] + config.tool_offset_along_r6 * r6_home.home_direction[2],
    )
    tool_point = transform_point(partial, home_tool)
    pointing = normalize(
        transform_direction(partial, r6_home.home_direction),
        name="pointing",
    )
    tool_frame = frame_from_axis(tool_point, pointing, length=config.frame_length)

    link_endpoints: list[tuple[Vec3, Vec3]] = []
    for a, b in pairwise(joints):
        link_endpoints.append((a.origin, b.origin))
    link_endpoints.append((joints[5].origin, tool_point))

    return ForwardKinematicsResult(
        joints=tuple(joints),
        tool_point=tool_point,
        pointing=pointing,
        tool_transform=tool_frame,
        link_endpoints=tuple(link_endpoints),
        q=(
            float(angles[0]),
            float(angles[1]),
            float(angles[2]),
            float(angles[3]),
            float(angles[4]),
            float(angles[5]),
        ),
    )
