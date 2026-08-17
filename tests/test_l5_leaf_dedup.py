"""Identical leaves deduplicate; asymmetric directed distance catches subsets."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    directed_q_distance,
    symmetric_q_distance,
)


def test_identical_q_sets_have_zero_symmetric_distance() -> None:
    qs = ((0.1, 0.2, 0.0, 0.0, 0.0), (0.2, 0.1, 0.0, 0.0, 0.0))
    assert symmetric_q_distance(qs, qs) <= 1e-12


def test_subset_is_asymmetric() -> None:
    a = ((0.0, 0.0, 0.0, 0.0, 0.0),)
    b = ((0.0, 0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0, 0.0))
    assert directed_q_distance(a, b) < directed_q_distance(b, a)
