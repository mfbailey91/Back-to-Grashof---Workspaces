"""Tests for 1D sequential fiber continuation."""

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
    JOINT_FREEZE_INDEX,
    PRIMARY_N,
    reduced_fiber_tangent,
)
from grashof_workspace.spatial_experiments.fiber_continuation import (
    continue_fiber,
    continue_fiber_ray,
    continue_joint_freeze_ray,
    sequential_fiber_step,
)
from grashof_workspace.spatial_experiments.fiber_diagnostics import (
    fiber_forward_reverse,
    fiber_paths_distinct,
    pointing_image_report,
)
from grashof_workspace.spatial_experiments.jacobians import (
    position_jacobian,
    reduced_pointing_basis,
)


def test_predictor_uses_last_accepted_q_and_one_d_tangent() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    tangent = reduced_fiber_tangent(chain, q0, PRIMARY_N)
    p0 = chain.evaluate(q0).p
    c = float(np.asarray(PRIMARY_N) @ chain.evaluate(q0).d)
    step, next_t, _rejected = sequential_fiber_step(
        chain,
        q0,
        tangent,
        0.03,
        p0,
        PRIMARY_N,
        c,
        q0[-1],
        path_id="+sigma",
        step_index=1,
        sigma0=0.0,
    )
    assert step is not None and step.accepted and step.q_pred is not None
    predicted = np.asarray(q0, dtype=float) + tangent * 0.03
    predicted[-1] = q0[-1]
    assert np.allclose(step.q_pred, predicted, atol=1e-12)
    nred = reduced_pointing_basis(position_jacobian(chain, q0))
    # Full-step prediction must not be a raw 2D chart step along N_red.
    chart_pred = np.asarray(q0, dtype=float) + nred @ np.array([0.03, 0.0])
    chart_pred[-1] = q0[-1]
    assert not np.allclose(step.q_pred, chart_pred, atol=1e-8)
    step2, _, _ = sequential_fiber_step(
        chain,
        step.q,
        next_t,
        0.03,
        p0,
        PRIMARY_N,
        c,
        q0[-1],
        path_id="+sigma",
        step_index=2,
        sigma0=step.sigma,
    )
    assert step2 is not None and step2.q_pred is not None and step.q is not None
    predicted2 = np.asarray(step.q, dtype=float) + next_t * 0.03
    predicted2[-1] = q0[-1]
    assert np.allclose(step2.q_pred, predicted2, atol=1e-12)
    assert not np.allclose(step2.q_pred, predicted)


def test_terminal_roll_remains_frozen_on_fiber() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    segment = continue_fiber(chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N, n_steps=4)
    q6 = INTERSECTING_PAIRS_REGULAR_Q[-1]
    for step in segment.accepted_samples:
        assert step.q is not None
        assert abs(step.q[-1] - q6) < 1e-15


def test_ip_fiber_reverse_from_endpoint() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    report = fiber_forward_reverse(
        chain,
        INTERSECTING_PAIRS_REGULAR_Q,
        PRIMARY_N,
        n_steps=4,
        step_size=0.03,
        architecture="IntersectingPairsAligned6R",
    )
    assert report.started_from_endpoint
    assert report.forward_accepted == 4
    assert report.reverse_accepted == 4
    assert report.passed


def test_pointing_image_is_noncollapsed_curve() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    segment = continue_fiber(chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N, n_steps=4)
    image = pointing_image_report(segment.accepted_samples)
    assert image.passed
    assert not image.collapsed
    assert image.local_pointing_tangent_nonzero


def test_urlike_fiber_path_does_not_invoke_suur(monkeypatch) -> None:
    calls: list[object] = []

    def boom(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("suur_map / pair distances must not be called on the UR-like fiber path")

    monkeypatch.setattr(
        "grashof_workspace.spatial_experiments.suur_coordinates.suur_map",
        boom,
    )
    monkeypatch.setattr(
        "grashof_workspace.spatial_experiments.suur_coordinates.pair_intersection_distances",
        boom,
    )
    chain = URLikeAligned6R.aligned().chain
    segment = continue_fiber(chain, URLIKE_REGULAR_Q, PRIMARY_N, n_steps=4)
    report = fiber_forward_reverse(
        chain, URLIKE_REGULAR_Q, PRIMARY_N, n_steps=4, step_size=0.03, architecture="URLikeAligned6R"
    )
    image = pointing_image_report(segment.accepted_samples)
    assert segment.plus.accepted[-1].accepted
    assert report.passed
    assert image.passed
    assert calls == []
    _ = URLIKE_REGULAR_Q


def test_alternate_n_fiber_and_joint_freeze_are_distinct() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    alt = continue_fiber_ray(chain, q0, ALTERNATE_N, direction=1.0, n_steps=4, step_size=0.03)[0]
    primary = continue_fiber_ray(chain, q0, PRIMARY_N, direction=1.0, n_steps=4, step_size=0.03)[0]
    freeze = continue_joint_freeze_ray(
        chain, q0, freeze_index=JOINT_FREEZE_INDEX, direction=1.0, n_steps=4, step_size=0.03
    )
    alt_rev = fiber_forward_reverse(chain, q0, ALTERNATE_N, n_steps=4, step_size=0.03)
    assert alt_rev.passed
    assert pointing_image_report(alt.accepted).passed
    distinct_alt = fiber_paths_distinct(primary, alt)
    distinct_freeze = fiber_paths_distinct(primary, freeze)
    assert distinct_alt["distinct"]
    assert distinct_freeze["distinct"]
