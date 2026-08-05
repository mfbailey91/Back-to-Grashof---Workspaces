"""Sprint 03 HTML readout assembly."""

from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path
from typing import Any

S3_IDS = (
    "ATR_EXP_011",
    "ATR_EXP_012",
    "ATR_EXP_013",
    "ATR_EXP_014",
    "ATR_EXP_015",
)

S3_TITLES = {
    "ATR_EXP_011": "Intersecting-pairs Stage A",
    "ATR_EXP_012": "UR-like Stage A",
    "ATR_EXP_013": "Compound-joint principal angles",
    "ATR_EXP_014": "Local N_red step probes",
    "ATR_EXP_015": "Three-architecture comparison",
}

M3_WARNING = (
    "Check-in 3 is approved with changed scope. ATR_EXP_013–014 do not establish "
    "SUUR equivalence. Fibers, spherical four-bars, and exact UR remain blocked."
)


def assemble_sprint03_payload(results_root: Path) -> dict[str, Any]:
    experiments = []
    commits: list[str] = []
    for exp_id in S3_IDS:
        manifest = json.loads((results_root / exp_id / "manifest.json").read_text(encoding="utf-8"))
        commits.append(str(manifest.get("repository_commit", "unknown")))
        figures = (
            sorted((results_root / exp_id / "figures").glob("*.png"))
            if (results_root / exp_id / "figures").is_dir()
            else []
        )
        experiments.append(
            {
                "experiment_id": exp_id,
                "title": S3_TITLES[exp_id],
                "status": manifest["status"],
                "expected": manifest["expected"],
                "observed": manifest["observed"],
                "figures": [str(path) for path in figures],
            }
        )
    pass_count = sum(1 for exp in experiments if exp["status"] == "PASS")
    return {
        "title": "Sprint 03 — Architecture comparison",
        "subtitle": "Stage A survival and local compound-joint probes",
        "brand": "aligned terminal-roll",
        "sprint_status": "Complete / Check-in 3 approved with changed scope",
        "milestone": "M3 — Architecture comparison",
        "warning": M3_WARNING,
        "claim": (
            "Stage A identities survive on IntersectingPairsAligned6R and URLikeAligned6R. "
            "On the intersecting-pair chain, literal UA/UB/RC grouping matches physical "
            "N_red locally by principal angles and short N_red steps."
        ),
        "pass_count": pass_count,
        "experiment_count": len(experiments),
        "checkin_interpretation": "PARTIALLY SUPPORTED",
        "checkin_rationale": (
            "Stage A survives at the named regular configurations of GenericAligned6R, "
            "IntersectingPairsAligned6R, and URLikeAligned6R. ATR_EXP_013 and ATR_EXP_014 "
            "do not independently establish local compound-joint equivalence: the compound "
            "basis is the fixed-roll portion of the same physical J_p null space used to "
            "construct N_red. SUUR remains a proposed exact kinematic regrouping. "
            "IntersectingPairsAligned6R is the continuation benchmark because it "
            "instantiates the workshop architecture, not because those tests selected it."
        ),
        "checkin_decision": "CONTINUE WITH CHANGED SCOPE",
        "human_gate_required": False,
        "recommended_continuation_parent": "IntersectingPairsAligned6R",
        "repository_commits": sorted({c for c in commits if c and c != "unknown"}),
        "experiments": experiments,
        "next_stage": (
            "Check-in 3 is approved with changed scope. Sprint 04: predictor-corrector "
            "continuation of p(q)=p0 with q6 constant on IntersectingPairsAligned6R, then "
            "URLikeAligned6R. Before interpreting continuation through SUUR, add an explicit "
            "coordinate-map/closure test, away-from-home pair persistence, a nonintersecting "
            "negative control, and committed source identifiers."
        ),
        "reproduce": [
            "python scripts/validate_architecture_comparison.py",
            "python scripts/generate_atr_sprint03_readout.py",
        ],
    }


def write_sprint03_readout(results_root: Path, out_dir: Path) -> dict[str, Any]:
    payload = assemble_sprint03_payload(results_root)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    rendered_exps = []
    for exp in payload["experiments"]:
        copied = []
        for src in exp["figures"]:
            src_path = Path(src)
            dest_name = f"{exp['experiment_id']}_{src_path.name}"
            shutil.copy2(src_path, fig_dir / dest_name)
            copied.append(f"figures/{dest_name}")
        item = dict(exp)
        item["figures"] = copied
        rendered_exps.append(item)
    payload["experiments"] = rendered_exps
    (out_dir / "readout.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out_dir / "index.html").write_text(render_sprint03_html(payload), encoding="utf-8")
    return payload


def render_sprint03_html(payload: dict[str, Any]) -> str:
    cards = []
    for exp in payload["experiments"]:
        imgs = "".join(
            f'<img src="{escape(src)}" alt="{escape(exp["experiment_id"])} figure" />' for src in exp["figures"]
        )
        cards.append(
            f"""
            <article class="card">
              <h3>{escape(exp["experiment_id"])} — {escape(exp["title"])}
                <span class="badge pass">{escape(exp["status"])}</span></h3>
              <p><strong>Expected.</strong> {escape(exp["expected"])}</p>
              <p><strong>Observed.</strong> {escape(exp["observed"])}</p>
              {imgs}
            </article>
            """
        )
    reproduce = "".join(f"<code>{escape(cmd)}</code>" for cmd in payload["reproduce"])
    commits = ", ".join(escape(c[:12]) for c in payload["repository_commits"]) or "unknown"
    gate = "human gate still required" if payload["human_gate_required"] else "authorized"
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
      background: radial-gradient(ellipse 80% 50% at 10% -10%, #1e3a42 0%, transparent 55%),
                  linear-gradient(160deg, var(--bg0), var(--bg1));
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
    <section class="claim"><strong>Check-in 3 interpretation.</strong> {escape(payload["checkin_interpretation"])}.
      <p>{escape(payload["checkin_rationale"])}</p></section>
    <section class="stats">
      <div class="stat"><div class="muted">Experiments</div><div>{payload["pass_count"]}/{payload["experiment_count"]} PASS</div></div>
      <div class="stat"><div class="muted">Check-in 3</div><div>{escape(payload["checkin_interpretation"])}</div></div>
      <div class="stat"><div class="muted">Decision</div><div>{escape(payload["checkin_decision"])}</div><div class="muted">{escape(gate)}</div></div>
      <div class="stat"><div class="muted">Recommended parent</div><div>{escape(payload["recommended_continuation_parent"])}</div><div class="muted">not auto-selected</div></div>
    </section>
    <h2>Experiments</h2>
    {''.join(cards)}
    <h2>Next stage</h2>
    <div class="card"><p>{escape(payload["next_stage"])}</p></div>
    <footer><p>Reproduce: {reproduce}</p><p>Manifest commits: {commits}</p></footer>
  </div>
</body>
</html>
"""
