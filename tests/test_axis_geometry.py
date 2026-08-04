"""Axis geometry unit tests."""

from __future__ import annotations

import math

import pytest

from sixr_grashof.kinematics.axes import (
    AxisLine,
    angular_separation,
    are_parallel,
    intersection_point,
    least_squares_spherical_center,
    point_line_distance,
    shortest_distance,
)
from sixr_grashof.reductions import concurrency_residual


def test_parallel_and_distance() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    b = AxisLine((1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    assert are_parallel(a, b)
    assert shortest_distance(a, b) == pytest.approx(1.0)


def test_intersection_of_perpendicular_axes() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    b = AxisLine((0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    p = intersection_point(a, b)
    assert p is not None
    assert point_line_distance(p, a) == pytest.approx(0.0)
    assert point_line_distance(p, b) == pytest.approx(0.0)
    assert angular_separation(a, b) == pytest.approx(math.pi / 2)


def test_exact_concurrency_residual() -> None:
    c = (1.0, 2.0, 3.0)
    axes = [
        AxisLine(c, (1.0, 0.0, 0.0)),
        AxisLine(c, (0.0, 1.0, 0.0)),
        AxisLine(c, (0.0, 0.0, 1.0)),
    ]
    center = least_squares_spherical_center(axes)
    assert center[0] == pytest.approx(1.0)
    assert center[1] == pytest.approx(2.0)
    assert center[2] == pytest.approx(3.0)
    report = concurrency_residual(axes, scale_L2=1.0)
    assert report.status == "exact"
    assert report.residual_rho == pytest.approx(0.0)


def test_offset_concurrency_scales() -> None:
    axes0 = [
        AxisLine((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        AxisLine((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    ]
    # Offset the third axis perpendicular to its direction.
    axes1 = [
        AxisLine((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        AxisLine((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        AxisLine((0.1, 0.0, 0.0), (0.0, 0.0, 1.0)),
    ]
    r0 = concurrency_residual(axes0, scale_L2=1.0)
    r1 = concurrency_residual(axes1, scale_L2=1.0)
    assert r0.status == "exact"
    assert r1.residual_rho > r0.residual_rho
    assert r1.residual_rho == pytest.approx(0.05, rel=1e-6)
    assert r1.status in {"approximate", "invalid"}
