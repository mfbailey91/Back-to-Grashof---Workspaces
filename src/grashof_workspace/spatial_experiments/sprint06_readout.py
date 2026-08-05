"""Sprint 06 HTML readout assembly."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .sprint04b_readout import render_later_sprint_html

S6_IDS = (
    "ATR_EXP_032",
    "ATR_EXP_033",
    "ATR_EXP_034",
    "ATR_EXP_035",
)

S6_TITLES = {
    "ATR_EXP_032": "Duplicate scan on all four candidate fibers",
    "ATR_EXP_033": "IP primary S−UA−UB−R5 global-center invariants",
    "ATR_EXP_034": "IP alternate S−UA−UB−R5 global-center invariants",
    "ATR_EXP_035": "UR-like duplicate scan plus exploratory fixed tuples",
    "ATR_EXP_036": "Tangent and continued-motion equivalence",
}

M6_WARNING = (
    "Sprint 06 ATR_EXP_032–035 use topology-derived S−UA−UB−R5 axes, a branch-global "
    "center c*, and body-fixed axis legitimacy. UR-like 035 is exploratory only. "
    "ATR_EXP_036, McCarthy–Soh, and exact UR remain blocked until an IP candidate is exact."
)


def assemble_sprint06_payload(results_root: Path) -> dict[str, Any]:
    experiments = []
    commits: list[str] = []
    source_ids: list[str] = []
    for exp_id in S6_IDS:
        manifest = json.loads((results_root / exp_id / "manifest.json").read_text(encoding="utf-8"))
        commits.append(str(manifest.get("repository_commit", "unknown")))
        source_ids.append(str(manifest.get("source_identifier", "unknown")))
        figures = (
            sorted((results_root / exp_id / "figures").glob("*.png"))
            if (results_root / exp_id / "figures").is_dir()
            else []
        )
        metrics = manifest.get("result", {}).get("metrics", {})
        experiments.append(
            {
                "experiment_id": exp_id,
                "title": S6_TITLES[exp_id],
                "status": manifest["status"],
                "expected": manifest["expected"],
                "observed": manifest["observed"],
                "verdict": metrics.get("verdict") or metrics.get("axes_construction"),
                "figures": [str(path) for path in figures],
            }
        )
    experiments.append(
        {
            "experiment_id": "ATR_EXP_036",
            "title": S6_TITLES["ATR_EXP_036"],
            "status": "DEFERRED",
            "expected": "Local tangent and continued-motion match a well-posed spherical RRRR",
            "observed": "Deferred — no exact IP candidate from ATR_EXP_033/034",
            "verdict": "deferred",
            "figures": [],
        }
    )
    pass_count = sum(1 for exp in experiments if exp["status"] == "PASS")
    return {
        "title": "Sprint 06 — Candidate spherical equivalence",
        "subtitle": "Topology-derived S−UA−UB−R5 tests on Sprint 05 candidate fibers",
        "brand": "aligned terminal-roll",
        "sprint_status": "032–035 complete / 036 deferred / Check-in 6 next",
        "milestone": "M6 — Spherical equivalence decision",
        "warning": M6_WARNING,
        "claim": (
            "For each named candidate slice, either branch-wide topology-derived concurrency "
            "and fixed arcs hold, or the candidate is rejected / approximate / unresolved / N/A. "
            "Failure of one slice is not nonexistence of all spherical fibers."
        ),
        "pass_count": pass_count,
        "experiment_count": len(experiments),
        "checkin_interpretation": "PENDING CHECK-IN 6",
        "checkin_rationale": (
            "No wrap duplicates. IP primary and alternate fail exact concurrency/arcs "
            "(ρ≈0.7–0.8 m). UR-like axis construction is not applicable. Terminal-roll "
            "reduction and local fiber existence stand."
        ),
        "checkin_decision": "AWAITING REVIEW",
        "human_gate_required": True,
        "source_identifiers": sorted({s for s in source_ids if s and s != "unknown"}),
        "repository_commits": sorted({c for c in commits if c and c != "unknown"}),
        "experiments": experiments,
        "next_stage": (
            "Check-in 6. Do not open ATR_EXP_036 or McCarthy–Soh unless an exact spherical "
            "candidate is later established. Exact UR remains blocked."
        ),
        "reproduce": [
            "python scripts/validate_spherical_candidates.py",
            "python scripts/generate_atr_sprint01_06_printout.py",
        ],
    }


def write_sprint06_readout(results_root: Path, out_dir: Path) -> dict[str, Any]:
    payload = assemble_sprint06_payload(results_root)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for exp in payload["experiments"]:
        copied = []
        for src in exp["figures"]:
            src_path = Path(src)
            dest_name = f"{exp['experiment_id']}_{src_path.name}"
            shutil.copy2(src_path, fig_dir / dest_name)
            copied.append(f"figures/{dest_name}")
        item = dict(exp)
        item["figures"] = copied
        rendered.append(item)
    payload["experiments"] = rendered
    (out_dir / "readout.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out_dir / "index.html").write_text(render_later_sprint_html(payload), encoding="utf-8")
    return payload
