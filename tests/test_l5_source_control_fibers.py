"""Source-control fiber residuals and per-c completeness."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    SourceControlCRecord,
    SourceIntervalStatus,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    build_source_control,
    classify_source_interval_status,
    h_value,
    radial_normal,
    unresolved_c_intervals_from_records,
)
from grashof_workspace.spatial_experiments.parent_level_sets import pointing_scalar

CONFIG = "configs/l5_positive_control_v1.json"


def test_source_control_samples_satisfy_constraints() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    discovery = build_direct_pointing_truth(
        arm, probe, config, split="discovery", icosphere_level=0, sobol_count=4, max_nfev=40, target_indices=(0, 1, 2)
    )
    result = build_source_control(
        arm, probe, discovery, c_count=3, confirmation_level=0, max_steps=8, step_size=0.1
    )
    n = radial_normal(probe.p_star)
    assert result.fibers
    for fiber in result.fibers:
        for q, d in zip(fiber.q_samples, fiber.pointing_samples, strict=False):
            state = arm.chain.evaluate(q)
            assert float(np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star))) <= 1e-6
            assert abs(pointing_scalar(state.d, n) - fiber.c) <= 1e-5
            assert abs(h_value(arm, q, n) - fiber.c) <= 1e-5
            assert abs(float(np.linalg.norm(d)) - 1.0) <= 1e-9


def test_source_control_reports_missing_c_intervals() -> None:
    c_values = (-0.5, 0.0, 0.5)
    records = (
        SourceControlCRecord(
            c=-0.5,
            expected_seed_count=2,
            projected_seed_count=2,
            continued_component_count=1,
            returned_count=1,
            open_count=0,
            singular_count=0,
            unresolved_count=0,
            deduplicated_component_ids=("ok_lo",),
            parameter_interval_status="RETURNED_COMPONENT_FOUND",
        ),
        SourceControlCRecord(
            c=0.0,
            expected_seed_count=2,
            projected_seed_count=0,
            continued_component_count=0,
            returned_count=0,
            open_count=0,
            singular_count=0,
            unresolved_count=2,
            deduplicated_component_ids=(),
            parameter_interval_status="UNRESOLVED",
        ),
        SourceControlCRecord(
            c=0.5,
            expected_seed_count=2,
            projected_seed_count=2,
            continued_component_count=1,
            returned_count=1,
            open_count=0,
            singular_count=0,
            unresolved_count=0,
            deduplicated_component_ids=("ok_hi",),
            parameter_interval_status="RETURNED_COMPONENT_FOUND",
        ),
    )
    intervals = unresolved_c_intervals_from_records(c_values, records)
    assert intervals
    assert any(lo <= 0.0 <= hi for lo, hi in intervals)


def test_source_returned_component_not_named_component_complete() -> None:
    status = classify_source_interval_status(returned_count=1, open_count=0, singular_count=0)
    assert status is SourceIntervalStatus.RETURNED_COMPONENT_FOUND
    assert status is not SourceIntervalStatus.COMPONENT_COMPLETE
    assert classify_source_interval_status(returned_count=0, open_count=1, singular_count=0) is SourceIntervalStatus.OPEN_ONLY
    assert classify_source_interval_status(returned_count=0, open_count=0, singular_count=1) is SourceIntervalStatus.SINGULAR
    covered = unresolved_c_intervals_from_records(
        (0.0,),
        (
            SourceControlCRecord(
                c=0.0,
                expected_seed_count=1,
                projected_seed_count=1,
                continued_component_count=1,
                returned_count=1,
                open_count=0,
                singular_count=0,
                unresolved_count=0,
                deduplicated_component_ids=("ok",),
                parameter_interval_status=SourceIntervalStatus.RETURNED_COMPONENT_FOUND.value,
            ),
        ),
    )
    assert covered == ()
    open_gap = unresolved_c_intervals_from_records(
        (0.0,),
        (
            SourceControlCRecord(
                c=0.0,
                expected_seed_count=1,
                projected_seed_count=1,
                continued_component_count=1,
                returned_count=0,
                open_count=1,
                singular_count=0,
                unresolved_count=0,
                deduplicated_component_ids=("open",),
                parameter_interval_status=SourceIntervalStatus.OPEN_ONLY.value,
            ),
        ),
    )
    assert open_gap
