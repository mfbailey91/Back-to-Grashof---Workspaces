"""Integration checks for the trusted L3 planar calibration adapter."""

from grashof_workspace.decomposition_ladder.models import CertificateStatus, LadderRung
from grashof_workspace.decomposition_ladder.planar_l3 import (
    evaluate_planar_l3,
    evaluate_planar_l3_radii,
)
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
