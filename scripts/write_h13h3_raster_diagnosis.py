#!/usr/bin/env python3
"""Replay and classify the selected H13G raster cases.

Reads the gitignored historical pilot. Does not rerun the metric audit or
accept a reconstruction. Interior probes are diagnostic measurements; they do
not change the raster samples.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    file_sha256,
    json_dumps_strict,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import radial_normal
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control_h13 import (
    wrapped_q_distance,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control_h13g import (
    _wrapped_midpoint,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics import (
    RASTER_NONLOCAL,
    classify_raster_observation,
    replay_selected_case,
    select_stored_raster_cases,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.sphere_grid import pointing_geodesic
from grashof_workspace.spatial_experiments.parent_level_sets import correct_to_local_levelset

CONFIG_RELATIVE = Path("configs/l5_positive_control_h13g_source_pilot_v1.json")
PILOT_RELATIVE = Path("outputs/r3a_h13g_source_pilot")
REPLAY_RELATIVE = Path("outputs/r3a_h13h3_raster")
RECEIPT_JSON_RELATIVE = Path("results/l5_reconstruction/h13h/h13h3_raster_diagnosis.json")
RECEIPT_MD_RELATIVE = Path("docs/methods/R3A_H13H_RASTER_DIAGNOSIS.md")
SCHEMA = "r3a_h13h3_raster_diagnosis_v1"


class DiagnosisError(RuntimeError):
    """A selected raster replay could not be classified."""


def _git_text(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DiagnosisError(f"{path} is not a JSON object")
    return payload


def _replay(case: dict[str, Any], *, refresh: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    outdir = ROOT / REPLAY_RELATIVE / "replays" / str(case["fiber_id"])
    trace_path = outdir / "selected_trace_diagnostics.json"
    raster_path = outdir / "selected_raster_segments.json"
    if trace_path.is_file() and raster_path.is_file() and not refresh:
        return _read_json(trace_path), _read_json(raster_path)
    case_path = ROOT / REPLAY_RELATIVE / "cases" / f"{case['category']}.json"
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json_dumps_strict(case), encoding="utf-8")
    print(f"replaying {case['fiber_id']} {case['category']}", flush=True)
    replay_selected_case(case_path=case_path, outdir=outdir, include_raster=True)
    return _read_json(trace_path), _read_json(raster_path)


def _interior_probes(
    case: dict[str, Any],
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    config = load_campaign_config(ROOT / CONFIG_RELATIVE)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe(str(case["probe_id"]))
    normal = radial_normal(probe.p_star)
    c_value = float(case["c"])
    probes: list[dict[str, Any]] = []
    for segment in segments:
        if segment.get("outcome") != "within_declared_gap":
            continue
        endpoints = segment.get("endpoint_q")
        directions = segment.get("endpoint_direction")
        if not isinstance(endpoints, list) or not isinstance(directions, list):
            continue
        if len(endpoints) != 2 or len(directions) != 2:
            continue
        q_a = tuple(float(value) for value in endpoints[0])
        q_b = tuple(float(value) for value in endpoints[1])
        guess = _wrapped_midpoint(q_a, q_b)
        span = wrapped_q_distance(q_a, q_b)
        corrected, ok, _residual = correct_to_local_levelset(
            arm.model,
            guess,
            q_a,
            q_b,
            probe.p_star,
            normal,
            c_value,
            trust_radius=span,
        )
        row: dict[str, Any] = {
            "correction_ok": ok,
            "closing_segment": segment.get("closing_segment") is True,
            "pointing_excursion_rad": None,
        }
        if ok:
            direction = as_vec3(arm.chain.evaluate(tuple(float(value) for value in corrected)).d)
            gap = float(segment["angular_gap_rad"])
            left = pointing_geodesic(directions[0], direction)
            right = pointing_geodesic(direction, directions[1])
            row["pointing_excursion_rad"] = left + right - gap
        probes.append(row)
    return probes


def _compact(
    case: dict[str, Any],
    trace: dict[str, Any],
    raster: dict[str, Any],
    probes: list[dict[str, Any]],
) -> dict[str, Any]:
    segments = raster.get("segments")
    if not isinstance(segments, list):
        raise DiagnosisError(f"{case['fiber_id']} has no raster segments")
    evidence = case.get("stored_interval_evidence")
    required = evidence.get("required") if isinstance(evidence, dict) else None
    observation = {
        "segments": segments,
        "rasterization_complete": raster.get("rasterization_complete"),
        "correction_failure_count": raster.get("correction_failure_count"),
        "depth_budget_exhausted": raster.get("depth_budget_exhausted"),
        "max_position_residual_m": raster.get("max_position_residual_m"),
        "max_h_residual": raster.get("max_h_residual"),
        "position_tolerance_m": raster.get("position_tolerance_m"),
        "h_tolerance": raster.get("h_tolerance"),
        "max_segment_rad": raster.get("max_segment_rad"),
        "positive_ray_termination": case.get("stored_positive_ray_termination"),
        "negative_ray_termination": case.get("stored_negative_ray_termination"),
        "stored_interval_status": case.get("stored_interval_status"),
        "interval_required": required,
        "interior_probes": probes,
    }
    classification = classify_raster_observation(observation)
    excursions = [
        float(item["pointing_excursion_rad"])
        for item in probes
        if isinstance(item.get("pointing_excursion_rad"), (int, float))
    ]
    return {
        "category": case["category"],
        "fiber_id": case["fiber_id"],
        "probe_id": case["probe_id"],
        "c": case["c"],
        "stored_termination_status": case["stored_termination_status"],
        "stored_positive_ray_termination": case.get("stored_positive_ray_termination"),
        "stored_negative_ray_termination": case.get("stored_negative_ray_termination"),
        "stored_rasterization_complete": case.get("stored_rasterization_complete"),
        "stored_interval_status": case.get("stored_interval_status"),
        "stored_interval_evidence": evidence,
        "stored_endpoint_gap_rad": case.get("stored_endpoint_gap_rad"),
        "stored_fiber_agreement": trace.get("stored_fiber_agreement"),
        "replay_rasterization_complete": raster.get("rasterization_complete"),
        "replay_correction_failure_count": raster.get("correction_failure_count"),
        "replay_depth_budget_exhausted": raster.get("depth_budget_exhausted"),
        "max_position_residual_m": raster.get("max_position_residual_m"),
        "max_h_residual": raster.get("max_h_residual"),
        "max_segment_rad": raster.get("max_segment_rad"),
        "segment_count": len(segments),
        "interior_probe_count": len(probes),
        "max_interior_excursion_rad": max(excursions) if excursions else None,
        "classification": classification,
    }


def build_receipt(*, refresh_replays: bool) -> dict[str, Any]:
    pilot = ROOT / PILOT_RELATIVE
    if not pilot.is_dir():
        raise DiagnosisError(f"historical pilot is not available at {pilot}")
    config = load_campaign_config(ROOT / CONFIG_RELATIVE)
    cases, counts = select_stored_raster_cases(campaign_root=pilot, config_path=ROOT / CONFIG_RELATIVE)
    records = []
    for case in cases:
        trace, raster = _replay(case, refresh=refresh_replays)
        segments = raster.get("segments")
        if not isinstance(segments, list):
            raise DiagnosisError(f"{case['fiber_id']} raster has no segments")
        probes = _interior_probes(case, [item for item in segments if isinstance(item, dict)])
        records.append(_compact(case, trace, raster, probes))
    defect = any(
        item["classification"]["demonstrated_cause"] == RASTER_NONLOCAL
        or item["classification"]["hidden_interior_count"] > 0
        or item["classification"]["interval_left_covered"] is True
        for item in records
    )
    head = _git_text(["rev-parse", "HEAD"])
    return {
        "schema_version": SCHEMA,
        "work_package": "H13H-3",
        "diagnostic_only": True,
        "accepted_reconstruction": False,
        "source_policy_validated": False,
        "h12_hub_replaced": False,
        "natural_budget_changed": False,
        "continuation_solver_changed": False,
        "production_raster_changed": True,
        "solver_defect_demonstrated": True,
        "replay_still_shows_nonlocal_sample": defect,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inspection": {
            "head": head,
            "branch": _git_text(["rev-parse", "--abbrev-ref", "HEAD"]),
        },
        "config_path": CONFIG_RELATIVE.as_posix(),
        "config_hash": config.config_hash,
        "campaign_root": PILOT_RELATIVE.as_posix(),
        "historical_producer": "historical_dirty_producer",
        "category_counts": counts,
        "source_control_sha256": {
            "summary": file_sha256(pilot / "source_control.json"),
        },
        "repair": {
            "midpoint_correction": "chord_section_with_chord_length_trust_radius",
            "residual_completion_gate": "position_and_scalar_residuals_block_completion",
            "continuation_max_steps_per_ray": "not_added",
            "h13h_source_convergence_v1": "not_registered",
            "raster_depth_increased": False,
        },
        "cases": records,
    }


def render_markdown(receipt: dict[str, Any]) -> str:
    inspection = receipt["inspection"]
    lines = [
        "# R3A-H13H-3 raster diagnosis",
        "",
        (
            "**Status:** DIAGNOSIS RECORDED. Source policy validated: false. "
            "`accepted_reconstruction`: false. Raster midpoints now stay on the "
            "wrapped chord section. Continuation is unchanged."
        ),
        "",
        (
            "**Authority:** This file is the H13H-3 raster diagnosis. "
            "[R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) "
            "remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the "
            "scientific status ledger. Machine-readable copy: "
            "[h13h3_raster_diagnosis.json](../../results/l5_reconstruction/h13h/h13h3_raster_diagnosis.json)."
        ),
        "",
        "Regenerate from the gitignored historical pilot with:",
        "",
        "```bash",
        "PYTHONPATH=src python scripts/write_h13h3_raster_diagnosis.py",
        "```",
        "",
        "## 1. Scope",
        "",
        (
            f"Inspection HEAD `{inspection['head']}` on `{inspection['branch']}`. "
            f"Config hash `{receipt['config_hash']}`."
        ),
        "",
        (
            "The historical pilot remains a dirty-producer record. "
            "Agreement compares termination, accepted step counts, and the raster "
            "completion flag. A false agreement means this repaired replay disagrees "
            "with that record. Disagreement is not a solver defect by itself."
        ),
        "",
        "## 2. Selected raster cases",
        "",
        f"Underlying counts: `{receipt['category_counts']}`.",
        "",
    ]
    for case in receipt["cases"]:
        classification = case["classification"]
        lines.extend(
            [
                f"### {case['category']}",
                "",
                (
                    f"- Fiber `{case['fiber_id']}` at c `{case['c']}`. "
                    f"Stored termination `{case['stored_termination_status']}`, "
                    f"rays `{case['stored_positive_ray_termination']}` / "
                    f"`{case['stored_negative_ray_termination']}`."
                ),
                (
                    f"- Stored raster complete: `{case['stored_rasterization_complete']}`. "
                    f"Replay raster complete: `{case['replay_rasterization_complete']}`. "
                    f"Stored fiber agreement: `{case['stored_fiber_agreement']}`."
                ),
                (
                    f"- Demonstrated cause: `{classification['demonstrated_cause']}`. "
                    f"{classification['explanation']}"
                ),
                (
                    f"- Closing outcomes: `{classification['closing_segment_outcomes']}`. "
                    f"Replay correction failures: `{case['replay_correction_failure_count']}`. "
                    f"Replay depth exhausted: `{case['replay_depth_budget_exhausted']}`. "
                    f"Nonlocal corrections: `{classification['nonlocal_correction_count']}`. "
                    f"Interval blocked: `{classification['interval_blocked']}`."
                ),
                (
                    f"- Residuals position `{case['max_position_residual_m']}`, "
                    f"scalar `{case['max_h_residual']}`. "
                    f"Max interior excursion `{case['max_interior_excursion_rad']}` "
                    f"over `{case['interior_probe_count']}` short segments."
                ),
                "",
            ]
        )
    repair = receipt["repair"]
    lines.extend(
        [
            "## 3. Repair decision",
            "",
            (
                "The selected depth-exhausted closing chord accepted a midpoint correction "
                "farther than the chord. Raster midpoints now solve the level set on the "
                "wrapped chord section and are rejected outside that chord. Position and "
                "scalar residuals block completion."
            ),
            "",
            f"- Midpoint correction: `{repair['midpoint_correction']}`.",
            f"- Residual gate: `{repair['residual_completion_gate']}`.",
            f"- Continuation step budget: `{repair['continuation_max_steps_per_ray']}`.",
            f"- `h13h_source_convergence_v1`: `{repair['h13h_source_convergence_v1']}`.",
            f"- Raster depth increased: `{repair['raster_depth_increased']}`.",
            "",
            (
                f"`replay_still_shows_nonlocal_sample` is `{receipt['replay_still_shows_nonlocal_sample']}`. "
                "`accepted_reconstruction` remains false."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_receipt(receipt: dict[str, Any]) -> None:
    json_path = ROOT / RECEIPT_JSON_RELATIVE
    md_path = ROOT / RECEIPT_MD_RELATIVE
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json_dumps_strict(receipt) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(receipt), encoding="utf-8")
    print(f"wrote {RECEIPT_JSON_RELATIVE}")
    print(f"wrote {RECEIPT_MD_RELATIVE}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-replays", action="store_true")
    args = parser.parse_args()
    write_receipt(build_receipt(refresh_replays=args.refresh_replays))


if __name__ == "__main__":
    main()
