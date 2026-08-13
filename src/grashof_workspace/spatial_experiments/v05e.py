"""Active V05E runner: exact-U rejection, tolerance boundary, and false-U error.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05e \
      --outdir results/kinematic_decomposition/v05e
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

from .axis_aggregation import (
    ORTHOGONALITY_DOT_TOL,
    PAIR_DISTANCE_TOL_M,
    PARALLEL_CROSS_TOL,
    FalseUTaskErrorReport,
    ToleranceBoundaryCase,
    evaluate_u_boundary_suite,
    measure_false_u_task_error,
)
from .decomposition_certificate import DecompositionCertificate, issue_axis_aggregation_certificate
from .v05_corpus import (
    Spatial4RCorpusEntry,
    build_exact_u_pair_4r,
    build_generic_4r,
    build_near_aligned_u_pair_4r,
)


def _plot_boundary_suite(cases: tuple[ToleranceBoundaryCase, ...], outpath: Path) -> None:
    figure, axis = plt.subplots(figsize=(7.0, 5.8))
    for case in cases:
        marker = "o" if case.accepted else "x"
        axis.scatter(
            case.distance_scale,
            case.orthogonality_scale,
            marker=marker,
            s=55,
            label=None,
        )
    axis.axvline(1.0, ls="--", linewidth=1.0)
    axis.axhline(1.0, ls="--", linewidth=1.0)
    axis.set_xlabel("distance / distance tolerance")
    axis.set_ylabel("|w·w'| / orthogonality tolerance")
    axis.set_title("Exact-U tolerance boundary: o=accepted, x=rejected")
    axis.set_xticks((0.0, 0.5, 1.0, 2.0, 10.0))
    axis.set_yticks((0.0, 0.5, 1.0, 2.0, 10.0))
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _plot_false_u_residuals(report: FalseUTaskErrorReport, outpath: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.0, 4.6))
    labels = (
        "seed Δp",
        "seed ΔR",
        "seed Δd",
        "fiber max Δp",
        "fiber max ΔR",
        "fiber max Δd",
    )
    values = (
        max(report.seed_position_residual_m, 1e-18),
        max(report.seed_rotation_frobenius, 1e-18),
        max(report.seed_pointing_residual, 1e-18),
        max(report.fiber_max_position_residual_m, 1e-18),
        max(report.fiber_max_rotation_frobenius, 1e-18),
        max(report.fiber_max_pointing_residual, 1e-18),
    )
    axis.semilogy(range(len(labels)), values, "o-")
    axis.set_xticks(range(len(labels)))
    axis.set_xticklabels(labels, rotation=25, ha="right")
    axis.set_title("Forced exact-U same-coordinate task error")
    axis.set_ylabel("residual")
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def render_v05e_html(
    rows: list[tuple[DecompositionCertificate, FalseUTaskErrorReport | None]],
    boundary_cases: tuple[ToleranceBoundaryCase, ...],
    *,
    figures: dict[str, str],
) -> str:
    table_rows = []
    for certificate, report in rows:
        max_position = "—" if report is None else f"{report.fiber_max_position_residual_m:.3e}"
        table_rows.append(
            "<tr>"
            f"<td><code>{certificate.source_chain_id}</code></td>"
            f"<td><code>{certificate.axis_aggregation_status}</code></td>"
            f"<td><code>{certificate.closed_mechanism_status}</code></td>"
            f"<td><code>{certificate.status}</code></td>"
            f"<td>{max_position}</td>"
            "</tr>"
        )
    accepted = sum(case.accepted for case in boundary_cases)
    figure_blocks = "".join(
        f'<h3>{label}</h3><p><img src="{rel}" alt="{label}" style="max-width:720px"></p>'
        for label, rel in figures.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>V05E — U Boundary Audit</title>
<style>body{{font-family:Georgia,serif;max-width:980px;margin:2rem auto;line-height:1.45}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:.4rem;text-align:left}}code{{font-family:ui-monospace,monospace}}.note{{background:#f7f4ea;border-left:3px solid #c4a35a;padding:.7rem}}</style>
</head><body>
<h1>V05E — Near-Aligned Rejection and Tolerance Boundary</h1>
<div class="note"><strong>Audit correction.</strong> The original planted near miss remains an easy exterior regression. A tolerance-relative grid now tests 0, 0.5×, 1×, 2×, and 10× the declared distance and orthogonality tolerances. The false-U comparison is diagnostic only and does not become an approximate decomposition certificate.</div>
<p>Exact tolerances: distance ≤ <code>{PAIR_DISTANCE_TOL_M:g} m</code>, |w·w'| ≤ <code>{ORTHOGONALITY_DOT_TOL:g}</code>, and ||w×w'|| ≥ <code>{PARALLEL_CROSS_TOL:g}</code>.</p>
<table><tr><th>Source</th><th>Axis aggregation</th><th>Closed mechanism</th><th>Overall</th><th>False-U max Δp [m]</th></tr>{''.join(table_rows)}</table>
<p>Boundary suite: {accepted}/{len(boundary_cases)} accepted. Values at or below both exact thresholds should be accepted, subject to floating-point tolerance; values above either threshold should be rejected.</p>
<h2>Figures</h2>{figure_blocks}
<h2>Remaining limitation</h2><p>The forced surrogate is compared at the source joint coordinates. An independently solved surrogate fixed-position component remains a later approximation study.</p>
</body></html>"""


def build_v05e_readout(
    outdir: Path,
    *,
    n_fiber_steps: int = 24,
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
    for entry in entries:
        certificate = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
        report = None
        if entry.model.architecture_id == "near_aligned_u_pair_4r":
            report = measure_false_u_task_error(
                entry.model,
                entry.regular_q,
                n_fiber_steps=n_fiber_steps,
                fiber_step_size=fiber_step_size,
            )
        rows.append((certificate, report))

    exact_entry = build_exact_u_pair_4r()
    boundary_cases = evaluate_u_boundary_suite(exact_entry.model)
    figures: dict[str, str] = {}
    boundary_path = figures_dir / "v05e_tolerance_boundary.png"
    _plot_boundary_suite(boundary_cases, boundary_path)
    figures["Tolerance-relative exact-U boundary"] = str(boundary_path.relative_to(outdir))

    near_report = next(report for _certificate, report in rows if report is not None)
    assert near_report is not None
    error_path = figures_dir / "v05e_false_u_task_error.png"
    _plot_false_u_residuals(near_report, error_path)
    figures["Near-miss forced-U task error"] = str(error_path.relative_to(outdir))

    payload = {
        "sprint": "V05E",
        "program": "kinematic_decomposition",
        "audit_status": "MVP_WITH_BOUNDARY_SUITE",
        "exact_tolerances": {
            "PAIR_DISTANCE_TOL_M": PAIR_DISTANCE_TOL_M,
            "ORTHOGONALITY_DOT_TOL": ORTHOGONALITY_DOT_TOL,
            "PARALLEL_CROSS_TOL": PARALLEL_CROSS_TOL,
        },
        "results": [
            {
                "certificate": certificate.to_json_dict(),
                "false_u_task_error": None if report is None else report.to_json_dict(),
            }
            for certificate, report in rows
        ],
        "tolerance_boundary_cases": [case.to_json_dict() for case in boundary_cases],
    }
    (data_dir / "v05e_near_aligned_rejection.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (outdir / "sprint_v05e_near_aligned_rejection.html").write_text(
        render_v05e_html(rows, boundary_cases, figures=figures),
        encoding="utf-8",
    )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05e"),
    )
    parser.add_argument("--n-fiber-steps", type=int, default=24)
    parser.add_argument("--fiber-step-size", type=float, default=0.04)
    args = parser.parse_args(argv)
    rows = build_v05e_readout(
        args.outdir,
        n_fiber_steps=args.n_fiber_steps,
        fiber_step_size=args.fiber_step_size,
    )
    for certificate, report in rows:
        extra = "" if report is None else f", false-U max Δp={report.fiber_max_position_residual_m:.3e}"
        print(
            f"{certificate.source_chain_id}: axis={certificate.axis_aggregation_status}, "
            f"closed={certificate.closed_mechanism_status}, overall={certificate.status}{extra}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
