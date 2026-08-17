"""Source-control fiber residuals: p=p* and h=c."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    build_source_control,
    h_value,
    radial_normal,
)
from grashof_workspace.spatial_experiments.parent_level_sets import pointing_scalar

CONFIG = "configs/l5_positive_control_v1.json"


def test_source_control_samples_satisfy_constraints() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    discovery = build_direct_pointing_truth(
        arm, probe, config, split="discovery", icosphere_level=0, sobol_count=4, max_nfev=40, target_indices=(0, 1, 2)
    )
    result = build_source_control(
        arm, probe, discovery, c_count=3, confirmation_level=0, max_steps=8, step_size=0.1
    )
    n = radial_normal(probe.p_star)
    assert result.fibers
    for fiber in result.fibers:
        for q, d in zip(fiber.q_samples, fiber.pointing_samples):
            state = arm.chain.evaluate(q)
            assert float(np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star))) <= 1e-6
            assert abs(pointing_scalar(state.d, n) - fiber.c) <= 1e-5
            assert abs(h_value(arm, q, n) - fiber.c) <= 1e-5
            assert abs(float(np.linalg.norm(d)) - 1.0) <= 1e-9
