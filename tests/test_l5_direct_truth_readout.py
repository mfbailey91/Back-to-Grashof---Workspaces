"""Direct-truth JSON readout is finite and split-tagged."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import write_truth_stage
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config

CONFIG = "configs/l5_positive_control_v1.json"


def test_truth_stage_writes_split_payloads(tmp_path: Path) -> None:
    config = load_campaign_config(CONFIG)
    probe = config.probe("P1_DEEP_COMPLETE")
    payload = write_truth_stage(
        config, tmp_path, [probe], mode="smoke", target_limit=2, sobol_count=4, max_nfev=40
    )
    assert payload["stage"] == "truth"
    text = (tmp_path / "P1_DEEP_COMPLETE" / "direct_truth.json").read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["discovery"]["split"] == "discovery"
    assert data["confirmation"]["split"] == "confirmation"
    assert data["discovery"]["icosphere_level"] != data["confirmation"]["icosphere_level"]
    json.dumps(data, allow_nan=False)
    assert "NaN" not in text
