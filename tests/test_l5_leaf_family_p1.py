"""P1 discovery produces multiple distinct UURU leaves; open leaves leave gaps."""

from __future__ import annotations

from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import discover_leaf_family
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    IntervalStatus,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def _p1_family():
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
    return family


def test_p1_discovers_at_least_three_distinct_leaves() -> None:
    family = _p1_family()
    keys = {(leaf.spec.chart_id, round(leaf.spec.lambda_fixed, 6)) for leaf in family.leaves}
    assert len(family.leaves) >= 3
    assert len(keys) >= 3
    # Smoke continuation does not return; accepted reconstruction stays empty.
    assert all(
        leaf.closed_mechanism_status in {"LOCAL_ONLY", "EXACT_ON_COMPONENT", "REJECTED", "UNRESOLVED"}
        for leaf in family.leaves
    )


def test_open_natural_leaf_creates_unresolved_lambda_interval() -> None:
    family = _p1_family()
    assert family.accepted_count == 0
    assert any(leaf.closed_mechanism_status == "LOCAL_ONLY" or leaf.returned is False for leaf in family.leaves)
    assert family.lambda_intervals
    chart_ids = {item.chart_id for item in family.lambda_intervals}
    assert chart_ids == {"ZYZ_WORLD", "ZYZ_RX90", "ZYZ_RY90"}
    assert all(item.interval_status != "COMPLETE" for item in family.lambda_intervals)
    sampled = {
        IntervalStatus.SAMPLED_LOCAL,
        IntervalStatus.SAMPLED_COMPONENT,
        IntervalStatus.SAMPLED_ADMISSIBLE,
        IntervalStatus.UNSAMPLED,
        IntervalStatus.UNRESOLVED,
        IntervalStatus.CRITICAL_OR_BOUNDARY,
        IntervalStatus.NOT_REQUIRED,
    }
    assert all(item.interval_status in sampled for item in family.lambda_intervals)
    assert any(
        item.interval_status
        in {
            IntervalStatus.SAMPLED_LOCAL,
            IntervalStatus.SAMPLED_COMPONENT,
            IntervalStatus.UNSAMPLED,
            IntervalStatus.UNRESOLVED,
        }
        for item in family.lambda_intervals
    )
    assert all(leaf.accepted_for_reconstruction is False for leaf in family.leaves)
