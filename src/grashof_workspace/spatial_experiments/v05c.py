"""Active V05C runner: orientation-curve truth for spatial 4R fibers.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05c \\
      --outdir results/kinematic_decomposition/v05c
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from .fixed_position_continuation import continue_fixed_position_fiber
from .orientation_image import (
    OrientationImageResult,
    PointingImageResult,
    build_orientation_image,
    build_pointing_image,
)
from .v05_corpus import Spatial4RCorpusEntry, v05a_spatial_4r_corpus


def _plot_orientation_charts(
    orientation: OrientationImageResult,
    pointing: PointingImageResult,
    outpath: Path,
) -> None:
    samples = orientation.samples
    figure = plt.figure(figsize=(10.0, 7.2))
    ax_quat = figure.add_subplot(2, 2, 1)
    ax_rot = figure.add_subplot(2, 2, 2)
    ax_s2 = figure.add_subplot(2, 2, 3, projection="3d")
    ax_sing = figure.add_subplot(2, 2, 4)

    if not samples:
        for ax in (ax_quat, ax_rot, ax_sing):
            ax.axis("off")
        ax_s2.axis("off")
        ax_quat.text(0.1, 0.5, f"{orientation.architecture_id}: no orientation samples")
        figure.suptitle("V05C orientation-curve truth (empty)")
        figure.tight_layout()
        figure.savefig(outpath, dpi=160)
        plt.close(figure)
        return

    sigma = np.asarray([s.sigma for s in samples], dtype=float)
    quats = np.asarray([s.quaternion for s in samples], dtype=float)
    rotvecs = np.asarray([s.rotvec for s in samples], dtype=float)
    sigma_min = np.asarray([s.sigma_min_jp for s in samples], dtype=float)
    near = np.asarray([s.near_singular for s in samples], dtype=bool)

    for i, label in enumerate(("w", "x", "y", "z")):
        ax_quat.plot(sigma, quats[:, i], label=label)
    ax_quat.set_title("Quaternion chart vs σ (sign-stabilized)")
    ax_quat.set_xlabel("σ")
    ax_quat.legend(fontsize="small", ncol=4)

    for i, label in enumerate(("rx", "ry", "rz")):
        ax_rot.plot(sigma, rotvecs[:, i], label=label)
    ax_rot.set_title("Rotation-vector chart vs σ")
    ax_rot.set_xlabel("σ")
    ax_rot.legend(fontsize="small")

    if pointing.points:
        d_vals = np.asarray(pointing.points, dtype=float)
        ax_s2.plot(d_vals[:, 0], d_vals[:, 1], d_vals[:, 2], color="#06a", lw=1.5)
        ax_s2.scatter(d_vals[0, 0], d_vals[0, 1], d_vals[0, 2], c="#0a5", s=30)
        u = np.linspace(0, 2 * np.pi, 24)
        v = np.linspace(0, np.pi, 12)
        xs = np.outer(np.cos(u), np.sin(v))
        ys = np.outer(np.sin(u), np.sin(v))
        zs = np.outer(np.ones_like(u), np.cos(v))
        ax_s2.plot_wireframe(xs, ys, zs, color="#ccc", linewidth=0.3)
    ax_s2.set_title("Tool-axis path on S² (not coverage)")
    ax_s2.set_xlim(-1.1, 1.1)
    ax_s2.set_ylim(-1.1, 1.1)
    ax_s2.set_zlim(-1.1, 1.1)

    ax_sing.semilogy(sigma, np.clip(np.nan_to_num(sigma_min, nan=1e-16), 1e-16, None), label="σ_min(J_p)")
    if np.any(near):
        ax_sing.scatter(
            sigma[near],
            np.clip(np.nan_to_num(sigma_min[near], nan=1e-16), 1e-16, None),
            c="#c40",
            s=18,
            label="near-singular",
        )
    ax_sing.set_title("Singularity margin along curve")
    ax_sing.set_xlabel("σ")
    ax_sing.legend(fontsize="small")

    figure.suptitle(
        f"V05C orientation-curve truth — {orientation.architecture_id} "
        f"(status={orientation.status}; not coverage)"
    )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _animate_orientation_curve(
    entry: Spatial4RCorpusEntry,
    orientation: OrientationImageResult,
    outpath: Path,
) -> None:
    chain = entry.model.chain
    samples = orientation.samples
    if not samples:
        figure = plt.figure(figsize=(6.4, 5.6))
        axis = figure.add_subplot(111, projection="3d")
        p_star = np.asarray(orientation.p_star, dtype=float)
        axis.scatter([p_star[0]], [p_star[1]], [p_star[2]], c="#c40", s=50)
        axis.set_title(f"{orientation.architecture_id}: no orientation curve")
        figure.tight_layout()
        figure.savefig(outpath.with_suffix(".png"), dpi=140)
        plt.close(figure)
        return

    # Recover q by re-continuing is expensive; animate from fiber via pointing + p*.
    # Use FK only when we can match sigma from a fresh short fiber.
    fiber = continue_fixed_position_fiber(
        entry.model,
        entry.regular_q,
        n_steps=24,
        step_size=0.05,
    )
    by_sigma = {round(step.sigma, 8): step for step in fiber.accepted_samples if step.q is not None}
    frames = []
    for sample in samples[:: max(1, len(samples) // 20)]:
        step = by_sigma.get(round(sample.sigma, 8))
        if step is not None and step.q is not None:
            frames.append((sample, step.q))
    if not frames:
        # Fallback: plot pointing only.
        figure = plt.figure(figsize=(6.4, 5.6))
        axis = figure.add_subplot(111, projection="3d")
        d_vals = np.asarray([s.d for s in samples], dtype=float)
        axis.plot(d_vals[:, 0], d_vals[:, 1], d_vals[:, 2], color="#06a")
        axis.set_title(f"{orientation.architecture_id}: pointing curve on S²")
        figure.tight_layout()
        figure.savefig(outpath.with_suffix(".png"), dpi=140)
        plt.close(figure)
        return

    p_star = np.asarray(orientation.p_star, dtype=float)
    figure = plt.figure(figsize=(7.0, 6.2))
    axis = figure.add_subplot(111, projection="3d")

    def _draw(frame_index: int) -> None:
        axis.cla()
        sample, q = frames[frame_index]
        state = chain.evaluate(q)
        origins = np.asarray([line.r for line in state.axes], dtype=float)
        pts = np.vstack([origins, state.p.reshape(1, 3)])
        axis.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="#333", lw=2.0)
        for line in state.axes:
            r = np.asarray(line.r, dtype=float)
            w = np.asarray(line.w, dtype=float)
            axis.quiver(r[0], r[1], r[2], w[0], w[1], w[2], length=0.12, normalize=True, color="#06a")
        axis.scatter([p_star[0]], [p_star[1]], [p_star[2]], c="#c40", s=55)
        axis.quiver(
            float(state.p[0]),
            float(state.p[1]),
            float(state.p[2]),
            float(state.d[0]),
            float(state.d[1]),
            float(state.d[2]),
            length=0.2,
            normalize=True,
            color="#c40",
        )
        axis.set_title(
            f"{orientation.architecture_id} orientation curve | param=σ (not coverage)\n"
            f"σ={sample.sigma:+.2f} | near_singular={sample.near_singular}"
        )
        mid = pts.mean(axis=0)
        radius = max(float(np.max(pts.max(axis=0) - pts.min(axis=0))) * 0.7, 0.35)
        axis.set_xlim(mid[0] - radius, mid[0] + radius)
        axis.set_ylim(mid[1] - radius, mid[1] + radius)
        axis.set_zlim(mid[2] - radius, mid[2] + radius)

    animation = FuncAnimation(figure, _draw, frames=len(frames), interval=140)
    animation.save(outpath, writer=PillowWriter(fps=7))
    plt.close(figure)


def render_v05c_html(
    rows: list[tuple[OrientationImageResult, PointingImageResult]],
    *,
    figures: dict[str, str],
) -> str:
    table_rows = []
    for orientation, pointing in rows:
        table_rows.append(
            "<tr>"
            f"<td><code>{orientation.architecture_id}</code></td>"
            f"<td>{orientation.status}</td>"
            f"<td>{len(orientation.samples)}</td>"
            f"<td>{pointing.status}</td>"
            f"<td>{len(pointing.points)}</td>"
            f"<td>{orientation.near_singular_count}</td>"
            f"<td>{orientation.multiplicity.same_pointing_distinct_orientation_pairs}</td>"
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
<title>Active V05C — Orientation-Curve Truth</title>
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
<h1>Active V05C — Orientation-Curve Truth</h1>
<p>
Exports the orientation image and pointing projection of continued spatial
<code>4R + S_v</code> fixed-position fibers from V05B. Representations are
rotation matrices, sign-stabilized quaternions, and rotation vectors — not a
single scalar angle.
</p>
<div class="note">
<strong>Gate note.</strong>
These plots are <strong>orientation-curve truth</strong>, not coverage of
<code>SO(3)</code> or <code>S²</code>. Singular / near-singular markers are
reported along the continued component. V05D aggregation certificates and V05E
rejection tests remain deferred.
</div>
<h2>Corpus orientation images</h2>
<table>
<tr><th>Architecture</th><th>Orientation</th><th>Samples</th><th>Pointing</th><th>Points</th><th>Near-sing.</th><th>d-mult. pairs</th></tr>
{''.join(table_rows)}
</table>
<h2>Figures</h2>
{''.join(figure_blocks)}
<h2>Deferred</h2>
<ul>
<li>V05D exact <code>RR→U</code> aggregation + DecompositionCertificate</li>
<li>V05E near-aligned rejection</li>
<li>Any claim that the orientation curve fills a coverage target</li>
</ul>
</body>
</html>
"""


def build_v05c_readout(
    outdir: Path,
    *,
    n_steps: int = 40,
    step_size: float = 0.04,
) -> list[tuple[OrientationImageResult, PointingImageResult]]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    rows: list[tuple[OrientationImageResult, PointingImageResult]] = []
    figures: dict[str, str] = {}
    payload_fibers = []

    for entry in v05a_spatial_4r_corpus():
        fiber = continue_fixed_position_fiber(
            entry.model,
            entry.regular_q,
            n_steps=n_steps,
            step_size=step_size,
        )
        orientation = build_orientation_image(fiber, chain=entry.model)
        pointing = build_pointing_image(fiber)
        rows.append((orientation, pointing))
        payload_fibers.append(
            {
                "fiber": {
                    "architecture_id": fiber.architecture_id,
                    "branch_status": fiber.branch_status,
                    "seed_status": fiber.seed_audit.status,
                },
                "orientation_image": orientation.to_json_dict(),
                "pointing_image": pointing.to_json_dict(),
            }
        )
        stem = entry.model.architecture_id
        chart = figures_dir / f"v05c_{stem}_orientation_charts.png"
        _plot_orientation_charts(orientation, pointing, chart)
        figures[f"{stem} orientation charts"] = str(chart.relative_to(outdir))
        gif = figures_dir / f"v05c_{stem}_orientation_curve.gif"
        _animate_orientation_curve(entry, orientation, gif)
        if gif.exists():
            figures[f"{stem} orientation curve animation"] = str(gif.relative_to(outdir))
        elif gif.with_suffix(".png").exists():
            figures[f"{stem} orientation curve view"] = str(gif.with_suffix(".png").relative_to(outdir))

    (data_dir / "v05c_orientation_curves.json").write_text(
        json.dumps(
            {
                "sprint": "V05C",
                "program": "kinematic_decomposition",
                "gate_note": (
                    "Orientation-curve truth only; not SO(3)/S^2 coverage. "
                    "V05D–E deferred."
                ),
                "fibers": payload_fibers,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    html = render_v05c_html(rows, figures=figures)
    (outdir / "sprint_v05c_orientation_curve.html").write_text(html, encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05c"),
    )
    parser.add_argument("--n-steps", type=int, default=40)
    parser.add_argument("--step-size", type=float, default=0.04)
    args = parser.parse_args(argv)
    rows = build_v05c_readout(args.outdir, n_steps=args.n_steps, step_size=args.step_size)
    summary = ", ".join(f"{o.architecture_id}:{o.status}" for o, _ in rows)
    print(f"V05C wrote {args.outdir} [{summary}]")


if __name__ == "__main__":
    main()
