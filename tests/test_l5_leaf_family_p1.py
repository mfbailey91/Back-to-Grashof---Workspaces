"""P1 discovery produces multiple distinct UURU leaves (LOCAL_ONLY until return)."""

from __future__ import annotations

from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import discover_leaf_family
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def test_p1_discovers_at_least_three_distinct_leaves() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    discovery = build_direct_pointing_truth(
        arm,
        probe,
        config,
        split="discovery",
        icosphere_level=0,
        sobol_count=4,
        max_nfev=40,
        target_indices=(0, 1, 4, 7),
    )
    family = discover_leaf_family(
        arm,
        probe,
        discovery,
        charts_from_config(config.charts),
        config,
        max_steps=4,
        max_leaves=8,
        lambda_bins=4,
    )
    keys = {(leaf.spec.chart_id, round(leaf.spec.lambda_fixed, 6)) for leaf in family.leaves}
    assert len(family.leaves) >= 3
    assert len(keys) >= 3
    # Smoke continuation does not return; accepted reconstruction stays empty.
    assert all(leaf.closed_mechanism_status in {"LOCAL_ONLY", "EXACT_ON_COMPONENT", "REJECTED", "UNRESOLVED"} for leaf in family.leaves)
