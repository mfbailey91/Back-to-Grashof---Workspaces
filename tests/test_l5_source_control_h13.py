"""H13A opt-in source policy and analytical c-domain authority."""

from __future__ import annotations

import inspect
import json
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.branch_continuation import (
    BranchStep,
    BranchTrace,
    UnitCircleProblem,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.artifacts import (
    finalize_stage,
    update_artifact_index,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.campaign_package import (
    package_r3a_campaign,
    validate_package_scope,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.cli import write_manifest
from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CampaignBlocker,
    SourceControlCRecord,
    SourceIntervalStatus,
    SourceTraceTermination,
    load_campaign_config,
    stage_envelope,
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
    classify_source_interval_status_h13,
    cluster_wrapped_q,
    deduplicate_fibers_h13,
    densify_pointing_curve,
    load_h13_source_policy,
    project_source_seed_clusters,
    source_trace_diagnostic,
    unresolved_c_intervals_from_records_h13,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.sphere_grid import (
    pointing_geodesic,
)

H12_CONFIG = "configs/l5_positive_control_v1.json"
H13A_CONFIG = "configs/l5_positive_control_h13a_c_domain_v1.json"
H13_PILOT_CONFIG = "configs/l5_positive_control_h13_source_pilot_v1.json"
H13F_CONFIG = "configs/l5_positive_control_h13_source_v1.json"
P1_P3 = ("P1_DEEP_COMPLETE", "P3_INNER_INCOMPLETE")


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
        "endpoint_state_tol_rad": 0.05,
        "endpoint_tangent_abs_dot_min": 0.99,
        "curve_segment_fraction": 0.50,
        "continuation_step_size": 0.08,
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
        endpoint_state_tol_rad=float(values["endpoint_state_tol_rad"]),
        endpoint_tangent_abs_dot_min=float(values["endpoint_tangent_abs_dot_min"]),
        curve_segment_fraction=float(values["curve_segment_fraction"]),
        continuation_step_size=float(values["continuation_step_size"]),
    )


def _fiber(
    fiber_id: str,
    qs: tuple[tuple[float, ...], ...],
    *,
    returned: bool = False,
    closed: bool | None = None,
    termination: SourceTraceTermination | None = None,
    residual: float = 0.0,
) -> SourceControlFiber:
    is_closed = returned if closed is None else closed
    status = termination
    if status is None:
        status = (
            SourceTraceTermination.RETURNED_TO_SEED
            if is_closed
            else SourceTraceTermination.OPEN_UNCLASSIFIED
        )
    return SourceControlFiber(
        fiber_id=fiber_id,
        c=0.1,
        q_samples=qs,
        pointing_samples=tuple((1.0, 0.0, 0.0) for _ in qs),
        branch_status="returned" if is_closed else "open",
        returned=returned,
        max_position_residual_m=residual,
        max_h_residual=residual,
        closed=is_closed,
        termination_status=status.value,
        budget_exhausted=status is SourceTraceTermination.BUDGET_EXHAUSTED,
    )


def _step(s: float, x: tuple[float, float]) -> BranchStep:
    return BranchStep(
        s=s,
        x_pred=x,
        x=x,
        constraint_residual=0.0,
        gauge_residual=0.0,
        correction_norm=0.0,
        step_size=abs(s),
        newton_iterations=1,
        condition_number=1.0,
        rank=1,
        nullity=1,
        tangent_alignment=1.0,
        accepted=True,
        rejection_reason=None,
    )


def _trace(*steps: BranchStep, branch_status: str = "open") -> BranchTrace:
    return BranchTrace(
        problem_id="analytical_unit_circle",
        branch_id="trace",
        x_seed=(1.0, 0.0),
        steps=steps,
        branch_status=branch_status,
        returned=False,
        notes=(),
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
    assert policy.endpoint_state_tol_rad == pytest.approx(0.10)
    assert policy.endpoint_tangent_abs_dot_min == pytest.approx(0.85)
    assert policy.curve_segment_fraction == pytest.approx(0.50)
    assert policy.continuation_step_size == pytest.approx(0.08)
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
            parameter_interval_status=SourceIntervalStatus.RETURNED_SET_FOUND.value,
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
    assert annotated[1].parameter_interval_status == SourceIntervalStatus.RETURNED_SET_FOUND.value
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
    assert "raw_pointing_sample_count" not in h12_payload
    assert "rasterization_max_segment_rad" not in h12_payload
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
        assert record["parameter_interval_status"] != (
            SourceIntervalStatus.RETURNED_COMPONENT_FOUND.value
        )
    assert any(SEED_COUNT_SEMANTICS in note for note in h13_payload["notes"])
    if h13_payload["fibers"]:
        assert "termination_status" in h13_payload["fibers"][0]
        assert "closed" in h13_payload["fibers"][0]
    raw_from_fibers = sum(int(fiber["sample_count"]) for fiber in h13_payload["fibers"])
    assert h13_payload["raw_pointing_sample_count"] == raw_from_fibers
    assert "rasterized_pointing_sample_count" in h13_payload
    assert h13_payload["rasterization_max_segment_rad"] > 0.0
    assert h13_payload["rasterization_max_segment_rad"] != pytest.approx(
        h13_payload["c_slice_max_angular_spacing_rad"]
    )


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


def test_mixed_returned_and_open_traces_are_unresolved() -> None:
    status = classify_source_interval_status_h13(
        closed_count=1,
        open_count=1,
        singular_count=0,
        unresolved_count=0,
        budget_exhausted_count=0,
        seed_budget_exhausted=False,
        required=True,
    )
    assert status is SourceIntervalStatus.MIXED_UNRESOLVED


def test_seed_or_trace_budget_exhaustion_blocks_required_interval() -> None:
    for seed_budget, trace_budget in ((True, 0), (False, 1)):
        status = classify_source_interval_status_h13(
            closed_count=1,
            open_count=0,
            singular_count=0,
            unresolved_count=0,
            budget_exhausted_count=trace_budget,
            seed_budget_exhausted=seed_budget,
            required=True,
        )
        assert status is SourceIntervalStatus.BUDGET_EXHAUSTED


def test_legacy_returned_component_label_is_not_a_h13_covered_interval() -> None:
    record = SourceControlCRecord(
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
    assert unresolved_c_intervals_from_records_h13((0.0,), (record,)) == ((0.0, 0.0),)


def test_plus_minus_endpoints_can_close_away_from_seed() -> None:
    diagnostic = source_trace_diagnostic(
        UnitCircleProblem(),
        _trace(
            _step(-1.0, (-1.0, -0.02)),
            _step(0.0, (1.0, 0.0)),
            _step(1.0, (-1.0, 0.02)),
        ),
        max_steps=4,
        policy=_policy(),
    )
    assert diagnostic.closed is True
    assert diagnostic.accepted_arclength == pytest.approx(2.0)
    assert diagnostic.termination is SourceTraceTermination.PLUS_MINUS_ENDPOINTS_CLOSED


def test_exhausted_two_ray_trace_is_not_called_topologically_open() -> None:
    diagnostic = source_trace_diagnostic(
        UnitCircleProblem(),
        _trace(
            _step(-0.5, (0.0, -1.0)),
            _step(0.0, (1.0, 0.0)),
            _step(0.5, (0.0, 1.0)),
        ),
        max_steps=1,
        policy=_policy(),
    )
    assert diagnostic.closed is False
    assert diagnostic.budget_exhausted is True
    assert diagnostic.termination is SourceTraceTermination.BUDGET_EXHAUSTED


def test_closed_duplicate_is_retained_over_budget_duplicate() -> None:
    q = (
        (0.1, 0.2, 0.3, 0.4, 0.5),
        (0.15, 0.2, 0.3, 0.4, 0.5),
        (-0.1, 0.0, 0.1, 0.0, 0.0),
    )
    open_trace = _fiber(
        "open",
        q,
        closed=False,
        termination=SourceTraceTermination.BUDGET_EXHAUSTED,
    )
    closed_trace = _fiber(
        "closed",
        q,
        returned=True,
        closed=True,
        termination=SourceTraceTermination.RETURNED_TO_SEED,
    )
    out = deduplicate_fibers_h13((open_trace, closed_trace), tol=0.2)
    assert len(out) == 1
    assert out[0].fiber_id == "closed"


def test_h12_fiber_json_omits_h13_termination_keys() -> None:
    fiber = SourceControlFiber(
        fiber_id="h12",
        c=0.0,
        q_samples=((0.0, 0.0, 0.0, 0.0, 0.0),),
        pointing_samples=((1.0, 0.0, 0.0),),
        branch_status="returned",
        returned=True,
        max_position_residual_m=0.0,
        max_h_residual=0.0,
    )
    payload = fiber.to_json_dict()
    assert "termination_status" not in payload
    assert "closed" not in payload


def test_densified_curve_obeys_maximum_pointing_segment() -> None:
    dense = densify_pointing_curve(
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        max_segment_rad=0.2,
        closed=False,
    )
    gaps = [pointing_geodesic(a, b) for a, b in pairwise(dense)]
    assert len(dense) > 2
    assert max(gaps) <= 0.2 + 1e-12


def test_closed_curve_paints_closing_arc_and_open_curve_does_not() -> None:
    endpoints = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    opened = densify_pointing_curve(endpoints, max_segment_rad=0.2, closed=False)
    closed = densify_pointing_curve(endpoints, max_segment_rad=0.2, closed=True)
    assert len(closed) > len(opened)
    closed_gaps = [pointing_geodesic(a, b) for a, b in pairwise(closed)]
    closing_gap = pointing_geodesic(closed[-1], closed[0])
    assert max(closed_gaps) <= 0.2 + 1e-12
    assert closing_gap <= 0.2 + 1e-12


def _write_pilot_probe_files(raw: Path, probe_id: str) -> None:
    probe = raw / probe_id
    probe.mkdir(parents=True, exist_ok=True)
    (probe / "fixture.json").write_text(
        json.dumps({"probe_id": probe_id, "rank_jp": 5}),
        encoding="utf-8",
    )
    (probe / "direct_truth.json").write_text(
        json.dumps({"discovery": {"solves": [{"clusters": [1]}]}, "confirmation": {"solves": []}}),
        encoding="utf-8",
    )
    (probe / "source_control.json").write_text(
        json.dumps(
            {
                "fibers": [{"q_samples": [[0.0]], "fiber_id": "f", "component_id": "c0"}],
                "pointing_samples": [[1.0, 0.0, 0.0]],
                "c_records": [{"parameter_interval_status": "RETURNED_SET_FOUND"}],
            }
        ),
        encoding="utf-8",
    )
    (probe / "natural_family.json").write_text(
        json.dumps(
            {
                "leaves": [
                    {"accepted_for_reconstruction": False, "samples": [{"q_source": [0.0]}]}
                ]
            }
        ),
        encoding="utf-8",
    )
    (probe / "comparison.json").write_text(
        json.dumps({"probe_id": probe_id}),
        encoding="utf-8",
    )


def _hashed_h13_pilot_campaign(
    raw: Path,
    *,
    probe_ids: tuple[str, ...] = P1_P3,
    mode: str = "ci",
    include_render: bool = False,
    config_path: Path | str = H13_PILOT_CONFIG,
) -> None:
    resolved = Path(config_path)
    write_manifest(resolved, raw, mode=mode)
    config = load_campaign_config(resolved)
    for probe_id in probe_ids:
        _write_pilot_probe_files(raw, probe_id)
    stages: tuple[tuple[str, dict[str, object]], ...] = (
        ("fixture", {}),
        ("truth", {}),
        ("source-control", {}),
        ("leaves", {}),
        (
            "compare",
            {
                "disposition": "PARTIAL",
                "campaign_blocker": CampaignBlocker.STITCHING_CONTROL_BLOCKED.value,
                "accepted_reconstruction": False,
            },
        ),
    )
    for stage, payload in stages:
        finalize_stage(
            raw,
            {
                **stage_envelope(config, stage=stage, mode=mode, probe_ids=probe_ids),
                **payload,
            },
            config=config,
            stage=stage,
            mode=mode,
            probe_ids=probe_ids,
        )
    campaign = raw / "campaign.json"
    if campaign.is_file():
        (raw / "compare.json").write_text(campaign.read_text(encoding="utf-8"), encoding="utf-8")
        update_artifact_index(raw, (raw / "compare.json",))
    if include_render:
        (raw / "index.html").write_text("<html></html>", encoding="utf-8")
        finalize_stage(
            raw,
            stage_envelope(config, stage="render", mode=mode, probe_ids=probe_ids),
            config=config,
            stage="render",
            mode=mode,
            probe_ids=probe_ids,
        )


def test_h13_pilot_freezes_diagnostic_policy_and_cannot_close() -> None:
    config = load_campaign_config(H13_PILOT_CONFIG)
    policy = load_h13_source_policy(config, "full")
    assert config.schema_version == "r3a_l5_positive_control_h13_source_pilot_v1"
    assert h13_source_policy_requested(config) is True
    assert config.mode("ci").allows_full_campaign_disposition is False
    assert config.mode("smoke").allows_full_campaign_disposition is False
    assert config.mode("full").allows_full_campaign_disposition is False
    assert policy.continuation_step_size == pytest.approx(0.08)
    assert policy.curve_segment_fraction == pytest.approx(0.50)
    assert policy.c_slice_max_angular_spacing_cell_fraction == pytest.approx(0.75)
    probe_ids = [probe.probe_id for probe in config.probes]
    with pytest.raises(ValueError, match="cannot issue a full-campaign disposition"):
        validate_package_scope(
            {
                "config_hash": config.config_hash,
                "mode": "full",
                "probe_ids": probe_ids,
                "campaign_blocker": CampaignBlocker.STITCHING_CONTROL_BLOCKED.value,
                "accepted_reconstruction": False,
            },
            config,
            full_closeout=True,
        )


def test_h13_pilot_full_closeout_is_refused(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    config = load_campaign_config(H13_PILOT_CONFIG)
    probe_ids = tuple(probe.probe_id for probe in config.probes)
    _hashed_h13_pilot_campaign(raw, probe_ids=probe_ids, mode="full", include_render=True)
    with pytest.raises(ValueError, match="cannot issue a full-campaign disposition"):
        package_r3a_campaign(
            raw_root=raw,
            results_root=tmp_path / "compact",
            bundle_dir=tmp_path / "bundles",
            config_path=Path(H13_PILOT_CONFIG),
            full_closeout=True,
        )


def test_h13_pilot_p1_p3_ci_package_is_diagnostic(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    results = tmp_path / "compact"
    bundles = tmp_path / "bundles"
    _hashed_h13_pilot_campaign(raw, probe_ids=P1_P3, mode="ci")
    manifest = package_r3a_campaign(
        raw_root=raw,
        results_root=results,
        bundle_dir=bundles,
        config_path=Path(H13_PILOT_CONFIG),
    )
    assert manifest["package_kind"] == "diagnostic"
    assert manifest["campaign_mode"] == "ci"
    assert manifest["probe_ids"] == list(P1_P3)
    assert manifest["full_closeout_eligible"] is False
    assert manifest["allows_full_campaign_disposition"] is False
    assert manifest["all_configured_probes_present"] is False


def test_h13f_full_config_may_close_but_packages_diagnostic(tmp_path: Path) -> None:
    config = load_campaign_config(H13F_CONFIG)
    policy = load_h13_source_policy(config, "full")
    assert config.schema_version == "r3a_l5_positive_control_h13_source_v1"
    assert h13_source_policy_requested(config) is True
    assert config.mode("ci").allows_full_campaign_disposition is False
    assert config.mode("smoke").allows_full_campaign_disposition is False
    assert config.mode("full").allows_full_campaign_disposition is True
    assert policy.continuation_step_size == pytest.approx(0.08)
    probe_ids = [probe.probe_id for probe in config.probes]
    mode, declared, all_configured = validate_package_scope(
        {
            "config_hash": config.config_hash,
            "mode": "full",
            "probe_ids": probe_ids,
            "campaign_blocker": CampaignBlocker.STITCHING_CONTROL_BLOCKED.value,
            "accepted_reconstruction": False,
        },
        config,
        full_closeout=True,
    )
    assert mode == "full"
    assert declared == tuple(probe_ids)
    assert all_configured is True
    raw = tmp_path / "raw"
    _hashed_h13_pilot_campaign(
        raw,
        probe_ids=tuple(probe_ids),
        mode="full",
        include_render=True,
        config_path=H13F_CONFIG,
    )
    manifest = package_r3a_campaign(
        raw_root=raw,
        results_root=tmp_path / "compact",
        bundle_dir=tmp_path / "bundles",
        config_path=Path(H13F_CONFIG),
    )
    assert manifest["package_kind"] == "diagnostic"
    assert manifest["campaign_mode"] == "full"
    assert manifest["probe_ids"] == probe_ids
    assert manifest["full_closeout_eligible"] is False
    assert manifest["allows_full_campaign_disposition"] is True
    assert manifest["all_configured_probes_present"] is True
