"""H13A opt-in source policy and analytical c-domain authority."""

from __future__ import annotations

import inspect
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
    SourceControlFiber,
    build_source_control,
    choose_c_values,
    h13_source_policy_requested,
    radial_normal,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control_h13 import (
    SEED_COUNT_SEMANTICS,
    H13ASourcePolicy,
    analytical_c_interval,
    annotate_analytical_endpoints,
    build_source_control_h13,
    choose_analytical_c_values,
    classify_h13b_interval_status,
    cluster_wrapped_q,
    deduplicate_fibers_h13,
    load_h13_source_policy,
    project_source_seed_clusters,
    unresolved_c_intervals_from_records_h13,
)

H12_CONFIG = "configs/l5_positive_control_v1.json"
H13A_CONFIG = "configs/l5_positive_control_h13a_c_domain_v1.json"


def _policy(**overrides: float) -> H13ASourcePolicy:
    values: dict[str, float] = {
        "c_slice_max_angular_spacing_cell_fraction": 0.75,
        "discovery_q_precluster_tol_rad": 0.15,
        "seed_h_window": 0.35,
        "seed_precluster_q_tol_rad": 0.35,
        "seed_projected_q_tol_rad": 0.20,
        "dedup_q_tol_rad": 0.35,
        "max_seed_candidates_per_c": 24,
        "max_seed_clusters_per_c": 3,
    }
    values.update(overrides)
    return H13ASourcePolicy(
        c_slice_max_angular_spacing_cell_fraction=float(
            values["c_slice_max_angular_spacing_cell_fraction"]
        ),
        discovery_q_precluster_tol_rad=float(values["discovery_q_precluster_tol_rad"]),
        seed_h_window=float(values["seed_h_window"]),
        seed_precluster_q_tol_rad=float(values["seed_precluster_q_tol_rad"]),
        seed_projected_q_tol_rad=float(values["seed_projected_q_tol_rad"]),
        dedup_q_tol_rad=float(values["dedup_q_tol_rad"]),
        max_seed_candidates_per_c=int(values["max_seed_candidates_per_c"]),
        max_seed_clusters_per_c=int(values["max_seed_clusters_per_c"]),
    )


def _fiber(
    fiber_id: str,
    qs: tuple[tuple[float, ...], ...],
    *,
    returned: bool,
    residual: float = 0.0,
) -> SourceControlFiber:
    return SourceControlFiber(
        fiber_id=fiber_id,
        c=0.1,
        q_samples=qs,
        pointing_samples=tuple((1.0, 0.0, 0.0) for _ in qs),
        branch_status="returned" if returned else "open",
        returned=returned,
        max_position_residual_m=residual,
        max_h_residual=residual,
    )


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
    assert policy.max_seed_candidates_per_c == 1024
    assert policy.max_seed_clusters_per_c == 16
    ci = load_h13_source_policy(config, "ci")
    smoke = load_h13_source_policy(config, "smoke")
    assert ci.max_seed_candidates_per_c == 24
    assert ci.max_seed_clusters_per_c == 3
    assert smoke.max_seed_candidates_per_c == 256
    assert smoke.max_seed_clusters_per_c == 8


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
    interior = [
        record
        for record in h13_payload["c_records"]
        if record["parameter_interval_status"] != SourceIntervalStatus.CRITICAL_OR_BOUNDARY.value
    ]
    assert interior
    for record in h13_payload["c_records"]:
        assert record["seed_count_semantics"] == SEED_COUNT_SEMANTICS
        assert record["attempted_seed_count"] == record["expected_seed_count"]
    assert any(SEED_COUNT_SEMANTICS in note for note in h13_payload["notes"])


def test_h12_build_source_control_still_uses_first_three() -> None:
    source = inspect.getsource(build_source_control)
    assert "chosen = seeds[:3]" in source


def test_wrapped_q_clustering_merges_equivalent_representatives() -> None:
    values = (
        (np.pi - 0.01, 0.0, 0.0, 0.0, 0.0),
        (-np.pi + 0.01, 0.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
    )
    clusters = cluster_wrapped_q(values, tol=0.05)
    assert len(clusters) == 2


def test_seed_candidate_cap_is_explicit_and_blocking() -> None:
    config = load_campaign_config(H12_CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    n = radial_normal(probe.p_star)
    configurations = (
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (2.0, 2.0, 2.0, 2.0, 2.0),
    )
    discovery = project_source_seed_clusters(
        arm,
        probe,
        n,
        0.0,
        configurations,
        policy=_policy(max_seed_candidates_per_c=1, max_seed_clusters_per_c=12),
    )
    assert discovery.candidate_configuration_count == 2
    assert discovery.projection_attempt_count == 1
    assert discovery.budget_exhausted is True
    status = classify_h13b_interval_status(
        required=True,
        seed_budget_exhausted=True,
        returned_count=1,
        open_count=0,
        singular_count=0,
    )
    assert status is SourceIntervalStatus.BUDGET_EXHAUSTED
    endpoint = classify_h13b_interval_status(
        required=False,
        seed_budget_exhausted=True,
        returned_count=1,
        open_count=0,
        singular_count=0,
    )
    assert endpoint is SourceIntervalStatus.CRITICAL_OR_BOUNDARY
    record = SourceControlCRecord(
        c=0.0,
        expected_seed_count=1,
        projected_seed_count=1,
        continued_component_count=1,
        returned_count=1,
        open_count=0,
        singular_count=0,
        unresolved_count=0,
        deduplicated_component_ids=("returned",),
        parameter_interval_status=SourceIntervalStatus.BUDGET_EXHAUSTED.value,
        attempted_seed_count=1,
        seed_budget_exhausted=True,
    )
    assert unresolved_c_intervals_from_records_h13((0.0,), (record,)) == ((0.0, 0.0),)
    payload = record.to_json_dict()
    assert payload["seed_budget_exhausted"] is True
    assert payload["seed_count_semantics"] == SEED_COUNT_SEMANTICS
    h12_record = SourceControlCRecord(
        c=0.0,
        expected_seed_count=1,
        projected_seed_count=1,
        continued_component_count=1,
        returned_count=1,
        open_count=0,
        singular_count=0,
        unresolved_count=0,
        deduplicated_component_ids=("legacy",),
        parameter_interval_status=SourceIntervalStatus.RETURNED_COMPONENT_FOUND.value,
    )
    assert "seed_count_semantics" not in h12_record.to_json_dict()


def test_returned_duplicate_is_retained_over_nonreturned_duplicate() -> None:
    q = (
        (0.1, 0.2, 0.3, 0.4, 0.5),
        (0.15, 0.2, 0.3, 0.4, 0.5),
        (-0.1, 0.0, 0.1, 0.0, 0.0),
    )
    open_trace = _fiber("open", q, returned=False, residual=0.1)
    returned_trace = _fiber("returned", q, returned=True, residual=0.0)
    out = deduplicate_fibers_h13((open_trace, returned_trace), tol=0.2)
    assert len(out) == 1
    assert out[0].fiber_id == "returned"


def test_asymmetric_source_q_subsets_remain_distinct() -> None:
    short = ((0.0, 0.0, 0.0, 0.0, 0.0), (0.1, 0.0, 0.0, 0.0, 0.0))
    long = short + ((1.5, 0.0, 0.0, 0.0, 0.0), (1.6, 0.0, 0.0, 0.0, 0.0))
    out = deduplicate_fibers_h13(
        (_fiber("short", short, returned=True), _fiber("long", long, returned=False)),
        tol=0.2,
    )
    assert {fiber.fiber_id for fiber in out} == {"short", "long"}
