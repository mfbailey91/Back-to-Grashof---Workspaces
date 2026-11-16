"""H13H-0 baseline receipt stays tied to protected evidence and the historical pilot."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RECEIPT_JSON = REPO / "results" / "l5_reconstruction" / "h13h" / "h13h0_baseline_receipt.json"
RECEIPT_MD = REPO / "docs" / "methods" / "R3A_H13H_BASELINE_RECEIPT.md"
H13G_SHA = "81f1e2059040b74e503d166f4e6588922ddafb8c"
LOCKED_BUNDLE = "d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec"
RAW_PILOT = REPO / "outputs" / "r3a_h13g_source_pilot"


def _receipt_module():
    path = REPO / "scripts" / "write_h13h0_baseline_receipt.py"
    spec = importlib.util.spec_from_file_location("write_h13h0_baseline_receipt", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_text(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def _load_receipt() -> dict:
    payload = json.loads(RECEIPT_JSON.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_h13h0_receipt_preserves_protected_invariants() -> None:
    receipt = _load_receipt()
    module = _receipt_module()
    assert receipt["schema_version"] == "r3a_h13h0_baseline_receipt_v1"
    assert receipt["work_package"] == "H13H-0"
    assert receipt["source_policy_validated"] is False
    assert receipt["accepted_reconstruction"] is False
    assert receipt["h12_hub_replaced"] is False
    assert receipt["protected"] == module.collect_protected()
    hub = receipt["protected"]["h12_hub"]
    assert hub["raw_bundle_sha256"] == LOCKED_BUNDLE
    assert hub["package_kind"] == "full_closeout"
    assert hub["campaign_blocker"] == "STITCHING_CONTROL_BLOCKED"
    assert hub["accepted_reconstruction"] is False
    assert receipt["protected"]["configs"]["h12"]["full_allows_campaign_disposition"] is True
    assert receipt["protected"]["configs"]["h13g"]["full_allows_campaign_disposition"] is False


def test_h13h0_receipt_records_dirty_historical_pilot() -> None:
    receipt = _load_receipt()
    pilot = receipt["historical_pilot"]
    inspection = receipt["inspection"]
    assert pilot["classification"] == "historical_dirty_producer"
    assert pilot["fresh_reproduction"] is False
    assert pilot["clean_h13g_checkout"] is False
    assert pilot["producer_dirty_tree"] is True
    assert pilot["dirty_diff"] == "unavailable"
    assert pilot["solver_wall_time_status"] == "unavailable"
    assert pilot["natural_family_interpreted"] is False
    assert pilot["campaign_probe_ids"] == [
        "P1_DEEP_COMPLETE",
        "P4_OUTER_COMPLETE",
        "P5_OUTER_INCOMPLETE",
    ]
    assert pilot["manifest_probe_ids"] == [
        "P1_DEEP_COMPLETE",
        "P2_INNER_COMPLETE",
        "P3_INNER_INCOMPLETE",
        "P4_OUTER_COMPLETE",
        "P5_OUTER_INCOMPLETE",
    ]
    assert pilot["package_kind"] == "diagnostic"
    assert pilot["allows_full_campaign_disposition"] is False
    assert inspection["h13g_implementation_sha"] == H13G_SHA
    assert inspection["h13g_is_ancestor_of_head"] is True
    assert inspection["h13g_is_ancestor_of_origin_main"] is False
    assert inspection["h13g_commit_contains_source_control_h13g"] is True
    assert inspection["h13g_parent_contains_source_control_h13g"] is False
    assert pilot["producer_git_commit"] == inspection["h13g_parent_sha"]
    text = RECEIPT_MD.read_text(encoding="utf-8")
    assert H13G_SHA in text
    assert LOCKED_BUNDLE in text
    assert "historical_dirty_producer" in text
    assert "Source policy validated: false" in text
    assert "A fresh reproduction on a clean H13G checkout was not run." in text


def test_h13h0_ancestry_matches_recorded_git_objects() -> None:
    inspection = _load_receipt()["inspection"]
    parent = _git_text(["rev-parse", f"{H13G_SHA}^"])
    assert parent == inspection["h13g_parent_sha"]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", H13G_SHA, inspection["origin_main_sha"]],
        cwd=REPO,
        check=False,
    )
    assert ancestor.returncode != 0
    parents = _git_text(["log", "-1", "--format=%P", inspection["origin_main_sha"]]).split()
    assert parents == inspection["origin_main_parents"]
    assert inspection["origin_main_parents"][1] == inspection["h13g_parent_sha"]


def test_h13h0_receipt_matches_historical_pilot_outputs() -> None:
    if not RAW_PILOT.is_dir():
        pytest.skip("historical H13G pilot outputs are gitignored and absent")
    receipt = _load_receipt()
    module = _receipt_module()
    assert receipt["historical_pilot"] == module.collect_historical_pilot()
