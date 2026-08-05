"""Combined printable readout for ATR Sprints 01–06."""

from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path
from typing import Any

from .sprint04b_readout import write_sprint04b_readout
from .sprint05_readout import write_sprint05_readout
from .sprint06_readout import write_sprint06_readout

EARLY_SPRINT_DIRS = (
    "sprint01_readout",
    "sprint02_readout",
    "sprint03_readout",
    "sprint04_readout",
)

CHECKIN_ROWS = (
    ("1", "M1 Terminal-roll symmetry", "SUPPORTED", "CONTINUE", "Approved"),
    ("2", "M2 Two-dimensional reduction", "SUPPORTED", "CONTINUE", "Approved"),
    ("3", "M3 Architecture comparison", "PARTIALLY SUPPORTED", "CONTINUE WITH CHANGED SCOPE", "Approved"),
    ("4", "M4 Pointing manifold", "SUPPORTED LOCALLY", "CONTINUE WITH CHANGED SCOPE", "Approved"),
    ("4B/04C", "M4 Sequential chart + method audit", "SUPPORTED LOCALLY", "Case A / Pass", "Approved"),
    ("5", "M5 Fiber legitimacy", "SUPPORTED LOCALLY", "CONTINUE WITH CHANGED SCOPE", "Approved"),
    ("6", "M6 Spherical equivalence", "PENDING", "AWAITING REVIEW", "Next"),
)


def assemble_sprint01_06_payload(results_root: Path) -> dict[str, Any]:
    sprints = []
    for dirname in EARLY_SPRINT_DIRS:
        payload = json.loads((results_root / dirname / "readout.json").read_text(encoding="utf-8"))
        payload["_dir"] = dirname
        sprints.append(payload)
    later = (
        ("sprint04b_readout", write_sprint04b_readout),
        ("sprint05_readout", write_sprint05_readout),
        ("sprint06_readout", write_sprint06_readout),
    )
    for dirname, writer in later:
        writer(results_root, results_root / dirname)
        payload = json.loads((results_root / dirname / "readout.json").read_text(encoding="utf-8"))
        payload["_dir"] = dirname
        sprints.append(payload)
    total_pass = sum(int(sprint["pass_count"]) for sprint in sprints)
    total_exp = sum(int(sprint["experiment_count"]) for sprint in sprints)
    return {
        "title": "Aligned terminal-roll — Sprints 01–06",
        "subtitle": "Combined printable readout",
        "date": "2026-08-05",
        "pass_count": total_pass,
        "experiment_count": total_exp,
        "sprints": sprints,
        "checkins": [
            {
                "n": n,
                "milestone": milestone,
                "interpretation": interp,
                "decision": decision,
                "status": status,
            }
            for n, milestone, interp, decision, status in CHECKIN_ROWS
        ],
        "blocked": [
            "ATR_EXP_036 spherical motion equivalence",
            "McCarthy–Soh classification",
            "canonical or architecture-derived fiber",
            "exact UR / URDF / sixr_grashof",
        ],
        "reproduce": [
            "python scripts/generate_atr_sprint01_readout.py",
            "python scripts/generate_atr_sprint02_readout.py",
            "python scripts/generate_atr_sprint03_readout.py",
            "python scripts/generate_atr_sprint04_readout.py",
            "python scripts/validate_pointing_chart.py",
            "python scripts/validate_pointing_fiber.py",
            "python scripts/validate_spherical_candidates.py",
            "python scripts/generate_atr_sprint01_06_printout.py",
        ],
    }


def write_sprint01_06_printout(results_root: Path, out_dir: Path) -> dict[str, Any]:
    payload = assemble_sprint01_06_payload(results_root)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for sprint in payload["sprints"]:
        src_dir = results_root / str(sprint["_dir"])
        items = []
        for exp in sprint["experiments"]:
            copied = []
            figure_keys = list(exp.get("figures") or [])
            if exp.get("residual_figure"):
                figure_keys = [exp["residual_figure"], *figure_keys]
            for rel in figure_keys:
                src = Path(rel)
                if not src.is_absolute():
                    src = src_dir / rel
                if not src.is_file():
                    continue
                dest_name = f"{exp['experiment_id']}_{src.name}"
                shutil.copy2(src, fig_dir / dest_name)
                copied.append(f"figures/{dest_name}")
            item = dict(exp)
            item["figures"] = copied
            items.append(item)
        sprint_copy = dict(sprint)
        sprint_copy["experiments"] = items
        rendered.append(sprint_copy)
    payload["sprints"] = rendered
    (out_dir / "printout.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out_dir / "index.html").write_text(render_sprint01_06_html(payload), encoding="utf-8")
    return payload


def render_sprint01_06_html(payload: dict[str, Any]) -> str:
    checkin_rows = "".join(
        f"<tr><td>{escape(c['n'])}</td><td>{escape(c['milestone'])}</td>"
        f"<td>{escape(c['interpretation'])}</td><td>{escape(c['decision'])}</td>"
        f"<td>{escape(c['status'])}</td></tr>"
        for c in payload["checkins"]
    )
    sprint_sections = []
    for sprint in payload["sprints"]:
        exp_rows = []
        for exp in sprint["experiments"]:
            status = str(exp["status"])
            cls = "pass" if status == "PASS" else ("deferred" if status == "DEFERRED" else "warn")
            verdict = exp.get("verdict")
            observed = exp["observed"]
            if verdict:
                observed = f"[{verdict}] {observed}"
            exp_rows.append(
                "<tr>"
                f"<td>{escape(exp['experiment_id'])}</td>"
                f"<td>{escape(exp['title'])}</td>"
                f"<td class='{cls}'>{escape(status)}</td>"
                f"<td>{escape(exp['expected'])}</td>"
                f"<td>{escape(str(observed))}</td>"
                "</tr>"
            )
        figs = []
        for exp in sprint["experiments"]:
            for src in exp.get("figures", []):
                figs.append(
                    f"<figure><img src='{escape(src)}' alt='{escape(exp['experiment_id'])}' />"
                    f"<figcaption>{escape(exp['experiment_id'])} — {escape(exp['title'])}</figcaption></figure>"
                )
        fig_block = f"<div class='figures'>{''.join(figs)}</div>" if figs else ""
        rationale = sprint.get("checkin_rationale") or sprint.get("claim") or ""
        sprint_sections.append(
            f"""
            <section class="sprint">
              <h2>{escape(sprint['title'])}</h2>
              <p class="muted">{escape(sprint.get('subtitle', ''))} · {escape(sprint.get('sprint_status', ''))} · {escape(sprint.get('milestone', ''))}</p>
              <p><strong>Check-in.</strong> {escape(str(sprint.get('checkin_interpretation', '')))} / {escape(str(sprint.get('checkin_decision', '')))}</p>
              <p>{escape(str(rationale))}</p>
              <table>
                <thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Expected</th><th>Observed</th></tr></thead>
                <tbody>{''.join(exp_rows)}</tbody>
              </table>
              {fig_block}
            </section>
            """
        )
    blocked = "".join(f"<li>{escape(item)}</li>" for item in payload["blocked"])
    reproduce = "".join(f"<code>{escape(cmd)}</code>" for cmd in payload["reproduce"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(payload["title"])}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1b1f24;
      --muted: #5b6570;
      --line: #c9d1d9;
      --panel: #f6f8fa;
      --pass: #0f7b4c;
      --warn: #9a6700;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background: #fff;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; line-height: 1.45; }}
    .shell {{ max-width: 980px; margin: 0 auto; padding: 1.25rem 1.5rem 3rem; }}
    h1 {{ margin: 0.2rem 0 0.4rem; font-size: 1.85rem; }}
    h2 {{ margin: 1.4rem 0 0.4rem; font-size: 1.25rem; page-break-after: avoid; }}
    .muted, figcaption {{ color: var(--muted); font-size: 0.92rem; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem; margin: 1rem 0; }}
    .stat {{ background: var(--panel); border: 1px solid var(--line); padding: 0.7rem 0.8rem; }}
    .stat b {{ display: block; font-size: 1.15rem; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.86rem; margin: 0.6rem 0 1rem; }}
    th, td {{ border: 1px solid var(--line); padding: 0.35rem 0.45rem; vertical-align: top; text-align: left; }}
    th {{ background: var(--panel); }}
    td.pass {{ color: var(--pass); font-weight: 600; }}
    td.deferred, td.warn {{ color: var(--warn); font-weight: 600; }}
    .figures {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
    figure {{ margin: 0; }}
    img {{ width: 100%; height: auto; border: 1px solid var(--line); background: #fff; }}
    .sprint {{ page-break-before: always; }}
    .sprint:first-of-type {{ page-break-before: auto; }}
    code {{ display: inline-block; background: var(--panel); border: 1px solid var(--line); padding: 0.15rem 0.4rem; margin: 0.15rem 0.25rem 0.15rem 0; font-size: 0.82rem; }}
    ul {{ margin-top: 0.3rem; }}
    @media print {{
      .shell {{ max-width: none; padding: 0; }}
      a {{ color: inherit; text-decoration: none; }}
      .sprint {{ break-before: page; }}
      .sprint:first-of-type {{ break-before: auto; }}
      img {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <p class="muted">aligned terminal-roll · {escape(payload["date"])}</p>
    <h1>{escape(payload["title"])}</h1>
    <p class="muted">{escape(payload["subtitle"])}. Experiments through Sprint 06 candidate spherical tests. Check-in 6 is the open gate.</p>
    <section class="stats">
      <div class="stat"><span class="muted">Experiments</span><b>{payload["pass_count"]}/{payload["experiment_count"]}</b></div>
      <div class="stat"><span class="muted">Sprints</span><b>01–06</b></div>
      <div class="stat"><span class="muted">Approved gates</span><b>Check-ins 1–5</b></div>
      <div class="stat"><span class="muted">Open gate</span><b>Check-in 6</b></div>
    </section>
    <h2>Check-in ledger</h2>
    <table>
      <thead><tr><th>#</th><th>Milestone</th><th>Interpretation</th><th>Decision</th><th>Status</th></tr></thead>
      <tbody>{checkin_rows}</tbody>
    </table>
    <h2>Still blocked</h2>
    <ul>{blocked}</ul>
    {''.join(sprint_sections)}
    <section>
      <h2>Reproduce</h2>
      <p>{reproduce}</p>
    </section>
  </div>
</body>
</html>
"""
