#!/usr/bin/env python3
"""Replay and classify the H13H-1 selected continuation cases.

Reads the gitignored H13G pilot. Does not rerun the metric audit, alter the
default solver, or accept a reconstruction. A clean replay that disagrees with
the dirty historical fiber stays labeled as disagreement.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    file_sha256,
    json_dumps_strict,
    load_campaign_config,
    resolve_stage_budgets,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics import (
    CAUSE_MISSED_RETURN,
    CAUSE_REGULAR_BUDGET,
    classify_continuation_observation,
    next_continuation_step_budget,
    replay_selected_case,
    select_stored_continuation_cases,
)

CONFIG_RELATIVE = Path("configs/l5_positive_control_h13g_source_pilot_v1.json")
PILOT_RELATIVE = Path("outputs/r3a_h13g_source_pilot")
REPLAY_RELATIVE = Path("outputs/r3a_h13h2_continuation")
RECEIPT_JSON_RELATIVE = Path("results/l5_reconstruction/h13h/h13h2_continuation_diagnosis.json")
RECEIPT_MD_RELATIVE = Path("docs/methods/R3A_H13H_CONTINUATION_DIAGNOSIS.md")
SCHEMA = "r3a_h13h2_continuation_diagnosis_v1"


class DiagnosisError(RuntimeError):
    """A selected continuation replay could not be classified."""


def _git_text(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _read_trace(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DiagnosisError(f"{path} is not a JSON object")
    return payload


def _replay_trace(
    case: dict[str, Any],
    *,
    steps_per_ray: int | None,
    refresh: bool,
) -> dict[str, Any]:
    label = "baseline" if steps_per_ray is None else f"steps_{steps_per_ray}"
    outdir = ROOT / REPLAY_RELATIVE / "replays" / str(case["fiber_id"]) / label
    trace_path = outdir / "selected_trace_diagnostics.json"
    if trace_path.is_file() and not refresh:
        return _read_trace(trace_path)
    case_path = ROOT / REPLAY_RELATIVE / "cases" / f"{case['category']}__{label}.json"
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json_dumps_strict(case), encoding="utf-8")
    print(f"replaying {case['fiber_id']} {label}", flush=True)
    return replay_selected_case(
        case_path=case_path,
        outdir=outdir,
        steps_per_ray=steps_per_ray,
        include_raster=False,
    )


def _compact(trace: dict[str, Any], *, steps_per_ray: int | None, interval: object) -> dict[str, Any]:
    case = trace.get("case")
    if not isinstance(case, dict):
        raise DiagnosisError("replay is missing its case observation")
    status = interval if isinstance(interval, str) else None
    classification = classify_continuation_observation(case, stored_interval_status=status)
    return {
        "steps_per_ray": steps_per_ray,
        "baseline_steps": trace.get("baseline_steps_per_ray") is True,
        "stored_fiber_agreement": trace.get("stored_fiber_agreement"),
        "trace_cover_seed": case.get("trace_cover_seed"),
        "continuation_seed": case.get("continuation_seed"),
        "first_serialized_sample_is_seed": case.get("first_serialized_sample_is_seed"),
        "seed_inferred_from_first_sample": False,
        "classification": classification,
    }


def _schedule(
    baseline: dict[str, Any],
    *,
    baseline_steps: int,
    refresh: bool,
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    baseline_classification = baseline["classification"]
    if not isinstance(baseline_classification, dict):
        raise DiagnosisError("baseline classification is missing")
    compared_steps: int | None = None
    compared: dict[str, Any] | None = None
    while True:
        nxt = next_continuation_step_budget(
            baseline_classification,
            baseline_steps=baseline_steps,
            compared_steps=compared_steps,
            compared=compared,
        )
        if nxt is None:
            return comparisons
        trace = _replay_trace(case, steps_per_ray=nxt, refresh=refresh)
        compact = _compact(trace, steps_per_ray=nxt, interval=case.get("stored_interval_status"))
        classification = compact["classification"]
        if not isinstance(classification, dict):
            raise DiagnosisError("comparison classification is missing")
        base_arc = baseline_classification.get("accepted_arclength")
        new_arc = classification.get("accepted_arclength")
        advanced = (
            isinstance(base_arc, (int, float))
            and isinstance(new_arc, (int, float))
            and float(new_arc) > float(base_arc)
        )
        compact["arclength_increased"] = advanced
        compact["remained_regular_budget"] = classification.get("demonstrated_cause") == CAUSE_REGULAR_BUDGET
        comparisons.append(compact)
        compared_steps = nxt
        compared = classification


def _case_record(case: dict[str, Any], *, baseline_steps: int, refresh: bool) -> dict[str, Any]:
    baseline_trace = _replay_trace(case, steps_per_ray=None, refresh=refresh)
    baseline = _compact(
        baseline_trace,
        steps_per_ray=baseline_steps,
        interval=case.get("stored_interval_status"),
    )
    comparisons = _schedule(baseline, baseline_steps=baseline_steps, refresh=refresh, case=case)
    classification = baseline["classification"]
    defect = (
        isinstance(classification, dict)
        and classification.get("demonstrated_cause") == CAUSE_MISSED_RETURN
    ) or any(
        isinstance(item.get("classification"), dict)
        and item["classification"].get("demonstrated_cause") == CAUSE_MISSED_RETURN
        for item in comparisons
    )
    return {
        "category": case["category"],
        "probe_id": case["probe_id"],
        "fiber_id": case["fiber_id"],
        "c": case["c"],
        "bin_index": case["bin_index"],
        "trace_index": case["trace_index"],
        "stored_termination_status": case["stored_termination_status"],
        "stored_interval_status": case["stored_interval_status"],
        "stored_positive_accepted_steps": case["stored_positive_accepted_steps"],
        "stored_negative_accepted_steps": case["stored_negative_accepted_steps"],
        "stored_interval_evidence": case.get("stored_interval_evidence"),
        "baseline": baseline,
        "step_count_comparisons": comparisons,
        "step_cap_comparison": "not_run",
        "unequal_ray_budget_comparison": "not_run",
        "solver_defect_demonstrated": defect,
    }


def build_receipt(*, refresh_replays: bool) -> dict[str, Any]:
    pilot = ROOT / PILOT_RELATIVE
    config_path = ROOT / CONFIG_RELATIVE
    if not pilot.is_dir():
        raise DiagnosisError(f"historical pilot is absent: {pilot}")
    config = load_campaign_config(config_path)
    cases, counts = select_stored_continuation_cases(campaign_root=pilot, config_path=config_path)
    if not cases:
        raise DiagnosisError("no continuation cases were selected")
    mode = str(cases[0]["mode"])
    baseline_steps = resolve_stage_budgets(config, mode).continuation_steps
    records = [
        _case_record(case, baseline_steps=baseline_steps, refresh=refresh_replays) for case in cases
    ]
    implicated_cap = [
        item["fiber_id"]
        for item in records
        if isinstance(item["baseline"]["classification"], dict)
        and item["baseline"]["classification"].get("reached_step_cap") is True
        and item["baseline"]["classification"].get("closure_route") is None
    ]
    implicated_endpoint = [
        item["fiber_id"]
        for item in records
        if isinstance(item["baseline"]["classification"], dict)
        and item["baseline"]["classification"].get("endpoint_meeting_implicated") is True
    ]
    for item in records:
        item["step_cap_comparison"] = "required" if item["fiber_id"] in implicated_cap else "not_implicated"
        item["unequal_ray_budget_comparison"] = (
            "required" if item["fiber_id"] in implicated_endpoint else "not_implicated"
        )
    defect = any(item["solver_defect_demonstrated"] for item in records)
    pending = [
        item["fiber_id"]
        for item in records
        if item["step_cap_comparison"] == "required" or item["unequal_ray_budget_comparison"] == "required"
    ]
    if pending:
        deferred_reason = (
            "A selected trace implicates return sampling or endpoint meeting. "
            f"Those comparisons are still required for {pending}."
        )
    elif any(item["step_count_comparisons"] for item in records):
        deferred_reason = (
            "No selected replay demonstrated a continuation defect. "
            "Step-count comparisons that remained regular budget are a later numerical-schedule question."
        )
    else:
        deferred_reason = (
            "No selected replay demonstrated a continuation defect. "
            "No selected fiber had demonstrated cause REGULAR_BUDGET_EXHAUSTED, "
            "so the 96-step and 192-step comparisons were not run. "
            "Regular budget exhaustion remains a later numerical-schedule question."
        )
    return {
        "schema_version": SCHEMA,
        "work_package": "H13H-2",
        "diagnostic_only": True,
        "accepted_reconstruction": False,
        "source_policy_validated": False,
        "h12_hub_replaced": False,
        "natural_budget_changed": False,
        "production_solver_changed": False,
        "solver_defect_demonstrated": defect,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inspection": {
            "head": _git_text(["rev-parse", "HEAD"]),
            "branch": _git_text(["rev-parse", "--abbrev-ref", "HEAD"]),
        },
        "config_path": CONFIG_RELATIVE.as_posix(),
        "config_hash": config.config_hash,
        "campaign_root": PILOT_RELATIVE.as_posix(),
        "mode": mode,
        "baseline_steps_per_ray": baseline_steps,
        "historical_producer": "historical_dirty_producer",
        "clean_replay_disagreement_is_not_a_solver_defect": True,
        "category_counts": counts,
        "source_control_sha256": {
            "summary": file_sha256(pilot / "source_control.json"),
            **{
                probe_id: file_sha256(pilot / probe_id / "source_control.json")
                for probe_id in dict.fromkeys(item["probe_id"] for item in records)
            },
        },
        "cases": records,
        "deferred": {
            "continuation_max_steps_per_ray": "not_added",
            "h13h_source_convergence_v1": "not_registered",
            "unknown_policy_rejection": "not_changed",
            "reason": deferred_reason,
        },
    }


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return "null" if value is None else str(value)


def interval_reading(evidence: object) -> str:
    if not isinstance(evidence, dict):
        return "No stored interval evidence."
    raster = evidence.get("rasterization_incomplete_count")
    kinds = evidence.get("closure_kind_counts")
    if isinstance(raster, int) and raster > 0 and kinds == {"RETURNED_TO_SEED": 8}:
        return (
            "Every stored closure in this bin returned to its seed. "
            f"{raster} fibers have incomplete rasterization, which leaves the interval mixed."
        )
    if evidence.get("required") is False and evidence.get("corrector_failure_count"):
        return (
            "This bin is not required. Its stored closures are corrector failures "
            "on a boundary interval, with blocking projection failures."
        )
    if evidence.get("rasterization_incomplete_count") == 0 and kinds == {"RETURNED_TO_SEED": 8}:
        return "The stored interval is a returned set. Rasterization is complete."
    return "The stored interval counts are recorded above."


def render_markdown(receipt: dict[str, Any]) -> str:
    inspection = receipt["inspection"]
    scope = (
        f"Inspection HEAD `{inspection['head']}` on `{inspection['branch']}`. "
        f"Config hash `{receipt['config_hash']}`. Mode `{receipt['mode']}` uses "
        f"{receipt['baseline_steps_per_ray']} continuation steps per ray when no override is supplied."
    )
    lines = [
        "# R3A-H13H-2 continuation diagnosis",
        "",
        (
            "**Status:** DIAGNOSIS RECORDED. Source policy validated: false. "
            "`accepted_reconstruction`: false. The default continuation solver is unchanged."
        ),
        "",
        (
            "**Authority:** This file is the H13H-2 continuation diagnosis. "
            "[R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) "
            "remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the "
            "scientific status ledger. Machine-readable copy: "
            "[h13h2_continuation_diagnosis.json](../../results/l5_reconstruction/h13h/h13h2_continuation_diagnosis.json)."
        ),
        "",
        "Regenerate from the gitignored historical pilot with:",
        "",
        "```bash",
        "PYTHONPATH=src python scripts/write_h13h2_continuation_diagnosis.py",
        "```",
        "",
        "## 1. Scope",
        "",
        scope,
        "",
        (
            "The historical pilot remains a dirty-producer record. `stored_fiber_agreement` false means "
            "this clean replay disagrees with that record. Disagreement is not a solver defect."
        ),
        "",
        (
            "Raster-only failures are outside this diagnosis. Full per-step traces stay in gitignored "
            "`outputs/r3a_h13h2_continuation/`."
        ),
        "",
        "## 2. Selected continuation cases",
        "",
        f"Underlying counts: `{receipt['category_counts']}`.",
        "",
    ]
    for case in receipt["cases"]:
        classification = case["baseline"]["classification"]
        identity = (
            f"- Fiber `{case['fiber_id']}` at c `{_fmt(case['c'])}`, stored termination "
            f"`{case['stored_termination_status']}`, stored interval `{case['stored_interval_status']}`."
        )
        closure = (
            f"- Closure route: `{classification['closure_route']}`. "
            f"Ray terminations: `{classification['ray_terminations']}`."
        )
        steps = (
            f"- Accepted steps `{classification['accepted_step_count']}`, arclength "
            f"`{_fmt(classification['accepted_arclength'])}`, step range "
            f"`{_fmt(classification['minimum_accepted_step'])}` to "
            f"`{_fmt(classification['maximum_accepted_step'])}`."
        )
        flags = (
            f"- Reached step cap: `{classification['reached_step_cap']}`. "
            f"Endpoint meeting implicated: `{classification['endpoint_meeting_implicated']}`."
        )
        comparisons = (
            f"- Step-count comparisons: `{len(case['step_count_comparisons'])}`. "
            f"Step-cap comparison: `{case['step_cap_comparison']}`. "
            f"Unequal ray budgets: `{case['unequal_ray_budget_comparison']}`."
        )
        lines.extend(
            [
                f"### {case['category']}",
                "",
                identity,
                f"- Baseline agreement with the stored fiber: `{case['baseline']['stored_fiber_agreement']}`.",
                f"- Demonstrated cause: `{classification['demonstrated_cause']}`. {classification['explanation']}",
                f"- Possible causes: `{classification['possible_causes']}`.",
                closure,
                steps,
                flags,
                comparisons,
                (
                    "- Seed inferred from the first serialized sample: "
                    f"`{case['baseline']['seed_inferred_from_first_sample']}`. "
                    "First serialized sample equals a recorded seed: "
                    f"`{case['baseline']['first_serialized_sample_is_seed']}`."
                ),
                f"- Rejection counts: `{classification['rejection_reason_counts']}`.",
                f"- Stored interval evidence: `{case.get('stored_interval_evidence')}`.",
                f"- Interval reading: {interval_reading(case.get('stored_interval_evidence'))}",
                "",
            ]
        )
    deferred = receipt["deferred"]
    decision = (
        f"`solver_defect_demonstrated` is `{receipt['solver_defect_demonstrated']}`. "
        f"`production_solver_changed` is `{receipt['production_solver_changed']}`. "
        "The shared natural continuation budget is unchanged."
    )
    lines.extend(
        [
            "## 3. Repair decision",
            "",
            decision,
            "",
            deferred["reason"],
            "",
            "- `continuation_max_steps_per_ray`: not added.",
            "- `h13h_source_convergence_v1`: not registered.",
            (
                "- Unknown nonempty policy tokens: dispatch unchanged. "
                "An absent policy version still selects the H12 path."
            ),
            "",
            (
                "A regular budget on a later numerical schedule remains an H13H-4 question. "
                "It is not converted into closure here."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_receipt(receipt: dict[str, Any]) -> None:
    json_path = ROOT / RECEIPT_JSON_RELATIVE
    md_path = ROOT / RECEIPT_MD_RELATIVE
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json_dumps_strict(receipt), encoding="utf-8")
    md_path.write_text(render_markdown(receipt), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the H13H-2 continuation diagnosis")
    parser.add_argument("--refresh-replays", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = build_receipt(refresh_replays=args.refresh_replays)
    except DiagnosisError as exc:
        print(f"continuation diagnosis failed: {exc}")
        return 1
    write_receipt(receipt)
    print(f"wrote {RECEIPT_JSON_RELATIVE}")
    print(f"wrote {RECEIPT_MD_RELATIVE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
