"""Tests for discriminating SUUR coordinate-map helpers."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.aligned_6r import REGULAR_Q, GenericAligned6R
from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    IntersectingPairsAligned6R,
)
from grashof_workspace.spatial_experiments.compound_joints import compare_reduced_tangents
from grashof_workspace.spatial_experiments.suur_coordinates import (
    PAIR_DISTANCE_TOL_M,
    closure_report,
    pair_intersection_distances,
    suur_map,
)


def test_intersecting_pairs_persistence_interior() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    for q in (INTERSECTING_PAIRS_REGULAR_Q, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (1.1, -0.7, 0.4, 0.9, -1.2, 0.3)):
        d_ua, d_ub = pair_intersection_distances(chain, q)
        assert d_ua <= PAIR_DISTANCE_TOL_M
        assert d_ub <= PAIR_DISTANCE_TOL_M


def test_generic_pairs_exterior_nonintersecting() -> None:
    chain = GenericAligned6R.aligned().chain
    d_ua, d_ub = pair_intersection_distances(chain, REGULAR_Q)
    assert d_ua > PAIR_DISTANCE_TOL_M
    assert d_ub > PAIR_DISTANCE_TOL_M


def test_phi_defined_on_intersecting_pairs() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    theta = INTERSECTING_PAIRS_REGULAR_Q[:5]
    result = suur_map(chain, theta, INTERSECTING_PAIRS_REGULAR_Q[5])
    assert result.defined is True
    assert result.q == INTERSECTING_PAIRS_REGULAR_Q


def test_phi_undefined_on_generic_exterior() -> None:
    chain = GenericAligned6R.aligned().chain
    result = suur_map(chain, REGULAR_Q[:5], REGULAR_Q[5])
    assert result.defined is False
    assert result.q is None


def test_phi_boundary_tolerance_accepts_exact_zero() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    result = suur_map(chain, INTERSECTING_PAIRS_REGULAR_Q[:5], INTERSECTING_PAIRS_REGULAR_Q[5], tol_m=0.0)
    assert result.defined is True


def test_closure_report_intersecting_pairs() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    report = closure_report(chain, INTERSECTING_PAIRS_REGULAR_Q[:5], INTERSECTING_PAIRS_REGULAR_Q[5])
    assert report.defined is True
    assert report.closed is True
    assert report.position_residual_m == 0.0 or report.position_residual_m < 1e-15


def test_old_tangent_test_still_passes_on_generic() -> None:
    chain = GenericAligned6R.aligned().chain
    report = compare_reduced_tangents(chain, REGULAR_Q)
    assert report.within_tolerance
    assert report.max_angle_rad <= 1e-8
    assert not suur_map(chain, REGULAR_Q[:5], REGULAR_Q[5]).defined
