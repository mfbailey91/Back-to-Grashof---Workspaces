"""Shared R3A L5 test fixtures; not a pytest collection module."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import LeafWorkRecord
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    continue_uuru_leaf,
    issue_leaf_certificate,
    leaf_spec_for,
    problem_from_source_seed,
)

CONFIG = "configs/l5_positive_control_v1.json"


def wrap_q(q: tuple[float, ...], delta: np.ndarray) -> tuple[float, ...]:
    arr = np.asarray(q, dtype=float) + np.asarray(delta, dtype=float)
    return tuple(float(np.arctan2(np.sin(value), np.cos(value))) for value in arr)


def work_from_q(arm, chart, probe, q, leaf_id: str, *, max_steps: int = 6) -> LeafWorkRecord | None:
    built = problem_from_source_seed(arm, chart, q, probe.p_star, leaf_id=leaf_id)
    if built is None:
        return None
    problem, x0 = built
    samples, status, returned = continue_uuru_leaf(
        problem,
        x0,
        max_steps=max_steps,
        step_size=0.08,
    )
    if not samples:
        return None
    spec = leaf_spec_for(
        probe.probe_id,
        chart,
        problem.lambda_fixed,
        probe.p_star,
        problem.problem_id,
    )
    cert = issue_leaf_certificate(
        spec,
        samples,
        branch_status=status,
        returned=returned,
        position_tol=1e-6,
        orientation_tol=1e-5,
        pointing_tol=1e-5,
        lift_tol=1e-8,
        lambda_tol=1e-5,
        closure_tol=1e-6,
    )
    return LeafWorkRecord(
        certificate=cert,
        problem=problem,
        seed_x=tuple(float(value) for value in x0),
        seed_q=tuple(float(value) for value in problem.physical_q(x0)),
        chart=chart,
        lambda_fixed=float(problem.lambda_fixed),
    )


def p1_fixture():
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    chart = charts_from_config(config.charts)[0]
    q0 = analytic_seed_configuration(config.geometry, probe)
    return config, arm, chart, probe, q0


def two_neighbor_works() -> tuple[LeafWorkRecord, LeafWorkRecord]:
    _config, arm, chart, probe, q0 = p1_fixture()
    work_a = work_from_q(arm, chart, probe, q0, "leaf_a", max_steps=6)
    assert work_a is not None
    for delta in (0.12, 0.2, 0.28, 0.36, -0.18, 0.45):
        q1 = wrap_q(q0, np.array([delta, 0.0, 0.0, 0.0, 0.0]))
        work_b = work_from_q(arm, chart, probe, q1, "leaf_b", max_steps=6)
        if work_b is None:
            continue
        gap = abs(
            float(
                np.arctan2(
                    np.sin(work_b.lambda_fixed - work_a.lambda_fixed),
                    np.cos(work_b.lambda_fixed - work_a.lambda_fixed),
                )
            )
        )
        if gap >= 0.05:
            return work_a, work_b
    raise AssertionError("could not construct a second distinct-lambda neighbor")
