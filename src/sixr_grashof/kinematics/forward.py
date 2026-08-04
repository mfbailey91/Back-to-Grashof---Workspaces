"""Homogeneous-transform forward kinematics helpers.

Convention
----------
 successive joint transforms use right-handed rotations about the local
 joint axis. Transforms map points from frame i to the base when composed
 left-to-right as ``T_0n = T_01 @ T_12 @ ...``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .axes import AxisLine, Vec3, normalize

Mat4 = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]


def identity4() -> Mat4:
    return (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


def matmul(A: Mat4, B: Mat4) -> Mat4:
    rows: list[tuple[float, float, float, float]] = []
    for i in range(4):
        row = (
            sum(A[i][k] * B[k][0] for k in range(4)),
            sum(A[i][k] * B[k][1] for k in range(4)),
            sum(A[i][k] * B[k][2] for k in range(4)),
            sum(A[i][k] * B[k][3] for k in range(4)),
        )
        rows.append(row)
    return (rows[0], rows[1], rows[2], rows[3])


def transform_point(T: Mat4, p: Vec3) -> Vec3:
    x, y, z = p
    return (
        T[0][0] * x + T[0][1] * y + T[0][2] * z + T[0][3],
        T[1][0] * x + T[1][1] * y + T[1][2] * z + T[1][3],
        T[2][0] * x + T[2][1] * y + T[2][2] * z + T[2][3],
    )


def transform_direction(T: Mat4, v: Vec3) -> Vec3:
    x, y, z = v
    return (
        T[0][0] * x + T[0][1] * y + T[0][2] * z,
        T[1][0] * x + T[1][1] * y + T[1][2] * z,
        T[2][0] * x + T[2][1] * y + T[2][2] * z,
    )


def translation(p: Vec3) -> Mat4:
    return (
        (1.0, 0.0, 0.0, p[0]),
        (0.0, 1.0, 0.0, p[1]),
        (0.0, 0.0, 1.0, p[2]),
        (0.0, 0.0, 0.0, 1.0),
    )


def rotation_about(axis: Vec3, angle: float) -> Mat4:
    """Rodrigues rotation matrix embedded in SE(3)."""
    ax = normalize(axis)
    x, y, z = ax
    c = math.cos(angle)
    s = math.sin(angle)
    C = 1.0 - c
    r00 = c + x * x * C
    r01 = x * y * C - z * s
    r02 = x * z * C + y * s
    r10 = y * x * C + z * s
    r11 = c + y * y * C
    r12 = y * z * C - x * s
    r20 = z * x * C - y * s
    r21 = z * y * C + x * s
    r22 = c + z * z * C
    return (
        (r00, r01, r02, 0.0),
        (r10, r11, r12, 0.0),
        (r20, r21, r22, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


@dataclass(frozen=True, slots=True)
class JointPose:
    """Pose of one revolute joint axis in the base frame."""

    index: int
    axis: AxisLine
    origin: Vec3


@dataclass(frozen=True, slots=True)
class ForwardKinematicsResult:
    """FK result with explicit joint axes in the base frame."""

    joints: tuple[JointPose, ...]
    tool_position: Vec3
    tool_transform: Mat4


def compose_chain(transforms: list[Mat4]) -> Mat4:
    T = identity4()
    for Ti in transforms:
        T = matmul(T, Ti)
    return T
