"""Active V05B runner: spatial 4R fixed-position source fiber.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05b \\
      --outdir results/kinematic_decomposition/v05b
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from .fixed_position_continuation import FixedPositionFiberResult, continue_fixed_position_fiber
from .v05_corpus import Spatial4RCorpusEntry, v05a_spatial_4r_corpus


def _plot_fiber_diagnostics(fiber: FixedPositionFiberResult, outpath: Path) -> None:
    samples = fiber.accepted_samples
    sigma = [step.sigma for step in samples]
    residuals = [max(step.p_residual_m, 1e-18) for step in samples]
    ranks = [step.rank_jp for step in samples]
    nullities = [step.nullity_jp for step in samples]

    figure, axes = plt.subplots(2, 2, figsize=(9.5, 7.0))
    axes[0, 0].semilogy(sigma, residuals, marker="o", ms=3)
    axes[0, 0].set_title(f"{fiber.architecture_id}: ||p − p*||")
    axes[0, 0].set_xlabel("σ")
    axes[0, 0].set_ylabel("residual [m]")

    axes[0, 1].plot(sigma, ranks, label="rank(J_p)")
    axes[0, 1].plot(sigma, nullities, label="nullity")
    axes[0, 1].set_title("Rank / nullity along component")
    axes[0, 1].set_xlabel("σ")
    axes[0, 1].legend(fontsize="small")

    if samples and samples[0].d is not None:
        d_vals = np.asarray([step.d for step in samples if step.d is not None], dtype=float)
        axes[1, 0].plot(d_vals[:, 0], d_vals[:, 1], marker="o", ms=3)
        axes[1, 0].set_xlabel("d_x")
        axes[1, 0].set_ylabel("d_y")
        axes[1, 0].set_title("Pointing samples (not coverage claim)")
        axes[1, 0].set_aspect("equal", adjustable="datalim")

    axes[1, 1].axis("off")
    axes[1, 1].text(
        0.02,
        0.98,
        (
            f"architecture = {fiber.architecture_id}\n"
            f"virtual closure = {fiber.virtual_closure_kind}\n"
            f"seed status = {fiber.seed_audit.status}\n"
            f"rank/nullity = {fiber.seed_audit.rank_jp}/{fiber.seed_audit.nullity_jp}\n"
            f"branch = {fiber.branch_status}\n"
            f"returned = {fiber.returned}\n"
            f"accepted samples = {len(samples)}\n"
            f"p* = {fiber.p_star}"
        ),
        va="top",
        family="monospace",
        fontsize=9,
    )
    figure.suptitle("Active V05B fixed-position fiber diagnostics")
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _animate_chain_fiber(fiber: FixedPositionFiberResult, entry: Spatial4RCorpusEntry, outpath: Path) -> None:
    chain = entry.model.chain
    samples = [step for step in fiber.accepted_samples if step.q is not None]
    if not samples:
        # Still write a static placeholder frame for singular exteriors.
        figure = plt.figure(figsize=(6.5, 5.8))
        axis = figure.add_subplot(111, projection="3d")
        p_star = np.asarray(fiber.p_star, dtype=float)
        axis.scatter([p_star[0]], [p_star[1]], [p_star[2]], c="#c40", s=60)
        axis.set_title(f"{fiber.architecture_id}: rejected seed (no fiber)")
        figure.tight_layout()
        figure.savefig(outpath.with_suffix(".png"), dpi=140)
        plt.close(figure)
        return

    # Subsample for GIF length.
    stride = max(1, len(samples) // 24)
    frames = samples[::stride]
    p_star = np.asarray(fiber.p_star, dtype=float)

    figure = plt.figure(figsize=(7.0, 6.2))
    axis = figure.add_subplot(111, projection="3d")

    def _draw(frame_index: int) -> None:
        axis.cla()
        step = frames[frame_index]
        assert step.q is not None
        state = chain.evaluate(step.q)
        origins = np.asarray([line.r for line in state.axes], dtype=float)
        # Approximate link polyline: axis origins + tool point.
        pts = np.vstack([origins, state.p.reshape(1, 3)])
        axis.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="#333", lw=2.0)
        axis.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c="#222", s=28)
        for line in state.axes:
            r = np.asarray(line.r, dtype=float)
            w = np.asarray(line.w, dtype=float)
            axis.quiver(r[0], r[1], r[2], w[0], w[1], w[2], length=0.12, normalize=True, color="#06a")
        axis.scatter([p_star[0]], [p_star[1]], [p_star[2]], c="#c40", s=55, label="S_v / p*")
        axis.quiver(
            float(state.p[0]),
            float(state.p[1]),
            float(state.p[2]),
            float(state.d[0]),
            float(state.d[1]),
            float(state.d[2]),
            length=0.18,
            normalize=True,
            color="#c40",
        )
        axis.set_title(
            f"{fiber.architecture_id} fixed-position fiber | param=σ\n"
            f"σ={step.sigma:+.2f} | residual={step.p_residual_m:.1e} | S_v at p*"
        )
        mid = pts.mean(axis=0)
        radius = max(float(np.max(pts.max(axis=0) - pts.min(axis=0))) * 0.7, 0.35)
        axis.set_xlim(mid[0] - radius, mid[0] + radius)
        axis.set_ylim(mid[1] - radius, mid[1] + radius)
        axis.set_zlim(mid[2] - radius, mid[2] + radius)
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        axis.set_zlabel("z")

    animation = FuncAnimation(figure, _draw, frames=len(frames), interval=120)
    animation.save(outpath, writer=PillowWriter(fps=8))
    plt.close(figure)


def render_v05b_html(
    fibers: list[FixedPositionFiberResult],
    *,
    figures: dict[str, str],
) -> str:
    rows = []
    for fiber in fibers:
        rows.append(
            "<tr>"
            f"<td><code>{fiber.architecture_id}</code></td>"
            f"<td>{fiber.seed_audit.status}</td>"
            f"<td>{fiber.seed_audit.rank_jp}/{fiber.seed_audit.nullity_jp}</td>"
            f"<td>{fiber.virtual_closure_kind}</td>"
            f"<td>{fiber.branch_status}</td>"
            f"<td>{fiber.returned}</td>"
            f"<td>{len(fiber.accepted_samples)}</td>"
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
<title>Active V05B — Spatial 4R Fixed-Position Fiber</title>
<style>
  body {{ font-family: Georgia, "Times New Roman", serif; max-width: 920px; margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.45; color: #1a1a1a; }}
  h1, h2, h3 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.75rem 0 1rem; }}
  th, td {{ border: 1px solid #bbb; padding: 0.4rem 0.55rem; text-align: left; }}
  th {{ background: #f3f3f3; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; }}
  .note {{ background: #f7f4ea; border-left: 3px solid #c4a35a; padding: 0.65rem 0.85rem; margin: 1rem 0; }}
</style>
</head>
<body>
<h1>Active V05B — Spatial 4R Fixed-Position Source Fiber</h1>
<p>
Source problem <code>4R + S_v</code>, <code>M = 1</code> at regular seeds.
This is the kinematic-decomposition ladder V05B, not the deferred explorer family-winding atlas (V10).
</p>
<div class="note">
<strong>Gate note.</strong>
At least one regular fixed-position component is continued with explicit rank/nullity and branch status.
Orientation samples along the fiber are stored for later V05C and are <em>not</em> coverage claims.
V05D axis-aggregation certificates, V05E near-aligned rejection, and historical V10 atlas work remain deferred.
Explorer <code>spatial4bar_explorer/v05a</code> pointing-slice MVP remains <code>mechanism_explorer_only</code>.
</div>
<h2>Corpus fibers</h2>
<table>
<tr><th>Architecture</th><th>Seed</th><th>rank/nullity</th><th>Closure</th><th>Branch</th><th>Returned</th><th>Samples</th></tr>
{''.join(rows)}
</table>
<h2>Figures</h2>
{''.join(figure_blocks)}
<h2>Deferred</h2>
<ul>
<li>V05C orientation-curve truth gallery</li>
<li>V05D exact <code>RR→U</code> aggregation + DecompositionCertificate</li>
<li>V05E near-aligned rejection tests</li>
<li>Historical all-family winding atlas (V10)</li>
</ul>
</body>
</html>
"""


def build_v05b_readout(outdir: Path, *, n_steps: int = 40, step_size: float = 0.04) -> list[FixedPositionFiberResult]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    corpus = v05a_spatial_4r_corpus()
    fibers: list[FixedPositionFiberResult] = []
    figures: dict[str, str] = {}

    for entry in corpus:
        fiber = continue_fixed_position_fiber(
            entry.model,
            entry.regular_q,
            n_steps=n_steps,
            step_size=step_size,
        )
        fibers.append(fiber)
        stem = entry.model.architecture_id
        diag = figures_dir / f"v05b_{stem}_diagnostics.png"
        _plot_fiber_diagnostics(fiber, diag)
        figures[f"{stem} diagnostics"] = str(diag.relative_to(outdir))
        gif = figures_dir / f"v05b_{stem}_fiber.gif"
        _animate_chain_fiber(fiber, entry, gif)
        if gif.exists():
            figures[f"{stem} fiber animation"] = str(gif.relative_to(outdir))
        elif gif.with_suffix(".png").exists():
            figures[f"{stem} seed view"] = str(gif.with_suffix(".png").relative_to(outdir))

    payload = {
        "sprint": "V05B",
        "program": "kinematic_decomposition",
        "gate_note": (
            "Active V05B spatial 4R fixed-position fiber MVP; "
            "V05C–E and deferred V10 atlas remain open."
        ),
        "fibers": [fiber.to_json_dict() for fiber in fibers],
        "explorer_v05a_policy": "mechanism_explorer_only",
    }
    (data_dir / "v05b_fixed_position_fibers.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    html = render_v05b_html(fibers, figures=figures)
    (outdir / "sprint_v05b_fixed_position_fiber.html").write_text(html, encoding="utf-8")
    return fibers


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05b"),
        help="directory for V05B HTML/JSON/figures",
    )
    parser.add_argument("--n-steps", type=int, default=40)
    parser.add_argument("--step-size", type=float, default=0.04)
    args = parser.parse_args(argv)
    fibers = build_v05b_readout(args.outdir, n_steps=args.n_steps, step_size=args.step_size)
    summary = ", ".join(
        f"{f.architecture_id}:{f.seed_audit.status}/{f.branch_status}" for f in fibers
    )
    print(f"V05B wrote {args.outdir} [{summary}]")


if __name__ == "__main__":
    main()
