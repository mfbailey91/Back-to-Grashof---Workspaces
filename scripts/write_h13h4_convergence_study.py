#!/usr/bin/env python3
"""Drive and record the H13H-4 P1/P4/P5 convergence study.

Runs source-only stages under gitignored profile directories. Escalates only
implicated axes. Does not accept a reconstruction or edit the H12 hub.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
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
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics import (
    audit_source_campaign,
    compare_source_reports,
    evaluate_source_run_level_gates,
)

PROBE_IDS = ("P1_DEEP_COMPLETE", "P4_OUTER_COMPLETE", "P5_OUTER_INCOMPLETE")
OUT_ROOT = Path("outputs/r3a_h13h4_convergence")
RECEIPT_JSON = Path("results/l5_reconstruction/h13h/h13h4_convergence_study.json")
RECEIPT_MD = Path("docs/methods/R3A_H13H_CONVERGENCE_STUDY.md")
SCHEMA = "r3a_h13h4_convergence_study_v1"
H13G_CONFIG = Path("configs/l5_positive_control_h13g_source_pilot_v1.json")

PROFILES: dict[str, dict[str, Any]] = {
    "baseline": {
        "config": H13G_CONFIG,
        "axis": "baseline",
        "declared": {"continuation_steps": 48},
    },
    "steps96": {
        "config": Path("configs/l5_positive_control_h13h4_steps96_v1.json"),
        "axis": "continuation_effort",
        "declared": {"continuation_max_steps_per_ray": 96},
    },
    "steps192": {
        "config": Path("configs/l5_positive_control_h13h4_steps192_v1.json"),
        "axis": "continuation_effort",
        "declared": {"continuation_max_steps_per_ray": 192},
    },
    "c50": {
        "config": Path("configs/l5_positive_control_h13h4_c50_v1.json"),
        "axis": "between_slice",
        "declared": {"c_slice_max_angular_spacing_cell_fraction": 0.50},
    },
    "curve25": {
        "config": Path("configs/l5_positive_control_h13h4_curve25_v1.json"),
        "axis": "within_curve",
        "declared": {"curve_segment_fraction": 0.25},
    },
    "stronger": {
        "config": Path("configs/l5_positive_control_h13h4_stronger_v1.json"),
        "axis": "combined_stronger",
        "declared": {
            "continuation_max_steps_per_ray": 96,
            "c_slice_max_angular_spacing_cell_fraction": 0.50,
        },
    },
}


class StudyError(RuntimeError):
    """The convergence study could not be completed."""


def _git_text(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _run_cli(config: Path, outdir: Path, stage: str) -> None:
    cmd = [
        str(ROOT / ".venv" / "bin" / "python"),
        "-m",
        "grashof_workspace.spatial_experiments.l5_reconstruction.cli",
        "--config",
        str(config),
        "--outdir",
        str(outdir),
        "--mode",
        "full",
        "--stage",
        stage,
    ]
    for probe in PROBE_IDS:
        cmd.extend(["--probe", probe])
    print(f"running {stage} -> {outdir}", flush=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    subprocess.check_call(cmd, cwd=ROOT, env=env)


def _stage_done(outdir: Path, stage_file: str) -> bool:
    return (outdir / stage_file).is_file()


def _scientific_config_fingerprint(config_path: Path) -> dict[str, Any]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    modes = raw.get("campaign_modes", {})
    mode_full = modes.get("full", {}) if isinstance(modes, dict) else {}
    return {
        "source_architecture": raw.get("source_architecture"),
        "analytical_oracle": raw.get("analytical_oracle"),
        "probes": raw.get("probes"),
        "tolerances": raw.get("tolerances"),
        "set_acceptance": raw.get("set_acceptance"),
        "full_discovery": {
            "discovery_icosphere_level": mode_full.get("discovery_icosphere_level"),
            "confirmation_icosphere_level": mode_full.get("confirmation_icosphere_level"),
            "sobol_seed_count_per_target": mode_full.get("sobol_seed_count_per_target"),
            "max_nfev_per_start": mode_full.get("max_nfev_per_start"),
            "source_c_value_count": mode_full.get("source_c_value_count"),
        },
        "sobol_seed_discovery": raw.get("sobol_seed_discovery"),
        "sobol_seed_confirmation": raw.get("sobol_seed_confirmation"),
        "sobol_scramble": raw.get("sobol_scramble"),
    }


def _reuse_truth(config_path: Path, outdir: Path, donor: Path) -> None:
    from grashof_workspace.spatial_experiments.l5_reconstruction.artifacts import finalize_stage
    from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
        file_sha256,
        stage_envelope,
    )

    donor_config = None
    for meta in PROFILES.values():
        if (ROOT / OUT_ROOT / "baseline") == donor:
            donor_config = ROOT / H13G_CONFIG
            break
    if donor_config is None:
        donor_config = ROOT / H13G_CONFIG
    if _scientific_config_fingerprint(config_path) != _scientific_config_fingerprint(donor_config):
        raise StudyError(
            f"cannot reuse truth from {donor}: scientific fingerprint differs from {config_path}"
        )
    print(f"reusing scientific truth from {donor} into {outdir}", flush=True)
    records = []
    for probe in PROBE_IDS:
        src = donor / probe / "direct_truth.json"
        if not src.is_file():
            raise StudyError(f"missing donor truth {src}")
        dst_dir = outdir / probe
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir / "direct_truth.json")
        blob = json.loads(src.read_text(encoding="utf-8"))
        records.append(
            {
                "probe_id": probe,
                "found_confirmation": blob.get("confirmation", {}).get("found_count"),
            }
        )
    config = load_campaign_config(config_path)
    summary = {
        **stage_envelope(config, stage="truth", mode="full", probe_ids=PROBE_IDS),
        "probes": records,
        "truth_provenance": {
            "kind": "reused_scientific_truth_across_source_numerical_profiles",
            "donor": donor.as_posix(),
            "donor_truth_sha256": file_sha256(donor / "truth.json"),
        },
    }
    finalize_stage(
        outdir,
        summary,
        config=config,
        stage="truth",
        mode="full",
        probe_ids=PROBE_IDS,
    )


def ensure_profile(name: str, *, reuse_truth_from: Path | None = None) -> Path:
    meta = PROFILES[name]
    config_path = ROOT / meta["config"]
    outdir = ROOT / OUT_ROOT / name
    outdir.mkdir(parents=True, exist_ok=True)
    if not _stage_done(outdir, "manifest.json"):
        _run_cli(config_path, outdir, "manifest")
    if not _stage_done(outdir, "fixture.json"):
        _run_cli(config_path, outdir, "fixture")
    if not _stage_done(outdir, "truth.json"):
        if reuse_truth_from is not None and (reuse_truth_from / "truth.json").is_file():
            _reuse_truth(config_path, outdir, reuse_truth_from)
        else:
            _run_cli(config_path, outdir, "truth")
    if not _stage_done(outdir, "source_control.json"):
        _run_cli(config_path, outdir, "source-control")
    return outdir


def audit_profile(name: str, outdir: Path) -> dict[str, Any]:
    config_path = ROOT / PROFILES[name]["config"]
    report_dir = outdir / "diagnostic_report"
    report_path = report_dir / "source_diagnostic_report.json"
    if report_path.is_file():
        return json.loads(report_path.read_text(encoding="utf-8"))
    print(f"auditing {name}", flush=True)
    return audit_source_campaign(
        config_path=config_path,
        campaign_root=outdir,
        outdir=report_dir,
    )


def gate_profile(name: str, outdir: Path, report: dict[str, Any]) -> dict[str, Any]:
    config = load_campaign_config(ROOT / PROFILES[name]["config"])
    probes = []
    all_pass = True
    continuation = False
    discovery = False
    for item in report.get("probes") or []:
        source_blob = json.loads((outdir / str(item["probe_id"]) / "source_control.json").read_text())
        gate = evaluate_source_run_level_gates(
            config=config,
            probe_report=item,
            source_blob=source_blob,
        )
        probes.append(gate)
        all_pass = all_pass and gate["passed"] is True
        continuation = continuation or gate["implicates_continuation_effort"] is True
        discovery = discovery or gate["implicates_discovery_cap"] is True
    return {
        "profile": name,
        "config": PROFILES[name]["config"].as_posix(),
        "config_hash": config.config_hash,
        "axis": PROFILES[name]["axis"],
        "declared": PROFILES[name]["declared"],
        "passed": all_pass,
        "implicates_continuation_effort": continuation,
        "implicates_discovery_cap": discovery,
        "probes": probes,
        "report_path": (outdir / "diagnostic_report" / "source_diagnostic_report.json").as_posix(),
    }


def compare_pair(left_name: str, right_name: str, left_gate: dict[str, Any], right_gate: dict[str, Any]) -> dict[str, Any]:
    left_report = ROOT / OUT_ROOT / left_name / "diagnostic_report" / "source_diagnostic_report.json"
    right_report = ROOT / OUT_ROOT / right_name / "diagnostic_report" / "source_diagnostic_report.json"
    outdir = ROOT / OUT_ROOT / "comparisons" / f"{left_name}_vs_{right_name}"
    result = compare_source_reports(left_path=left_report, right_path=right_report, outdir=outdir)
    result["run_level_gates_evaluated"] = True
    result["left_run_level_passed"] = left_gate["passed"]
    result["right_run_level_passed"] = right_gate["passed"]
    result["pair_eligible"] = bool(left_gate["passed"] and right_gate["passed"] and result.get("compatible_convergence_pair"))
    result["within_cross_run_limit"] = bool(
        result["pair_eligible"] and result.get("within_cross_run_limit")
    )
    (outdir / "source_run_comparison.json").write_text(json_dumps_strict(result), encoding="utf-8")
    return result


def run_study(*, refresh_audit: bool = False) -> dict[str, Any]:
    executed: list[str] = []
    skipped: list[dict[str, str]] = [
        {"axis": "step_resolution", "reason": "H13H-2 did not implicate return sampling or endpoint meeting"},
        {"axis": "raster_depth", "reason": "H13H-3 classified depth exhaustion as an untraced closing gap"},
    ]
    gates: dict[str, dict[str, Any]] = {}
    comparisons: list[dict[str, Any]] = []

    baseline_dir = ensure_profile("baseline")
    if refresh_audit:
        shutil.rmtree(baseline_dir / "diagnostic_report", ignore_errors=True)
    baseline_report = audit_profile("baseline", baseline_dir)
    gates["baseline"] = gate_profile("baseline", baseline_dir, baseline_report)
    executed.append("baseline")

    candidate: str | None = None
    blocker: dict[str, Any] | None = None

    if gates["baseline"]["passed"]:
        candidate = "baseline"
    elif gates["baseline"]["implicates_continuation_effort"]:
        steps96_dir = ensure_profile("steps96", reuse_truth_from=baseline_dir)
        if refresh_audit:
            shutil.rmtree(steps96_dir / "diagnostic_report", ignore_errors=True)
        gates["steps96"] = gate_profile("steps96", steps96_dir, audit_profile("steps96", steps96_dir))
        executed.append("steps96")
        if gates["steps96"]["passed"]:
            candidate = "steps96"
        elif gates["steps96"]["implicates_continuation_effort"]:
            # 192 only if still a regular traversal question. Absent a regular-budget
            # demonstration, stop rather than inventing closure.
            still_budget = any(
                any(str(item.get("status")) == "BUDGET_EXHAUSTED" for item in probe["interval_blockers"])
                for probe in gates["steps96"]["probes"]
            )
            if still_budget:
                steps192_dir = ensure_profile("steps192", reuse_truth_from=baseline_dir)
                if refresh_audit:
                    shutil.rmtree(steps192_dir / "diagnostic_report", ignore_errors=True)
                gates["steps192"] = gate_profile(
                    "steps192", steps192_dir, audit_profile("steps192", steps192_dir)
                )
                executed.append("steps192")
                if gates["steps192"]["passed"]:
                    candidate = "steps192"
                else:
                    remaining = []
                    for probe in gates["steps192"]["probes"]:
                        statuses = sorted(
                            {
                                str(item.get("status"))
                                for item in probe["interval_blockers"]
                                if item.get("status") is not None
                            }
                        )
                        remaining.append(
                            {
                                "probe_id": probe["probe_id"],
                                "statuses": statuses,
                                "raster_failures": len(probe["required_raster_failures"]),
                            }
                        )
                    blocker = {
                        "status": "REQUIRED_INTERVALS_UNRESOLVED",
                        "after_profile": "steps192",
                        "detail": (
                            "Continuation effort through 192 steps left required bins unresolved. "
                            "Remaining blockers mix projection-backed MIXED_UNRESOLVED bins with "
                            "P5 budget exhaustion and incomplete rasterization."
                        ),
                        "remaining": remaining,
                    }
            else:
                blocker = {
                    "status": "REQUIRED_INTERVALS_UNRESOLVED",
                    "after_profile": "steps96",
                    "detail": "Continuation effort did not clear required bins and did not remain a regular budget question",
                }
        else:
            blocker = {
                "status": "REQUIRED_INTERVALS_UNRESOLVED",
                "after_profile": "steps96",
                "detail": "Steps-96 profile failed without a continuation-effort implication",
            }
    else:
        blocker = {
            "status": "REQUIRED_INTERVALS_UNRESOLVED",
            "after_profile": "baseline",
            "detail": "Baseline failed without a continuation-effort implication",
        }

    if candidate is not None:
        # Between-slice after a passing candidate.
        c50_dir = ensure_profile("c50", reuse_truth_from=baseline_dir)
        if refresh_audit:
            shutil.rmtree(c50_dir / "diagnostic_report", ignore_errors=True)
        gates["c50"] = gate_profile("c50", c50_dir, audit_profile("c50", c50_dir))
        executed.append("c50")
        if not gates["c50"]["passed"]:
            blocker = {
                "status": "SPACING_PROFILE_FAILED",
                "after_profile": "c50",
                "detail": "Between-slice 0.50 profile did not pass run-level gates",
            }
            candidate = None
        else:
            comparisons.append(compare_pair(candidate, "c50", gates[candidate], gates["c50"]))
            stronger_dir = ensure_profile("stronger", reuse_truth_from=baseline_dir)
            if refresh_audit:
                shutil.rmtree(stronger_dir / "diagnostic_report", ignore_errors=True)
            gates["stronger"] = gate_profile(
                "stronger", stronger_dir, audit_profile("stronger", stronger_dir)
            )
            executed.append("stronger")
            if not gates["stronger"]["passed"]:
                blocker = {
                    "status": "STRONGER_PROFILE_FAILED",
                    "after_profile": "stronger",
                    "detail": "Combined stronger profile did not pass run-level gates",
                }
                candidate = None
            else:
                comparisons.append(
                    compare_pair(candidate, "stronger", gates[candidate], gates["stronger"])
                )
                if not comparisons[-1].get("within_cross_run_limit"):
                    blocker = {
                        "status": "CROSS_RUN_LIMIT_EXCEEDED",
                        "after_profile": "stronger",
                        "detail": "Candidate versus stronger profile exceeded Section 3.3 limits",
                    }
                    candidate = None

    if candidate is None and blocker is None:
        blocker = {
            "status": "NO_CANDIDATE",
            "after_profile": executed[-1] if executed else "none",
            "detail": "No three-probe candidate survived the bounded matrix",
        }

    head = _git_text(["rev-parse", "HEAD"])
    receipt = {
        "schema_version": SCHEMA,
        "work_package": "H13H-4",
        "diagnostic_only": True,
        "accepted_reconstruction": False,
        "source_policy_validated": False,
        "h12_hub_replaced": False,
        "natural_budget_changed": False,
        "h13g_pilot_config_changed": False,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inspection": {
            "head": head,
            "branch": _git_text(["rev-parse", "--abbrev-ref", "HEAD"]),
        },
        "probe_ids": list(PROBE_IDS),
        "executed_profiles": executed,
        "skipped_axes": skipped,
        "gates": gates,
        "comparisons": [
            {
                "left_config_hash": item.get("left_config_hash"),
                "right_config_hash": item.get("right_config_hash"),
                "compatible_convergence_pair": item.get("compatible_convergence_pair"),
                "run_level_gates_evaluated": item.get("run_level_gates_evaluated"),
                "pair_eligible": item.get("pair_eligible"),
                "within_cross_run_limit": item.get("within_cross_run_limit"),
                "problems": item.get("problems"),
            }
            for item in comparisons
        ],
        "candidate_policy": None
        if candidate is None
        else {
            "profile": candidate,
            "config": PROFILES[candidate]["config"].as_posix(),
            "config_hash": gates[candidate]["config_hash"],
            "declared": PROFILES[candidate]["declared"],
            "policy_version": "h13g_evidence_safe_v1",
        },
        "blocker": blocker,
        "protected_h13g_config_sha256": file_sha256(ROOT / H13G_CONFIG),
    }
    return receipt


def render_markdown(receipt: dict[str, Any]) -> str:
    candidate = receipt.get("candidate_policy")
    blocker = receipt.get("blocker")
    status = (
        f"Candidate profile `{candidate['profile']}` recorded."
        if isinstance(candidate, dict)
        else f"No candidate. Blocker `{blocker['status']}`."
    )
    lines = [
        "# R3A-H13H-4 P1/P4/P5 convergence study",
        "",
        (
            f"**Status:** STUDY RECORDED. {status} "
            "Source policy validated: false. `accepted_reconstruction`: false."
        ),
        "",
        (
            "**Authority:** This file is the H13H-4 convergence receipt. "
            "[R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) "
            "remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the "
            "scientific status ledger. Machine-readable copy: "
            "[h13h4_convergence_study.json](../../results/l5_reconstruction/h13h/h13h4_convergence_study.json)."
        ),
        "",
        "Regenerate with:",
        "",
        "```bash",
        "PYTHONPATH=src python scripts/write_h13h4_convergence_study.py",
        "```",
        "",
        "## 1. Scope",
        "",
        (
            f"Inspection HEAD `{receipt['inspection']['head']}` on "
            f"`{receipt['inspection']['branch']}`. Probes `{receipt['probe_ids']}`."
        ),
        "",
        f"Executed profiles: `{receipt['executed_profiles']}`.",
        f"Skipped axes: `{receipt['skipped_axes']}`.",
        "",
        "## 2. Run-level gates",
        "",
    ]
    for name, gate in receipt["gates"].items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(
            f"- Config `{gate['config']}` hash `{gate['config_hash']}`. Passed: `{gate['passed']}`."
        )
        lines.append(f"- Declared numerical fields: `{gate['declared']}`.")
        for probe in gate["probes"]:
            lines.append(
                
                    f"- `{probe['probe_id']}` passed `{probe['passed']}`; "
                    f"interval blockers `{len(probe['interval_blockers'])}`; "
                    f"required raster failures `{len(probe['required_raster_failures'])}`; "
                    f"cap flags `{len(probe['cap_flags'])}`."
                
            )
        lines.append("")
    lines.extend(["## 3. Cross-run comparisons", ""])
    if not receipt["comparisons"]:
        lines.append("No eligible Section 3.3 pair was formed.")
        lines.append("")
    for item in receipt["comparisons"]:
        lines.append(
            
                f"- Compatible `{item['compatible_convergence_pair']}`, "
                f"eligible `{item['pair_eligible']}`, "
                f"within limit `{item['within_cross_run_limit']}`, "
                f"problems `{item['problems']}`."
            
        )
    lines.extend(
        [
            "",
            "## 4. Decision",
            "",
            f"`candidate_policy`: `{receipt['candidate_policy']}`.",
            f"`blocker`: `{receipt['blocker']}`.",
            "",
            "Natural continuation budgets and the committed H13G pilot config are unchanged.",
            "",
        ]
    )
    return "\n".join(lines)


def write_receipt(receipt: dict[str, Any]) -> None:
    json_path = ROOT / RECEIPT_JSON
    md_path = ROOT / RECEIPT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json_dumps_strict(receipt) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(receipt), encoding="utf-8")
    print(f"wrote {RECEIPT_JSON}")
    print(f"wrote {RECEIPT_MD}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-audit", action="store_true")
    args = parser.parse_args()
    write_receipt(run_study(refresh_audit=args.refresh_audit))


if __name__ == "__main__":
    main()
