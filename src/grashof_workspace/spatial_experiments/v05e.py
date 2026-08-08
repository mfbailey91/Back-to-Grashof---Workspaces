"""Active V05E runner: near-aligned RR→U rejection + false-U task error.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05e \\
      --outdir results/kinematic_decomposition/v05e
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .axis_aggregation import (
    ORTHOGONALITY_DOT_TOL,
    PAIR_DISTANCE_TOL_M,
    PARALLEL_CROSS_TOL,
    FalseUTaskErrorReport,
    detect_exact_u_pairs,
    measure_false_u_task_error,
)
from .decomposition_certificate import DecompositionCertificate, issue_axis_aggregation_certificate
from .v05_corpus import (
    Spatial4RCorpusEntry,
    build_exact_u_pair_4r,
    build_generic_4r,
    build_near_aligned_u_pair_4r,
)


def _plot_geometry_vs_tols(cert: DecompositionCertificate, outpath: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    cands = cert.candidates
    idx = [c.pair_index for c in cands]
    dists = [max(c.distance_m, 1e-18) for c in cands]
    dots = [max(c.orthogonality_abs_dot, 1e-18) for c in cands]

    axes[0].semilogy(idx, dists, "o-", label="pair distance")
    axes[0].axhline(PAIR_DISTANCE_TOL_M, color="#c40", ls="--", label=f"distance tol={PAIR_DISTANCE_TOL_M:g}")
    axes[0].set_title(f"{cert.source_chain_id}: distance vs exact tol")
    axes[0].set_xlabel("pair index")
    axes[0].set_xticks(idx)
    axes[0].legend(fontsize="small")

    axes[1].semilogy(idx, dots, "s-", color="#06a", label="|w·w'|")
    axes[1].axhline(ORTHOGONALITY_DOT_TOL, color="#c40", ls="--", label=f"orth tol={ORTHOGONALITY_DOT_TOL:g}")
    axes[1].set_title("orthogonality vs exact tol")
    axes[1].set_xlabel("pair index")
    axes[1].set_xticks(idx)
    axes[1].legend(fontsize="small")

    figure.suptitle(f"V05E geometric tolerances — certificate={cert.status}")
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _plot_false_u_residuals(report: FalseUTaskErrorReport, outpath: Path) -> None:
    figure, ax = plt.subplots(figsize=(7.2, 4.4))
    labels = ["seed ||Δp||", "seed ||ΔR||_F", "seed ||Δd||", "fiber max ||Δp||", "fiber max ||ΔR||_F", "fiber max ||Δd||"]
    vals = [
        max(report.seed_position_residual_m, 1e-18),
        max(report.seed_rotation_frobenius, 1e-18),
        max(report.seed_pointing_residual, 1e-18),
        max(report.fiber_max_position_residual_m, 1e-18),
        max(report.fiber_max_rotation_frobenius, 1e-18),
        max(report.fiber_max_pointing_residual, 1e-18),
    ]
    ax.semilogy(range(len(labels)), vals, "o-", color="#c40")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("residual")
    ax.set_title(
        f"False-U surrogate task error — {report.architecture_id}\n"
        f"(diagnostic only; dist={report.source_distance_m:.2e}, |dot|={report.source_orthogonality_abs_dot:.2e})"
    )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def render_v05e_html(
    rows: list[tuple[DecompositionCertificate, FalseUTaskErrorReport | None]],
    *,
    figures: dict[str, str],
) -> str:
    table_rows = []
    for cert, report in rows:
        task = "—"
        if report is not None:
            task = f"{report.fiber_max_position_residual_m:.3e}"
        table_rows.append(
            "<tr>"
            f"<td><code>{cert.source_chain_id}</code></td>"
            f"<td><code>{cert.status}</code></td>"
            f"<td>{cert.closure_residuals}</td>"
            f"<td>{task}</td>"
            "</tr>"
        )
    figure_blocks = []
    for label, rel in figures.items():
        figure_blocks.append(
            f'<h3>{label}</h3><p><img src="{rel}" alt="{label}" style="max-width: 720px;"></p>'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Active V05E — Near-Aligned Rejection</title>
<style>
  body {{ font-family: Georgia, "Times New Roman", serif; max-width: 920px; margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.45; color: #1a1a1a; }}
  h1, h2, h3 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.75rem 0 1rem; }}
  th, td {{ border: 1px solid #bbb; padding: 0.4rem 0.55rem; text-align: left; font-size: 0.88em; }}
  th {{ background: #f3f3f3; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.88em; }}
  .note {{ background: #f7f4ea; border-left: 3px solid #c4a35a; padding: 0.65rem 0.85rem; margin: 1rem 0; }}
</style>
</head>
<body>
<h1>Active V05E — Near-Aligned Rejection</h1>
<p>
Near-aligned consecutive RR pairs must be rejected as exact <code>U_phys</code> aggregation.
Declared exact geometric tolerances:
<code>distance ≤ {PAIR_DISTANCE_TOL_M:g}</code>,
<code>|w·w'| ≤ {ORTHOGONALITY_DOT_TOL:g}</code>,
<code>||w×w'|| ≥ {PARALLEL_CROSS_TOL:g}</code>.
</p>
<div class="note">
<strong>Gate note.</strong>
<code>near_aligned_u_pair_4r</code> yields <code>DecompositionCertificate</code> status
<code>REJECTED</code>. A forced exact-U surrogate quantifies source-versus-surrogate
FK / fiber <em>task error</em> as diagnostic evidence only
(<code>false_u_surrogate</code>), not an <code>APPROXIMATE</code> certificate.
<code>exact_u_pair_4r</code> remains the V05D control that still certifies.
</div>
<h2>Certificates and false-U diagnostics</h2>
<table>
<tr><th>Architecture</th><th>Certificate</th><th>Closure / geometry residuals</th><th>False-U max ||Δp||</th></tr>
{''.join(table_rows)}
</table>
<h2>Figures</h2>
{''.join(figure_blocks)}
<h2>Deferred</h2>
<ul>
<li>Non-proximal near-aligned suites</li>
<li>V06 spatial 5R parent</li>
</ul>
</body>
</html>
"""


def build_v05e_readout(
    outdir: Path,
    *,
    n_fiber_steps: int = 16,
    fiber_step_size: float = 0.04,
) -> list[tuple[DecompositionCertificate, FalseUTaskErrorReport | None]]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    entries: tuple[Spatial4RCorpusEntry, ...] = (
        build_near_aligned_u_pair_4r(),
        build_exact_u_pair_4r(),
        build_generic_4r(),
    )
    rows: list[tuple[DecompositionCertificate, FalseUTaskErrorReport | None]] = []
    figures: dict[str, str] = {}

    for entry in entries:
        cert = issue_axis_aggregation_certificate(
            entry.model,
            entry.regular_q,
            n_fiber_steps=n_fiber_steps,
            fiber_step_size=fiber_step_size,
        )
        report: FalseUTaskErrorReport | None = None
        stem = entry.model.architecture_id
        geo = figures_dir / f"v05e_{stem}_geometry_vs_tol.png"
        _plot_geometry_vs_tols(cert, geo)
        figures[f"{stem} geometry vs tol"] = str(geo.relative_to(outdir))

        if stem == "near_aligned_u_pair_4r":
            report = measure_false_u_task_error(
                entry.model,
                entry.regular_q,
                n_fiber_steps=n_fiber_steps,
                fiber_step_size=fiber_step_size,
            )
            err = figures_dir / f"v05e_{stem}_false_u_task_error.png"
            _plot_false_u_residuals(report, err)
            figures[f"{stem} false-U task error"] = str(err.relative_to(outdir))
        rows.append((cert, report))

    payload = {
        "sprint": "V05E",
        "program": "kinematic_decomposition",
        "operation": "axis_aggregation",
        "exact_tolerances": {
            "PAIR_DISTANCE_TOL_M": PAIR_DISTANCE_TOL_M,
            "ORTHOGONALITY_DOT_TOL": ORTHOGONALITY_DOT_TOL,
            "PARALLEL_CROSS_TOL": PARALLEL_CROSS_TOL,
        },
        "gate_note": (
            "Active V05E near-aligned rejection; false_u_surrogate is diagnostic-only."
        ),
        "results": [
            {
                "certificate": cert.to_json_dict(),
                "false_u_task_error": None if report is None else report.to_json_dict(),
                "exact_u_candidates_home": [
                    c.to_json_dict() for c in detect_exact_u_pairs(entry.model)
                ],
            }
            for (cert, report), entry in zip(rows, entries, strict=True)
        ],
    }
    (data_dir / "v05e_near_aligned_rejection.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    html = render_v05e_html(rows, figures=figures)
    (outdir / "sprint_v05e_near_aligned_rejection.html").write_text(html, encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Active V05E near-aligned rejection readout")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05e"),
    )
    parser.add_argument("--n-fiber-steps", type=int, default=16)
    parser.add_argument("--fiber-step-size", type=float, default=0.04)
    args = parser.parse_args(argv)
    rows = build_v05e_readout(
        args.outdir,
        n_fiber_steps=args.n_fiber_steps,
        fiber_step_size=args.fiber_step_size,
    )
    for cert, report in rows:
        extra = ""
        if report is not None:
            extra = f" | false_u max||Δp||={report.fiber_max_position_residual_m:.3e}"
        print(f"{cert.source_chain_id}: {cert.status}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
