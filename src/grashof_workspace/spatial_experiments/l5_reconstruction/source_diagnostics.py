"""Source-only H13H diagnostics.

Audit, replay, and paired-report comparison stay outside campaign acceptance.
They do not read or invent natural-family results. Replay records the
continuation seed from the deterministic construction; serialized samples are
ordered by signed arclength and are not treated as the seed.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from grashof_workspace.spatial_experiments.branch_continuation import (
    MAX_DS,
    MIN_DS,
    RETURN_STATE_TOL,
)

from .artifacts import validate_campaign_tree
from .comparison import evaluate_direct_and_source_columns, reconstruction_pass
from .direct_truth import found_configurations
from .models import (
    PointingSetMetrics,
    file_sha256,
    git_provenance,
    json_dumps_strict,
    load_campaign_config,
    resolve_stage_budgets,
)
from .positive_control import build_positive_control_arm
from .source_control import radial_normal
from .source_control_h13 import (
    _load_discovery,
    analytical_c_interval,
    choose_analytical_c_values,
    cluster_wrapped_q,
    confirmation_c_slice_spacing_rad,
    wrapped_q_distance,
)
from .source_control_h13g import (
    RASTER_H_TOLERANCE,
    continue_source_fiber_h13g,
    discover_projected_source_seeds,
    load_h13g_source_policy,
    rasterize_fiber_kinematically,
    trace_and_cover_projected_seeds,
)
from .sphere_grid import build_sphere_grid, pointing_geodesic

REPORT_SCHEMA = "r3a_h13h_source_diagnostic_report_v1"
TRACE_SCHEMA = "r3a_h13h_selected_trace_diagnostics_v1"
RASTER_SCHEMA = "r3a_h13h_selected_raster_segments_v1"
COMPARE_SCHEMA = "r3a_h13h_source_run_comparison_v1"
FIBER_ID_RE = re.compile(r"_c(\d+)_t(\d+)$")
SELECTION_ORDER = (
    "passing_regular",
    "budget_exhausted",
    "mixed_bin",
    "raster_failing",
    "singular_or_corrector",
)
SOURCE_COLUMNS = ("direct_vs_oracle", "source_vs_direct", "source_vs_oracle")
SCALAR_KEYS = (
    "missed_covered_fraction",
    "false_positive_fraction",
    "hausdorff_rad",
)
CROSS_RUN_LIMIT = 0.02
CAUSE_REGULAR_BUDGET = "REGULAR_BUDGET_EXHAUSTED"
CAUSE_CORRECTOR = "REPEATED_CORRECTOR_REJECTION"
CAUSE_SINGULAR = "GENUINE_SINGULAR_LEVEL_SET"
CAUSE_HIDDEN_RAY = "RAY_LOCAL_FAILURE_HIDDEN_BY_AGGREGATE"
CAUSE_BIN_BLOCKED = "CLOSED_TRACE_BIN_BLOCKED_BY_OTHER_STAGE"
CAUSE_MISSED_RETURN = "MISSED_RETURN_UNDER_STEP_CAP"
CAUSE_UNRESOLVED = "UNRESOLVED"
CAUSE_NO_FAILURE = "NO_CONTINUATION_FAILURE"
POSSIBLE_RETURN_SAMPLING = "RETURN_SAMPLING"
POSSIBLE_SINGULAR_WITHOUT_RANK = "SINGULAR_LABEL_WITHOUT_RANK_EVIDENCE"
POSSIBLE_ENDPOINT_MEETING = "ENDPOINT_MEETING_SENSITIVITY"
CONTINUATION_CASE_CATEGORIES = (
    "passing_regular",
    "budget_exhausted",
    "mixed_bin",
    "singular_or_corrector",
)
RASTER_UNTRACED_CLOSING = "UNTRACED_CLOSING_GAP"
RASTER_FAILED_CORRECTION = "FAILED_MIDPOINT_CORRECTION"
RASTER_DEPTH = "DEPTH_EXHAUSTED"
RASTER_NONLOCAL = "ACCEPTED_NONLOCAL_CORRECTION"
RASTER_RESIDUAL = "ACCEPTED_RESIDUAL_EXCEEDANCE"
RASTER_ACCEPTED_FAILURE = "ACCEPTED_CORRECTION_OR_DEPTH_FAILURE"
RASTER_HIDDEN = "HIDDEN_INTERIOR_EXCURSION"
RASTER_INTERVAL_COVERED = "INCOMPLETE_RASTER_LEFT_INTERVAL_COVERED"
RASTER_NO_FAILURE = "NO_RASTER_FAILURE"
RASTER_UNRESOLVED = "UNRESOLVED"
POSSIBLE_INTERIOR_UNMEASURED = "INTERIOR_EXCURSION_NOT_MEASURED"
_COVERED_RASTER_INTERVALS = frozenset({"RETURNED_SET_FOUND", "COMPONENT_COMPLETE"})
_OPEN_RASTER_RAYS = frozenset(
    {"BUDGET_EXHAUSTED", "OPEN_UNCLASSIFIED", "CORRECTOR_FAILURE", "SINGULAR"}
)
_LEVEL_SET_RANK = 4
_CLOSED_INTERVALS = frozenset({"RETURNED_SET_FOUND", "COMPONENT_COMPLETE"})
_FAILURE_RAYS = frozenset({"CORRECTOR_FAILURE", "SINGULAR"})
_OPEN_RAYS = frozenset({"BUDGET_EXHAUSTED", "OPEN_UNCLASSIFIED"})


class DiagnosticError(RuntimeError):
    """A source diagnostic input is missing, drifted, or incompatible."""


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _point_rows(value: object) -> list[Sequence[float]]:
    if not isinstance(value, list):
        return []
    rows: list[Sequence[float]] = []
    for item in value:
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes)) and len(item) >= 3:
            rows.append((float(item[0]), float(item[1]), float(item[2])))
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DiagnosticError(f"{path} is not a JSON object")
    return payload


def _probe_scope(campaign_root: Path) -> tuple[str, ...]:
    summary = _read_json(campaign_root / "source_control.json")
    raw = summary.get("probe_ids")
    if not isinstance(raw, list) or not raw:
        raise DiagnosticError("source-control summary is missing probe_ids")
    return tuple(str(item) for item in raw)


def _inventory_row(probe_id: str, record: Mapping[str, Any]) -> dict[str, Any]:
    kinds = record.get("closure_kind_counts")
    counts = kinds if isinstance(kinds, Mapping) else {}
    return {
        "probe_id": probe_id,
        "c": record.get("c"),
        "required": bool(record.get("required")),
        "parameter_interval_status": record.get("parameter_interval_status"),
        "continuation_returned": int(counts.get("closed", 0)),
        "continuation_budget_exhausted": int(record.get("budget_exhausted_count") or 0),
        "continuation_corrector_failure": int(record.get("corrector_failure_count") or 0),
        "continuation_singular": int(record.get("singular_count") or 0),
        "continuation_open": int(record.get("open_count") or 0),
        "projection_blocking_failures": int(record.get("blocking_projection_failure_count") or 0),
        "projection_diagnostic_failures": int(record.get("diagnostic_projection_failure_count") or 0),
        "candidate_cap": int(bool(record.get("candidate_budget_exhausted"))),
        "trace_cap": int(bool(record.get("trace_budget_exhausted"))),
        "seed_cap": int(bool(record.get("seed_budget_exhausted"))),
        "explained_representatives": int(record.get("explained_projected_seed_count") or 0),
        "unexplained_representatives": int(record.get("unexplained_projected_seed_count") or 0),
        "raster_incomplete_count": int(record.get("rasterization_incomplete_count") or 0),
    }


def _record_for_c(records: Sequence[Mapping[str, Any]], c: object) -> Mapping[str, Any]:
    if not isinstance(c, (int, float)):
        return {}
    for record in records:
        stored = record.get("c")
        if isinstance(stored, (int, float)) and abs(float(stored) - float(c)) <= 1e-12:
            return record
    return {}


def _mapping_items(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _branch_trace(observation: Mapping[str, Any]) -> Mapping[str, Any]:
    trace = observation.get("branch_trace")
    return trace if isinstance(trace, Mapping) else {}


def _outcome(observation: Mapping[str, Any]) -> str:
    for key in ("outcome", "stored_termination_status", "termination_status"):
        value = observation.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _ray_map(observation: Mapping[str, Any]) -> dict[str, str]:
    rays: dict[str, str] = {}
    for record in _mapping_items(_branch_trace(observation).get("ray_records")):
        direction = record.get("direction")
        termination = record.get("termination")
        if isinstance(direction, str) and isinstance(termination, str):
            rays[direction] = termination
    for direction, key in (
        ("positive", "positive_ray_termination"),
        ("negative", "negative_ray_termination"),
    ):
        value = observation.get(key)
        if direction not in rays and isinstance(value, str):
            rays[direction] = value
    return rays


def _accepted_steps(observation: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    steps = []
    for step in _mapping_items(_branch_trace(observation).get("steps")):
        if step.get("accepted") is True:
            steps.append(step)
    return steps


def _moving_steps(steps: Sequence[Mapping[str, Any]]) -> list[float]:
    sizes: list[float] = []
    for step in steps:
        size = step.get("step_size")
        if isinstance(size, (int, float)) and abs(float(size)) > 0.0:
            sizes.append(abs(float(size)))
    return sizes


def _rank_evidence(step: Mapping[str, Any]) -> bool:
    rank = step.get("rank")
    nullity = step.get("nullity")
    rank_bad = isinstance(rank, int) and not isinstance(rank, bool) and rank != _LEVEL_SET_RANK
    nullity_bad = isinstance(nullity, int) and not isinstance(nullity, bool) and nullity != 1
    return rank_bad or nullity_bad


def _rejection_counts(observation: Mapping[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for step in _mapping_items(_branch_trace(observation).get("steps")):
        reason = step.get("rejection_reason")
        if step.get("accepted") is not True and isinstance(reason, str) and reason:
            counts[reason] += 1
    for record in _mapping_items(_branch_trace(observation).get("ray_records")):
        raw = record.get("rejection_reason_counts")
        if isinstance(raw, Mapping):
            for reason, count in raw.items():
                if isinstance(count, int) and not isinstance(count, bool):
                    counts[str(reason)] += count
    return dict(counts)


def _optional_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _aggregate_names_ray(outcome: str, ray_value: str) -> bool:
    return (outcome, ray_value) in {
        ("SINGULAR_OR_CRITICAL_ENDPOINT", "SINGULAR"),
        ("CORRECTOR_FAILURE", "CORRECTOR_FAILURE"),
        ("BUDGET_EXHAUSTED", "BUDGET_EXHAUSTED"),
        ("OPEN_UNCLASSIFIED", "OPEN_UNCLASSIFIED"),
    } or outcome == ray_value


def _closure_route(observation: Mapping[str, Any], outcome: str) -> str | None:
    returned = bool(observation.get("returned")) or outcome == "RETURNED_TO_SEED"
    endpoint_closed = bool(observation.get("closed")) or outcome == "PLUS_MINUS_ENDPOINTS_CLOSED"
    trace_returned = _branch_trace(observation).get("returned") is True
    if outcome == "PLUS_MINUS_ENDPOINTS_CLOSED" or (endpoint_closed and not returned and not trace_returned):
        return "plus_minus_endpoints"
    if returned or trace_returned or outcome == "RETURNED_TO_SEED":
        return "seed_return"
    return None


def classify_continuation_observation(
    observation: Mapping[str, Any],
    *,
    stored_interval_status: str | None = None,
    bounded_replay: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify one replayed source fiber.

    ``demonstrated_cause`` is established by this trace. ``possible_causes``
    are hypotheses this trace does not establish. A step-count increase that
    later returns explains a budget; it does not demonstrate a missed return.
    A missed return requires a step-cap comparison at comparable traversal.
    """

    outcome = _outcome(observation)
    rays = _ray_map(observation)
    accepted = _accepted_steps(observation)
    sizes = _moving_steps(accepted)
    singular_steps = [
        step
        for step in _mapping_items(_branch_trace(observation).get("steps"))
        if step.get("rejection_reason") == "singular"
    ]
    rank_evidence = any(_rank_evidence(step) for step in singular_steps)
    minimum = min(sizes) if sizes else None
    maximum = max(sizes) if sizes else None
    reached_cap = maximum is not None and maximum >= 0.99 * MAX_DS
    collapsed = minimum is not None and minimum <= MIN_DS * 1.01
    route = _closure_route(observation, outcome)
    returned = route is not None
    ray_values = [value for value in rays.values() if value]
    distinct_failures = {value for value in ray_values if value in _FAILURE_RAYS or value in _OPEN_RAYS}
    failure_rays = [value for value in ray_values if value in _FAILURE_RAYS]
    hidden_failure = bool(failure_rays) and (
        len(distinct_failures) > 1
        or any(not _aggregate_names_ray(outcome, value) for value in failure_rays)
    )
    interval = stored_interval_status
    if interval is None and isinstance(observation.get("stored_interval_status"), str):
        interval = str(observation["stored_interval_status"])
    bin_blocked = interval is not None and interval not in _CLOSED_INTERVALS
    endpoint_distance = _optional_float(observation.get("endpoint_state_distance"))
    endpoint_tangent = _optional_float(observation.get("endpoint_tangent_abs_dot"))
    both_budget = bool(ray_values) and set(ray_values) == {"BUDGET_EXHAUSTED"}
    singular_label = "SINGULAR" in ray_values or outcome == "SINGULAR_OR_CRITICAL_ENDPOINT"
    corrector_label = "CORRECTOR_FAILURE" in ray_values or outcome == "CORRECTOR_FAILURE"
    endpoint_implicated = (
        both_budget
        and not returned
        and endpoint_distance is not None
        and endpoint_distance <= RETURN_STATE_TOL
    )
    possible: list[str] = []
    if reached_cap and not returned:
        possible.append(POSSIBLE_RETURN_SAMPLING)
    if endpoint_implicated:
        possible.append(POSSIBLE_ENDPOINT_MEETING)
    if singular_label and not rank_evidence:
        possible.append(POSSIBLE_SINGULAR_WITHOUT_RANK)
    step_cap_return = (
        isinstance(bounded_replay, Mapping)
        and bounded_replay.get("kind") == "step_cap"
        and bounded_replay.get("baseline_returned") is False
        and bounded_replay.get("comparison_returned") is True
    )
    if step_cap_return:
        cause = CAUSE_MISSED_RETURN
        explanation = "A lower step cap returned where the baseline cap did not."
    elif hidden_failure and any(value in _FAILURE_RAYS for value in ray_values):
        cause = CAUSE_HIDDEN_RAY
        explanation = "One ray's singular or corrector termination is not the aggregate label."
    elif returned and bin_blocked:
        cause = CAUSE_BIN_BLOCKED
        explanation = "The trace is closed, and the stored c interval is blocked by another stage."
    elif singular_label and rank_evidence:
        cause = CAUSE_SINGULAR
        explanation = "A singular rejection retains rank or nullity evidence."
    elif singular_label:
        cause = CAUSE_UNRESOLVED
        explanation = "The singular label has no retained rank or nullity evidence."
    elif corrector_label or collapsed:
        cause = CAUSE_CORRECTOR
        explanation = "Continuation ended in corrector rejection or minimum-step collapse."
    elif returned and not any(value in _FAILURE_RAYS for value in ray_values):
        cause = CAUSE_NO_FAILURE
        explanation = "The trace closed without a hidden singular or corrector ray."
    elif both_budget and sizes and not collapsed and not rank_evidence:
        cause = CAUSE_REGULAR_BUDGET
        explanation = "Both rays accepted regular steps until the step budget."
    else:
        cause = CAUSE_UNRESOLVED
        explanation = "The trace does not establish one continuation cause."
    arclength = 0.0
    arclength_known = False
    for record in _mapping_items(_branch_trace(observation).get("ray_records")):
        value = _optional_float(record.get("accepted_arclength"))
        if value is not None:
            arclength += value
            arclength_known = True
    return {
        "demonstrated_cause": cause,
        "possible_causes": sorted(set(possible)),
        "explanation": explanation,
        "closure_route": route,
        "aggregate_outcome": outcome,
        "ray_terminations": rays,
        "distinct_ray_classes": sorted(distinct_failures),
        "accepted_step_count": len(sizes),
        "minimum_accepted_step": minimum,
        "maximum_accepted_step": maximum,
        "reached_step_cap": reached_cap,
        "minimum_step_collapse": collapsed,
        "rank_evidence": rank_evidence,
        "rejection_reason_counts": _rejection_counts(observation),
        "accepted_arclength": arclength if arclength_known else None,
        "endpoint_state_distance": endpoint_distance,
        "endpoint_tangent_abs_dot": endpoint_tangent,
        "endpoint_meeting_implicated": endpoint_implicated,
        "stored_interval_status": interval,
    }


def next_continuation_step_budget(
    classification: Mapping[str, Any],
    *,
    baseline_steps: int,
    compared_steps: int | None = None,
    compared: Mapping[str, Any] | None = None,
) -> int | None:
    """Return 96 or 192 when a regular budget still needs that comparison."""

    if classification.get("demonstrated_cause") != CAUSE_REGULAR_BUDGET:
        return None
    if compared is None:
        if baseline_steps < 96:
            return 96
        if baseline_steps < 192:
            return 192
        return None
    if compared.get("demonstrated_cause") != CAUSE_REGULAR_BUDGET:
        return None
    base_arc = classification.get("accepted_arclength")
    new_arc = compared.get("accepted_arclength")
    if not isinstance(base_arc, (int, float)) or not isinstance(new_arc, (int, float)):
        return None
    if float(new_arc) <= float(base_arc):
        return None
    if compared_steps == 96:
        return 192
    return None


def _segment_span(segment: Mapping[str, Any]) -> float | None:
    endpoints = segment.get("endpoint_q")
    if not isinstance(endpoints, list) or len(endpoints) != 2:
        return None
    start, end = endpoints
    if not isinstance(start, list) or not isinstance(end, list):
        return None
    return wrapped_q_distance(tuple(float(value) for value in start), tuple(float(value) for value in end))


def _positive_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def classify_raster_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Classify one raster replay from its segment records.

    A correction that travels farther than its wrapped chord is a demonstrated
    nonlocal sample. A closing-segment failure on an open ray is an untraced
    gap. Interior excursion is demonstrated only by a recorded interior probe.
    """

    segments = [item for item in observation.get("segments") or [] if isinstance(item, Mapping)]
    outcomes = Counter(str(item.get("outcome")) for item in segments)
    closing = [item for item in segments if item.get("closing_segment") is True]
    traced = [item for item in segments if item.get("closing_segment") is not True]
    nonlocal_segments = []
    for item in segments:
        distance = _positive_float(item.get("wrapped_correction_distance_rad"))
        span = _segment_span(item)
        if item.get("outcome") == "corrected" and distance is not None and span is not None and distance > span:
            nonlocal_segments.append(item)
    probes = [item for item in observation.get("interior_probes") or [] if isinstance(item, Mapping)]
    max_segment = _positive_float(observation.get("max_segment_rad"))
    hidden = []
    for item in probes:
        excursion = _positive_float(item.get("pointing_excursion_rad"))
        if item.get("correction_ok") is False or excursion is not None and max_segment is not None and excursion > max_segment:
            hidden.append(item)
    complete = observation.get("rasterization_complete") is True
    position = _positive_float(observation.get("max_position_residual_m"))
    scalar = _positive_float(observation.get("max_h_residual"))
    position_tol = _positive_float(observation.get("position_tolerance_m"))
    scalar_tol = _positive_float(observation.get("h_tolerance"))
    residual_exceeded = (
        position is not None
        and position_tol is not None
        and scalar is not None
        and scalar_tol is not None
        and (position > position_tol or scalar > scalar_tol)
    )
    failure_count = observation.get("correction_failure_count")
    depth_flag = observation.get("depth_budget_exhausted") is True
    accepted_failure = complete and (
        outcomes["failed_correction"] > 0
        or outcomes["depth_exhausted"] > 0
        or (isinstance(failure_count, int) and failure_count > 0)
        or depth_flag
    )
    rays = (
        observation.get("positive_ray_termination"),
        observation.get("negative_ray_termination"),
    )
    open_ray = any(isinstance(ray, str) and ray in _OPEN_RASTER_RAYS for ray in rays)
    closing_failures = [
        item for item in closing if item.get("outcome") in {"failed_correction", "depth_exhausted"}
    ]
    traced_failures = [
        item for item in traced if item.get("outcome") in {"failed_correction", "depth_exhausted"}
    ]
    interval = observation.get("stored_interval_status")
    required = observation.get("interval_required") is True
    incomplete = complete is False
    interval_blocked = bool(
        incomplete and required and isinstance(interval, str) and interval not in _COVERED_RASTER_INTERVALS
    )
    interval_left_covered = bool(
        incomplete and required and isinstance(interval, str) and interval in _COVERED_RASTER_INTERVALS
    )
    possible: list[str] = []
    short_segments = [item for item in segments if item.get("outcome") == "within_declared_gap"]
    if short_segments and not probes:
        possible.append(POSSIBLE_INTERIOR_UNMEASURED)
    if complete and residual_exceeded:
        cause = RASTER_RESIDUAL
        explanation = "Raster completion was recorded with a residual above the declared tolerance."
    elif accepted_failure:
        cause = RASTER_ACCEPTED_FAILURE
        explanation = "A correction failure or depth exhaustion was retained on a completed raster."
    elif nonlocal_segments:
        cause = RASTER_NONLOCAL
        explanation = "A corrected midpoint moved farther than its wrapped endpoint chord."
    elif hidden:
        cause = RASTER_HIDDEN
        explanation = "An accepted short segment has an interior sample outside the declared gap."
    elif interval_left_covered:
        cause = RASTER_INTERVAL_COVERED
        explanation = "Incomplete rasterization left a required interval covered."
    elif closing_failures and not traced_failures and open_ray:
        cause = RASTER_UNTRACED_CLOSING
        explanation = (
            "The closing chord joins an open ray to the seed. "
            "The local section correction does not cross that untraced gap."
        )
    elif outcomes["failed_correction"] > 0 and not complete:
        cause = RASTER_FAILED_CORRECTION
        explanation = "Midpoint correction failed and the raster remains incomplete."
    elif (outcomes["depth_exhausted"] > 0 or depth_flag) and not complete:
        cause = RASTER_DEPTH
        explanation = "Refinement reached its depth budget before the declared gap."
    elif complete and not residual_exceeded and not hidden and not nonlocal_segments:
        cause = RASTER_NO_FAILURE
        explanation = "The raster meets the declared gap, correction, depth, and residual checks."
    else:
        cause = RASTER_UNRESOLVED
        explanation = "The raster records do not establish a single cause."
    return {
        "demonstrated_cause": cause,
        "possible_causes": possible,
        "explanation": explanation,
        "observed_outcomes": dict(outcomes),
        "closing_segment_outcomes": dict(Counter(str(item.get("outcome")) for item in closing)),
        "traced_segment_failures": len(traced_failures),
        "closing_segment_failures": len(closing_failures),
        "nonlocal_correction_count": len(nonlocal_segments),
        "hidden_interior_count": len(hidden),
        "open_ray": open_ray,
        "interval_blocked": interval_blocked,
        "interval_left_covered": interval_left_covered,
        "stored_interval_status": interval,
    }


def _categories(fiber: Mapping[str, Any], record: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    termination = str(fiber.get("termination_status"))
    raster_complete = fiber.get("rasterization_complete")
    if termination in {"RETURNED_TO_SEED", "PLUS_MINUS_ENDPOINTS_CLOSED"} and raster_complete is True:
        found.add("passing_regular")
    if termination == "BUDGET_EXHAUSTED" or fiber.get("budget_exhausted") is True:
        found.add("budget_exhausted")
    if str(record.get("parameter_interval_status")) == "MIXED_UNRESOLVED":
        found.add("mixed_bin")
    if raster_complete is False:
        found.add("raster_failing")
    if termination in {"SINGULAR_OR_CRITICAL_ENDPOINT", "CORRECTOR_FAILURE"}:
        found.add("singular_or_corrector")
    return found


def select_diagnostic_cases(
    probes: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, int]]:
    """Pick one deterministic case for each category that is actually present."""

    ranked: list[tuple[tuple[int, float, str], Mapping[str, Any], set[str]]] = []
    counts: Counter[str] = Counter()
    for probe_index, probe in enumerate(probes):
        records = [item for item in probe.get("c_records") or [] if isinstance(item, Mapping)]
        fibers = [item for item in probe.get("fibers") or [] if isinstance(item, Mapping)]
        for fiber in fibers:
            record = _record_for_c(records, fiber.get("c"))
            categories = _categories(fiber, record)
            counts.update(categories)
            c_value = fiber.get("c")
            c_sort = float(c_value) if isinstance(c_value, (int, float)) else 0.0
            ranked.append(((probe_index, c_sort, str(fiber.get("fiber_id"))), fiber, categories))
    ranked.sort(key=lambda item: item[0])
    selected: dict[str, Any] = {}
    chosen_ids: set[str] = set()
    for category in SELECTION_ORDER:
        if category == "singular_or_corrector" and counts[category] == 0:
            continue
        fallback: Mapping[str, Any] | None = None
        distinct: Mapping[str, Any] | None = None
        for _key, fiber, categories in ranked:
            if category not in categories:
                continue
            if fallback is None:
                fallback = fiber
            if str(fiber.get("fiber_id")) not in chosen_ids:
                distinct = fiber
                break
        chosen = distinct if distinct is not None else fallback
        if chosen is None:
            continue
        selected[category] = chosen
        chosen_ids.add(str(chosen.get("fiber_id")))
    return selected, {category: int(counts[category]) for category in SELECTION_ORDER}


def _case_identity(
    *,
    campaign_root: Path,
    config_path: Path,
    mode: str,
    probe_id: str,
    fiber: Mapping[str, Any],
    category: str,
    config_hash: str | None = None,
    source_commit: str | None = None,
) -> dict[str, Any]:
    fiber_id = str(fiber.get("fiber_id"))
    match = FIBER_ID_RE.search(fiber_id)
    if match is None:
        raise DiagnosticError(f"fiber id {fiber_id} has no deterministic c/trace index")
    return {
        "campaign_root": campaign_root.as_posix(),
        "config": config_path.as_posix(),
        "mode": mode,
        "config_hash": config_hash,
        "source_commit": source_commit,
        "probe_id": probe_id,
        "category": category,
        "c": fiber.get("c"),
        "fiber_id": fiber_id,
        "bin_index": int(match.group(1)),
        "trace_index": int(match.group(2)),
        "trace_cover_seed": None,
        "seed_status": "requires_replay",
        "stored_termination_status": fiber.get("termination_status"),
        "stored_positive_ray_termination": fiber.get("positive_ray_termination"),
        "stored_negative_ray_termination": fiber.get("negative_ray_termination"),
        "stored_positive_accepted_steps": fiber.get("positive_accepted_steps"),
        "stored_negative_accepted_steps": fiber.get("negative_accepted_steps"),
        "stored_rasterization_complete": fiber.get("rasterization_complete"),
        "stored_rasterization_failure_count": fiber.get("rasterization_failure_count"),
        "branch_trace": None,
    }


def select_stored_continuation_cases(
    *,
    campaign_root: Path,
    config_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Select continuation cases from stored fibers without recomputing metrics."""

    config = load_campaign_config(config_path)
    summary = _read_json(campaign_root / "source_control.json")
    if summary.get("config_hash") != config.config_hash:
        raise DiagnosticError("source-control config hash does not match the supplied config")
    mode = str(summary.get("mode") or "")
    probe_ids = _probe_scope(campaign_root)
    probes: list[dict[str, Any]] = []
    for probe_id in probe_ids:
        blob = _read_json(campaign_root / probe_id / "source_control.json")
        probes.append(
            {
                "probe_id": probe_id,
                "c_records": [item for item in blob.get("c_records") or [] if isinstance(item, Mapping)],
                "fibers": [item for item in blob.get("fibers") or [] if isinstance(item, Mapping)],
            }
        )
    selected, counts = select_diagnostic_cases(probes)
    git_blob = summary.get("git")
    source_commit = str(git_blob.get("git_commit")) if isinstance(git_blob, Mapping) else None
    cases: list[dict[str, Any]] = []
    for category in CONTINUATION_CASE_CATEGORIES:
        fiber = selected.get(category)
        if not isinstance(fiber, Mapping):
            continue
        probe_id = str(fiber.get("fiber_id")).rsplit("_c", 1)[0]
        matched = next((probe for probe in probes if probe["probe_id"] == probe_id), None)
        raw_records = matched["c_records"] if isinstance(matched, Mapping) else []
        records = [item for item in raw_records if isinstance(item, Mapping)]
        record = _record_for_c(records, fiber.get("c"))
        case = _case_identity(
            campaign_root=campaign_root,
            config_path=config_path,
            mode=mode,
            probe_id=probe_id,
            fiber=fiber,
            category=category,
            config_hash=config.config_hash,
            source_commit=source_commit,
        )
        case["stored_interval_status"] = record.get("parameter_interval_status")
        kinds = record.get("closure_kind_counts")
        case["stored_interval_evidence"] = {
            "required": record.get("required"),
            "rasterization_incomplete_count": record.get("rasterization_incomplete_count"),
            "blocking_projection_failure_count": record.get("blocking_projection_failure_count"),
            "diagnostic_projection_failure_count": record.get("diagnostic_projection_failure_count"),
            "budget_exhausted_count": record.get("budget_exhausted_count"),
            "corrector_failure_count": record.get("corrector_failure_count"),
            "closure_kind_counts": dict(kinds) if isinstance(kinds, Mapping) else {},
        }
        cases.append(case)
    return cases, counts


def _interval_evidence(record: Mapping[str, Any]) -> dict[str, Any]:
    kinds = record.get("closure_kind_counts")
    return {
        "required": record.get("required"),
        "rasterization_incomplete_count": record.get("rasterization_incomplete_count"),
        "blocking_projection_failure_count": record.get("blocking_projection_failure_count"),
        "diagnostic_projection_failure_count": record.get("diagnostic_projection_failure_count"),
        "budget_exhausted_count": record.get("budget_exhausted_count"),
        "corrector_failure_count": record.get("corrector_failure_count"),
        "closure_kind_counts": dict(kinds) if isinstance(kinds, Mapping) else {},
    }


def _endpoint_gap(fiber: Mapping[str, Any]) -> float | None:
    samples = fiber.get("pointing_samples")
    if not isinstance(samples, list) or len(samples) < 2:
        return None
    start, end = samples[0], samples[-1]
    if not isinstance(start, list) or not isinstance(end, list):
        return None
    start_xyz = tuple(float(value) for value in start)
    end_xyz = tuple(float(value) for value in end)
    if len(start_xyz) != 3 or len(end_xyz) != 3:
        return None
    return pointing_geodesic(
        (start_xyz[0], start_xyz[1], start_xyz[2]),
        (end_xyz[0], end_xyz[1], end_xyz[2]),
    )


def select_stored_raster_cases(
    *,
    campaign_root: Path,
    config_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Select raster cases from stored fibers without recomputing metrics."""

    config = load_campaign_config(config_path)
    summary = _read_json(campaign_root / "source_control.json")
    if summary.get("config_hash") != config.config_hash:
        raise DiagnosticError("source-control config hash does not match the supplied config")
    mode = str(summary.get("mode") or "")
    probes: list[dict[str, Any]] = []
    for probe_id in _probe_scope(campaign_root):
        blob = _read_json(campaign_root / probe_id / "source_control.json")
        probes.append(
            {
                "probe_id": probe_id,
                "c_records": [item for item in blob.get("c_records") or [] if isinstance(item, Mapping)],
                "fibers": [item for item in blob.get("fibers") or [] if isinstance(item, Mapping)],
            }
        )
    selected, counts = select_diagnostic_cases(probes)
    git_blob = summary.get("git")
    source_commit = str(git_blob.get("git_commit")) if isinstance(git_blob, Mapping) else None
    chosen: list[tuple[str, str, Mapping[str, Any]]] = []
    passing = selected.get("passing_regular")
    failing = selected.get("raster_failing")
    if isinstance(passing, Mapping):
        chosen.append(("closing_control", str(passing.get("fiber_id")).rsplit("_c", 1)[0], passing))
    if isinstance(failing, Mapping):
        chosen.append(("raster_failing", str(failing.get("fiber_id")).rsplit("_c", 1)[0], failing))
    seen = {str(fiber.get("fiber_id")) for _role, _probe, fiber in chosen}
    for probe in probes:
        for fiber in probe["fibers"]:
            if fiber.get("rasterization_budget_exhausted") is True and str(fiber.get("fiber_id")) not in seen:
                chosen.append(("depth_exhausted_closing", str(probe["probe_id"]), fiber))
                seen.add(str(fiber.get("fiber_id")))
                break
        else:
            continue
        break
    for probe in probes:
        for fiber in probe["fibers"]:
            rays = (fiber.get("positive_ray_termination"), fiber.get("negative_ray_termination"))
            open_ray = any(isinstance(ray, str) and ray in _OPEN_RASTER_RAYS for ray in rays)
            gap = _endpoint_gap(fiber)
            if (
                fiber.get("returned") is True
                and open_ray
                and fiber.get("rasterization_complete") is True
                and gap is not None
                and gap > 0.2
                and str(fiber.get("fiber_id")) not in seen
            ):
                chosen.append(("open_ray_completed", str(probe["probe_id"]), fiber))
                seen.add(str(fiber.get("fiber_id")))
                break
        else:
            continue
        break
    cases: list[dict[str, Any]] = []
    for category, probe_id, fiber in chosen:
        matched = next(probe for probe in probes if probe["probe_id"] == probe_id)
        records = [item for item in matched["c_records"] if isinstance(item, Mapping)]
        record = _record_for_c(records, fiber.get("c"))
        case = _case_identity(
            campaign_root=campaign_root,
            config_path=config_path,
            mode=mode,
            probe_id=probe_id,
            fiber=fiber,
            category=category,
            config_hash=config.config_hash,
            source_commit=source_commit,
        )
        case["stored_interval_status"] = record.get("parameter_interval_status")
        case["stored_interval_evidence"] = _interval_evidence(record)
        case["stored_endpoint_gap_rad"] = _endpoint_gap(fiber)
        cases.append(case)
    return cases, counts


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = list(rows[0]) if rows else ["probe_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mask_payload(columns: Any) -> dict[str, Any]:
    return {
        "fine_oracle_labels": list(columns.fine_oracle_labels),
        "coarse_oracle_labels": list(columns.coarse_oracle_labels),
        "fine_direct_labels": list(columns.fine_direct_labels),
        "coarse_direct_labels": list(columns.coarse_direct_labels),
        "fine_source_hits": [bool(item) for item in columns.fine_source_hits],
        "coarse_source_hits": [bool(item) for item in columns.coarse_source_hits],
        "fine_direct_hits": [bool(item) for item in columns.fine_direct_hits],
    }


def _parity(stored: Mapping[str, Any] | None, fresh: Mapping[str, Any]) -> dict[str, Any]:
    if stored is None:
        return {"state": "ABSENT", "matches": None}
    mismatches = [
        name
        for name in SOURCE_COLUMNS
        if stored.get(name) != fresh.get(name)
    ]
    return {"state": "MATCH" if not mismatches else "MISMATCH", "matches": not mismatches, "columns": mismatches}


def _sphere_plot(path: Path, raw: Sequence[Sequence[float]], raster: Sequence[Sequence[float]]) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg", force=False)
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    figure = plt.figure(figsize=(5, 5))
    axis = figure.add_subplot(111, projection="3d")
    if raw:
        axis.scatter([item[0] for item in raw], [item[1] for item in raw], [item[2] for item in raw], s=8, label="raw FK")
    if raster:
        axis.scatter(
            [item[0] for item in raster],
            [item[1] for item in raster],
            [item[2] for item in raster],
            s=6,
            label="raster",
        )
    axis.set_title("Stored pointing samples")
    axis.legend(loc="upper left")
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)
    return True


def _write_review(path: Path, cases: Sequence[Mapping[str, Any]], plot_names: Mapping[str, str]) -> None:
    rows = []
    for case in cases:
        plot = plot_names.get(str(case["category"]), "")
        image = f"<img src='{plot}' alt='{case['category']}'>" if plot else "<p>No stored pointing plot.</p>"
        rows.append(
            "<section>"
            f"<h2>{case['category']}</h2>"
            f"<p>probe {case['probe_id']} c {case['c']} fiber {case['fiber_id']}</p>"
            f"<p>stored termination {case['stored_termination_status']}; "
            f"rays {case['stored_positive_ray_termination']} / {case['stored_negative_ray_termination']}</p>"
            "<p>Per-step branch history is absent from the stored source record. "
            "Replay recovers the continuation seed and BranchTrace.</p>"
            f"{image}</section>"
        )
    path.write_text(
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>H13H source diagnostic review</title></head>"
        "<body><h1>H13H source diagnostic review</h1>"
        "<p>Diagnostic only. This page does not accept a reconstruction.</p>"
        + "".join(rows)
        + "</body></html>\n",
        encoding="utf-8",
    )


def audit_source_campaign(
    *,
    config_path: Path,
    campaign_root: Path,
    outdir: Path,
) -> dict[str, Any]:
    """Audit stored direct and source artifacts. Does not run continuation."""

    config = load_campaign_config(config_path)
    probe_ids = _probe_scope(campaign_root)
    summary = _read_json(campaign_root / "source_control.json")
    mode = str(summary.get("mode") or "")
    if summary.get("config_hash") != config.config_hash:
        raise DiagnosticError("source-control config hash does not match the supplied config")
    validate_campaign_tree(
        campaign_root,
        probe_ids,
        expected_config_hash=config.config_hash,
        expected_mode=mode,
        require_all_stages=False,
    )
    for name in ("manifest.json", "fixture.json", "truth.json", "source_control.json"):
        if not (campaign_root / name).is_file():
            raise DiagnosticError(f"missing {name}")
    outdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    probe_reports: list[dict[str, Any]] = []
    selection_input: list[dict[str, Any]] = []
    input_hashes: dict[str, str] = {}
    for probe_id in probe_ids:
        for relative in (
            f"{probe_id}/fixture.json",
            f"{probe_id}/direct_truth.json",
            f"{probe_id}/source_control.json",
        ):
            input_hashes[relative] = file_sha256(campaign_root / relative)
        source_blob = _read_json(campaign_root / probe_id / "source_control.json")
        truth_blob = _read_json(campaign_root / probe_id / "direct_truth.json")
        probe = config.probe(probe_id)
        columns = evaluate_direct_and_source_columns(
            config=config,
            probe=probe,
            mode=mode,
            source_blob=source_blob,
            truth_blob=truth_blob,
        )
        fresh = {name: getattr(columns, name).to_json_dict() for name in SOURCE_COLUMNS}
        comparison_path = campaign_root / probe_id / "comparison.json"
        stored = _read_json(comparison_path) if comparison_path.is_file() else None
        parity = _parity(stored, fresh)
        if parity["matches"] is False:
            raise DiagnosticError(
                f"{probe_id} source diagnostic metrics differ from the stored comparison: {parity['columns']}"
            )
        records = [item for item in source_blob.get("c_records") or [] if isinstance(item, Mapping)]
        rows.extend(_inventory_row(probe_id, record) for record in records)
        blockers = [
            {"c": record.get("c"), "status": record.get("parameter_interval_status")}
            for record in records
            if record.get("required") is True
            and record.get("parameter_interval_status") not in {"RETURNED_SET_FOUND", "COMPONENT_COMPLETE"}
        ]
        probe_reports.append(
            {
                "probe_id": probe_id,
                "direct_complete": columns.direct_complete,
                "oracle_complete": columns.oracle_complete,
                "fine_level": columns.fine_level,
                "coarse_level": columns.coarse_level,
                "unresolved_c_intervals": [list(item) for item in columns.unresolved_c_intervals],
                "interval_blockers": blockers,
                "columns": fresh,
                "masks": _mask_payload(columns),
                "parity": parity,
            }
        )
        selection_input.append(
            {
                "probe_id": probe_id,
                "c_records": records,
                "fibers": [item for item in source_blob.get("fibers") or [] if isinstance(item, Mapping)],
            }
        )
    selected, category_counts = select_diagnostic_cases(selection_input)
    git_blob = summary.get("git")
    source_commit = str(git_blob.get("git_commit")) if isinstance(git_blob, Mapping) else None
    cases: list[dict[str, Any]] = []
    plot_names: dict[str, str] = {}
    case_dir = outdir / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for category in SELECTION_ORDER:
        fiber = selected.get(category)
        if not isinstance(fiber, Mapping):
            continue
        probe_id = str(fiber["fiber_id"]).rsplit("_c", 1)[0]
        case = _case_identity(
            campaign_root=campaign_root,
            config_path=config_path,
            mode=mode,
            probe_id=probe_id,
            fiber=fiber,
            category=category,
            config_hash=config.config_hash,
            source_commit=source_commit,
        )
        cases.append(case)
        (case_dir / f"{category}.json").write_text(json_dumps_strict(case), encoding="utf-8")
        raw_samples = _point_rows(fiber.get("pointing_samples"))
        raster_samples = _point_rows(fiber.get("rasterized_pointing_samples"))
        plot_name = f"{category}_pointing.png"
        if _sphere_plot(outdir / plot_name, raw_samples, raster_samples):
            plot_names[category] = plot_name
    report = {
        "schema_version": REPORT_SCHEMA,
        "diagnostic_only": True,
        "accepted_reconstruction": False,
        "natural_family_used": False,
        "config_path": config_path.as_posix(),
        "config_hash": config.config_hash,
        "campaign_root": campaign_root.as_posix(),
        "mode": mode,
        "probe_ids": list(probe_ids),
        "producer_git": summary.get("git"),
        "inspection_git": git_provenance(campaign_root),
        "input_hashes": input_hashes,
        "category_counts": category_counts,
        "probes": probe_reports,
    }
    _write_csv(outdir / "source_failure_inventory.csv", rows)
    (outdir / "source_diagnostic_report.json").write_text(json_dumps_strict(report), encoding="utf-8")
    trace_doc = {
        "schema_version": TRACE_SCHEMA,
        "seed_rule": "continuation seed comes from deterministic replay, not the first serialized sample",
        "cases": cases,
    }
    raster_doc = {
        "schema_version": RASTER_SCHEMA,
        "segment_evidence": "requires_replay",
        "cases": [
            {
                "category": case["category"],
                "fiber_id": case["fiber_id"],
                "rasterization_complete": case["stored_rasterization_complete"],
                "rasterization_failure_count": case["stored_rasterization_failure_count"],
                "segments": None,
            }
            for case in cases
        ],
    }
    (outdir / "selected_trace_diagnostics.json").write_text(json_dumps_strict(trace_doc), encoding="utf-8")
    (outdir / "selected_raster_segments.json").write_text(json_dumps_strict(raster_doc), encoding="utf-8")
    _write_review(outdir / "source_diagnostic_review.html", cases, plot_names)
    return report


def replay_selected_case(
    *,
    case_path: Path,
    outdir: Path,
    steps_per_ray: int | None = None,
    include_raster: bool = True,
) -> dict[str, Any]:
    """Replay one selected fiber and record its seed, BranchTrace, and raster segments.

    Tracing stops at the selected trace index. Later cover traces do not change
    that fiber. Raster recording stays on unless a continuation-only caller
    passes ``include_raster=False``.
    """

    case = _read_json(case_path)
    config = load_campaign_config(Path(str(case["config"])))
    campaign_root = Path(str(case["campaign_root"]))
    mode = str(case["mode"])
    probe = config.probe(str(case["probe_id"]))
    arm = build_positive_control_arm(config.geometry)
    policy = load_h13g_source_policy(config, mode)
    budgets = resolve_stage_budgets(config, mode)
    truth = _read_json(campaign_root / probe.probe_id / "direct_truth.json")
    discovery = _load_discovery(truth["discovery"])
    interval = analytical_c_interval(arm, probe)
    spacing = confirmation_c_slice_spacing_rad(
        budgets.confirmation_icosphere_level,
        policy.c_slice_max_angular_spacing_cell_fraction,
    )
    c_values = choose_analytical_c_values(
        interval,
        budgets.source_c_value_count,
        max_angular_spacing_rad=spacing,
    )
    bin_index = int(case["bin_index"])
    if bin_index < 0 or bin_index >= len(c_values):
        raise DiagnosticError(f"bin index {bin_index} is outside the deterministic c schedule")
    c_value = float(c_values[bin_index])
    stored_c = case.get("c")
    if not isinstance(stored_c, (int, float)) or abs(float(stored_c) - c_value) > 1e-8:
        raise DiagnosticError("case c does not match the deterministic c schedule")
    n = radial_normal(probe.p_star)
    configs = cluster_wrapped_q(
        found_configurations(discovery),
        tol=policy.discovery_q_precluster_tol_rad,
    )
    projection = discover_projected_source_seeds(arm, probe, n, c_value, configs, policy=policy)
    observations: list[Mapping[str, Any]] = []
    if steps_per_ray is not None:
        steps = int(steps_per_ray)
    elif policy.continuation_max_steps_per_ray is not None:
        steps = policy.continuation_max_steps_per_ray
    else:
        steps = budgets.continuation_steps
    target_index = int(case["trace_index"])

    def trace_builder(seed: tuple[float, ...], trace_index: int) -> Any:
        observer = observations.append if trace_index == target_index else None
        return continue_source_fiber_h13g(
            arm,
            probe,
            n,
            c_value,
            seed,
            fiber_id=f"{probe.probe_id}_c{bin_index}_t{trace_index}",
            max_steps=steps,
            policy=policy,
            trace_observer=observer,
        )

    cover = trace_and_cover_projected_seeds(
        projection.projected_seed_clusters,
        max_traces=target_index + 1,
        cover_tol_rad=policy.trace_cover_q_tol_rad,
        trace_builder=trace_builder,
    )
    matched = [fiber for fiber in cover.fibers if fiber.fiber_id == case["fiber_id"]]
    if len(matched) != 1 or len(observations) != 1:
        raise DiagnosticError(f"replay did not isolate {case['fiber_id']}")
    fiber = matched[0]
    observation = dict(observations[0])
    seed = observation.get("trace_cover_seed")
    continuation_seed = observation.get("continuation_seed")
    samples = fiber.q_samples
    if isinstance(seed, list) and samples:
        first = list(samples[0])
        observation["first_serialized_sample_is_seed"] = first == seed or first == continuation_seed
    segments: list[dict[str, Any]] = []
    raster_complete: bool | None = None
    raster_failures: int | None = None
    raster_budget: bool | None = None
    max_segment_rad: float | None = None
    max_position_residual_m: float | None = None
    max_h_residual: float | None = None
    if include_raster:

        def _record_segment(payload: Mapping[str, Any]) -> None:
            segments.append(dict(payload))

        grid = build_sphere_grid(budgets.confirmation_icosphere_level)
        max_segment_rad = policy.curve_segment_fraction * grid.max_cell_diameter_rad
        raster = rasterize_fiber_kinematically(
            arm,
            probe,
            n,
            fiber,
            max_segment_rad=max_segment_rad,
            max_depth=policy.kinematic_refinement_max_depth,
            segment_observer=_record_segment,
            position_tolerance_m=config.tolerances.position_residual_m,
            h_tolerance=RASTER_H_TOLERANCE,
        )
        raster_complete = raster.complete
        raster_failures = raster.correction_failure_count
        raster_budget = raster.depth_budget_exhausted
        max_position_residual_m = raster.max_position_residual_m
        max_h_residual = raster.max_h_residual
    stored_match = None
    if steps_per_ray is None:
        stored_match = (
            fiber.termination_status == case.get("stored_termination_status")
            and fiber.positive_accepted_steps == case.get("stored_positive_accepted_steps")
            and fiber.negative_accepted_steps == case.get("stored_negative_accepted_steps")
        )
        if include_raster:
            stored_match = stored_match and raster_complete == case.get("stored_rasterization_complete")
    outdir.mkdir(parents=True, exist_ok=True)
    trace_doc = {
        "schema_version": TRACE_SCHEMA,
        "diagnostic_overrides": {"steps_per_ray": steps_per_ray, "include_raster": include_raster},
        "baseline_steps_per_ray": steps_per_ray is None,
        "stored_fiber_agreement": stored_match,
        "case": {**case, **observation, "branch_trace": observation.get("branch_trace")},
    }
    raster_doc = {
        "schema_version": RASTER_SCHEMA,
        "fiber_id": fiber.fiber_id,
        "segment_evidence": "recorded" if include_raster else "not_run",
        "rasterization_complete": raster_complete,
        "correction_failure_count": raster_failures,
        "depth_budget_exhausted": raster_budget,
        "max_segment_rad": max_segment_rad,
        "max_position_residual_m": max_position_residual_m,
        "max_h_residual": max_h_residual,
        "position_tolerance_m": config.tolerances.position_residual_m,
        "h_tolerance": RASTER_H_TOLERANCE,
        "segments": segments if include_raster else None,
    }
    (outdir / "selected_trace_diagnostics.json").write_text(json_dumps_strict(trace_doc), encoding="utf-8")
    (outdir / "selected_raster_segments.json").write_text(json_dumps_strict(raster_doc), encoding="utf-8")
    return trace_doc


def _scalar(blob: Mapping[str, Any], grid: str, key: str) -> tuple[str, float | None]:
    node = blob.get(grid)
    if not isinstance(node, Mapping):
        node = blob
    state = str(node.get(f"{key}_state") or "")
    value = node.get(key)
    if state == "NOT_APPLICABLE":
        return state, None
    if state != "VALUE" or not isinstance(value, (int, float)):
        return state or "MISSING", None
    return state, float(value)


def _normalized_hausdorff(blob: Mapping[str, Any], grid: str) -> tuple[str, float | None]:
    state, value = _scalar(blob, grid, "hausdorff_rad")
    node = blob.get(grid)
    diameter_node = node if isinstance(node, Mapping) else blob
    diameter = diameter_node.get("max_cell_diameter_rad")
    if state != "VALUE" or value is None or not isinstance(diameter, (int, float)) or diameter == 0:
        return state, None
    return state, value / float(diameter)


def _occupancy_delta(left: Sequence[bool], right: Sequence[bool], labels: Sequence[str]) -> dict[str, Any]:
    if not (len(left) == len(right) == len(labels)):
        raise DiagnosticError("occupancy masks and reference labels have different lengths")
    strict = [index for index, label in enumerate(labels) if label == "STRICT_COVERED"]
    if not strict:
        return {"state": "UNEVALUABLE", "value": None, "reason": "empty strict covered set"}
    changed = [index for index in strict if bool(left[index]) != bool(right[index])]
    return {
        "state": "VALUE",
        "value": len(changed) / len(strict),
        "changed_count": len(changed),
        "strict_count": len(strict),
        "changed_indices": changed,
    }


_COVERED_INTERVALS = frozenset({"RETURNED_SET_FOUND", "COMPONENT_COMPLETE"})


def evaluate_source_run_level_gates(
    *,
    config: Any,
    probe_report: Mapping[str, Any],
    source_blob: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply Section 3.1 source gates to one audited probe."""

    records = [item for item in source_blob.get("c_records") or [] if isinstance(item, Mapping)]
    fibers = [item for item in source_blob.get("fibers") or [] if isinstance(item, Mapping)]
    interval_blockers = [
        {
            "c": record.get("c"),
            "status": record.get("parameter_interval_status"),
            "rasterization_incomplete_count": record.get("rasterization_incomplete_count"),
            "budget_exhausted_count": record.get("budget_exhausted_count"),
            "candidate_budget_exhausted": record.get("candidate_budget_exhausted"),
            "trace_budget_exhausted": record.get("trace_budget_exhausted"),
            "unexplained_projected_seed_count": record.get("unexplained_projected_seed_count"),
        }
        for record in records
        if record.get("required") is True
        and str(record.get("parameter_interval_status")) not in _COVERED_INTERVALS
    ]
    required_raster_failures = [
        {
            "fiber_id": fiber.get("fiber_id"),
            "c": fiber.get("c"),
            "rasterization_complete": fiber.get("rasterization_complete"),
            "rasterization_budget_exhausted": fiber.get("rasterization_budget_exhausted"),
            "rasterization_failure_count": fiber.get("rasterization_failure_count"),
            "termination_status": fiber.get("termination_status"),
            "positive_ray_termination": fiber.get("positive_ray_termination"),
            "negative_ray_termination": fiber.get("negative_ray_termination"),
        }
        for fiber in fibers
        if fiber.get("rasterization_complete") is False
        and any(
            abs(float(fiber["c"]) - float(record["c"])) <= 1e-12
            for record in records
            if record.get("required") is True and isinstance(fiber.get("c"), (int, float)) and isinstance(record.get("c"), (int, float))
        )
    ]
    cap_flags = [
        {
            "c": record.get("c"),
            "candidate_budget_exhausted": record.get("candidate_budget_exhausted"),
            "trace_budget_exhausted": record.get("trace_budget_exhausted"),
            "unexplained_projected_seed_count": record.get("unexplained_projected_seed_count"),
        }
        for record in records
        if record.get("required") is True
        and (
            record.get("candidate_budget_exhausted") is True
            or record.get("trace_budget_exhausted") is True
            or (
                isinstance(record.get("unexplained_projected_seed_count"), int)
                and int(record["unexplained_projected_seed_count"]) > 0
            )
        )
    ]
    columns = _as_mapping(probe_report.get("columns"))
    metric_results: dict[str, Any] = {}
    metric_ok = True
    for name in ("direct_vs_oracle", "source_vs_direct", "source_vs_oracle"):
        blob = columns.get(name)
        if not isinstance(blob, Mapping):
            metric_results[name] = {"present": False, "passed": False}
            metric_ok = False
            continue
        metrics = PointingSetMetrics.from_json_dict(blob)
        passed = reconstruction_pass(metrics, config)
        metric_results[name] = {
            "present": True,
            "passed": passed,
            "missed_covered_fraction": metrics.missed_covered_fraction,
            "false_positive_fraction": metrics.false_positive_fraction,
            "hausdorff_rad": metrics.hausdorff_rad,
            "refinement_delta": metrics.refinement_delta,
        }
        if name != "direct_vs_oracle" and not passed:
            metric_ok = False
    direct_ok = metric_results.get("direct_vs_oracle", {}).get("passed") is True
    if not direct_ok:
        metric_ok = False
    open_ray_incomplete = any(
        item.get("positive_ray_termination") in _OPEN_RASTER_RAYS
        or item.get("negative_ray_termination") in _OPEN_RASTER_RAYS
        for item in required_raster_failures
    )
    budget_blocker = any(
        str(item.get("status")) == "BUDGET_EXHAUSTED" or int(item.get("budget_exhausted_count") or 0) > 0
        for item in interval_blockers
    )
    passed = (
        metric_ok
        and not interval_blockers
        and not required_raster_failures
        and not cap_flags
    )
    return {
        "probe_id": probe_report.get("probe_id"),
        "passed": passed,
        "direct_complete": probe_report.get("direct_complete"),
        "metric_gates": metric_results,
        "interval_blockers": interval_blockers,
        "required_raster_failures": required_raster_failures,
        "cap_flags": cap_flags,
        "implicates_continuation_effort": bool(budget_blocker or open_ray_incomplete),
        "implicates_spacing": False,
        "implicates_curve_resolution": False,
        "implicates_discovery_cap": bool(cap_flags),
    }


def compare_source_reports(
    *,
    left_path: Path,
    right_path: Path,
    outdir: Path,
) -> dict[str, Any]:
    """Compare two source diagnostic reports on fixed grids."""

    left = _read_json(left_path)
    right = _read_json(right_path)
    problems: list[str] = []
    if left.get("schema_version") != REPORT_SCHEMA or right.get("schema_version") != REPORT_SCHEMA:
        problems.append("report schema mismatch")
    left_git = str((left.get("producer_git") or {}).get("git_commit"))
    right_git = str((right.get("producer_git") or {}).get("git_commit"))
    if left_git != right_git:
        problems.append("producer code differs")
    left_ids = left.get("probe_ids")
    right_ids = right.get("probe_ids")
    if left_ids != right_ids:
        problems.append("probe scope differs")
    probes: list[dict[str, Any]] = []
    if isinstance(left_ids, list) and left_ids == right_ids:
        right_by_id = {str(item.get("probe_id")): item for item in right.get("probes") or []}
        for item in left.get("probes") or []:
            if not isinstance(item, Mapping):
                continue
            other = right_by_id.get(str(item.get("probe_id")))
            if not isinstance(other, Mapping):
                problems.append(f"missing probe {item.get('probe_id')}")
                continue
            if item.get("fine_level") != other.get("fine_level") or item.get("coarse_level") != other.get("coarse_level"):
                problems.append(f"{item.get('probe_id')} grid identity differs")
                continue
            left_masks = _as_mapping(item.get("masks"))
            right_masks = _as_mapping(other.get("masks"))
            for label_name in ("fine_oracle_labels", "coarse_oracle_labels", "fine_direct_labels", "coarse_direct_labels"):
                if left_masks.get(label_name) != right_masks.get(label_name):
                    problems.append(f"{item.get('probe_id')} {label_name} differ")
            column_changes: dict[str, Any] = {}
            occupancy: dict[str, Any] = {}
            left_columns = _as_mapping(item.get("columns"))
            right_columns = _as_mapping(other.get("columns"))
            for column in ("source_vs_direct", "source_vs_oracle"):
                left_column = _as_mapping(left_columns.get(column))
                right_column = _as_mapping(right_columns.get(column))
                if not left_column or not right_column:
                    problems.append(f"{item.get('probe_id')} missing {column}")
                    continue
                changes: dict[str, Any] = {}
                for grid in ("fine", "coarse"):
                    for key in ("missed_covered_fraction", "false_positive_fraction"):
                        left_state, left_value = _scalar(left_column, grid, key)
                        right_state, right_value = _scalar(right_column, grid, key)
                        if left_state == right_state == "NOT_APPLICABLE":
                            changes[f"{grid}.{key}"] = {"state": "NOT_APPLICABLE", "absolute_change": None}
                            continue
                        if left_state != "VALUE" or right_state != "VALUE" or left_value is None or right_value is None:
                            changes[f"{grid}.{key}"] = {"state": "UNEVALUABLE", "absolute_change": None}
                            continue
                        changes[f"{grid}.{key}"] = {
                            "state": "VALUE",
                            "absolute_change": abs(left_value - right_value),
                        }
                    left_state, left_value = _normalized_hausdorff(left_column, grid)
                    right_state, right_value = _normalized_hausdorff(right_column, grid)
                    if left_state == "VALUE" and right_state == "VALUE" and left_value is not None and right_value is not None:
                        changes[f"{grid}.hausdorff_cell_diameters"] = {
                            "state": "VALUE",
                            "absolute_change": abs(left_value - right_value),
                        }
                    else:
                        changes[f"{grid}.hausdorff_cell_diameters"] = {"state": "UNEVALUABLE", "absolute_change": None}
                column_changes[column] = changes
            for column, fine_label, coarse_label in (
                ("source_vs_direct", "fine_direct_labels", "coarse_direct_labels"),
                ("source_vs_oracle", "fine_oracle_labels", "coarse_oracle_labels"),
            ):
                column_occupancy: dict[str, Any] = {}
                for grid, label_name, hit_name in (
                    ("fine", fine_label, "fine_source_hits"),
                    ("coarse", coarse_label, "coarse_source_hits"),
                ):
                    labels = left_masks.get(label_name)
                    left_hits = left_masks.get(hit_name)
                    right_hits = right_masks.get(hit_name)
                    if isinstance(labels, list) and isinstance(left_hits, list) and isinstance(right_hits, list):
                        column_occupancy[grid] = _occupancy_delta(left_hits, right_hits, labels)
                    else:
                        column_occupancy[grid] = {"state": "UNEVALUABLE", "value": None}
                occupancy[column] = column_occupancy
            probes.append(
                {
                    "probe_id": item.get("probe_id"),
                    "scalar_changes": column_changes,
                    "occupancy_disagreement": occupancy,
                }
            )
    compatible = not problems
    limit_ok = compatible
    for probe in probes:
        for changes in probe["scalar_changes"].values():
            for change in changes.values():
                value = change.get("absolute_change")
                if change.get("state") == "UNEVALUABLE" or (isinstance(value, float) and value > CROSS_RUN_LIMIT):
                    limit_ok = False
        for column_occupancy in probe["occupancy_disagreement"].values():
            if not isinstance(column_occupancy, Mapping):
                limit_ok = False
                continue
            for item in column_occupancy.values():
                value = item.get("value")
                if item.get("state") != "VALUE" or not isinstance(value, float) or value > CROSS_RUN_LIMIT:
                    limit_ok = False
    result = {
        "schema_version": COMPARE_SCHEMA,
        "compatible_convergence_pair": compatible,
        "run_level_gates_evaluated": False,
        "within_cross_run_limit": limit_ok,
        "cross_run_limit": CROSS_RUN_LIMIT,
        "problems": problems,
        "left_config_hash": left.get("config_hash"),
        "right_config_hash": right.get("config_hash"),
        "config_hashes_may_differ": True,
        "probes": probes,
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "source_run_comparison.json").write_text(json_dumps_strict(result), encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H13H source-only diagnostics")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit")
    audit.add_argument("--config", required=True, type=Path)
    audit.add_argument("--campaign-root", required=True, type=Path)
    audit.add_argument("--outdir", required=True, type=Path)
    replay = subparsers.add_parser("replay")
    replay.add_argument("--case", required=True, type=Path)
    replay.add_argument("--steps-per-ray", type=int)
    replay.add_argument("--outdir", required=True, type=Path)
    compare = subparsers.add_parser("compare-runs")
    compare.add_argument("--left", required=True, type=Path)
    compare.add_argument("--right", required=True, type=Path)
    compare.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "audit":
            audit_source_campaign(config_path=args.config, campaign_root=args.campaign_root, outdir=args.outdir)
        elif args.command == "replay":
            replay_selected_case(case_path=args.case, outdir=args.outdir, steps_per_ray=args.steps_per_ray)
        else:
            compare_source_reports(left_path=args.left, right_path=args.right, outdir=args.outdir)
    except (DiagnosticError, FileNotFoundError, ValueError) as exc:
        print(f"source diagnostics failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
