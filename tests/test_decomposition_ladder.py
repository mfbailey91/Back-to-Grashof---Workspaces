"""Contracts for the L3-L7 decomposition ladder scaffold and U-drive semantics."""

from __future__ import annotations

import math

import numpy as np
import pytest

from grashof_workspace.decomposition_ladder.leaf_engine import (
    LeafSolveRequest,
    _evidence_scope,
)
from grashof_workspace.decomposition_ladder.models import (
    CertificateStatus,
    ChildMechanismRecord,
    DriveMode,
    EquivalenceCertificateRecord,
    LadderRung,
    ProcessStatus,
    ReconstructionRecord,
    SourceFiberRecord,
    SourceParentRecord,
    loop_mobility,
)
from grashof_workspace.decomposition_ladder.readout import build_ladder_readout
from grashof_workspace.decomposition_ladder.registry import (
    DEFAULT_FIBER_SPECS,
    PARENT_CHILD_FAMILIES,
    RUNG_SPECS,
    rung_spec,
)
from grashof_workspace.decomposition_ladder.u_drive import (
    choose_local_drive_coordinate,
    conceptual_branch_samples,
    free_branch_contract,
    prescribed_coordinate_contract,
    summarize_branch,
    u_pointing,
    u_rotation_matrix,
)
from grashof_workspace.spatial4bar_explorer.geometry import OrderedFamily, canonical_geometry


def test_rung_dimensions_reduce_to_one_dimensional_leaves() -> None:
    assert [spec.rung for spec in RUNG_SPECS] == [
        LadderRung.L3,
        LadderRung.L4,
        LadderRung.L5,
        LadderRung.L6,
        LadderRung.L7,
    ]
    for spec in RUNG_SPECS:
        assert spec.fixed_position_mobility == spec.n_joints - spec.position_dimension
        assert spec.leaf_dimension == 1
        assert spec.total_slice_count == spec.fixed_position_mobility - 1
    assert rung_spec("L5").task_slice_count == 1
    assert rung_spec(LadderRung.L7).redundancy_slice_count == 1
    assert rung_spec(LadderRung.L7).process_status is ProcessStatus.BLOCKED
    assert rung_spec(LadderRung.L6).process_status is ProcessStatus.SCAFFOLD
    assert rung_spec(LadderRung.L5).process_status is ProcessStatus.SCAFFOLD
    assert rung_spec(LadderRung.L4).process_status is ProcessStatus.SCAFFOLD


def test_registered_fiber_specs_match_rung_leaf_dimensions() -> None:
    by_rung = {spec.rung: spec for spec in RUNG_SPECS}
    assert len(DEFAULT_FIBER_SPECS) == len(RUNG_SPECS)
    for fiber in DEFAULT_FIBER_SPECS:
        assert fiber.parent_dimension == by_rung[fiber.rung].fixed_position_mobility
        assert fiber.source_fiber_dimension == 1
        assert len(fiber.constraints) == by_rung[fiber.rung].total_slice_count
    assert DEFAULT_FIBER_SPECS[1].certificate_status is CertificateStatus.LOCAL_ONLY
    assert "exact_u_pair_4r" in " ".join(DEFAULT_FIBER_SPECS[1].notes)
    assert "component" in " ".join(DEFAULT_FIBER_SPECS[1].notes).casefold()
    l5_fiber = next(spec for spec in DEFAULT_FIBER_SPECS if spec.rung is LadderRung.L5)
    assert l5_fiber.process_status is ProcessStatus.SCAFFOLD
    assert l5_fiber.certificate_status is CertificateStatus.UNRESOLVED
    l6_fiber = next(spec for spec in DEFAULT_FIBER_SPECS if spec.rung is LadderRung.L6)
    assert l6_fiber.process_status is ProcessStatus.SCAFFOLD
    assert l6_fiber.certificate_status is CertificateStatus.UNRESOLVED
    assert DEFAULT_FIBER_SPECS[4].process_status is ProcessStatus.BLOCKED


def test_parent_child_families_are_candidate_corpus_not_certificates() -> None:
    assert [family.child_label for family in PARENT_CHILD_FAMILIES] == [
        "UUUR",
        "UURU",
        "URUU",
        "USRR",
        "URSR",
        "URRS",
    ]
    for family in PARENT_CHILD_FAMILIES:
        assert family.parent_mobility == 2
        assert family.child_mobility == 1
        assert family.parent_joint_roles[0] == "S_v"
        assert family.child_joint_roles[0] == "U_v"
        assert len(family.parent_joint_kinds) == 4
        assert len(family.child_joint_kinds) == 4
        assert family.candidate_corpus_status is ProcessStatus.PLANNED
        assert family.axis_aggregation_status is CertificateStatus.UNRESOLVED
        assert family.closed_mechanism_status is CertificateStatus.UNRESOLVED


def test_loop_mobility_rejects_unknown_role() -> None:
    assert loop_mobility(("S_v", "U_phys", "U_phys", "R_phys")) == 2
    assert loop_mobility(("U_v", "U_phys", "U_phys", "R_phys")) == 1
    with pytest.raises(ValueError):
        loop_mobility(("S_v", "unknown", "R_phys", "R_phys"))


def test_u_rotation_and_pointing_are_proper() -> None:
    rotation = u_rotation_matrix(0.4, -0.2)
    assert np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-12)
    assert abs(float(np.linalg.det(rotation)) - 1.0) < 1e-12
    pointing = np.asarray(u_pointing(0.4, -0.2), dtype=float)
    assert abs(float(np.linalg.norm(pointing)) - 1.0) < 1e-12


def test_free_branch_is_canonical_drive_contract() -> None:
    contract = free_branch_contract()
    assert contract.mode is DriveMode.FREE_BRANCH
    assert contract.commanded_coordinate is None
    assert "alpha(s)" in contract.solved_coordinates
    assert "beta(s)" in contract.solved_coordinates


def test_local_drive_switches_at_coordinate_turning_points() -> None:
    alpha = choose_local_drive_coordinate(0.8, 0.1)
    beta = choose_local_drive_coordinate(0.0, -0.6)
    neutral = choose_local_drive_coordinate(1e-12, -1e-12)
    assert alpha.mode is DriveMode.PRESCRIBED_ALPHA
    assert beta.mode is DriveMode.PRESCRIBED_BETA
    assert neutral.mode is DriveMode.FREE_BRANCH
    assert prescribed_coordinate_contract("alpha").commanded_coordinate == "alpha"
    with pytest.raises(ValueError):
        prescribed_coordinate_contract("gamma")


def test_conceptual_u_branch_has_one_winding_and_one_rocker() -> None:
    samples = conceptual_branch_samples()
    summary = summarize_branch(samples)
    assert summary.alpha_winding == 1
    assert summary.beta_winding == 0
    assert math.isclose(summary.alpha_range, 2.0 * math.pi, rel_tol=1e-12)
    assert summary.beta_range > 1.0
    assert "circulates" in summary.interpretation


def test_ladder_readout_writes_html_json_and_plot(tmp_path) -> None:
    paths = build_ladder_readout(tmp_path, include_animation=False)
    assert paths.html.is_file()
    assert paths.json.is_file()
    assert paths.coordinate_plot.is_file()
    assert paths.animation is None
    html = paths.html.read_text(encoding="utf-8")
    assert "L3 through L7" in html
    assert "KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md" in html
    assert "drive the branch parameter" in html or "pseudo-arclength" in html
    assert "UUUR" in html and "SUUR" in html
    assert "candidate test corpus" in html
    assert "Descriptor discovery remains downstream" in html
    assert "L5 spatial 5R scaffold" in html
    assert "L6 spatial 6R scaffold" in html
    assert "nullity=2" in html or "nullity</th>" in html
    payload = paths.json.read_text(encoding="utf-8")
    assert "optional_subordinate_to_V05_V09" in payload
    assert '"l5_scaffold"' in payload
    assert '"l6_scaffold"' in payload
    assert '"nullity_jp": 2' in payload or '"seed_nullity_jp": 2' in payload
    assert '"seed_nullity_jp": 3' in payload or '"nullity_jp": 3' in payload


def test_certificate_preserves_aggregation_closed_split() -> None:
    certificate = EquivalenceCertificateRecord(
        source_fiber_id="fiber0",
        child_id="child0",
        axis_aggregation_status=CertificateStatus.EXACT_GLOBAL,
        closed_mechanism_status=CertificateStatus.UNRESOLVED,
        component_scope="component0",
        coordinate_map="phi",
        reconstruction_map="phi_inv",
        closure_error=None,
        tangent_error=None,
        task_map_error=None,
        reason="aggregation exact; independent closed solve unresolved",
    )
    assert certificate.status is CertificateStatus.UNRESOLVED
    assert not certificate.accepted_for_reconstruction
    payload = certificate.to_decomposition_certificate_dict()
    assert payload["axis_aggregation_status"] == "EXACT_GLOBAL"
    assert payload["closed_mechanism_status"] == "UNRESOLVED"
    assert payload["status"] == "UNRESOLVED"


def test_common_result_records_preserve_process_vs_certificate() -> None:
    parent = SourceParentRecord(
        rung=LadderRung.L5,
        parent_id="parent0",
        source_chain_id="synthetic_5r",
        task_point=(0.2, 0.3, 0.4),
        dimension=2,
        target_space="S^2",
        component_ids=("component0",),
        process_status=ProcessStatus.SCAFFOLD,
    )
    fiber = SourceFiberRecord(
        rung=LadderRung.L5,
        fiber_id="fiber_c0",
        parent_id=parent.parent_id,
        component_id="component0",
        slice_values=(("c", 0.0),),
        branch_status="returned",
        returned=True,
        source_provenance="source_derived",
        sample_count=101,
        task_image_status="EXPORTED",
    )
    child = ChildMechanismRecord(
        child_id="child0",
        source_fiber_id=fiber.fiber_id,
        family="UUUR",
        joint_kind_sequence=("U", "U", "U", "R"),
        joint_role_sequence=("U_v", "U_phys", "U_phys", "R_phys"),
        expected_mobility=1,
        geometry_provenance="task_derived",
        status=CertificateStatus.UNRESOLVED,
    )
    certificate = EquivalenceCertificateRecord(
        source_fiber_id=fiber.fiber_id,
        child_id=child.child_id,
        axis_aggregation_status=CertificateStatus.EXACT_ON_COMPONENT,
        closed_mechanism_status=CertificateStatus.EXACT_ON_COMPONENT,
        component_scope="component0",
        coordinate_map="phi_c",
        reconstruction_map="phi_c_inverse",
        closure_error=1e-12,
        tangent_error=1e-9,
        task_map_error=1e-8,
        reason="accepted test fixture",
    )
    reconstruction = ReconstructionRecord(
        rung=LadderRung.L5,
        parent_id=parent.parent_id,
        target_space="S^2",
        accepted_fiber_ids=(fiber.fiber_id,),
        unresolved_fiber_ids=(),
        direct_coverage_status="PARTIAL_COVERAGE",
        reconstructed_coverage_status="PARTIAL_COVERAGE",
        comparison_error=1e-5,
        process_status=ProcessStatus.REVIEW,
        certificate_status=CertificateStatus.UNRESOLVED,
    )

    assert parent.to_dict()["process_status"] == "SCAFFOLD"
    assert fiber.to_dict()["slice_values"] == {"c": 0.0}
    assert child.to_dict()["joint_role_sequence"][0] == "U_v"
    assert certificate.accepted_for_reconstruction
    assert reconstruction.to_dict()["certificate_status"] == "UNRESOLVED"


def test_unresolved_certificate_is_not_reconstruction_evidence() -> None:
    certificate = EquivalenceCertificateRecord(
        source_fiber_id="fiber0",
        child_id="child0",
        axis_aggregation_status=CertificateStatus.UNRESOLVED,
        closed_mechanism_status=CertificateStatus.UNRESOLVED,
        component_scope="not established",
        coordinate_map="unknown",
        reconstruction_map="unknown",
        closure_error=None,
        tangent_error=None,
        task_map_error=None,
        reason="independent child solve not yet available",
    )
    assert not certificate.accepted_for_reconstruction


def test_leaf_engine_rejects_forged_provenance_without_certificate() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    forged = LeafSolveRequest(
        geometry=geometry,
        sample_id="forged",
        source_rung="L4",
        source_parent_id="parent",
        source_component_id="component0",
        slice_id="none",
        source_provenance="source_derived",
        certificate=None,
    )
    assert _evidence_scope(forged) == "unresolved_source_correspondence"

    explorer_only = LeafSolveRequest(
        geometry=geometry,
        sample_id="explorer",
        source_rung="L4",
        source_parent_id="parent",
        source_component_id="component0",
        slice_id="none",
        source_provenance="mechanism_explorer_only",
        certificate=None,
    )
    assert _evidence_scope(explorer_only) == "mechanism_explorer_only"

    aggregation_only = EquivalenceCertificateRecord(
        source_fiber_id="fiber0",
        child_id="child0",
        axis_aggregation_status=CertificateStatus.EXACT_GLOBAL,
        closed_mechanism_status=CertificateStatus.UNRESOLVED,
        component_scope="component0",
        coordinate_map="regroup",
        reconstruction_map="unknown",
        closure_error=None,
        tangent_error=None,
        task_map_error=None,
        reason="ADR-021: aggregation is not closed-mechanism acceptance",
    )
    aggregation_request = LeafSolveRequest(
        geometry=geometry,
        sample_id="agg_only",
        source_rung="L4",
        source_parent_id="parent",
        source_component_id="component0",
        slice_id="none",
        source_provenance="source_derived",
        certificate=aggregation_only,
    )
    assert _evidence_scope(aggregation_request) == "unresolved_source_correspondence"

    accepted = EquivalenceCertificateRecord(
        source_fiber_id="fiber0",
        child_id="child0",
        axis_aggregation_status=CertificateStatus.EXACT_GLOBAL,
        closed_mechanism_status=CertificateStatus.EXACT_ON_COMPONENT,
        component_scope="component0",
        coordinate_map="phi",
        reconstruction_map="phi_inv",
        closure_error=1e-12,
        tangent_error=1e-9,
        task_map_error=1e-8,
        reason="accepted fixture",
    )
    accepted_request = LeafSolveRequest(
        geometry=geometry,
        sample_id="accepted",
        source_rung="L4",
        source_parent_id="parent",
        source_component_id="component0",
        slice_id="none",
        source_provenance="source_derived",
        certificate=accepted,
    )
    assert _evidence_scope(accepted_request) == "source_chain_evidence"
