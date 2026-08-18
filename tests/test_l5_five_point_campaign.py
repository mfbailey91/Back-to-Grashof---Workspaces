"""Smoke five-point campaign: manifests, fixtures, reduced compare, no GIF."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grashof_workspace.spatial_experiments.l5_reconstruction.cli import run_stage, write_manifest
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    write_fixture_stage,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.readout import write_render_stage

CONFIG = Path("configs/l5_positive_control_v1.json")


def test_manifest_lists_all_five_probes(tmp_path: Path) -> None:
    path = write_manifest(CONFIG, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["probe_ids"] == [
        "P1_DEEP_COMPLETE",
        "P2_INNER_COMPLETE",
        "P3_INNER_INCOMPLETE",
        "P4_OUTER_COMPLETE",
        "P5_OUTER_INCOMPLETE",
    ]


def test_fixture_and_render_smoke(tmp_path: Path) -> None:
    config = load_campaign_config(CONFIG)
    write_manifest(CONFIG, tmp_path)
    write_fixture_stage(config, tmp_path, list(config.probes))
    for probe in config.probes:
        assert (tmp_path / probe.probe_id / "fixture.json").is_file()
    payload = write_render_stage(config, tmp_path, list(config.probes), mode="smoke", generate_gif=False)
    assert (tmp_path / "index.html").is_file()
    assert (tmp_path / "five_point_summary.png").is_file()
    assert "selected_leaf.gif" not in json.dumps(payload)
    html = (tmp_path / "P1_DEEP_COMPLETE" / "index.html").read_text(encoding="utf-8")
    assert "SCAFFOLD_NO_DATA" in html
    titles = (tmp_path / "P1_DEEP_COMPLETE" / "figures" / "source_control.png").read_bytes()
    assert titles  # file exists; watermark is in HTML and figure titles


def test_compare_without_truth_leaves_raises(tmp_path: Path) -> None:
    write_manifest(CONFIG, tmp_path)
    with pytest.raises(FileNotFoundError):
        run_stage(
            config_path=CONFIG,
            outdir=tmp_path,
            stage="compare",
            mode="smoke",
            probe_id=None,
            resume_from=None,
        )


def test_hash_drift_refuses_resume(tmp_path: Path) -> None:
    write_manifest(CONFIG, tmp_path)
    run_stage(
        config_path=CONFIG,
        outdir=tmp_path,
        stage="manifest",
        mode="smoke",
        probe_id=None,
        resume_from=tmp_path / "manifest.json",
    )
    bad = tmp_path / "bad_manifest.json"
    bad.write_text(json.dumps({"config_hash": "0" * 64, "program_id": "x"}), encoding="utf-8")
    with pytest.raises(ValueError, match="config-hash"):
        run_stage(
            config_path=CONFIG,
            outdir=tmp_path,
            stage="manifest",
            mode="smoke",
            probe_id=None,
            resume_from=bad,
        )


@pytest.mark.stress
def test_full_five_point_campaign_stress(tmp_path: Path) -> None:
    payload = run_stage(
        config_path=CONFIG,
        outdir=tmp_path,
        stage="all",
        mode="smoke",
        probe_id="P1_DEEP_COMPLETE",
        resume_from=None,
    )
    assert payload["program_id"]
