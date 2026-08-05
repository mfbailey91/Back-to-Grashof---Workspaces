"""Tests for the Sprint 01 HTML readout generator."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from grashof_workspace.spatial_experiments.readout import (
    EXPERIMENT_IDS,
    M1_WARNING,
    assemble_sprint01_payload,
    render_sprint01_html,
    write_readout_artifacts,
)

REPO_RESULTS = Path(__file__).resolve().parents[1] / "results" / "aligned_terminal_roll"


def _copy_experiment_tree(tmp_path: Path) -> Path:
    dest_root = tmp_path / "aligned_terminal_roll"
    for exp_id in EXPERIMENT_IDS:
        shutil.copytree(REPO_RESULTS / exp_id, dest_root / exp_id)
    return dest_root


def test_assemble_payload_from_copied_results(tmp_path: Path) -> None:
    results_root = _copy_experiment_tree(tmp_path)
    payload = assemble_sprint01_payload(results_root)
    assert [exp["experiment_id"] for exp in payload["experiments"]] == list(EXPERIMENT_IDS)
    assert payload["pass_count"] == 5
    assert all(exp["status"] == "PASS" for exp in payload["experiments"])
    assert payload["human_gate_required"] is False
    assert "Check-in 1 is approved" in payload["next_stage"]
    assert payload["fd_refinement"]
    assert payload["warning"] == M1_WARNING


def test_render_html_contains_ids_and_m1_warning(tmp_path: Path) -> None:
    results_root = _copy_experiment_tree(tmp_path)
    payload = assemble_sprint01_payload(results_root)
    payload["fd_figure"] = "figures/fd_refinement_ATR_EXP_005.png"
    html = render_sprint01_html(payload)
    for exp_id in EXPERIMENT_IDS:
        assert exp_id in html
    assert "does not establish 6R rank or nullity" in html
    assert ">authorized<" in html or "authorized" in html


def test_write_readout_artifacts(tmp_path: Path) -> None:
    results_root = _copy_experiment_tree(tmp_path)
    out_dir = tmp_path / "sprint01_readout"
    payload = write_readout_artifacts(results_root, out_dir)
    assert (out_dir / "index.html").is_file()
    assert (out_dir / "readout.json").is_file()
    assert (out_dir / "figures" / "fd_refinement_ATR_EXP_005.png").is_file()
    for exp_id in EXPERIMENT_IDS:
        assert (out_dir / "figures" / f"residuals_{exp_id}.png").is_file()
    dumped = json.loads((out_dir / "readout.json").read_text(encoding="utf-8"))
    assert dumped["pass_count"] == payload["pass_count"] == 5
    html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "ATR_EXP_001" in html
    assert "M1" in html or "nullity" in html
