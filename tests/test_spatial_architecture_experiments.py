"""Tests for Sprint 03 architecture-comparison experiments and readout."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.spatial_experiments.architecture_experiments import (
    CONTINUATION_PARENT_RECOMMENDATION,
    evaluate_architecture_comparison,
    evaluate_intersecting_pairs_stage_a,
    evaluate_local_nred_steps,
    evaluate_principal_angles,
    evaluate_urlike_stage_a,
    run_all_architecture_experiments,
)
from grashof_workspace.spatial_experiments.sprint03_readout import (
    M3_WARNING,
    S3_IDS,
    assemble_sprint03_payload,
    write_sprint03_readout,
)


def test_exp_011_intersecting_pairs_stage_a() -> None:
    result = evaluate_intersecting_pairs_stage_a()
    assert result["status"] == "PASS"
    assert result["snapshot"]["regular"] is True


def test_exp_012_urlike_stage_a() -> None:
    result = evaluate_urlike_stage_a()
    assert result["status"] == "PASS"
    assert result["snapshot"]["regular"] is True


def test_exp_013_principal_angles() -> None:
    result = evaluate_principal_angles()
    assert result["status"] == "PASS"


def test_exp_014_local_steps() -> None:
    result = evaluate_local_nred_steps()
    assert result["status"] == "PASS"


def test_exp_015_comparison_records_parent_without_autoselect() -> None:
    result = evaluate_architecture_comparison()
    assert result["status"] == "PASS"
    assert result["continuation_parent_recommendation"] == CONTINUATION_PARENT_RECOMMENDATION
    assert result["continuation_parent_auto_selected"] is False


def test_runner_and_readout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "results").mkdir(parents=True)
    results = run_all_architecture_experiments(repo)
    assert [r["experiment_id"] for r in results] == list(S3_IDS)
    assert all(r["status"] == "PASS" for r in results)
    results_root = repo / "results" / "aligned_terminal_roll"
    payload = assemble_sprint03_payload(results_root)
    assert payload["human_gate_required"] is False
    assert payload["checkin_interpretation"] == "PARTIALLY SUPPORTED"
    assert payload["checkin_decision"] == "CONTINUE WITH CHANGED SCOPE"
    assert payload["warning"] == M3_WARNING
    out = tmp_path / "sprint03_readout"
    written = write_sprint03_readout(results_root, out)
    html = (out / "index.html").read_text(encoding="utf-8")
    dumped = json.loads((out / "readout.json").read_text(encoding="utf-8"))
    assert dumped["pass_count"] == written["pass_count"] == 5
    for exp_id in S3_IDS:
        assert exp_id in html
    assert "Check-in 3 is approved with changed scope" in html
    assert "do not establish SUUR equivalence" in html
    assert "IntersectingPairsAligned6R" in html
