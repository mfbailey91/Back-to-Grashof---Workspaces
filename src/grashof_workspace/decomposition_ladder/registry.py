"""Canonical L3-L7 ladder and candidate parent/child mechanism-family corpus."""

from __future__ import annotations

from typing import Any

from .models import (
    CertificateStatus,
    FiberFamilySpec,
    LadderRung,
    ParentChildFamilySpec,
    ProcessStatus,
    RungSpec,
    SliceConstraintSpec,
    SliceRole,
)

_CANDIDATE_NOTES = (
    "Letter labels identify a candidate test corpus only.",
    "Mobility and joint-letter matching are not equivalence certificates.",
    "axis_aggregation_status and closed_mechanism_status remain UNRESOLVED until issued.",
)


RUNG_SPECS: tuple[RungSpec, ...] = (
    RungSpec(
        rung=LadderRung.L3,
        source_chain="planar 3R",
        n_joints=3,
        position_dimension=2,
        fixed_position_mobility=1,
        target_label="SO(2) planar orientation",
        target_dimension=1,
        task_slice_count=0,
        redundancy_slice_count=0,
        direct_leaf=True,
        active_question=(
            "Can the trusted planar source fiber, exact virtual 4R, winding, and "
            "workspace reconstruction be expressed through the common interfaces?"
        ),
        process_status=ProcessStatus.SCAFFOLD,
        notes=("Calibration rung with an exact analytical result.",),
    ),
    RungSpec(
        rung=LadderRung.L4,
        source_chain="spatial 4R",
        n_joints=4,
        position_dimension=3,
        fixed_position_mobility=1,
        target_label="specified one-parameter orientation family Y1 ⊂ SO(3)",
        target_dimension=1,
        task_slice_count=0,
        redundancy_slice_count=0,
        direct_leaf=True,
        active_question=(
            "Can a complete source component and an independently instantiated "
            "one-DOF closed mechanism be shown to have the same orientation map?"
        ),
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            (
                "Maps to active V05. Proximal exact_u_pair_4r has an independent LOCAL_ONLY "
                "traced-arc match; complete component correspondence remains unresolved."
            ),
            "The generic orientation image is a curve in SO(3), not full spatial dexterity.",
        ),
    ),
    RungSpec(
        rung=LadderRung.L5,
        source_chain="spatial 5R",
        n_joints=5,
        position_dimension=3,
        fixed_position_mobility=2,
        target_label="S^2 tool pointing",
        target_dimension=2,
        task_slice_count=1,
        redundancy_slice_count=0,
        direct_leaf=False,
        active_question=(
            "Can the complete two-dimensional pointing parent be reconstructed from a "
            "task-derived family of certified one-DOF fibers?"
        ),
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            "Maps to active V06. Direct 2D source-parent construction may proceed independently of L4 acceptance.",
            "V06A1 parent representation is LOCAL_PATCH at one seed; complete atlas and reconstruction remain UNRESOLVED.",
            "Letter families are candidate tests only; not pointing-image reconstruction.",
        ),
    ),
    RungSpec(
        rung=LadderRung.L6,
        source_chain="spatial 6R",
        n_joints=6,
        position_dimension=3,
        fixed_position_mobility=3,
        target_label="SO(3) full orientation",
        target_dimension=3,
        task_slice_count=2,
        redundancy_slice_count=0,
        direct_leaf=False,
        active_question=(
            "After freezing a decomposition-free SO(3) reference (V07), can nested task "
            "slices and any V08 quotient reconstruct that independent truth?"
        ),
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            "V07-first architecture-scoped scaffold; L4 closed-mechanism is currently LOCAL_ONLY.",
            "SO(3) freeze / nested reconstruction still UNRESOLVED; V08 blocked until Gate K3.",
            "Not a frozen SO(3) reference (V07A next).",
        ),
    ),
    RungSpec(
        rung=LadderRung.L7,
        source_chain="spatial 7R",
        n_joints=7,
        position_dimension=3,
        fixed_position_mobility=4,
        target_label="SO(3) orientation plus one-dimensional self-motion",
        target_dimension=3,
        task_slice_count=2,
        redundancy_slice_count=1,
        direct_leaf=False,
        active_question=(
            "Can task orientation and internal redundancy be separated while preserving "
            "nonempty, compatible one-DOF leaves over the required target?"
        ),
        process_status=ProcessStatus.BLOCKED,
        notes=(
            "Deferred beyond the active V05–V09 sequence pending multi-component certificates.",
            "The redundancy coordinate is not a fourth orientation coordinate.",
        ),
    ),
)


PARENT_CHILD_FAMILIES: tuple[ParentChildFamilySpec, ...] = (
    ParentChildFamilySpec(
        parent_label="SUUR",
        child_label="UUUR",
        parent_joint_kinds=("S", "U", "U", "R"),
        child_joint_kinds=("U", "U", "U", "R"),
        parent_joint_roles=("S_v", "U_phys", "U_phys", "R_phys"),
        child_joint_roles=("U_v", "U_phys", "U_phys", "R_phys"),
        source_pattern=(
            "candidate 5R + S_v corpus entry assuming two physical RR→U aggregates "
            "followed by R (aggregation uncertified)"
        ),
        notes=_CANDIDATE_NOTES,
    ),
    ParentChildFamilySpec(
        parent_label="SURU",
        child_label="UURU",
        parent_joint_kinds=("S", "U", "R", "U"),
        child_joint_kinds=("U", "U", "R", "U"),
        parent_joint_roles=("S_v", "U_phys", "R_phys", "U_phys"),
        child_joint_roles=("U_v", "U_phys", "R_phys", "U_phys"),
        source_pattern="candidate 5R + S_v corpus entry with U-R-U physical ordering",
        notes=_CANDIDATE_NOTES,
    ),
    ParentChildFamilySpec(
        parent_label="SRUU",
        child_label="URUU",
        parent_joint_kinds=("S", "R", "U", "U"),
        child_joint_kinds=("U", "R", "U", "U"),
        parent_joint_roles=("S_v", "R_phys", "U_phys", "U_phys"),
        child_joint_roles=("U_v", "R_phys", "U_phys", "U_phys"),
        source_pattern="candidate 5R + S_v corpus entry with R-U-U physical ordering",
        notes=_CANDIDATE_NOTES,
    ),
    ParentChildFamilySpec(
        parent_label="SSRR",
        child_label="USRR",
        parent_joint_kinds=("S", "S", "R", "R"),
        child_joint_kinds=("U", "S", "R", "R"),
        parent_joint_roles=("S_v", "S_phys", "R_phys", "R_phys"),
        child_joint_roles=("U_v", "S_phys", "R_phys", "R_phys"),
        source_pattern=(
            "candidate 5R + S_v corpus entry assuming one physical RRR→S aggregate "
            "followed by R-R (aggregation uncertified)"
        ),
        notes=_CANDIDATE_NOTES,
    ),
    ParentChildFamilySpec(
        parent_label="SRSR",
        child_label="URSR",
        parent_joint_kinds=("S", "R", "S", "R"),
        child_joint_kinds=("U", "R", "S", "R"),
        parent_joint_roles=("S_v", "R_phys", "S_phys", "R_phys"),
        child_joint_roles=("U_v", "R_phys", "S_phys", "R_phys"),
        source_pattern="candidate 5R + S_v corpus entry with R-S-R physical ordering",
        notes=_CANDIDATE_NOTES,
    ),
    ParentChildFamilySpec(
        parent_label="SRRS",
        child_label="URRS",
        parent_joint_kinds=("S", "R", "R", "S"),
        child_joint_kinds=("U", "R", "R", "S"),
        parent_joint_roles=("S_v", "R_phys", "R_phys", "S_phys"),
        child_joint_roles=("U_v", "R_phys", "R_phys", "S_phys"),
        source_pattern="candidate 5R + S_v corpus entry with R-R-S physical ordering",
        notes=_CANDIDATE_NOTES,
    ),
)


POINTING_LATITUDE_SLICE = SliceConstraintSpec(
    name="pointing_latitude",
    role=SliceRole.TASK,
    formula="h(d)=n·d=c",
    parameter_name="c",
    target_space="S^2",
    rationale=(
        "At regular values, a scalar pointing level set reduces the two-dimensional "
        "5R pointing parent to a one-dimensional source fiber."
    ),
)

ORIENTATION_CHART_SLICE_1 = SliceConstraintSpec(
    name="orientation_chart_coordinate_1",
    role=SliceRole.TASK,
    formula="h1(R)=c1",
    parameter_name="c1",
    target_space="SO(3)",
    rationale="First local/global task coordinate used to foliate a 3D orientation parent.",
)

ORIENTATION_CHART_SLICE_2 = SliceConstraintSpec(
    name="orientation_chart_coordinate_2",
    role=SliceRole.TASK,
    formula="h2(R)=c2",
    parameter_name="c2",
    target_space="SO(3)",
    rationale="Second independent task coordinate leaving a one-dimensional orientation leaf.",
)

REDUNDANCY_GAUGE_SLICE = SliceConstraintSpec(
    name="redundancy_gauge",
    role=SliceRole.REDUNDANCY,
    formula="r(q)=ρ",
    parameter_name="rho",
    target_space="configuration self-motion",
    rationale=(
        "Select one internal self-motion level without pretending it is an orientation coordinate."
    ),
)


DEFAULT_FIBER_SPECS: tuple[FiberFamilySpec, ...] = (
    FiberFamilySpec(
        rung=LadderRung.L3,
        parent_id="planar_3r_fixed_position_component",
        parent_dimension=1,
        constraints=(),
        source_fiber_dimension=1,
        candidate_child_family="planar 4R",
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.EXACT_GLOBAL,
        reconstruction_target="SO(2)",
        notes=("Trusted calibration leaf; no additional slicing required.",),
    ),
    FiberFamilySpec(
        rung=LadderRung.L4,
        parent_id="spatial_4r_fixed_position_component",
        parent_dimension=1,
        constraints=(),
        source_fiber_dimension=1,
        candidate_child_family="architecture-dependent spatial four-bar",
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.LOCAL_ONLY,
        reconstruction_target="Y1 ⊂ SO(3)",
        notes=(
            (
                "Catalog status LOCAL_ONLY is scoped to the budget-limited traced arc of "
                "proximal exact_u_pair_4r; complete component correspondence is unverified."
            ),
            (
                "generic_4r, near-aligned, and non-proximal architectures remain unresolved "
                "or rejected for closed-mechanism equivalence."
            ),
        ),
    ),
    FiberFamilySpec(
        rung=LadderRung.L5,
        parent_id="spatial_5r_pointing_parent",
        parent_dimension=2,
        constraints=(POINTING_LATITUDE_SLICE,),
        source_fiber_dimension=1,
        candidate_child_family="candidate UUUR/UURU/URUU/USRR/URSR/URRS corpus",
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.UNRESOLVED,
        reconstruction_target="S^2 pointing image",
        notes=(
            "V06E source-fiber paint; coverage comparison unevaluable without COVERED cells (ADR-043).",
            "Reconstruction still required before reconstruction claims (Gate K2).",
        ),
    ),
    FiberFamilySpec(
        rung=LadderRung.L6,
        parent_id="spatial_6r_orientation_parent",
        parent_dimension=3,
        constraints=(ORIENTATION_CHART_SLICE_1, ORIENTATION_CHART_SLICE_2),
        source_fiber_dimension=1,
        candidate_child_family="architecture-dependent one-DOF leaf",
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=CertificateStatus.UNRESOLVED,
        reconstruction_target="SO(3) orientation image",
        notes=(
            "V07 architecture-scoped scaffold; no L4 component certificate is inherited.",
            "Requires frozen V07 decomposition-free SO(3) reference before reconstruction claims (Gate K3).",
        ),
    ),
    FiberFamilySpec(
        rung=LadderRung.L7,
        parent_id="spatial_7r_orientation_redundancy_parent",
        parent_dimension=4,
        constraints=(
            REDUNDANCY_GAUGE_SLICE,
            ORIENTATION_CHART_SLICE_1,
            ORIENTATION_CHART_SLICE_2,
        ),
        source_fiber_dimension=1,
        candidate_child_family="architecture-dependent one-DOF leaf",
        process_status=ProcessStatus.BLOCKED,
        certificate_status=CertificateStatus.UNRESOLVED,
        reconstruction_target="SO(3) coverage with nonempty redundancy fibers",
        notes=("Deferred pending multi-component certificates beyond proximal exact-U gate.",),
    ),
)


def rung_spec(rung: LadderRung | str) -> RungSpec:
    """Return one registered rung by enum or string value."""

    resolved = LadderRung(rung)
    for spec in RUNG_SPECS:
        if spec.rung is resolved:
            return spec
    raise KeyError(resolved.value)


def program_payload() -> dict[str, Any]:
    """Return the complete machine-readable scaffold for readouts."""

    return {
        "program": "decomposition_ladder_L3_L7_scaffold",
        "active_sequence": "docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md",
        "scaffold_status": "optional_subordinate_to_V05_V09",
        "rungs": [spec.to_dict() for spec in RUNG_SPECS],
        "parent_child_families": [spec.to_dict() for spec in PARENT_CHILD_FAMILIES],
        "default_fiber_specs": [spec.to_dict() for spec in DEFAULT_FIBER_SPECS],
        "guardrails": [
            "V05–V09 remains the active scientific sequence; this ladder is an optional scaffold.",
            "Construct and validate the source parent before proposing child mechanisms.",
            "A one-dimensional level-set fiber is not automatically a known four-bar family.",
            "Letter/mobility families are candidate corpus entries, not certified parents.",
            "Preserve axis_aggregation_status vs closed_mechanism_status (ADR-021).",
            "Drive continuation arclength s by default; alpha(s) and beta(s) are outputs.",
            "Prescribe alpha or beta only where that coordinate is a regular local chart.",
            "Promote source_chain_evidence only from an accepted closed-mechanism certificate.",
            "L7 remains BLOCKED pending multi-component / nested-slice certificate work.",
        ],
    }
