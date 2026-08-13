"""Tests for the V05 independent S_v-U_phys-R-R closed-mechanism gate."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.axis_aggregation import (
    build_aggregated_mechanism,
    detect_exact_u_pairs,
)
from grashof_workspace.spatial_experiments.closed_mechanism_compare import (
    compare_independent_closed_mechanism,
    forged_identity_comparison,
)
from grashof_workspace.spatial_experiments.closed_mechanism_sv_uphys import (
    build_independent_sv_uphys_rr,
)
from grashof_workspace.spatial_experiments.decomposition_certificate import (
    issue_axis_aggregation_certificate,
    issue_closed_mechanism_certificate,
)
from grashof_workspace.spatial_experiments.v05_corpus import (
    build_exact_u_pair_4r,
    build_generic_4r,
)
from grashof_workspace.spatial_experiments.v05d import build_v05d_readout


def test_independent_geometry_is_distinct_from_source_chain() -> None:
    entry = build_exact_u_pair_4r()
    candidate = next(c for c in detect_exact_u_pairs(entry.model) if c.exact_u_candidate)
    aggregated = build_aggregated_mechanism(entry.model, candidate)
    mechanism = build_independent_sv_uphys_rr(entry.model, aggregated, entry.regular_q)
    assert mechanism.geometry_object_id != mechanism.source_chain_object_id
    assert id(mechanism.geometry) != id(entry.model.chain)
    assert id(mechanism.geometry) != id(aggregated.chain)
    assert mechanism.provenance == "source_derived"
    assert mechanism.joint_role_sequence_solver[0] == "U_phys"
    assert mechanism.semantic_origin_role == "S_v"
    assert "U_v" not in mechanism.joint_role_sequence_solver


def test_aggregation_only_path_remains_unresolved_for_closed_mechanism() -> None:
    entry = build_exact_u_pair_4r()
    certificate = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    assert certificate.axis_aggregation_status == "EXACT_GLOBAL"
    assert certificate.closed_mechanism_status == "UNRESOLVED"
    assert certificate.status == "UNRESOLVED"
    assert not certificate.evidence["independent_reduced_solve_present"]


def test_independent_solve_promotes_exact_on_component() -> None:
    entry = build_exact_u_pair_4r()
    aggregation = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    candidate = next(c for c in detect_exact_u_pairs(entry.model) if c.exact_u_candidate)
    aggregated = build_aggregated_mechanism(entry.model, candidate)
    mechanism = build_independent_sv_uphys_rr(entry.model, aggregated, entry.regular_q)
    comparison = compare_independent_closed_mechanism(entry.model, mechanism)
    assert comparison.accepted
    assert comparison.independent_reduced_solve_present
    assert comparison.comparison_mode == "independent_closed_loop"
    assert comparison.max_position_error_m <= 1e-9
    assert comparison.seed_tangent_misalignment <= 1e-6

    certificate = issue_closed_mechanism_certificate(aggregation, comparison)
    assert certificate.axis_aggregation_status == "EXACT_GLOBAL"
    assert certificate.closed_mechanism_status == "EXACT_ON_COMPONENT"
    assert certificate.status == "EXACT_ON_COMPONENT"
    assert certificate.evidence["independent_reduced_solve_present"]
    assert certificate.component_correspondence.startswith("exact_on_component:")
    assert certificate.trajectory_position_error_m is not None
    assert certificate.tangent_subspace_error is not None


def test_forged_identity_comparison_cannot_promote() -> None:
    entry = build_exact_u_pair_4r()
    aggregation = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    candidate = next(c for c in detect_exact_u_pairs(entry.model) if c.exact_u_candidate)
    aggregated = build_aggregated_mechanism(entry.model, candidate)
    mechanism = build_independent_sv_uphys_rr(entry.model, aggregated, entry.regular_q)
    forged = forged_identity_comparison(mechanism)
    certificate = issue_closed_mechanism_certificate(aggregation, forged)
    assert certificate.closed_mechanism_status == "UNRESOLVED"
    assert certificate.status == "UNRESOLVED"
    assert not certificate.evidence["independent_reduced_solve_present"]
    assert "identity" in certificate.failure_or_scope_reason.lower()


def test_generic_corpus_does_not_promote_closed_mechanism() -> None:
    entry = build_generic_4r()
    certificate = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    assert certificate.axis_aggregation_status == "REJECTED"
    assert certificate.closed_mechanism_status == "UNRESOLVED"


def test_v05d_readout_reports_scoped_closed_gate(tmp_path) -> None:
    certificates = build_v05d_readout(tmp_path)
    by_id = {certificate.source_chain_id: certificate for certificate in certificates}
    assert by_id["exact_u_pair_4r"].closed_mechanism_status == "EXACT_ON_COMPONENT"
    assert by_id["exact_u_pair_4r"].status == "EXACT_ON_COMPONENT"
    assert by_id["generic_4r"].status == "REJECTED"
    html = (tmp_path / "sprint_v05d_axis_aggregation.html").read_text(encoding="utf-8")
    assert "Scoped gate closed" in html or "EXACT_ON_COMPONENT" in html
    payload = (tmp_path / "data" / "v05d_axis_aggregation.json").read_text(encoding="utf-8")
    assert "CLOSED_ON_COMPONENT_EXACT_U_PAIR" in payload
    assert (tmp_path / "figures" / "v05d_exact_u_pair_4r_source_reduced_overlay.png").exists()
