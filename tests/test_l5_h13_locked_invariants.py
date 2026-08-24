"""R3A-H13 locked invariants. H13A and H13E may exist; H12 hub and config stay frozen."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction import (
    cli as l5_cli,
)
from grashof_workspace.spatial_experiments.l5_reconstruction import (
    source_control as h12_source_control,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    load_campaign_config,
)

REPO = Path(__file__).resolve().parents[1]
H12_CONFIG = REPO / "configs" / "l5_positive_control_v1.json"
H13A_CONFIG = REPO / "configs" / "l5_positive_control_h13a_c_domain_v1.json"
COMPACT_MANIFEST = REPO / "results" / "l5_reconstruction" / "r3a" / "compact_manifest.json"
CURRENT_STATUS = REPO / "docs" / "CURRENT_STATUS.md"
H13_MODULE = (
    REPO
    / "src"
    / "grashof_workspace"
    / "spatial_experiments"
    / "l5_reconstruction"
    / "source_control_h13.py"
)
H13_PILOT_CONFIG = REPO / "configs" / "l5_positive_control_h13_source_pilot_v1.json"
LOCKED_RAW_BUNDLE_SHA256 = (
    "d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec"
)


def _top_level_imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_frozen_h12_config_has_no_source_control_policy_version() -> None:
    payload = json.loads(H12_CONFIG.read_text(encoding="utf-8"))
    source_control = payload["source_control"]
    assert "policy_version" not in source_control


def test_compact_hub_remains_h12_full_closeout() -> None:
    manifest = json.loads(COMPACT_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["package_kind"] == "full_closeout"
    assert manifest["campaign_blocker"] == "STITCHING_CONTROL_BLOCKED"
    assert manifest["accepted_reconstruction"] is False
    assert manifest["semantic_revalidation"] is True
    assert manifest["raw_bundle_sha256"] == LOCKED_RAW_BUNDLE_SHA256


def test_current_status_keeps_parent_incomplete_without_new_closeout() -> None:
    text = CURRENT_STATUS.read_text(encoding="utf-8")
    assert "parent_incomplete" in text
    assert "STITCHING_CONTROL_BLOCKED" in text
    assert "H13 opt-in" not in text
    assert "H13 is active" not in text
    assert "source-control component and coverage closure is active" not in text
    assert "CONTROLLED_COVER_ACCEPTED" not in text
    assert "new scientific closeout" not in text.lower()


def test_h12_path_does_not_import_source_control_h13_at_module_level() -> None:
    assert H13_MODULE.is_file()
    assert H13A_CONFIG.is_file()
    assert H13_PILOT_CONFIG.is_file()
    pilot = load_campaign_config(H13_PILOT_CONFIG)
    assert pilot.schema_version == "r3a_l5_positive_control_h13_source_pilot_v1"
    assert pilot.mode("ci").allows_full_campaign_disposition is False
    assert pilot.mode("smoke").allows_full_campaign_disposition is False
    assert pilot.mode("full").allows_full_campaign_disposition is False
    assert h12_source_control.__file__ is not None
    assert l5_cli.__file__ is not None
    cli_top = _top_level_imported_modules(Path(l5_cli.__file__))
    source_top = _top_level_imported_modules(Path(h12_source_control.__file__))
    assert "source_control_h13" not in cli_top
    assert ".source_control_h13" not in cli_top
    assert "source_control_h13" not in source_top
    assert ".source_control_h13" not in source_top
    assert "source_control_h13" not in Path(l5_cli.__file__).read_text(encoding="utf-8")
