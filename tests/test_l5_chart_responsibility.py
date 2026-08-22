"""Canonical chart responsibility and per-chart leaf budgets."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from l5_test_support import two_neighbor_works as _two_neighbor_works

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    _family_chart_overlap,
    audit_family_intervals,
    required_chart_transition_pairs,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    IntervalStatus,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    canonical_chart,
    chart_quality,
    charts_from_config,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def _dummy_arm() -> SimpleNamespace:
    class FixedRotationChain:
        def evaluate(self, _q):
            return SimpleNamespace(R=None)

    return SimpleNamespace(chain=FixedRotationChain())


def _overlap_kwargs(config):
    return {
        "q_tol": config.tolerances.leaf_duplicate_distance_rad,
        "rotation_tol": config.tolerances.orientation_geodesic_rad,
        "pointing_tol": config.tolerances.pointing_geodesic_rad,
        "lambda_tol": config.tolerances.family_coordinate_error_rad,
    }


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


def test_out_of_band_chart_pair_is_not_applicable() -> None:
    config = load_campaign_config(CONFIG)
    charts = charts_from_config(config.charts)
    audits = _family_chart_overlap(
        _dummy_arm(),
        charts,
        (),
        required_transitions={},
        policy=config.chart_atlas_policy,
        **_overlap_kwargs(config),
    )
    assert len(audits) == 3
    assert all(item.status == "NOT_APPLICABLE" for item in audits)
    assert all(item.required is False for item in audits)
    assert all(item.transition_sample_count == 0 for item in audits)
    assert all(item.chart_id_a and item.chart_id_b for item in audits)
    assert all(item.responsibility_transition_id == f"{item.chart_id_a}<->{item.chart_id_b}" for item in audits)
    assert all("overlap band" in " ".join(item.notes).lower() for item in audits)


def test_required_transition_without_matched_leaves_is_unresolved() -> None:
    config = load_campaign_config(CONFIG)
    charts = charts_from_config(config.charts)
    policy = config.chart_atlas_policy
    pair = (policy.chart_ids[0], policy.chart_ids[1])
    source_q = (0.0, 0.0, 0.0, 0.0, 0.0)
    audits = _family_chart_overlap(
        _dummy_arm(),
        charts,
        (),
        required_transitions={pair: (source_q,)},
        policy=policy,
        **_overlap_kwargs(config),
    )
    required = tuple(item for item in audits if item.required)
    optional = tuple(item for item in audits if not item.required)
    assert len(required) == 1
    assert required[0].status == "UNRESOLVED"
    assert required[0].chart_id_a == pair[0]
    assert required[0].chart_id_b == pair[1]
    assert required[0].leaf_id_a is None
    assert required[0].leaf_id_b is None
    assert required[0].transition_sample_count == 1
    assert required[0].responsibility_transition_id == f"{pair[0]}<->{pair[1]}"
    assert all(item.status == "NOT_APPLICABLE" for item in optional)


def _copy_work_onto_chart(work, chart, leaf_id: str):
    return replace(
        work,
        chart=chart,
        certificate=replace(
            work.certificate,
            spec=replace(work.certificate.spec, leaf_id=leaf_id, chart_id=chart.chart_id),
        ),
    )


def test_frozen_lambda_leaves_are_audited_as_separate_pairs() -> None:
    config = load_campaign_config(CONFIG)
    charts = charts_from_config(config.charts)
    arm = build_positive_control_arm(config.geometry)
    work_a, work_b = _two_neighbor_works()
    copy_a = _copy_work_onto_chart(work_a, charts[1], "leaf_a_chart1")
    copy_b = _copy_work_onto_chart(work_b, charts[1], "leaf_b_chart1")
    pair = (charts[0].chart_id, charts[1].chart_id)
    audits = _family_chart_overlap(
        arm,
        charts,
        (work_a, work_b, copy_a, copy_b),
        required_transitions={pair: (work_a.seed_q, work_b.seed_q)},
        policy=config.chart_atlas_policy,
        **_overlap_kwargs(config),
    )
    required = tuple(item for item in audits if item.required)
    pairs = {(item.leaf_id_a, item.leaf_id_b) for item in required}
    assert len(required) == 2
    assert pairs == {
        (work_a.certificate.spec.leaf_id, "leaf_a_chart1"),
        (work_b.certificate.spec.leaf_id, "leaf_b_chart1"),
    }
    assert all(item.chart_id_a == pair[0] and item.chart_id_b == pair[1] for item in required)
    assert all(item.transition_sample_count == 1 for item in required)


def test_repeated_transition_samples_dedup_to_one_leaf_pair() -> None:
    config = load_campaign_config(CONFIG)
    charts = charts_from_config(config.charts)
    arm = build_positive_control_arm(config.geometry)
    work_a, _work_b = _two_neighbor_works()
    copy_a = _copy_work_onto_chart(work_a, charts[1], "leaf_a_chart1")
    pair = (charts[0].chart_id, charts[1].chart_id)
    audits = _family_chart_overlap(
        arm,
        charts,
        (work_a, copy_a),
        required_transitions={pair: (work_a.seed_q, work_a.seed_q)},
        policy=config.chart_atlas_policy,
        **_overlap_kwargs(config),
    )
    required = tuple(item for item in audits if item.required)
    assert len(required) == 1
    assert required[0].leaf_id_a == work_a.certificate.spec.leaf_id
    assert required[0].leaf_id_b == "leaf_a_chart1"
    assert required[0].transition_sample_count == 2
