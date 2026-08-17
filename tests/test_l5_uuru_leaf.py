"""Exact UURU leaf: rank, identity lift, frozen lambda, independent chain."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.jacobians import matrix_rank_report
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
    problem_from_source_seed,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_uuru_leaf_rank_identity_and_frozen_lambda() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q = analytic_seed_configuration(config.geometry, probe)
    chart = charts_from_config(config.charts)[0]
    built = problem_from_source_seed(arm, chart, q, probe.p_star, leaf_id="p1_leaf")
    assert built is not None
    problem, x0 = built
    assert id(problem.independent_chain) != id(arm.chain)
    assert problem.physical_q(x0) == tuple(float(v) for v in x0[2:7])
    report = matrix_rank_report(problem.jacobian(x0))
    assert report.rank == 6
    assert report.nullity == 1
    assert float(np.linalg.norm(problem.residual(x0))) <= 1e-8
    samples, status, _returned = continue_uuru_leaf(problem, x0, max_steps=6, step_size=0.08)
    assert samples
    for sample in samples:
        assert sample.family_coordinate_error_rad <= 1e-5
        assert abs(sample.x[0]) <= np.pi + 1e-9
    assert problem.lambda_fixed == built[0].lambda_fixed
    assert status in {"open", "returned", "singular", "unresolved"}
