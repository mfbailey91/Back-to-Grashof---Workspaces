"""Immutable R3A records, process/reconstruction enums, and frozen config loader.

Conventions
-----------
- Lengths in metres, angles in radians.
- Tool point ``p_star`` and pointing ``d`` are world-frame.
- Undefined metrics serialize as JSON ``null``, never ``NaN`` or fabricated zeros.
- Process labels (``PLANNED``, ``SCAFFOLD``, …) are not ``DecompositionCertificate``
  statuses.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import Any

Vec3 = tuple[float, float, float]
Mat3 = tuple[Vec3, Vec3, Vec3]

ACCEPTED_CHILD_STATUSES = frozenset({"EXACT_GLOBAL", "EXACT_ON_COMPONENT"})
PROCESS_STAGE_NAMES = (
    "manifest",
    "fixture",
    "truth",
    "source-control",
    "leaves",
    "compare",
    "render",
)


class ProcessStageStatus(str, Enum):
    """CLI/process label. Not a decomposition certificate."""

    PLANNED = "PLANNED"
    SCAFFOLD = "SCAFFOLD"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True, slots=True)
class StageArtifactRef:
    stage: str
    path: str
    sha256: str
    config_hash: str
    mode: str
    probe_ids: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "stage": self.stage,
                "path": self.path,
                "sha256": self.sha256,
                "config_hash": self.config_hash,
                "mode": self.mode,
                "probe_ids": list(self.probe_ids),
            }
        )


@dataclass(frozen=True, slots=True)
class StageResult:
    stage: str
    stage_status: ProcessStageStatus
    scientific_disposition: str
    config_hash: str
    mode: str
    probe_ids: tuple[str, ...]
    inputs: tuple[StageArtifactRef, ...]
    outputs: tuple[StageArtifactRef, ...]
    limitations: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "stage": self.stage,
                "stage_status": self.stage_status.value,
                "scientific_disposition": self.scientific_disposition,
                "config_hash": self.config_hash,
                "mode": self.mode,
                "probe_ids": list(self.probe_ids),
                "inputs": [item.to_json_dict() for item in self.inputs],
                "outputs": [item.to_json_dict() for item in self.outputs],
                "limitations": list(self.limitations),
            }
        )


class PointingSolveStatus(str, Enum):
    FOUND = "FOUND"
    NOT_FOUND_AT_DECLARED_BUDGET = "NOT_FOUND_AT_DECLARED_BUDGET"
    UNRESOLVED = "UNRESOLVED"


class LeafConstructionKind(str, Enum):
    TASK_LEVEL_SET_CONTROL = "task_level_set_control"
    VIRTUAL_ORIENTATION_COORDINATE = "virtual_orientation_coordinate"
    SEED_DERIVED_DIAGNOSTIC = "seed_derived_diagnostic"


class ReconstructionDisposition(str, Enum):
    PASS_AT_DECLARED_RESOLUTION = "PASS_AT_DECLARED_RESOLUTION"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


class FamilyAdmissibilityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"


class LeafPairStatus(str, Enum):
    DUPLICATE_SAME_COMPONENT = "DUPLICATE_SAME_COMPONENT"
    DISTINCT_COMPATIBLE = "DISTINCT_COMPATIBLE"
    CROSSING_DIFFERENT_TANGENT = "CROSSING_DIFFERENT_TANGENT"
    INCOMPATIBLE_COMPONENT = "INCOMPATIBLE_COMPONENT"
    UNRESOLVED = "UNRESOLVED"


class CompletenessLabel(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    BOUNDARY = "BOUNDARY"


class OracleFeasibility(str, Enum):
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    BOUNDARY = "BOUNDARY"


class CellClass(str, Enum):
    STRICT_COVERED = "STRICT_COVERED"
    STRICT_UNCOVERED = "STRICT_UNCOVERED"
    AMBIGUOUS_BOUNDARY = "AMBIGUOUS_BOUNDARY"


def json_safe(obj: Any) -> Any:
    """Recursively replace non-finite floats with ``None``."""

    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, Enum):
        return obj.value
    if obj is True or obj is False or obj is None:
        return obj
    if type(obj).__name__ in {"bool_", "bool8"}:
        return bool(obj)
    if isinstance(obj, int) and not isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        return obj if isfinite(obj) else None
    if isinstance(obj, Path):
        return str(obj)
    return obj


def json_object(payload: dict[str, Any]) -> dict[str, Any]:
    out = json_safe(payload)
    if not isinstance(out, dict):
        raise TypeError("expected a JSON object")
    return out


def json_dumps_strict(payload: Mapping[str, Any] | dict[str, Any]) -> str:
    return json.dumps(json_object(dict(payload)), indent=2, allow_nan=False, sort_keys=True) + "\n"


def stage_envelope(
    config: CampaignConfig,
    *,
    stage: str,
    mode: str,
    probe_ids: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    return {
        "program_id": config.program_id,
        "config_hash": config.config_hash,
        "stage": stage,
        "mode": mode,
        "probe_ids": list(probe_ids),
    }


def _as_vec3(values: Any, *, name: str) -> Vec3:
    arr = list(values)
    if len(arr) != 3:
        raise ValueError(f"{name} must have length 3")
    out = (float(arr[0]), float(arr[1]), float(arr[2]))
    if any(not isfinite(v) for v in out):
        raise ValueError(f"{name} must be finite")
    return out


def _as_mat3(values: Any, *, name: str) -> Mat3:
    rows = list(values)
    if len(rows) != 3:
        raise ValueError(f"{name} must be 3x3")
    return (_as_vec3(rows[0], name=f"{name}[0]"), _as_vec3(rows[1], name=f"{name}[1]"), _as_vec3(rows[2], name=f"{name}[2]"))


def config_sha256(raw: Mapping[str, Any]) -> str:
    blob = json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True, slots=True)
class L5PositiveControlGeometry:
    """Unrestricted idealized ``U_shoulder-R_elbow-U_wrist`` 5R."""

    architecture_id: str
    L1: float
    L2: float
    tool_offset: float
    r_min: float
    r_max: float
    home_pointing: Vec3
    home_wrist_center: Vec3
    home_tool_point: Vec3
    parent_family: str
    parent_joint_roles: tuple[str, ...]
    natural_child_family: str
    natural_child_joint_roles: tuple[str, ...]
    joint_limits: str

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "architecture_id": self.architecture_id,
                "L1": self.L1,
                "L2": self.L2,
                "tool_offset": self.tool_offset,
                "r_min": self.r_min,
                "r_max": self.r_max,
                "home_pointing": list(self.home_pointing),
                "home_wrist_center": list(self.home_wrist_center),
                "home_tool_point": list(self.home_tool_point),
                "parent_family": self.parent_family,
                "parent_joint_roles": list(self.parent_joint_roles),
                "natural_child_family": self.natural_child_family,
                "natural_child_joint_roles": list(self.natural_child_joint_roles),
                "joint_limits": self.joint_limits,
            }
        )


@dataclass(frozen=True, slots=True)
class FixedPointProbe:
    probe_id: str
    p_star: Vec3
    rho: float
    expected_pointing_complete: bool
    limiting_boundary: str
    analytical_margin_m: float
    seed_pointing_policy: str
    seed_configuration: tuple[float, ...] | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "probe_id": self.probe_id,
                "p_star": list(self.p_star),
                "rho": self.rho,
                "expected_pointing_complete": self.expected_pointing_complete,
                "limiting_boundary": self.limiting_boundary,
                "analytical_margin_m": self.analytical_margin_m,
                "seed_pointing_policy": self.seed_pointing_policy,
                "seed_configuration": None if self.seed_configuration is None else list(self.seed_configuration),
            }
        )


@dataclass(frozen=True, slots=True)
class AnalyticalDirectionOracleResult:
    p_star: Vec3
    d_target: Vec3
    wrist: Vec3
    wrist_radius: float
    feasibility: OracleFeasibility
    margin_m: float
    formula: str = "r_min <= norm(p_star - tool_offset * d_target) <= r_max"

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "p_star": list(self.p_star),
                "d_target": list(self.d_target),
                "wrist": list(self.wrist),
                "wrist_radius": self.wrist_radius,
                "feasibility": self.feasibility.value,
                "feasible": self.feasibility is OracleFeasibility.FEASIBLE,
                "margin_m": self.margin_m,
                "formula": self.formula,
            }
        )


@dataclass(frozen=True, slots=True)
class AnalyticalPointingCompletenessResult:
    p_star: Vec3
    rho: float
    inner_margin_m: float
    outer_margin_m: float
    label: CompletenessLabel
    complete: bool
    formula: str = "abs(rho-tool_offset) >= r_min and rho+tool_offset <= r_max"

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "p_star": list(self.p_star),
                "rho": self.rho,
                "inner_margin_m": self.inner_margin_m,
                "outer_margin_m": self.outer_margin_m,
                "label": self.label.value,
                "complete": self.complete,
                "formula": self.formula,
            }
        )


@dataclass(frozen=True, slots=True)
class PointingSolutionCluster:
    cluster_id: str
    q_representative: tuple[float, ...]
    members: tuple[tuple[float, ...], ...]
    seed_sources: tuple[str, ...]
    position_residual_m: float
    pointing_geodesic_rad: float

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "cluster_id": self.cluster_id,
                "q_representative": list(self.q_representative),
                "members": [list(m) for m in self.members],
                "seed_sources": list(self.seed_sources),
                "position_residual_m": self.position_residual_m,
                "pointing_geodesic_rad": self.pointing_geodesic_rad,
            }
        )


@dataclass(frozen=True, slots=True)
class PointingTargetSolve:
    target_index: int
    d_target: Vec3
    status: PointingSolveStatus
    clusters: tuple[PointingSolutionCluster, ...]
    best_position_residual_m: float | None
    best_pointing_geodesic_rad: float | None
    n_starts: int
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "target_index": self.target_index,
                "d_target": list(self.d_target),
                "status": self.status.value,
                "clusters": [c.to_json_dict() for c in self.clusters],
                "best_position_residual_m": self.best_position_residual_m,
                "best_pointing_geodesic_rad": self.best_pointing_geodesic_rad,
                "n_starts": self.n_starts,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class DirectReferenceCell:
    cell_id: str
    vertex_or_barycenter_direction: Vec3
    oracle_status: OracleFeasibility
    direct_status: PointingSolveStatus
    direct_cluster_count: int
    best_position_residual_m: float | None
    best_pointing_error_rad: float | None
    strict_reference_eligible: bool

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "cell_id": self.cell_id,
                "vertex_or_barycenter_direction": list(self.vertex_or_barycenter_direction),
                "oracle_status": self.oracle_status.value,
                "direct_status": self.direct_status.value,
                "direct_cluster_count": self.direct_cluster_count,
                "best_position_residual_m": self.best_position_residual_m,
                "best_pointing_error_rad": self.best_pointing_error_rad,
                "strict_reference_eligible": self.strict_reference_eligible,
            }
        )

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, Any]) -> DirectReferenceCell:
        return cls(
            cell_id=str(payload["cell_id"]),
            vertex_or_barycenter_direction=_as_vec3(
                payload["vertex_or_barycenter_direction"], name="vertex_or_barycenter_direction"
            ),
            oracle_status=OracleFeasibility(str(payload["oracle_status"])),
            direct_status=PointingSolveStatus(str(payload["direct_status"])),
            direct_cluster_count=int(payload["direct_cluster_count"]),
            best_position_residual_m=(
                None
                if payload.get("best_position_residual_m") is None
                else float(payload["best_position_residual_m"])
            ),
            best_pointing_error_rad=(
                None
                if payload.get("best_pointing_error_rad") is None
                else float(payload["best_pointing_error_rad"])
            ),
            strict_reference_eligible=bool(payload["strict_reference_eligible"]),
        )


@dataclass(frozen=True, slots=True)
class DirectPointingTruth:
    probe_id: str
    split: str
    icosphere_level: int
    solves: tuple[PointingTargetSolve, ...]
    found_count: int
    not_found_count: int
    unresolved_count: int

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "probe_id": self.probe_id,
                "split": self.split,
                "icosphere_level": self.icosphere_level,
                "solves": [s.to_json_dict() for s in self.solves],
                "found_count": self.found_count,
                "not_found_count": self.not_found_count,
                "unresolved_count": self.unresolved_count,
                "certificate_status": None,
            }
        )


@dataclass(frozen=True, slots=True)
class SphericalClosureChartRecord:
    chart_id: str
    sequence: str
    basis: Mat3
    reference: Mat3
    singularity_tol: float

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "chart_id": self.chart_id,
                "sequence": self.sequence,
                "basis": [list(row) for row in self.basis],
                "reference": [list(row) for row in self.reference],
                "singularity_tol": self.singularity_tol,
            }
        )


@dataclass(frozen=True, slots=True)
class NaturalLeafSpec:
    leaf_id: str
    probe_id: str
    construction_kind: LeafConstructionKind
    chart_id: str
    lambda_fixed: float
    p_star: Vec3
    geometry_hash: str
    joint_kind_sequence: tuple[str, ...]
    joint_role_sequence: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "leaf_id": self.leaf_id,
                "probe_id": self.probe_id,
                "construction_kind": self.construction_kind.value,
                "chart_id": self.chart_id,
                "lambda_fixed": self.lambda_fixed,
                "p_star": list(self.p_star),
                "geometry_hash": self.geometry_hash,
                "joint_kind_sequence": list(self.joint_kind_sequence),
                "joint_role_sequence": list(self.joint_role_sequence),
            }
        )


@dataclass(frozen=True, slots=True)
class NaturalLeafSample:
    s: float
    x: tuple[float, ...]
    q_source: tuple[float, ...]
    pointing: Vec3
    lambda_recovered: float
    closure_residual: float
    position_residual_m: float
    orientation_error_rad: float
    pointing_error_rad: float
    joint_lift_error_rad: float
    family_coordinate_error_rad: float
    rank_j: int
    nullity_j: int
    chart_singularity: bool

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "s": self.s,
                "x": list(self.x),
                "q_source": list(self.q_source),
                "pointing": list(self.pointing),
                "lambda_recovered": self.lambda_recovered,
                "closure_residual": self.closure_residual,
                "position_residual_m": self.position_residual_m,
                "orientation_error_rad": self.orientation_error_rad,
                "pointing_error_rad": self.pointing_error_rad,
                "joint_lift_error_rad": self.joint_lift_error_rad,
                "family_coordinate_error_rad": self.family_coordinate_error_rad,
                "rank_j": self.rank_j,
                "nullity_j": self.nullity_j,
                "chart_singularity": self.chart_singularity,
            }
        )


@dataclass(frozen=True, slots=True)
class ReseedAttempt:
    reseed_id: str
    seed_s: float
    lambda_error_rad: float | None
    symmetric_wrapped_q_distance_rad: float | None
    symmetric_pointing_distance_rad: float | None
    tangent_error: float | None
    returned_match: bool | None
    branch_status_match: bool | None
    component_identity: bool | None
    status: str
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "reseed_id": self.reseed_id,
                "seed_s": self.seed_s,
                "lambda_error_rad": self.lambda_error_rad,
                "symmetric_wrapped_q_distance_rad": self.symmetric_wrapped_q_distance_rad,
                "symmetric_pointing_distance_rad": self.symmetric_pointing_distance_rad,
                "tangent_error": self.tangent_error,
                "returned_match": self.returned_match,
                "branch_status_match": self.branch_status_match,
                "component_identity": self.component_identity,
                "status": self.status,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class ReseedAudit:
    status: str
    n_reseeds: int
    max_symmetric_q_distance_rad: float | None
    max_pointing_distance_rad: float | None
    notes: tuple[str, ...] = ()
    attempts: tuple[ReseedAttempt, ...] = ()
    max_tangent_error: float | None = None
    all_component_ids_match: bool | None = None

    @property
    def reseed_status(self) -> str:
        return self.status

    @property
    def max_symmetric_pointing_distance_rad(self) -> float | None:
        return self.max_pointing_distance_rad

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "status": self.status,
                "reseed_status": self.status,
                "n_reseeds": self.n_reseeds,
                "max_symmetric_q_distance_rad": self.max_symmetric_q_distance_rad,
                "max_pointing_distance_rad": self.max_pointing_distance_rad,
                "max_symmetric_pointing_distance_rad": self.max_pointing_distance_rad,
                "max_tangent_error": self.max_tangent_error,
                "all_component_ids_match": self.all_component_ids_match,
                "attempts": [item.to_json_dict() for item in self.attempts],
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class TransversalityAudit:
    status: str
    sigma_min: float | None
    rank_span: int | None
    notes: tuple[str, ...] = ()
    leaf_id_a: str | None = None
    leaf_id_b: str | None = None
    lambda_a: float | None = None
    lambda_b: float | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "status": self.status,
                "sigma_min": self.sigma_min,
                "rank_span": self.rank_span,
                "leaf_id_a": self.leaf_id_a,
                "leaf_id_b": self.leaf_id_b,
                "lambda_a": self.lambda_a,
                "lambda_b": self.lambda_b,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class ChartOverlapAudit:
    status: str
    source_q_correspondence: bool | None = None
    recovered_rotation_correspondence: bool | None = None
    chart_coordinate_transform: bool | None = None
    family_parameter_correspondence: bool | None = None
    component_identity: bool | None = None
    pointing_set_correspondence: bool | None = None
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "status": self.status,
                "source_q_correspondence": self.source_q_correspondence,
                "recovered_rotation_correspondence": self.recovered_rotation_correspondence,
                "chart_coordinate_transform": self.chart_coordinate_transform,
                "family_parameter_correspondence": self.family_parameter_correspondence,
                "component_identity": self.component_identity,
                "pointing_set_correspondence": self.pointing_set_correspondence,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class NaturalLeafCertificate:
    spec: NaturalLeafSpec
    construction_status: str
    leaf_component_status: str
    family_admissibility_status: FamilyAdmissibilityStatus
    component_scope: str
    branch_status: str
    returned: bool
    samples: tuple[NaturalLeafSample, ...]
    max_closure_residual: float | None
    max_position_residual_m: float | None
    max_orientation_error_rad: float | None
    max_pointing_error_rad: float | None
    max_joint_lift_error_rad: float | None
    max_family_coordinate_error_rad: float | None
    reseed: ReseedAudit | None
    transversality: TransversalityAudit | None
    chart_overlap_status: str
    accepted_for_reconstruction: bool
    failure_or_scope_reason: str

    @property
    def closed_mechanism_status(self) -> str:
        return self.leaf_component_status

    def to_json_dict(self) -> dict[str, Any]:
        payload = {
            "spec": self.spec.to_json_dict(),
            "construction_kind": self.spec.construction_kind.value,
            "chart_id": self.spec.chart_id,
            "family_parameter_name": "lambda",
            "family_parameter_value": self.spec.lambda_fixed,
            "child_family": "UURU",
            "joint_kind_sequence": list(self.spec.joint_kind_sequence),
            "joint_role_sequence": list(self.spec.joint_role_sequence),
            "geometry_hash": self.spec.geometry_hash,
            "construction_status": self.construction_status,
            "leaf_component_status": self.leaf_component_status,
            "closed_mechanism_status": self.leaf_component_status,
            "family_admissibility_status": self.family_admissibility_status.value,
            "component_scope": self.component_scope,
            "branch_status": self.branch_status,
            "returned": self.returned,
            "sample_count": len(self.samples),
            "samples": [s.to_json_dict() for s in self.samples],
            "max_closure_residual": self.max_closure_residual,
            "max_position_residual_m": self.max_position_residual_m,
            "max_orientation_error_rad": self.max_orientation_error_rad,
            "max_pointing_error_rad": self.max_pointing_error_rad,
            "max_joint_lift_error_rad": self.max_joint_lift_error_rad,
            "max_family_coordinate_error_rad": self.max_family_coordinate_error_rad,
            "reseed": None if self.reseed is None else self.reseed.to_json_dict(),
            "transversality": None if self.transversality is None else self.transversality.to_json_dict(),
            "chart_overlap_status": self.chart_overlap_status,
            "accepted_for_reconstruction": self.accepted_for_reconstruction,
            "failure_or_scope_reason": self.failure_or_scope_reason,
        }
        return json_object(payload)


@dataclass(frozen=True, slots=True)
class LeafFamilyResult:
    probe_id: str
    leaves: tuple[NaturalLeafCertificate, ...]
    accepted_count: int
    duplicate_count: int
    chart_overlap_status: str
    unresolved_lambda_intervals: tuple[tuple[float, float], ...]
    notes: tuple[str, ...] = ()
    neighbor_audits: tuple[TransversalityAudit, ...] = ()
    chart_overlap: ChartOverlapAudit | None = None
    duplicate_classifications: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "probe_id": self.probe_id,
                "leaves": [leaf.to_json_dict() for leaf in self.leaves],
                "accepted_count": self.accepted_count,
                "duplicate_count": self.duplicate_count,
                "chart_overlap_status": self.chart_overlap_status,
                "unresolved_lambda_intervals": [list(iv) for iv in self.unresolved_lambda_intervals],
                "neighbor_audits": [item.to_json_dict() for item in self.neighbor_audits],
                "chart_overlap": None if self.chart_overlap is None else self.chart_overlap.to_json_dict(),
                "duplicate_classifications": list(self.duplicate_classifications),
                "notes": list(self.notes),
                "certificate_status": None,
            }
        )


@dataclass(frozen=True, slots=True)
class PointingSetMetrics:
    strict_covered_count: int
    strict_uncovered_count: int
    reconstructed_hit_count: int
    missed_covered_fraction: float | None
    false_positive_fraction: float | None
    hausdorff_rad: float | None
    boundary_disagreement_fraction: float | None
    unresolved_fraction: float
    max_cell_diameter_rad: float
    refinement_delta: float | None

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "strict_covered_count": self.strict_covered_count,
                "strict_uncovered_count": self.strict_uncovered_count,
                "reconstructed_hit_count": self.reconstructed_hit_count,
                "missed_covered_fraction": self.missed_covered_fraction,
                "false_positive_fraction": self.false_positive_fraction,
                "hausdorff_rad": self.hausdorff_rad,
                "boundary_disagreement_fraction": self.boundary_disagreement_fraction,
                "unresolved_fraction": self.unresolved_fraction,
                "max_cell_diameter_rad": self.max_cell_diameter_rad,
                "refinement_delta": self.refinement_delta,
            }
        )


@dataclass(frozen=True, slots=True)
class ThreeWayReconstructionResult:
    probe_id: str
    oracle_complete: bool
    direct_complete: bool | None
    source_control_metrics: PointingSetMetrics | None
    natural_leaf_metrics: PointingSetMetrics | None
    point_classification: CompletenessLabel
    disposition: ReconstructionDisposition
    failure_localization: str
    excluded_child_dispositions: tuple[str, ...] = ()
    direct_vs_oracle: PointingSetMetrics | None = None
    source_vs_direct: PointingSetMetrics | None = None
    natural_vs_direct: PointingSetMetrics | None = None

    @property
    def source_vs_oracle(self) -> PointingSetMetrics | None:
        return self.source_control_metrics

    @property
    def natural_vs_oracle(self) -> PointingSetMetrics | None:
        return self.natural_leaf_metrics

    def to_json_dict(self) -> dict[str, Any]:
        def _metrics(item: PointingSetMetrics | None) -> dict[str, Any] | None:
            return None if item is None else item.to_json_dict()

        source_vs_oracle = _metrics(self.source_control_metrics)
        natural_vs_oracle = _metrics(self.natural_leaf_metrics)
        return json_object(
            {
                "probe_id": self.probe_id,
                "oracle_complete": self.oracle_complete,
                "direct_complete": self.direct_complete,
                "source_control_metrics": source_vs_oracle,
                "natural_leaf_metrics": natural_vs_oracle,
                "direct_vs_oracle": _metrics(self.direct_vs_oracle),
                "source_vs_direct": _metrics(self.source_vs_direct),
                "natural_vs_direct": _metrics(self.natural_vs_direct),
                "source_vs_oracle": source_vs_oracle,
                "natural_vs_oracle": natural_vs_oracle,
                "point_classification": self.point_classification.value,
                "disposition": self.disposition.value,
                "failure_localization": self.failure_localization,
                "excluded_child_dispositions": list(self.excluded_child_dispositions),
            }
        )


@dataclass(frozen=True, slots=True)
class FivePointCampaignResult:
    program_id: str
    config_hash: str
    probe_ids: tuple[str, ...]
    stage_statuses: dict[str, str]
    comparisons: tuple[ThreeWayReconstructionResult, ...]
    disposition: ReconstructionDisposition
    accepted_reconstruction: bool
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "program_id": self.program_id,
                "config_hash": self.config_hash,
                "probe_ids": list(self.probe_ids),
                "stage_statuses": dict(self.stage_statuses),
                "comparisons": [c.to_json_dict() for c in self.comparisons],
                "disposition": self.disposition.value,
                "accepted_reconstruction": self.accepted_reconstruction,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class CampaignMode:
    name: str
    discovery_icosphere_level: int
    confirmation_icosphere_level: int
    sobol_seed_count_per_target: int
    max_nfev_per_start: int
    source_c_value_count: int
    natural_lambda_bin_count_per_chart: int
    max_natural_leaves_per_probe: int
    reseed_samples_per_leaf: int

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "name": self.name,
                "discovery_icosphere_level": self.discovery_icosphere_level,
                "confirmation_icosphere_level": self.confirmation_icosphere_level,
                "sobol_seed_count_per_target": self.sobol_seed_count_per_target,
                "max_nfev_per_start": self.max_nfev_per_start,
                "source_c_value_count": self.source_c_value_count,
                "natural_lambda_bin_count_per_chart": self.natural_lambda_bin_count_per_chart,
                "max_natural_leaves_per_probe": self.max_natural_leaves_per_probe,
                "reseed_samples_per_leaf": self.reseed_samples_per_leaf,
            }
        )


@dataclass(frozen=True, slots=True)
class CampaignTolerances:
    axis_intersection_m: float
    axis_orthogonality_abs_dot: float
    position_residual_m: float
    pointing_geodesic_rad: float
    orientation_geodesic_rad: float
    closed_loop_residual: float
    joint_lift_error_rad: float
    family_coordinate_error_rad: float
    chart_singularity_sin_beta: float
    reseed_symmetric_q_distance_rad: float
    reseed_pointing_distance_rad: float
    minimum_transversality_sigma: float
    leaf_duplicate_distance_rad: float
    strict_analytical_boundary_margin_m: float

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "axis_intersection_m": self.axis_intersection_m,
                "axis_orthogonality_abs_dot": self.axis_orthogonality_abs_dot,
                "position_residual_m": self.position_residual_m,
                "pointing_geodesic_rad": self.pointing_geodesic_rad,
                "orientation_geodesic_rad": self.orientation_geodesic_rad,
                "closed_loop_residual": self.closed_loop_residual,
                "joint_lift_error_rad": self.joint_lift_error_rad,
                "family_coordinate_error_rad": self.family_coordinate_error_rad,
                "chart_singularity_sin_beta": self.chart_singularity_sin_beta,
                "reseed_symmetric_q_distance_rad": self.reseed_symmetric_q_distance_rad,
                "reseed_pointing_distance_rad": self.reseed_pointing_distance_rad,
                "minimum_transversality_sigma": self.minimum_transversality_sigma,
                "leaf_duplicate_distance_rad": self.leaf_duplicate_distance_rad,
                "strict_analytical_boundary_margin_m": self.strict_analytical_boundary_margin_m,
            }
        )


@dataclass(frozen=True, slots=True)
class CampaignConfig:
    program_id: str
    schema_version: str
    config_hash: str
    geometry: L5PositiveControlGeometry
    probes: tuple[FixedPointProbe, ...]
    charts: tuple[SphericalClosureChartRecord, ...]
    modes: dict[str, CampaignMode]
    tolerances: CampaignTolerances
    accepted_child_statuses: tuple[str, ...]
    sobol_scramble: bool
    sobol_seed_discovery: int
    sobol_seed_confirmation: int
    max_hausdorff_in_confirmation_cell_diameters: float
    max_missed_strict_covered_fraction: float
    max_strict_false_positive_fraction: float
    max_refinement_metric_delta: float
    raw: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "program_id": self.program_id,
                "schema_version": self.schema_version,
                "config_hash": self.config_hash,
                "geometry": self.geometry.to_json_dict(),
                "probes": [p.to_json_dict() for p in self.probes],
                "charts": [c.to_json_dict() for c in self.charts],
                "modes": {k: v.to_json_dict() for k, v in self.modes.items()},
                "tolerances": self.tolerances.to_json_dict(),
                "accepted_child_statuses": list(self.accepted_child_statuses),
            }
        )

    def probe(self, probe_id: str) -> FixedPointProbe:
        for probe in self.probes:
            if probe.probe_id == probe_id:
                return probe
        raise KeyError(probe_id)

    def mode(self, name: str) -> CampaignMode:
        if name not in self.modes:
            raise KeyError(name)
        return self.modes[name]


def empty_stage_statuses() -> dict[str, str]:
    return {name: ProcessStageStatus.PLANNED.value for name in PROCESS_STAGE_NAMES}


def empty_campaign_result(config: CampaignConfig) -> FivePointCampaignResult:
    statuses = empty_stage_statuses()
    statuses["manifest"] = ProcessStageStatus.COMPLETE.value
    return FivePointCampaignResult(
        program_id=config.program_id,
        config_hash=config.config_hash,
        probe_ids=tuple(p.probe_id for p in config.probes),
        stage_statuses=statuses,
        comparisons=(),
        disposition=ReconstructionDisposition.UNRESOLVED,
        accepted_reconstruction=False,
        notes=("Empty R3A scaffold; no accepted reconstruction.",),
    )


def load_campaign_config(path: Path | str) -> CampaignConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("campaign config must be a JSON object")
    arch = raw["source_architecture"]
    lengths = arch["link_lengths_m"]
    oracle = raw["analytical_oracle"]
    geometry = L5PositiveControlGeometry(
        architecture_id=str(arch["architecture_id"]),
        L1=float(lengths["L1"]),
        L2=float(lengths["L2"]),
        tool_offset=float(lengths["tool_offset"]),
        r_min=float(oracle["r_min_m"]),
        r_max=float(oracle["r_max_m"]),
        home_pointing=_as_vec3(arch["home_pointing"], name="home_pointing"),
        home_wrist_center=_as_vec3(arch["home_wrist_center"], name="home_wrist_center"),
        home_tool_point=_as_vec3(arch["home_tool_point"], name="home_tool_point"),
        parent_family=str(arch["parent_family"]),
        parent_joint_roles=tuple(str(x) for x in arch["parent_joint_roles"]),
        natural_child_family=str(arch["natural_child_family"]),
        natural_child_joint_roles=tuple(str(x) for x in arch["natural_child_joint_roles"]),
        joint_limits=str(arch["joint_limits"]),
    )
    probes_raw = list(raw["probes"])
    probe_ids = [str(p["probe_id"]) for p in probes_raw]
    if len(probe_ids) != len(set(probe_ids)):
        raise ValueError("duplicate probe ids in campaign config")
    probes = tuple(
        FixedPointProbe(
            probe_id=str(item["probe_id"]),
            p_star=_as_vec3(item["p_star_m"], name=f"{item['probe_id']}.p_star"),
            rho=float(item["rho_m"]),
            expected_pointing_complete=bool(item["expected_pointing_complete"]),
            limiting_boundary=str(item["limiting_boundary"]),
            analytical_margin_m=float(item["analytical_margin_m"]),
            seed_pointing_policy=str(item["seed_pointing_policy"]),
        )
        for item in probes_raw
    )
    charts = tuple(
        SphericalClosureChartRecord(
            chart_id=str(item["chart_id"]),
            sequence=str(item.get("sequence", "ZYZ")),
            basis=_as_mat3(item["basis"], name=f"{item['chart_id']}.basis"),
            reference=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            singularity_tol=float(raw["tolerances"]["chart_singularity_sin_beta"]),
        )
        for item in raw["virtual_spherical_charts"]
    )
    modes = {
        name: CampaignMode(
            name=name,
            discovery_icosphere_level=int(spec["discovery_icosphere_level"]),
            confirmation_icosphere_level=int(spec["confirmation_icosphere_level"]),
            sobol_seed_count_per_target=int(spec["sobol_seed_count_per_target"]),
            max_nfev_per_start=int(spec["max_nfev_per_start"]),
            source_c_value_count=int(spec["source_c_value_count"]),
            natural_lambda_bin_count_per_chart=int(spec["natural_lambda_bin_count_per_chart"]),
            max_natural_leaves_per_probe=int(spec["max_natural_leaves_per_probe"]),
            reseed_samples_per_leaf=int(spec["reseed_samples_per_leaf"]),
        )
        for name, spec in raw["campaign_modes"].items()
    }
    tol = raw["tolerances"]
    tolerances = CampaignTolerances(
        axis_intersection_m=float(tol["axis_intersection_m"]),
        axis_orthogonality_abs_dot=float(tol["axis_orthogonality_abs_dot"]),
        position_residual_m=float(tol["position_residual_m"]),
        pointing_geodesic_rad=float(tol["pointing_geodesic_rad"]),
        orientation_geodesic_rad=float(tol["orientation_geodesic_rad"]),
        closed_loop_residual=float(tol["closed_loop_residual"]),
        joint_lift_error_rad=float(tol["joint_lift_error_rad"]),
        family_coordinate_error_rad=float(tol["family_coordinate_error_rad"]),
        chart_singularity_sin_beta=float(tol["chart_singularity_sin_beta"]),
        reseed_symmetric_q_distance_rad=float(tol["reseed_symmetric_q_distance_rad"]),
        reseed_pointing_distance_rad=float(tol["reseed_pointing_distance_rad"]),
        minimum_transversality_sigma=float(tol["minimum_transversality_sigma"]),
        leaf_duplicate_distance_rad=float(tol["leaf_duplicate_distance_rad"]),
        strict_analytical_boundary_margin_m=float(tol["strict_analytical_boundary_margin_m"]),
    )
    accept = raw["set_acceptance"]
    repro = raw["reproducibility"]
    return CampaignConfig(
        program_id=str(raw["program_id"]),
        schema_version=str(raw["schema_version"]),
        config_hash=config_sha256(raw),
        geometry=geometry,
        probes=probes,
        charts=charts,
        modes=modes,
        tolerances=tolerances,
        accepted_child_statuses=tuple(str(x) for x in accept["accepted_child_statuses"]),
        sobol_scramble=bool(repro["sobol_scramble"]),
        sobol_seed_discovery=int(repro["sobol_seed_discovery"]),
        sobol_seed_confirmation=int(repro["sobol_seed_confirmation"]),
        max_hausdorff_in_confirmation_cell_diameters=float(
            accept["max_hausdorff_in_confirmation_cell_diameters"]
        ),
        max_missed_strict_covered_fraction=float(accept["max_missed_strict_covered_fraction"]),
        max_strict_false_positive_fraction=float(accept["max_strict_false_positive_fraction"]),
        max_refinement_metric_delta=float(accept["max_refinement_metric_delta"]),
        raw=raw,
    )
