"""Rotation primitives for the terminal-roll fixture.

Conventions
-----------
- Canonical orientation representation is a ``3x3`` rotation matrix in SO(3).
- Positive rotation about unit axis ``w`` follows the right-hand rule.
- Relative orientation uses ``R_rel = R0.T @ R1``; never subtract Euler angles.
- Angles are in radians.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import AxisLine, unit_vector

Vec3 = NDArray[np.floating]
Mat3 = NDArray[np.floating]


def rotation_about_axis(w: Vec3 | tuple[float, float, float], angle: float) -> Mat3:
    """Return Rodrigues rotation matrix about unit direction ``w`` by ``angle``.

    Interior: nonzero angle about a valid axis.
    Boundary: ``angle = 0`` returns identity.
    """
    w_hat = unit_vector(w, name="rotation axis")
    wx, wy, wz = float(w_hat[0]), float(w_hat[1]), float(w_hat[2])
    K = np.array(
        [
            [0.0, -wz, wy],
            [wz, 0.0, -wx],
            [-wy, wx, 0.0],
        ],
        dtype=float,
    )
    c = math.cos(angle)
    s = math.sin(angle)
    I = np.eye(3)
    return np.asarray(I + s * K + (1.0 - c) * (K @ K), dtype=float)


def rotate_vector_about_axis(
    v: Vec3 | tuple[float, float, float],
    w: Vec3 | tuple[float, float, float],
    angle: float,
) -> Vec3:
    """Rotate free vector ``v`` about direction ``w`` by ``angle``."""
    R = rotation_about_axis(w, angle)
    return np.asarray(R @ np.asarray(v, dtype=float).reshape(3), dtype=float)


def rotate_point_about_axis(
    x: Vec3 | tuple[float, float, float],
    axis: AxisLine,
    angle: float,
) -> Vec3:
    """Rotate point ``x`` about the directed line ``axis`` by ``angle``.

    Implements ``r + R(w, angle)(x - r)``.
    """
    x_arr = np.asarray(x, dtype=float).reshape(3)
    return np.asarray(axis.r_array + rotate_vector_about_axis(x_arr - axis.r_array, axis.w, angle), dtype=float)


def axis_angle_from_rotation(R: Mat3, *, tol: float = 1e-12) -> tuple[Vec3, float]:
    """Extract ``(axis, angle)`` from a rotation matrix via the matrix logarithm path.

    Angle is returned in ``[0, pi]``. For ``angle = 0`` the axis is ``(1, 0, 0)``.
    For ``angle = pi`` a stable axis is recovered from the diagonal of ``R``.

    Does not use Euler-angle subtraction.
    """
    R_arr = np.asarray(R, dtype=float).reshape(3, 3)
    # Clamp for numerical safety of acos.
    cos_theta = 0.5 * (float(np.trace(R_arr)) - 1.0)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    angle = math.acos(cos_theta)

    if angle <= tol:
        return np.array([1.0, 0.0, 0.0], dtype=float), 0.0

    if abs(angle - math.pi) <= 1e-8:
        # 180-degree case: axis from (R + I) columns.
        M = R_arr + np.eye(3)
        col_norms = np.linalg.norm(M, axis=0)
        j = int(np.argmax(col_norms))
        axis = M[:, j]
        n = float(np.linalg.norm(axis))
        if n <= tol:
            raise ValueError("failed to recover axis from 180-degree rotation")
        return axis / n, math.pi

    axis = np.array(
        [
            R_arr[2, 1] - R_arr[1, 2],
            R_arr[0, 2] - R_arr[2, 0],
            R_arr[1, 0] - R_arr[0, 1],
        ],
        dtype=float,
    )
    axis = axis / (2.0 * math.sin(angle))
    return axis, angle


def relative_rotation(R0: Mat3, R1: Mat3) -> Mat3:
    """Return ``R_rel = R0.T @ R1``."""
    return np.asarray(np.asarray(R0, dtype=float).T @ np.asarray(R1, dtype=float), dtype=float)
