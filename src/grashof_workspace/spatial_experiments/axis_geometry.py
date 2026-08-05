"""Point-direction axis geometry for spatial terminal-roll experiments.

Conventions
-----------
A revolute axis is the directed line ``A = (r, w)`` where:

- ``r`` is any point on the axis (metres, frame ``W``);
- ``w`` is a unit direction (dimensionless);
- positive rotation follows the right-hand rule about ``w``.

Equality of axes is line equality, not equality of the representative point ``r``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Vec3 = NDArray[np.floating]


def unit_vector(v: Vec3 | tuple[float, float, float], *, name: str = "vector") -> Vec3:
    """Return a unit vector, rejecting a zero-length direction.

    Boundary: ``||v|| = 0`` raises ``ValueError``.
    Interior: any nonzero ``v`` returns ``v / ||v||``.
    """
    arr = np.asarray(v, dtype=float).reshape(3)
    n = float(np.linalg.norm(arr))
    if n == 0.0:
        raise ValueError(f"cannot normalize zero-length {name}")
    return arr / n


@dataclass(frozen=True, slots=True)
class AxisLine:
    """Directed line ``A = (r, w)`` with unit direction ``w``.

    Parameters
    ----------
    r:
        Any point on the axis in metres (frame ``W``).
    w:
        Axis direction; normalized to unit length on construction.
    """

    r: tuple[float, float, float]
    w: tuple[float, float, float]

    def __post_init__(self) -> None:
        w_unit = unit_vector(self.w, name="axis direction")
        object.__setattr__(self, "w", (float(w_unit[0]), float(w_unit[1]), float(w_unit[2])))
        object.__setattr__(
            self,
            "r",
            (float(self.r[0]), float(self.r[1]), float(self.r[2])),
        )

    @property
    def r_array(self) -> Vec3:
        return np.asarray(self.r, dtype=float)

    @property
    def w_array(self) -> Vec3:
        return np.asarray(self.w, dtype=float)


def point_axis_distance(x: Vec3 | tuple[float, float, float], axis: AxisLine) -> float:
    """Return Euclidean distance from point ``x`` to axis ``(r, w)``.

    Formula (MATH / geometric conventions)::

        ||(I - w w^T)(x - r)||

    Equality: a point on the axis has distance exactly ``0``.
    Exterior: a transverse offset of length ``L`` yields distance ``L``.
    """
    x_arr = np.asarray(x, dtype=float).reshape(3)
    delta = x_arr - axis.r_array
    w = axis.w_array
    radial = delta - float(np.dot(delta, w)) * w
    return float(np.linalg.norm(radial))


def parallelism_residual(
    a: Vec3 | tuple[float, float, float],
    b: Vec3 | tuple[float, float, float],
) -> float:
    """Return ``||a_hat x b_hat||``, the unsigned parallelism residual.

    Both inputs are normalized. Parallel or anti-parallel unit vectors give
    residual ``0`` (boundary). Non-aligned directions give a positive residual
    (interior / exterior relative to the aligned set).
    """
    a_hat = unit_vector(a, name="direction a")
    b_hat = unit_vector(b, name="direction b")
    return float(np.linalg.norm(np.cross(a_hat, b_hat)))


def are_parallel(
    a: Vec3 | tuple[float, float, float],
    b: Vec3 | tuple[float, float, float],
    *,
    tol: float = 1e-12,
) -> bool:
    """Return True when unit directions are parallel or anti-parallel within ``tol``."""
    return parallelism_residual(a, b) <= tol
