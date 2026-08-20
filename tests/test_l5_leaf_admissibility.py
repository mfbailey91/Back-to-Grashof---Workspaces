"""Leaf-scoped family admission and local vs component reseed classification."""

from __future__ import annotations

from dataclasses import replace

from l5_test_support import two_neighbor_works as _two_neighbor_works

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    chart_audits_by_leaf,
    classify_reseed_attempt,
    recompute_family_acceptance,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    ChartOverlapAudit,
    FamilyAdmissibilityStatus,
    ReseedAudit,
    ReseedDisposition,
    ReseedScope,
    TransversalityAudit,
)


def test_component_pass_requires_symmetric_branch_distances() -> None:
    scope, disposition, _ret, _branch, identity, notes = classify_reseed_attempt(
        lambda_ok=True,
        seed_q_ok=True,
        seed_pointing_ok=True,
        tangent_ok=True,
        original_returned=True,
        reseeded_returned=True,
        original_branch_status="returned",
        reseeded_branch_status="returned",
        symmetric_q=0.5,
        symmetric_p=0.0,
        q_tol=1e-3,
        p_tol=1e-3,
    )
    assert disposition is ReseedDisposition.LOCAL_PASS
    assert disposition is not ReseedDisposition.COMPONENT_PASS
    assert scope is ReseedScope.LOCAL
    assert identity is False
    assert any("symmetric" in note.lower() or "local pass" in note.lower() for note in notes)


def test_return_mismatch_blocks_component_pass() -> None:
    _scope, disposition, returned_match, _branch, identity, _notes = classify_reseed_attempt(
        lambda_ok=True,
        seed_q_ok=True,
        seed_pointing_ok=True,
        tangent_ok=True,
        original_returned=True,
        reseeded_returned=False,
        original_branch_status="returned",
        reseeded_branch_status="open",
        symmetric_q=0.0,
        symmetric_p=0.0,
        q_tol=1e-3,
        p_tol=1e-3,
    )
    assert returned_match is False
    assert disposition is ReseedDisposition.LOCAL_PASS
    assert disposition is not ReseedDisposition.COMPONENT_PASS
    assert identity is False


def test_returned_symmetric_match_is_component_pass() -> None:
    scope, disposition, returned_match, branch_match, set_match, notes = classify_reseed_attempt(
        lambda_ok=True,
        seed_q_ok=True,
        seed_pointing_ok=True,
        tangent_ok=True,
        original_returned=True,
        reseeded_returned=True,
        original_branch_status="returned",
        reseeded_branch_status="returned",
        symmetric_q=0.0,
        symmetric_p=0.0,
        q_tol=1e-3,
        p_tol=1e-3,
    )
    assert scope is ReseedScope.COMPONENT
    assert disposition is ReseedDisposition.COMPONENT_PASS
    assert returned_match is True
    assert branch_match is True
    assert set_match is True
    assert all("circuit identity" not in note.lower() for note in notes)


def _component_reseed() -> ReseedAudit:
    return ReseedAudit(
        disposition=ReseedDisposition.COMPONENT_PASS,
        n_reseeds=3,
        max_symmetric_q_distance_rad=0.0,
        max_pointing_distance_rad=0.0,
        notes=("synthetic component pass",),
    )


def test_leaf_only_inherits_incident_neighbor_audits() -> None:
    work_a, work_b = _two_neighbor_works()
    spec_c = replace(work_a.certificate.spec, leaf_id="leaf_c")
    cert_a = replace(work_a.certificate, reseed=_component_reseed())
    cert_b = replace(work_b.certificate, reseed=_component_reseed())
    cert_c = replace(work_a.certificate, spec=spec_c, reseed=_component_reseed())
    pass_ab = TransversalityAudit(
        status="PASS",
        sigma_min=0.4,
        rank_span=2,
        notes=("synthetic pass",),
        leaf_id_a=cert_a.spec.leaf_id,
        leaf_id_b=cert_b.spec.leaf_id,
    )
    fail_bc = TransversalityAudit(
        status="FAIL",
        sigma_min=1e-12,
        rank_span=1,
        notes=("synthetic fail",),
        leaf_id_a=cert_b.spec.leaf_id,
        leaf_id_b="leaf_c",
    )
    overlap = ChartOverlapAudit(
        status="COMPATIBLE",
        required=False,
        claim_scope="declared_chart_domain_only",
    )
    updated = recompute_family_acceptance((cert_a, cert_b, cert_c), (pass_ab, fail_bc), overlap)
    by_id = {leaf.spec.leaf_id: leaf for leaf in updated}
    assert by_id[cert_a.spec.leaf_id].family_admissibility_status is not FamilyAdmissibilityStatus.FAIL
    assert by_id[cert_b.spec.leaf_id].family_admissibility_status is FamilyAdmissibilityStatus.FAIL
    assert by_id["leaf_c"].family_admissibility_status is FamilyAdmissibilityStatus.FAIL
    assert by_id[cert_a.spec.leaf_id].accepted_for_reconstruction is False
    assert by_id[cert_b.spec.leaf_id].accepted_for_reconstruction is False


def test_unresolved_required_chart_overlap_blocks_leaf() -> None:
    work_a, work_b = _two_neighbor_works()
    cert_a = replace(work_a.certificate, reseed=_component_reseed())
    cert_b = replace(work_b.certificate, reseed=_component_reseed())
    pass_ab = TransversalityAudit(
        status="PASS",
        sigma_min=0.4,
        rank_span=2,
        notes=("synthetic pass",),
        leaf_id_a=cert_a.spec.leaf_id,
        leaf_id_b=cert_b.spec.leaf_id,
    )
    overlap = ChartOverlapAudit(
        status="UNRESOLVED",
        required=True,
        claim_scope="multi_chart_declared_domain",
        chart_id_a=work_a.chart.chart_id,
        chart_id_b=work_b.chart.chart_id,
    )
    updated = recompute_family_acceptance((cert_a, cert_b), (pass_ab,), overlap)
    assert all(leaf.family_admissibility_status is FamilyAdmissibilityStatus.UNRESOLVED for leaf in updated)
    assert all(leaf.accepted_for_reconstruction is False for leaf in updated)


def test_optional_chart_overlap_is_not_required() -> None:
    work_a, work_b = _two_neighbor_works()
    cert_a = replace(work_a.certificate, reseed=_component_reseed())
    cert_b = replace(work_b.certificate, reseed=_component_reseed())
    pass_ab = TransversalityAudit(
        status="PASS",
        sigma_min=0.4,
        rank_span=2,
        notes=("synthetic pass",),
        leaf_id_a=cert_a.spec.leaf_id,
        leaf_id_b=cert_b.spec.leaf_id,
    )
    overlap = ChartOverlapAudit(
        status="UNRESOLVED",
        required=False,
        claim_scope="declared_chart_domain_only",
        chart_id_a=work_a.chart.chart_id,
        chart_id_b=work_b.chart.chart_id,
    )
    updated = recompute_family_acceptance((cert_a, cert_b), (pass_ab,), overlap)
    assert all(
        leaf.family_admissibility_status is not FamilyAdmissibilityStatus.FAIL
        for leaf in updated
    )
    chart_ok_status = {leaf.chart_overlap_status for leaf in updated}
    assert "INCOMPATIBLE" not in chart_ok_status


def test_leaf_only_inherits_incident_chart_audits() -> None:
    work_a, work_b = _two_neighbor_works()
    spec_c = replace(work_a.certificate.spec, leaf_id="leaf_c")
    cert_c = replace(work_a.certificate, spec=spec_c)
    audit = ChartOverlapAudit(
        status="UNRESOLVED",
        required=True,
        claim_scope="multi_chart_declared_domain",
        chart_id_a=work_a.chart.chart_id,
        chart_id_b=work_b.chart.chart_id,
        leaf_id_a=work_a.certificate.spec.leaf_id,
        leaf_id_b=work_b.certificate.spec.leaf_id,
        responsibility_transition_id="synthetic-transition",
        transition_sample_count=2,
    )
    mapped = chart_audits_by_leaf(
        (work_a.certificate, work_b.certificate, cert_c),
        (audit,),
    )
    assert mapped[work_a.certificate.spec.leaf_id] == [audit]
    assert mapped[work_b.certificate.spec.leaf_id] == [audit]
    assert mapped["leaf_c"] == []


def test_chart_level_unresolved_attaches_only_to_affected_charts() -> None:
    work_a, work_b = _two_neighbor_works()
    world, rx90, ry90 = "ZYZ_WORLD", "ZYZ_RX90", "ZYZ_RY90"
    cert_a = replace(work_a.certificate, spec=replace(work_a.certificate.spec, chart_id=world))
    cert_b = replace(
        work_b.certificate,
        spec=replace(work_b.certificate.spec, chart_id=rx90),
    )
    cert_c = replace(
        work_a.certificate,
        spec=replace(work_a.certificate.spec, leaf_id="leaf_c", chart_id=ry90),
    )
    audit = ChartOverlapAudit(
        status="UNRESOLVED",
        required=True,
        claim_scope="multi_chart_declared_domain",
        chart_id_a=world,
        chart_id_b=rx90,
        responsibility_transition_id=f"{world}<->{rx90}",
        transition_sample_count=1,
    )
    mapped = chart_audits_by_leaf((cert_a, cert_b, cert_c), (audit,))
    assert mapped[cert_a.spec.leaf_id] == [audit]
    assert mapped[cert_b.spec.leaf_id] == [audit]
    assert mapped["leaf_c"] == []
