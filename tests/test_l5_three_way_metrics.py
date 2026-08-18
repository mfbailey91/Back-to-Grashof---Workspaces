"""Pointing-set metrics: null fractions when denominators are empty."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import (
    classify_point,
    pointing_set_metrics,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CellClass,
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
