"""R3C L5 behavior-atlas extraction records.

This module is deliberately pre-descriptor.  It records exact mechanism family
identity, source provenance, and immutable canonical geometry payloads.  It does
not classify mechanism behavior and does not issue workspace certificates.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any

SCHEMA_VERSION = "l5_behavior_atlas_extraction_v1"
WORKSPACE_ACCEPTED_CHILD_STATUSES = frozenset({"EXACT_GLOBAL", "EXACT_ON_COMPONENT"})


class MechanismProvenance(str, Enum):
    """Where an extracted mechanism came from."""

    SOURCE_DERIVED_NATURAL_LEAF = "source_derived_natural_leaf"
    SOURCE_DERIVED_CANDIDATE = "source_derived_candidate"
    MECHANISM_EXPLORER_ONLY = "mechanism_explorer_only"


def _normalize_json(value: Any, *, path: str = "$") -> Any:
    """Return a deterministic JSON-compatible copy and reject non-finite floats."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError(f"{path} has non-string mapping key {key!r}")
            out[key] = _normalize_json(value[key], path=f"{path}.{key}")
        return out
    if isinstance(value, (list, tuple)):
        return [_normalize_json(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"{path} contains non-JSON value of type {type(value).__name__}")


def canonical_json_text(payload: Any) -> str:
    """Serialize finite JSON data with stable ordering and no insignificant whitespace."""

    normalized = _normalize_json(payload)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_json_sha256(payload: Any) -> str:
    """Hash the canonical JSON representation of ``payload``."""

    return hashlib.sha256(canonical_json_text(payload).encode("utf-8")).hexdigest()


def _require_nonempty(value: str, *, field: str) -> None:
    if not value.strip():
        raise ValueError(f"{field} must be non-empty")


def _validate_vec3(value: tuple[float, float, float], *, field: str) -> None:
    if len(value) != 3 or any(not isfinite(float(v)) for v in value):
        raise ValueError(f"{field} must contain three finite values")


@dataclass(frozen=True, slots=True)
class MechanismFamilyIdentity:
    """Exact role-aware child-family identity emitted by the decomposition."""

    family_id: str
    joint_kind_sequence: tuple[str, ...]
    joint_role_sequence: tuple[str, ...]
    parent_family_id: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.family_id, field="family_id")
        if not self.joint_kind_sequence:
            raise ValueError("joint_kind_sequence must be non-empty")
        if len(self.joint_kind_sequence) != len(self.joint_role_sequence):
            raise ValueError("joint kind/role sequences must have equal length")
        if any(not item.strip() for item in self.joint_kind_sequence):
            raise ValueError("joint_kind_sequence entries must be non-empty")
        if any(not item.strip() for item in self.joint_role_sequence):
            raise ValueError("joint_role_sequence entries must be non-empty")
        if self.parent_family_id is not None:
            _require_nonempty(self.parent_family_id, field="parent_family_id")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "parent_family_id": self.parent_family_id,
            "joint_kind_sequence": list(self.joint_kind_sequence),
            "joint_role_sequence": list(self.joint_role_sequence),
        }


@dataclass(frozen=True, slots=True)
class SourceProvenanceRecord:
    """Manipulator-side provenance for one extracted child mechanism."""

    source_chain_id: str
    fixed_position_problem_id: str
    source_component_id: str
    probe_id: str
    task_point: tuple[float, float, float]
    source_artifact: str
    leaf_id: str | None
    construction_kind: str
    chart_id: str | None
    family_parameters: tuple[tuple[str, float], ...]
    child_certificate_status: str
    accepted_for_reconstruction: bool
    provenance: MechanismProvenance

    def __post_init__(self) -> None:
        for field_name in (
            "source_chain_id",
            "fixed_position_problem_id",
            "source_component_id",
            "probe_id",
            "source_artifact",
            "construction_kind",
            "child_certificate_status",
        ):
            _require_nonempty(str(getattr(self, field_name)), field=field_name)
        _validate_vec3(self.task_point, field="task_point")
        if self.leaf_id is not None:
            _require_nonempty(self.leaf_id, field="leaf_id")
        if self.chart_id is not None:
            _require_nonempty(self.chart_id, field="chart_id")

        names: set[str] = set()
        for name, value in self.family_parameters:
            _require_nonempty(name, field="family parameter name")
            if name in names:
                raise ValueError(f"duplicate family parameter name: {name}")
            names.add(name)
            if not isfinite(float(value)):
                raise ValueError(f"family parameter {name} must be finite")

        if (
            self.provenance is MechanismProvenance.MECHANISM_EXPLORER_ONLY
            and self.accepted_for_reconstruction
        ):
            raise ValueError(
                "mechanism_explorer_only records cannot be accepted for workspace reconstruction"
            )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "source_chain_id": self.source_chain_id,
            "fixed_position_problem_id": self.fixed_position_problem_id,
            "source_component_id": self.source_component_id,
            "probe_id": self.probe_id,
            "task_point": list(self.task_point),
            "source_artifact": self.source_artifact,
            "leaf_id": self.leaf_id,
            "construction_kind": self.construction_kind,
            "chart_id": self.chart_id,
            "family_parameters": [
                {"name": name, "value": value} for name, value in self.family_parameters
            ],
            "child_certificate_status": self.child_certificate_status,
            "accepted_for_reconstruction": self.accepted_for_reconstruction,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True, slots=True)
class MechanismGeometryRecord:
    """Canonical, reconstructible frozen mechanism geometry payload."""

    geometry_schema_id: str
    payload_json: str
    geometry_sha256: str

    def __post_init__(self) -> None:
        _require_nonempty(self.geometry_schema_id, field="geometry_schema_id")
        _require_nonempty(self.payload_json, field="payload_json")
        _require_nonempty(self.geometry_sha256, field="geometry_sha256")
        try:
            payload = json.loads(self.payload_json)
        except json.JSONDecodeError as exc:
            raise ValueError("payload_json must contain valid JSON") from exc
        canonical = canonical_json_text(payload)
        if canonical != self.payload_json:
            raise ValueError("payload_json must already be canonical JSON")
        digest = hashlib.sha256(self.payload_json.encode("utf-8")).hexdigest()
        if digest != self.geometry_sha256:
            raise ValueError("geometry_sha256 does not match payload_json")

    @classmethod
    def from_payload(cls, *, geometry_schema_id: str, payload: Any) -> MechanismGeometryRecord:
        payload_json = canonical_json_text(payload)
        digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        return cls(
            geometry_schema_id=geometry_schema_id,
            payload_json=payload_json,
            geometry_sha256=digest,
        )

    def payload(self) -> Any:
        return json.loads(self.payload_json)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "geometry_schema_id": self.geometry_schema_id,
            "geometry_sha256": self.geometry_sha256,
            "payload": self.payload(),
        }


@dataclass(frozen=True, slots=True)
class ExtractedMechanismRecord:
    """One E0 mechanism record entering the future family-atlas pipeline."""

    record_id: str
    family: MechanismFamilyIdentity
    source: SourceProvenanceRecord
    geometry: MechanismGeometryRecord
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonempty(self.record_id, field="record_id")
        if any(not note.strip() for note in self.notes):
            raise ValueError("notes entries must be non-empty")

    @property
    def workspace_evidence_eligible(self) -> bool:
        return (
            self.source.provenance is MechanismProvenance.SOURCE_DERIVED_NATURAL_LEAF
            and self.source.accepted_for_reconstruction
            and self.source.child_certificate_status in WORKSPACE_ACCEPTED_CHILD_STATUSES
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "family": self.family.to_json_dict(),
            "source": self.source.to_json_dict(),
            "geometry": self.geometry.to_json_dict(),
            "workspace_evidence_eligible": self.workspace_evidence_eligible,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class ExtractionManifest:
    """Frozen E0 collection for one source-to-mechanism extraction campaign."""

    program_id: str
    source_campaign_id: str
    source_config_sha256: str
    records: tuple[ExtractedMechanismRecord, ...]
    notes: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_nonempty(self.program_id, field="program_id")
        _require_nonempty(self.source_campaign_id, field="source_campaign_id")
        _require_nonempty(self.source_config_sha256, field="source_config_sha256")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {self.schema_version!r}; expected {SCHEMA_VERSION!r}"
            )
        ids = [record.record_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("record_id values must be unique within a manifest")
        if any(not note.strip() for note in self.notes):
            raise ValueError("notes entries must be non-empty")

    def family_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.records:
            counts[record.family.family_id] = counts.get(record.family.family_id, 0) + 1
        return dict(sorted(counts.items()))

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "program_id": self.program_id,
            "source_campaign_id": self.source_campaign_id,
            "source_config_sha256": self.source_config_sha256,
            "record_count": len(self.records),
            "workspace_evidence_eligible_count": sum(
                int(record.workspace_evidence_eligible) for record in self.records
            ),
            "family_counts": self.family_counts(),
            "records": [record.to_json_dict() for record in self.records],
            "notes": list(self.notes),
        }

    def to_json_text(self) -> str:
        normalized = _normalize_json(self.to_json_dict())
        return json.dumps(
            normalized,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=False,
        ) + "\n"
