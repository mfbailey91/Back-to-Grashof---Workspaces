"""Positive-control SURU geometry, aggregation, and wrist identity."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.axis_aggregation import (
    build_suru_multi_aggregation,
    build_suur_multi_aggregation,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
    evaluate_wrist_center,
)
from grashof_workspace.spatial_experiments.v06_corpus import build_exact_two_u_5r

CONFIG = "configs/l5_positive_control_v1.json"


def test_suru_aggregation_roles_and_status() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    q0 = (0.0, 0.0, 0.0, 0.0, 0.0)
    agg = build_suru_multi_aggregation(arm.model, q0)
    assert agg.axis_aggregation_status == "EXACT_GLOBAL"
    assert agg.joint_role_sequence == ("S_v", "U_phys", "R_phys", "U_phys")
    assert agg.joint_kind_sequence == ("S", "U", "R", "U")
    assert "U_v" not in agg.joint_role_sequence
    payload = agg.to_json_dict()
    assert payload["certificate_status"] is None


def test_suur_wrapper_still_exact_on_two_u_corpus() -> None:
    entry = build_exact_two_u_5r()
    agg = build_suur_multi_aggregation(entry.model, entry.regular_q)
    assert agg.axis_aggregation_status == "EXACT_GLOBAL"
    assert agg.family_label == "S_v-U_phys-U_phys-R"


def test_wrist_plus_offset_matches_tool_over_random_q() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    rng = np.random.default_rng(310031)
    ell = config.geometry.tool_offset
    for _ in range(24):
        q = tuple(float(v) for v in rng.uniform(-np.pi, np.pi, size=5))
        state = arm.chain.evaluate(q)
        wrist = evaluate_wrist_center(arm, q)
        assert float(np.linalg.norm(state.p - (wrist + ell * state.d))) <= 1e-12
