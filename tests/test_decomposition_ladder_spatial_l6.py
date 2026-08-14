"""L6 scaffold interface: empty children and UNRESOLVED reconstruction."""

from __future__ import annotations

from grashof_workspace.decomposition_ladder.models import (
    CertificateStatus,
    LadderRung,
    ProcessStatus,
)
from grashof_workspace.decomposition_ladder.registry import DEFAULT_FIBER_SPECS, rung_spec
from grashof_workspace.decomposition_ladder.spatial_l6 import (
    build_spatial_l6_scaffold_bundle,
    default_l6_scaffold_payload,
)


def test_l6_process_promoted_scaffold_certificates_unresolved() -> None:
    assert rung_spec(LadderRung.L6).process_status is ProcessStatus.SCAFFOLD
    fiber = next(spec for spec in DEFAULT_FIBER_SPECS if spec.rung is LadderRung.L6)
    assert fiber.process_status is ProcessStatus.SCAFFOLD
    assert fiber.certificate_status is CertificateStatus.UNRESOLVED


def test_l6_bundle_shapes_empty_children() -> None:
    bundle = build_spatial_l6_scaffold_bundle()
    assert bundle.architecture_id == "generic_6r"
    assert bundle.parent.rung is LadderRung.L6
    assert bundle.parent.dimension == 3
    assert bundle.parent.target_space == "SO(3)"
    assert bundle.parent.process_status is ProcessStatus.SCAFFOLD
    assert "UNRESOLVED" in " ".join(bundle.parent.notes)
    assert "frozen" in " ".join(bundle.parent.notes).casefold()

    assert bundle.fiber_placeholder.sample_count == 0
    assert bundle.fiber_placeholder.source_provenance == "scaffold_only"
    assert bundle.seed_audit["rank_jp"] == 3
    assert bundle.seed_audit["nullity_jp"] == 3
    assert bundle.seed_audit["status"] == "PASS"

    assert bundle.children == ()
    assert bundle.certificates == ()


def test_l6_reconstruction_empty_no_so3_claim() -> None:
    bundle = build_spatial_l6_scaffold_bundle()
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.fiber_placeholder.fiber_id in bundle.reconstruction.unresolved_fiber_ids
    assert bundle.reconstruction.certificate_status is CertificateStatus.UNRESOLVED
    assert bundle.reconstruction.process_status is ProcessStatus.SCAFFOLD
    notes = " ".join(bundle.reconstruction.notes).casefold()
    assert "gate k3" in notes or "adr-013" in notes
    assert "adr-024" in notes
    assert "adr-026" in notes
    assert "v08" in notes

    payload = default_l6_scaffold_payload()
    assert payload["summary"]["seed_nullity_jp"] == 3
    assert payload["summary"]["child_count"] == 0
    assert payload["summary"]["accepted_fiber_count"] == 0
    assert payload["summary"]["reconstruction_status"] == "UNRESOLVED"
    assert payload["summary"]["target_space"] == "SO(3)"
    assert "frozen so(3)" in payload["note"].casefold()
    assert "not v08" in payload["note"].casefold()
