"""L6 scaffold adapter: shared records for V07-mapped spatial 6R work.

This does **not** freeze a decomposition-free SO(3) orientation reference
(Gate K3 / V07A), does not continue nested orientation fibers, and does not
start V08 terminal-roll quotient work. Children remain empty until V07 truth
exists (ADR-013 / ADR-024 / ADR-026).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from grashof_workspace.spatial_experiments.v07_corpus import (
    Spatial6RCorpusEntry,
    audit_fixed_position_seed_6r,
    build_generic_6r,
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


@dataclass(frozen=True, slots=True)
class SpatialL6ScaffoldBundle:
    """Scaffold evidence for L6 / V07 without SO(3)-reference claims."""

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


def build_spatial_l6_scaffold_bundle(
    entry: Spatial6RCorpusEntry | None = None,
) -> SpatialL6ScaffoldBundle:
    """Emit L6 shared records from the synthetic 6R corpus (no child corpus)."""

    corpus = entry or build_generic_6r()
    audit = audit_fixed_position_seed_6r(corpus)
    architecture_id = corpus.model.architecture_id
    parent_id = f"{architecture_id}_orientation_parent_scaffold"
    fiber_id = f"{architecture_id}_fiber_placeholder"

    parent = SourceParentRecord(
        rung=LadderRung.L6,
        parent_id=parent_id,
        source_chain_id=architecture_id,
        task_point=tuple(float(v) for v in audit.p_star),
        dimension=3,
        target_space="SO(3)",
        component_ids=(fiber_id,),
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            "Scaffold placeholder keyed to a fixed-position seed p*.",
            "Orientation parent/charts are UNRESOLVED — not a frozen SO(3) reference.",
            "V07A must freeze a decomposition-free SO(3) reference before nested slices / V08.",
        ),
    )
    fiber = SourceFiberRecord(
        rung=LadderRung.L6,
        fiber_id=fiber_id,
        parent_id=parent_id,
        component_id=fiber_id,
        slice_values=(),
        branch_status="scaffold_placeholder",
        returned=False,
        source_provenance="scaffold_only",
        sample_count=0,
        task_image_status="UNRESOLVED_so3_reference_absent",
        notes=(
            "No nested orientation chart leaves (h1,h2) have been continued.",
            "Placeholder exists so shared L6 interfaces are exercisable without Gate K3 violations.",
        ),
    )

    reconstruction = ReconstructionRecord(
        rung=LadderRung.L6,
        parent_id=parent_id,
        target_space="SO(3)",
        accepted_fiber_ids=(),
        unresolved_fiber_ids=(fiber_id,),
        direct_coverage_status="UNRESOLVED_no_frozen_so3_reference",
        reconstructed_coverage_status="UNRESOLVED_no_accepted_children",
        comparison_error=None,
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.UNRESOLVED,
        notes=(
            "Gate K3 / ADR-013: freeze a decomposition-free SO(3) reference before reconstruction.",
            "ADR-024: a collection of 1D fibers is not the complete M=3 parent.",
            "ADR-026: descriptor discovery remains blocked until parent image reconstruction succeeds.",
            "V08 terminal-roll quotient is blocked until the V07 reference exists.",
            "Reconstruction uses only accepted source-derived children — none exist yet.",
        ),
    )

    return SpatialL6ScaffoldBundle(
        architecture_id=architecture_id,
        parent=parent,
        fiber_placeholder=fiber,
        children=(),
        certificates=(),
        reconstruction=reconstruction,
        seed_audit=seed_audit_summary(audit),
        notes=(
            (
                "L6 scaffold interface under V07-first mapping; scientific source remains "
                "docs/archive/programs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md."
            ),
            "Next scientific step: V07A FixedPositionParentResult / frozen SO(3) reference.",
            "Architecture-scoped after proximal exact_u_pair_4r LOCAL_ONLY traced-arc match.",
            "Does not reuse L5 PARENT_CHILD_FAMILIES as an L6 letter corpus.",
        ),
    )


def default_l6_scaffold_payload() -> dict[str, Any]:
    """Machine-readable L6 section for ladder readouts."""

    bundle = build_spatial_l6_scaffold_bundle()
    return {
        "note": (
            "L6 scaffold only: seed nullity-3 audit for generic spatial 6R. "
            "Not a frozen SO(3) reference, not nested-slice reconstruction, and not V08. "
            "V07A remains the next scientific step."
        ),
        "v07_program": "docs/archive/programs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md#sprint-v07",
        "bundle": bundle.to_dict(),
        "summary": {
            "architecture_id": bundle.architecture_id,
            "seed_rank_jp": bundle.seed_audit.get("rank_jp"),
            "seed_nullity_jp": bundle.seed_audit.get("nullity_jp"),
            "seed_status": bundle.seed_audit.get("status"),
            "child_count": len(bundle.children),
            "certificate_count": len(bundle.certificates),
            "reconstruction_status": bundle.reconstruction.certificate_status.value,
            "accepted_fiber_count": len(bundle.reconstruction.accepted_fiber_ids),
            "process_status": bundle.parent.process_status.value,
            "target_space": bundle.parent.target_space,
        },
    }
