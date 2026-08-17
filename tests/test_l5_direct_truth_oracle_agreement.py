"""Post-solve oracle agreement for direct pointing truth."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
    compare_direct_truth_to_oracle,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
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
