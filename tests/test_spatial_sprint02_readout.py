"""Tests for the Sprint 02 HTML readout."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from grashof_workspace.spatial_experiments.sprint02_readout import (
    M2_WARNING,
    S2_IDS,
    assemble_sprint02_payload,
    write_sprint02_readout,
)

REPO_RESULTS = Path(__file__).resolve().parents[1] / "results" / "aligned_terminal_roll"


def test_sprint02_payload_and_html(tmp_path: Path) -> None:
    dest = tmp_path / "aligned_terminal_roll"
    for exp_id in S2_IDS:
        shutil.copytree(REPO_RESULTS / exp_id, dest / exp_id)
    payload = assemble_sprint02_payload(dest)
    assert [exp["experiment_id"] for exp in payload["experiments"]] == list(S2_IDS)
    assert payload["pass_count"] == 5
    assert payload["human_gate_required"] is True
    assert payload["warning"] == M2_WARNING
    out = tmp_path / "sprint02_readout"
    written = write_sprint02_readout(dest, out)
    html = (out / "index.html").read_text(encoding="utf-8")
    dumped = json.loads((out / "readout.json").read_text(encoding="utf-8"))
    assert dumped["pass_count"] == written["pass_count"] == 5
    for exp_id in S2_IDS:
        assert exp_id in html
    assert "Check-in 2 remains a human gate" in html
