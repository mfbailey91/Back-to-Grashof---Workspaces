"""Smoke five-point campaign: manifests, fixtures, reduced compare, no GIF."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grashof_workspace.spatial_experiments.l5_reconstruction.cli import run_stage, write_manifest
from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import (
    campaign_reconstruction_accepted,
    pointing_set_metrics,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CellClass,
    CompletenessLabel,
    ReconstructionDisposition,
    ThreeWayReconstructionResult,
    load_campaign_config,
    resolve_stage_budgets,
)
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


def _perfect_metrics():
    return pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (True, True, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        covered_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        refinement_delta=0.0,
    )


def _passing_comparison(probe_id: str, *, expected_complete: bool) -> ThreeWayReconstructionResult:
    metrics = _perfect_metrics()
    label = CompletenessLabel.COMPLETE if expected_complete else CompletenessLabel.PARTIAL
    return ThreeWayReconstructionResult(
        probe_id=probe_id,
        oracle_complete=expected_complete,
        direct_complete=expected_complete,
        source_control_metrics=metrics,
        natural_leaf_metrics=metrics,
        point_classification=label,
        disposition=ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION,
        failure_localization="synthetic pass",
        direct_vs_oracle=metrics,
        source_vs_direct=metrics,
        natural_vs_direct=metrics,
    )


def test_smoke_and_ci_cannot_issue_full_campaign_disposition() -> None:
    config = load_campaign_config(CONFIG)
    comparisons = tuple(
        _passing_comparison(probe.probe_id, expected_complete=probe.expected_pointing_complete)
        for probe in config.probes
    )
    smoke = resolve_stage_budgets(config, "smoke")
    ci = resolve_stage_budgets(config, "ci")
    full = resolve_stage_budgets(config, "full")
    assert campaign_reconstruction_accepted(comparisons, config.probes, smoke) is False
    assert campaign_reconstruction_accepted(comparisons, config.probes, ci) is False
    assert campaign_reconstruction_accepted(comparisons, config.probes, full) is True


def test_campaign_requires_classification_to_match_oracle() -> None:
    config = load_campaign_config(CONFIG)
    full = resolve_stage_budgets(config, "full")
    comparisons = tuple(
        _passing_comparison(probe.probe_id, expected_complete=probe.expected_pointing_complete)
        for probe in config.probes
    )
    mismatched = list(comparisons)
    mismatched[2] = ThreeWayReconstructionResult(
        probe_id=comparisons[2].probe_id,
        oracle_complete=False,
        direct_complete=False,
        source_control_metrics=comparisons[2].source_control_metrics,
        natural_leaf_metrics=comparisons[2].natural_leaf_metrics,
        point_classification=CompletenessLabel.COMPLETE,
        disposition=ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION,
        failure_localization="synthetic mismatch",
        direct_vs_oracle=comparisons[2].direct_vs_oracle,
        source_vs_direct=comparisons[2].source_vs_direct,
        natural_vs_direct=comparisons[2].natural_vs_direct,
    )
    assert campaign_reconstruction_accepted(tuple(mismatched), config.probes, full) is False


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
