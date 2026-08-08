"""Interior, exterior, and boundary tests for active V05C orientation-curve truth."""

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
from grashof_workspace.spatial_experiments.v05_corpus import build_generic_4r, build_singular_4r
from grashof_workspace.spatial_experiments.v05c import build_v05c_readout, render_v05c_html


def test_interior_generic_orientation_image_has_samples() -> None:
    entry = build_generic_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=12, step_size=0.05)
    orientation = build_orientation_image(fiber, chain=entry.model)
    pointing = build_pointing_image(fiber)
    assert orientation.status == "PASS"
    assert len(orientation.samples) >= 5
    assert pointing.status == "PASS"
    assert len(pointing.points) == len(orientation.samples)
    for sample in orientation.samples:
        q = np.asarray(sample.quaternion, dtype=float)
        assert abs(float(np.linalg.norm(q)) - 1.0) < 1e-9
        assert np.all(np.isfinite(sample.rotvec))
        d = np.asarray(sample.d, dtype=float)
        assert abs(float(np.linalg.norm(d)) - 1.0) < 1e-9


def test_exterior_singular_has_no_orientation_curve() -> None:
    entry = build_singular_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=8)
    orientation = build_orientation_image(fiber, chain=entry.model)
    pointing = build_pointing_image(fiber)
    assert orientation.status == "FAIL"
    assert orientation.samples == ()
    assert pointing.status == "FAIL"
    assert pointing.points == ()


def test_boundary_quaternion_round_trip_and_sign_stability() -> None:
    entry = build_generic_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=10, step_size=0.05)
    orientation = build_orientation_image(fiber, chain=entry.model)
    assert orientation.samples
    prev = None
    for sample in orientation.samples:
        R = np.asarray(sample.R, dtype=float)
        q = rotation_matrix_to_quaternion(R)
        R_back = quaternion_to_rotation_matrix(q)
        assert float(np.linalg.norm(R - R_back)) < 1e-9
        rotvec = rotation_matrix_to_rotvec(R)
        assert np.all(np.isfinite(rotvec))
        cur = np.asarray(sample.quaternion, dtype=float)
        if prev is not None:
            assert float(np.dot(prev, cur)) >= -1e-12
        prev = cur
        if sample.rank_jp < 3 or not sample.regular:
            assert sample.near_singular


def test_v05c_html_and_readout(tmp_path) -> None:
    rows = build_v05c_readout(tmp_path, n_steps=10, step_size=0.05)
    assert len(rows) == 4
    assert any(o.status == "PASS" for o, _ in rows)
    assert any(o.status == "FAIL" for o, _ in rows)
    html = render_v05c_html(rows, figures={"demo": "figures/demo.png"})
    assert "orientation-curve" in html.casefold()
    assert "not coverage" in html.casefold()
    assert "single scalar angle" in html.casefold() or "not a" in html.casefold()
    assert (tmp_path / "data" / "v05c_orientation_curves.json").is_file()
    assert (tmp_path / "sprint_v05c_orientation_curve.html").is_file()
