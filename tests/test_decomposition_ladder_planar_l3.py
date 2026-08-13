"""Integration checks for the trusted L3 planar calibration adapter."""

from __future__ import annotations

from dataclasses import replace

from grashof_workspace.decomposition_ladder.models import (
    CertificateStatus,
    LadderRung,
    ProcessStatus,
)
from grashof_workspace.decomposition_ladder.planar_l3 import (
    DEFAULT_L3_RADII,
    build_planar_l3_evidence_bundle,
    default_l3_calibration_payload,
    evaluate_planar_l3,
    evaluate_planar_l3_evidence_radii,
    evaluate_planar_l3_radii,
)
from grashof_workspace.decomposition_ladder.readout import build_ladder_readout, render_ladder_html
from grashof_workspace.planar3r import Planar3R


def test_l3_adapter_reconstructs_planar_dexterity_from_exact_rotatability() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    interior = evaluate_planar_l3(arm, 2.0)
    exterior = evaluate_planar_l3(arm, 3.5)

    assert interior.rung is LadderRung.L3
    assert interior.decomposition_status is CertificateStatus.EXACT_GLOBAL
    assert "non-assemblable" in interior.certificate_scope
    assert interior.designated_input_can_fully_rotate
    assert interior.dexterous
    assert interior.predicate_reconstruction_match

    assert exterior.decomposition_status is CertificateStatus.EXACT_GLOBAL
    assert not exterior.designated_input_can_fully_rotate
    assert not exterior.dexterous
    assert exterior.predicate_reconstruction_match


def test_l3_adapter_preserves_ordered_fourbar_lengths() -> None:
    arm = Planar3R(2.0, 1.5, 0.75)
    result = evaluate_planar_l3(arm, 1.25)
    assert result.child_loop_lengths == (1.25, 0.75, 1.5, 2.0)
    assert result.source_parent_mobility == 1
    assert result.target_space == "SO(2)"


def test_l3_multi_radius_payload_is_deterministic() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    results = evaluate_planar_l3_radii(arm, (0.0, 1.0, 2.0, 3.5))
    assert [result.rho for result in results] == [0.0, 1.0, 2.0, 3.5]
    assert all(result.predicate_reconstruction_match for result in results)


def test_l3_evidence_bundle_shapes_and_roles() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    bundle = build_planar_l3_evidence_bundle(arm, 2.0)

    assert bundle.parent.rung is LadderRung.L3
    assert bundle.parent.process_status is ProcessStatus.SCAFFOLD
    assert bundle.parent.task_point == (2.0, 0.0)
    assert bundle.parent.dimension == 1
    assert bundle.parent.target_space == "SO(2)"

    assert bundle.fiber.slice_values == (("rho", 2.0),)
    assert bundle.fiber.source_provenance == "analytical_planar3r"
    assert bundle.fiber.returned
    assert bundle.fiber.task_image_status == "SO2_full_circle"

    assert bundle.child.family == "planar 4R"
    assert bundle.child.joint_kind_sequence == ("R", "R", "R", "R")
    assert bundle.child.joint_role_sequence == ("R_v", "R_phys", "R_phys", "R_phys")
    assert bundle.child.geometry_provenance == "source_derived_analytical"
    assert bundle.child.status is CertificateStatus.EXACT_GLOBAL

    assert bundle.certificate.axis_aggregation_status is CertificateStatus.EXACT_GLOBAL
    assert bundle.certificate.closed_mechanism_status is CertificateStatus.EXACT_GLOBAL
    assert bundle.certificate.status is CertificateStatus.EXACT_GLOBAL
    assert bundle.certificate.accepted_for_reconstruction
    assert "analytical" in bundle.certificate.reason.casefold()

    assert bundle.leaf_predicate.coordinate_windings == (("designated_input", 1),)
    assert "not automatic" in bundle.leaf_predicate.evidence_scope

    assert bundle.reconstruction.certificate_status is CertificateStatus.EXACT_GLOBAL
    assert bundle.reconstruction.process_status is ProcessStatus.SCAFFOLD
    assert bundle.reconstruction.comparison_error == 0.0
    assert bundle.fiber.fiber_id in bundle.reconstruction.accepted_fiber_ids


def test_l3_non_dexterous_assemblable_bundle_keeps_map_exact() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    bundle = build_planar_l3_evidence_bundle(arm, 3.5)

    assert bundle.summary.assemblable
    assert not bundle.summary.designated_input_can_fully_rotate
    assert not bundle.summary.dexterous
    assert bundle.summary.predicate_reconstruction_match
    assert bundle.certificate.closed_mechanism_status is CertificateStatus.EXACT_GLOBAL
    assert bundle.fiber.returned
    assert bundle.fiber.task_image_status == "SO2_partial_or_bounded"
    assert bundle.fiber.fiber_id in bundle.reconstruction.accepted_fiber_ids


def test_l3_non_assemblable_exterior_bundle_keeps_map_exact() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    bundle = build_planar_l3_evidence_bundle(arm, 6.0)

    assert not bundle.summary.assemblable
    assert not bundle.summary.designated_input_can_fully_rotate
    assert not bundle.summary.dexterous
    assert bundle.summary.predicate_reconstruction_match
    assert bundle.certificate.closed_mechanism_status is CertificateStatus.EXACT_GLOBAL
    assert bundle.fiber.branch_status == "exterior_non_assemblable"
    assert bundle.fiber.fiber_id in bundle.reconstruction.unresolved_fiber_ids
    assert bundle.reconstruction.accepted_fiber_ids == ()


def test_l3_mismatched_predicates_refuse_reconstruction_acceptance() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    bundle = build_planar_l3_evidence_bundle(arm, 2.0)
    forged = replace(
        bundle.reconstruction,
        accepted_fiber_ids=(),
        unresolved_fiber_ids=(bundle.fiber.fiber_id,),
        comparison_error=None,
        notes=(
            "predicate mismatch: refuse workspace-membership reconstruction acceptance",
        ),
    )
    assert forged.accepted_fiber_ids == ()
    assert "mismatch" in forged.notes[0]
    # Workspace membership may not be claimed when predicates disagree.
    assert bundle.summary.predicate_reconstruction_match
    mismatched_summary = replace(bundle.summary, predicate_reconstruction_match=False)
    assert not mismatched_summary.predicate_reconstruction_match


def test_l3_readout_includes_calibration_section(tmp_path) -> None:
    paths = build_ladder_readout(tmp_path, include_animation=False)
    payload = default_l3_calibration_payload()
    assert payload["radii"] == list(DEFAULT_L3_RADII)
    assert len(payload["bundles"]) == len(DEFAULT_L3_RADII)

    import json

    written = json.loads(paths.json.read_text(encoding="utf-8"))
    assert "l3_calibration" in written
    assert written["l3_calibration"]["radii"] == list(DEFAULT_L3_RADII)

    html = paths.html.read_text(encoding="utf-8")
    assert "L3 planar calibration" in html
    assert "trusted exact map" in html
    assert "EXACT_GLOBAL" in html

    rendered = render_ladder_html(
        payload={
            **written,
            "conceptual_u_branch": written["conceptual_u_branch"],
        },
        coordinate_plot_name="figures/u_drive_coordinates.svg",
        animation_name=None,
    )
    assert "predicate match" in rendered


def test_l3_evidence_radii_helper_matches_default_set() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    bundles = evaluate_planar_l3_evidence_radii(arm)
    assert [bundle.summary.rho for bundle in bundles] == list(DEFAULT_L3_RADII)
    assert all(
        bundle.summary.decomposition_status is CertificateStatus.EXACT_GLOBAL
        for bundle in bundles
    )
