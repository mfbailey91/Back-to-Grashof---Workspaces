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

from .artifacts import validate_campaign_tree
from .comparison import evaluate_direct_and_source_columns
from .direct_truth import found_configurations
from .models import (
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
)
from .source_control_h13g import (
    continue_source_fiber_h13g,
    discover_projected_source_seeds,
    load_h13g_source_policy,
    rasterize_fiber_kinematically,
    trace_and_cover_projected_seeds,
)
from .sphere_grid import build_sphere_grid

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
) -> dict[str, Any]:
    """Replay one selected fiber and record its seed, BranchTrace, and raster segments."""

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
    steps = budgets.continuation_steps if steps_per_ray is None else int(steps_per_ray)
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
        max_traces=max(policy.max_source_traces_per_c, target_index + 1),
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

    def _record_segment(payload: Mapping[str, Any]) -> None:
        segments.append(dict(payload))

    grid = build_sphere_grid(budgets.confirmation_icosphere_level)
    raster = rasterize_fiber_kinematically(
        arm,
        probe,
        n,
        fiber,
        max_segment_rad=policy.curve_segment_fraction * grid.max_cell_diameter_rad,
        max_depth=policy.kinematic_refinement_max_depth,
        segment_observer=_record_segment,
    )
    stored_match = None
    if steps_per_ray is None:
        stored_match = (
            fiber.termination_status == case.get("stored_termination_status")
            and fiber.positive_accepted_steps == case.get("stored_positive_accepted_steps")
            and fiber.negative_accepted_steps == case.get("stored_negative_accepted_steps")
            and raster.complete == case.get("stored_rasterization_complete")
        )
    outdir.mkdir(parents=True, exist_ok=True)
    trace_doc = {
        "schema_version": TRACE_SCHEMA,
        "diagnostic_overrides": {"steps_per_ray": steps_per_ray},
        "baseline_steps_per_ray": steps_per_ray is None,
        "stored_fiber_agreement": stored_match,
        "case": {**case, **observation, "branch_trace": observation.get("branch_trace")},
    }
    raster_doc = {
        "schema_version": RASTER_SCHEMA,
        "fiber_id": fiber.fiber_id,
        "rasterization_complete": raster.complete,
        "correction_failure_count": raster.correction_failure_count,
        "depth_budget_exhausted": raster.depth_budget_exhausted,
        "segments": segments,
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
