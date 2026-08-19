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
    json_dumps_strict,
    load_campaign_config,
    resolve_stage_budgets,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    write_fixture_stage,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.readout import (
    PROBE_FIGURE_NAMES,
    SCAFFOLD_WATERMARK,
    write_render_stage,
)

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
    assert SCAFFOLD_WATERMARK in html
    titles = (tmp_path / "P1_DEEP_COMPLETE" / "figures" / "source_control_curves.png").read_bytes()
    assert titles


def test_placeholder_render_is_watermarked_or_refused(tmp_path: Path) -> None:
    config = load_campaign_config(CONFIG)
    write_manifest(CONFIG, tmp_path)
    write_fixture_stage(config, tmp_path, [config.probe("P1_DEEP_COMPLETE")])
    write_render_stage(config, tmp_path, [config.probe("P1_DEEP_COMPLETE")], mode="ci", generate_gif=True)
    html = (tmp_path / "P1_DEEP_COMPLETE" / "index.html").read_text(encoding="utf-8")
    assert SCAFFOLD_WATERMARK in html
    assert not (tmp_path / "P1_DEEP_COMPLETE" / "figures" / "selected_leaf.gif").exists()
    for name in PROBE_FIGURE_NAMES:
        assert (tmp_path / "P1_DEEP_COMPLETE" / "figures" / name).is_file()


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


def _sample(s: float, pointing: tuple[float, float, float], q: list[float], lam: float) -> dict:
    return {
        "s": s,
        "x": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "q_source": q,
        "pointing": list(pointing),
        "lambda_recovered": lam,
        "closure_residual": 1e-9,
        "position_residual_m": 1e-9,
        "orientation_error_rad": 1e-9,
        "pointing_error_rad": 1e-9,
        "joint_lift_error_rad": 1e-9,
        "family_coordinate_error_rad": 1e-9,
        "rank_j": 6,
        "nullity_j": 1,
        "chart_singularity": False,
    }


def _write_synthetic_artifacts(outdir: Path, config, probe) -> None:
    probe_dir = outdir / probe.probe_id
    probe_dir.mkdir(parents=True, exist_ok=True)
    q = [0.1, 0.2, 0.3, 0.4, 0.5]
    cells = [
        {
            "cell_id": "c0",
            "vertex_or_barycenter_direction": [1.0, 0.0, 0.0],
            "oracle_status": "FEASIBLE",
            "direct_status": "FOUND",
            "direct_cluster_count": 1,
            "best_position_residual_m": 1e-9,
            "best_pointing_error_rad": 1e-9,
            "strict_reference_eligible": True,
        },
        {
            "cell_id": "c1",
            "vertex_or_barycenter_direction": [0.0, 1.0, 0.0],
            "oracle_status": "INFEASIBLE",
            "direct_status": "NOT_FOUND_AT_DECLARED_BUDGET",
            "direct_cluster_count": 0,
            "best_position_residual_m": None,
            "best_pointing_error_rad": None,
            "strict_reference_eligible": True,
        },
    ]
    (probe_dir / "direct_truth.json").write_text(
        json_dumps_strict({"probe_id": probe.probe_id, "confirmation_cells": cells}),
        encoding="utf-8",
    )
    (probe_dir / "source_control.json").write_text(
        json_dumps_strict(
            {
                "probe_id": probe.probe_id,
                "pointing_samples": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                "fibers": [
                    {
                        "c": 0.2,
                        "pointing_samples": [[1.0, 0.0, 0.0], [0.7071, 0.7071, 0.0]],
                        "q_samples": [q],
                        "branch_status": "returned",
                    }
                ],
                "unresolved_c_intervals": [],
            }
        ),
        encoding="utf-8",
    )
    accepted = {
        "spec": {"leaf_id": "acc0", "chart_id": "ZYZ_WORLD", "lambda_fixed": 0.1},
        "family_parameter_value": 0.1,
        "accepted_for_reconstruction": True,
        "closed_mechanism_status": "EXACT_ON_COMPONENT",
        "samples": [_sample(0.0, (1.0, 0.0, 0.0), q, 0.1), _sample(0.2, (0.0, 1.0, 0.0), q, 0.1)],
    }
    excluded = {
        "spec": {"leaf_id": "exc0", "chart_id": "ZYZ_WORLD", "lambda_fixed": 0.8},
        "family_parameter_value": 0.8,
        "accepted_for_reconstruction": False,
        "closed_mechanism_status": "LOCAL_ONLY",
        "samples": [_sample(0.0, (0.0, 0.0, 1.0), q, 0.8)],
    }
    (probe_dir / "natural_family.json").write_text(
        json_dumps_strict(
            {
                "probe_id": probe.probe_id,
                "leaves": [accepted, excluded],
                "unresolved_lambda_intervals": [[0.4, 0.6]],
            }
        ),
        encoding="utf-8",
    )
    (probe_dir / "comparison.json").write_text(
        json_dumps_strict(
            {
                "probe_id": probe.probe_id,
                "disposition": "PARTIAL",
                "point_classification": "PARTIAL",
                "failure_localization": "synthetic",
            }
        ),
        encoding="utf-8",
    )
    (outdir / "campaign.json").write_text(
        json_dumps_strict(
            {
                "program_id": config.program_id,
                "config_hash": config.config_hash,
                "accepted_reconstruction": False,
                "disposition": "PARTIAL",
            }
        ),
        encoding="utf-8",
    )


def test_render_reads_json_artifacts(tmp_path: Path) -> None:
    config = load_campaign_config(CONFIG)
    probe = config.probe("P1_DEEP_COMPLETE")
    write_manifest(CONFIG, tmp_path, mode="ci")
    write_fixture_stage(config, tmp_path, [probe], mode="ci")
    _write_synthetic_artifacts(tmp_path, config, probe)
    payload = write_render_stage(config, tmp_path, [probe], mode="ci", generate_gif=False)
    html = (tmp_path / probe.probe_id / "index.html").read_text(encoding="utf-8")
    assert SCAFFOLD_WATERMARK not in html
    assert probe.probe_id in html
    assert "ci" in html
    assert config.config_hash in html
    assert "stage_status=COMPLETE" in html
    assert "PARTIAL" in html
    assert "declared_resolution" in html
    assert "oracle" in html.casefold()
    assert "direct" in html.casefold()
    assert "source control" in html.casefold()
    assert "natural accepted" in html.casefold()
    assert "natural excluded" in html.casefold()
    assert "difference maps" in html.casefold()
    assert "accepted and excluded leaves are plotted separately" in html.casefold()
    for name in PROBE_FIGURE_NAMES:
        assert (tmp_path / probe.probe_id / "figures" / name).is_file()
    assert "selected_leaf.gif" not in json.dumps(payload)


def test_repeatable_probe_flag_selects_p1_and_p3() -> None:
    from grashof_workspace.spatial_experiments.l5_reconstruction.cli import build_parser

    args = build_parser().parse_args(
        [
            "--config",
            str(CONFIG),
            "--outdir",
            "tmp",
            "--mode",
            "ci",
            "--probe",
            "P1_DEEP_COMPLETE",
            "--probe",
            "P3_INNER_INCOMPLETE",
        ]
    )
    assert args.probe_ids == ["P1_DEEP_COMPLETE", "P3_INNER_INCOMPLETE"]


def test_p1_p3_end_to_end_smoke(tmp_path: Path) -> None:
    payload = run_stage(
        config_path=CONFIG,
        outdir=tmp_path,
        stage="all",
        mode="ci",
        probe_id=None,
        resume_from=None,
        probe_ids=("P1_DEEP_COMPLETE", "P3_INNER_INCOMPLETE"),
    )
    assert payload["accepted_reconstruction"] is False
    for probe_id in ("P1_DEEP_COMPLETE", "P3_INNER_INCOMPLETE"):
        html = (tmp_path / probe_id / "index.html").read_text(encoding="utf-8")
        assert probe_id in html
        assert (tmp_path / probe_id / "figures" / "three_way_cell_comparison.png").is_file()
        assert (tmp_path / probe_id / "figures" / "accepted_vs_excluded_leaves.png").is_file()
        assert not (tmp_path / probe_id / "figures" / "selected_leaf.gif").exists()
    hub = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "accepted_reconstruction=False" in hub
    assert (tmp_path / "campaign.json").is_file()


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
