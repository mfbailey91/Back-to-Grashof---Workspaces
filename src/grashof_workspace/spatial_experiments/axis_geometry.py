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
Vec3Tuple = tuple[float, float, float]
Mat3Tuple = tuple[Vec3Tuple, Vec3Tuple, Vec3Tuple]


def as_vec3(values: Vec3 | tuple[float, ...] | list[float]) -> Vec3Tuple:
    """Cast a length-3 array-like to ``tuple[float, float, float]``."""
    arr = np.asarray(values, dtype=float).reshape(3)
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def as_mat3(values: NDArray[np.floating] | tuple[tuple[float, ...], ...]) -> Mat3Tuple:
    """Cast a 3×3 array-like to a nested float triple."""
    mat = np.asarray(values, dtype=float).reshape(3, 3)
    return (
        as_vec3(mat[0]),
        as_vec3(mat[1]),
        as_vec3(mat[2]),
    )


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


def line_line_distance(a: AxisLine, b: AxisLine) -> float:
    """Return the Euclidean distance between two directed lines.

    Formula::

        ||(r_b - r_a) · (w_a × w_b)|| / ||w_a × w_b||

    when the directions are not parallel. Parallel lines use the transverse
    offset of ``r_b - r_a`` from ``w_a``.

    Equality: intersecting or coincident lines have distance ``0``.
    Interior / exterior: a positive common perpendicular length is returned.
    """
    w_a = a.w_array
    w_b = b.w_array
    delta = b.r_array - a.r_array
    cross = np.cross(w_a, w_b)
    n = float(np.linalg.norm(cross))
    if n == 0.0:
        return float(np.linalg.norm(delta - float(np.dot(delta, w_a)) * w_a))
    return abs(float(np.dot(delta, cross))) / n


def line_closest_points(a: AxisLine, b: AxisLine) -> tuple[Vec3, Vec3]:
    """Return the closest points on ``a`` and ``b``.

    Equality: intersecting lines share the same closest point.
    Parallel distinct lines return a transverse pair.
    """
    w_a = a.w_array
    w_b = b.w_array
    delta = b.r_array - a.r_array
    cos = float(np.dot(w_a, w_b))
    denom = 1.0 - cos * cos
    if denom <= 1e-24:
        point_a = a.r_array + float(np.dot(delta, w_a)) * w_a
        point_b = b.r_array + float(np.dot(point_a - b.r_array, w_b)) * w_b
        return point_a, point_b
    delta_a = float(np.dot(delta, w_a))
    delta_b = float(np.dot(delta, w_b))
    s = (delta_a - cos * delta_b) / denom
    t = (cos * delta_a - delta_b) / denom
    return a.r_array + s * w_a, b.r_array + t * w_b


def line_intersection_point(
    a: AxisLine,
    b: AxisLine,
    *,
    tol_m: float = 1e-12,
) -> tuple[float, float, float] | None:
    """Return the closest-approach midpoint if the lines intersect within ``tol_m``.

    Interior: concurrent nonparallel lines return the shared point.
    Exterior: a positive common perpendicular rejects the intersection.
    Boundary: distance equal to ``tol_m`` is accepted.
    """
    if line_line_distance(a, b) > tol_m:
        return None
    point_a, point_b = line_closest_points(a, b)
    mid = 0.5 * (point_a + point_b)
    return (float(mid[0]), float(mid[1]), float(mid[2]))


def are_parallel(
    a: Vec3 | tuple[float, float, float],
    b: Vec3 | tuple[float, float, float],
    *,
    tol: float = 1e-12,
) -> bool:
    """Return True when unit directions are parallel or anti-parallel within ``tol``."""
    return parallelism_residual(a, b) <= tol
