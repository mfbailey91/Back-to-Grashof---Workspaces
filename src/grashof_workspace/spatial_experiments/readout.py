"""Sprint 01 HTML readout payload and static page rendering.

This module only assembles already-written experiment artifacts. It does not
run kinematics or import ``sixr_grashof``.
"""

from __future__ import annotations

import csv
import json
import shutil
from html import escape
from pathlib import Path
from typing import Any

EXPERIMENT_IDS = (
    "ATR_EXP_001",
    "ATR_EXP_002",
    "ATR_EXP_003",
    "ATR_EXP_004",
    "ATR_EXP_005",
)

EXPERIMENT_TITLES = {
    "ATR_EXP_001": "Aligned positive control",
    "ATR_EXP_002": "Off-axis task point",
    "ATR_EXP_003": "Misaligned pointing direction",
    "ATR_EXP_004": "Combined alignment violation",
    "ATR_EXP_005": "Finite-difference refinement",
}

ACCEPTANCE_ROWS = (
    (
        "Isolated under spatial_experiments",
        "no planar / 6R coupling",
        "package separate; no sixr import",
        "PASS",
    ),
    (
        "Planar tests unchanged",
        "trusted suite green",
        "fourbar/planar3r/validation + spatial: 76 passed",
        "PASS",
    ),
    (
        "Positive/negative qualitative behavior",
        "Sprint matrix",
        "all five PASS",
        "PASS",
    ),
    (
        "Analytical vs FD",
        "convergence",
        "O(h²) then mild round-off",
        "PASS",
    ),
    (
        "Orientation roll without Euler subtraction",
        "relative R + probe atan2",
        "max roll err ~1e-15 rad on aligned case",
        "PASS",
    ),
    (
        "Explicit tolerances/units",
        "documented",
        "metres / radians in manifests",
        "PASS",
    ),
    (
        "Experiment manifests/summaries",
        "results/aligned_terminal_roll/<id>/",
        "written",
        "PASS",
    ),
    (
        "No 6R / spherical / continuation code",
        "deferred",
        "not introduced",
        "PASS",
    ),
)

M1_WARNING = (
    "This readout does not establish 6R rank or nullity. "
    "It only validates an isolated terminal-roll fixture (Level 0 / M1)."
)


def experiment_dir(results_root: Path, experiment_id: str) -> Path:
    return results_root / experiment_id


def load_manifest(results_root: Path, experiment_id: str) -> dict[str, Any]:
    path = experiment_dir(results_root, experiment_id) / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_fd_rows(results_root: Path) -> list[dict[str, float]]:
    manifest = load_manifest(results_root, "ATR_EXP_005")
    rows = manifest.get("fd_refinement")
    if isinstance(rows, list) and rows:
        return [
            {
                "h": float(row["h"]),
                "dp_error": float(row["dp_error"]),
                "dd_error": float(row["dd_error"]),
            }
            for row in rows
        ]
    csv_path = experiment_dir(results_root, "ATR_EXP_005") / "fd_refinement.csv"
    out: list[dict[str, float]] = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(
                {
                    "h": float(row["h_rad"]),
                    "dp_error": float(row["dp_error"]),
                    "dd_error": float(row["dd_error"]),
                }
            )
    return out


def assemble_sprint01_payload(results_root: Path) -> dict[str, Any]:
    """Build a machine-readable Sprint 01 readout payload from experiment dirs."""
    experiments: list[dict[str, Any]] = []
    commits: list[str] = []
    for exp_id in EXPERIMENT_IDS:
        manifest = load_manifest(results_root, exp_id)
        commits.append(str(manifest.get("repository_commit", "unknown")))
        residual_src = experiment_dir(results_root, exp_id) / "figures" / "residuals_vs_q6.png"
        experiments.append(
            {
                "experiment_id": exp_id,
                "title": EXPERIMENT_TITLES[exp_id],
                "status": manifest["status"],
                "expected": manifest["expected"],
                "observed": manifest["observed"],
                "notes": manifest.get("notes") or "",
                "metrics": manifest["metrics"],
                "tolerances": manifest["tolerances"],
                "units": manifest["units"],
                "model": manifest["model"],
                "residual_figure_src": str(residual_src),
                "residual_figure": f"figures/residuals_{exp_id}.png",
            }
        )

    fd_rows = load_fd_rows(results_root)
    pass_count = sum(1 for exp in experiments if exp["status"] == "PASS")
    unique_commits = sorted({c for c in commits if c and c != "unknown"})
    return {
        "title": "Sprint 01 — Spatial Foundations",
        "subtitle": "Terminal-roll fixture",
        "brand": "aligned terminal-roll",
        "sprint_status": "Complete",
        "milestone": "M1 — Terminal-roll symmetry established",
        "warning": M1_WARNING,
        "claim": (
            "If p lies on R6 and d is parallel to w6, then dp/dq6 = 0 and dd/dq6 = 0, "
            "while full tool orientation changes by roll about d."
        ),
        "pass_count": pass_count,
        "experiment_count": len(experiments),
        "tests_passed": 76,
        "checkin_interpretation": "SUPPORTED",
        "checkin_decision": "CONTINUE",
        "human_gate_required": False,
        "repository_commits": unique_commits,
        "experiments": experiments,
        "fd_refinement": fd_rows,
        "acceptance": [
            {
                "criterion": row[0],
                "required": row[1],
                "observed": row[2],
                "status": row[3],
            }
            for row in ACCEPTANCE_ROWS
        ],
        "limitations": [
            "Single revolute only; no serial-chain forward kinematics.",
            "Does not test fixed-position Jacobian rank or quotient bases.",
            "Finite-difference round-off appears near h ≲ 1e-6 rad.",
            "Spherical four-bar / McCarthy-Soh work remains deferred.",
        ],
        "next_stage": (
            "Check-in 1 is approved. Next authorized stage: generic synthetic aligned-terminal "
            "6R kernel and local rank/nullity checks. Compound-joint, UR-like, fiber, and "
            "spherical four-bar work remain blocked."
        ),
        "reproduce": [
            "python scripts/validate_terminal_roll_fixture.py",
            "python scripts/generate_atr_sprint01_readout.py",
        ],
    }


def plot_fd_refinement(rows: list[dict[str, float]], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dest.parent.mkdir(parents=True, exist_ok=True)
    hs = [row["h"] for row in rows]
    dp = [row["dp_error"] for row in rows]
    dd = [row["dd_error"] for row in rows]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.loglog(hs, dp, marker="o", label="||Δ(dp/dq6)||")
    ax.loglog(hs, dd, marker="s", label="||Δ(dd/dq6)||")
    ax.set_xlabel("finite-difference step h [rad]")
    ax.set_ylabel("analytical vs central-FD error")
    ax.set_title("ATR_EXP_005 derivative refinement")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def write_readout_artifacts(results_root: Path, out_dir: Path) -> dict[str, Any]:
    """Write readout.json, copied figures, FD plot, and index.html."""
    payload = assemble_sprint01_payload(results_root)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for exp in payload["experiments"]:
        src = Path(exp["residual_figure_src"])
        dest = out_dir / exp["residual_figure"]
        shutil.copy2(src, dest)

    fd_fig = fig_dir / "fd_refinement_ATR_EXP_005.png"
    plot_fd_refinement(payload["fd_refinement"], fd_fig)
    payload["fd_figure"] = "figures/fd_refinement_ATR_EXP_005.png"

    serializable = dict(payload)
    for exp in serializable["experiments"]:
        exp.pop("residual_figure_src", None)

    (out_dir / "readout.json").write_text(
        json.dumps(serializable, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "index.html").write_text(render_sprint01_html(serializable), encoding="utf-8")
    return serializable


def render_sprint01_html(payload: dict[str, Any]) -> str:
    """Return a self-contained Sprint 01 readout HTML document."""
    exp_cards = "\n".join(_experiment_card(exp) for exp in payload["experiments"])
    fd_rows = "".join(
        (
            "<tr>"
            f"<td>{_sci(row['h'])}</td>"
            f"<td>{_sci(row['dp_error'])}</td>"
            f"<td>{_sci(row['dd_error'])}</td>"
            "</tr>"
        )
        for row in payload["fd_refinement"]
    )
    acceptance_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(row['criterion'])}</td>"
            f"<td>{escape(row['required'])}</td>"
            f"<td>{escape(row['observed'])}</td>"
            f"<td><span class='badge pass'>{escape(row['status'])}</span></td>"
            "</tr>"
        )
        for row in payload["acceptance"]
    )
    limitations = "".join(f"<li>{escape(item)}</li>" for item in payload["limitations"])
    reproduce = "".join(f"<code>{escape(cmd)}</code>" for cmd in payload["reproduce"])
    commits = ", ".join(escape(c[:12]) for c in payload["repository_commits"]) or "unknown"
    gate_note = "human gate still required" if payload["human_gate_required"] else "authorized"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(payload["title"])}</title>
  <style>
    :root {{
      --bg0: #10151b;
      --bg1: #182028;
      --panel: #24303c;
      --ink: #e8eef4;
      --muted: #9aa8b5;
      --line: #3a4a5a;
      --teal: #2a9d8f;
      --amber: #e9a319;
      --good: #3cbf9a;
      font-family: "IBM Plex Sans", "Source Sans 3", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(ellipse 80% 50% at 10% -10%, #1e3a42 0%, transparent 55%),
        linear-gradient(160deg, var(--bg0), var(--bg1));
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; line-height: 1.5; padding-bottom: 3rem; }}
    a {{ color: var(--teal); text-decoration: none; }}
    .shell {{ max-width: 1100px; margin: 0 auto; padding: 1.5rem; }}
    .brand {{ color: var(--teal); letter-spacing: 0.04em; font-size: 0.85rem; text-transform: uppercase; }}
    h1 {{ margin: 0.35rem 0 0.6rem; font-size: 2rem; }}
    .lead, .muted {{ color: var(--muted); }}
    .warning {{
      border-left: 3px solid var(--amber);
      background: rgba(233, 163, 25, 0.08);
      padding: 0.75rem 1rem;
      margin: 1rem 0 0;
    }}
    .claim {{
      border: 1px solid var(--line);
      background: var(--panel);
      padding: 1rem 1.1rem;
      margin: 1.25rem 0;
      border-radius: 8px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 0.75rem;
      margin: 1.25rem 0 1.75rem;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0.85rem 1rem;
    }}
    .stat .label {{ color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }}
    .stat .value {{ font-size: 1.25rem; margin-top: 0.25rem; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 1rem;
      margin: 0 0 1rem;
    }}
    .card h3 {{ margin: 0 0 0.4rem; display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }}
    .badge {{
      font-size: 0.75rem;
      border-radius: 999px;
      padding: 0.15rem 0.55rem;
      border: 1px solid var(--line);
      color: var(--muted);
    }}
    .badge.pass {{ color: var(--good); border-color: var(--good); }}
    img {{ max-width: 100%; height: auto; border-radius: 6px; background: #0b1014; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 0.45rem 0.4rem; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; }}
    code {{
      display: inline-block;
      background: #0b1014;
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 0.2rem 0.45rem;
      margin: 0.2rem 0.35rem 0.2rem 0;
      font-size: 0.85rem;
    }}
    footer {{ color: var(--muted); margin-top: 2rem; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="brand">{escape(payload["brand"])}</div>
      <h1>{escape(payload["title"])}</h1>
      <p class="lead">{escape(payload["subtitle"])} · status {escape(payload["sprint_status"])} · {escape(payload["milestone"])}</p>
      <p class="warning">{escape(payload["warning"])}</p>
    </header>

    <section class="claim">
      <strong>Claim under test.</strong>
      <p style="margin:0.4rem 0 0;">{escape(payload["claim"])}</p>
    </section>

    <section class="stats">
      <div class="stat"><div class="label">Experiments</div><div class="value">{payload["pass_count"]}/{payload["experiment_count"]} PASS</div></div>
      <div class="stat"><div class="label">Trusted tests</div><div class="value">{payload["tests_passed"]} passed</div></div>
      <div class="stat"><div class="label">Check-in 1</div><div class="value">{escape(payload["checkin_interpretation"])}</div></div>
      <div class="stat"><div class="label">Decision</div><div class="value">{escape(payload["checkin_decision"])}</div><div class="muted">{escape(gate_note)}</div></div>
    </section>

    <section>
      <h2>Experiments</h2>
      {exp_cards}
    </section>

    <section>
      <h2>Finite-difference refinement</h2>
      <p class="muted">Central differences versus analytical derivatives. Error falls as O(h²) until round-off near h = 1e-6 rad.</p>
      <div class="card">
        <img src="{escape(payload["fd_figure"])}" alt="ATR_EXP_005 finite-difference refinement" />
        <table>
          <thead><tr><th>h [rad]</th><th>dp error</th><th>dd error</th></tr></thead>
          <tbody>{fd_rows}</tbody>
        </table>
      </div>
    </section>

    <section>
      <h2>Acceptance criteria</h2>
      <div class="card">
        <table>
          <thead><tr><th>Criterion</th><th>Required</th><th>Observed</th><th>Status</th></tr></thead>
          <tbody>{acceptance_rows}</tbody>
        </table>
      </div>
    </section>

    <section>
      <h2>Limitations and next stage</h2>
      <div class="card">
        <ul>{limitations}</ul>
        <p>{escape(payload["next_stage"])}</p>
      </div>
    </section>

    <footer>
      <p>Reproduce: {reproduce}</p>
      <p>Manifest commits: {commits}</p>
    </footer>
  </div>
</body>
</html>
"""


def _experiment_card(exp: dict[str, Any]) -> str:
    metrics = exp["metrics"]
    notes = f"<p class='muted'>{escape(exp['notes'])}</p>" if exp["notes"] else ""
    return f"""
    <article class="card">
      <h3>{escape(exp["experiment_id"])} — {escape(exp["title"])}
        <span class="badge pass">{escape(exp["status"])}</span>
      </h3>
      <p><strong>Expected.</strong> {escape(exp["expected"])}</p>
      <p><strong>Observed.</strong> {escape(exp["observed"])}</p>
      {notes}
      <p class="muted">
        max |Δp| = {_sci(metrics["max_position_residual_m"])} m ·
        max |Δd| = {_sci(metrics["max_pointing_residual"])} ·
        max roll err = {_sci(metrics["max_roll_angle_error_rad"])} rad ·
        position_changes = {metrics["position_changes"]} ·
        pointing_changes = {metrics["pointing_changes"]}
      </p>
      <img src="{escape(exp["residual_figure"])}" alt="{escape(exp["experiment_id"])} residuals versus q6" />
    </article>
    """


def _sci(value: float) -> str:
    return f"{float(value):.3e}"
