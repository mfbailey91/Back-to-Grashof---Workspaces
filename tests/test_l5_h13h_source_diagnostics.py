"""H13H source-only diagnostics: selection, parity inputs, and replay evidence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    SourceTraceTermination,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    SourceControlFiber,
    h_value,
    radial_normal,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control_h13g import (
    continue_source_fiber_h13g,
    load_h13g_source_policy,
    rasterize_fiber_kinematically,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics import (
    REPORT_SCHEMA,
    audit_source_campaign,
    compare_source_reports,
    select_diagnostic_cases,
)
from grashof_workspace.spatial_experiments.parent_level_sets import (
    PointingLevelSetProblem,
    correct_to_levelset,
    pointing_scalar,
)

REPO = Path(__file__).resolve().parents[1]
H13G_CONFIG = REPO / "configs" / "l5_positive_control_h13g_source_pilot_v1.json"
HISTORICAL_PILOT = REPO / "outputs" / "r3a_h13g_source_pilot"


def _fiber(
    fiber_id: str,
    *,
    c: float,
    termination: str,
    raster_complete: bool,
    budget: bool = False,
) -> dict[str, object]:
    return {
        "fiber_id": fiber_id,
        "c": c,
        "termination_status": termination,
        "budget_exhausted": budget,
        "rasterization_complete": raster_complete,
        "positive_ray_termination": termination,
        "negative_ray_termination": None,
        "positive_accepted_steps": 1,
        "negative_accepted_steps": 0,
        "rasterization_failure_count": 0 if raster_complete else 1,
        "pointing_samples": [[1.0, 0.0, 0.0]],
        "rasterized_pointing_samples": [[1.0, 0.0, 0.0]],
    }


def _record(c: float, status: str) -> dict[str, object]:
    return {"c": c, "required": True, "parameter_interval_status": status}


def test_selection_is_deterministic_and_keeps_distinct_failure_categories() -> None:
    probes = [
        {
            "probe_id": "P1_DEEP_COMPLETE",
            "c_records": [_record(0.1, "RETURNED_SET_FOUND"), _record(0.2, "MIXED_UNRESOLVED")],
            "fibers": [
                _fiber(
                    "P1_DEEP_COMPLETE_c0_t0",
                    c=0.1,
                    termination="RETURNED_TO_SEED",
                    raster_complete=True,
                ),
                _fiber(
                    "P1_DEEP_COMPLETE_c1_t0",
                    c=0.2,
                    termination="BUDGET_EXHAUSTED",
                    raster_complete=False,
                    budget=True,
                ),
                _fiber(
                    "P1_DEEP_COMPLETE_c1_t1",
                    c=0.2,
                    termination="CORRECTOR_FAILURE",
                    raster_complete=False,
                ),
            ],
        }
    ]
    first, counts = select_diagnostic_cases(probes)
    second, _ = select_diagnostic_cases(probes)
    assert [item["fiber_id"] for item in first.values()] == [item["fiber_id"] for item in second.values()]
    assert first["passing_regular"]["fiber_id"] == "P1_DEEP_COMPLETE_c0_t0"
    assert first["budget_exhausted"]["fiber_id"] == "P1_DEEP_COMPLETE_c1_t0"
    assert first["mixed_bin"]["fiber_id"] == "P1_DEEP_COMPLETE_c1_t1"
    assert first["raster_failing"]["fiber_id"] == "P1_DEEP_COMPLETE_c1_t0"
    assert first["singular_or_corrector"]["fiber_id"] == "P1_DEEP_COMPLETE_c1_t1"
    assert counts["singular_or_corrector"] == 1


def test_selection_omits_singular_category_when_absent() -> None:
    probes = [
        {
            "probe_id": "P4_OUTER_COMPLETE",
            "c_records": [_record(0.0, "RETURNED_SET_FOUND")],
            "fibers": [
                _fiber(
                    "P4_OUTER_COMPLETE_c0_t0",
                    c=0.0,
                    termination="RETURNED_TO_SEED",
                    raster_complete=True,
                )
            ],
        }
    ]
    selected, counts = select_diagnostic_cases(probes)
    assert "singular_or_corrector" not in selected
    assert counts["singular_or_corrector"] == 0


def _report(hits: list[bool], *, commit: str = "abc") -> dict[str, object]:
    column = {
        "missed_covered_fraction": 0.0,
        "missed_covered_fraction_state": "VALUE",
        "false_positive_fraction": None,
        "false_positive_fraction_state": "NOT_APPLICABLE",
        "hausdorff_rad": 0.0,
        "hausdorff_rad_state": "VALUE",
        "max_cell_diameter_rad": 1.0,
        "fine": {
            "missed_covered_fraction": 0.0,
            "missed_covered_fraction_state": "VALUE",
            "false_positive_fraction": None,
            "false_positive_fraction_state": "NOT_APPLICABLE",
            "hausdorff_rad": 0.0,
            "hausdorff_rad_state": "VALUE",
            "max_cell_diameter_rad": 1.0,
        },
        "coarse": {
            "missed_covered_fraction": 0.0,
            "missed_covered_fraction_state": "VALUE",
            "false_positive_fraction": None,
            "false_positive_fraction_state": "NOT_APPLICABLE",
            "hausdorff_rad": 0.0,
            "hausdorff_rad_state": "VALUE",
            "max_cell_diameter_rad": 2.0,
        },
    }
    labels = ["STRICT_COVERED", "STRICT_COVERED"]
    return {
        "schema_version": REPORT_SCHEMA,
        "config_hash": "left-hash" if hits[0] else "right-hash",
        "producer_git": {"git_commit": commit},
        "probe_ids": ["P1_DEEP_COMPLETE"],
        "probes": [
            {
                "probe_id": "P1_DEEP_COMPLETE",
                "fine_level": 3,
                "coarse_level": 2,
                "columns": {"source_vs_direct": column, "source_vs_oracle": column},
                "masks": {
                    "fine_oracle_labels": labels,
                    "coarse_oracle_labels": labels,
                    "fine_direct_labels": labels,
                    "coarse_direct_labels": labels,
                    "fine_source_hits": hits,
                    "coarse_source_hits": hits,
                },
            }
        ],
    }


def test_cross_run_comparison_detects_moving_holes_with_equal_scalars(tmp_path: Path) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text(json.dumps(_report([True, False])), encoding="utf-8")
    right.write_text(json.dumps(_report([False, True], commit="abc")), encoding="utf-8")
    # The helper above changes config hash when the first hit is false. Force equal code and different hashes.
    payload = json.loads(right.read_text(encoding="utf-8"))
    payload["config_hash"] = "right-hash"
    payload["producer_git"] = {"git_commit": "abc"}
    right.write_text(json.dumps(payload), encoding="utf-8")
    result = compare_source_reports(left_path=left, right_path=right, outdir=tmp_path / "out")
    assert result["compatible_convergence_pair"] is True
    assert result["left_config_hash"] != result["right_config_hash"]
    occupancy = result["probes"][0]["occupancy_disagreement"]["source_vs_direct"]["fine"]
    assert occupancy["value"] == 1.0
    assert result["probes"][0]["occupancy_disagreement"]["source_vs_oracle"]["fine"]["value"] == 1.0
    assert result["run_level_gates_evaluated"] is False
    assert result["within_cross_run_limit"] is False


def test_cross_run_comparison_refuses_different_producer_code(tmp_path: Path) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text(json.dumps(_report([True, True], commit="one")), encoding="utf-8")
    right.write_text(json.dumps(_report([True, True], commit="two")), encoding="utf-8")
    result = compare_source_reports(left_path=left, right_path=right, outdir=tmp_path / "out")
    assert result["compatible_convergence_pair"] is False
    assert "producer code differs" in result["problems"]


def test_trace_observer_preserves_fiber_and_records_construction_seed() -> None:
    config = load_campaign_config(H13G_CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    n = radial_normal(probe.p_star)
    seed = analytic_seed_configuration(arm.geometry, probe)
    c = h_value(arm, seed, n)
    problem = PointingLevelSetProblem(
        model=arm.model,
        p_star=probe.p_star,
        n=n,
        c=c,
        problem_id="observer_seed",
    )
    vt = np.linalg.svd(
        np.asarray(problem.jacobian(np.asarray(seed, dtype=float)), dtype=float),
        full_matrices=True,
    )[2]
    regular_seed = tuple(float(value) for value in np.asarray(seed, dtype=float) + 0.2 * vt[-2])
    policy = load_h13g_source_policy(config, "ci")
    plain = continue_source_fiber_h13g(
        arm,
        probe,
        n,
        c,
        regular_seed,
        fiber_id="observer_fiber",
        max_steps=3,
        policy=policy,
    )
    observed: list[dict[str, object]] = []
    recorded = continue_source_fiber_h13g(
        arm,
        probe,
        n,
        c,
        regular_seed,
        fiber_id="observer_fiber",
        max_steps=3,
        policy=policy,
        trace_observer=observed.append,
    )
    assert recorded.q_samples == plain.q_samples
    assert recorded.termination_status == plain.termination_status
    assert len(observed) == 1
    observation = observed[0]
    assert observation["trace_cover_seed"] == [float(value) for value in regular_seed]
    branch_trace = observation["branch_trace"]
    assert isinstance(branch_trace, dict)
    assert observation["continuation_seed"] == branch_trace["x_seed"]
    assert observation["continuation_seed"] != "inferred_from_first_sample"
    unchanged = rasterize_fiber_kinematically(
        arm,
        probe,
        n,
        plain,
        max_segment_rad=0.05,
        max_depth=4,
    )
    untouched: list[dict[str, object]] = []
    unchanged_observed = rasterize_fiber_kinematically(
        arm,
        probe,
        n,
        plain,
        max_segment_rad=0.05,
        max_depth=4,
        segment_observer=untouched.append,
    )
    assert unchanged_observed.pointings == unchanged.pointings
    assert unchanged_observed.complete == unchanged.complete
    assert untouched == []
    endpoints: list[tuple[float, ...]] = []
    directions = []
    for scale in (-0.6, 0.6):
        guess = tuple(float(value) for value in np.asarray(seed, dtype=float) + scale * vt[-2])
        corrected, ok, _residual = correct_to_levelset(arm.model, guess, probe.p_star, n, c)
        assert ok
        q_endpoint = tuple(float(value) for value in corrected)
        endpoints.append(q_endpoint)
        directions.append(as_vec3(arm.chain.evaluate(q_endpoint).d))
    gap_fiber = SourceControlFiber(
        fiber_id="raster_gap",
        c=c,
        q_samples=tuple(endpoints),
        pointing_samples=tuple(directions),
        branch_status="open",
        returned=False,
        max_position_residual_m=0.0,
        max_h_residual=0.0,
    )
    raster_plain = rasterize_fiber_kinematically(
        arm,
        probe,
        n,
        gap_fiber,
        max_segment_rad=1e-6,
        max_depth=6,
    )
    segments: list[dict[str, object]] = []
    raster_observed = rasterize_fiber_kinematically(
        arm,
        probe,
        n,
        gap_fiber,
        max_segment_rad=1e-6,
        max_depth=6,
        segment_observer=segments.append,
    )
    assert raster_observed.pointings == raster_plain.pointings
    assert raster_observed.complete == raster_plain.complete
    assert segments
    corrected_segments = [item for item in segments if item["outcome"] == "corrected"]
    assert corrected_segments
    sample_segment = corrected_segments[0]
    assert sample_segment["midpoint_guess"] is not None
    assert sample_segment["corrected_q"] is not None
    assert sample_segment["h_residual"] is not None
    assert "local_tangent" in sample_segment
    assert any(isinstance(item["local_tangent"], list) for item in corrected_segments)
    assert plain.termination_status != SourceTraceTermination.PROJECTION_FAILED.value
    assert abs(pointing_scalar(plain.pointing_samples[0], n) - c) <= 1e-6


@pytest.mark.stress
def test_historical_h13g_audit_matches_stored_direct_and_source_columns(tmp_path: Path) -> None:
    """Recompute stored direct/source columns.

    The historical source records omit hit masks, so the existing evaluator
    paints every stored pointing. That is the parity check, and it is slow.
    """
    if not HISTORICAL_PILOT.is_dir():
        pytest.skip("historical H13G pilot outputs are gitignored and absent")
    report = audit_source_campaign(
        config_path=H13G_CONFIG,
        campaign_root=HISTORICAL_PILOT,
        outdir=tmp_path / "audit",
    )
    assert report["natural_family_used"] is False
    assert report["accepted_reconstruction"] is False
    assert report["probe_ids"] == [
        "P1_DEEP_COMPLETE",
        "P4_OUTER_COMPLETE",
        "P5_OUTER_INCOMPLETE",
    ]
    assert all(probe["parity"]["matches"] is True for probe in report["probes"])
    inventory = (tmp_path / "audit" / "source_failure_inventory.csv").read_text(encoding="utf-8")
    assert "BUDGET_EXHAUSTED" in inventory
    assert (tmp_path / "audit" / "selected_trace_diagnostics.json").is_file()
    assert (tmp_path / "audit" / "source_diagnostic_review.html").is_file()
