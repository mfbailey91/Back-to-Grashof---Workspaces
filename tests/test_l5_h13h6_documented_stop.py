"""H13H-6 receipt stays a documented stop without freeze or H13I authorization."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECEIPT = REPO / "results" / "l5_reconstruction" / "h13h" / "h13h6_documented_stop.json"
H13H5 = REPO / "results" / "l5_reconstruction" / "h13h" / "h13h5_five_probe_validation.json"
FROZEN_CONFIG = REPO / "configs" / "l5_positive_control_h13h_source_frozen_v1.json"


def test_h13h6_receipt_records_documented_stop_without_freeze() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    h13h5 = json.loads(H13H5.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "r3a_h13h6_documented_stop_v1"
    assert receipt["work_package"] == "H13H-6"
    assert receipt["closeout_kind"] == "documented_stop"
    assert receipt["diagnostic_only"] is True
    assert receipt["accepted_reconstruction"] is False
    assert receipt["source_policy_validated"] is False
    assert receipt["h12_hub_replaced"] is False
    assert receipt["natural_budget_changed"] is False
    assert receipt["h13g_pilot_config_changed"] is False
    assert receipt["frozen_policy"] is None
    assert receipt["frozen_config_created"] is False
    assert not FROZEN_CONFIG.exists()
    assert receipt["blocker"]["status"] == "REQUIRED_INTERVALS_UNRESOLVED"
    assert receipt["blocker"]["after_profile"] == "steps192"
    assert receipt["blocker"] == h13h5["blocker"]
    assert receipt["h13i_handoff"]["authorized"] is False
    assert receipt["adr"] == "ADR-063"
    assert [item["work_package"] for item in receipt["evidence_chain"]] == [
        "H13H-0",
        "H13H-2",
        "H13H-3",
        "H13H-4",
        "H13H-5",
    ]
