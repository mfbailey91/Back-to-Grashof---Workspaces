"""L3 adapter for the trusted planar 3R → exact planar 4R calibration.

This module does not replace the existing analytical kernel. It wraps one
radius-level result in the decomposition-ladder vocabulary so later spatial
rungs can be compared against a known exact example.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from grashof_workspace.planar3r import DEFAULT_TOL, Planar3R

from .models import (
    CertificateStatus,
    ChildMechanismRecord,
    EquivalenceCertificateRecord,
    LadderRung,
    LeafPredicateRecord,
    ProcessStatus,
    ReconstructionRecord,
    SourceFiberRecord,
    SourceParentRecord,
)

# Deterministic demo radii used by readout and multi-radius tests.
DEFAULT_L3_RADII: tuple[float, ...] = (0.0, 1.0, 2.0, 3.5)
DEFAULT_L3_ARM_LENGTHS: tuple[float, float, float] = (2.0, 2.0, 1.0)

_JOINT_KINDS = ("R", "R", "R", "R")
# Loop order matches FourBar / Planar3R: (ground, input, coupler, output)
# = (rho, l3, l2, l1) → R_v at p*, then physical links tip→base.
_JOINT_ROLES = ("R_v", "R_phys", "R_phys", "R_phys")


@dataclass(frozen=True, slots=True)
class PlanarL3CalibrationResult:
    """Exact source/child/predicate/reconstruction record at one radius."""

    rung: LadderRung
    rho: float
    source_chain: str
    source_lengths: tuple[float, float, float]
    source_parent_mobility: int
    target_space: str
    virtual_closure: str
    child_family: str
    child_loop_lengths: tuple[float, float, float, float]
    assemblable: bool
    grashof_class: str
    inversion_type: str
    designated_input_can_fully_rotate: bool
    dexterous: bool
    decomposition_status: CertificateStatus
    certificate_scope: str
    predicate_reconstruction_match: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rung"] = self.rung.value
        payload["decomposition_status"] = self.decomposition_status.value
        return payload


@dataclass(frozen=True, slots=True)
class PlanarL3EvidenceBundle:
    """Shared ladder evidence records for one planar calibration radius."""

    summary: PlanarL3CalibrationResult
    parent: SourceParentRecord
    fiber: SourceFiberRecord
    child: ChildMechanismRecord
    certificate: EquivalenceCertificateRecord
    leaf_predicate: LeafPredicateRecord
    reconstruction: ReconstructionRecord

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "parent": self.parent.to_dict(),
            "fiber": self.fiber.to_dict(),
            "child": self.child.to_dict(),
            "certificate": self.certificate.to_dict(),
            "leaf_predicate": self.leaf_predicate.to_dict(),
            "reconstruction": self.reconstruction.to_dict(),
        }


def _radius_ids(rho: float) -> tuple[str, str, str]:
    tag = f"{rho:.6g}"
    parent_id = f"planar3r_fixed_position_rho_{tag}"
    fiber_id = f"planar3r_fiber_rho_{tag}"
    child_id = f"planar4r_child_rho_{tag}"
    return parent_id, fiber_id, child_id


def build_planar_l3_evidence_bundle(
    arm: Planar3R,
    rho: float,
    *,
    tol: float = DEFAULT_TOL,
) -> PlanarL3EvidenceBundle:
    """Emit shared ladder records for the analytical planar map at ``rho``."""

    linkage = arm.fourbar_at_radius(rho)
    state = arm.mechanism_state(rho, tol=tol)
    rotatable = linkage.input_can_fully_rotate(tol=tol)
    dexterous = arm.is_dexterous_radius(rho, tol=tol)
    match = rotatable == dexterous
    parent_id, fiber_id, child_id = _radius_ids(rho)

    if state.assemblable:
        branch_status = "returned_analytical"
        task_image_status = "SO2_full_circle" if rotatable else "SO2_partial_or_bounded"
        sample_count = 1
        accepted_ids: tuple[str, ...] = (fiber_id,)
        unresolved_ids: tuple[str, ...] = ()
        direct_coverage = "dexterous_radius" if dexterous else "non_dexterous_assemblable_radius"
        reconstructed_coverage = (
            "designated_input_full_rotation" if rotatable else "designated_input_non_rotating"
        )
    else:
        branch_status = "exterior_non_assemblable"
        task_image_status = "empty_or_unavailable"
        sample_count = 0
        accepted_ids = ()
        unresolved_ids = (fiber_id,)
        direct_coverage = "non_assemblable_exterior"
        reconstructed_coverage = "non_assemblable_exterior"

    summary = PlanarL3CalibrationResult(
        rung=LadderRung.L3,
        rho=float(rho),
        source_chain="planar 3R",
        source_lengths=(arm.l1, arm.l2, arm.l3),
        source_parent_mobility=1,
        target_space="SO(2)",
        virtual_closure="exact virtual revolute closure R_v at p*",
        child_family="planar 4R",
        child_loop_lengths=linkage.lengths,
        assemblable=state.assemblable,
        grashof_class=state.grashof_class,
        inversion_type=state.inversion_type,
        designated_input_can_fully_rotate=rotatable,
        dexterous=dexterous,
        decomposition_status=CertificateStatus.EXACT_GLOBAL,
        certificate_scope=(
            "exact 3R↔4R map at this radius, including non-assemblable exterior radii; "
            "dexterity/rotatability are separate predicates"
        ),
        predicate_reconstruction_match=match,
        notes=(
            "Exact designated-link rotatability, not the textual Grashof label, is the predicate.",
            "This is the trusted calibration rung for the ladder interfaces.",
            "EXACT_GLOBAL certifies the analytical map, not workspace membership.",
        ),
    )

    parent = SourceParentRecord(
        rung=LadderRung.L3,
        parent_id=parent_id,
        source_chain_id="planar_3r",
        task_point=(float(rho), 0.0),
        dimension=1,
        target_space="SO(2)",
        component_ids=(fiber_id,),
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            "Radius-level adapter: task_point=(rho, 0) uses radial symmetry of the planar workspace.",
            "SourceProblemRecord in the L3 program doc aliases this SourceParentRecord.",
        ),
    )

    fiber = SourceFiberRecord(
        rung=LadderRung.L3,
        fiber_id=fiber_id,
        parent_id=parent_id,
        component_id=fiber_id,
        slice_values=(("rho", float(rho)),),
        branch_status=branch_status,
        returned=state.assemblable,
        source_provenance="analytical_planar3r",
        sample_count=sample_count,
        task_image_status=task_image_status,
        notes=("Analytical planar fixed-position fiber; no numerical continuation.",),
    )

    child = ChildMechanismRecord(
        child_id=child_id,
        source_fiber_id=fiber_id,
        family="planar 4R",
        joint_kind_sequence=_JOINT_KINDS,
        joint_role_sequence=_JOINT_ROLES,
        expected_mobility=1,
        geometry_provenance="source_derived_analytical",
        status=CertificateStatus.EXACT_GLOBAL,
        notes=(
            "Loop lengths (ground,input,coupler,output)=(rho,l3,l2,l1).",
            "Trusted analytical child, not a spatial independent reduced solve.",
        ),
    )

    certificate = EquivalenceCertificateRecord(
        source_fiber_id=fiber_id,
        child_id=child_id,
        axis_aggregation_status=CertificateStatus.EXACT_GLOBAL,
        closed_mechanism_status=CertificateStatus.EXACT_GLOBAL,
        component_scope=f"analytical_planar_map_at_rho_{rho:.6g}",
        coordinate_map="planar3r_radius_to_fourbar_lengths",
        reconstruction_map="designated_input_rotatability_equals_dexterous_radius",
        closure_error=0.0,
        tangent_error=0.0,
        task_map_error=0.0 if match else None,
        reason=(
            "Trusted planar analytical 3R↔4R map at this radius "
            "(not a spatial independent reduced-solve certificate)."
        ),
    )

    leaf_predicate = LeafPredicateRecord(
        child_id=child_id,
        branch_status=branch_status,
        returned=state.assemblable,
        coordinate_windings=(("designated_input", 1 if rotatable else 0),),
        coordinate_ranges=(("designated_input", None if rotatable else 0.0),),
        minimum_singularity_margin=None,
        evidence_scope=(
            "leaf_predicate_only; not automatic dexterous_workspace coverage promotion"
        ),
        notes=(
            "designated_input winding 1 means full rotation; 0 means not fully rotatable.",
            "Workspace membership is reconstructed separately via ReconstructionRecord.",
        ),
    )

    reconstruction = ReconstructionRecord(
        rung=LadderRung.L3,
        parent_id=parent_id,
        target_space="SO(2)",
        accepted_fiber_ids=accepted_ids if match else (),
        unresolved_fiber_ids=unresolved_ids if match else (fiber_id,),
        direct_coverage_status=direct_coverage,
        reconstructed_coverage_status=reconstructed_coverage,
        comparison_error=0.0 if match else None,
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.EXACT_GLOBAL,
        notes=(
            "EXACT_GLOBAL here certifies the analytical map; dexterity is the separate predicate.",
            (
                "predicate_reconstruction_match=True"
                if match
                else "predicate mismatch: refuse workspace-membership reconstruction acceptance"
            ),
        ),
    )

    return PlanarL3EvidenceBundle(
        summary=summary,
        parent=parent,
        fiber=fiber,
        child=child,
        certificate=certificate,
        leaf_predicate=leaf_predicate,
        reconstruction=reconstruction,
    )


def evaluate_planar_l3(
    arm: Planar3R,
    rho: float,
    *,
    tol: float = DEFAULT_TOL,
) -> PlanarL3CalibrationResult:
    """Evaluate the exact L3 decomposition contract at Cartesian radius ``rho``."""

    return build_planar_l3_evidence_bundle(arm, rho, tol=tol).summary


def evaluate_planar_l3_radii(
    arm: Planar3R,
    radii: tuple[float, ...],
    *,
    tol: float = DEFAULT_TOL,
) -> tuple[PlanarL3CalibrationResult, ...]:
    """Evaluate a deterministic set of planar calibration radii."""

    return tuple(evaluate_planar_l3(arm, rho, tol=tol) for rho in radii)


def evaluate_planar_l3_evidence_radii(
    arm: Planar3R,
    radii: tuple[float, ...] = DEFAULT_L3_RADII,
    *,
    tol: float = DEFAULT_TOL,
) -> tuple[PlanarL3EvidenceBundle, ...]:
    """Evaluate shared-record evidence bundles for a deterministic radius set."""

    return tuple(build_planar_l3_evidence_bundle(arm, rho, tol=tol) for rho in radii)


def default_l3_calibration_payload() -> dict[str, Any]:
    """Machine-readable L3 calibration section for ladder readouts."""

    arm = Planar3R(*DEFAULT_L3_ARM_LENGTHS)
    bundles = evaluate_planar_l3_evidence_radii(arm, DEFAULT_L3_RADII)
    return {
        "arm_lengths": list(DEFAULT_L3_ARM_LENGTHS),
        "radii": list(DEFAULT_L3_RADII),
        "note": (
            "Trusted planar calibration leaf: EXACT_GLOBAL certifies the analytical "
            "3R↔4R map at each radius; process_status remains SCAFFOLD."
        ),
        "bundles": [bundle.to_dict() for bundle in bundles],
        "summaries": [bundle.summary.to_dict() for bundle in bundles],
    }
