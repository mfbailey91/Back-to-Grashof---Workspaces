"""Post-solve oracle agreement for direct pointing truth."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
    compare_direct_truth_to_oracle,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    DirectPointingTruth,
    OracleFeasibility,
    PointingSolveStatus,
    PointingTargetSolve,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
    direction_oracle,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_no_accepted_solution_violates_strict_shell() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    for probe_id in ("P1_DEEP_COMPLETE", "P3_INNER_INCOMPLETE"):
        probe = config.probe(probe_id)
        truth = build_direct_pointing_truth(
            arm,
            probe,
            config,
            split="confirmation",
            icosphere_level=0,
            sobol_count=6,
            max_nfev=50,
            target_indices=(0, 3, 7),
            neighbor_propagate=True,
        )
        agreement = compare_direct_truth_to_oracle(
            truth,
            config.geometry,
            probe.p_star,
            margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m,
        )
        assert agreement.n_strict_oracle_infeasible_found == 0


def _synthetic_solve(
    index: int, direction: tuple[float, float, float], status: PointingSolveStatus
) -> PointingTargetSolve:
    return PointingTargetSolve(
        target_index=index,
        d_target=direction,
        status=status,
        clusters=(),
        best_position_residual_m=None,
        best_pointing_geodesic_rad=None,
        n_starts=1,
    )


def test_strict_feasible_unresolved_is_a_blocker() -> None:
    config = load_campaign_config(CONFIG)
    probe = config.probe("P1_DEEP_COMPLETE")
    margin = config.tolerances.strict_analytical_boundary_margin_m
    oracle = direction_oracle(config.geometry, probe.p_star, (1.0, 0.0, 0.0), margin_tol_m=margin)
    assert oracle.feasibility is OracleFeasibility.FEASIBLE
    truth = DirectPointingTruth(
        probe_id=probe.probe_id,
        split="confirmation",
        icosphere_level=0,
        solves=(_synthetic_solve(0, (1.0, 0.0, 0.0), PointingSolveStatus.UNRESOLVED),),
        found_count=0,
        not_found_count=0,
        unresolved_count=1,
    )
    before = tuple(s.status for s in truth.solves)
    agreement = compare_direct_truth_to_oracle(truth, config.geometry, probe.p_star, margin_tol_m=margin)
    assert tuple(s.status for s in truth.solves) == before
    assert agreement.n_strict_oracle_feasible_missing >= 1


def test_found_in_strict_infeasible_is_false_positive() -> None:
    config = load_campaign_config(CONFIG)
    probe = config.probe("P3_INNER_INCOMPLETE")
    margin = config.tolerances.strict_analytical_boundary_margin_m
    norm = sum(float(v) * float(v) for v in probe.p_star) ** 0.5
    radial = tuple(float(v) / norm for v in probe.p_star)
    oracle = direction_oracle(config.geometry, probe.p_star, radial, margin_tol_m=margin)
    assert oracle.feasibility is OracleFeasibility.INFEASIBLE
    truth = DirectPointingTruth(
        probe_id=probe.probe_id,
        split="confirmation",
        icosphere_level=0,
        solves=(_synthetic_solve(0, radial, PointingSolveStatus.FOUND),),
        found_count=1,
        not_found_count=0,
        unresolved_count=0,
    )
    agreement = compare_direct_truth_to_oracle(truth, config.geometry, probe.p_star, margin_tol_m=margin)
    assert agreement.n_strict_oracle_infeasible_found >= 1
