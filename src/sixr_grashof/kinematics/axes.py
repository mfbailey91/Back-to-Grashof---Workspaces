"""Directed lines in R3 and geometric predicates.

Conventions
-----------
A revolute axis is the directed line ``ell = (p, a_hat)`` with ``||a_hat|| = 1``.
Points and directions are ``tuple[float, float, float]``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Vec3 = tuple[float, float, float]


def _dot(u: Vec3, v: Vec3) -> float:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _cross(u: Vec3, v: Vec3) -> Vec3:
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _sub(u: Vec3, v: Vec3) -> Vec3:
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])


def _add(u: Vec3, v: Vec3) -> Vec3:
    return (u[0] + v[0], u[1] + v[1], u[2] + v[2])


def _scale(u: Vec3, s: float) -> Vec3:
    return (u[0] * s, u[1] * s, u[2] * s)


def _norm(u: Vec3) -> float:
    return math.sqrt(_dot(u, u))


def normalize(u: Vec3) -> Vec3:
    n = _norm(u)
    if n == 0.0:
        raise ValueError("cannot normalize zero vector")
    return _scale(u, 1.0 / n)


@dataclass(frozen=True, slots=True)
class AxisLine:
    """Directed line ``ell = (point, direction)`` with unit direction."""

    point: Vec3
    direction: Vec3

    def __post_init__(self) -> None:
        n = _norm(self.direction)
        if abs(n - 1.0) > 1e-9:
            object.__setattr__(self, "direction", normalize(self.direction))


def angular_separation(a: AxisLine, b: AxisLine) -> float:
    """Return angle in ``[0, pi/2]`` between axis directions (unsigned)."""
    c = abs(_dot(a.direction, b.direction))
    c = min(1.0, max(0.0, c))
    return math.acos(c)


def are_parallel(
    a: AxisLine,
    b: AxisLine,
    *,
    tol: float = 1e-12,
) -> bool:
    return abs(abs(_dot(a.direction, b.direction)) - 1.0) <= tol


def are_antiparallel(
    a: AxisLine,
    b: AxisLine,
    *,
    tol: float = 1e-12,
) -> bool:
    return abs(_dot(a.direction, b.direction) + 1.0) <= tol


def shortest_distance(a: AxisLine, b: AxisLine, *, tol: float = 1e-12) -> float:
    """Return the shortest distance between two lines in R3."""
    w0 = _sub(a.point, b.point)
    if are_parallel(a, b, tol=tol):
        # Distance from b.point to line a.
        return _norm(_cross(w0, a.direction))
    n = _cross(a.direction, b.direction)
    return abs(_dot(w0, n)) / _norm(n)


def point_line_distance(point: Vec3, line: AxisLine) -> float:
    return _norm(_cross(_sub(point, line.point), line.direction))


def intersection_point(
    a: AxisLine,
    b: AxisLine,
    *,
    tol: float = 1e-12,
) -> Vec3 | None:
    """Return an intersection point if lines intersect within ``tol``, else None."""
    if shortest_distance(a, b, tol=tol) > tol:
        return None
    if are_parallel(a, b, tol=tol):
        # Coincident or parallel-nonintersecting; if distance ~ 0, any point on a.
        if shortest_distance(a, b, tol=tol) <= tol:
            return a.point
        return None
    # Solve a.p + s a.d = b.p + t b.d in least squares / exact for skew=0.
    w0 = _sub(a.point, b.point)
    ad = a.direction
    bd = b.direction
    a_dot_a = _dot(ad, ad)
    b_dot_b = _dot(bd, bd)
    a_dot_b = _dot(ad, bd)
    a_dot_w = _dot(ad, w0)
    b_dot_w = _dot(bd, w0)
    denom = a_dot_a * b_dot_b - a_dot_b * a_dot_b
    if abs(denom) <= tol:
        return a.point
    s = (a_dot_b * b_dot_w - b_dot_b * a_dot_w) / denom
    return _add(a.point, _scale(ad, s))


def least_squares_spherical_center(axes: list[AxisLine]) -> Vec3:
    """Return the least-squares concurrency center for an axis cluster.

    Minimizes ``sum_i || (I - a_i a_i^T)(c - p_i) ||^2``.
    """
    if not axes:
        raise ValueError("axes must be nonempty")
    # Accumulate 3x3 system A c = b.
    A = [[0.0, 0.0, 0.0] for _ in range(3)]
    b = [0.0, 0.0, 0.0]
    for axis in axes:
        ax, ay, az = axis.direction
        # P = I - a a^T
        P = [
            [1.0 - ax * ax, -ax * ay, -ax * az],
            [-ay * ax, 1.0 - ay * ay, -ay * az],
            [-az * ax, -az * ay, 1.0 - az * az],
        ]
        px, py, pz = axis.point
        # A += P, b += P p
        for i in range(3):
            b[i] += P[i][0] * px + P[i][1] * py + P[i][2] * pz
            for j in range(3):
                A[i][j] += P[i][j]
    return _solve3(A, b)


def _solve3(A: list[list[float]], b: list[float]) -> Vec3:
    """Solve a 3x3 linear system by Gaussian elimination with partial pivoting."""
    M = [A[i][:] + [b[i]] for i in range(3)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(M[r][col]))
        if abs(M[pivot][col]) < 1e-15:
            raise ValueError("singular concurrency system")
        M[col], M[pivot] = M[pivot], M[col]
        div = M[col][col]
        for j in range(col, 4):
            M[col][j] /= div
        for row in range(3):
            if row == col:
                continue
            factor = M[row][col]
            for j in range(col, 4):
                M[row][j] -= factor * M[col][j]
    return (M[0][3], M[1][3], M[2][3])
