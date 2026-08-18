"""Duplicate semantics live in source-Q space, not pointing-set overlap."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    classify_source_components,
    dedup_source_q_leaves,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import LeafPairStatus
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    directed_q_distance,
    symmetric_q_distance,
)


def test_identical_q_sets_have_zero_symmetric_distance() -> None:
    qs = ((0.1, 0.2, 0.0, 0.0, 0.0), (0.2, 0.1, 0.0, 0.0, 0.0))
    assert symmetric_q_distance(qs, qs) <= 1e-12


def test_identical_leaves_are_duplicate_same_component() -> None:
    qs = ((0.1, 0.2, 0.0, 0.0, 0.0), (0.2, 0.1, 0.0, 0.0, 0.0))
    t = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    status = classify_source_components(qs, qs, t, t, q_tol=0.02, tangent_tol=0.05)
    assert status is LeafPairStatus.DUPLICATE_SAME_COMPONENT


def test_disjoint_q_same_pointing_are_not_duplicates() -> None:
    q_a = ((0.0, 0.0, 0.0, 0.0, 0.0),)
    q_b = ((1.2, 0.4, -0.3, 0.1, 0.0),)
    t = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    status = classify_source_components(q_a, q_b, t, t, q_tol=0.02, tangent_tol=0.05)
    assert status is LeafPairStatus.DISTINCT_COMPATIBLE
    assert status is not LeafPairStatus.DUPLICATE_SAME_COMPONENT


def test_nearby_q_disagreeing_tangents_are_crossing() -> None:
    q_a = ((0.10, 0.20, 0.0, 0.0, 0.0),)
    q_b = ((0.11, 0.20, 0.0, 0.0, 0.0),)
    t_a = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    t_b = np.array([0.0, 1.0, 0.0, 0.0, 0.0], dtype=float)
    status = classify_source_components(q_a, q_b, t_a, t_b, q_tol=0.05, tangent_tol=0.05)
    assert status is LeafPairStatus.CROSSING_DIFFERENT_TANGENT


def test_dedup_removes_only_source_q_duplicates() -> None:
    qs_a = ((0.0, 0.0, 0.0, 0.0, 0.0), (0.05, 0.0, 0.0, 0.0, 0.0))
    qs_b = qs_a
    qs_c = ((1.4, 0.2, 0.0, 0.0, 0.0), (1.5, 0.2, 0.0, 0.0, 0.0))
    t = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    kept, dropped, labels = dedup_source_q_leaves(
        (
            ("chart0", "a", qs_a, t),
            ("chart0", "b", qs_b, t),
            ("chart0", "c", qs_c, t),
        ),
        q_tol=0.02,
        tangent_tol=0.05,
    )
    assert dropped == 1
    assert [item[1] for item in kept] == ["a", "c"]
    assert LeafPairStatus.DUPLICATE_SAME_COMPONENT in labels
    assert LeafPairStatus.DISTINCT_COMPATIBLE in labels


def test_subset_directed_distance_is_not_a_duplicate_rule() -> None:
    a = ((0.0, 0.0, 0.0, 0.0, 0.0),)
    b = ((0.0, 0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0, 0.0))
    assert directed_q_distance(a, b) < directed_q_distance(b, a)
    t = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    # Asymmetry is a sampling diagnostic, not identity.
    status = classify_source_components(a, b, t, t, q_tol=0.02, tangent_tol=0.05)
    assert status is not LeafPairStatus.DUPLICATE_SAME_COMPONENT
