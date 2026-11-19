"""Raster-cause classification uses synthetic segment records, not the arm."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics import (
    RASTER_ACCEPTED_FAILURE,
    RASTER_DEPTH,
    RASTER_FAILED_CORRECTION,
    RASTER_HIDDEN,
    RASTER_INTERVAL_COVERED,
    RASTER_NO_FAILURE,
    RASTER_NONLOCAL,
    RASTER_RESIDUAL,
    RASTER_UNTRACED_CLOSING,
    classify_raster_observation,
)


def _segment(
    outcome: str,
    *,
    closing: bool = False,
    distance: float | None = None,
    span: float = 0.2,
) -> dict[str, object]:
    start = [0.0, 0.0, 0.0, 0.0, 0.0]
    end = [span, 0.0, 0.0, 0.0, 0.0]
    return {
        "outcome": outcome,
        "closing_segment": closing,
        "endpoint_q": [start, end],
        "wrapped_correction_distance_rad": distance,
        "angular_gap_rad": 0.05,
    }


def test_open_ray_closing_failure_is_an_untraced_gap() -> None:
    classification = classify_raster_observation(
        {
            "segments": [
                _segment("within_declared_gap"),
                _segment("failed_correction", closing=True, distance=0.5),
            ],
            "rasterization_complete": False,
            "correction_failure_count": 1,
            "depth_budget_exhausted": False,
            "positive_ray_termination": "BUDGET_EXHAUSTED",
            "negative_ray_termination": "RETURNED_TO_SEED",
            "stored_interval_status": "MIXED_UNRESOLVED",
            "interval_required": True,
            "max_position_residual_m": 1e-11,
            "max_h_residual": 1e-11,
            "position_tolerance_m": 1e-8,
            "h_tolerance": 1e-8,
            "interior_probes": [{"correction_ok": True, "pointing_excursion_rad": 1e-4}],
            "max_segment_rad": 0.08,
        }
    )
    assert classification["demonstrated_cause"] == RASTER_UNTRACED_CLOSING
    assert classification["interval_blocked"] is True
    assert classification["open_ray"] is True


def test_depth_exhaustion_stays_incomplete() -> None:
    classification = classify_raster_observation(
        {
            "segments": [_segment("depth_exhausted", closing=True)],
            "rasterization_complete": False,
            "depth_budget_exhausted": True,
            "correction_failure_count": 0,
            "positive_ray_termination": "RETURNED_TO_SEED",
            "negative_ray_termination": "RETURNED_TO_SEED",
            "stored_interval_status": "MIXED_UNRESOLVED",
            "interval_required": True,
            "interior_probes": [],
        }
    )
    assert classification["demonstrated_cause"] == RASTER_DEPTH
    assert classification["interval_blocked"] is True


def test_completed_raster_cannot_hide_residual_or_failure() -> None:
    residual = classify_raster_observation(
        {
            "segments": [_segment("within_declared_gap")],
            "rasterization_complete": True,
            "max_position_residual_m": 1e-6,
            "max_h_residual": 1e-12,
            "position_tolerance_m": 1e-8,
            "h_tolerance": 1e-8,
            "interior_probes": [{"correction_ok": True, "pointing_excursion_rad": 0.0}],
            "max_segment_rad": 0.08,
        }
    )
    assert residual["demonstrated_cause"] == RASTER_RESIDUAL
    failure = classify_raster_observation(
        {
            "segments": [_segment("failed_correction")],
            "rasterization_complete": True,
            "correction_failure_count": 1,
            "depth_budget_exhausted": False,
            "interior_probes": [],
        }
    )
    assert failure["demonstrated_cause"] == RASTER_ACCEPTED_FAILURE


def test_nonlocal_correction_and_hidden_excursion_are_distinct() -> None:
    nonlocal_jump = classify_raster_observation(
        {
            "segments": [_segment("corrected", distance=0.4, span=0.2)],
            "rasterization_complete": False,
            "correction_failure_count": 0,
            "depth_budget_exhausted": False,
            "interior_probes": [],
        }
    )
    assert nonlocal_jump["demonstrated_cause"] == RASTER_NONLOCAL
    hidden = classify_raster_observation(
        {
            "segments": [_segment("within_declared_gap")],
            "rasterization_complete": True,
            "max_position_residual_m": 1e-12,
            "max_h_residual": 1e-12,
            "position_tolerance_m": 1e-8,
            "h_tolerance": 1e-8,
            "max_segment_rad": 0.08,
            "interior_probes": [{"correction_ok": True, "pointing_excursion_rad": 0.2}],
        }
    )
    assert hidden["demonstrated_cause"] == RASTER_HIDDEN


def test_clean_raster_and_uncovered_interval_contract() -> None:
    clean = classify_raster_observation(
        {
            "segments": [_segment("within_declared_gap", closing=True)],
            "rasterization_complete": True,
            "max_position_residual_m": 1e-12,
            "max_h_residual": 1e-12,
            "position_tolerance_m": 1e-8,
            "h_tolerance": 1e-8,
            "max_segment_rad": 0.08,
            "stored_interval_status": "RETURNED_SET_FOUND",
            "interval_required": True,
            "positive_ray_termination": "RETURNED_TO_SEED",
            "negative_ray_termination": None,
            "interior_probes": [{"correction_ok": True, "pointing_excursion_rad": 1e-5}],
        }
    )
    assert clean["demonstrated_cause"] == RASTER_NO_FAILURE
    covered = classify_raster_observation(
        {
            "segments": [_segment("failed_correction")],
            "rasterization_complete": False,
            "correction_failure_count": 1,
            "stored_interval_status": "RETURNED_SET_FOUND",
            "interval_required": True,
            "positive_ray_termination": "RETURNED_TO_SEED",
            "negative_ray_termination": "RETURNED_TO_SEED",
            "interior_probes": [],
        }
    )
    assert covered["demonstrated_cause"] == RASTER_INTERVAL_COVERED


def test_traced_segment_failure_is_not_relabeled_as_a_closing_gap() -> None:
    classification = classify_raster_observation(
        {
            "segments": [
                _segment("failed_correction"),
                _segment("failed_correction", closing=True),
            ],
            "rasterization_complete": False,
            "correction_failure_count": 2,
            "positive_ray_termination": "BUDGET_EXHAUSTED",
            "negative_ray_termination": "RETURNED_TO_SEED",
            "interior_probes": [],
        }
    )
    assert classification["demonstrated_cause"] == RASTER_FAILED_CORRECTION


_RECEIPT = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "l5_reconstruction"
    / "h13h"
    / "h13h3_raster_diagnosis.json"
)


def test_h13h3_receipt_records_diagnosis_without_acceptance() -> None:
    receipt = json.loads(_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "r3a_h13h3_raster_diagnosis_v1"
    assert receipt["work_package"] == "H13H-3"
    assert receipt["diagnostic_only"] is True
    assert receipt["accepted_reconstruction"] is False
    assert receipt["source_policy_validated"] is False
    assert receipt["continuation_solver_changed"] is False
    assert receipt["production_raster_changed"] is True
    assert receipt["replay_still_shows_nonlocal_sample"] is False
    assert receipt["natural_budget_changed"] is False
    assert set(receipt["category_counts"]) >= {
        "passing_regular",
        "budget_exhausted",
        "mixed_bin",
        "raster_failing",
        "singular_or_corrector",
    }
    by_category = {item["category"]: item for item in receipt["cases"]}
    assert set(by_category) == {
        "closing_control",
        "raster_failing",
        "depth_exhausted_closing",
        "open_ray_completed",
    }
    expected = {
        "closing_control": RASTER_NO_FAILURE,
        "raster_failing": RASTER_UNTRACED_CLOSING,
        "depth_exhausted_closing": RASTER_UNTRACED_CLOSING,
        "open_ray_completed": RASTER_NO_FAILURE,
    }
    for category, cause in expected.items():
        item = by_category[category]
        assert item["stored_fiber_agreement"] is True
        assert item["classification"]["demonstrated_cause"] == cause
        assert item["classification"]["nonlocal_correction_count"] == 0
    assert by_category["raster_failing"]["classification"]["interval_blocked"] is True
    assert by_category["depth_exhausted_closing"]["replay_depth_budget_exhausted"] is False
    assert by_category["closing_control"]["replay_rasterization_complete"] is True
    repair = receipt["repair"]
    assert repair["continuation_max_steps_per_ray"] == "not_added"
    assert repair["h13h_source_convergence_v1"] == "not_registered"
    assert repair["raster_depth_increased"] is False
