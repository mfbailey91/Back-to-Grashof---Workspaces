"""Interior, exterior, and boundary tests for active V05D axis aggregation."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.axis_aggregation import (
    ORTHOGONALITY_DOT_TOL,
    PAIR_DISTANCE_TOL_M,
    assess_consecutive_pair,
    build_aggregated_mechanism,
    detect_exact_u_pairs,
    fk_identity_residuals,
)
from grashof_workspace.spatial_experiments.decomposition_certificate import (
    TANGENT_AGREEMENT_TOL,
    issue_axis_aggregation_certificate,
)
from grashof_workspace.spatial_experiments.v05_corpus import (
    build_exact_u_pair_4r,
    build_generic_4r,
)
from grashof_workspace.spatial_experiments.v05d import build_v05d_readout, render_v05d_html


def test_interior_exact_u_pair_detects_proximal_and_certifies() -> None:
    entry = build_exact_u_pair_4r()
    candidates = detect_exact_u_pairs(entry.model)
    assert candidates[0].exact_u_candidate
    assert candidates[0].pair_index == 0
    assert candidates[0].distance_m <= PAIR_DISTANCE_TOL_M
    assert candidates[0].orthogonality_abs_dot <= ORTHOGONALITY_DOT_TOL

    agg = build_aggregated_mechanism(entry.model, candidates[0])
    assert agg.family_label == "S_v-U_phys-R-R"
    assert agg.joint_kind_sequence == ("S_v", "U", "R", "R")
    assert agg.joint_role_sequence == ("S_v", "U_phys", "R_phys", "R_phys")
    assert "U_v" not in agg.joint_role_sequence
    assert "tool_a" not in agg.joint_role_sequence

    fk = fk_identity_residuals(agg, entry.regular_q)
    assert fk["position_residual_m"] <= 1e-12
    assert fk["rotation_frobenius"] <= 1e-12
    assert fk["joint_map_residual"] <= 1e-12

    cert = issue_axis_aggregation_certificate(entry.model, entry.regular_q, n_fiber_steps=12)
    assert cert.status in {"EXACT_ON_COMPONENT", "EXACT_GLOBAL"}
    assert cert.reduction_operations == ("axis_aggregation",)
    assert cert.aggregated is not None
    assert cert.tangent_subspace_error <= TANGENT_AGREEMENT_TOL


def test_exterior_generic_4r_rejected_no_false_u() -> None:
    entry = build_generic_4r()
    candidates = detect_exact_u_pairs(entry.model)
    assert all(not c.exact_u_candidate for c in candidates)
    cert = issue_axis_aggregation_certificate(entry.model, entry.regular_q, n_fiber_steps=8)
    assert cert.status == "REJECTED"
    assert cert.aggregated is None
    assert "No consecutive exact" in cert.failure_or_scope_reason


def test_boundary_tolerance_edge_and_roles() -> None:
    entry = build_exact_u_pair_4r()
    # At default tol the planted pair is exact.
    ok = assess_consecutive_pair(entry.model.chain, 0)
    assert ok.exact_u_candidate
    # Tighten orthogonality below the planted residual → reject (boundary exterior).
    # Planted |dot| is ~0; use a zero-width orthogonality window that still requires
    # non-parallel axes, then a distance that is just below the planted distance+eps.
    tight = assess_consecutive_pair(
        entry.model.chain,
        0,
        distance_tol_m=0.0,
        orthogonality_tol=-1.0,
    )
    # Negative orthogonality tol cannot be satisfied for |dot|>=0.
    assert not tight.exact_orthogonal
    assert not tight.exact_u_candidate

    # Distance just outside planted exact (generic first pair is skew).
    generic = build_generic_4r()
    g0 = assess_consecutive_pair(generic.model.chain, 0)
    assert g0.distance_m > PAIR_DISTANCE_TOL_M
    edge = assess_consecutive_pair(
        generic.model.chain,
        0,
        distance_tol_m=g0.distance_m * 0.5,
    )
    assert not edge.exact_intersecting

    cert = issue_axis_aggregation_certificate(entry.model, entry.regular_q, n_fiber_steps=10)
    assert cert.aggregated is not None
    assert "S_v" in cert.joint_role_sequence
    assert "U_phys" in cert.joint_role_sequence
    assert cert.tangent_subspace_error <= TANGENT_AGREEMENT_TOL


def test_v05d_html_and_readout(tmp_path) -> None:
    certs = build_v05d_readout(tmp_path, n_fiber_steps=10, fiber_step_size=0.05)
    assert len(certs) == 2
    statuses = {c.source_chain_id: c.status for c in certs}
    assert statuses["exact_u_pair_4r"] in {"EXACT_ON_COMPONENT", "EXACT_GLOBAL"}
    assert statuses["generic_4r"] == "REJECTED"
    html = render_v05d_html(certs, figures={"demo": "figures/demo.png"})
    assert "DecompositionCertificate" in html
    assert "S_v-U_phys-R-R" in html
    assert (tmp_path / "data" / "v05d_axis_aggregation.json").exists()
    assert (tmp_path / "sprint_v05d_axis_aggregation.html").exists()
