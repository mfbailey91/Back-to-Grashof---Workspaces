"""Typed contracts for the L3-L7 kinematic-decomposition ladder scaffold.

The ladder separates five objects that were previously easy to conflate:

1. the fixed-position source parent;
2. task- or redundancy-derived scalar slices;
3. one-dimensional source fibers;
4. candidate one-DOF closed-mechanism children;
5. task-image reconstruction from the accepted children.

Process/scaffold labels are never certificate statuses. A child family is never
promoted to source-chain evidence without an accepted closed-mechanism
certificate status (ADR-021 split preserved).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class LadderRung(str, Enum):
    """Dimension ladder identifier."""

    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"
    L7 = "L7"


class SliceRole(str, Enum):
    """Why a scalar level-set constraint is introduced."""

    TASK = "task"
    REDUNDANCY = "redundancy"


class DriveMode(str, Enum):
    """How a one-DOF leaf mechanism is parameterized numerically."""

    FREE_BRANCH = "free_branch"
    TASK_DERIVED_FIBER = "task_derived_fiber"
    PRESCRIBED_ALPHA = "prescribed_alpha"
    PRESCRIBED_BETA = "prescribed_beta"


class ProcessStatus(str, Enum):
    """Scaffold / program-process labels. Never used as certificate statuses."""

    PLANNED = "PLANNED"
    SCAFFOLD = "SCAFFOLD"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class CertificateStatus(str, Enum):
    """DecompositionCertificate taxonomy (rule 7 / ADR-021)."""

    EXACT_GLOBAL = "EXACT_GLOBAL"
    EXACT_ON_COMPONENT = "EXACT_ON_COMPONENT"
    LOCAL_ONLY = "LOCAL_ONLY"
    APPROXIMATE = "APPROXIMATE"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


_ACCEPTED_CLOSED = {
    CertificateStatus.EXACT_GLOBAL,
    CertificateStatus.EXACT_ON_COMPONENT,
}


@dataclass(frozen=True, slots=True)
class RungSpec:
    """One rung of the source-parent-to-one-DOF-leaf program."""

    rung: LadderRung
    source_chain: str
    n_joints: int
    position_dimension: int
    fixed_position_mobility: int
    target_label: str
    target_dimension: int
    task_slice_count: int
    redundancy_slice_count: int
    direct_leaf: bool
    active_question: str
    process_status: ProcessStatus = ProcessStatus.SCAFFOLD
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        expected_mobility = self.n_joints - self.position_dimension
        if self.fixed_position_mobility != expected_mobility:
            raise ValueError(
                "fixed_position_mobility must equal n_joints - position_dimension "
                f"({expected_mobility})"
            )
        expected_slices = max(0, self.fixed_position_mobility - 1)
        actual_slices = self.task_slice_count + self.redundancy_slice_count
        if actual_slices != expected_slices:
            raise ValueError(
                "task_slice_count + redundancy_slice_count must reduce the parent "
                f"to one dimension ({expected_slices} required, got {actual_slices})"
            )
        if self.direct_leaf != (self.fixed_position_mobility == 1):
            raise ValueError("direct_leaf must be true exactly for one-DOF parents")
        if self.target_dimension < 1:
            raise ValueError("target_dimension must be positive")

    @property
    def total_slice_count(self) -> int:
        return self.task_slice_count + self.redundancy_slice_count

    @property
    def leaf_dimension(self) -> int:
        return self.fixed_position_mobility - self.total_slice_count

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rung"] = self.rung.value
        payload["process_status"] = self.process_status.value
        return payload


JOINT_ROLE_DOF: dict[str, int] = {
    "R_phys": 1,
    "U_phys": 2,
    "S_phys": 3,
    "U_v": 2,
    "S_v": 3,
}


def loop_mobility(joint_role_sequence: tuple[str, ...]) -> int:
    """Return generic single-loop spatial mobility ``sum(f_i) - 6``.

    This count is a regular generic mobility check, not a proof of assemblability,
    component topology, or task equivalence.
    """

    try:
        freedoms = [JOINT_ROLE_DOF[role] for role in joint_role_sequence]
    except KeyError as exc:
        raise ValueError(f"unknown joint role {exc.args[0]!r}") from exc
    return sum(freedoms) - 6


@dataclass(frozen=True, slots=True)
class ParentChildFamilySpec:
    """Candidate L5 letter-family test corpus entry (not a certified equivalence)."""

    parent_label: str
    child_label: str
    parent_joint_kinds: tuple[str, str, str, str]
    child_joint_kinds: tuple[str, str, str, str]
    parent_joint_roles: tuple[str, str, str, str]
    child_joint_roles: tuple[str, str, str, str]
    source_pattern: str
    candidate_corpus_status: ProcessStatus = ProcessStatus.PLANNED
    axis_aggregation_status: CertificateStatus = CertificateStatus.UNRESOLVED
    closed_mechanism_status: CertificateStatus = CertificateStatus.UNRESOLVED
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.parent_joint_kinds) != len(self.parent_joint_roles):
            raise ValueError("parent kinds and roles must have equal length")
        if len(self.child_joint_kinds) != len(self.child_joint_roles):
            raise ValueError("child kinds and roles must have equal length")
        if self.parent_joint_roles[0] != "S_v":
            raise ValueError("parent must retain S_v as the semantic origin")
        if self.child_joint_roles[0] != "U_v":
            raise ValueError("child must begin with task-derived U_v")
        if self.parent_mobility != 2:
            raise ValueError(f"parent {self.parent_label} must have mobility 2")
        if self.child_mobility != 1:
            raise ValueError(f"child {self.child_label} must have mobility 1")

    @property
    def parent_mobility(self) -> int:
        return loop_mobility(self.parent_joint_roles)

    @property
    def child_mobility(self) -> int:
        return loop_mobility(self.child_joint_roles)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["parent_mobility"] = self.parent_mobility
        payload["child_mobility"] = self.child_mobility
        payload["candidate_corpus_status"] = self.candidate_corpus_status.value
        payload["axis_aggregation_status"] = self.axis_aggregation_status.value
        payload["closed_mechanism_status"] = self.closed_mechanism_status.value
        return payload


@dataclass(frozen=True, slots=True)
class SliceConstraintSpec:
    """A named scalar level-set constraint used to lower parent dimension."""

    name: str
    role: SliceRole
    formula: str
    parameter_name: str
    target_space: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["role"] = self.role.value
        return payload


@dataclass(frozen=True, slots=True)
class FiberFamilySpec:
    """Definition of one family of one-dimensional level-set fibers."""

    rung: LadderRung
    parent_id: str
    parent_dimension: int
    constraints: tuple[SliceConstraintSpec, ...]
    source_fiber_dimension: int
    candidate_child_family: str | None
    process_status: ProcessStatus
    certificate_status: CertificateStatus
    reconstruction_target: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        expected_dimension = self.parent_dimension - len(self.constraints)
        if self.source_fiber_dimension != expected_dimension:
            raise ValueError(
                "source_fiber_dimension must equal parent_dimension - constraint_count "
                f"({expected_dimension})"
            )
        if self.source_fiber_dimension != 1:
            raise ValueError("the leaf-engine contract requires one-dimensional fibers")

    def to_dict(self) -> dict[str, Any]:
        return {
            "rung": self.rung.value,
            "parent_id": self.parent_id,
            "parent_dimension": self.parent_dimension,
            "constraints": [constraint.to_dict() for constraint in self.constraints],
            "source_fiber_dimension": self.source_fiber_dimension,
            "candidate_child_family": self.candidate_child_family,
            "process_status": self.process_status.value,
            "certificate_status": self.certificate_status.value,
            "reconstruction_target": self.reconstruction_target,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class UDriveContract:
    """Explicit meaning of "drive" for the two coordinates inside a U joint."""

    mode: DriveMode
    branch_parameter: str
    commanded_coordinate: str | None
    solved_coordinates: tuple[str, ...]
    valid_when: str
    fallback: str
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        return payload


@dataclass(frozen=True, slots=True)
class SourceParentRecord:
    """One fixed-position source parent before additional scalar slices."""

    rung: LadderRung
    parent_id: str
    source_chain_id: str
    task_point: tuple[float, ...]
    dimension: int
    target_space: str
    component_ids: tuple[str, ...]
    process_status: ProcessStatus
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.dimension < 1:
            raise ValueError("source parent dimension must be positive")
        if not self.parent_id:
            raise ValueError("parent_id must be nonempty")
        if not self.source_chain_id:
            raise ValueError("source_chain_id must be nonempty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "rung": self.rung.value,
            "parent_id": self.parent_id,
            "source_chain_id": self.source_chain_id,
            "task_point": list(self.task_point),
            "dimension": self.dimension,
            "target_space": self.target_space,
            "component_ids": list(self.component_ids),
            "process_status": self.process_status.value,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class SourceFiberRecord:
    """One one-dimensional level-set component inside a source parent."""

    rung: LadderRung
    fiber_id: str
    parent_id: str
    component_id: str
    slice_values: tuple[tuple[str, float], ...]
    branch_status: str
    returned: bool
    source_provenance: str
    sample_count: int
    task_image_status: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sample_count < 0:
            raise ValueError("sample_count must be nonnegative")
        if len({name for name, _value in self.slice_values}) != len(self.slice_values):
            raise ValueError("slice coordinate names must be unique")

    @property
    def dimension(self) -> int:
        return 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "rung": self.rung.value,
            "fiber_id": self.fiber_id,
            "parent_id": self.parent_id,
            "component_id": self.component_id,
            "slice_values": {name: value for name, value in self.slice_values},
            "dimension": self.dimension,
            "branch_status": self.branch_status,
            "returned": self.returned,
            "source_provenance": self.source_provenance,
            "sample_count": self.sample_count,
            "task_image_status": self.task_image_status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class ChildMechanismRecord:
    """Role-aware candidate one-DOF mechanism proposed for a source fiber."""

    child_id: str
    source_fiber_id: str
    family: str
    joint_kind_sequence: tuple[str, ...]
    joint_role_sequence: tuple[str, ...]
    expected_mobility: int
    geometry_provenance: str
    status: CertificateStatus
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.joint_kind_sequence) != len(self.joint_role_sequence):
            raise ValueError("joint kind and role sequences must have equal length")
        if self.expected_mobility != 1:
            raise ValueError("the current leaf engine accepts only one-DOF children")

    def to_dict(self) -> dict[str, Any]:
        return {
            "child_id": self.child_id,
            "source_fiber_id": self.source_fiber_id,
            "family": self.family,
            "joint_kind_sequence": list(self.joint_kind_sequence),
            "joint_role_sequence": list(self.joint_role_sequence),
            "expected_mobility": self.expected_mobility,
            "geometry_provenance": self.geometry_provenance,
            "status": self.status.value,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class EquivalenceCertificateRecord:
    """Component-scoped source-fiber ↔ child-mechanism comparison.

    Preserves the ADR-021 split: axis aggregation may be exact while the
    independently instantiated closed mechanism remains ``UNRESOLVED``.
    Overall ``status`` mirrors ``closed_mechanism_status``.
    """

    source_fiber_id: str
    child_id: str
    axis_aggregation_status: CertificateStatus
    closed_mechanism_status: CertificateStatus
    component_scope: str
    coordinate_map: str
    reconstruction_map: str
    closure_error: float | None
    tangent_error: float | None
    task_map_error: float | None
    reason: str

    def __post_init__(self) -> None:
        for name, value in (
            ("closure_error", self.closure_error),
            ("tangent_error", self.tangent_error),
            ("task_map_error", self.task_map_error),
        ):
            if value is not None and value < 0.0:
                raise ValueError(f"{name} must be nonnegative or None")

    @property
    def status(self) -> CertificateStatus:
        """Overall disposition equals closed-mechanism status (ADR-021)."""

        return self.closed_mechanism_status

    @property
    def accepted_for_reconstruction(self) -> bool:
        return self.closed_mechanism_status in _ACCEPTED_CLOSED

    def to_decomposition_certificate_dict(self) -> dict[str, Any]:
        """Emit the status fields expected by ``DecompositionCertificate``."""

        return {
            "axis_aggregation_status": self.axis_aggregation_status.value,
            "closed_mechanism_status": self.closed_mechanism_status.value,
            "status": self.status.value,
            "source_fiber_id": self.source_fiber_id,
            "child_id": self.child_id,
            "component_scope": self.component_scope,
            "coordinate_map": self.coordinate_map,
            "inverse_or_reconstruction_map": self.reconstruction_map,
            "closure_residuals": {
                "closure_error": self.closure_error,
            },
            "tangent_subspace_error": self.tangent_error,
            "trajectory_pointing_error": self.task_map_error,
            "failure_or_scope_reason": self.reason,
            "accepted_for_reconstruction": self.accepted_for_reconstruction,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_fiber_id": self.source_fiber_id,
            "child_id": self.child_id,
            "axis_aggregation_status": self.axis_aggregation_status.value,
            "closed_mechanism_status": self.closed_mechanism_status.value,
            "status": self.status.value,
            "component_scope": self.component_scope,
            "coordinate_map": self.coordinate_map,
            "reconstruction_map": self.reconstruction_map,
            "closure_error": self.closure_error,
            "tangent_error": self.tangent_error,
            "task_map_error": self.task_map_error,
            "reason": self.reason,
            "accepted_for_reconstruction": self.accepted_for_reconstruction,
        }


@dataclass(frozen=True, slots=True)
class LeafPredicateRecord:
    """Intrinsic one-DOF child result without automatic workspace promotion."""

    child_id: str
    branch_status: str
    returned: bool
    coordinate_windings: tuple[tuple[str, int | None], ...]
    coordinate_ranges: tuple[tuple[str, float | None], ...]
    minimum_singularity_margin: float | None
    evidence_scope: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_singularity_margin is not None and self.minimum_singularity_margin < 0.0:
            raise ValueError("minimum_singularity_margin must be nonnegative or None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "child_id": self.child_id,
            "branch_status": self.branch_status,
            "returned": self.returned,
            "coordinate_windings": dict(self.coordinate_windings),
            "coordinate_ranges": dict(self.coordinate_ranges),
            "minimum_singularity_margin": self.minimum_singularity_margin,
            "evidence_scope": self.evidence_scope,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class ReconstructionRecord:
    """Comparison of fiber-family reconstruction against direct parent truth."""

    rung: LadderRung
    parent_id: str
    target_space: str
    accepted_fiber_ids: tuple[str, ...]
    unresolved_fiber_ids: tuple[str, ...]
    direct_coverage_status: str
    reconstructed_coverage_status: str
    comparison_error: float | None
    process_status: ProcessStatus
    certificate_status: CertificateStatus
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.comparison_error is not None and self.comparison_error < 0.0:
            raise ValueError("comparison_error must be nonnegative or None")
        overlap = set(self.accepted_fiber_ids) & set(self.unresolved_fiber_ids)
        if overlap:
            raise ValueError(f"fibers cannot be both accepted and unresolved: {sorted(overlap)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "rung": self.rung.value,
            "parent_id": self.parent_id,
            "target_space": self.target_space,
            "accepted_fiber_ids": list(self.accepted_fiber_ids),
            "unresolved_fiber_ids": list(self.unresolved_fiber_ids),
            "direct_coverage_status": self.direct_coverage_status,
            "reconstructed_coverage_status": self.reconstructed_coverage_status,
            "comparison_error": self.comparison_error,
            "process_status": self.process_status.value,
            "certificate_status": self.certificate_status.value,
            "notes": list(self.notes),
        }
