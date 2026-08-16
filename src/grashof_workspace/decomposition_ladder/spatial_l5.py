"""L5 adapter: V06-mapped spatial 5R records with atlas, images, fibers, and one UUUR child.

V06D2 may attach one task-derived ``U_v`` / UUUR audit from ``exact_two_u_5r``.
That is not parent completeness and not reconstruction. Other letter families
remain ``UNRESOLVED``
(Gate K2 / ADR-024 / ADR-026 / ADR-036 / ADR-037 / ADR-038 / ADR-039 / ADR-040 / ADR-041 / ADR-042).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from grashof_workspace.spatial_experiments.compound_parent import v06b_program_summary
from grashof_workspace.spatial_experiments.parent_atlas import (
    build_generic_5r_parent_atlas,
    parent_atlas_summary,
)
from grashof_workspace.spatial_experiments.parent_level_sets import (
    build_parent_level_sets,
    level_set_summary,
)
from grashof_workspace.spatial_experiments.parent_local import (
    build_generic_5r_local_patch,
    parent_local_summary,
)
from grashof_workspace.spatial_experiments.parent_reconstruction import (
    build_parent_reconstruction,
    reconstruction_summary,
)
from grashof_workspace.spatial_experiments.parent_task_images import (
    build_source_task_images,
    source_task_image_summary,
)
from grashof_workspace.spatial_experiments.v06_corpus import (
    Spatial5RCorpusEntry,
    audit_fixed_position_seed_5r,
    build_generic_5r,
    seed_audit_summary,
)
from grashof_workspace.spatial_experiments.virtual_u_child import v06d2_program_summary

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
    parent_local: dict[str, Any] | None = None
    parent_atlas: dict[str, Any] | None = None
    parent_images: dict[str, Any] | None = None
    parent_compound: dict[str, Any] | None = None
    parent_level_sets: dict[str, Any] | None = None
    parent_virtual_u: dict[str, Any] | None = None
    parent_reconstruction: dict[str, Any] | None = None
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
            "parent_local": self.parent_local,
            "parent_atlas": self.parent_atlas,
            "parent_images": self.parent_images,
            "parent_compound": self.parent_compound,
            "parent_level_sets": self.parent_level_sets,
            "parent_virtual_u": self.parent_virtual_u,
            "parent_reconstruction": self.parent_reconstruction,
            "notes": list(self.notes),
        }


def build_spatial_l5_scaffold_bundle(
    entry: Spatial5RCorpusEntry | None = None,
) -> SpatialL5ScaffoldBundle:
    """Emit L5 shared records from the synthetic 5R corpus + letter families."""

    corpus = entry or build_generic_5r()
    audit = audit_fixed_position_seed_5r(corpus)
    local = build_generic_5r_local_patch(corpus)
    local_summary = parent_local_summary(local)
    atlas = build_generic_5r_parent_atlas(
        corpus, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    atlas_summary = parent_atlas_summary(atlas)
    images = build_source_task_images(atlas, corpus.model)
    image_summary = source_task_image_summary(images)
    compound_summary = v06b_program_summary(grow_atlases=False)
    virtual_u_summary = v06d2_program_summary(grow_exact=True)
    level_sets = build_parent_level_sets(atlas, corpus.model)
    level_summary = level_set_summary(level_sets)
    recon = build_parent_reconstruction(atlas, corpus.model, images, level_sets)
    recon_summary = reconstruction_summary(recon)
    architecture_id = corpus.model.architecture_id
    parent_id = f"{architecture_id}_pointing_parent_scaffold"
    first = level_sets.fibers[0] if level_sets.fibers else None
    fiber_id = first.fiber_id if first is not None else f"{architecture_id}_fiber_placeholder"
    component_id = (
        first.parent_component_id
        if first is not None and first.parent_component_id
        else (atlas.component_ids[0] if atlas.component_ids else "UNRESOLVED_PARENT_COMPONENT")
    )

    parent = SourceParentRecord(
        rung=LadderRung.L5,
        parent_id=parent_id,
        source_chain_id=architecture_id,
        task_point=tuple(float(v) for v in audit.p_star),
        dimension=2,
        target_space="S^2",
        component_ids=atlas.component_ids,
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            f"V06A2 parent atlas representation_status={atlas.representation_status.value}.",
            f"discovery={atlas.discovery.status.value}; not a complete parent (ADR-037).",
            f"V06C source images coverage_label={images.pointing.coverage_label.value} (ADR-038).",
            "V06B SUUR parent is not a U_v child and not reconstruction (ADR-039).",
            "V06D1 task-derived source fibers exist; they are not the 2D parent (ADR-040).",
            (
                "V06E source-fiber paint exists; coverage comparison "
                f"{'evaluable' if recon.metrics.coverage_comparison_evaluable else 'unevaluable'} "
                f"(ADR-043); factorization={recon.factorization_status}."
            ),
            "Descriptor discovery remains blocked. V07A held (ADR-047).",
        ),
    )
    if first is not None:
        fiber = SourceFiberRecord(
            rung=LadderRung.L5,
            fiber_id=fiber_id,
            parent_id=parent_id,
            component_id=component_id,
            slice_values=(("h", float(first.c)),),
            branch_status=first.branch_status,
            returned=first.returned,
            source_provenance="task-derived",
            sample_count=len(first.samples),
            task_image_status="SOURCE_LEVEL_SET_PARTIAL",
            notes=(
                "Task-derived h=c source fiber; not U_v and not reconstruction.",
                "A collection of 1D fibers is not the complete 2D parent (Gate K2).",
                *first.notes,
            ),
        )
    else:
        fiber = SourceFiberRecord(
            rung=LadderRung.L5,
            fiber_id=fiber_id,
            parent_id=parent_id,
            component_id="UNRESOLVED_PARENT_COMPONENT",
            slice_values=(),
            branch_status="scaffold_placeholder",
            returned=False,
            source_provenance="scaffold_only",
            sample_count=0,
            task_image_status="SOURCE_IMAGE_PARTIAL_FIBER_ABSENT",
            notes=(
                "No pointing-latitude fiber has been continued.",
                "Placeholder exists so shared L5 interfaces are exercisable without Gate K2 violations.",
            ),
        )

    uuur_audit = (virtual_u_summary.get("exact_two_u_5r") or {})
    uuur_cert = uuur_audit.get("certificate") or {}
    children: list[ChildMechanismRecord] = []
    certificates: list[EquivalenceCertificateRecord] = []
    for family in PARENT_CHILD_FAMILIES:
        child_id = f"{architecture_id}_{family.child_label}_candidate"
        is_uuur = family.child_label == "UUUR"
        if is_uuur and uuur_cert:
            closed = CertificateStatus(uuur_cert.get("closed_mechanism_status", "UNRESOLVED"))
            axis = CertificateStatus(uuur_cert.get("axis_aggregation_status", "UNRESOLVED"))
            children.append(
                ChildMechanismRecord(
                    child_id=child_id,
                    source_fiber_id=uuur_audit.get("fiber_id") or fiber_id,
                    family=family.child_label,
                    joint_kind_sequence=family.child_joint_kinds,
                    joint_role_sequence=family.child_joint_roles,
                    expected_mobility=1,
                    geometry_provenance="source_derived_local_audit",
                    status=closed,
                    notes=(
                        *family.notes,
                        "V06D2 one-child UUUR audit on exact_two_u_5r (ADR-041).",
                        "Local U_v chart is not a global child certificate.",
                        "U_v on the child is a task-derived role, not source_chain_evidence until EXACT_*.",
                    ),
                )
            )
            certificates.append(
                EquivalenceCertificateRecord(
                    source_fiber_id=uuur_audit.get("fiber_id") or fiber_id,
                    child_id=child_id,
                    axis_aggregation_status=axis,
                    closed_mechanism_status=closed,
                    component_scope="local_budget_limited_fiber",
                    coordinate_map=str(uuur_cert.get("coordinate_map") or "uuur_local"),
                    reconstruction_map="unresolved",
                    closure_error=(uuur_cert.get("closure_residuals") or {}).get("max_closure_residual"),
                    tangent_error=uuur_cert.get("tangent_subspace_error"),
                    task_map_error=uuur_cert.get("trajectory_pointing_error"),
                    reason=str(uuur_cert.get("failure_or_scope_reason") or "UUUR local audit"),
                )
            )
            continue
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

    fiber_ids = tuple(f.fiber_id for f in level_sets.fibers) or (fiber_id,)
    reconstruction = ReconstructionRecord(
        rung=LadderRung.L5,
        parent_id=parent_id,
        target_space="S^2",
        accepted_fiber_ids=(),
        unresolved_fiber_ids=fiber_ids,
        direct_coverage_status=f"SOURCE_{images.pointing.coverage_label.value}",
        reconstructed_coverage_status="SOURCE_FIBER_UNEVALUABLE_CHILD_EMPTY",
        comparison_error=recon.metrics.hausdorff_rad,
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.UNRESOLVED,
        notes=(
            "Gate K2 / ADR-024: a collection of 1D fibers is not the complete 2D parent.",
            "ADR-026: descriptor discovery remains blocked until accepted-child reconstruction succeeds.",
            "ADR-039: SUUR EXACT_GLOBAL aggregation is not closed-component completeness.",
            "ADR-040: task-derived h=c fibers are not reconstruction.",
            "ADR-041: local U_v / UUUR is not reconstruction.",
            "ADR-042: source-fiber cell paint does not unblock reconstruction certificates.",
            "ADR-043: empty COVERED cells make the miss metric unevaluable; a nonempty COVERED set does not pass V06.",
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
        parent_local=local_summary,
        parent_atlas=atlas_summary,
        parent_images=image_summary,
        parent_compound=compound_summary,
        parent_level_sets=level_summary,
        parent_virtual_u=virtual_u_summary,
        parent_reconstruction=recon_summary,
        notes=(
            (
                "L5 scaffold interface under V06; scientific source remains "
                "docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md."
            ),
            "V06B SUUR parent exists; it is not UUUR reconstruction (ADR-039).",
            "V06D1 source fibers exist; they are not U_v children (ADR-040).",
            "V06D2 one UUUR child exists; it is not reconstruction (ADR-041).",
            "V06E closeout is honest non-pass; V07A held (ADR-047).",
        ),
    )


def default_l5_scaffold_payload() -> dict[str, Any]:
    """Machine-readable L5 section for ladder readouts."""

    bundle = build_spatial_l5_scaffold_bundle()
    return {
        "note": (
            "L5 scaffold: V06E accepted-child reconstruction is empty. Coverage comparison "
            "follows ADR-043 (unevaluable iff COVERED is empty). Not a 2D parent completeness "
            "claim and not pointing-image reconstruction. V07A held (ADR-047)."
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
            "parent_representation_status": (bundle.parent_atlas or {}).get("representation_status"),
            "parent_discovery_status": (bundle.parent_atlas or {}).get("discovery_status"),
            "source_image_coverage_label": (bundle.parent_images or {}).get("coverage_label"),
            "exact_two_u_axis_status": ((bundle.parent_compound or {}).get("exact_two_u_5r") or {})
            .get("certificate", {})
            .get("axis_aggregation_status"),
            "exact_two_u_closed_status": ((bundle.parent_compound or {}).get("exact_two_u_5r") or {})
            .get("certificate", {})
            .get("closed_mechanism_status"),
            "source_fiber_count": (bundle.parent_level_sets or {}).get("fiber_count"),
            "complete_foliation": (bundle.parent_level_sets or {}).get("complete_foliation"),
            "uuur_closed_status": ((bundle.parent_virtual_u or {}).get("exact_two_u_5r") or {})
            .get("certificate", {})
            .get("closed_mechanism_status"),
            "factorization_status": (bundle.parent_reconstruction or {}).get("factorization_status"),
            "v06_program_passed": (bundle.parent_reconstruction or {}).get("v06_program_passed"),
        },
    }
