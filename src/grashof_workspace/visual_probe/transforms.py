"""Homogeneous SE(3) helpers for the visual probe.

Conventions
-----------
Transforms map points from a child frame into the parent / world when
composed left-to-right as ``T_world = T_0 @ T_1 @ ...``. Rotations are
right-handed about the stated axis.
"""

from __future__ import annotations

import math

from .model import AxisLine, Mat4, Vec3


def identity4() -> Mat4:
    return (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


def matmul(a: Mat4, b: Mat4) -> Mat4:
    rows: list[tuple[float, float, float, float]] = []
    for i in range(4):
        row = (
            sum(a[i][k] * b[k][0] for k in range(4)),
            sum(a[i][k] * b[k][1] for k in range(4)),
            sum(a[i][k] * b[k][2] for k in range(4)),
            sum(a[i][k] * b[k][3] for k in range(4)),
        )
        rows.append(row)
    return (rows[0], rows[1], rows[2], rows[3])


def transform_point(t: Mat4, p: Vec3) -> Vec3:
    x, y, z = p
    return (
        t[0][0] * x + t[0][1] * y + t[0][2] * z + t[0][3],
        t[1][0] * x + t[1][1] * y + t[1][2] * z + t[1][3],
        t[2][0] * x + t[2][1] * y + t[2][2] * z + t[2][3],
    )


def transform_direction(t: Mat4, v: Vec3) -> Vec3:
    x, y, z = v
    return (
        t[0][0] * x + t[0][1] * y + t[0][2] * z,
        t[1][0] * x + t[1][1] * y + t[1][2] * z,
        t[2][0] * x + t[2][1] * y + t[2][2] * z,
    )


def translation(p: Vec3) -> Mat4:
    return (
        (1.0, 0.0, 0.0, p[0]),
        (0.0, 1.0, 0.0, p[1]),
        (0.0, 0.0, 1.0, p[2]),
        (0.0, 0.0, 0.0, 1.0),
    )


def normalize(v: Vec3, *, name: str = "vector") -> Vec3:
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n == 0.0:
        raise ValueError(f"cannot normalize zero-length {name}")
    return (v[0] / n, v[1] / n, v[2] / n)


def rotation_about(axis: Vec3, angle: float) -> Mat4:
    """Rodrigues rotation embedded in SE(3)."""
    ax, ay, az = normalize(axis, name="rotation axis")
    c = math.cos(angle)
    s = math.sin(angle)
    C = 1.0 - c
    r00 = c + ax * ax * C
    r01 = ax * ay * C - az * s
    r02 = ax * az * C + ay * s
    r10 = ay * ax * C + az * s
    r11 = c + ay * ay * C
    r12 = ay * az * C - ax * s
    r20 = az * ax * C - ay * s
    r21 = az * ay * C + ax * s
    r22 = c + az * az * C
    return (
        (r00, r01, r02, 0.0),
        (r10, r11, r12, 0.0),
        (r20, r21, r22, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


def screw_rotation(axis: AxisLine, angle: float) -> Mat4:
    """Rotate about the world line ``axis`` by ``angle`` (space screw)."""
    p = axis.point
    return matmul(
        matmul(translation(p), rotation_about(axis.direction, angle)),
        translation((-p[0], -p[1], -p[2])),
    )


def frame_from_axis(origin: Vec3, direction: Vec3, *, length: float = 1.0) -> Mat4:
    """Build a right-handed triad with ``z`` along ``direction`` at ``origin``."""
    z = normalize(direction, name="frame z")
    # Prefer a world-up reference unless nearly parallel.
    ref = (0.0, 0.0, 1.0) if abs(z[2]) < 0.9 else (1.0, 0.0, 0.0)
    x = normalize(
        (
            ref[1] * z[2] - ref[2] * z[1],
            ref[2] * z[0] - ref[0] * z[2],
            ref[0] * z[1] - ref[1] * z[0],
        ),
        name="frame x",
    )
    y = (
        z[1] * x[2] - z[2] * x[1],
        z[2] * x[0] - z[0] * x[2],
        z[0] * x[1] - z[1] * x[0],
    )
    s = float(length)
    return (
        (x[0] * s, y[0] * s, z[0] * s, origin[0]),
        (x[1] * s, y[1] * s, z[1] * s, origin[1]),
        (x[2] * s, y[2] * s, z[2] * s, origin[2]),
        (0.0, 0.0, 0.0, 1.0),
    )


def as_axis_line(point: Vec3, direction: Vec3) -> AxisLine:
    return AxisLine(point=point, direction=normalize(direction, name="axis direction"))
