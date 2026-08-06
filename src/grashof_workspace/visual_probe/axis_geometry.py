"""Exact line-line relationship classification for the visual probe.

Conventions
-----------
Each revolute axis is ``AxisLine(point, direction)`` with unit direction.
Axis sign does not affect incidence classification. Labels:

- ``collinear`` — parallel and distance ~ 0
- ``intersecting`` — non-parallel and distance ~ 0
- ``parallel_distinct`` — parallel and distance > tol
- ``skew`` — non-parallel and distance > tol
- ``numerically_ambiguous`` — residuals fall between incidence and clear tol
"""

from __future__ import annotations

import math

from .model import AxisLine, AxisRelation, AxisRelationship, Vec3


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _norm(a: Vec3) -> float:
    return math.sqrt(_dot(a, a))


def line_line_distance(a: AxisLine, b: AxisLine) -> float:
    """Return the Euclidean distance between two directed lines."""
    w0 = _sub(a.point, b.point)
    cross = _cross(a.direction, b.direction)
    n = _norm(cross)
    if n == 0.0:
        return _norm(_cross(w0, a.direction))
    return abs(_dot(w0, cross)) / n


def are_parallel(a: AxisLine, b: AxisLine, *, tol: float) -> bool:
    return abs(abs(_dot(a.direction, b.direction)) - 1.0) <= tol


def intersection_point(
    a: AxisLine,
    b: AxisLine,
    *,
    tol: float,
) -> Vec3 | None:
    """Return an intersection point when lines meet within ``tol``."""
    if line_line_distance(a, b) > tol:
        return None
    if are_parallel(a, b, tol=tol):
        return a.point
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


def classify_axis_pair(
    a: AxisLine,
    b: AxisLine,
    *,
    joint_a: int,
    joint_b: int,
    incidence_tol: float,
    parallel_tol: float,
    ambiguous_tol: float,
) -> AxisRelationship:
    """Classify the geometric relationship of one adjacent axis pair."""
    distance = line_line_distance(a, b)
    parallel = are_parallel(a, b, tol=parallel_tol)

    if distance <= incidence_tol:
        if parallel:
            relation: AxisRelation = "collinear"
            point: Vec3 | None = a.point
        else:
            relation = "intersecting"
            point = intersection_point(a, b, tol=incidence_tol)
        return AxisRelationship(joint_a, joint_b, relation, distance, point)

    if distance <= ambiguous_tol:
        return AxisRelationship(joint_a, joint_b, "numerically_ambiguous", distance, None)

    if parallel:
        return AxisRelationship(joint_a, joint_b, "parallel_distinct", distance, None)
    return AxisRelationship(joint_a, joint_b, "skew", distance, None)


def point_axis_distance(point: Vec3, axis: AxisLine) -> float:
    return _norm(_cross(_sub(point, axis.point), axis.direction))


def parallelism_residual(a: Vec3, b: Vec3) -> float:
    return _norm(_cross(a, b))
