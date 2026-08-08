"""Interior, exterior, and boundary tests for active V05E near-aligned rejection."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.axis_aggregation import (
    ORTHOGONALITY_DOT_TOL,
    PAIR_DISTANCE_TOL_M,
    detect_exact_u_pairs,
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


def test_interior_exact_control_still_certifies() -> None:
    entry = build_exact_u_pair_4r()
    cert = issue_axis_aggregation_certificate(entry.model, entry.regular_q, n_fiber_steps=10)
    assert cert.status in {"EXACT_ON_COMPONENT", "EXACT_GLOBAL"}
    assert cert.aggregated is not None
    assert "U_phys" in cert.joint_role_sequence
    assert "U_v" not in cert.joint_role_sequence


def test_exterior_near_aligned_rejected() -> None:
    entry = build_near_aligned_u_pair_4r()
    candidates = detect_exact_u_pairs(entry.model)
    assert all(not c.exact_u_candidate for c in candidates)
    cert = issue_axis_aggregation_certificate(entry.model, entry.regular_q, n_fiber_steps=8)
    assert cert.status == "REJECTED"
    assert cert.aggregated is None
    assert candidates[0].distance_m > PAIR_DISTANCE_TOL_M
    assert candidates[0].orthogonality_abs_dot > ORTHOGONALITY_DOT_TOL


def test_boundary_false_u_task_error_visible() -> None:
    near = build_near_aligned_u_pair_4r()
    exact = build_exact_u_pair_4r()
    near_report = measure_false_u_task_error(near.model, near.regular_q, n_fiber_steps=10)
    exact_report = measure_false_u_task_error(exact.model, exact.regular_q, n_fiber_steps=10)
    assert near_report.exceeds_distance_tol
    assert near_report.exceeds_orthogonality_tol
    assert near_report.seed_position_residual_m > exact_report.seed_position_residual_m
    assert near_report.fiber_max_position_residual_m > exact_report.fiber_max_position_residual_m
    assert near_report.label == "false_u_surrogate"


def test_corpus_includes_near_aligned() -> None:
    ids = [e.model.architecture_id for e in v05a_spatial_4r_corpus()]
    assert ids == [
        "generic_4r",
        "exact_u_pair_4r",
        "near_aligned_u_pair_4r",
        "singular_4r_parallel",
    ]


def test_v05e_html_and_readout(tmp_path) -> None:
    rows = build_v05e_readout(tmp_path, n_fiber_steps=8, fiber_step_size=0.05)
    assert len(rows) == 3
    by_id = {c.source_chain_id: (c, r) for c, r in rows}
    assert by_id["near_aligned_u_pair_4r"][0].status == "REJECTED"
    assert by_id["near_aligned_u_pair_4r"][1] is not None
    assert by_id["exact_u_pair_4r"][0].status in {"EXACT_ON_COMPONENT", "EXACT_GLOBAL"}
    html = render_v05e_html(rows, figures={"demo": "figures/demo.png"})
    assert "geometric" in html.casefold() or "tolerance" in html.casefold()
    assert "false" in html.casefold() and "task error" in html.casefold()
    assert "DecompositionCertificate" in html
    assert (tmp_path / "data" / "v05e_near_aligned_rejection.json").exists()
    assert (tmp_path / "sprint_v05e_near_aligned_rejection.html").exists()
