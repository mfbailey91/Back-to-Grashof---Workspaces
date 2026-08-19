"""Pointing-set metrics: denominator-aware states; reconstruction_pass."""

from __future__ import annotations

from dataclasses import replace

from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import (
    classify_point,
    classify_probe_reconstruction,
    direct_complete_from_cells,
    direct_reference_labels,
    evaluate_reconstruction_gates,
    pointing_set_metrics,
    reconstruction_pass,
    resolved_direct_mask,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CellClass,
    CompletenessLabel,
    DirectReferenceCell,
    MetricState,
    OracleFeasibility,
    PointingSetMetrics,
    PointingSolveStatus,
    ReconstructionDisposition,
    ScalarMetric,
    load_campaign_config,
)

CONFIG = "configs/l5_positive_control_v1.json"


def _perfect_metrics() -> PointingSetMetrics:
    return pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (True, True, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        covered_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        refinement_delta=0.0,
    )


def _empty_metrics() -> PointingSetMetrics:
    return pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED, CellClass.STRICT_UNCOVERED),
        (False, False, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=(),
        covered_dirs=(),
    )


def test_empty_denominators_are_not_applicable() -> None:
    labels = (CellClass.AMBIGUOUS_BOUNDARY, CellClass.AMBIGUOUS_BOUNDARY)
    hits = (False, True)
    metrics = pointing_set_metrics(
        labels,
        hits,
        max_cell_diameter_rad=0.5,
        reconstructed_dirs=(),
        covered_dirs=(),
    )
    assert metrics.missed_covered.state is MetricState.NOT_APPLICABLE
    assert metrics.false_positive.state is MetricState.NOT_APPLICABLE
    assert metrics.hausdorff.state is MetricState.NOT_APPLICABLE
    assert metrics.missed_covered_fraction is None
    assert metrics.false_positive_fraction is None
    assert metrics.hausdorff_rad is None
    payload = metrics.to_json_dict()
    assert payload["missed_covered_fraction"] is None
    assert payload["missed_covered_fraction_state"] == "NOT_APPLICABLE"
    assert payload["false_positive_fraction"] is None
    config = load_campaign_config(CONFIG)
    assert reconstruction_pass(metrics, config) is False
    assert reconstruction_pass(None, config) is False


def test_false_positive_and_miss_fractions() -> None:
    labels = (
        CellClass.STRICT_COVERED,
        CellClass.STRICT_COVERED,
        CellClass.STRICT_UNCOVERED,
        CellClass.STRICT_UNCOVERED,
    )
    hits = (True, False, True, False)
    metrics = pointing_set_metrics(
        labels,
        hits,
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0),),
        covered_dirs=((1.0, 0.0, 0.0),),
        refinement_delta=0.0,
    )
    assert metrics.missed_covered_fraction == 0.5
    assert metrics.false_positive_fraction == 0.5
    assert metrics.hausdorff_rad is not None
    assert metrics.hausdorff_rad <= 1e-9
    config = load_campaign_config(CONFIG)
    assert reconstruction_pass(metrics, config) is False


def test_empty_reconstruction_fails_all_five_gates() -> None:
    config = load_campaign_config(CONFIG)
    empty = _empty_metrics()
    assert reconstruction_pass(empty, config) is False
    gates = evaluate_reconstruction_gates(
        direct_vs_oracle=empty,
        source_vs_direct=empty,
        natural_vs_direct=empty,
        source_vs_oracle=empty,
        natural_vs_oracle=empty,
        config=config,
    )
    assert gates == (False, False, False, False, False)
    _label, disposition, _reason = classify_point(False, empty, config)
    assert disposition is not ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION


def test_empty_negative_probe_reconstruction_does_not_pass() -> None:
    config = load_campaign_config(CONFIG)
    empty = _empty_metrics()
    assert empty.reconstructed_hit_count == 0
    _label, disposition, _reason = classify_point(False, empty, config)
    assert disposition is not ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION


def test_synthetic_perfect_reconstruction_passes_all_five_gates() -> None:
    config = load_campaign_config(CONFIG)
    perfect = _perfect_metrics()
    assert reconstruction_pass(perfect, config) is True
    gates = evaluate_reconstruction_gates(
        direct_vs_oracle=perfect,
        source_vs_direct=perfect,
        natural_vs_direct=perfect,
        source_vs_oracle=perfect,
        natural_vs_oracle=perfect,
        config=config,
    )
    assert gates == (True, True, True, True, True)
    label, disposition, _reason = classify_point(True, perfect, config)
    assert label is CompletenessLabel.COMPLETE
    assert disposition is ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION


def test_none_metric_fields_do_not_pass() -> None:
    config = load_campaign_config(CONFIG)
    perfect = _perfect_metrics()
    missing_haus = replace(perfect, hausdorff=ScalarMetric.unevaluable("missing hausdorff"))
    assert reconstruction_pass(missing_haus, config) is False
    missing_refine = replace(perfect, refinement=ScalarMetric.unevaluable("missing refinement"))
    assert reconstruction_pass(missing_refine, config) is False
    assert missing_refine.refinement_delta is None
    assert missing_refine.refinement.state is MetricState.UNEVALUABLE


def test_boundary_only_does_not_fabricate_strict_pass() -> None:
    config = load_campaign_config(CONFIG)
    metrics = pointing_set_metrics(
        (CellClass.AMBIGUOUS_BOUNDARY, CellClass.AMBIGUOUS_BOUNDARY),
        (True, True),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0),),
        covered_dirs=(),
        refinement_delta=0.0,
    )
    assert metrics.missed_covered_fraction is None
    assert metrics.false_positive.state is MetricState.NOT_APPLICABLE
    assert metrics.hausdorff.state is MetricState.FAILED_VALUE
    assert reconstruction_pass(metrics, config) is False
    _label, disposition, _reason = classify_point(True, metrics, config)
    assert disposition is not ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION


def test_negative_probe_pass_is_partial_not_complete() -> None:
    config = load_campaign_config(CONFIG)
    perfect = _perfect_metrics()
    label, disposition, _reason = classify_point(False, perfect, config)
    assert label is CompletenessLabel.PARTIAL
    assert disposition is ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION


def test_source_failure_is_localized_before_natural() -> None:
    config = load_campaign_config(CONFIG)
    perfect = _perfect_metrics()
    empty = _empty_metrics()
    label, disposition, reason = classify_probe_reconstruction(
        oracle_complete=True,
        expected_complete=True,
        direct_complete=True,
        direct_vs_oracle=perfect,
        source_vs_direct=empty,
        natural_vs_direct=perfect,
        source_vs_oracle=empty,
        natural_vs_oracle=perfect,
        unresolved_family_intervals=(),
        unresolved_c_intervals=(),
        config=config,
    )
    assert disposition is not ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION
    assert "source" in reason.lower()
    assert "decomposition" not in reason.lower() or "not attributed" in reason.lower()
    assert label is CompletenessLabel.PARTIAL


def test_unresolved_family_interval_blocks_pass() -> None:
    config = load_campaign_config(CONFIG)
    perfect = _perfect_metrics()
    _label, disposition, reason = classify_probe_reconstruction(
        oracle_complete=True,
        expected_complete=True,
        direct_complete=True,
        direct_vs_oracle=perfect,
        source_vs_direct=perfect,
        natural_vs_direct=perfect,
        source_vs_oracle=perfect,
        natural_vs_oracle=perfect,
        unresolved_family_intervals=((0.0, 0.5),),
        unresolved_c_intervals=(),
        config=config,
    )
    assert disposition is not ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION
    assert "interval" in reason.lower() or "lambda" in reason.lower() or "family" in reason.lower()


def _cell(
    cell_id: str,
    oracle: OracleFeasibility,
    direct: PointingSolveStatus,
    *,
    direction: tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> DirectReferenceCell:
    eligible = oracle is not OracleFeasibility.BOUNDARY and direct is not PointingSolveStatus.UNRESOLVED
    return DirectReferenceCell(
        cell_id=cell_id,
        vertex_or_barycenter_direction=direction,
        oracle_status=oracle,
        direct_status=direct,
        direct_cluster_count=1 if direct is PointingSolveStatus.FOUND else 0,
        best_position_residual_m=1e-9 if direct is PointingSolveStatus.FOUND else None,
        best_pointing_error_rad=1e-9 if direct is PointingSolveStatus.FOUND else None,
        strict_reference_eligible=eligible,
    )


def test_boundary_cells_excluded_from_strict_denominators() -> None:
    cells = (
        _cell("c0", OracleFeasibility.FEASIBLE, PointingSolveStatus.FOUND),
        _cell("c1", OracleFeasibility.BOUNDARY, PointingSolveStatus.FOUND, direction=(0.0, 1.0, 0.0)),
        _cell("c2", OracleFeasibility.INFEASIBLE, PointingSolveStatus.NOT_FOUND_AT_DECLARED_BUDGET),
    )
    labels = (
        CellClass.STRICT_COVERED,
        CellClass.AMBIGUOUS_BOUNDARY,
        CellClass.STRICT_UNCOVERED,
    )
    hits = resolved_direct_mask(cells)
    metrics = pointing_set_metrics(
        labels,
        hits,
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=(),
        covered_dirs=(),
    )
    assert metrics.strict_covered_count == 1
    assert metrics.strict_uncovered_count == 1
    assert metrics.missed_covered_fraction == 0.0
    assert metrics.false_positive_fraction == 0.0


def test_unresolved_strict_cell_blocks_direct_complete() -> None:
    cells = (
        _cell("c0", OracleFeasibility.FEASIBLE, PointingSolveStatus.FOUND),
        _cell("c1", OracleFeasibility.FEASIBLE, PointingSolveStatus.UNRESOLVED),
        _cell("c2", OracleFeasibility.INFEASIBLE, PointingSolveStatus.NOT_FOUND_AT_DECLARED_BUDGET),
    )
    assert direct_complete_from_cells(cells) is None


def test_direct_source_natural_masks_remain_independent() -> None:
    cells = (
        _cell("c0", OracleFeasibility.FEASIBLE, PointingSolveStatus.FOUND),
        _cell("c1", OracleFeasibility.FEASIBLE, PointingSolveStatus.NOT_FOUND_AT_DECLARED_BUDGET),
        _cell("c2", OracleFeasibility.INFEASIBLE, PointingSolveStatus.FOUND),
        _cell("c3", OracleFeasibility.BOUNDARY, PointingSolveStatus.UNRESOLVED),
    )
    oracle_labels = (
        CellClass.STRICT_COVERED,
        CellClass.STRICT_COVERED,
        CellClass.STRICT_UNCOVERED,
        CellClass.AMBIGUOUS_BOUNDARY,
    )
    direct_hits = resolved_direct_mask(cells)
    source_hits = (True, True, False, False)
    natural_hits = (False, False, False, False)
    assert direct_hits == (True, False, True, False)
    assert direct_hits != source_hits
    assert direct_hits != natural_hits
    direct_labels = direct_reference_labels(cells)
    assert direct_labels[0] is CellClass.STRICT_COVERED
    assert direct_labels[1] is CellClass.STRICT_UNCOVERED
    assert direct_labels[2] is CellClass.STRICT_COVERED
    assert direct_labels[3] is CellClass.AMBIGUOUS_BOUNDARY
    vs_oracle = pointing_set_metrics(
        oracle_labels,
        direct_hits,
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=(),
        covered_dirs=(),
    )
    vs_direct = pointing_set_metrics(
        direct_labels,
        source_hits,
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=(),
        covered_dirs=(),
    )
    assert vs_oracle.missed_covered_fraction == 0.5
    assert vs_oracle.false_positive_fraction == 1.0
    assert vs_direct.missed_covered_fraction == 0.5
    assert vs_direct.false_positive_fraction == 1.0
    assert direct_complete_from_cells(cells) is False


def test_complete_reference_no_uncovered_cells_can_pass_fp_gate() -> None:
    config = load_campaign_config(CONFIG)
    dirs = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    metrics = pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED),
        (True, True),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=dirs,
        covered_dirs=dirs,
        refinement_delta=0.0,
    )
    assert metrics.strict_uncovered_count == 0
    assert metrics.false_positive.state is MetricState.NOT_APPLICABLE
    assert metrics.false_positive_fraction is None
    assert metrics.missed_covered.state is MetricState.VALUE
    assert metrics.missed_covered_fraction == 0.0
    assert reconstruction_pass(metrics, config) is True


def test_partial_reference_still_requires_recall_and_precision() -> None:
    config = load_campaign_config(CONFIG)
    metrics = pointing_set_metrics(
        (
            CellClass.STRICT_COVERED,
            CellClass.STRICT_COVERED,
            CellClass.STRICT_UNCOVERED,
            CellClass.STRICT_UNCOVERED,
        ),
        (True, False, False, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0),),
        covered_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        refinement_delta=0.0,
    )
    assert metrics.missed_covered.state is MetricState.VALUE
    assert metrics.false_positive.state is MetricState.VALUE
    assert metrics.missed_covered_fraction == 0.5
    assert reconstruction_pass(metrics, config) is False


def test_empty_reconstruction_has_failed_hausdorff_not_missing_hausdorff() -> None:
    config = load_campaign_config(CONFIG)
    metrics = pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (False, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=(),
        covered_dirs=((1.0, 0.0, 0.0),),
        refinement_delta=0.0,
    )
    assert metrics.hausdorff.state is MetricState.FAILED_VALUE
    assert metrics.hausdorff_rad is None
    payload = metrics.to_json_dict()
    assert payload["hausdorff_rad"] is None
    assert payload["hausdorff_rad_state"] == "FAILED_VALUE"
    assert reconstruction_pass(metrics, config) is False
