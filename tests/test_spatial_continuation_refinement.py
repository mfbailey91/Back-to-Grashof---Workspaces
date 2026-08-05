"""Refinement, loop, and alternate-path continuation tests."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.chart_diagnostics import (
    alternate_path_to_target,
    chart_differentials,
    compare_shared_nodes,
    rectangular_loop,
)
from grashof_workspace.spatial_experiments.continuation import continue_sequential_chart


def test_shared_nodes_agree_under_common_microstep() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    coarse = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=5, nt=5, ds=0.03, dt=0.03)
    fine = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=9, nt=9, ds=0.015, dt=0.015)
    comparison = compare_shared_nodes(coarse, fine)
    assert comparison.n_shared >= 9
    assert comparison.passed


def test_rectangular_loop_error_decreases_when_step_halved() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    coarse = rectangular_loop(chain, INTERSECTING_PAIRS_REGULAR_Q, n_steps=2, step_size=0.03)
    fine = rectangular_loop(chain, INTERSECTING_PAIRS_REGULAR_Q, n_steps=2, step_size=0.015)
    assert coarse.accepted_legs == 4
    assert fine.accepted_legs == 4
    assert fine.epsilon_q < coarse.epsilon_q


def test_alternate_path_discrepancy_stable_or_decreased() -> None:
    chain = URLikeAligned6R.aligned().chain
    coarse = alternate_path_to_target(chain, URLIKE_REGULAR_Q, s_target=0.06, t_target=0.06, step_size=0.06)
    fine = alternate_path_to_target(chain, URLIKE_REGULAR_Q, s_target=0.06, t_target=0.06, step_size=0.03)
    rel = abs(fine.epsilon_q - coarse.epsilon_q) / max(coarse.epsilon_q, 1e-30)
    assert fine.epsilon_q <= 5e-3
    assert fine.epsilon_q < coarse.epsilon_q or rel <= 0.05


def test_compact_and_fine_charts_remain_rank_two() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    compact = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=5, nt=5, ds=0.015, dt=0.015)
    fine = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=9, nt=9, ds=0.015, dt=0.015)
    assert chart_differentials(compact, ds=0.015, dt=0.015).all_rank_two
    assert chart_differentials(fine, ds=0.015, dt=0.015).all_rank_two
