"""Continuation-cause classification uses synthetic traces, not the arm."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics import (
    CAUSE_BIN_BLOCKED,
    CAUSE_CORRECTOR,
    CAUSE_HIDDEN_RAY,
    CAUSE_MISSED_RETURN,
    CAUSE_NO_FAILURE,
    CAUSE_REGULAR_BUDGET,
    CAUSE_SINGULAR,
    CAUSE_UNRESOLVED,
    POSSIBLE_ENDPOINT_MEETING,
    POSSIBLE_RETURN_SAMPLING,
    POSSIBLE_SINGULAR_WITHOUT_RANK,
    classify_continuation_observation,
    next_continuation_step_budget,
)


def _step(
    *,
    accepted: bool,
    step_size: float,
    reason: str | None = None,
    rank: int = 4,
    nullity: int = 1,
) -> dict[str, object]:
    return {
        "accepted": accepted,
        "step_size": step_size,
        "rejection_reason": reason,
        "rank": rank,
        "nullity": nullity,
    }


def _ray(direction: str, termination: str, arclength: float = 1.0) -> dict[str, object]:
    return {
        "direction": direction,
        "termination": termination,
        "accepted_arclength": arclength,
        "rejection_reason_counts": {},
    }


def _observation(
    outcome: str,
    rays: list[dict[str, object]],
    steps: list[dict[str, object]],
    **extra: object,
) -> dict[str, object]:
    returned = outcome == "RETURNED_TO_SEED"
    return {
        "outcome": outcome,
        "returned": returned,
        "closed": outcome == "PLUS_MINUS_ENDPOINTS_CLOSED",
        "branch_trace": {
            "returned": returned,
            "steps": steps,
            "ray_records": rays,
        },
        **extra,
    }


def test_regular_budget_is_distinct_from_return_sampling_hypothesis() -> None:
    observation = _observation(
        "BUDGET_EXHAUSTED",
        [_ray("positive", "BUDGET_EXHAUSTED", 2.0), _ray("negative", "BUDGET_EXHAUSTED", 1.5)],
        [_step(accepted=True, step_size=0.0), _step(accepted=True, step_size=0.25)],
    )
    result = classify_continuation_observation(observation)
    assert result["demonstrated_cause"] == CAUSE_REGULAR_BUDGET
    assert result["possible_causes"] == [POSSIBLE_RETURN_SAMPLING]
    assert result["reached_step_cap"] is True
    assert result["accepted_arclength"] == 3.5
    assert result["closure_route"] is None
    bounded = classify_continuation_observation(
        observation,
        bounded_replay={"kind": "step_count", "baseline_returned": False, "comparison_returned": True},
    )
    assert bounded["demonstrated_cause"] == CAUSE_REGULAR_BUDGET


def test_minimum_step_collapse_is_not_regular_budget() -> None:
    observation = _observation(
        "BUDGET_EXHAUSTED",
        [_ray("positive", "BUDGET_EXHAUSTED"), _ray("negative", "BUDGET_EXHAUSTED")],
        [_step(accepted=True, step_size=1e-4), _step(accepted=True, step_size=-1e-4)],
    )
    result = classify_continuation_observation(observation)
    assert result["demonstrated_cause"] == CAUSE_CORRECTOR
    assert result["minimum_step_collapse"] is True


def test_corrector_failure_without_rank_evidence_is_not_singular() -> None:
    observation = _observation(
        "CORRECTOR_FAILURE",
        [_ray("positive", "CORRECTOR_FAILURE"), _ray("negative", "CORRECTOR_FAILURE")],
        [_step(accepted=False, step_size=0.04, reason="corrector_failed")],
    )
    result = classify_continuation_observation(observation)
    assert result["demonstrated_cause"] == CAUSE_CORRECTOR
    assert result["rank_evidence"] is False


def test_singular_label_requires_retained_rank_evidence() -> None:
    singular = _observation(
        "SINGULAR_OR_CRITICAL_ENDPOINT",
        [_ray("positive", "SINGULAR"), _ray("negative", "SINGULAR")],
        [_step(accepted=False, step_size=0.08, reason="singular", rank=3, nullity=2)],
    )
    demonstrated = classify_continuation_observation(singular)
    assert demonstrated["demonstrated_cause"] == CAUSE_SINGULAR
    unlabeled = _observation(
        "SINGULAR_OR_CRITICAL_ENDPOINT",
        [_ray("positive", "SINGULAR"), _ray("negative", "SINGULAR")],
        [_step(accepted=False, step_size=0.08, reason="singular", rank=4, nullity=1)],
    )
    unresolved = classify_continuation_observation(unlabeled)
    assert unresolved["demonstrated_cause"] == CAUSE_UNRESOLVED
    assert POSSIBLE_SINGULAR_WITHOUT_RANK in unresolved["possible_causes"]


def test_disagreement_between_rays_is_not_collapsed_into_one_ray_label() -> None:
    observation = _observation(
        "CORRECTOR_FAILURE",
        [_ray("positive", "BUDGET_EXHAUSTED"), _ray("negative", "CORRECTOR_FAILURE")],
        [_step(accepted=True, step_size=0.08)],
    )
    result = classify_continuation_observation(observation)
    assert result["demonstrated_cause"] == CAUSE_HIDDEN_RAY
    assert result["ray_terminations"]["positive"] == "BUDGET_EXHAUSTED"


def test_seed_return_on_one_ray_remains_a_seed_return() -> None:
    observation = _observation(
        "RETURNED_TO_SEED",
        [_ray("positive", "RETURNED_TO_SEED"), _ray("negative", "BUDGET_EXHAUSTED")],
        [_step(accepted=True, step_size=0.08)],
        stored_interval_status="RETURNED_SET_FOUND",
    )
    result = classify_continuation_observation(observation)
    assert result["demonstrated_cause"] == CAUSE_NO_FAILURE
    assert result["closure_route"] == "seed_return"


def test_closed_trace_in_a_blocked_bin_is_not_a_continuation_failure() -> None:
    observation = _observation(
        "RETURNED_TO_SEED",
        [_ray("positive", "RETURNED_TO_SEED"), _ray("negative", "RETURNED_TO_SEED")],
        [_step(accepted=True, step_size=0.08)],
    )
    result = classify_continuation_observation(observation, stored_interval_status="MIXED_UNRESOLVED")
    assert result["demonstrated_cause"] == CAUSE_BIN_BLOCKED
    assert result["closure_route"] == "seed_return"


def test_endpoint_closure_stays_distinct_from_seed_return() -> None:
    observation = _observation(
        "PLUS_MINUS_ENDPOINTS_CLOSED",
        [_ray("positive", "BUDGET_EXHAUSTED"), _ray("negative", "BUDGET_EXHAUSTED")],
        [_step(accepted=True, step_size=0.08)],
    )
    result = classify_continuation_observation(observation, stored_interval_status="RETURNED_SET_FOUND")
    assert result["demonstrated_cause"] == CAUSE_NO_FAILURE
    assert result["closure_route"] == "plus_minus_endpoints"


def test_endpoint_meeting_within_tolerance_is_only_a_possible_cause() -> None:
    observation = _observation(
        "BUDGET_EXHAUSTED",
        [_ray("positive", "BUDGET_EXHAUSTED"), _ray("negative", "BUDGET_EXHAUSTED")],
        [_step(accepted=True, step_size=0.08)],
        endpoint_state_distance=0.05,
        endpoint_tangent_abs_dot=0.2,
    )
    result = classify_continuation_observation(observation)
    assert result["demonstrated_cause"] == CAUSE_REGULAR_BUDGET
    assert result["endpoint_meeting_implicated"] is True
    assert POSSIBLE_ENDPOINT_MEETING in result["possible_causes"]


def test_step_cap_comparison_can_demonstrate_a_missed_return() -> None:
    observation = _observation(
        "BUDGET_EXHAUSTED",
        [_ray("positive", "BUDGET_EXHAUSTED"), _ray("negative", "BUDGET_EXHAUSTED")],
        [_step(accepted=True, step_size=0.25)],
    )
    result = classify_continuation_observation(
        observation,
        bounded_replay={"kind": "step_cap", "baseline_returned": False, "comparison_returned": True},
    )
    assert result["demonstrated_cause"] == CAUSE_MISSED_RETURN


def test_regular_budget_schedules_96_then_192_only_while_arclength_advances() -> None:
    baseline = {
        "demonstrated_cause": CAUSE_REGULAR_BUDGET,
        "accepted_arclength": 1.0,
    }
    assert next_continuation_step_budget(baseline, baseline_steps=48) == 96
    still_budget = {"demonstrated_cause": CAUSE_REGULAR_BUDGET, "accepted_arclength": 2.0}
    assert (
        next_continuation_step_budget(
            baseline,
            baseline_steps=48,
            compared_steps=96,
            compared=still_budget,
        )
        == 192
    )
    stalled = {"demonstrated_cause": CAUSE_REGULAR_BUDGET, "accepted_arclength": 1.0}
    assert (
        next_continuation_step_budget(
            baseline,
            baseline_steps=48,
            compared_steps=96,
            compared=stalled,
        )
        is None
    )
    collapsed = {"demonstrated_cause": CAUSE_CORRECTOR, "accepted_arclength": 0.2}
    assert (
        next_continuation_step_budget(
            baseline,
            baseline_steps=48,
            compared_steps=96,
            compared=collapsed,
        )
        is None
    )
    assert next_continuation_step_budget(
        {"demonstrated_cause": CAUSE_CORRECTOR, "accepted_arclength": 0.0},
        baseline_steps=48,
    ) is None


_RECEIPT = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "l5_reconstruction"
    / "h13h"
    / "h13h2_continuation_diagnosis.json"
)
_CONFIG_HASH = "e4b25df91753f9861f643db3558d20790b5e69184affd3fad0034fd9428ea9c4"


def test_h13h2_receipt_records_diagnosis_without_acceptance() -> None:
    receipt = json.loads(_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "r3a_h13h2_continuation_diagnosis_v1"
    assert receipt["work_package"] == "H13H-2"
    assert receipt["diagnostic_only"] is True
    assert receipt["accepted_reconstruction"] is False
    assert receipt["source_policy_validated"] is False
    assert receipt["h12_hub_replaced"] is False
    assert receipt["natural_budget_changed"] is False
    assert receipt["production_solver_changed"] is False
    assert receipt["solver_defect_demonstrated"] is False
    assert receipt["config_hash"] == _CONFIG_HASH
    assert receipt["historical_producer"] == "historical_dirty_producer"
    assert receipt["clean_replay_disagreement_is_not_a_solver_defect"] is True
    assert receipt["baseline_steps_per_ray"] == 48
    assert set(receipt["category_counts"]) == {
        "passing_regular",
        "budget_exhausted",
        "mixed_bin",
        "raster_failing",
        "singular_or_corrector",
    }
    by_category = {item["category"]: item for item in receipt["cases"]}
    assert set(by_category) == {
        "passing_regular",
        "budget_exhausted",
        "mixed_bin",
        "singular_or_corrector",
    }
    expected = {
        "passing_regular": CAUSE_NO_FAILURE,
        "budget_exhausted": CAUSE_BIN_BLOCKED,
        "mixed_bin": CAUSE_BIN_BLOCKED,
        "singular_or_corrector": CAUSE_CORRECTOR,
    }
    for category, cause in expected.items():
        item = by_category[category]
        classification = item["baseline"]["classification"]
        assert item["baseline"]["stored_fiber_agreement"] is True
        assert item["step_count_comparisons"] == []
        assert item["step_cap_comparison"] == "not_implicated"
        assert item["unequal_ray_budget_comparison"] == "not_implicated"
        assert item["solver_defect_demonstrated"] is False
        assert classification["demonstrated_cause"] == cause
    mixed = by_category["mixed_bin"]["stored_interval_evidence"]
    assert mixed["rasterization_incomplete_count"] == 2
    assert mixed["closure_kind_counts"] == {"RETURNED_TO_SEED": 8}
    corrector = by_category["singular_or_corrector"]["baseline"]["classification"]
    assert corrector["rank_evidence"] is False
    assert corrector["accepted_step_count"] == 0
    deferred = receipt["deferred"]
    assert deferred["continuation_max_steps_per_ray"] == "not_added"
    assert deferred["h13h_source_convergence_v1"] == "not_registered"
    assert deferred["unknown_policy_rejection"] == "not_changed"
