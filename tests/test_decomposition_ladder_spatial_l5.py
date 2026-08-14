"""L5 scaffold interface: UNRESOLVED certificates and empty reconstruction."""

from __future__ import annotations

from grashof_workspace.decomposition_ladder.models import (
    CertificateStatus,
    LadderRung,
    ProcessStatus,
)
from grashof_workspace.decomposition_ladder.registry import (
    DEFAULT_FIBER_SPECS,
    PARENT_CHILD_FAMILIES,
    rung_spec,
)
from grashof_workspace.decomposition_ladder.spatial_l5 import (
    build_spatial_l5_scaffold_bundle,
    default_l5_scaffold_payload,
)


def test_l5_process_promoted_scaffold_certificates_unresolved() -> None:
    assert rung_spec(LadderRung.L5).process_status is ProcessStatus.SCAFFOLD
    fiber = next(spec for spec in DEFAULT_FIBER_SPECS if spec.rung is LadderRung.L5)
    assert fiber.process_status is ProcessStatus.SCAFFOLD
    assert fiber.certificate_status is CertificateStatus.UNRESOLVED


def test_l5_bundle_shapes_and_unresolved_families() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.architecture_id == "generic_5r"
    assert bundle.parent.rung is LadderRung.L5
    assert bundle.parent.dimension == 2
    assert bundle.parent.target_space == "S^2"
    assert bundle.parent.process_status is ProcessStatus.SCAFFOLD
    assert "UNRESOLVED" in " ".join(bundle.parent.notes)

    assert bundle.fiber_placeholder.sample_count >= 0
    assert bundle.fiber_placeholder.source_provenance in {"task-derived", "scaffold_only"}
    if bundle.fiber_placeholder.source_provenance == "task-derived":
        assert bundle.fiber_placeholder.sample_count > 0
        assert "U_v" not in bundle.fiber_placeholder.fiber_id
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.seed_audit["rank_jp"] == 3
    assert bundle.seed_audit["nullity_jp"] == 2
    assert bundle.seed_audit["status"] == "PASS"

    assert len(bundle.children) == len(PARENT_CHILD_FAMILIES)
    assert len(bundle.certificates) == len(bundle.children)
    for child, cert in zip(bundle.children, bundle.certificates, strict=True):
        assert child.joint_role_sequence[0] == "U_v"
        assert "source_chain_evidence" not in child.geometry_provenance
        assert "source_chain_evidence" in " ".join(child.notes).casefold()
        assert not cert.accepted_for_reconstruction
        if child.family == "UUUR":
            assert child.status not in {
                CertificateStatus.EXACT_GLOBAL,
                CertificateStatus.EXACT_ON_COMPONENT,
            }
            assert child.joint_role_sequence == ("U_v", "U_phys", "U_phys", "R_phys")
        else:
            assert child.status is CertificateStatus.UNRESOLVED
            assert child.geometry_provenance == "candidate_corpus_only"
            assert cert.closed_mechanism_status is CertificateStatus.UNRESOLVED


def test_l5_reconstruction_empty_and_no_u_v_source_promotion() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.fiber_placeholder.fiber_id in bundle.reconstruction.unresolved_fiber_ids
    assert bundle.reconstruction.certificate_status is CertificateStatus.UNRESOLVED
    assert bundle.reconstruction.process_status is ProcessStatus.SCAFFOLD
    notes = " ".join(bundle.reconstruction.notes).casefold()
    assert "gate k2" in notes or "adr-024" in notes
    assert "adr-026" in notes

    payload = default_l5_scaffold_payload()
    assert payload["summary"]["seed_nullity_jp"] == 2
    assert payload["summary"]["accepted_fiber_count"] == 0
    assert payload["summary"]["reconstruction_status"] == "UNRESOLVED"
    assert "not a 2d parent" in payload["note"].casefold()
    assert "pointing-image reconstruction" in payload["note"].casefold()
