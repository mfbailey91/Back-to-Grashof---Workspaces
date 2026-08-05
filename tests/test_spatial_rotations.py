"""Unit tests for spatial rotation primitives."""

from __future__ import annotations

import math

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.axis_geometry import AxisLine
from grashof_workspace.spatial_experiments.rotations import (
    axis_angle_from_rotation,
    relative_rotation,
    rotate_point_about_axis,
    rotate_vector_about_axis,
    rotation_about_axis,
)


def test_rotation_about_axis_boundary_identity() -> None:
    R = rotation_about_axis((0.0, 0.0, 1.0), 0.0)
    assert float(np.linalg.norm(R - np.eye(3))) == pytest.approx(0.0)


def test_rotation_about_z_interior_90_deg() -> None:
    R = rotation_about_axis((0.0, 0.0, 1.0), math.pi / 2)
    v = rotate_vector_about_axis((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), math.pi / 2)
    assert v[0] == pytest.approx(0.0, abs=1e-12)
    assert v[1] == pytest.approx(1.0, abs=1e-12)
    assert v[2] == pytest.approx(0.0, abs=1e-12)
    assert float(np.linalg.det(R)) == pytest.approx(1.0)


def test_rotate_point_about_offset_axis() -> None:
    axis = AxisLine((1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    # Point at (2,0,0): radius 1 about axis through (1,0,0).
    p = rotate_point_about_axis((2.0, 0.0, 0.0), axis, math.pi / 2)
    assert p[0] == pytest.approx(1.0, abs=1e-12)
    assert p[1] == pytest.approx(1.0, abs=1e-12)
    assert p[2] == pytest.approx(0.0, abs=1e-12)


def test_axis_angle_roundtrip_interior() -> None:
    w = np.array([1.0, 2.0, 3.0], dtype=float)
    w = w / float(np.linalg.norm(w))
    angle = 0.7
    R = rotation_about_axis(w, angle)
    axis, recovered = axis_angle_from_rotation(R)
    assert recovered == pytest.approx(angle, abs=1e-12)
    assert abs(float(np.dot(axis, w))) == pytest.approx(1.0, abs=1e-12)


def test_axis_angle_boundary_identity() -> None:
    axis, angle = axis_angle_from_rotation(np.eye(3))
    assert angle == pytest.approx(0.0)
    assert float(np.linalg.norm(axis)) == pytest.approx(1.0)


def test_relative_rotation_composition() -> None:
    R0 = rotation_about_axis((0.0, 0.0, 1.0), 0.2)
    R1 = rotation_about_axis((0.0, 0.0, 1.0), 0.5)
    R_rel = relative_rotation(R0, R1)
    axis, angle = axis_angle_from_rotation(R_rel)
    assert angle == pytest.approx(0.3, abs=1e-12)
    assert abs(axis[2]) == pytest.approx(1.0, abs=1e-12)
