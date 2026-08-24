"""H13A opt-in source policy and analytical c-domain authority."""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pytest

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
    choose_c_values,
    h13_source_policy_requested,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control_h13 import (
    analytical_c_interval,
    annotate_analytical_endpoints,
    build_source_control_h13,
    choose_analytical_c_values,
    load_h13_source_policy,
    unresolved_c_intervals_from_records_h13,
)

H12_CONFIG = "configs/l5_positive_control_v1.json"
H13A_CONFIG = "configs/l5_positive_control_h13a_c_domain_v1.json"


def test_analytical_c_intervals_match_positive_control_oracle() -> None:
    config = load_campaign_config(H12_CONFIG)
    arm = build_positive_control_arm(config.geometry)
    expected = {
        "P1_DEEP_COMPLETE": (-1.0, 1.0),
        "P2_INNER_COMPLETE": (-1.0, 1.0),
        "P3_INNER_INCOMPLETE": (-1.0, 0.875),
        "P4_OUTER_COMPLETE": (-1.0, 1.0),
        "P5_OUTER_INCOMPLETE": (-0.7234848484848492, 1.0),
    }
    for probe_id, interval in expected.items():
        actual = analytical_c_interval(arm, config.probe(probe_id))
        assert actual == pytest.approx(interval, abs=1e-12)


def test_c_samples_include_endpoints_and_obey_angular_spacing() -> None:
    values = choose_analytical_c_values(
        (-1.0, 1.0),
        17,
        max_angular_spacing_rad=0.15,
    )
    assert values[0] == pytest.approx(-1.0)
    assert values[-1] == pytest.approx(1.0)
    theta = tuple(float(np.arccos(np.clip(value, -1.0, 1.0))) for value in values)
    gaps = [abs(a - b) for a, b in pairwise(theta)]
    assert max(gaps) <= 0.15 + 1e-12
    assert len(values) >= 17


def test_h12_choose_c_values_still_uses_discovery_extrema() -> None:
    values = choose_c_values((-0.2, 0.4), 3)
    assert values[0] == pytest.approx(-0.2)
    assert values[-1] == pytest.approx(0.4)
    analytical = choose_analytical_c_values((-1.0, 1.0), 3, max_angular_spacing_rad=10.0)
    assert analytical[0] == pytest.approx(-1.0)
    assert analytical[-1] == pytest.approx(1.0)


def test_h12_config_does_not_dispatch_to_h13() -> None:
    h12 = load_campaign_config(H12_CONFIG)
    h13 = load_campaign_config(H13A_CONFIG)
    assert h13_source_policy_requested(h12) is False
    assert h13_source_policy_requested(h13) is True
    with pytest.raises(ValueError, match="policy_version"):
        load_h13_source_policy(h12)


def test_h13a_full_cannot_issue_campaign_disposition() -> None:
    config = load_campaign_config(H13A_CONFIG)
    policy = load_h13_source_policy(config, "full")
    assert config.schema_version == "r3a_l5_positive_control_h13a_c_domain_v1"
    assert config.mode("ci").allows_full_campaign_disposition is False
    assert config.mode("smoke").allows_full_campaign_disposition is False
    assert config.mode("full").allows_full_campaign_disposition is False
    assert policy.c_slice_max_angular_spacing_cell_fraction == pytest.approx(0.75)


def test_analytical_endpoints_serialize_as_critical_or_boundary() -> None:
    records = (
        SourceControlCRecord(
            c=-1.0,
            expected_seed_count=1,
            projected_seed_count=1,
            continued_component_count=0,
            returned_count=0,
            open_count=1,
            singular_count=0,
            unresolved_count=0,
            deduplicated_component_ids=("open_lo",),
            parameter_interval_status=SourceIntervalStatus.OPEN_ONLY.value,
        ),
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
        SourceControlCRecord(
            c=1.0,
            expected_seed_count=1,
            projected_seed_count=0,
            continued_component_count=0,
            returned_count=0,
            open_count=0,
            singular_count=1,
            unresolved_count=0,
            deduplicated_component_ids=(),
            parameter_interval_status=SourceIntervalStatus.SINGULAR.value,
        ),
    )
    c_values = (-1.0, 0.0, 1.0)
    annotated = annotate_analytical_endpoints(c_values, records)
    assert annotated[0].parameter_interval_status == SourceIntervalStatus.CRITICAL_OR_BOUNDARY.value
    assert annotated[1].parameter_interval_status == SourceIntervalStatus.RETURNED_COMPONENT_FOUND.value
    assert annotated[2].parameter_interval_status == SourceIntervalStatus.CRITICAL_OR_BOUNDARY.value
    unresolved = unresolved_c_intervals_from_records_h13(c_values, annotated)
    assert unresolved == ()


def test_h13a_json_records_analytical_domain_h12_does_not() -> None:
    h12 = load_campaign_config(H12_CONFIG)
    h13 = load_campaign_config(H13A_CONFIG)
    arm = build_positive_control_arm(h12.geometry)
    probe = h12.probe("P1_DEEP_COMPLETE")
    discovery = build_direct_pointing_truth(
        arm,
        probe,
        h12,
        split="discovery",
        icosphere_level=0,
        sobol_count=4,
        max_nfev=40,
        target_indices=(0, 1, 2),
    )
    h12_payload = build_source_control(
        arm, probe, discovery, c_count=3, confirmation_level=0, max_steps=8, step_size=0.1
    ).to_json_dict()
    h13_result = build_source_control_h13(
        arm,
        probe,
        discovery,
        config=h13,
        mode="ci",
        max_steps=8,
        step_size=0.1,
    )
    h13_payload = h13_result.to_json_dict()
    assert "analytical_c_interval" not in h12_payload
    assert h13_payload["analytical_c_interval"] == pytest.approx([-1.0, 1.0], abs=1e-12)
    assert h13_payload["c_values"][0] == pytest.approx(-1.0)
    assert h13_payload["c_values"][-1] == pytest.approx(1.0)
    assert h13_payload["effective_c_value_count"] >= h13_payload["requested_c_value_count"]
    assert h13_payload["c_records"][0]["parameter_interval_status"] == (
        SourceIntervalStatus.CRITICAL_OR_BOUNDARY.value
    )
    assert h13_payload["c_records"][-1]["parameter_interval_status"] == (
        SourceIntervalStatus.CRITICAL_OR_BOUNDARY.value
    )
    theta = tuple(
        float(np.arccos(np.clip(value, -1.0, 1.0))) for value in h13_payload["c_values"]
    )
    gaps = [abs(a - b) for a, b in pairwise(theta)]
    assert max(gaps) <= h13_payload["c_slice_max_angular_spacing_rad"] + 1e-12
