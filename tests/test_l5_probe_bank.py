"""Frozen five-point probe bank: labels, seeds, rank/nullity."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.fixed_position import (
    audit_fixed_position_seed,
    pose_fixed_position_problem,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
    fixture_seed_for_probe,
    point_completeness_oracle,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_five_probes_match_expected_completeness_and_rank() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    margin = config.tolerances.strict_analytical_boundary_margin_m
    expected_complete = {
        "P1_DEEP_COMPLETE": True,
        "P2_INNER_COMPLETE": True,
        "P3_INNER_INCOMPLETE": False,
        "P4_OUTER_COMPLETE": True,
        "P5_OUTER_INCOMPLETE": False,
    }
    for probe in config.probes:
        completeness = point_completeness_oracle(config.geometry, probe.p_star, margin_tol_m=margin)
        assert completeness.complete is expected_complete[probe.probe_id]
        assert completeness.complete is probe.expected_pointing_complete
        q = fixture_seed_for_probe(
            arm,
            probe,
            position_tol_m=config.tolerances.position_residual_m,
            pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
        )
        posed = pose_fixed_position_problem(arm.model, q)
        audit = audit_fixed_position_seed(posed)
        assert audit.rank_jp == 3
        assert audit.nullity_jp == 2
        state = arm.chain.evaluate(q)
        assert float(np.linalg.norm(state.p - np.asarray(probe.p_star))) <= 1e-8
