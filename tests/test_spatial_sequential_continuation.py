"""Tests for sequential predictor-corrector continuation."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.continuation import (
    continue_sequential_chart,
    continue_sequential_ray,
    procrustes_align_frame,
    seed_tangent_frame,
    sequential_predictor_step,
    wrap_joint_delta,
)
from grashof_workspace.spatial_experiments.jacobians import position_jacobian, reduced_pointing_basis


def test_sequential_predictor_starts_from_previous_corrected_q() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    frame = seed_tangent_frame(chain, q0)
    p0 = chain.evaluate(q0).p
    step, next_frame, _rejected = sequential_predictor_step(
        chain, q0, frame, 0.03, 0.0, p0, q0[-1], path_id="+s", step_index=1, s0=0.0, t0=0.0
    )
    assert step is not None and step.accepted and step.q_pred is not None
    predicted = np.asarray(q0, dtype=float) + frame.as_matrix() @ np.array([0.005, 0.0])
    predicted[-1] = q0[-1]
    assert np.allclose(step.q_pred, predicted, atol=1e-12)
    step2, _frame2, _ = sequential_predictor_step(
        chain, step.q, next_frame, 0.03, 0.0, p0, q0[-1], path_id="+s", step_index=2, s0=step.s, t0=step.t
    )
    assert step2 is not None and step2.q_pred is not None and step.q is not None
    predicted2 = np.asarray(step.q, dtype=float) + next_frame.as_matrix() @ np.array([0.005, 0.0])
    predicted2[-1] = q0[-1]
    assert np.allclose(step2.q_pred, predicted2, atol=1e-12)
    assert not np.allclose(step2.q_pred, predicted)


def test_procrustes_undoes_sign_flip_and_column_swap() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    nred = reduced_pointing_basis(position_jacobian(chain, INTERSECTING_PAIRS_REGULAR_Q))
    scrambled = np.column_stack([-nred[:, 1], nred[:, 0]])
    aligned, angles = procrustes_align_frame(scrambled, nred)
    assert float(np.max(np.abs(aligned - nred))) < 1e-12 or float(np.max(np.abs(aligned + nred))) < 1e-12
    overlap = float(np.linalg.norm(aligned.T @ nred - np.eye(2)))
    assert overlap < 1e-10
    assert float(np.max(angles)) < 1e-12


def test_terminal_roll_remains_frozen() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q6 = INTERSECTING_PAIRS_REGULAR_Q[-1]
    chart = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=5, nt=5)
    assert all(abs(sample.q[-1] - q6) < 1e-15 for sample in chart.samples)


def test_step_halving_and_failed_steps_are_reported() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    frame = seed_tangent_frame(chain, q0)
    p0 = chain.evaluate(q0).p
    accepted, _frame, rejected = sequential_predictor_step(
        chain,
        q0,
        frame,
        2.5,
        0.0,
        p0,
        q0[-1],
        path_id="+s",
        step_index=1,
        s0=0.0,
        t0=0.0,
        max_reductions=3,
        max_correction_norm=1e-9,
    )
    assert accepted is None
    assert len(rejected) == 4
    assert [step.step_reductions for step in rejected] == [0, 1, 2, 3]
    assert all(not step.accepted for step in rejected)


def test_urlike_uses_same_continuation_api() -> None:
    chain = URLikeAligned6R.aligned().chain
    chart = continue_sequential_chart(chain, URLIKE_REGULAR_Q, ns=5, nt=5)
    assert len(chart.samples) >= 15
    assert all(sample.regular for sample in chart.samples)
    path, _, _ = continue_sequential_ray(
        chain, URLIKE_REGULAR_Q, axis="s", direction=1.0, n_steps=3, step_size=0.03
    )
    assert len(path.accepted) == 4
