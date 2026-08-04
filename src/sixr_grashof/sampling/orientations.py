"""Reproducible SO(3) orientation sampling (Sprint 4)."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np

SampleResolution = Literal["coarse", "medium", "fine"]

RESOLUTION_COUNTS: dict[SampleResolution, int] = {
    "coarse": 512,
    "medium": 5000,
    "fine": 50000,
}


def hopf_quaternion_grid(n: int, *, seed: int = 0) -> np.ndarray:
    """Return ``(n, 4)`` unit quaternions ``(w, x, y, z)`` via Hopf coordinates.

    Uses a deterministic scrambled lattice in [0, 1)^3 mapped to Hopf angles:

        theta in [0, pi],  phi in [0, 2pi),  psi in [0, 2pi)

    so that the induced Haar measure on SO(3) is approximately uniform.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    rng = np.random.default_rng(seed)
    # Low-discrepancy-ish: stratified random within equal bins along a space-filling order.
    u = (np.arange(n, dtype=float) + 0.5) / n
    v = (np.arange(n, dtype=float) * (math.sqrt(2) - 1.0)) % 1.0
    w = (np.arange(n, dtype=float) * (math.sqrt(3) - 1.0)) % 1.0
    # Small deterministic jitter for uniqueness without breaking reproducibility.
    jitter = rng.random((n, 3)) * (0.5 / n)
    u = (u + jitter[:, 0]) % 1.0
    v = (v + jitter[:, 1]) % 1.0
    w = (w + jitter[:, 2]) % 1.0

    theta = np.arccos(1.0 - 2.0 * u)  # [0, pi]
    phi = 2.0 * math.pi * v
    psi = 2.0 * math.pi * w

    # Hopf → unit quaternion
    half_th = 0.5 * theta
    qw = np.cos(half_th) * np.cos(0.5 * psi)
    qx = np.sin(half_th) * np.cos(phi + 0.5 * psi)
    qy = np.sin(half_th) * np.sin(phi + 0.5 * psi)
    qz = np.cos(half_th) * np.sin(0.5 * psi)
    q = np.column_stack([qw, qx, qy, qz])
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    # Canonicalize hemisphere for uniqueness (w >= 0)
    flip = q[:, 0] < 0.0
    q[flip] *= -1.0
    return q


def quaternion_to_rotation(q: np.ndarray) -> np.ndarray:
    """Map unit quaternion ``(w,x,y,z)`` to a 3×3 rotation matrix."""
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )


def rotation_to_quaternion(R: np.ndarray) -> np.ndarray:
    """Shepperd conversion; returns ``(w,x,y,z)`` with ``w >= 0``."""
    m00, m01, m02 = R[0]
    m10, m11, m12 = R[1]
    m20, m21, m22 = R[2]
    trace = m00 + m11 + m22
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (m21 - m12) / s
        y = (m02 - m20) / s
        z = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    q = np.array([w, x, y, z], dtype=float)
    q /= np.linalg.norm(q)
    if q[0] < 0.0:
        q *= -1.0
    return q


def geodesic_angle(Ra: np.ndarray, Rb: np.ndarray) -> float:
    """Geodesic angle between two rotations (radians in [0, π])."""
    R = Ra.T @ Rb
    cos_th = 0.5 * (np.trace(R) - 1.0)
    return float(math.acos(max(-1.0, min(1.0, cos_th))))


def sample_orientations(
    resolution: SampleResolution = "coarse",
    *,
    seed: int = 0,
    count: int | None = None,
) -> list[np.ndarray]:
    """Return a list of 3×3 rotation matrices for the requested resolution."""
    n = count if count is not None else RESOLUTION_COUNTS[resolution]
    qs = hopf_quaternion_grid(n, seed=seed)
    return [quaternion_to_rotation(q) for q in qs]


def rotation_from_mat4(T: tuple[tuple[float, ...], ...]) -> np.ndarray:
    """Extract 3×3 rotation from an SE(3) Mat4 tuple."""
    return np.array(
        [
            [T[0][0], T[0][1], T[0][2]],
            [T[1][0], T[1][1], T[1][2]],
            [T[2][0], T[2][1], T[2][2]],
        ],
        dtype=float,
    )
