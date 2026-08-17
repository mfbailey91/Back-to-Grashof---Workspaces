"""Analytical pointing oracle interior, exterior, and boundary cases."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CompletenessLabel,
    OracleFeasibility,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    direction_oracle,
    point_completeness_oracle,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_direction_oracle_interior_and_exterior() -> None:
    config = load_campaign_config(CONFIG)
    geo = config.geometry
    p_complete = np.array([1.0, 0.0, 0.0])
    feasible = direction_oracle(geo, p_complete, np.array([1.0, 0.0, 0.0]), margin_tol_m=1e-12)
    assert feasible.feasibility is OracleFeasibility.FEASIBLE
    p_inner = np.array([0.35, 0.0, 0.0])
    infeasible = direction_oracle(geo, p_inner, np.array([1.0, 0.0, 0.0]), margin_tol_m=1e-12)
    assert infeasible.feasibility is OracleFeasibility.INFEASIBLE


def test_point_completeness_matches_formula() -> None:
    config = load_campaign_config(CONFIG)
    geo = config.geometry
    deep = point_completeness_oracle(geo, np.array([1.0, 0.0, 0.0]), margin_tol_m=1e-12)
    assert deep.complete is True
    assert deep.label is CompletenessLabel.COMPLETE
    inner_partial = point_completeness_oracle(geo, np.array([0.35, 0.0, 0.0]), margin_tol_m=1e-12)
    assert inner_partial.complete is False
    assert inner_partial.label is CompletenessLabel.PARTIAL
    outer_partial = point_completeness_oracle(geo, np.array([1.65, 0.0, 0.0]), margin_tol_m=1e-12)
    assert outer_partial.complete is False


def test_boundary_returns_boundary_not_a_forced_sign() -> None:
    config = load_campaign_config(CONFIG)
    geo = config.geometry
    # rho = r_min + ell = 0.4 is the inner completeness boundary.
    boundary = point_completeness_oracle(geo, np.array([0.4, 0.0, 0.0]), margin_tol_m=1e-9)
    assert boundary.label is CompletenessLabel.BOUNDARY
    assert boundary.complete is False
    # Radial outward at the inner completeness boundary places the wrist on r_min.
    p = np.array([0.4, 0.0, 0.0])
    result = direction_oracle(geo, p, np.array([1.0, 0.0, 0.0]), margin_tol_m=1e-9)
    assert result.feasibility is OracleFeasibility.BOUNDARY
