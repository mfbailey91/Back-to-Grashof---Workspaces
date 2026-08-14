"""Integration checks for the L4 spatial-4R ladder adapter wrapping V05."""

from __future__ import annotations

from grashof_workspace.decomposition_ladder.models import (
    CertificateStatus,
    LadderRung,
    ProcessStatus,
)
from grashof_workspace.decomposition_ladder.registry import DEFAULT_FIBER_SPECS
from grashof_workspace.decomposition_ladder.spatial_l4 import (
    build_spatial_l4_exact_u_pair_bundle,
    build_spatial_l4_generic_bundle,
    default_l4_equivalence_payload,
    ladder_certificate_from_forged_identity,
)


def test_l4_exact_u_bundle_records_local_traced_arc_without_component_promotion() -> None:
    bundle = build_spatial_l4_exact_u_pair_bundle(n_steps=20)
    assert bundle.parent.rung is LadderRung.L4
    assert bundle.parent.process_status is ProcessStatus.SCAFFOLD
    assert bundle.parent.target_space == "Y1 ⊂ SO(3)"
    assert bundle.fiber.source_provenance == "source_derived"
    assert bundle.fiber.slice_values == ()

    assert bundle.child is not None
    assert bundle.child.family == "S_v-U_phys-R-R"
    assert "U_phys" in bundle.child.joint_role_sequence
    assert "U_v" not in bundle.child.joint_role_sequence
    assert bundle.child.geometry_provenance == "source_derived"
    assert bundle.child.status is CertificateStatus.LOCAL_ONLY

    assert bundle.certificate.axis_aggregation_status is CertificateStatus.EXACT_GLOBAL
    assert bundle.certificate.closed_mechanism_status is CertificateStatus.LOCAL_ONLY
    assert not bundle.certificate.accepted_for_reconstruction
    assert bundle.v05_certificate["evidence"]["independent_reduced_solve_present"] is True
    assert bundle.comparison is not None
    assert bundle.comparison["component_correspondence_complete"] is False

    assert bundle.orientation_image is not None
    assert bundle.orientation_image["curve_type"] != "SO3_coverage"
    assert "coverage" not in bundle.orientation_image["curve_type"].casefold()
    assert bundle.orientation_image["sample_count"] > 0

    assert bundle.reconstruction.certificate_status is CertificateStatus.LOCAL_ONLY
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.fiber.fiber_id in bundle.reconstruction.unresolved_fiber_ids
    assert bundle.reconstruction.reconstructed_coverage_status == "matched_on_traced_arc"
    assert bundle.reconstruction.target_space == "Y1 ⊂ SO(3)"
    assert "Not dexterous_workspace" in " ".join(bundle.reconstruction.notes)
    assert bundle.max_orientation_error_rad is not None
    assert bundle.max_orientation_error_rad >= 0.0
    assert bundle.certificate.task_map_error == bundle.max_orientation_error_rad


def test_l4_generic_bundle_does_not_promote_child() -> None:
    bundle = build_spatial_l4_generic_bundle()
    assert bundle.child is None
    assert bundle.certificate.closed_mechanism_status is CertificateStatus.UNRESOLVED
    assert not bundle.certificate.accepted_for_reconstruction
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.fiber.fiber_id in bundle.reconstruction.unresolved_fiber_ids
    assert bundle.orientation_image is not None  # source curve may still exist


def test_l4_forged_identity_cannot_accept_closed_status() -> None:
    certificate = ladder_certificate_from_forged_identity()
    assert certificate.closed_mechanism_status is CertificateStatus.UNRESOLVED
    assert not certificate.accepted_for_reconstruction
    assert "independent" in certificate.reason.casefold() or "identity" in certificate.reason.casefold()


def test_l4_catalog_fiber_status_is_local_until_component_completeness() -> None:
    fiber = next(spec for spec in DEFAULT_FIBER_SPECS if spec.rung is LadderRung.L4)
    assert fiber.certificate_status is CertificateStatus.LOCAL_ONLY
    assert fiber.process_status is ProcessStatus.SCAFFOLD
    notes = " ".join(fiber.notes).casefold()
    assert "exact_u_pair_4r" in notes
    assert "component" in notes


def test_l4_default_payload_summaries() -> None:
    payload = default_l4_equivalence_payload()
    assert "bundles" in payload and len(payload["bundles"]) == 2
    by_id = {item["architecture_id"]: item for item in payload["summaries"]}
    assert by_id["exact_u_pair_4r"]["closed_mechanism_status"] == "LOCAL_ONLY"
    assert by_id["exact_u_pair_4r"]["independent_reduced_solve_present"] is True
    assert by_id["generic_4r"]["closed_mechanism_status"] == "UNRESOLVED"
    assert by_id["generic_4r"]["independent_reduced_solve_present"] is False
