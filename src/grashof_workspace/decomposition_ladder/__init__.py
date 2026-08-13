"""Reusable source-parent → one-DOF-leaf decomposition ladder scaffold (L3-L7).

This package is an optional scaffold subordinate to the active V05–V09 sequence in
``docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md``.
"""

from .models import (
    CertificateStatus,
    ChildMechanismRecord,
    DriveMode,
    EquivalenceCertificateRecord,
    FiberFamilySpec,
    LadderRung,
    LeafPredicateRecord,
    ParentChildFamilySpec,
    ProcessStatus,
    ReconstructionRecord,
    RungSpec,
    SliceConstraintSpec,
    SliceRole,
    SourceFiberRecord,
    SourceParentRecord,
    UDriveContract,
)
from .registry import (
    DEFAULT_FIBER_SPECS,
    PARENT_CHILD_FAMILIES,
    RUNG_SPECS,
    program_payload,
    rung_spec,
)
from .u_drive import (
    UBranchSample,
    UBranchSummary,
    choose_local_drive_coordinate,
    conceptual_branch_samples,
    free_branch_contract,
    prescribed_coordinate_contract,
    simple_drive_explanation,
    summarize_branch,
    task_derived_fiber_contract,
    u_pointing,
    u_rotation_matrix,
)

__all__ = [
    "DEFAULT_FIBER_SPECS",
    "PARENT_CHILD_FAMILIES",
    "RUNG_SPECS",
    "CertificateStatus",
    "ChildMechanismRecord",
    "DriveMode",
    "EquivalenceCertificateRecord",
    "FiberFamilySpec",
    "LadderRung",
    "LeafPredicateRecord",
    "ParentChildFamilySpec",
    "ProcessStatus",
    "ReconstructionRecord",
    "RungSpec",
    "SliceConstraintSpec",
    "SliceRole",
    "SourceFiberRecord",
    "SourceParentRecord",
    "UBranchSample",
    "UBranchSummary",
    "UDriveContract",
    "choose_local_drive_coordinate",
    "conceptual_branch_samples",
    "free_branch_contract",
    "prescribed_coordinate_contract",
    "program_payload",
    "rung_spec",
    "simple_drive_explanation",
    "summarize_branch",
    "task_derived_fiber_contract",
    "u_pointing",
    "u_rotation_matrix",
]
