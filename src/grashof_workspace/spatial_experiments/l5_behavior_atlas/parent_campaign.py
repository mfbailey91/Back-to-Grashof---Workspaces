"""R3C-A2: controlled 5R source-parent population and family-support census.

This module distinguishes:
- exact source physical aggregation / registered parent pattern,
- an actually exported reconstructible E0 child,
- workspace-evidence eligibility.

It does not construct new children or classify mechanism behavior.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from grashof_workspace.decomposition_ladder.registry import PARENT_CHILD_FAMILIES
from grashof_workspace.spatial_experiments.axis_aggregation import (
    AggregationCandidate,
    build_multi_u_aggregation,
    detect_exact_u_pairs,
    multi_u_kind_role_sequences,
)
from grashof_workspace.spatial_experiments.axis_geometry import AxisLine
from grashof_workspace.spatial_experiments.fixed_position import (
    audit_fixed_position_seed,
    pose_fixed_position_problem,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CampaignConfig,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
    fixture_seed_for_probe,
)
from grashof_workspace.spatial_experiments.open_chain import OpenChainModel
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain
from grashof_workspace.spatial_experiments.v06_corpus import (
    Spatial5RCorpusEntry,
    build_exact_two_u_5r,
    build_generic_5r,
    build_near_two_u_5r,
)

from .models import canonical_json_sha256

PROGRAM_ID = "R3C_A2_5R_PARENT_CAMPAIGN"
CONFIG_SCHEMA = "r3c_a2_parent_campaign_v1"
A1_PROGRAM_ID = "R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER"

U_BASED_PARENT_FAMILIES = frozenset({"SUUR", "SURU", "SRUU"})


class ArchitectureDisposition(str, Enum):
    EXACT_CHILD_EXPORTED = "EXACT_CHILD_EXPORTED"
    REGISTERED_PARENT_PATTERN_ONLY = "REGISTERED_PARENT_PATTERN_ONLY"
    NEAR_PATTERN_REJECTED = "NEAR_PATTERN_REJECTED"
    NO_REGISTERED_FOURBAR_PARENT_PATTERN = "NO_REGISTERED_FOURBAR_PARENT_PATTERN"


@dataclass(frozen=True, slots=True)
class A2Config:
    program_id: str
    schema_version: str
    r3a_config_path: Path
    required_cases: tuple[str, ...]
    q_offset_bank_rad: tuple[tuple[float, ...], ...]
    near_axis_offset_m: float
    near_pair_distance_max_m: float
    near_pair_orthogonality_abs_dot_max: float
    required_positive_parent_family: str
    require_a1_zero_roundtrip_failures: bool
    require_all_cases_present: bool
    raw: dict[str, Any]
    config_hash: str


@dataclass(frozen=True, slots=True)
class ParentPatternObservation:
    pair_indices: tuple[int, int]
    parent_family: str
    candidate_child_family: str | None
    aggregation_status: str
    joint_kind_sequence: tuple[str, ...]
    joint_role_sequence: tuple[str, ...]
    fk_identity_residuals: dict[str, float]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "pair_indices": list(self.pair_indices),
            "parent_family": self.parent_family,
            "candidate_child_family": self.candidate_child_family,
            "aggregation_status": self.aggregation_status,
            "joint_kind_sequence": list(self.joint_kind_sequence),
            "joint_role_sequence": list(self.joint_role_sequence),
            "fk_identity_residuals": dict(self.fk_identity_residuals),
        }


@dataclass(frozen=True, slots=True)
class ParentProbeRecord:
    case_id: str
    probe_id: str
    q_seed: tuple[float, ...]
    p_star: tuple[float, float, float]
    rank_jp: int
    nullity_jp: int
    regular: bool
    audit_status: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "probe_id": self.probe_id,
            "q_seed": list(self.q_seed),
            "p_star": list(self.p_star),
            "rank_jp": self.rank_jp,
            "nullity_jp": self.nullity_jp,
            "regular": self.regular,
            "audit_status": self.audit_status,
        }


@dataclass(frozen=True, slots=True)
class ParentArchitectureRecord:
    case_id: str
    control_role: str
    source_chain_id: str
    source_geometry_sha256: str
    exact_u_pair_indices: tuple[int, ...]
    near_u_pair_indices: tuple[int, ...]
    pair_diagnostics: tuple[dict[str, Any], ...]
    parent_patterns: tuple[ParentPatternObservation, ...]
    actual_e0_child_families: tuple[str, ...]
    actual_e0_record_count: int
    regular_probe_count: int
    total_probe_count: int
    disposition: ArchitectureDisposition
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "control_role": self.control_role,
            "source_chain_id": self.source_chain_id,
            "source_geometry_sha256": self.source_geometry_sha256,
            "exact_u_pair_indices": list(self.exact_u_pair_indices),
            "near_u_pair_indices": list(self.near_u_pair_indices),
            "pair_diagnostics": list(self.pair_diagnostics),
            "parent_patterns": [item.to_json_dict() for item in self.parent_patterns],
            "actual_e0_child_families": list(self.actual_e0_child_families),
            "actual_e0_record_count": self.actual_e0_record_count,
            "regular_probe_count": self.regular_probe_count,
            "total_probe_count": self.total_probe_count,
            "disposition": self.disposition.value,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class ParentCase:
    case_id: str
    control_role: str
    model: OpenChainModel
    q_seeds: tuple[tuple[float, ...], ...]
    probe_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.q_seeds) != len(self.probe_ids):
            raise ValueError("q_seeds and probe_ids must have equal length")


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a JSON object")
    return value


def _finite_q(values: Any, *, field: str) -> tuple[float, ...]:
    q = tuple(float(v) for v in values)
    if len(q) != 5:
        raise ValueError(f"{field} must contain five joint coordinates")
    if any(not np.isfinite(v) for v in q):
        raise ValueError(f"{field} must be finite")
    return q


def load_a2_config(path: Path | str) -> A2Config:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    root = _mapping(raw, field="A2 config")
    if str(root.get("schema_version")) != CONFIG_SCHEMA:
        raise ValueError(f"expected schema_version {CONFIG_SCHEMA}")
    if str(root.get("program_id")) != PROGRAM_ID:
        raise ValueError(f"expected program_id {PROGRAM_ID}")

    near = _mapping(root["near_controls"], field="near_controls")
    accept = _mapping(root["acceptance"], field="acceptance")
    offsets = tuple(
        _finite_q(item, field=f"q_offset_bank_rad[{i}]")
        for i, item in enumerate(root["q_offset_bank_rad"])
    )
    if not offsets:
        raise ValueError("q_offset_bank_rad must be non-empty")
    required = tuple(str(v) for v in root["required_cases"])
    if len(required) != len(set(required)):
        raise ValueError("required_cases must be unique")

    raw_dict = dict(root)
    return A2Config(
        program_id=str(root["program_id"]),
        schema_version=str(root["schema_version"]),
        r3a_config_path=Path(str(root["r3a_config_path"])),
        required_cases=required,
        q_offset_bank_rad=offsets,
        near_axis_offset_m=float(near["axis_offset_m"]),
        near_pair_distance_max_m=float(near["near_pair_distance_max_m"]),
        near_pair_orthogonality_abs_dot_max=float(
            near["near_pair_orthogonality_abs_dot_max"]
        ),
        required_positive_parent_family=str(
            accept["required_positive_parent_family"]
        ),
        require_a1_zero_roundtrip_failures=bool(
            accept["require_a1_zero_roundtrip_failures"]
        ),
        require_all_cases_present=bool(accept["require_all_cases_present"]),
        raw=raw_dict,
        config_hash=canonical_json_sha256(raw_dict),
    )


def _source_geometry_payload(model: OpenChainModel) -> dict[str, Any]:
    return {
        "home_axes": [
            {"r": list(axis.r), "w": list(axis.w)}
            for axis in model.chain.home_axes
        ],
        "p0": list(model.chain.p0),
        "d0": list(model.chain.d0),
        "R0": [list(row) for row in model.chain.R0],
        "joint_kind_sequence": list(model.joint_kind_sequence),
        "joint_role_sequence": list(model.joint_role_sequence),
    }


def source_geometry_sha256(model: OpenChainModel) -> str:
    return canonical_json_sha256(_source_geometry_payload(model))


def _copy_with_axis_offset(
    model: OpenChainModel,
    *,
    axis_index: int,
    delta_xyz: tuple[float, float, float],
    architecture_id: str,
) -> OpenChainModel:
    axes = list(model.chain.home_axes)
    axis = axes[axis_index]
    r = (
        float(axis.r[0] + delta_xyz[0]),
        float(axis.r[1] + delta_xyz[1]),
        float(axis.r[2] + delta_xyz[2]),
    )
    axes[axis_index] = AxisLine(r, axis.w)
    chain = SerialRevoluteChain(
        home_axes=tuple(axes),
        p0=model.chain.p0,
        d0=model.chain.d0,
        R0=model.chain.R0,
    )
    return OpenChainModel(
        architecture_id=architecture_id,
        chain=chain,
        joint_kind_sequence=model.joint_kind_sequence,
        joint_role_sequence=model.joint_role_sequence,
        notes=(
            *model.notes,
            f"A2 near-SURU control; axis {axis_index} point offset by {delta_xyz}.",
        ),
    )


def build_near_suru_controls(
    r3a_config: CampaignConfig,
    *,
    offset_m: float,
) -> tuple[OpenChainModel, OpenChainModel]:
    """Break one exact physical U pair at a time without modifying R3A source code."""

    if offset_m <= 0.0:
        raise ValueError("near control offset_m must be positive")
    source = build_positive_control_arm(r3a_config.geometry).model
    # Both selected axes are y-directed in the positive control.  x is transverse.
    delta = (float(offset_m), 0.0, 0.0)
    shoulder = _copy_with_axis_offset(
        source,
        axis_index=1,
        delta_xyz=delta,
        architecture_id="near_suru_shoulder_5r",
    )
    wrist = _copy_with_axis_offset(
        source,
        axis_index=4,
        delta_xyz=delta,
        architecture_id="near_suru_wrist_5r",
    )
    return shoulder, wrist


def _offset_seed_bank(
    q0: tuple[float, ...],
    offsets: tuple[tuple[float, ...], ...],
) -> tuple[tuple[float, ...], ...]:
    base = np.asarray(q0, dtype=float)
    return tuple(
        tuple(float(v) for v in base + np.asarray(offset, dtype=float))
        for offset in offsets
    )


def _entry_case(
    entry: Spatial5RCorpusEntry,
    *,
    case_id: str,
    control_role: str,
    offsets: tuple[tuple[float, ...], ...],
) -> ParentCase:
    seeds = _offset_seed_bank(entry.regular_q, offsets)
    return ParentCase(
        case_id=case_id,
        control_role=control_role,
        model=entry.model,
        q_seeds=seeds,
        probe_ids=tuple(f"{case_id}_Q{i:02d}" for i in range(len(seeds))),
    )


def build_parent_cases(
    config: A2Config,
    r3a_config: CampaignConfig,
) -> tuple[ParentCase, ...]:
    """Create the frozen A2 source bank."""

    positive_arm = build_positive_control_arm(r3a_config.geometry)
    positive_seeds = tuple(
        fixture_seed_for_probe(
            positive_arm,
            probe,
            position_tol_m=r3a_config.tolerances.position_residual_m,
            pointing_tol_rad=r3a_config.tolerances.pointing_geodesic_rad,
        )
        for probe in r3a_config.probes
    )
    positive = ParentCase(
        case_id="r3a_positive_control",
        control_role="positive_control",
        model=positive_arm.model,
        q_seeds=positive_seeds,
        probe_ids=tuple(probe.probe_id for probe in r3a_config.probes),
    )

    exact = _entry_case(
        build_exact_two_u_5r(),
        case_id="exact_two_u_5r",
        control_role="structured_transfer",
        offsets=config.q_offset_bank_rad,
    )
    generic = _entry_case(
        build_generic_5r(),
        case_id="generic_5r",
        control_role="generic_control",
        offsets=config.q_offset_bank_rad,
    )
    near_two = _entry_case(
        build_near_two_u_5r(),
        case_id="near_two_u_5r",
        control_role="near_control",
        offsets=config.q_offset_bank_rad,
    )

    shoulder_model, wrist_model = build_near_suru_controls(
        r3a_config,
        offset_m=config.near_axis_offset_m,
    )
    base_q = positive_seeds[0]
    shoulder_seeds = _offset_seed_bank(base_q, config.q_offset_bank_rad)
    wrist_seeds = _offset_seed_bank(base_q, config.q_offset_bank_rad)
    near_shoulder = ParentCase(
        case_id="near_suru_shoulder",
        control_role="near_control",
        model=shoulder_model,
        q_seeds=shoulder_seeds,
        probe_ids=tuple(
            f"near_suru_shoulder_Q{i:02d}"
            for i in range(len(shoulder_seeds))
        ),
    )
    near_wrist = ParentCase(
        case_id="near_suru_wrist",
        control_role="near_control",
        model=wrist_model,
        q_seeds=wrist_seeds,
        probe_ids=tuple(
            f"near_suru_wrist_Q{i:02d}"
            for i in range(len(wrist_seeds))
        ),
    )

    cases = (
        positive,
        exact,
        generic,
        near_two,
        near_shoulder,
        near_wrist,
    )
    by_id = {case.case_id: case for case in cases}
    if config.require_all_cases_present:
        missing = tuple(case for case in config.required_cases if case not in by_id)
        if missing:
            raise ValueError(f"missing required A2 cases: {missing}")
    return tuple(by_id[case_id] for case_id in config.required_cases)


def _registered_u_family_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for spec in PARENT_CHILD_FAMILIES:
        roles = tuple(spec.parent_joint_roles)
        if spec.parent_label in U_BASED_PARENT_FAMILIES and "S_phys" not in roles:
            out[spec.parent_label] = spec.child_label
    return out


def detector_scope() -> dict[str, Any]:
    in_scope = _registered_u_family_map()
    all_registered = {spec.child_label for spec in PARENT_CHILD_FAMILIES}
    return {
        "operation": "exact consecutive RR -> U_phys",
        "parent_to_child_candidates": dict(sorted(in_scope.items())),
        "in_scope_child_families": sorted(in_scope.values()),
        "out_of_scope_registered_child_families": sorted(
            all_registered - set(in_scope.values())
        ),
        "out_of_scope_label": "OUT_OF_DETECTOR_SCOPE",
    }


def _nonoverlapping(pair_indices: tuple[int, int]) -> bool:
    return pair_indices[1] > pair_indices[0] + 1


def detect_parent_patterns(
    model: OpenChainModel,
    *,
    q_seed: tuple[float, ...],
) -> tuple[tuple[AggregationCandidate, ...], tuple[ParentPatternObservation, ...]]:
    """Return raw pair diagnostics and exact registered two-U parent patterns."""

    diagnostics = detect_exact_u_pairs(model)
    exact = tuple(item.pair_index for item in diagnostics if item.exact_u_candidate)
    registry = _registered_u_family_map()
    patterns: list[ParentPatternObservation] = []
    for pair_indices in itertools.combinations(exact, 2):
        pair = (int(pair_indices[0]), int(pair_indices[1]))
        if not _nonoverlapping(pair):
            continue
        kinds, _roles = multi_u_kind_role_sequences(5, pair)
        parent_family = "".join(kinds)
        aggregation = build_multi_u_aggregation(
            model,
            q_seed,
            pair_indices=pair,
            expected_parent_label=parent_family,
        )
        patterns.append(
            ParentPatternObservation(
                pair_indices=pair,
                parent_family=parent_family,
                candidate_child_family=registry.get(parent_family),
                aggregation_status=aggregation.axis_aggregation_status,
                joint_kind_sequence=aggregation.joint_kind_sequence,
                joint_role_sequence=aggregation.joint_role_sequence,
                fk_identity_residuals=dict(aggregation.fk_identity_residuals),
            )
        )
    patterns.sort(key=lambda item: item.pair_indices)
    return diagnostics, tuple(patterns)


def _near_pair_indices(
    diagnostics: tuple[AggregationCandidate, ...],
    config: A2Config,
) -> tuple[int, ...]:
    return tuple(
        item.pair_index
        for item in diagnostics
        if (
            not item.exact_u_candidate
            and item.distance_m <= config.near_pair_distance_max_m
            and item.orthogonality_abs_dot
            <= config.near_pair_orthogonality_abs_dot_max
        )
    )


def _audit_probes(case: ParentCase) -> tuple[ParentProbeRecord, ...]:
    records: list[ParentProbeRecord] = []
    for probe_id, q_seed in zip(case.probe_ids, case.q_seeds, strict=True):
        posed = pose_fixed_position_problem(case.model, q_seed)
        audit = audit_fixed_position_seed(posed)
        records.append(
            ParentProbeRecord(
                case_id=case.case_id,
                probe_id=probe_id,
                q_seed=tuple(float(v) for v in q_seed),
                p_star=(
                    float(audit.p_star[0]),
                    float(audit.p_star[1]),
                    float(audit.p_star[2]),
                ),
                rank_jp=int(audit.rank_jp),
                nullity_jp=int(audit.nullity_jp),
                regular=bool(audit.regular),
                audit_status=str(audit.status),
            )
        )
    return tuple(records)


def _load_a1_inputs(
    manifest_path: Path | str,
    audit_path: Path | str,
    *,
    expected_r3a_config_hash: str,
    require_zero_failures: bool,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    audit_path = Path(audit_path)
    manifest = _mapping(
        json.loads(manifest_path.read_text(encoding="utf-8")),
        field="A1 manifest",
    )
    audit = _mapping(
        json.loads(audit_path.read_text(encoding="utf-8")),
        field="A1 audit",
    )
    if str(manifest.get("program_id")) != A1_PROGRAM_ID:
        raise ValueError("A2 requires an A1 E0 manifest")
    if str(manifest.get("source_config_sha256")) != expected_r3a_config_hash:
        raise ValueError("A1 source config hash does not match frozen R3A config")
    audit_program = audit.get("program_id")
    if audit_program is not None and str(audit_program) != A1_PROGRAM_ID:
        raise ValueError("A1 audit program_id mismatch")

    failures = tuple(str(v) for v in audit.get("roundtrip_failures", []))
    counts = _mapping(
        audit.get("roundtrip_status_counts", {}),
        field="A1 roundtrip_status_counts",
    )
    fail_count = int(counts.get("FAIL", len(failures)))
    if require_zero_failures and (failures or fail_count != 0):
        raise ValueError("A2 refuses A1 input with geometry round-trip failures")

    records = tuple(
        _mapping(item, field=f"A1 records[{i}]")
        for i, item in enumerate(manifest.get("records", []))
    )
    family_counts = Counter(
        str(_mapping(item["family"], field="A1 record.family")["family_id"])
        for item in records
    )
    source_family_counts: dict[str, Counter[str]] = {}
    for item in records:
        family = str(_mapping(item["family"], field="A1 record.family")["family_id"])
        source = _mapping(item["source"], field="A1 record.source")
        source_id = str(source["source_chain_id"])
        source_family_counts.setdefault(source_id, Counter())[family] += 1

    return {
        "manifest_path": str(manifest_path),
        "manifest_sha256": _file_sha256(manifest_path),
        "audit_path": str(audit_path),
        "audit_sha256": _file_sha256(audit_path),
        "record_count": len(records),
        "family_counts": dict(sorted(family_counts.items())),
        "source_family_counts": {
            source_id: dict(sorted(counter.items()))
            for source_id, counter in sorted(source_family_counts.items())
        },
        "roundtrip_failures": list(failures),
        "roundtrip_fail_count": fail_count,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _architecture_record(
    case: ParentCase,
    probes: tuple[ParentProbeRecord, ...],
    config: A2Config,
    a1: Mapping[str, Any],
) -> ParentArchitectureRecord:
    diagnostics, patterns = detect_parent_patterns(
        case.model,
        q_seed=case.q_seeds[0],
    )
    exact = tuple(item.pair_index for item in diagnostics if item.exact_u_candidate)
    near = _near_pair_indices(diagnostics, config)
    source_family_counts = _mapping(
        a1.get("source_family_counts", {}),
        field="A1 source_family_counts",
    )
    actual_counts = _mapping(
        source_family_counts.get(case.model.architecture_id, {}),
        field=f"A1 source_family_counts[{case.model.architecture_id}]",
    )
    actual_families = tuple(
        sorted(family for family, count in actual_counts.items() if int(count) > 0)
    )
    actual_count = sum(int(v) for v in actual_counts.values())

    registered_candidate = any(
        item.candidate_child_family is not None
        and item.aggregation_status == "EXACT_GLOBAL"
        for item in patterns
    )
    structural_child_families = {
        item.candidate_child_family
        for item in patterns
        if (
            item.candidate_child_family is not None
            and item.aggregation_status == "EXACT_GLOBAL"
        )
    }
    unexpected_actual = set(actual_families) - structural_child_families
    if unexpected_actual:
        raise ValueError(
            f"{case.case_id}: A1 child families {sorted(unexpected_actual)} do not "
            "match the exact registered parent-pattern census"
        )
    if actual_families:
        disposition = ArchitectureDisposition.EXACT_CHILD_EXPORTED
    elif registered_candidate:
        disposition = ArchitectureDisposition.REGISTERED_PARENT_PATTERN_ONLY
    elif near:
        disposition = ArchitectureDisposition.NEAR_PATTERN_REJECTED
    else:
        disposition = ArchitectureDisposition.NO_REGISTERED_FOURBAR_PARENT_PATTERN

    return ParentArchitectureRecord(
        case_id=case.case_id,
        control_role=case.control_role,
        source_chain_id=case.model.architecture_id,
        source_geometry_sha256=source_geometry_sha256(case.model),
        exact_u_pair_indices=exact,
        near_u_pair_indices=near,
        pair_diagnostics=tuple(item.to_json_dict() for item in diagnostics),
        parent_patterns=patterns,
        actual_e0_child_families=actual_families,
        actual_e0_record_count=actual_count,
        regular_probe_count=sum(int(item.regular) for item in probes),
        total_probe_count=len(probes),
        disposition=disposition,
        notes=(
            "Physical aggregation census is architecture-level; task probes are recorded separately.",
            "A registered parent pattern is not a source-derived child certificate.",
        ),
    )


def _candidate_backlog(
    architectures: tuple[ParentArchitectureRecord, ...],
) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], set[str]] = {}
    actual = {
        family
        for arch in architectures
        for family in arch.actual_e0_child_families
    }
    for arch in architectures:
        for pattern in arch.parent_patterns:
            child = pattern.candidate_child_family
            if child is None or child in actual:
                continue
            rows.setdefault((pattern.parent_family, child), set()).add(arch.case_id)
    return [
        {
            "parent_family": parent,
            "candidate_child_family": child,
            "source_cases": sorted(cases),
            "status": "REGISTERED_PARENT_PATTERN_ONLY",
            "next_action": "construct and certify a source-derived child before A3",
        }
        for (parent, child), cases in sorted(rows.items())
    ]


def _a3_queue(
    architectures: tuple[ParentArchitectureRecord, ...],
    a1: Mapping[str, Any],
) -> list[dict[str, Any]]:
    family_cases: dict[str, set[str]] = {}
    family_counts: Counter[str] = Counter()
    for arch in architectures:
        for family in arch.actual_e0_child_families:
            family_cases.setdefault(family, set()).add(arch.case_id)
    for family, count in _mapping(
        a1.get("family_counts", {}),
        field="A1 family_counts",
    ).items():
        family_counts[str(family)] += int(count)
    return [
        {
            "family_id": family,
            "e0_specimen_count": int(family_counts[family]),
            "source_cases": sorted(cases),
            "status": "READY_FOR_A3_SUPPORT_PARAMETERIZATION",
            "authority": "actual reconstructible E0 child specimens",
        }
        for family, cases in sorted(family_cases.items())
        if family_counts[family] > 0
    ]


def _write_csvs(
    outdir: Path,
    architectures: tuple[ParentArchitectureRecord, ...],
    probes: tuple[ParentProbeRecord, ...],
) -> None:
    with (outdir / "parent_family_census.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "case_id",
                "control_role",
                "source_chain_id",
                "source_geometry_sha256",
                "regular_probe_count",
                "total_probe_count",
                "exact_u_pair_indices",
                "near_u_pair_indices",
                "parent_patterns",
                "candidate_child_families",
                "actual_e0_child_families",
                "actual_e0_record_count",
                "disposition",
            ),
        )
        writer.writeheader()
        for arch in architectures:
            writer.writerow(
                {
                    "case_id": arch.case_id,
                    "control_role": arch.control_role,
                    "source_chain_id": arch.source_chain_id,
                    "source_geometry_sha256": arch.source_geometry_sha256,
                    "regular_probe_count": arch.regular_probe_count,
                    "total_probe_count": arch.total_probe_count,
                    "exact_u_pair_indices": ";".join(
                        str(v) for v in arch.exact_u_pair_indices
                    ),
                    "near_u_pair_indices": ";".join(
                        str(v) for v in arch.near_u_pair_indices
                    ),
                    "parent_patterns": ";".join(
                        pattern.parent_family for pattern in arch.parent_patterns
                    ),
                    "candidate_child_families": ";".join(
                        pattern.candidate_child_family or ""
                        for pattern in arch.parent_patterns
                    ),
                    "actual_e0_child_families": ";".join(
                        arch.actual_e0_child_families
                    ),
                    "actual_e0_record_count": arch.actual_e0_record_count,
                    "disposition": arch.disposition.value,
                }
            )

    with (outdir / "parent_probes.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "case_id",
                "probe_id",
                "q_seed",
                "p_star",
                "rank_jp",
                "nullity_jp",
                "regular",
                "audit_status",
            ),
        )
        writer.writeheader()
        for probe in probes:
            writer.writerow(
                {
                    "case_id": probe.case_id,
                    "probe_id": probe.probe_id,
                    "q_seed": ";".join(f"{v:.17g}" for v in probe.q_seed),
                    "p_star": ";".join(f"{v:.17g}" for v in probe.p_star),
                    "rank_jp": probe.rank_jp,
                    "nullity_jp": probe.nullity_jp,
                    "regular": str(probe.regular).lower(),
                    "audit_status": probe.audit_status,
                }
            )


def run_parent_campaign(
    *,
    config_path: Path | str,
    a1_manifest_path: Path | str,
    a1_audit_path: Path | str,
    outdir: Path | str | None = None,
) -> dict[str, Any]:
    config = load_a2_config(config_path)
    r3a_config = load_campaign_config(config.r3a_config_path)
    a1 = _load_a1_inputs(
        a1_manifest_path,
        a1_audit_path,
        expected_r3a_config_hash=r3a_config.config_hash,
        require_zero_failures=config.require_a1_zero_roundtrip_failures,
    )
    cases = build_parent_cases(config, r3a_config)

    all_probes: list[ParentProbeRecord] = []
    architecture_records: list[ParentArchitectureRecord] = []
    for case in cases:
        probes = _audit_probes(case)
        all_probes.extend(probes)
        architecture_records.append(_architecture_record(case, probes, config, a1))

    architectures = tuple(architecture_records)
    probes = tuple(all_probes)
    positive = next(
        item for item in architectures if item.case_id == "r3a_positive_control"
    )
    positive_patterns = {
        pattern.parent_family for pattern in positive.parent_patterns
    }
    if config.required_positive_parent_family not in positive_patterns:
        raise ValueError(
            "R3A positive-control structural census no longer recovers "
            f"{config.required_positive_parent_family}"
        )

    queue = _a3_queue(architectures, a1)
    backlog = _candidate_backlog(architectures)
    scope = detector_scope()
    boundary_cases = [
        item.case_id
        for item in architectures
        if item.disposition
        in {
            ArchitectureDisposition.NEAR_PATTERN_REJECTED,
            ArchitectureDisposition.NO_REGISTERED_FOURBAR_PARENT_PATTERN,
        }
    ]
    payload = {
        "schema_version": CONFIG_SCHEMA,
        "program_id": PROGRAM_ID,
        "config_hash": config.config_hash,
        "r3a_config_hash": r3a_config.config_hash,
        "a1_authority": dict(a1),
        "detector_scope": scope,
        "architectures": [item.to_json_dict() for item in architectures],
        "probes": [item.to_json_dict() for item in probes],
        "actual_e0_family_counts": dict(
            sorted(
                (
                    str(family),
                    int(count),
                )
                for family, count in _mapping(
                    a1.get("family_counts", {}),
                    field="A1 family_counts",
                ).items()
            )
        ),
        "a3_family_queue": queue,
        "child_construction_backlog": backlog,
        "architecture_boundary_cases": boundary_cases,
        "notes": [
            "A2 is a source-structure and mechanism-specimen census, not parent reconstruction.",
            "REGISTERED_PARENT_PATTERN_ONLY does not count as an observed child family.",
            "S_phys candidate families are outside the exact-U detector scope.",
        ],
    }

    if outdir is not None:
        target = Path(outdir)
        target.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
        (target / "parent_campaign.json").write_text(text, encoding="utf-8")
        (target / "a3_family_queue.json").write_text(
            json.dumps(queue, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        (target / "child_construction_backlog.json").write_text(
            json.dumps(backlog, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        _write_csvs(target, architectures, probes)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the R3C-A2 5R parent architecture/family census."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--a1-manifest", type=Path, required=True)
    parser.add_argument("--a1-audit", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_parent_campaign(
        config_path=args.config,
        a1_manifest_path=args.a1_manifest,
        a1_audit_path=args.a1_audit,
        outdir=args.outdir,
    )
    summary = {
        "architectures": {
            item["case_id"]: {
                "parent_patterns": [
                    pattern["parent_family"] for pattern in item["parent_patterns"]
                ],
                "actual_e0_child_families": item["actual_e0_child_families"],
                "disposition": item["disposition"],
            }
            for item in payload["architectures"]
        },
        "a3_family_queue": [
            item["family_id"] for item in payload["a3_family_queue"]
        ],
        "child_construction_backlog": [
            item["candidate_child_family"]
            for item in payload["child_construction_backlog"]
        ],
        "outdir": str(args.outdir),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
