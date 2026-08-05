"""Unit tests for the isolated terminal-roll fixture."""

from __future__ import annotations

import math

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.axis_geometry import AxisLine, point_axis_distance
from grashof_workspace.spatial_experiments.diagnostics import (
    make_aligned_fixture,
    make_misaligned_pointing_fixture,
    make_off_axis_fixture,
)
from grashof_workspace.spatial_experiments.terminal_roll_fixture import (
    TerminalRollFixture,
    analytical_dd_dq6,
    analytical_dp_dq6,
)


def test_aligned_fixture_point_on_axis_and_parallel_pointing() -> None:
    fixture = make_aligned_fixture()
    state = fixture.evaluate(0.0)
    assert point_axis_distance(state.p, fixture.axis) == pytest.approx(0.0)
    assert float(np.linalg.norm(np.cross(state.d, fixture.axis.w_array))) == pytest.approx(0.0)


def test_aligned_derivatives_vanish_equality() -> None:
    fixture = make_aligned_fixture()
    for q in (0.0, 0.4, 1.7, math.pi):
        state = fixture.evaluate(q)
        assert float(np.linalg.norm(state.dp_dq6)) == pytest.approx(0.0, abs=1e-14)
        assert float(np.linalg.norm(state.dd_dq6)) == pytest.approx(0.0, abs=1e-14)


def test_off_axis_position_derivative_nonzero_exterior() -> None:
    fixture = make_off_axis_fixture(transverse_offset_m=0.03)
    state = fixture.evaluate(0.2)
    assert float(np.linalg.norm(state.dp_dq6)) > 1e-6
    assert float(np.linalg.norm(state.dd_dq6)) == pytest.approx(0.0, abs=1e-14)


def test_misaligned_pointing_derivative_nonzero() -> None:
    fixture = make_misaligned_pointing_fixture(tilt_rad=0.25)
    state = fixture.evaluate(0.1)
    assert float(np.linalg.norm(state.dp_dq6)) == pytest.approx(0.0, abs=1e-14)
    assert float(np.linalg.norm(state.dd_dq6)) > 1e-6


def test_analytical_derivative_helpers_match_state() -> None:
    fixture = make_off_axis_fixture()
    state = fixture.evaluate(0.55)
    assert analytical_dp_dq6(state.p, fixture.axis) == pytest.approx(state.dp_dq6)
    assert analytical_dd_dq6(state.d, fixture.axis) == pytest.approx(state.dd_dq6)


def test_fixture_rejects_non_rotation_R0() -> None:
    axis = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    bad = ((2.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="proper rotation"):
        TerminalRollFixture(axis=axis, p0=(0.0, 0.0, 0.0), d0=(0.0, 0.0, 1.0), R0=bad)


def test_evaluate_is_deterministic() -> None:
    fixture = make_aligned_fixture()
    a = fixture.evaluate(0.123)
    b = fixture.evaluate(0.123)
    assert a.p == pytest.approx(b.p)
    assert a.d == pytest.approx(b.d)
    assert a.R == pytest.approx(b.R)
