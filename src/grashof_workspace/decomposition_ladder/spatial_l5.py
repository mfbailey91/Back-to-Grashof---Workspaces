"""L5 scaffold adapter: shared records for V06-mapped spatial 5R work.

This does **not** construct a two-dimensional fixed-position parent chart, does
not continue pointing fibers, and does not issue closed-mechanism certificates.
Letter families remain a candidate corpus with ``UNRESOLVED`` statuses
(Gate K2 / ADR-024 / ADR-026).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from grashof_workspace.spatial_experiments.v06_corpus import (
    Spatial5RCorpusEntry,
    audit_fixed_position_seed_5r,
    build_generic_5r,
    seed_audit_summary,
)

from .models import (
    CertificateStatus,
    ChildMechanismRecord,
    EquivalenceCertificateRecord,
    LadderRung,
    ProcessStatus,
    ReconstructionRecord,
    SourceFiberRecord,
    SourceParentRecord,
)
from .registry import PARENT_CHILD_FAMILIES


@dataclass(frozen=True, slots=True)
class SpatialL5ScaffoldBundle:
    """Scaffold evidence for L5 / V06 without parent-reconstruction claims."""

    architecture_id: str
    parent: SourceParentRecord
    fiber_placeholder: SourceFiberRecord
    children: tuple[ChildMechanismRecord, ...]
    certificates: tuple[EquivalenceCertificateRecord, ...]
    reconstruction: ReconstructionRecord
    seed_audit: dict[str, Any]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "parent": self.parent.to_dict(),
            "fiber_placeholder": self.fiber_placeholder.to_dict(),
            "children": [child.to_dict() for child in self.children],
            "certificates": [cert.to_dict() for cert in self.certificates],
            "reconstruction": self.reconstruction.to_dict(),
            "seed_audit": self.seed_audit,
            "notes": list(self.notes),
        }


def build_spatial_l5_scaffold_bundle(
    entry: Spatial5RCorpusEntry | None = None,
) -> SpatialL5ScaffoldBundle:
    """Emit L5 shared records from the synthetic 5R corpus + letter families."""

    corpus = entry or build_generic_5r()
    audit = audit_fixed_position_seed_5r(corpus)
    architecture_id = corpus.model.architecture_id
    parent_id = f"{architecture_id}_pointing_parent_scaffold"
    fiber_id = f"{architecture_id}_fiber_placeholder"

    parent = SourceParentRecord(
        rung=LadderRung.L5,
        parent_id=parent_id,
        source_chain_id=architecture_id,
        task_point=tuple(float(v) for v in audit.p_star),
        dimension=2,
        target_space="S^2",
        component_ids=(fiber_id,),
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            "Scaffold placeholder keyed to a fixed-position seed p*.",
            "Parent geometry/charts are UNRESOLVED — not a FixedPositionParentResult.",
            "V06A must construct the complete M=2 parent independently of children.",
        ),
    )
    fiber = SourceFiberRecord(
        rung=LadderRung.L5,
        fiber_id=fiber_id,
        parent_id=parent_id,
        component_id=fiber_id,
        slice_values=(),
        branch_status="scaffold_placeholder",
        returned=False,
        source_provenance="scaffold_only",
        sample_count=0,
        task_image_status="UNRESOLVED_parent_charts_absent",
        notes=(
            "No pointing-latitude fiber has been continued.",
            "Placeholder exists so shared L5 interfaces are exercisable without Gate K2 violations.",
        ),
    )

    children: list[ChildMechanismRecord] = []
    certificates: list[EquivalenceCertificateRecord] = []
    for family in PARENT_CHILD_FAMILIES:
        child_id = f"{architecture_id}_{family.child_label}_candidate"
        children.append(
            ChildMechanismRecord(
                child_id=child_id,
                source_fiber_id=fiber_id,
                family=family.child_label,
                joint_kind_sequence=family.child_joint_kinds,
                joint_role_sequence=family.child_joint_roles,
                expected_mobility=1,
                geometry_provenance="candidate_corpus_only",
                status=CertificateStatus.UNRESOLVED,
                notes=(
                    *family.notes,
                    "Letter/mobility matching is not an equivalence certificate.",
                    "U_v on the child is a candidate task role, not source_chain_evidence.",
                ),
            )
        )
        certificates.append(
            EquivalenceCertificateRecord(
                source_fiber_id=fiber_id,
                child_id=child_id,
                axis_aggregation_status=CertificateStatus.UNRESOLVED,
                closed_mechanism_status=CertificateStatus.UNRESOLVED,
                component_scope="scaffold_candidate_corpus_only",
                coordinate_map="unresolved",
                reconstruction_map="unresolved",
                closure_error=None,
                tangent_error=None,
                task_map_error=None,
                reason=(
                    f"Candidate family {family.parent_label}→{family.child_label} has no "
                    "issued axis-aggregation or independent closed-mechanism certificate."
                ),
            )
        )

    reconstruction = ReconstructionRecord(
        rung=LadderRung.L5,
        parent_id=parent_id,
        target_space="S^2",
        accepted_fiber_ids=(),
        unresolved_fiber_ids=(fiber_id,),
        direct_coverage_status="UNRESOLVED_no_parent_image",
        reconstructed_coverage_status="UNRESOLVED_no_accepted_children",
        comparison_error=None,
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.UNRESOLVED,
        notes=(
            "Gate K2 / ADR-024: a collection of 1D fibers is not the complete 2D parent.",
            "ADR-026: descriptor discovery remains blocked until parent image reconstruction succeeds.",
            "Reconstruction uses only accepted source-derived children — none exist yet.",
        ),
    )

    return SpatialL5ScaffoldBundle(
        architecture_id=architecture_id,
        parent=parent,
        fiber_placeholder=fiber,
        children=tuple(children),
        certificates=tuple(certificates),
        reconstruction=reconstruction,
        seed_audit=seed_audit_summary(audit),
        notes=(
            (
                "L5 scaffold interface under V06; scientific source remains "
                "docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md."
            ),
            "Next scientific step: V06A FixedPositionParentResult (independent 2D parent).",
            "Architecture-scoped after proximal exact_u_pair_4r EXACT_ON_COMPONENT gate.",
        ),
    )


def default_l5_scaffold_payload() -> dict[str, Any]:
    """Machine-readable L5 section for ladder readouts."""

    bundle = build_spatial_l5_scaffold_bundle()
    return {
        "note": (
            "L5 scaffold only: seed nullity-2 audit + candidate letter families. "
            "Not a 2D parent representation and not pointing-image reconstruction. "
            "V06A remains the next scientific step."
        ),
        "v06_program": "docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md#sprint-v06",
        "bundle": bundle.to_dict(),
        "summary": {
            "architecture_id": bundle.architecture_id,
            "seed_rank_jp": bundle.seed_audit.get("rank_jp"),
            "seed_nullity_jp": bundle.seed_audit.get("nullity_jp"),
            "seed_status": bundle.seed_audit.get("status"),
            "candidate_family_count": len(bundle.children),
            "candidate_families": [child.family for child in bundle.children],
            "all_certificates_unresolved": all(
                cert.closed_mechanism_status is CertificateStatus.UNRESOLVED
                and cert.axis_aggregation_status is CertificateStatus.UNRESOLVED
                for cert in bundle.certificates
            ),
            "reconstruction_status": bundle.reconstruction.certificate_status.value,
            "accepted_fiber_count": len(bundle.reconstruction.accepted_fiber_ids),
            "process_status": bundle.parent.process_status.value,
        },
    }
