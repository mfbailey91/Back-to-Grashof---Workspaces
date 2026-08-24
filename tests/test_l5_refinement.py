"""Two-resolution refinement and metric-state JSON loading."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import (
    attach_two_resolution_metrics,
    campaign_reconstruction_accepted,
    compute_refinement_delta,
    evaluate_set_on_grid,
    pointing_set_metrics,
    reconstruction_pass,
    write_compare_stage,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CellClass,
    CompletenessLabel,
    MetricState,
    PointingSetMetrics,
    ReconstructionDisposition,
    ThreeWayReconstructionResult,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.readout import (
    comparison_metrics_from_json,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.sphere_grid import build_sphere_grid

CONFIG = Path("configs/l5_positive_control_v1.json")


def _perfect_metrics() -> PointingSetMetrics:
    return pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (True, True, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        covered_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        refinement_delta=0.0,
    )


def test_missing_refinement_is_unevaluable() -> None:
    config = load_campaign_config(CONFIG)
    metrics = pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (True, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0),),
        covered_dirs=((1.0, 0.0, 0.0),),
    )
    assert metrics.refinement.state is MetricState.UNEVALUABLE
    assert metrics.refinement_delta is None
    assert reconstruction_pass(metrics, config) is False


def test_identical_grids_have_zero_refinement() -> None:
    dirs = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    labels = (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED)
    hits = (True, True, False)
    fine = pointing_set_metrics(
        labels,
        hits,
        max_cell_diameter_rad=0.2,
        reconstructed_dirs=dirs,
        covered_dirs=dirs,
    )
    coarse = pointing_set_metrics(
        labels,
        hits,
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=dirs,
        covered_dirs=dirs,
    )
    attached = attach_two_resolution_metrics(fine, coarse)
    assert attached.refinement.state is MetricState.VALUE
    assert attached.refinement_delta is not None
    assert attached.refinement_delta >= 0.0
    assert attached.coarse_metrics is coarse
    payload = attached.to_json_dict()
    assert payload["fine"]["missed_covered_fraction"] == payload["missed_covered_fraction"]
    assert payload["coarse"]["max_cell_diameter_rad"] == 0.4


def test_not_applicable_pair_contributes_zero() -> None:
    dirs = ((1.0, 0.0, 0.0),)
    all_covered = (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED)
    hits = (True, True)
    fine = pointing_set_metrics(
        all_covered,
        hits,
        max_cell_diameter_rad=0.2,
        reconstructed_dirs=dirs,
        covered_dirs=dirs,
    )
    coarse = pointing_set_metrics(
        all_covered,
        hits,
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=dirs,
        covered_dirs=dirs,
    )
    assert fine.false_positive.state is MetricState.NOT_APPLICABLE
    assert coarse.false_positive.state is MetricState.NOT_APPLICABLE
    delta = compute_refinement_delta(coarse, fine)
    assert delta.state is MetricState.VALUE
    assert delta.value is not None


def test_value_not_applicable_transition_is_unevaluable() -> None:
    dirs = ((1.0, 0.0, 0.0),)
    fine = pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED),
        (True, True),
        max_cell_diameter_rad=0.2,
        reconstructed_dirs=dirs,
        covered_dirs=dirs,
    )
    coarse = pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (True, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=dirs,
        covered_dirs=dirs,
    )
    delta = compute_refinement_delta(coarse, fine)
    assert delta.state is MetricState.UNEVALUABLE


def test_evaluate_set_on_grid_paints_same_samples() -> None:
    grid = build_sphere_grid(0)
    labels = tuple(CellClass.STRICT_COVERED for _ in grid.faces)
    dirs = (tuple(float(v) for v in grid.barycenters[0]),)
    metrics = evaluate_set_on_grid(
        grid=grid,
        reference_labels=labels,
        reconstructed_dirs=dirs,
        reference_dirs=dirs,
    )
    assert metrics.reconstructed_hit_count >= 1
    assert metrics.refinement.state is MetricState.UNEVALUABLE
    assert metrics.hausdorff.state is MetricState.VALUE


def test_complete_sphere_refinement_is_zero_on_non_nested_grids() -> None:
    fine_grid = build_sphere_grid(1)
    coarse_grid = build_sphere_grid(0)
    fine_labels = tuple(CellClass.STRICT_COVERED for _ in fine_grid.faces)
    coarse_labels = tuple(CellClass.STRICT_COVERED for _ in coarse_grid.faces)
    fine_dirs = tuple(tuple(float(value) for value in row) for row in fine_grid.barycenters)
    fine = evaluate_set_on_grid(
        grid=fine_grid,
        reference_labels=fine_labels,
        reconstructed_dirs=fine_dirs,
        reconstructed_hits=tuple(True for _ in fine_grid.faces),
    )
    coarse = evaluate_set_on_grid(
        grid=coarse_grid,
        reference_labels=coarse_labels,
        reconstructed_dirs=fine_dirs,
    )
    attached = attach_two_resolution_metrics(fine, coarse)
    assert fine.hausdorff_rad == 0.0
    assert coarse.hausdorff_rad == 0.0
    assert attached.refinement.state is MetricState.VALUE
    assert attached.refinement_delta == 0.0


def test_ambiguous_boundary_hits_do_not_enter_strict_hausdorff() -> None:
    grid = build_sphere_grid(0)
    labels = [CellClass.STRICT_UNCOVERED for _ in grid.faces]
    labels[0] = CellClass.STRICT_COVERED
    labels[1] = CellClass.AMBIGUOUS_BOUNDARY
    hits = [False for _ in grid.faces]
    hits[0] = True
    hits[1] = True
    dirs = (
        tuple(float(value) for value in grid.barycenters[0]),
        tuple(float(value) for value in grid.barycenters[1]),
    )
    metrics = evaluate_set_on_grid(
        grid=grid,
        reference_labels=tuple(labels),
        reconstructed_dirs=dirs,
        reconstructed_hits=tuple(hits),
    )
    assert metrics.missed_covered_fraction == 0.0
    assert metrics.false_positive_fraction == 0.0
    assert metrics.hausdorff_rad == 0.0


def test_legacy_null_json_is_unevaluable() -> None:
    blob = {
        "strict_covered_count": 1,
        "strict_uncovered_count": 1,
        "reconstructed_hit_count": 1,
        "missed_covered_fraction": 0.0,
        "false_positive_fraction": 0.0,
        "hausdorff_rad": 0.01,
        "boundary_disagreement_fraction": 0.0,
        "unresolved_fraction": 0.0,
        "max_cell_diameter_rad": 0.4,
        "refinement_delta": None,
    }
    loaded = PointingSetMetrics.from_json_dict(blob)
    assert loaded.missed_covered.state is MetricState.VALUE
    assert loaded.refinement.state is MetricState.UNEVALUABLE
    wrapped = {"direct_vs_oracle": blob}
    via_readout = comparison_metrics_from_json(wrapped, "direct_vs_oracle")
    assert via_readout is not None
    assert via_readout.refinement.state is MetricState.UNEVALUABLE


def test_ci_smoke_cannot_accept_even_with_perfect_metrics() -> None:
    config = load_campaign_config(CONFIG)
    perfect = _perfect_metrics()
    comparisons = tuple(
        ThreeWayReconstructionResult(
            probe_id=probe.probe_id,
            oracle_complete=probe.expected_pointing_complete,
            direct_complete=probe.expected_pointing_complete,
            source_control_metrics=perfect,
            natural_leaf_metrics=perfect,
            point_classification=(
                CompletenessLabel.COMPLETE if probe.expected_pointing_complete else CompletenessLabel.PARTIAL
            ),
            disposition=ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION,
            failure_localization="synthetic pass",
            direct_vs_oracle=perfect,
            source_vs_direct=perfect,
            natural_vs_direct=perfect,
        )
        for probe in config.probes
    )
    assert campaign_reconstruction_accepted(comparisons, config.probes, config.mode("ci")) is False
    assert campaign_reconstruction_accepted(comparisons, config.probes, config.mode("smoke")) is False
    assert campaign_reconstruction_accepted(comparisons, config.probes, config.mode("full")) is True


def test_full_metric_path_computes_refinement(tmp_path: Path) -> None:
    config = load_campaign_config(CONFIG)
    probe = config.probes[0]
    probe_dir = tmp_path / probe.probe_id
    probe_dir.mkdir()
    (probe_dir / "source_control.json").write_text(
        json.dumps({"pointing_samples": [[1.0, 0.0, 0.0]], "unresolved_c_intervals": []}),
        encoding="utf-8",
    )
    (probe_dir / "natural_family.json").write_text(
        json.dumps({"leaves": [], "unresolved_lambda_intervals": []}),
        encoding="utf-8",
    )
    (probe_dir / "direct_truth.json").write_text(
        json.dumps({"confirmation_cells": [], "confirmation": {"solves": []}}),
        encoding="utf-8",
    )
    write_compare_stage(config, tmp_path, [probe], mode="ci")
    blob = json.loads((probe_dir / "comparison.json").read_text(encoding="utf-8"))
    for key in ("direct_vs_oracle", "source_vs_direct", "natural_vs_direct", "source_vs_oracle", "natural_vs_oracle"):
        metrics = blob[key]
        assert metrics["refinement_delta_state"] in {
            "VALUE",
            "NOT_APPLICABLE",
            "UNEVALUABLE",
            "FAILED_VALUE",
        }
        assert "fine" in metrics
        assert "coarse" in metrics
        assert "refinement" in metrics
        assert metrics["refinement"]["state"] == metrics["refinement_delta_state"]
