"""Unit tests for spatial axis-line geometry."""

from __future__ import annotations

import math

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.axis_geometry import (
    AxisLine,
    are_parallel,
    parallelism_residual,
    point_axis_distance,
    unit_vector,
)


def test_unit_vector_interior() -> None:
    u = unit_vector((3.0, 0.0, 4.0))
    assert float(np.linalg.norm(u)) == pytest.approx(1.0)
    assert u[0] == pytest.approx(0.6)
    assert u[2] == pytest.approx(0.8)


def test_unit_vector_zero_boundary_fails() -> None:
    with pytest.raises(ValueError, match="zero-length"):
        unit_vector((0.0, 0.0, 0.0))


def test_axis_normalizes_direction() -> None:
    axis = AxisLine((1.0, 2.0, 3.0), (0.0, 0.0, 5.0))
    assert axis.w == pytest.approx((0.0, 0.0, 1.0))


def test_point_on_axis_distance_equality() -> None:
    axis = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    assert point_axis_distance((0.0, 0.0, 7.0), axis) == pytest.approx(0.0)


def test_point_axis_distance_exterior_offset() -> None:
    axis = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    assert point_axis_distance((0.3, 0.4, 2.0), axis) == pytest.approx(0.5)


def test_point_axis_distance_invariant_to_axis_point() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    b = AxisLine((5.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    x = (2.0, 1.0, 0.0)
    assert point_axis_distance(x, a) == pytest.approx(point_axis_distance(x, b))


def test_parallelism_residual_boundary_parallel_and_antiparallel() -> None:
    assert parallelism_residual((0.0, 0.0, 1.0), (0.0, 0.0, 2.0)) == pytest.approx(0.0)
    assert parallelism_residual((0.0, 0.0, 1.0), (0.0, 0.0, -1.0)) == pytest.approx(0.0)
    assert are_parallel((1.0, 0.0, 0.0), (-2.0, 0.0, 0.0))


def test_parallelism_residual_interior_orthogonal() -> None:
    assert parallelism_residual((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == pytest.approx(1.0)


def test_parallelism_residual_exterior_oblique() -> None:
    # 45 degrees: ||a x b|| = sin(theta) = sqrt(2)/2
    residual = parallelism_residual((1.0, 0.0, 0.0), (1.0, 1.0, 0.0))
    assert residual == pytest.approx(math.sqrt(2.0) / 2.0)
