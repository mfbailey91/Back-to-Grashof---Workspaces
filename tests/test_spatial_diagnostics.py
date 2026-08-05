"""Tests for terminal-roll controls and finite-difference refinement."""

from __future__ import annotations

import math

import numpy as np

from grashof_workspace.spatial_experiments.diagnostics import (
    central_difference_derivatives,
    evaluate_combined_control,
    evaluate_fd_refinement,
    evaluate_misaligned_control,
    evaluate_off_axis_control,
    evaluate_positive_control,
    fd_converges,
    finite_difference_refinement,
    make_aligned_fixture,
    make_combined_violation_fixture,
    make_off_axis_fixture,
    signed_roll_about_direction,
    sweep_residuals,
)
from grashof_workspace.spatial_experiments.rotations import rotation_about_axis


def test_positive_control_pass() -> None:
    result = evaluate_positive_control()
    assert result.status == "PASS"
    assert not result.metrics.position_changes
    assert not result.metrics.pointing_changes
    assert result.metrics.roll_recovered


def test_off_axis_negative_control_pass() -> None:
    result = evaluate_off_axis_control()
    assert result.status == "PASS"
    assert result.metrics.position_changes
    assert not result.metrics.pointing_changes


def test_misaligned_negative_control_pass() -> None:
    result = evaluate_misaligned_control()
    assert result.status == "PASS"
    assert not result.metrics.position_changes
    assert result.metrics.pointing_changes


def test_combined_negative_control_pass() -> None:
    result = evaluate_combined_control()
    assert result.status == "PASS"
    assert result.metrics.position_changes
    assert result.metrics.pointing_changes


def test_signed_roll_full_circle() -> None:
    d = np.array([0.0, 0.0, 1.0], dtype=float)
    for angle in (0.0, 0.5, math.pi / 2, 2.0, math.pi, 4.0, 2.0 * math.pi - 0.1):
        R_rel = rotation_about_axis(d, angle)
        signed, mis = signed_roll_about_direction(R_rel, d)
        commanded = (angle + math.pi) % (2.0 * math.pi) - math.pi
        assert abs(((signed - commanded + math.pi) % (2.0 * math.pi)) - math.pi) < 1e-10
        assert mis < 1e-10


def test_central_difference_matches_analytical_interior() -> None:
    fixture = make_off_axis_fixture(transverse_offset_m=0.04)
    q6 = 0.37
    state = fixture.evaluate(q6)
    dp_fd, dd_fd = central_difference_derivatives(fixture, q6, h=1e-6)
    assert float(np.linalg.norm(dp_fd - state.dp_dq6)) < 1e-8
    assert float(np.linalg.norm(dd_fd - state.dd_dq6)) < 1e-8


def test_fd_refinement_converges() -> None:
    result, rows = evaluate_fd_refinement()
    assert result.status == "PASS"
    assert fd_converges(rows)
    assert rows[0].dp_error > rows[2].dp_error or rows[2].dp_error < 1e-10


def test_aligned_fd_errors_near_zero() -> None:
    rows = finite_difference_refinement(make_aligned_fixture(), q6=0.4)
    assert all(r.dp_error < 1e-10 and r.dd_error < 1e-10 for r in rows)


def test_sweep_series_shapes() -> None:
    metrics, series = sweep_residuals(make_combined_violation_fixture(), experiment_id="TEST", n_samples=17)
    assert len(series["q6"]) == 17
    assert metrics.experiment_id == "TEST"
