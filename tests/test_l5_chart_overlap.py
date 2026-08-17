"""Chart-overlap source identity is preserved when Q sets match."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import chart_overlap_status


def test_matching_source_curves_are_duplicates() -> None:
    qs = ((0.3, -0.2, 0.1, 0.0, 0.0), (0.31, -0.2, 0.1, 0.0, 0.0))
    assert chart_overlap_status(qs, qs, tol=0.05) == "duplicate"


def test_empty_overlap_is_unresolved() -> None:
    assert chart_overlap_status((), ((0.0, 0.0, 0.0, 0.0, 0.0),), tol=0.05) == "UNRESOLVED"
