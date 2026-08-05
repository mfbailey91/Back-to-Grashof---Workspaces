"""Geometry and Stage A tests for Sprint 03 synthetic architectures."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.reduction_experiments import reduction_snapshot


def test_intersecting_pairs_home_geometry() -> None:
    model = IntersectingPairsAligned6R.aligned()
    dist, par = model.home_alignment_residuals()
    d_ua, d_ub = model.pair_intersection_distances()
    assert dist < 1e-15
    assert par < 1e-15
    assert d_ua == 0.0 or d_ua < 1e-15
    assert d_ub == 0.0 or d_ub < 1e-15


def test_intersecting_pairs_stage_a_regular() -> None:
    model = IntersectingPairsAligned6R.aligned()
    snap = reduction_snapshot(model.chain, INTERSECTING_PAIRS_REGULAR_Q)
    assert snap.regular is True


def test_urlike_home_geometry() -> None:
    model = URLikeAligned6R.aligned()
    dist, par = model.home_alignment_residuals()
    wrist = model.wrist_concurrency_distances()
    assert dist < 1e-15
    assert par < 1e-15
    assert model.elbow_parallelism_residual() < 1e-15
    assert all(d < 1e-15 for d in wrist)


def test_urlike_stage_a_regular() -> None:
    model = URLikeAligned6R.aligned()
    snap = reduction_snapshot(model.chain, URLIKE_REGULAR_Q)
    assert snap.regular is True


def test_urlike_is_not_exact_ur_claim() -> None:
    model = URLikeAligned6R.aligned()
    assert model.is_aligned is True
    assert "URLike" in type(model).__name__
