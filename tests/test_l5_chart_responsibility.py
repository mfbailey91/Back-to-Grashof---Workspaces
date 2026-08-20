"""Canonical chart responsibility and per-chart leaf budgets."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    audit_family_intervals,
    required_chart_transition_pairs,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    IntervalStatus,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    canonical_chart,
    chart_quality,
    charts_from_config,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def test_all_configured_charts_appear_even_without_leaves() -> None:
    config = load_campaign_config(CONFIG)
    chart_ids = tuple(item.chart_id for item in config.charts)
    n_bins = 3
    records = audit_family_intervals((), n_bins=n_bins, chart_ids=chart_ids)
    seen = {item.chart_id for item in records}
    assert seen == set(chart_ids)
    assert len(records) == len(chart_ids) * n_bins
    assert all(item.interval_status is IntervalStatus.NOT_REQUIRED for item in records)
    assert all(item.required is False for item in records)
    assert all(item.leaf_count == 0 for item in records)


def test_chart_responsibility_is_deterministic() -> None:
    config = load_campaign_config(CONFIG)
    charts = charts_from_config(config.charts)
    policy = config.chart_atlas_policy
    rotation = charts[0].compose(0.3, 0.8, -0.4)
    first = canonical_chart(charts, rotation, policy=policy)
    second = canonical_chart(charts, rotation, policy=policy)
    assert first == second
    assert first is not None
    qualities = {chart.chart_id: chart_quality(chart, rotation) for chart in charts}
    eligible = {
        chart_id: quality
        for chart_id, quality in qualities.items()
        if quality > policy.singularity_margin
    }
    best = max(eligible.values())
    winners = [chart_id for chart_id, quality in eligible.items() if abs(quality - best) <= 1e-15]
    expected = min(winners, key=lambda chart_id: policy.chart_ids.index(chart_id))
    assert first == expected
    reversed_order = tuple(reversed(policy.chart_ids))
    tied = canonical_chart(charts, rotation, policy=policy, tie_break_order=reversed_order)
    if len(winners) == 1:
        assert tied == first
    else:
        assert tied == min(winners, key=lambda chart_id: reversed_order.index(chart_id))


def test_full_budget_covers_required_bins_by_policy() -> None:
    config = load_campaign_config(CONFIG)
    full = config.mode("full")
    n_charts = len(config.charts)
    assert full.max_natural_leaves_per_chart == full.natural_lambda_bin_count_per_chart
    assert full.max_natural_leaves_per_probe == n_charts * full.max_natural_leaves_per_chart
    assert full.max_natural_leaves_per_probe >= n_charts * full.natural_lambda_bin_count_per_chart
    assert full.max_natural_leaves_per_probe != 36
    assert config.chart_atlas_policy.canonical_assignment == "max_abs_sin_beta"
    assert config.chart_atlas_policy.chart_ids == tuple(item.chart_id for item in config.charts)


def test_overlap_band_drives_required_transition_pairs() -> None:
    config = load_campaign_config(CONFIG)
    charts = charts_from_config(config.charts)
    rotation = None
    for chart in charts:
        for beta in (0.4, 0.8, 1.2):
            candidate = chart.compose(0.37, beta, -0.29)
            qualities = sorted((chart_quality(item, candidate) for item in charts), reverse=True)
            if qualities[0] - qualities[1] > 1e-6 and qualities[1] > 1e-6:
                rotation = candidate
                break
        if rotation is not None:
            break
    assert rotation is not None

    class FixedRotationChain:
        def evaluate(self, _q):
            return SimpleNamespace(R=rotation)

    arm = SimpleNamespace(chain=FixedRotationChain())
    source_qs = ((0.0, 0.0, 0.0, 0.0, 0.0),)
    wide_policy = replace(
        config.chart_atlas_policy,
        singularity_margin=0.0,
        overlap_margin=1.0,
    )
    required = required_chart_transition_pairs(
        arm,
        charts,
        source_qs,
        policy=wide_policy,
    )
    assert required
    assert all(samples == source_qs for samples in required.values())

    narrow_policy = replace(
        config.chart_atlas_policy,
        singularity_margin=0.0,
        overlap_margin=0.0,
    )
    not_required = required_chart_transition_pairs(
        arm,
        charts,
        source_qs,
        policy=narrow_policy,
    )
    assert not_required == {}
