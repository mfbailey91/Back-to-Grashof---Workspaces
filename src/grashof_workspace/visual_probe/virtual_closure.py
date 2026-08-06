"""Virtual spherical closure and terminal-roll quotient helpers.

Conventions
-----------
The virtual spherical joint ``S_v`` is centered at the fixed task point ``p``.
For display it is decomposed into three tool-frame-aligned axes
``{Sx, Sy, Sz}``. This is a chosen coordinate decomposition, not a claim that
the spherical joint intrinsically admits only three axes.

Terminal roll ``R6`` remains physically present; quotient graphics only mark
that roll is removed from the reduced pointing task.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import AxisLine, ForwardKinematicsResult, Mat4, Vec3
from .transforms import normalize, transform_direction


@dataclass(frozen=True, slots=True)
class VirtualSphericalClosure:
    """Tool-aligned spherical coordinate axes at the task point."""

    center: Vec3
    sx: AxisLine
    sy: AxisLine
    sz: AxisLine
    tool_transform: Mat4


@dataclass(frozen=True, slots=True)
class TerminalRollDisplay:
    """Display record for quotiented terminal roll."""

    axis: AxisLine
    pointing: Vec3
    label: str
    style: str


def virtual_spherical_closure(fk: ForwardKinematicsResult) -> VirtualSphericalClosure:
    """Place ``S_v = {Sx, Sy, Sz}`` at the FK task point using the tool triad."""
    t = fk.tool_transform
    center = fk.tool_point
    sx_dir = normalize(transform_direction(t, (1.0, 0.0, 0.0)), name="Sx")
    sy_dir = normalize(transform_direction(t, (0.0, 1.0, 0.0)), name="Sy")
    sz_dir = normalize(fk.pointing, name="Sz")
    return VirtualSphericalClosure(
        center=center,
        sx=AxisLine(center, sx_dir),
        sy=AxisLine(center, sy_dir),
        sz=AxisLine(center, sz_dir),
        tool_transform=t,
    )


def terminal_roll_display(fk: ForwardKinematicsResult) -> TerminalRollDisplay:
    """Mark ``R6`` as quotiented terminal roll without deleting it."""
    r6 = fk.joints[5]
    return TerminalRollDisplay(
        axis=r6.axis,
        pointing=fk.pointing,
        label="quotiented terminal roll",
        style="translucent_dashed",
    )


def roll_preserves_task(
    fk_a: ForwardKinematicsResult,
    fk_b: ForwardKinematicsResult,
    *,
    tol: float = 1e-9,
) -> bool:
    """Return True when two poses share task point and pointing within ``tol``."""
    dp = (
        (fk_a.tool_point[0] - fk_b.tool_point[0]) ** 2
        + (fk_a.tool_point[1] - fk_b.tool_point[1]) ** 2
        + (fk_a.tool_point[2] - fk_b.tool_point[2]) ** 2
    ) ** 0.5
    cross = (
        fk_a.pointing[1] * fk_b.pointing[2] - fk_a.pointing[2] * fk_b.pointing[1],
        fk_a.pointing[2] * fk_b.pointing[0] - fk_a.pointing[0] * fk_b.pointing[2],
        fk_a.pointing[0] * fk_b.pointing[1] - fk_a.pointing[1] * fk_b.pointing[0],
    )
    parallel = (cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2) ** 0.5
    return bool(dp <= tol and parallel <= tol)
