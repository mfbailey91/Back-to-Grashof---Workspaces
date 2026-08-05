"""Tests for the combined Sprint 01–06 printable readout."""

from __future__ import annotations

from pathlib import Path

from grashof_workspace.spatial_experiments.sprint01_06_printout import (
    assemble_sprint01_06_payload,
    write_sprint01_06_printout,
)
from grashof_workspace.spatial_experiments.sprint05_readout import S5_IDS
from grashof_workspace.spatial_experiments.sprint06_readout import S6_IDS

REPO_RESULTS = Path(__file__).resolve().parents[1] / "results" / "aligned_terminal_roll"


def test_sprint01_06_printout_payload_and_html(tmp_path: Path) -> None:
    payload = assemble_sprint01_06_payload(REPO_RESULTS)
    assert len(payload["sprints"]) == 7
    assert payload["pass_count"] >= 35
    assert payload["experiment_count"] == payload["pass_count"] + 1
    out = tmp_path / "sprint01_06_printout"
    written = write_sprint01_06_printout(REPO_RESULTS, out)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert written["pass_count"] == payload["pass_count"]
    for exp_id in ("ATR_EXP_001", "ATR_EXP_021", "ATR_EXP_027", "ATR_EXP_032", "ATR_EXP_036"):
        assert exp_id in html
    for exp_id in (*S5_IDS, *S6_IDS):
        assert exp_id in html
    assert "Check-in 6 is the open gate" in html
    assert "DEFERRED" in html
    assert "@media print" in html
    assert (out / "printout.json").is_file()
