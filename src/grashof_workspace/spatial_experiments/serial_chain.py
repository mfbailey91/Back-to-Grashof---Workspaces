"""Serial revolute chain with space product-of-exponentials kinematics.

Conventions
-----------
- Joint order is base ``R1`` through tool ``Rn`` (0-based index ``i`` maps to ``R{i+1}``).
- Home axes are directed lines in world frame ``W`` (``W = B`` unless a caller
  introduces a base transform).
- Space PoE: ``T(q) = exp([ξ1]q1) … exp([ξn]qn) M``.
- Applying ``T(q)`` to a home point therefore rotates about home axes from distal
  to proximal: joint ``n``, then ``n-1``, …, then joint ``1``.
- Task point ``p`` and pointing ``d`` are expressed in ``W``.
- Positive rotation follows the right-hand rule about each axis direction.
- Angles are radians; lengths are metres. No DH parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import AxisLine, unit_vector
from .rotations import rotate_point_about_axis, rotate_vector_about_axis, rotation_about_axis

Vec3 = NDArray[np.floating]
Mat3 = NDArray[np.floating]


@dataclass(frozen=True, slots=True)
class ChainState:
    """World-frame forward-kinematics snapshot."""

    q: tuple[float, ...]
    p: Vec3
    d: Vec3
    R: Mat3
    axes: tuple[AxisLine, ...]


@dataclass(frozen=True, slots=True)
class SerialRevoluteChain:
    """Open serial chain of revolute joints defined by home axis lines.

    Parameters
    ----------
    home_axes:
        Home configuration axes ``(r_i, w_i)`` in ``W``, proximal to distal.
    p0:
        Task point at ``q = 0``, metres in ``W``.
    d0:
        Pointing direction at ``q = 0`` (normalized on construction).
    R0:
        Tool orientation at ``q = 0``.
    """

    home_axes: tuple[AxisLine, ...]
    p0: tuple[float, float, float]
    d0: tuple[float, float, float]
    R0: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

    def __post_init__(self) -> None:
        if len(self.home_axes) < 1:
            raise ValueError("serial chain requires at least one revolute axis")
        d_unit = unit_vector(self.d0, name="pointing direction d0")
        object.__setattr__(self, "d0", (float(d_unit[0]), float(d_unit[1]), float(d_unit[2])))
        object.__setattr__(self, "p0", tuple(float(x) for x in self.p0))
        R = np.asarray(self.R0, dtype=float).reshape(3, 3)
        if abs(float(np.linalg.det(R)) - 1.0) > 1e-8:
            raise ValueError("R0 must be a proper rotation matrix (det = 1)")
        if float(np.linalg.norm(R.T @ R - np.eye(3))) > 1e-8:
            raise ValueError("R0 must be orthonormal")
        object.__setattr__(
            self,
            "R0",
            tuple(tuple(float(R[i, j]) for j in range(3)) for i in range(3)),
        )

    @property
    def n_joints(self) -> int:
        return len(self.home_axes)

    @property
    def p0_array(self) -> Vec3:
        return np.asarray(self.p0, dtype=float)

    @property
    def d0_array(self) -> Vec3:
        return np.asarray(self.d0, dtype=float)

    @property
    def R0_array(self) -> Mat3:
        return np.asarray(self.R0, dtype=float)

    def evaluate(self, q: tuple[float, ...] | NDArray[np.floating]) -> ChainState:
        """Return world ``p``, ``d``, ``R`` and current axes at configuration ``q``."""
        q_t = _as_q(q, self.n_joints)
        p = self.p0_array.copy()
        d = self.d0_array.copy()
        R = self.R0_array.copy()
        for i in range(self.n_joints - 1, -1, -1):
            axis = self.home_axes[i]
            angle = q_t[i]
            p = rotate_point_about_axis(p, axis, angle)
            d = rotate_vector_about_axis(d, axis.w, angle)
            R = rotation_about_axis(axis.w, angle) @ R
        d = d / float(np.linalg.norm(d))
        return ChainState(q=q_t, p=p, d=d, R=R, axes=self.current_axes(q_t))

    def current_axes(self, q: tuple[float, ...] | NDArray[np.floating]) -> tuple[AxisLine, ...]:
        """Return each axis after proximal joints ``q1…q_{i-1}`` have acted."""
        q_t = _as_q(q, self.n_joints)
        moved: list[AxisLine] = []
        for i, home in enumerate(self.home_axes):
            r = np.asarray(home.r, dtype=float)
            w = np.asarray(home.w, dtype=float)
            for j in range(i - 1, -1, -1):
                r = rotate_point_about_axis(r, self.home_axes[j], q_t[j])
                w = rotate_vector_about_axis(w, self.home_axes[j].w, q_t[j])
            moved.append(AxisLine((float(r[0]), float(r[1]), float(r[2])), (float(w[0]), float(w[1]), float(w[2]))))
        return tuple(moved)


def _as_q(q: tuple[float, ...] | NDArray[np.floating], n: int) -> tuple[float, ...]:
    arr = np.asarray(q, dtype=float).reshape(-1)
    if arr.size != n:
        raise ValueError(f"expected {n} joint coordinates, got {arr.size}")
    return tuple(float(x) for x in arr)
