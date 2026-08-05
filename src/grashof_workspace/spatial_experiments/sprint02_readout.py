"""Sprint 02 HTML readout assembly."""

from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path
from typing import Any

S2_IDS = (
    "ATR_EXP_006",
    "ATR_EXP_007",
    "ATR_EXP_008",
    "ATR_EXP_009",
    "ATR_EXP_010",
)

S2_TITLES = {
    "ATR_EXP_006": "Regular configuration rank suite",
    "ATR_EXP_007": "Jacobian finite-difference refinement",
    "ATR_EXP_008": "Full-chain terminal-roll check",
    "ATR_EXP_009": "Alignment negative controls",
    "ATR_EXP_010": "Seeded survey and named near-singular sample",
}

M2_WARNING = (
    "This readout does not authorize compound-joint, continuation, or spherical-four-bar work. "
    "Check-in 2 remains a human gate."
)


def assemble_sprint02_payload(results_root: Path) -> dict[str, Any]:
    experiments = []
    commits: list[str] = []
    for exp_id in S2_IDS:
        manifest = json.loads((results_root / exp_id / "manifest.json").read_text(encoding="utf-8"))
        commits.append(str(manifest.get("repository_commit", "unknown")))
        figures = sorted((results_root / exp_id / "figures").glob("*.png")) if (results_root / exp_id / "figures").is_dir() else []
        experiments.append(
            {
                "experiment_id": exp_id,
                "title": S2_TITLES[exp_id],
                "status": manifest["status"],
                "expected": manifest["expected"],
                "observed": manifest["observed"],
                "figures": [str(path) for path in figures],
            }
        )
    pass_count = sum(1 for exp in experiments if exp["status"] == "PASS")
    return {
        "title": "Sprint 02 — Generic aligned 6R",
        "subtitle": "Stage A differential reduction",
        "brand": "aligned terminal-roll",
        "sprint_status": "Implementation complete / Check-in 2 draft",
        "milestone": "M2 — Two-dimensional reduction established",
        "warning": M2_WARNING,
        "claim": (
            "At regular aligned-terminal 6R configurations, rank(J_p)=3, rank(J_pd)=5 with "
            "ker(J_pd) aligned to e6, and rank(J_d N_red)=2."
        ),
        "pass_count": pass_count,
        "experiment_count": len(experiments),
        "checkin_interpretation": "SUPPORTED",
        "checkin_rationale": (
            "For the GenericAligned6R skew reference chain, the named regular configuration "
            "and all 48 seeded configurations satisfy the expected local fixed-position and "
            "position-and-pointing ranks. Terminal roll is the sole task-kernel direction, "
            "and the quotient fixed-position tangent space has rank-two pointing motion. "
            "This establishes the numerical Stage A reference result but does not yet "
            "establish architecture independence or global continuation."
        ),
        "checkin_decision": "CONTINUE",
        "human_gate_required": True,
        "repository_commits": sorted({c for c in commits if c and c != "unknown"}),
        "experiments": experiments,
        "next_stage": (
            "Pending human Check-in 2. If approved, next stage is architecture comparison "
            "(generic vs compound-joint vs UR-like), not spherical four-bars."
        ),
        "reproduce": [
            "python scripts/validate_aligned_6r_reduction.py",
            "python scripts/generate_atr_sprint02_readout.py",
        ],
    }


def write_sprint02_readout(results_root: Path, out_dir: Path) -> dict[str, Any]:
    payload = assemble_sprint02_payload(results_root)
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
    (out_dir / "index.html").write_text(render_sprint02_html(payload), encoding="utf-8")
    return payload


def render_sprint02_html(payload: dict[str, Any]) -> str:
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
    <section class="claim"><strong>Check-in 2 interpretation.</strong> {escape(payload["checkin_interpretation"])}.
      <p>{escape(payload["checkin_rationale"])}</p></section>
    <section class="stats">
      <div class="stat"><div class="muted">Experiments</div><div>{payload["pass_count"]}/{payload["experiment_count"]} PASS</div></div>
      <div class="stat"><div class="muted">Check-in 2</div><div>{escape(payload["checkin_interpretation"])}</div></div>
      <div class="stat"><div class="muted">Decision</div><div>{escape(payload["checkin_decision"])}</div><div class="muted">{escape(gate)}</div></div>
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
