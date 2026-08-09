"""Tests for V05C orientation-curve truth and curve-type separation."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.fixed_position_continuation import (
    continue_fixed_position_fiber,
)
from grashof_workspace.spatial_experiments.orientation_image import (
    build_orientation_image,
    build_pointing_image,
    quaternion_to_rotation_matrix,
    rotation_matrix_to_quaternion,
    rotation_matrix_to_rotvec,
)
from grashof_workspace.spatial_experiments.v05_corpus import (
    build_generic_4r,
    build_singular_4r,
    build_terminal_roll_control_4r,
)
from grashof_workspace.spatial_experiments.v05c import build_v05c_readout, render_v05c_html


def test_generic_orientation_image_is_nontrivial_pointing_curve() -> None:
    entry = build_generic_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=14, step_size=0.03)
    orientation = build_orientation_image(fiber, chain=entry.model)
    pointing = build_pointing_image(fiber)
    assert orientation.status == "EXPORTED"
    assert orientation.curve_type in {
        "NONTRIVIAL_POINTING_CURVE",
        "FIXED_AXIS_ONE_PARAMETER_SUBGROUP",
    }
    assert orientation.metrics.orientation_path_length_rad > 1e-4
    assert orientation.metrics.pointing_path_length_rad > 1e-5
    assert pointing.status == "EXPORTED"
    assert pointing.path_length_rad > 1e-5
    assert len(pointing.points) == len(orientation.samples)


def test_terminal_roll_control_is_classified_separately() -> None:
    entry = build_terminal_roll_control_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=14, step_size=0.03)
    orientation = build_orientation_image(fiber, chain=entry.model)
    pointing = build_pointing_image(fiber)
    assert orientation.status == "EXPORTED"
    assert orientation.curve_type == "PURE_TERMINAL_ROLL"
    assert orientation.metrics.orientation_path_length_rad > 1e-4
    assert orientation.metrics.pointing_path_length_rad <= 1e-5
    assert pointing.path_length_rad <= 1e-5


def test_singular_has_no_orientation_curve() -> None:
    entry = build_singular_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=8)
    orientation = build_orientation_image(fiber, chain=entry.model)
    pointing = build_pointing_image(fiber)
    assert orientation.status == "FAIL"
    assert orientation.curve_type == "SINGULAR_OR_EMPTY"
    assert orientation.samples == ()
    assert pointing.status == "FAIL"
    assert pointing.points == ()


def test_quaternion_round_trip_and_sign_stability() -> None:
    entry = build_generic_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=10, step_size=0.03)
    orientation = build_orientation_image(fiber, chain=entry.model)
    assert orientation.samples
    previous = None
    for sample in orientation.samples:
        R = np.asarray(sample.R, dtype=float)
        quaternion = rotation_matrix_to_quaternion(R)
        R_back = quaternion_to_rotation_matrix(quaternion)
        assert float(np.linalg.norm(R - R_back)) < 1e-9
        assert np.all(np.isfinite(rotation_matrix_to_rotvec(R)))
        current = np.asarray(sample.quaternion, dtype=float)
        if previous is not None:
            assert float(np.dot(previous, current)) >= -1e-12
        previous = current


def test_v05c_html_and_readout(tmp_path) -> None:
    rows = build_v05c_readout(tmp_path, n_steps=8, step_size=0.03)
    assert len(rows) == 5
    by_id = {orientation.architecture_id: orientation for orientation, _pointing in rows}
    assert by_id["generic_4r"].status == "EXPORTED"
    assert by_id["terminal_roll_control_4r"].curve_type == "PURE_TERMINAL_ROLL"
    assert by_id["singular_4r_parallel"].status == "FAIL"
    html = render_v05c_html(rows, figures={"demo": "figures/demo.png"})
    assert "orientation-curve" in html.casefold()
    assert "not coverage" in html.casefold()
    assert (tmp_path / "data" / "v05c_orientation_curves.json").is_file()
    assert (tmp_path / "sprint_v05c_orientation_curve.html").is_file()
