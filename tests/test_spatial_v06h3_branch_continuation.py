"""V06H3: shared 1D pseudo-arclength continuation is infrastructure only."""

from __future__ import annotations

import inspect
import json

import numpy as np

from grashof_workspace.spatial_experiments.branch_continuation import (
    ParabolaProblem,
    UnitCircleProblem,
    branch_tangent,
    continue_implicit_branch,
    correct_pseudo_arclength,
    detect_branch_return,
)
from grashof_workspace.spatial_experiments.parent_level_sets import continue_level_set
from grashof_workspace.spatial_experiments.virtual_u_child import continue_uuur


def test_circle_returns_with_conjunctive_loop_test() -> None:
    problem = UnitCircleProblem()
    x0 = np.array([1.0, 0.0])
    t0 = branch_tangent(problem, x0)
    pred = x0 + 0.1 * t0
    corr = correct_pseudo_arclength(problem, pred, t0)
    assert corr.accepted is True
    assert corr.x is not None
    assert corr.gauge_residual <= 1e-10
    trace = continue_implicit_branch(problem, x0, max_steps=80, step_size=0.12)
    assert trace.returned is True
    assert trace.branch_status == "returned"
    accepted = [s for s in trace.steps if s.accepted and s.x is not None]
    assert len(accepted) >= 8
    blob = json.dumps(trace.to_json_dict(), allow_nan=False)
    assert "NaN" not in blob
    assert trace.to_json_dict()["notes"]


def test_signed_rays_leave_seed_on_opposite_tangent_sides() -> None:
    problem = UnitCircleProblem()
    x0 = np.array([1.0, 0.0])
    t0 = branch_tangent(problem, x0)
    trace = continue_implicit_branch(problem, x0, max_steps=1, step_size=0.1)
    positive = next(
        step for step in trace.steps if step.accepted and step.x is not None and step.s > 0.0
    )
    negative = next(
        step for step in trace.steps if step.accepted and step.x is not None and step.s < 0.0
    )
    delta_positive = np.asarray(positive.x) - x0
    delta_negative = np.asarray(negative.x) - x0
    assert float(np.dot(delta_positive, t0)) > 0.0
    assert float(np.dot(delta_negative, t0)) < 0.0
    by_direction = {record.direction: record for record in trace.ray_records}
    assert by_direction["positive"].termination == "BUDGET_EXHAUSTED"
    assert by_direction["negative"].termination == "BUDGET_EXHAUSTED"


def test_parabola_does_not_return() -> None:
    problem = ParabolaProblem()
    trace = continue_implicit_branch(problem, np.array([0.0, 0.0]), max_steps=20, step_size=0.1)
    assert trace.returned is False
    assert trace.branch_status != "returned"


def test_return_is_not_position_only() -> None:
    periodic = (False, False, False, True, True)
    seed_x = np.array([0.0, 0.0, 0.0, 1.0, 0.0])
    seed_t = np.array([0.0, 0.0, 0.0, 0.0, 1.0])
    # First three coordinates match the seed (a position-only test would fire).
    x_same_position = np.array([0.0, 0.0, 0.0, 0.0, 1.0])
    assert (
        detect_branch_return(
            seed_x=seed_x,
            seed_t=seed_t,
            x=x_same_position,
            t=seed_t,
            accumulated_arclength=4.0,
            periodic=periodic,
            seed_branch_id="a",
            branch_id="a",
        )
        is False
    )


def test_h3_does_not_replace_d1_d2_correctors() -> None:
    assert continue_level_set.__module__.endswith("parent_level_sets")
    assert continue_uuur.__module__.endswith("virtual_u_child")
    src_d1 = continue_level_set.__code__.co_filename
    src_d2 = continue_uuur.__code__.co_filename
    assert "branch_continuation" not in src_d1
    assert "branch_continuation" not in src_d2
    assert "continue_implicit_branch" in inspect.getsource(continue_level_set)
    assert "continue_implicit_branch" in inspect.getsource(continue_uuur)
