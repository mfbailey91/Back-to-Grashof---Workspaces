"""Pointing-set metrics: null fractions when denominators are empty."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import (
    classify_point,
    direct_complete_from_cells,
    direct_reference_labels,
    pointing_set_metrics,
    resolved_direct_mask,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CellClass,
    DirectReferenceCell,
    OracleFeasibility,
    PointingSolveStatus,
    ReconstructionDisposition,
    load_campaign_config,
)


def test_empty_denominators_are_null() -> None:
    labels = (CellClass.AMBIGUOUS_BOUNDARY, CellClass.AMBIGUOUS_BOUNDARY)
    hits = (False, True)
    metrics = pointing_set_metrics(
        labels,
        hits,
        max_cell_diameter_rad=0.5,
        reconstructed_dirs=(),
        covered_dirs=(),
    )
    assert metrics.missed_covered_fraction is None
    assert metrics.false_positive_fraction is None
    assert metrics.hausdorff_rad is None
    payload = metrics.to_json_dict()
    assert payload["missed_covered_fraction"] is None
    assert payload["false_positive_fraction"] is None


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
    )
    assert metrics.missed_covered_fraction == 0.5
    assert metrics.false_positive_fraction == 0.5
    assert metrics.hausdorff_rad is not None
    assert metrics.hausdorff_rad <= 1e-9


def test_empty_negative_probe_reconstruction_does_not_pass() -> None:
    config = load_campaign_config("configs/l5_positive_control_v1.json")
    labels = (
        CellClass.STRICT_COVERED,
        CellClass.STRICT_UNCOVERED,
        CellClass.STRICT_UNCOVERED,
    )
    empty = pointing_set_metrics(
        labels,
        (False, False, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=(),
        covered_dirs=(),
    )
    assert empty.reconstructed_hit_count == 0
    _label, disposition, _reason = classify_point(False, empty, config)
    assert disposition is not ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION


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
