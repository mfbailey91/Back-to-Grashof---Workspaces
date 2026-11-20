"""H13H-4 receipt stays diagnostic and does not invent a candidate."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECEIPT = REPO / "results" / "l5_reconstruction" / "h13h" / "h13h4_convergence_study.json"
H13G = REPO / "configs" / "l5_positive_control_h13g_source_pilot_v1.json"


def test_h13h4_receipt_records_blocked_study_without_acceptance() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "r3a_h13h4_convergence_study_v1"
    assert receipt["work_package"] == "H13H-4"
    assert receipt["diagnostic_only"] is True
    assert receipt["accepted_reconstruction"] is False
    assert receipt["source_policy_validated"] is False
    assert receipt["h12_hub_replaced"] is False
    assert receipt["natural_budget_changed"] is False
    assert receipt["h13g_pilot_config_changed"] is False
    assert receipt["candidate_policy"] is None
    assert receipt["blocker"]["status"] == "REQUIRED_INTERVALS_UNRESOLVED"
    assert receipt["blocker"]["after_profile"] == "steps192"
    assert receipt["executed_profiles"] == ["baseline", "steps96", "steps192"]
    assert set(receipt["gates"]) == {"baseline", "steps96", "steps192"}
    assert all(gate["passed"] is False for gate in receipt["gates"].values())
    assert receipt["comparisons"] == []
    assert receipt["probe_ids"] == [
        "P1_DEEP_COMPLETE",
        "P4_OUTER_COMPLETE",
        "P5_OUTER_INCOMPLETE",
    ]
    skipped = {item["axis"] for item in receipt["skipped_axes"]}
    assert "step_resolution" in skipped
    assert "raster_depth" in skipped
    h13g = json.loads(H13G.read_text(encoding="utf-8"))
    assert "continuation_max_steps_per_ray" not in h13g["source_control"]
    assert h13g["campaign_modes"]["full"]["continuation_steps"] == 48
