"""Tests for exact axis regrouping without closed-mechanism overclaim."""

from __future__ import annotations

import json

from grashof_workspace.spatial_experiments.axis_aggregation import (
    ORTHOGONALITY_DOT_TOL,
    PAIR_DISTANCE_TOL_M,
    assess_consecutive_pair,
    build_aggregated_mechanism,
    detect_exact_u_pairs,
    fk_identity_residuals,
)
from grashof_workspace.spatial_experiments.decomposition_certificate import (
    issue_axis_aggregation_certificate,
)
from grashof_workspace.spatial_experiments.v05_corpus import (
    build_exact_u_pair_4r,
    build_generic_4r,
)
from grashof_workspace.spatial_experiments.v05d import build_v05d_readout, render_v05d_html


def test_exact_u_pair_gets_axis_certificate_not_loop_certificate() -> None:
    entry = build_exact_u_pair_4r()
    candidates = detect_exact_u_pairs(entry.model)
    assert candidates[0].exact_u_candidate
    assert candidates[0].distance_m <= PAIR_DISTANCE_TOL_M
    assert candidates[0].orthogonality_abs_dot <= ORTHOGONALITY_DOT_TOL

    aggregated = build_aggregated_mechanism(entry.model, candidates[0])
    assert aggregated.family_label == "S_v-U_phys-R-R"
    assert aggregated.joint_role_sequence == ("S_v", "U_phys", "R_phys", "R_phys")
    diagnostics = fk_identity_residuals(aggregated, entry.regular_q)
    assert max(diagnostics.values()) <= 1e-12

    certificate = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    assert certificate.axis_aggregation_status == "EXACT_GLOBAL"
    assert certificate.closed_mechanism_status == "UNRESOLVED"
    assert certificate.status == "UNRESOLVED"
    assert certificate.designated_task_joint_role == "tool_frame"
    assert certificate.tangent_subspace_error is None
    assert certificate.trajectory_position_error_m is None
    assert certificate.component_correspondence == "not_evaluated_with_independent_reduced_mechanism"
    assert not certificate.evidence["independent_reduced_solve_present"]


def test_generic_4r_rejects_exact_u_aggregation() -> None:
    entry = build_generic_4r()
    assert all(not candidate.exact_u_candidate for candidate in detect_exact_u_pairs(entry.model))
    certificate = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    assert certificate.axis_aggregation_status == "REJECTED"
    assert certificate.status == "REJECTED"
    assert certificate.aggregated is None


def test_tolerance_inputs_are_validated() -> None:
    entry = build_exact_u_pair_4r()
    for kwargs in (
        {"distance_tol_m": -1.0},
        {"orthogonality_tol": -1.0},
        {"parallel_tol": -1.0},
        {"orthogonality_tol": 1.1},
        {"parallel_tol": 1.1},
    ):
        try:
            assess_consecutive_pair(entry.model.chain, 0, **kwargs)
            raised = False
        except ValueError:
            raised = True
        assert raised


def test_certificate_serialization_is_strict_json() -> None:
    exact = build_exact_u_pair_4r()
    generic = build_generic_4r()
    payload = {
        "exact": issue_axis_aggregation_certificate(exact.model, exact.regular_q).to_json_dict(),
        "generic": issue_axis_aggregation_certificate(generic.model, generic.regular_q).to_json_dict(),
    }
    encoded = json.dumps(payload, allow_nan=False)
    assert "NaN" not in encoded
    assert "Infinity" not in encoded


def test_v05d_html_and_readout(tmp_path) -> None:
    certificates = build_v05d_readout(tmp_path)
    by_id = {certificate.source_chain_id: certificate for certificate in certificates}
    assert by_id["exact_u_pair_4r"].axis_aggregation_status == "EXACT_GLOBAL"
    assert by_id["exact_u_pair_4r"].closed_mechanism_status == "LOCAL_ONLY"
    assert by_id["generic_4r"].status == "REJECTED"
    html = render_v05d_html(certificates, figures={"demo": "figures/demo.png"})
    assert "different claims" in html or "Independent traced-arc match" in html
    assert (tmp_path / "data" / "v05d_axis_aggregation.json").exists()
    assert (tmp_path / "sprint_v05d_axis_aggregation.html").exists()
