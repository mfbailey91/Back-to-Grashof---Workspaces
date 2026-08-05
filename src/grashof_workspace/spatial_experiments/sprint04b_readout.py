"""Sprint 04B/04C HTML readout assembly."""

from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path
from typing import Any

S4B_IDS = (
    "ATR_EXP_021",
    "ATR_EXP_022",
    "ATR_EXP_023",
    "ATR_EXP_024",
    "ATR_EXP_025",
    "ATR_EXP_026",
)

S4B_TITLES = {
    "ATR_EXP_021": "Sequential forward/reverse rays",
    "ATR_EXP_022": "Intersecting-pairs transported chart",
    "ATR_EXP_023": "UR-like transported chart",
    "ATR_EXP_024": "Shared-microstep consistency",
    "ATR_EXP_025": "Independent-step refinement",
    "ATR_EXP_026": "Alternate-path and duplicate analysis",
}

M4B_WARNING = (
    "Check-ins 4B and 04C are approved. This diagnostic does not authorize spherical "
    "RRRR, McCarthy–Soh, or exact UR."
)


def assemble_sprint04b_payload(results_root: Path) -> dict[str, Any]:
    experiments = []
    commits: list[str] = []
    source_ids: list[str] = []
    for exp_id in S4B_IDS:
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
                "title": S4B_TITLES[exp_id],
                "status": manifest["status"],
                "expected": manifest["expected"],
                "observed": manifest["observed"],
                "figures": [str(path) for path in figures],
            }
        )
    pass_count = sum(1 for exp in experiments if exp["status"] == "PASS")
    return {
        "title": "Sprint 04B / 04C — Sequential chart validation",
        "subtitle": "Endpoint reverse, rank-two charts, refinement, and claim-language audit",
        "brand": "aligned terminal-roll",
        "sprint_status": "Complete — Check-in 4B Case A / 04C Pass",
        "milestone": "M4 — Two-dimensional pointing surface",
        "warning": M4B_WARNING,
        "claim": (
            "Sequential predictor-corrector continuation with transported tangent frames "
            "produces a reversible, rank-two, noncollapsed local pointing chart on both "
            "IntersectingPairsAligned6R and URLikeAligned6R."
        ),
        "pass_count": pass_count,
        "experiment_count": len(experiments),
        "checkin_interpretation": "SUPPORTED LOCALLY",
        "checkin_rationale": (
            "Check-in 4B Case A and Check-in 04C Pass authorize Sprint 05 fiber work. "
            "ATR_EXP_024 is shared-microstep consistency, not independent refinement."
        ),
        "checkin_decision": "CONTINUE / Case A",
        "human_gate_required": False,
        "source_identifiers": sorted({s for s in source_ids if s and s != "unknown"}),
        "repository_commits": sorted({c for c in commits if c and c != "unknown"}),
        "experiments": experiments,
        "next_stage": "Sprint 05 explicit one-dimensional fiber is closed. Sprint 06 candidate spherical tests follow.",
        "reproduce": [
            "python scripts/validate_pointing_chart.py",
            "python scripts/generate_atr_sprint01_06_printout.py",
        ],
    }


def write_sprint04b_readout(results_root: Path, out_dir: Path) -> dict[str, Any]:
    payload = assemble_sprint04b_payload(results_root)
    return _write_readout(payload, out_dir)


def _write_readout(payload: dict[str, Any], out_dir: Path) -> dict[str, Any]:
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


def render_later_sprint_html(payload: dict[str, Any]) -> str:
    cards = []
    for exp in payload["experiments"]:
        status = str(exp["status"])
        badge = "pass" if status == "PASS" else ("deferred" if status == "DEFERRED" else "warn")
        imgs = "".join(
            f'<img src="{escape(src)}" alt="{escape(exp["experiment_id"])} figure" />' for src in exp["figures"]
        )
        cards.append(
            f"""
            <article class="card">
              <h3>{escape(exp["experiment_id"])} — {escape(exp["title"])}
                <span class="badge {badge}">{escape(status)}</span></h3>
              <p><strong>Expected.</strong> {escape(exp["expected"])}</p>
              <p><strong>Observed.</strong> {escape(exp["observed"])}</p>
              {imgs}
            </article>
            """
        )
    reproduce = "".join(f"<code>{escape(cmd)}</code>" for cmd in payload["reproduce"])
    commits = ", ".join(escape(c[:12]) for c in payload["repository_commits"]) or "unknown"
    sources = ", ".join(escape(s) for s in payload["source_identifiers"]) or "unknown"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(payload["title"])}</title>
  <style>
    :root {{
      --bg0:#10151b; --bg1:#182028; --panel:#24303c; --ink:#e8eef4; --muted:#9aa8b5;
      --line:#3a4a5a; --teal:#2a9d8f; --amber:#e9a319; --good:#3cbf9a;
      font-family:"IBM Plex Sans","Segoe UI",sans-serif; color:var(--ink);
      background: linear-gradient(160deg, var(--bg0), var(--bg1));
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; line-height:1.5; padding-bottom:3rem; }}
    .shell {{ max-width:1100px; margin:0 auto; padding:1.5rem; }}
    .brand {{ color:var(--teal); letter-spacing:.04em; font-size:.85rem; text-transform:uppercase; }}
    h1 {{ margin:.35rem 0 .6rem; font-size:2rem; }}
    .lead,.muted {{ color:var(--muted); }}
    .warning {{ border-left:3px solid var(--amber); background:rgba(233,163,25,.08); padding:.75rem 1rem; }}
    .claim,.card,.stat {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:1rem; margin:1rem 0; }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:.75rem; }}
    .stat {{ margin:0; }}
    .badge.pass {{ color:var(--good); border:1px solid var(--good); border-radius:999px; padding:.15rem .55rem; font-size:.75rem; }}
    .badge.deferred,.badge.warn {{ color:var(--amber); border:1px solid var(--amber); border-radius:999px; padding:.15rem .55rem; font-size:.75rem; }}
    img {{ max-width:100%; height:auto; border-radius:6px; background:#0b1014; margin-top:.6rem; }}
    code {{ display:inline-block; background:#0b1014; border:1px solid var(--line); border-radius:4px; padding:.2rem .45rem; margin:.2rem .35rem .2rem 0; }}
    footer {{ color:var(--muted); margin-top:2rem; font-size:.9rem; }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="brand">{escape(payload["brand"])}</div>
    <h1>{escape(payload["title"])}</h1>
    <p class="lead">{escape(payload["subtitle"])} · {escape(payload["sprint_status"])} · {escape(payload["milestone"])}</p>
    <p class="warning">{escape(payload["warning"])}</p>
    <section class="claim"><strong>Claim under test.</strong><p>{escape(payload["claim"])}</p></section>
    <section class="claim"><strong>Check-in.</strong> {escape(payload["checkin_interpretation"])} / {escape(payload["checkin_decision"])}.
      <p>{escape(payload["checkin_rationale"])}</p></section>
    <section class="stats">
      <div class="stat"><div class="muted">Experiments</div><div>{payload["pass_count"]}/{payload["experiment_count"]} PASS</div></div>
      <div class="stat"><div class="muted">Interpretation</div><div>{escape(payload["checkin_interpretation"])}</div></div>
      <div class="stat"><div class="muted">Decision</div><div>{escape(payload["checkin_decision"])}</div></div>
    </section>
    <h2>Experiments</h2>
    {''.join(cards)}
    <h2>Next stage</h2>
    <div class="card"><p>{escape(payload["next_stage"])}</p></div>
    <footer><p>Reproduce: {reproduce}</p><p>Manifest commits: {commits}</p><p>Source identifiers: {sources}</p></footer>
  </div>
</body>
</html>
"""
