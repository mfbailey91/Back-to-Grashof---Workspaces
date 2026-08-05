"""Interior, exterior, and boundary tests for the pointing-scalar fiber constraint."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.fiber_constraints import (
    ALTERNATE_N,
    PRIMARY_N,
    fiber_independence_report,
    pointing_scalar,
    pointing_scalar_gradient,
    reduced_fiber_jacobian,
    reduced_fiber_tangent,
)


def test_primary_n_is_independent_at_regular_ip_seed() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    report = fiber_independence_report(chain, q0, PRIMARY_N)
    assert abs(report.c - pointing_scalar(chain, q0, PRIMARY_N)) < 1e-15
    assert report.rank == 4
    assert report.nullity == 1
    assert report.independent
    assert report.dh_dq6_vanishes


def test_alternate_n_is_independent_at_regular_seeds() -> None:
    for chain, q0 in (
        (IntersectingPairsAligned6R.aligned().chain, INTERSECTING_PAIRS_REGULAR_Q),
        (URLikeAligned6R.aligned().chain, URLIKE_REGULAR_Q),
    ):
        report = fiber_independence_report(chain, q0, ALTERNATE_N)
        assert report.independent
        assert report.dh_dq6_vanishes


def test_parallel_n_is_exterior_and_drops_rank() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    d0 = tuple(float(x) for x in chain.evaluate(q0).d)
    report = fiber_independence_report(chain, q0, d0)
    grad = np.asarray(report.grad_h, dtype=float)
    assert float(np.linalg.norm(grad)) < 1e-12
    assert report.rank < 4
    assert not report.independent


def test_dh_dq6_is_zero_at_aligned_seed() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    grad = pointing_scalar_gradient(chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    assert abs(float(grad[-1])) <= 1e-12


def test_analytical_gradient_matches_central_difference() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = np.asarray(INTERSECTING_PAIRS_REGULAR_Q, dtype=float)
    analytical = pointing_scalar_gradient(chain, tuple(float(x) for x in q0), PRIMARY_N)
    fd = np.zeros(6)
    step = 1e-6
    for i in range(6):
        qp = q0.copy()
        qm = q0.copy()
        qp[i] += step
        qm[i] -= step
        fd[i] = (
            pointing_scalar(chain, tuple(float(x) for x in qp), PRIMARY_N)
            - pointing_scalar(chain, tuple(float(x) for x in qm), PRIMARY_N)
        ) / (2.0 * step)
    assert float(np.max(np.abs(analytical - fd))) < 1e-8


def test_reduced_fiber_jacobian_is_four_by_five() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    jac = reduced_fiber_jacobian(chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    assert jac.shape == (4, 5)


def test_fiber_tangent_has_frozen_roll_and_sign_lock() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    t0 = reduced_fiber_tangent(chain, q0, PRIMARY_N)
    assert abs(float(t0[-1])) < 1e-15
    assert abs(float(np.linalg.norm(t0)) - 1.0) < 1e-12
    flipped = reduced_fiber_tangent(chain, q0, PRIMARY_N, previous=-t0)
    assert float(np.dot(flipped, -t0)) > 0.0
    assert float(np.linalg.norm(flipped - (-t0))) < 1e-12 or float(np.dot(flipped, t0)) > 0.9
