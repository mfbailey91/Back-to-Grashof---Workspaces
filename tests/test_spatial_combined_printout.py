"""Tests for the combined Sprint 01–04 printable readout."""

from __future__ import annotations

from pathlib import Path

from grashof_workspace.spatial_experiments.combined_printout import (
    assemble_combined_payload,
    write_combined_printout,
)

REPO_RESULTS = Path(__file__).resolve().parents[1] / "results" / "aligned_terminal_roll"


def test_combined_printout_payload_and_html(tmp_path: Path) -> None:
    payload = assemble_combined_payload(REPO_RESULTS)
    assert payload["pass_count"] == 20
    assert payload["experiment_count"] == 20
    assert len(payload["sprints"]) == 4
    out = tmp_path / "sprint01_04_printout"
    written = write_combined_printout(REPO_RESULTS, out)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert written["pass_count"] == 20
    for exp_id in ("ATR_EXP_001", "ATR_EXP_010", "ATR_EXP_015", "ATR_EXP_020"):
        assert exp_id in html
    assert "Check-in 4 remains a human gate" in html
    assert "@media print" in html
