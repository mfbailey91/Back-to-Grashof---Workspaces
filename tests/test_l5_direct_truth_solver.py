"""Direct source-chain pointing truth tests (reduced CI budgets)."""

from __future__ import annotations

import json

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
    compare_direct_truth_to_oracle,
    pointing_residual,
    solve_target,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    OracleFeasibility,
    PointingSolveStatus,
    json_dumps_strict,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
    direction_oracle,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.sphere_grid import build_sphere_grid

CONFIG = "configs/l5_positive_control_v1.json"


def test_residual_and_deep_complete_solves() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q_seed = analytic_seed_configuration(config.geometry, probe)
    d = np.asarray(arm.chain.evaluate(q_seed).d, dtype=float)
    r = pointing_residual(arm.chain, q_seed, np.asarray(probe.p_star), d)
    assert float(np.linalg.norm(r[:3])) <= 1e-8
    solve = solve_target(
        arm.chain,
        np.asarray(probe.p_star),
        d,
        starts=[(q_seed, "probe_seed")],
        max_nfev=80,
        position_tol_m=config.tolerances.position_residual_m,
        pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
        target_index=0,
    )
    assert solve.status is PointingSolveStatus.FOUND
    assert solve.best_pointing_geodesic_rad is not None
    assert solve.best_pointing_geodesic_rad <= 1e-6


def test_known_infeasible_direction_is_not_found() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P3_INNER_INCOMPLETE")
    d = np.asarray(probe.p_star, dtype=float)
    d = d / float(np.linalg.norm(d))
    oracle = direction_oracle(
        config.geometry, probe.p_star, d, margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m
    )
    assert oracle.feasibility is OracleFeasibility.INFEASIBLE
    grid = build_sphere_grid(0)
    # Use the vertex nearest the infeasible radial-outward direction.
    idx = int(np.argmax(grid.vertices @ d))
    truth = build_direct_pointing_truth(
        arm,
        probe,
        config,
        split="confirmation",
        icosphere_level=0,
        sobol_count=8,
        max_nfev=60,
        target_indices=(idx,),
        neighbor_propagate=False,
    )
    assert truth.solves[0].status is not PointingSolveStatus.FOUND
    agreement = compare_direct_truth_to_oracle(
        truth, config.geometry, probe.p_star, margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m
    )
    assert agreement.n_strict_oracle_infeasible_found == 0
    json.dumps(truth.to_json_dict(), allow_nan=False)


def test_wrapped_clustering_and_json() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q = analytic_seed_configuration(config.geometry, probe)
    q_wrap = tuple(v + 2.0 * np.pi for v in q)
    d = np.asarray(arm.chain.evaluate(q).d)
    solve = solve_target(
        arm.chain,
        np.asarray(probe.p_star),
        d,
        starts=[(q, "probe_seed"), (q_wrap, "sobol_bank")],
        max_nfev=40,
        position_tol_m=1e-6,
        pointing_tol_rad=1e-5,
        target_index=0,
    )
    assert solve.status is PointingSolveStatus.FOUND
    assert len(solve.clusters) == 1
    json.dumps(json.loads(json_dumps_strict(solve.to_json_dict())), allow_nan=False)


def test_oracle_does_not_rewrite_status() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    truth = build_direct_pointing_truth(
        arm,
        probe,
        config,
        split="discovery",
        icosphere_level=0,
        sobol_count=4,
        max_nfev=40,
        target_indices=(0, 1),
        neighbor_propagate=True,
    )
    before = tuple(s.status for s in truth.solves)
    compare_direct_truth_to_oracle(
        truth, config.geometry, probe.p_star, margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m
    )
    assert tuple(s.status for s in truth.solves) == before
