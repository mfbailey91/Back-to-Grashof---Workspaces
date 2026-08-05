"""Isolated terminal-revolute fixture for aligned terminal-roll validation.

Conventions
-----------
The fixture places a single revolute axis ``R6 = (r6, w6)`` in world frame ``W``
and attaches a tool frame whose body-fixed task point and pointing direction are
explicit inputs (not DH-derived).

World outputs at joint angle ``q6`` (radians, right-hand about ``w6``)::

    p(q6) = r6 + R(w6, q6)(p0 - r6)
    d(q6) = R(w6, q6) d0
    R(q6) = R(w6, q6) @ R0

Analytical derivatives::

    dp/dq6 = w6 x (p - r6)
    dd/dq6 = w6 x d

Aligned terminal roll requires ``distance(p, R6) = 0`` and ``d parallel w6``,
which implies both derivatives vanish while full orientation still rolls.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import (
    AxisLine,
    parallelism_residual,
    point_axis_distance,
    unit_vector,
)
from .rotations import rotate_point_about_axis, rotate_vector_about_axis, rotation_about_axis

Vec3 = NDArray[np.floating]
Mat3 = NDArray[np.floating]


@dataclass(frozen=True, slots=True)
class TerminalRollState:
    """World-frame snapshot of the terminal-roll fixture."""

    q6: float
    p: Vec3
    d: Vec3
    R: Mat3
    dp_dq6: Vec3
    dd_dq6: Vec3


@dataclass(frozen=True, slots=True)
class TerminalRollFixture:
    """Single revolute terminal joint with explicit task point and pointing.

    Parameters
    ----------
    axis:
        Terminal revolute axis ``R6 = (r6, w6)`` in frame ``W``.
    p0:
        Task point at ``q6 = 0``, metres in ``W``.
    d0:
        Tool pointing direction at ``q6 = 0`` (normalized on construction).
    R0:
        Tool orientation at ``q6 = 0``. Defaults to a right-handed frame with
        column 2 aligned to ``d0`` when omitted.
    """

    axis: AxisLine
    p0: tuple[float, float, float]
    d0: tuple[float, float, float]
    R0: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

    def __post_init__(self) -> None:
        d_unit = unit_vector(self.d0, name="pointing direction d0")
        object.__setattr__(
            self,
            "d0",
            (float(d_unit[0]), float(d_unit[1]), float(d_unit[2])),
        )
        object.__setattr__(
            self,
            "p0",
            (float(self.p0[0]), float(self.p0[1]), float(self.p0[2])),
        )
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

    @classmethod
    def from_explicit(
        cls,
        *,
        axis: AxisLine,
        p0: tuple[float, float, float] | Vec3,
        d0: tuple[float, float, float] | Vec3,
        R0: Mat3 | None = None,
    ) -> TerminalRollFixture:
        """Build a fixture, synthesizing a right-handed ``R0`` from ``d0`` if needed."""
        p_t = tuple(float(x) for x in np.asarray(p0, dtype=float).reshape(3))
        d_t = tuple(float(x) for x in np.asarray(d0, dtype=float).reshape(3))
        if R0 is None:
            R_mat = _frame_from_pointing(d_t)
        else:
            R_mat = np.asarray(R0, dtype=float).reshape(3, 3)
        R_tuple = tuple(tuple(float(R_mat[i, j]) for j in range(3)) for i in range(3))
        return cls(axis=axis, p0=p_t, d0=d_t, R0=R_tuple)  # type: ignore[arg-type]

    @property
    def p0_array(self) -> Vec3:
        return np.asarray(self.p0, dtype=float)

    @property
    def d0_array(self) -> Vec3:
        return np.asarray(self.d0, dtype=float)

    @property
    def R0_array(self) -> Mat3:
        return np.asarray(self.R0, dtype=float)

    def evaluate(self, q6: float) -> TerminalRollState:
        """Return world ``p``, ``d``, ``R`` and analytical derivatives at ``q6``."""
        p = rotate_point_about_axis(self.p0_array, self.axis, q6)
        d = rotate_vector_about_axis(self.d0_array, self.axis.w, q6)
        d = d / float(np.linalg.norm(d))
        R = rotation_about_axis(self.axis.w, q6) @ self.R0_array
        dp = analytical_dp_dq6(p, self.axis)
        dd = analytical_dd_dq6(d, self.axis)
        return TerminalRollState(q6=q6, p=p, d=d, R=R, dp_dq6=dp, dd_dq6=dd)

    def point_axis_distance_at(self, q6: float) -> float:
        return point_axis_distance(self.evaluate(q6).p, self.axis)

    def pointing_parallelism_residual_at(self, q6: float) -> float:
        state = self.evaluate(q6)
        return parallelism_residual(state.d, self.axis.w)


def analytical_dp_dq6(p: Vec3 | tuple[float, float, float], axis: AxisLine) -> Vec3:
    """Analytical position derivative ``dp/dq6 = w6 x (p - r6)``."""
    p_arr = np.asarray(p, dtype=float).reshape(3)
    return np.cross(axis.w_array, p_arr - axis.r_array)


def analytical_dd_dq6(d: Vec3 | tuple[float, float, float], axis: AxisLine) -> Vec3:
    """Analytical pointing derivative ``dd/dq6 = w6 x d``."""
    d_arr = np.asarray(d, dtype=float).reshape(3)
    return np.cross(axis.w_array, d_arr)


def _frame_from_pointing(d: tuple[float, float, float]) -> Mat3:
    """Build a right-handed frame with column 2 equal to unit ``d``."""
    z = unit_vector(d, name="pointing")
    # Choose a helper not parallel to z.
    helper = np.array([1.0, 0.0, 0.0], dtype=float)
    if abs(float(np.dot(helper, z))) > 0.9:
        helper = np.array([0.0, 1.0, 0.0], dtype=float)
    x = np.cross(helper, z)
    x = x / float(np.linalg.norm(x))
    y = np.cross(z, x)
    return np.column_stack([x, y, z])
