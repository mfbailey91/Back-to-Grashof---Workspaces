"""Tests for one-dimensional fiber duplicate scans."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.fiber_constraints import ALTERNATE_N, PRIMARY_N
from grashof_workspace.spatial_experiments.fiber_continuation import FiberStep, continue_fiber
from grashof_workspace.spatial_experiments.fiber_duplicates import (
    DUPLICATE_TOL_RAD,
    fiber_duplicate_report,
)


def _step(sigma: float, q: tuple[float, ...]) -> FiberStep:
    return FiberStep(
        sigma=sigma,
        path_id="test",
        step_index=0,
        q_pred=q,
        q=q,
        d=(0.0, 0.0, 1.0),
        p_residual_m=0.0,
        h_residual=0.0,
        corrector_iterations=0,
        correction_norm=0.0,
        step_reductions=0,
        rank_jf=4,
        nullity_jf=1,
        tangent_dot=1.0,
        regular=True,
        label="regular",
        accepted=True,
    )


def test_interior_fiber_stations_are_distinct() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    segment = continue_fiber(chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    report = fiber_duplicate_report(segment)
    assert report.passed
    assert report.n_duplicates == 0
    assert report.min_nn_distance > DUPLICATE_TOL_RAD


def test_urlike_and_alternate_fibers_are_distinct() -> None:
    ip = IntersectingPairsAligned6R.aligned().chain
    ur = URLikeAligned6R.aligned().chain
    for chain, q0, n in (
        (ip, INTERSECTING_PAIRS_REGULAR_Q, ALTERNATE_N),
        (ur, URLIKE_REGULAR_Q, PRIMARY_N),
        (ur, URLIKE_REGULAR_Q, ALTERNATE_N),
    ):
        report = fiber_duplicate_report(continue_fiber(chain, q0, n))
        assert report.passed


def test_exterior_wrap_equivalent_pair_fails() -> None:
    q = INTERSECTING_PAIRS_REGULAR_Q
    wrapped = (*q[:5], q[5] + 2.0 * 3.141592653589793)
    report = fiber_duplicate_report((_step(0.0, q), _step(0.12, wrapped)))
    assert not report.passed
    assert report.n_duplicates == 1
    assert report.duplicate_pairs[0][2] < 1e-12


def test_boundary_duplicate_tolerance_counts_as_duplicate() -> None:
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    q1 = (q0[0] + DUPLICATE_TOL_RAD * 0.5, *q0[1:])
    report = fiber_duplicate_report((_step(-0.03, q0), _step(0.03, q1)))
    assert not report.passed
    assert report.n_duplicates == 1
    assert report.duplicate_pairs[0][2] <= DUPLICATE_TOL_RAD
