"""R3A0 scaffold tests: enums, frozen records, config, JSON, empty campaign."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from grashof_workspace.spatial_experiments.l5_reconstruction.cli import write_manifest
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    ACCEPTED_CHILD_STATUSES,
    LeafConstructionKind,
    PointingSolveStatus,
    ReconstructionDisposition,
    empty_campaign_result,
    json_dumps_strict,
    load_campaign_config,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def test_enum_values() -> None:
    assert PointingSolveStatus.FOUND.value == "FOUND"
    assert PointingSolveStatus.NOT_FOUND_AT_DECLARED_BUDGET.value == "NOT_FOUND_AT_DECLARED_BUDGET"
    assert PointingSolveStatus.UNRESOLVED.value == "UNRESOLVED"
    assert LeafConstructionKind.VIRTUAL_ORIENTATION_COORDINATE.value == "virtual_orientation_coordinate"
    assert ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION.value == "PASS_AT_DECLARED_RESOLUTION"
    assert ACCEPTED_CHILD_STATUSES == {"EXACT_GLOBAL", "EXACT_ON_COMPONENT"}


def test_config_loads_deterministically() -> None:
    a = load_campaign_config(CONFIG)
    b = load_campaign_config(CONFIG)
    assert a.config_hash == b.config_hash
    assert len(a.config_hash) == 64
    assert a.program_id == "R3A_L5_FIVE_POINT_NATURAL_LEAF_RECONSTRUCTION"
    ids = [p.probe_id for p in a.probes]
    assert ids == [
        "P1_DEEP_COMPLETE",
        "P2_INNER_COMPLETE",
        "P3_INNER_INCOMPLETE",
        "P4_OUTER_COMPLETE",
        "P5_OUTER_INCOMPLETE",
    ]
    assert len(set(ids)) == 5


def test_records_are_immutable() -> None:
    config = load_campaign_config(CONFIG)
    with pytest.raises(FrozenInstanceError):
        config.geometry.L1 = 2.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config.probes[0].rho = 0.0  # type: ignore[misc]


def test_json_serialization_forbids_nan() -> None:
    config = load_campaign_config(CONFIG)
    campaign = empty_campaign_result(config)
    text = json_dumps_strict(campaign.to_json_dict())
    json.loads(text)
    json.dumps(campaign.to_json_dict(), allow_nan=False)
    assert "NaN" not in text
    assert campaign.accepted_reconstruction is False
    assert campaign.disposition is ReconstructionDisposition.UNRESOLVED
    assert campaign.comparisons == ()


def test_manifest_cli_writes_planned_scaffold(tmp_path: Path) -> None:
    path = write_manifest(CONFIG, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["program_id"] == "R3A_L5_FIVE_POINT_NATURAL_LEAF_RECONSTRUCTION"
    assert payload["config_hash"]
    assert payload["probe_ids"] == [
        "P1_DEEP_COMPLETE",
        "P2_INNER_COMPLETE",
        "P3_INNER_INCOMPLETE",
        "P4_OUTER_COMPLETE",
        "P5_OUTER_INCOMPLETE",
    ]
    assert payload["accepted_reconstruction"] is False
    statuses = payload["stage_statuses"]
    assert statuses["manifest"] == "COMPLETE"
    assert all(statuses[name] == "PLANNED" for name in statuses if name != "manifest")
    json.dumps(payload, allow_nan=False)
