"""Active V05B runner: spatial-4R fixed-position source fibers.

The active corpus contains nontrivial off-axis tool geometries plus an explicit
terminal-roll control. Continuation uses the augmented pseudo-arclength
corrector from ``fixed_position_continuation``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .fixed_position_continuation import FixedPositionFiberResult, continue_fixed_position_fiber
from .v05_corpus import v05a_spatial_4r_corpus


def _plot_fiber_diagnostics(fiber: FixedPositionFiberResult, outpath: Path) -> None:
    samples = fiber.accepted_samples
    figure, axes = plt.subplots(2, 2, figsize=(10.0, 7.4))
    if not samples:
        for axis in axes.flat:
            axis.axis("off")
        axes[0, 0].text(0.1, 0.5, f"{fiber.architecture_id}: rejected seed")
    else:
        sigma = np.asarray([step.sigma for step in samples], dtype=float)
        residual = np.asarray([max(step.p_residual_m, 1e-18) for step in samples])
        arc_residual = np.asarray(
            [max(step.arclength_residual_rad, 1e-18) for step in samples]
        )
        axes[0, 0].semilogy(sigma, residual, label="||p-p*||")
        axes[0, 0].semilogy(sigma, arc_residual, label="arclength residual")
        axes[0, 0].set_title("Augmented corrector residuals")
        axes[0, 0].set_xlabel("signed arclength σ")
        axes[0, 0].legend(fontsize="small")

        q = np.asarray([step.q for step in samples if step.q is not None], dtype=float)
        for joint_index in range(q.shape[1]):
            axes[0, 1].plot(sigma[: len(q)], q[:, joint_index], label=f"q{joint_index + 1}")
        axes[0, 1].set_title("Joint participation along source fiber")
        axes[0, 1].set_xlabel("σ")
        axes[0, 1].legend(fontsize="small", ncol=2)

        d = np.asarray([step.d for step in samples if step.d is not None], dtype=float)
        axes[1, 0].plot(d[:, 0], d[:, 1], marker="o", ms=2)
        axes[1, 0].set_title("Pointing projection (not coverage)")
        axes[1, 0].set_xlabel("d_x")
        axes[1, 0].set_ylabel("d_y")
        axes[1, 0].set_aspect("equal", adjustable="datalim")

        axes[1, 1].axis("off")
        audit = fiber.seed_audit
        axes[1, 1].text(
            0.02,
            0.98,
            "\n".join(
                (
                    f"source = {fiber.architecture_id}",
                    f"seed = {audit.status}",
                    f"rank/nullity = {audit.rank_jp}/{audit.nullity_jp}",
                    f"motion = {audit.motion_signature}",
                    f"terminal-axis distance = {audit.terminal_axis_distance_m:.3e} m",
                    f"upstream tangent norm = {audit.upstream_tangent_norm}",
                    f"pointing speed = {audit.pointing_speed}",
                    f"FD Jacobian error = {audit.finite_difference_jp_error_fro:.3e}",
                    f"branch = {fiber.branch_status}",
                    f"returned = {fiber.returned}",
                )
            ),
            va="top",
            family="monospace",
            fontsize=8.5,
        )
    figure.suptitle("V05B fixed-position source-fiber diagnostics")
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def render_v05b_html(
    fibers: list[FixedPositionFiberResult],
    *,
    figures: dict[str, str],
) -> str:
    rows = []
    for fiber in fibers:
        audit = fiber.seed_audit
        rows.append(
            "<tr>"
            f"<td><code>{fiber.architecture_id}</code></td>"
            f"<td>{audit.status}</td>"
            f"<td>{audit.rank_jp}/{audit.nullity_jp}</td>"
            f"<td><code>{audit.motion_signature}</code></td>"
            f"<td>{audit.terminal_axis_distance_m:.3e}</td>"
            f"<td>{fiber.branch_status}</td>"
            f"<td>{fiber.returned}</td>"
            f"<td>{len(fiber.accepted_samples)}</td>"
            "</tr>"
        )
    figure_blocks = "".join(
        f'<h3>{label}</h3><p><img src="{rel}" alt="{label}" style="max-width:760px"></p>'
        for label, rel in figures.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>V05B — Corrected Spatial-4R Fibers</title>
<style>body{{font-family:Georgia,serif;max-width:1000px;margin:2rem auto;line-height:1.45}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:.4rem;text-align:left}}code{{font-family:ui-monospace,monospace}}.note{{background:#f7f4ea;border-left:3px solid #c4a35a;padding:.7rem}}</style></head><body>
<h1>Active V05B — Spatial-4R Fixed-Position Source Fibers</h1>
<div class="note"><strong>Audit correction.</strong> Active regular sources place the tool point off R4 so the nullspace cannot collapse to terminal roll. The original on-axis geometry is retained as <code>terminal_roll_control_4r</code>. Continuation solves the augmented pseudo-arclength system for the exact fixed-position closure <code>4R + S_v</code>.</div>
<table><tr><th>Source</th><th>Seed</th><th>rank/nullity</th><th>Motion signature</th><th>Tool-axis distance [m]</th><th>Branch</th><th>Returned</th><th>Samples</th></tr>{''.join(rows)}</table>
<h2>Figures</h2>{figure_blocks}
<p>This readout establishes source-fiber and orientation-curve inputs. It does not certify an independent reduced closed mechanism.</p>
</body></html>"""


def build_v05b_readout(
    outdir: Path,
    *,
    n_steps: int = 80,
    step_size: float = 0.04,
) -> list[FixedPositionFiberResult]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    fibers: list[FixedPositionFiberResult] = []
    figures: dict[str, str] = {}
    for entry in v05a_spatial_4r_corpus():
        fiber = continue_fixed_position_fiber(
            entry.model,
            entry.regular_q,
            n_steps=n_steps,
            step_size=step_size,
        )
        fibers.append(fiber)
        path = figures_dir / f"v05b_{entry.model.architecture_id}_diagnostics.png"
        _plot_fiber_diagnostics(fiber, path)
        figures[f"{entry.model.architecture_id} diagnostics"] = str(path.relative_to(outdir))

    payload = {
        "sprint": "V05B",
        "program": "kinematic_decomposition",
        "audit_status": "CORRECTED_SOURCE_FIBER_MVP",
        "fibers": [fiber.to_json_dict() for fiber in fibers],
    }
    (data_dir / "v05b_fixed_position_fibers.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (outdir / "sprint_v05b_fixed_position_fiber.html").write_text(
        render_v05b_html(fibers, figures=figures),
        encoding="utf-8",
    )
    return fibers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05b"),
    )
    parser.add_argument("--n-steps", type=int, default=80)
    parser.add_argument("--step-size", type=float, default=0.04)
    args = parser.parse_args(argv)
    fibers = build_v05b_readout(args.outdir, n_steps=args.n_steps, step_size=args.step_size)
    for fiber in fibers:
        print(
            f"{fiber.architecture_id}: {fiber.seed_audit.status}, "
            f"motion={fiber.seed_audit.motion_signature}, branch={fiber.branch_status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
