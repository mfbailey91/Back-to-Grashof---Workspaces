"""Tests for V05E exact rejection, tolerance boundaries, and false-U diagnostics."""

from __future__ import annotations

import json

from grashof_workspace.spatial_experiments.axis_aggregation import (
    evaluate_u_boundary_suite,
    measure_false_u_task_error,
)
from grashof_workspace.spatial_experiments.decomposition_certificate import (
    issue_axis_aggregation_certificate,
)
from grashof_workspace.spatial_experiments.v05_corpus import (
    build_exact_u_pair_4r,
    build_near_aligned_u_pair_4r,
    v05a_spatial_4r_corpus,
)
from grashof_workspace.spatial_experiments.v05e import build_v05e_readout, render_v05e_html


def test_exact_control_has_exact_axis_aggregation_only() -> None:
    entry = build_exact_u_pair_4r()
    certificate = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    assert certificate.axis_aggregation_status == "EXACT_GLOBAL"
    assert certificate.closed_mechanism_status == "UNRESOLVED"
    assert certificate.status == "UNRESOLVED"
    assert "U_phys" in certificate.joint_role_sequence
    assert certificate.designated_task_joint_role == "tool_frame"


def test_near_aligned_exterior_is_rejected() -> None:
    entry = build_near_aligned_u_pair_4r()
    certificate = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    assert certificate.axis_aggregation_status == "REJECTED"
    assert certificate.status == "REJECTED"
    assert certificate.aggregated is None


def test_tolerance_relative_boundary_suite() -> None:
    exact = build_exact_u_pair_4r()
    cases = evaluate_u_boundary_suite(exact.model)
    assert len(cases) == 25
    for case in cases:
        should_accept = case.distance_scale <= 1.0 and case.orthogonality_scale <= 1.0
        assert case.accepted is should_accept
        if should_accept:
            assert case.measured_distance_m <= 1.000001 * case.target_distance_m + 1e-18 or case.distance_scale == 0.0


def test_false_u_error_is_measured_over_nontrivial_source_motion() -> None:
    near = build_near_aligned_u_pair_4r()
    report = measure_false_u_task_error(near.model, near.regular_q, n_fiber_steps=12, fiber_step_size=0.03)
    assert report.label == "false_u_surrogate"
    assert report.comparison_mode == "same_source_coordinates_not_independent_surrogate_solve"
    assert report.exceeds_distance_tol
    assert report.exceeds_orthogonality_tol
    assert report.fiber_samples_compared >= 5
    assert report.fiber_max_position_residual_m >= report.seed_position_residual_m
    assert report.fiber_max_rotation_frobenius >= report.seed_rotation_frobenius
    assert report.fiber_max_pointing_residual >= report.seed_pointing_residual


def test_corpus_contains_nontrivial_sources_and_terminal_roll_control() -> None:
    entries = v05a_spatial_4r_corpus()
    ids = [entry.model.architecture_id for entry in entries]
    assert ids == [
        "generic_4r",
        "terminal_roll_control_4r",
        "exact_u_pair_4r",
        "near_aligned_u_pair_4r",
        "singular_4r_parallel",
    ]
    by_id = {entry.model.architecture_id: entry for entry in entries}
    assert by_id["generic_4r"].terminal_axis_offset_m > 0.0
    assert by_id["terminal_roll_control_4r"].terminal_axis_offset_m <= 1e-12


def test_v05e_html_readout_and_strict_json(tmp_path) -> None:
    rows = build_v05e_readout(tmp_path, n_fiber_steps=8, fiber_step_size=0.03)
    by_id = {certificate.source_chain_id: (certificate, report) for certificate, report in rows}
    assert by_id["near_aligned_u_pair_4r"][0].status == "REJECTED"
    assert by_id["near_aligned_u_pair_4r"][1] is not None
    assert by_id["exact_u_pair_4r"][0].axis_aggregation_status == "EXACT_GLOBAL"
    html = render_v05e_html(rows, evaluate_u_boundary_suite(build_exact_u_pair_4r().model), figures={})
    assert "tolerance-relative" in html
    assert "diagnostic only" in html
    data_path = tmp_path / "data" / "v05e_near_aligned_rejection.json"
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    assert payload["tolerance_boundary_cases"]
    assert (tmp_path / "sprint_v05e_near_aligned_rejection.html").exists()
