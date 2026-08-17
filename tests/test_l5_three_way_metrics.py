"""Pointing-set metrics: null fractions when denominators are empty."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import pointing_set_metrics
from grashof_workspace.spatial_experiments.l5_reconstruction.models import CellClass


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
