"""Tests for Sprint 04 manifold experiments and readout."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.spatial_experiments.manifold_experiments import (
    SOURCE_IDENTIFIER,
    evaluate_coordinate_map_closure,
    evaluate_intersecting_pairs_patch,
    evaluate_negative_control,
    evaluate_pair_persistence,
    evaluate_urlike_patch,
    run_all_manifold_experiments,
)
from grashof_workspace.spatial_experiments.sprint04_readout import (
    M4_WARNING,
    S4_IDS,
    assemble_sprint04_payload,
    write_sprint04_readout,
)


def test_exp_016_persistence() -> None:
    assert evaluate_pair_persistence()["status"] == "PASS"


def test_exp_017_negative_control() -> None:
    assert evaluate_negative_control()["status"] == "PASS"


def test_exp_018_closure() -> None:
    assert evaluate_coordinate_map_closure()["status"] == "PASS"


def test_exp_019_ip_patch() -> None:
    result = evaluate_intersecting_pairs_patch()
    assert result["status"] == "PASS"
    assert result["metrics"]["phi_defined_on_regular"] is True


def test_exp_020_urlike_patch() -> None:
    result = evaluate_urlike_patch()
    assert result["status"] == "PASS"
    assert result["metrics"]["phi_defined_on_regular"] is None


def test_runner_source_identifier_and_readout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "results").mkdir(parents=True)
    results = run_all_manifold_experiments(repo)
    assert [r["experiment_id"] for r in results] == list(S4_IDS)
    assert all(r["status"] == "PASS" for r in results)
    results_root = repo / "results" / "aligned_terminal_roll"
    manifest = json.loads((results_root / "ATR_EXP_016" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_identifier"] == SOURCE_IDENTIFIER
    payload = assemble_sprint04_payload(results_root)
    assert payload["human_gate_required"] is True
    assert payload["warning"] == M4_WARNING
    out = tmp_path / "sprint04_readout"
    written = write_sprint04_readout(results_root, out)
    html = (out / "index.html").read_text(encoding="utf-8")
    dumped = json.loads((out / "readout.json").read_text(encoding="utf-8"))
    assert dumped["pass_count"] == written["pass_count"] == 5
    for exp_id in S4_IDS:
        assert exp_id in html
    assert "Check-in 4 remains a human gate" in html
    assert SOURCE_IDENTIFIER in html
