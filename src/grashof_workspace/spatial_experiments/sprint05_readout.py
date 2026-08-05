"""Sprint 05 HTML readout assembly."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .sprint04b_readout import render_later_sprint_html

S5_IDS = (
    "ATR_EXP_027",
    "ATR_EXP_028",
    "ATR_EXP_029",
    "ATR_EXP_030",
    "ATR_EXP_031",
)

S5_TITLES = {
    "ATR_EXP_027": "Independence of h = n · d",
    "ATR_EXP_028": "Intersecting-pairs sequential fiber",
    "ATR_EXP_029": "UR-like sequential fiber",
    "ATR_EXP_030": "Alternate task-space h artifact control",
    "ATR_EXP_031": "Independent-step fiber refinement",
}

M5_WARNING = (
    "Check-in 5 is approved with changed scope. Fibers are candidate slices, not canonical. "
    "This readout does not authorize spherical RRRR, McCarthy–Soh, or exact UR."
)


def assemble_sprint05_payload(results_root: Path) -> dict[str, Any]:
    experiments = []
    commits: list[str] = []
    source_ids: list[str] = []
    for exp_id in S5_IDS:
        manifest = json.loads((results_root / exp_id / "manifest.json").read_text(encoding="utf-8"))
        commits.append(str(manifest.get("repository_commit", "unknown")))
        source_ids.append(str(manifest.get("source_identifier", "unknown")))
        figures = (
            sorted((results_root / exp_id / "figures").glob("*.png"))
            if (results_root / exp_id / "figures").is_dir()
            else []
        )
        experiments.append(
            {
                "experiment_id": exp_id,
                "title": S5_TITLES[exp_id],
                "status": manifest["status"],
                "expected": manifest["expected"],
                "observed": manifest["observed"],
                "figures": [str(path) for path in figures],
            }
        )
    pass_count = sum(1 for exp in experiments if exp["status"] == "PASS")
    return {
        "title": "Sprint 05 — Explicit one-dimensional fiber",
        "subtitle": "Task-space scalar fibers on the validated pointing parent",
        "brand": "aligned terminal-roll",
        "sprint_status": "Closed — Check-in 5 CONTINUE WITH CHANGED SCOPE",
        "milestone": "M5 — Fiber legitimacy",
        "warning": M5_WARNING,
        "claim": (
            "One independent task-space scalar h=n·d on p=p0 and q6=q6* defines a regular, "
            "reversible local one-dimensional fiber whose pointing image is noncollapsed."
        ),
        "pass_count": pass_count,
        "experiment_count": len(experiments),
        "checkin_interpretation": "SUPPORTED LOCALLY",
        "checkin_rationale": (
            "Primary and alternate fibers exist on IP and UR-like seeds. They are candidate "
            "slices, not architecture-derived canonical fibers. Joint-freeze control is distinct."
        ),
        "checkin_decision": "CONTINUE WITH CHANGED SCOPE",
        "human_gate_required": False,
        "source_identifiers": sorted({s for s in source_ids if s and s != "unknown"}),
        "repository_commits": sorted({c for c in commits if c and c != "unknown"}),
        "experiments": experiments,
        "next_stage": "Sprint 06 topology-derived spherical candidate tests. McCarthy–Soh remains blocked.",
        "reproduce": [
            "python scripts/validate_pointing_fiber.py",
            "python scripts/generate_atr_sprint01_06_printout.py",
        ],
    }


def write_sprint05_readout(results_root: Path, out_dir: Path) -> dict[str, Any]:
    payload = assemble_sprint05_payload(results_root)
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
