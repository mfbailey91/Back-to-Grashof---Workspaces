"""Tests for fixed-position predictor-corrector continuation."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.continuation import (
    POSITION_RESIDUAL_TOL_M,
    continue_fixed_position_patch,
)


def test_intersecting_pairs_patch_has_regular_interior() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    patch = continue_fixed_position_patch(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=5, nt=5, include_pairs=True)
    regular = [s for s in patch.samples if s.regular]
    assert len(regular) >= 10
    assert all(s.p_residual_m <= POSITION_RESIDUAL_TOL_M for s in regular)
    assert all(s.rank_jd_nred == 2 for s in regular)
    assert all(s.dist_ua_m is not None and s.dist_ua_m <= 1e-12 for s in regular)
    assert all(s.dist_ub_m is not None and s.dist_ub_m <= 1e-12 for s in regular)


def test_urlike_patch_same_api() -> None:
    chain = URLikeAligned6R.aligned().chain
    patch = continue_fixed_position_patch(chain, URLIKE_REGULAR_Q, ns=5, nt=5)
    regular = [s for s in patch.samples if s.regular]
    assert len(regular) >= 8
    assert all(s.p_residual_m <= POSITION_RESIDUAL_TOL_M for s in regular)


def test_reverse_run_returns_near_start() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    patch = continue_fixed_position_patch(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=7, nt=3)
    assert patch.reverse_return_error < 1e-8
    assert patch.reverse_samples[-1].s == 0.0 or abs(patch.reverse_samples[-1].s) < 1e-15


def test_chart_freezes_q6() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q6 = INTERSECTING_PAIRS_REGULAR_Q[-1]
    patch = continue_fixed_position_patch(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=5, nt=5)
    assert all(abs(s.q[-1] - q6) < 1e-15 for s in patch.samples)
