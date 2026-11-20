"""H13H-5 receipt stays blocked and does not invent a freeze."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECEIPT = REPO / "results" / "l5_reconstruction" / "h13h" / "h13h5_five_probe_validation.json"
H13H4 = REPO / "results" / "l5_reconstruction" / "h13h" / "h13h4_convergence_study.json"


def test_h13h5_receipt_records_blocked_validation_without_freeze() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    h13h4 = json.loads(H13H4.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "r3a_h13h5_five_probe_validation_v1"
    assert receipt["work_package"] == "H13H-5"
    assert receipt["diagnostic_only"] is True
    assert receipt["accepted_reconstruction"] is False
    assert receipt["source_policy_validated"] is False
    assert receipt["h12_hub_replaced"] is False
    assert receipt["natural_budget_changed"] is False
    assert receipt["h13g_pilot_config_changed"] is False
    assert receipt["frozen_policy"] is None
    assert receipt["p2_p3_evaluated"] is False
    assert receipt["held_out_validation_claimed"] is False
    assert receipt["blocker"]["status"] == "REQUIRED_INTERVALS_UNRESOLVED"
    assert receipt["blocker"]["after_profile"] == "steps192"
    assert receipt["blocker"] == h13h4["blocker"]
    assert receipt["prerequisite"]["path"] == "results/l5_reconstruction/h13h/h13h4_convergence_study.json"
    assert receipt["prerequisite"]["candidate_policy"] is None
    assert receipt["unevaluated_probe_ids"] == [
        "P2_INNER_COMPLETE",
        "P3_INNER_INCOMPLETE",
    ]
