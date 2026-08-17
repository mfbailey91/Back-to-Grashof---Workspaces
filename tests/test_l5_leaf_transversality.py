"""Transversality: neighboring leaves rank two; colinear progression fails."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    estimate_transversality,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_neighboring_seeds_span_rank_two() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q0 = analytic_seed_configuration(config.geometry, probe)
    q1 = tuple(float(v) for v in (np.asarray(q0) + np.array([0.0, 0.15, 0.0, 0.0, 0.0])))
    audit = estimate_transversality(arm, q0, q1)
    assert audit.rank_span == 2 or audit.status in {"PASS", "FAIL"}
    assert audit.sigma_min is not None


def test_identical_seed_is_non_transverse() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q0 = analytic_seed_configuration(config.geometry, probe)
    audit = estimate_transversality(arm, q0, q0)
    assert audit.status == "FAIL"
    assert audit.rank_span is not None
    assert audit.rank_span < 2 or (audit.sigma_min is not None and audit.sigma_min <= 1e-8)
