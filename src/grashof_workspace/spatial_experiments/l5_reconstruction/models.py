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


class ArtifactHashDrift(ValueError):
    """Recorded SHA-256 does not match the file on disk."""


@dataclass(frozen=True, slots=True)
class StageArtifactRef:
    stage: str
    path: str
    sha256: str
    config_hash: str
    mode: str
    probe_ids: tuple[str, ...]
    schema_version: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "stage": self.stage,
                "path": self.path,
                "sha256": self.sha256,
                "config_hash": self.config_hash,
                "mode": self.mode,
                "probe_ids": list(self.probe_ids),
                "schema_version": self.schema_version,
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


class CampaignBlocker(str, Enum):
    """First failing scientific column. Not a generic PARTIAL label."""

    DIRECT_REFERENCE_BLOCKED = "DIRECT_REFERENCE_BLOCKED"
    STITCHING_CONTROL_BLOCKED = "STITCHING_CONTROL_BLOCKED"
    NATURAL_DECOMPOSITION_BLOCKED = "NATURAL_DECOMPOSITION_BLOCKED"
    CONTROLLED_COVER_ACCEPTED = "CONTROLLED_COVER_ACCEPTED"


class FamilyAdmissibilityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"


class ReseedScope(str, Enum):
    LOCAL = "LOCAL"
    RETURNED_SET = "RETURNED_SET"
    COMPONENT = "COMPONENT"


class ReseedDisposition(str, Enum):
    LOCAL_PASS = "LOCAL_PASS"
    RETURNED_SET_PASS = "RETURNED_SET_PASS"
    COMPONENT_PASS = "COMPONENT_PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"


class IntervalStatus(str, Enum):
    """Finite-domain coverage of one declared chart-by-lambda bin.

    ``SAMPLED_ADMISSIBLE`` is not a complete foliation, and is never ``COMPLETE``.
    """

    UNSAMPLED = "UNSAMPLED"
    SAMPLED_LOCAL = "SAMPLED_LOCAL"
    SAMPLED_COMPONENT = "SAMPLED_COMPONENT"
    SAMPLED_ADMISSIBLE = "SAMPLED_ADMISSIBLE"
    CRITICAL_OR_BOUNDARY = "CRITICAL_OR_BOUNDARY"
    UNRESOLVED = "UNRESOLVED"
    NOT_REQUIRED = "NOT_REQUIRED"


class SourceIntervalStatus(str, Enum):
    """Per-c source-control evidence. Not a component-completeness theorem."""

    RETURNED_SET_FOUND = "RETURNED_SET_FOUND"
    # Historical H12 JSON only. H13 production does not emit this as a covered status.
    RETURNED_COMPONENT_FOUND = "RETURNED_COMPONENT_FOUND"
    MIXED_UNRESOLVED = "MIXED_UNRESOLVED"
    CRITICAL_OR_BOUNDARY = "CRITICAL_OR_BOUNDARY"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    OPEN_ONLY = "OPEN_ONLY"
    SINGULAR = "SINGULAR"
    UNRESOLVED = "UNRESOLVED"
    COMPONENT_COMPLETE = "COMPONENT_COMPLETE"


class SourceTraceTermination(str, Enum):
    """Termination of one declared-budget source ``h=c`` trace.

    Closure at the seed and closure by meeting of the two arclength rays remain
    distinct evidence. Neither status is an independent component-identity proof.
    """

    PROJECTION_FAILED = "PROJECTION_FAILED"
    RETURNED_TO_SEED = "RETURNED_TO_SEED"
    PLUS_MINUS_ENDPOINTS_CLOSED = "PLUS_MINUS_ENDPOINTS_CLOSED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    SINGULAR_OR_CRITICAL_ENDPOINT = "SINGULAR_OR_CRITICAL_ENDPOINT"
    CORRECTOR_FAILURE = "CORRECTOR_FAILURE"
    OPEN_UNCLASSIFIED = "OPEN_UNCLASSIFIED"


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


@dataclass(frozen=True, slots=True)
class ChartAtlasPolicy:
    policy_id: str
    chart_ids: tuple[str, ...]
    canonical_assignment: str
    singularity_margin: float
    overlap_margin: float
    claim_scope: str

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "policy_id": self.policy_id,
                "chart_ids": list(self.chart_ids),
                "canonical_assignment": self.canonical_assignment,
                "singularity_margin": self.singularity_margin,
                "overlap_margin": self.overlap_margin,
                "claim_scope": self.claim_scope,
            }
        )


class OracleFeasibility(str, Enum):
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    BOUNDARY = "BOUNDARY"


class CellClass(str, Enum):
    STRICT_COVERED = "STRICT_COVERED"
    STRICT_UNCOVERED = "STRICT_UNCOVERED"
    AMBIGUOUS_BOUNDARY = "AMBIGUOUS_BOUNDARY"


class MetricState(str, Enum):
    """Applicability of one comparison scalar. ``None`` is not a pass/fail."""

    VALUE = "VALUE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNEVALUABLE = "UNEVALUABLE"
    FAILED_VALUE = "FAILED_VALUE"


@dataclass(frozen=True, slots=True)
class ScalarMetric:
    state: MetricState
    value: float | None
    reason: str

    def to_json_dict(self) -> dict[str, Any]:
        return json_object({"state": self.state.value, "value": self.value, "reason": self.reason})

    @classmethod
    def computed(cls, value: float, reason: str = "computed") -> ScalarMetric:
        return cls(MetricState.VALUE, float(value), reason)

    @classmethod
    def not_applicable(cls, reason: str) -> ScalarMetric:
        return cls(MetricState.NOT_APPLICABLE, None, reason)

    @classmethod
    def unevaluable(cls, reason: str) -> ScalarMetric:
        return cls(MetricState.UNEVALUABLE, None, reason)

    @classmethod
    def failed(cls, reason: str) -> ScalarMetric:
        return cls(MetricState.FAILED_VALUE, None, reason)

    @classmethod
    def from_json_fields(
        cls,
        blob: Mapping[str, Any],
        name: str,
        *,
        default_unevaluable_reason: str = "legacy null metric",
    ) -> ScalarMetric:
        """Load ``<name>`` plus optional ``<name>_state`` / ``<name>_reason``.

        Pre-H7 JSON (numeric only) is ``VALUE`` when present and ``UNEVALUABLE``
        when null. Missing refinement is never treated as a pass.
        """

        raw_state = blob.get(f"{name}_state")
        raw_value = blob.get(name)
        raw_reason = blob.get(f"{name}_reason")
        reason = str(raw_reason) if raw_reason else ""
        if raw_state is None:
            if raw_value is None:
                return cls.unevaluable(reason or default_unevaluable_reason)
            return cls.computed(float(raw_value), reason or "legacy numeric")
        state = MetricState(str(raw_state))
        value = None if raw_value is None else float(raw_value)
        if not reason:
            reason = {
                MetricState.VALUE: "loaded",
                MetricState.NOT_APPLICABLE: "not applicable",
                MetricState.UNEVALUABLE: "unevaluable",
                MetricState.FAILED_VALUE: "failed",
            }[state]
        return cls(state, value, reason)


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


def file_sha256(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def git_provenance(repo: Path | None = None) -> dict[str, Any]:
    """Best-effort source commit and dirty-tree flag. Missing git is not a crash."""

    import subprocess

    cwd = Path(repo) if repo is not None else Path.cwd()
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=cwd,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        )
        return {"git_commit": commit, "dirty_tree": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"git_commit": None, "dirty_tree": None}


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
    local_seed_q_error: float | None
    local_seed_pointing_error: float | None
    local_lambda_error: float | None
    local_tangent_error: float | None
    symmetric_branch_q_distance: float | None
    symmetric_branch_pointing_distance: float | None
    return_status_match: bool | None
    branch_status_match: bool | None
    returned_symmetric_set_match: bool | None
    scope: ReseedScope
    disposition: ReseedDisposition
    notes: tuple[str, ...] = ()

    @property
    def lambda_error_rad(self) -> float | None:
        return self.local_lambda_error

    @property
    def tangent_error(self) -> float | None:
        return self.local_tangent_error

    @property
    def returned_match(self) -> bool | None:
        return self.return_status_match

    @property
    def circuit_or_component_match(self) -> None:
        """Legacy compatibility: no independent circuit/component signature exists."""
        return None

    @property
    def component_identity(self) -> None:
        """Reserved for a future independent circuit/component signature."""
        return None

    @property
    def status(self) -> str:
        return self.disposition.value

    @property
    def symmetric_wrapped_q_distance_rad(self) -> float | None:
        return self.symmetric_branch_q_distance

    @property
    def symmetric_pointing_distance_rad(self) -> float | None:
        return self.symmetric_branch_pointing_distance

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "reseed_id": self.reseed_id,
                "seed_s": self.seed_s,
                "local_seed_q_error": self.local_seed_q_error,
                "local_seed_pointing_error": self.local_seed_pointing_error,
                "local_lambda_error": self.local_lambda_error,
                "lambda_error_rad": self.local_lambda_error,
                "local_tangent_error": self.local_tangent_error,
                "tangent_error": self.local_tangent_error,
                "symmetric_branch_q_distance": self.symmetric_branch_q_distance,
                "symmetric_wrapped_q_distance_rad": self.symmetric_branch_q_distance,
                "symmetric_branch_pointing_distance": self.symmetric_branch_pointing_distance,
                "symmetric_pointing_distance_rad": self.symmetric_branch_pointing_distance,
                "return_status_match": self.return_status_match,
                "returned_match": self.return_status_match,
                "branch_status_match": self.branch_status_match,
                "returned_symmetric_set_match": self.returned_symmetric_set_match,
                "legacy_returned_set_match_signal": self.returned_symmetric_set_match,
                "circuit_or_component_match": None,
                "component_identity": None,
                "scope": self.scope.value,
                "disposition": self.disposition.value,
                "status": self.disposition.value,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class ReseedAudit:
    disposition: ReseedDisposition
    n_reseeds: int
    max_symmetric_q_distance_rad: float | None
    max_pointing_distance_rad: float | None
    notes: tuple[str, ...] = ()
    attempts: tuple[ReseedAttempt, ...] = ()
    max_tangent_error: float | None = None
    all_returned_symmetric_set_matches: bool | None = None
    max_local_seed_q_error: float | None = None
    max_local_seed_pointing_error: float | None = None

    @property
    def all_component_ids_match(self) -> None:
        """Legacy compatibility: component IDs are not independently computed."""
        return None

    @property
    def status(self) -> str:
        return self.disposition.value

    @property
    def reseed_status(self) -> str:
        return self.disposition.value

    @property
    def max_symmetric_pointing_distance_rad(self) -> float | None:
        return self.max_pointing_distance_rad

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "status": self.disposition.value,
                "disposition": self.disposition.value,
                "reseed_status": self.disposition.value,
                "n_reseeds": self.n_reseeds,
                "max_symmetric_q_distance_rad": self.max_symmetric_q_distance_rad,
                "max_pointing_distance_rad": self.max_pointing_distance_rad,
                "max_symmetric_pointing_distance_rad": self.max_pointing_distance_rad,
                "max_local_seed_q_error": self.max_local_seed_q_error,
                "max_local_seed_pointing_error": self.max_local_seed_pointing_error,
                "max_tangent_error": self.max_tangent_error,
                "all_returned_symmetric_set_matches": self.all_returned_symmetric_set_matches,
                "all_component_ids_match": None,
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
    required: bool = True
    claim_scope: str = "multi_chart_declared_domain"
    chart_id_a: str | None = None
    chart_id_b: str | None = None
    leaf_id_a: str | None = None
    leaf_id_b: str | None = None
    responsibility_transition_id: str | None = None
    transition_sample_count: int = 0

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
                "required": self.required,
                "claim_scope": self.claim_scope,
                "chart_id_a": self.chart_id_a,
                "chart_id_b": self.chart_id_b,
                "leaf_id_a": self.leaf_id_a,
                "leaf_id_b": self.leaf_id_b,
                "responsibility_transition_id": self.responsibility_transition_id,
                "transition_sample_count": self.transition_sample_count,
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
    responsible_chart_id: str | None = None

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
            "responsible_chart_id": self.responsible_chart_id,
        }
        return json_object(payload)


@dataclass(frozen=True, slots=True)
class FamilyIntervalRecord:
    chart_id: str
    lambda_interval: tuple[float, float]
    sampled_lambda_values: tuple[float, ...]
    accepted_leaf_ids: tuple[str, ...]
    rejected_leaf_ids: tuple[str, ...]
    unresolved_leaf_ids: tuple[str, ...]
    duplicate_groups: tuple[tuple[str, ...], ...] = ()
    critical_values: tuple[float, ...] = ()
    birth_death_merge_events: tuple[str, ...] = ()
    topology_event_status: str = "NOT_EVALUATED_EXCLUDED_FROM_DECLARED_RESOLUTION_SET_COVER"
    interval_status: IntervalStatus = IntervalStatus.UNSAMPLED
    required: bool = False
    seed_count: int = 0
    leaf_count: int = 0
    component_status_counts: dict[str, int] | None = None
    admissibility_status_counts: dict[str, int] | None = None
    budget_exhausted: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        status = (
            self.interval_status.value
            if isinstance(self.interval_status, IntervalStatus)
            else str(self.interval_status)
        )
        return json_object(
            {
                "chart_id": self.chart_id,
                "lambda_interval": list(self.lambda_interval),
                "sampled_lambda_values": list(self.sampled_lambda_values),
                "accepted_leaf_ids": list(self.accepted_leaf_ids),
                "rejected_leaf_ids": list(self.rejected_leaf_ids),
                "unresolved_leaf_ids": list(self.unresolved_leaf_ids),
                "duplicate_groups": [list(group) for group in self.duplicate_groups],
                "critical_values": list(self.critical_values),
                "birth_death_merge_events": list(self.birth_death_merge_events),
                "topology_event_status": self.topology_event_status,
                "interval_status": status,
                "required": self.required,
                "seed_count": self.seed_count,
                "leaf_count": self.leaf_count,
                "component_status_counts": dict(self.component_status_counts or {}),
                "admissibility_status_counts": dict(self.admissibility_status_counts or {}),
                "budget_exhausted": self.budget_exhausted,
            }
        )


@dataclass(frozen=True, slots=True)
class SourceControlCRecord:
    c: float
    expected_seed_count: int
    projected_seed_count: int
    continued_component_count: int
    returned_count: int
    open_count: int
    singular_count: int
    unresolved_count: int
    deduplicated_component_ids: tuple[str, ...]
    parameter_interval_status: str
    candidate_seed_count: int = 0
    projection_attempt_count: int = 0
    attempted_seed_count: int | None = None
    projected_seed_cluster_count: int = 0
    projection_failure_count: int = 0
    seed_budget_exhausted: bool = False
    required: bool = True
    domain_boundary: bool = False
    closed_count: int = 0
    endpoint_closed_count: int = 0
    budget_exhausted_count: int = 0
    corrector_failure_count: int = 0
    closure_kind_counts: dict[str, int] | None = None
    seed_count_semantics: str | None = None
    required_candidate_count: int = 0
    exploratory_candidate_count: int = 0
    candidate_budget_exhausted: bool = False
    blocking_projection_failure_count: int = 0
    diagnostic_projection_failure_count: int = 0
    trace_attempt_count: int = 0
    explained_projected_seed_count: int = 0
    failed_trace_seed_count: int = 0
    unexplained_projected_seed_count: int = 0
    trace_budget_exhausted: bool = False
    rasterization_incomplete_count: int = 0

    def to_json_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "c": self.c,
            "expected_seed_count": self.expected_seed_count,
            "projected_seed_count": self.projected_seed_count,
            "continued_component_count": self.continued_component_count,
            "returned_count": self.returned_count,
            "open_count": self.open_count,
            "singular_count": self.singular_count,
            "unresolved_count": self.unresolved_count,
            "deduplicated_component_ids": list(self.deduplicated_component_ids),
            "parameter_interval_status": self.parameter_interval_status,
        }
        if self.attempted_seed_count is not None:
            payload.update(
                {
                    "candidate_seed_count": self.candidate_seed_count,
                    "projection_attempt_count": self.projection_attempt_count,
                    "attempted_seed_count": self.attempted_seed_count,
                    "projected_seed_cluster_count": self.projected_seed_cluster_count,
                    "projection_failure_count": self.projection_failure_count,
                    "seed_budget_exhausted": self.seed_budget_exhausted,
                    "seed_count_semantics": self.seed_count_semantics
                    or "attempted_projected_seed_clusters_not_expected_components",
                    "required": self.required,
                    "domain_boundary": self.domain_boundary,
                    "closed_count": self.closed_count,
                    "endpoint_closed_count": self.endpoint_closed_count,
                    "budget_exhausted_count": self.budget_exhausted_count,
                    "corrector_failure_count": self.corrector_failure_count,
                    "closure_kind_counts": dict(self.closure_kind_counts or {}),
                }
            )
            if self.seed_count_semantics is not None:
                payload.update(
                    {
                        "required_candidate_count": self.required_candidate_count,
                        "exploratory_candidate_count": self.exploratory_candidate_count,
                        "candidate_budget_exhausted": self.candidate_budget_exhausted,
                        "blocking_projection_failure_count": (
                            self.blocking_projection_failure_count
                        ),
                        "diagnostic_projection_failure_count": (
                            self.diagnostic_projection_failure_count
                        ),
                        "trace_attempt_count": self.trace_attempt_count,
                        "explained_projected_seed_count": (
                            self.explained_projected_seed_count
                        ),
                        "failed_trace_seed_count": self.failed_trace_seed_count,
                        "unexplained_projected_seed_count": (
                            self.unexplained_projected_seed_count
                        ),
                        "trace_budget_exhausted": self.trace_budget_exhausted,
                        "rasterization_incomplete_count": (
                            self.rasterization_incomplete_count
                        ),
                    }
                )
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
    chart_overlap_audits: tuple[ChartOverlapAudit, ...] = ()
    duplicate_classifications: tuple[str, ...] = ()
    lambda_intervals: tuple[FamilyIntervalRecord, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "probe_id": self.probe_id,
                "leaves": [leaf.to_json_dict() for leaf in self.leaves],
                "accepted_count": self.accepted_count,
                "duplicate_count": self.duplicate_count,
                "chart_overlap_status": self.chart_overlap_status,
                "unresolved_lambda_intervals": [list(iv) for iv in self.unresolved_lambda_intervals],
                "lambda_intervals": [item.to_json_dict() for item in self.lambda_intervals],
                "neighbor_audits": [item.to_json_dict() for item in self.neighbor_audits],
                "chart_overlap": None if self.chart_overlap is None else self.chart_overlap.to_json_dict(),
                "chart_overlap_audits": [item.to_json_dict() for item in self.chart_overlap_audits],
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
    missed_covered: ScalarMetric
    false_positive: ScalarMetric
    hausdorff: ScalarMetric
    boundary_disagreement_fraction: float | None
    unresolved_fraction: float
    max_cell_diameter_rad: float
    refinement: ScalarMetric
    coarse_metrics: PointingSetMetrics | None = None

    @property
    def missed_covered_fraction(self) -> float | None:
        return self.missed_covered.value if self.missed_covered.state is MetricState.VALUE else None

    @property
    def false_positive_fraction(self) -> float | None:
        return self.false_positive.value if self.false_positive.state is MetricState.VALUE else None

    @property
    def hausdorff_rad(self) -> float | None:
        return self.hausdorff.value if self.hausdorff.state is MetricState.VALUE else None

    @property
    def refinement_delta(self) -> float | None:
        return self.refinement.value if self.refinement.state is MetricState.VALUE else None

    def _scalar_json(self, name: str, metric: ScalarMetric) -> dict[str, Any]:
        return {
            name: metric.value if metric.state is MetricState.VALUE else None,
            f"{name}_state": metric.state.value,
            f"{name}_reason": metric.reason,
        }

    def to_json_dict(self, *, nested: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "strict_covered_count": self.strict_covered_count,
            "strict_uncovered_count": self.strict_uncovered_count,
            "reconstructed_hit_count": self.reconstructed_hit_count,
            **self._scalar_json("missed_covered_fraction", self.missed_covered),
            **self._scalar_json("false_positive_fraction", self.false_positive),
            **self._scalar_json("hausdorff_rad", self.hausdorff),
            "boundary_disagreement_fraction": self.boundary_disagreement_fraction,
            "unresolved_fraction": self.unresolved_fraction,
            "max_cell_diameter_rad": self.max_cell_diameter_rad,
            **self._scalar_json("refinement_delta", self.refinement),
            "refinement": self.refinement.to_json_dict(),
        }
        if not nested:
            payload["fine"] = self.to_json_dict(nested=True)
            payload["coarse"] = None if self.coarse_metrics is None else self.coarse_metrics.to_json_dict(nested=True)
        return json_object(payload)

    @classmethod
    def from_json_dict(cls, blob: Mapping[str, Any]) -> PointingSetMetrics:
        coarse_raw = blob.get("coarse")
        coarse = None
        if isinstance(coarse_raw, dict):
            coarse = cls.from_json_dict(coarse_raw)
        return cls(
            strict_covered_count=int(blob["strict_covered_count"]),
            strict_uncovered_count=int(blob["strict_uncovered_count"]),
            reconstructed_hit_count=int(blob["reconstructed_hit_count"]),
            missed_covered=ScalarMetric.from_json_fields(blob, "missed_covered_fraction"),
            false_positive=ScalarMetric.from_json_fields(blob, "false_positive_fraction"),
            hausdorff=ScalarMetric.from_json_fields(blob, "hausdorff_rad"),
            boundary_disagreement_fraction=(
                None
                if blob.get("boundary_disagreement_fraction") is None
                else float(blob["boundary_disagreement_fraction"])
            ),
            unresolved_fraction=float(blob.get("unresolved_fraction", 0.0)),
            max_cell_diameter_rad=float(blob["max_cell_diameter_rad"]),
            refinement=ScalarMetric.from_json_fields(
                blob,
                "refinement_delta",
                default_unevaluable_reason="legacy null refinement",
            ),
            coarse_metrics=coarse,
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
    campaign_blocker: CampaignBlocker | None = None

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
                "campaign_blocker": None if self.campaign_blocker is None else self.campaign_blocker.value,
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
    campaign_blocker: CampaignBlocker | None = None

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
                "campaign_blocker": None if self.campaign_blocker is None else self.campaign_blocker.value,
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
    max_natural_leaves_per_chart: int
    max_natural_leaves_per_probe: int
    reseed_samples_per_leaf: int
    continuation_steps: int
    allows_full_campaign_disposition: bool

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
                "max_natural_leaves_per_chart": self.max_natural_leaves_per_chart,
                "max_natural_leaves_per_probe": self.max_natural_leaves_per_probe,
                "reseed_samples_per_leaf": self.reseed_samples_per_leaf,
                "continuation_steps": self.continuation_steps,
                "allows_full_campaign_disposition": self.allows_full_campaign_disposition,
            }
        )


def resolve_stage_budgets(config: CampaignConfig, mode: str) -> CampaignMode:
    """Return frozen mode budgets with no silent clipping."""
    return config.mode(mode)


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
    chart_atlas_policy: ChartAtlasPolicy
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
                "chart_atlas_policy": self.chart_atlas_policy.to_json_dict(),
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
            max_natural_leaves_per_chart=int(spec["max_natural_leaves_per_chart"]),
            max_natural_leaves_per_probe=int(spec["max_natural_leaves_per_probe"]),
            reseed_samples_per_leaf=int(spec["reseed_samples_per_leaf"]),
            continuation_steps=int(spec["continuation_steps"]),
            allows_full_campaign_disposition=bool(spec["allows_full_campaign_disposition"]),
        )
        for name, spec in raw["campaign_modes"].items()
    }
    n_charts = len(charts)
    for mode in modes.values():
        if mode.max_natural_leaves_per_chart < mode.natural_lambda_bin_count_per_chart:
            raise ValueError(
                f"{mode.name}: max_natural_leaves_per_chart must cover declared bins "
                f"({mode.natural_lambda_bin_count_per_chart})"
            )
        expected_probe_cap = n_charts * mode.max_natural_leaves_per_chart
        if mode.max_natural_leaves_per_probe != expected_probe_cap:
            raise ValueError(
                f"{mode.name}: max_natural_leaves_per_probe must equal n_charts * "
                f"max_natural_leaves_per_chart ({expected_probe_cap}), "
                f"got {mode.max_natural_leaves_per_probe}"
            )
    policy_raw = raw["chart_atlas_policy"]
    declared_ids = tuple(item.chart_id for item in charts)
    policy_ids = tuple(str(x) for x in policy_raw.get("chart_ids", declared_ids))
    if policy_ids != declared_ids:
        raise ValueError("chart_atlas_policy.chart_ids must match virtual_spherical_charts order")
    chart_atlas_policy = ChartAtlasPolicy(
        policy_id=str(policy_raw["policy_id"]),
        chart_ids=policy_ids,
        canonical_assignment=str(policy_raw["canonical_assignment"]),
        singularity_margin=float(policy_raw["singularity_margin"]),
        overlap_margin=float(policy_raw["overlap_margin"]),
        claim_scope=str(policy_raw["claim_scope"]),
    )
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
        chart_atlas_policy=chart_atlas_policy,
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
