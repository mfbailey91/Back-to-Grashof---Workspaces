"""Sprint V05A runner: parent-first pointing fiber (SUUR → UUUR MVP).

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial4bar_explorer.v05a \\
      --outdir results/spatial4bar_explorer/v05a
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    IntersectingPairsAligned6R,
)
from grashof_workspace.spatial_experiments.fiber_constraints import PRIMARY_N, pointing_scalar
from grashof_workspace.spatial_experiments.fiber_continuation import continue_fiber

from .closure import mechanism_state
from .geometry_plots import plot_physical_geometry_3d
from .pointing_slice import (
    PointingSliceFiberResult,
    child_branch_trace,
    construct_suur_uuur_pointing_fiber,
)


def _plot_parent_fiber_diagnostics(
    result: PointingSliceFiberResult,
    outpath: Path,
) -> None:
    architecture = IntersectingPairsAligned6R.aligned()
    chain = architecture.chain
    q0 = result.slice_definition.q0
    n = result.slice_definition.n
    segment = continue_fiber(chain, q0, n, n_steps=8, step_size=0.02)
    samples = segment.accepted_samples
    sigma = [step.sigma for step in samples]
    h_res = [abs(pointing_scalar(chain, step.q, n) - segment.c) for step in samples if step.q is not None]
    rank = [step.rank_jf for step in samples]
    nullity = [step.nullity_jf for step in samples]
    d_vals = np.asarray([step.d for step in samples if step.d is not None], dtype=float)

    figure, axes = plt.subplots(2, 2, figsize=(9.5, 7.0))
    axes[0, 0].plot(sigma[: len(h_res)], h_res, marker="o", ms=3)
    axes[0, 0].set_title("Parent fiber: |h − c|")
    axes[0, 0].set_xlabel("σ")
    axes[0, 0].set_ylabel("residual")

    axes[0, 1].plot(sigma, rank, label="rank(J_F)")
    axes[0, 1].plot(sigma, nullity, label="nullity")
    axes[0, 1].set_title("Parent fiber rank / nullity")
    axes[0, 1].set_xlabel("σ")
    axes[0, 1].legend(fontsize="small")

    if len(d_vals):
        axes[1, 0].plot(d_vals[:, 0], d_vals[:, 1], marker="o", ms=3)
        axes[1, 0].set_xlabel("d_x")
        axes[1, 0].set_ylabel("d_y")
        axes[1, 0].set_title("Pointing curve (d_x, d_y)")
        axes[1, 0].set_aspect("equal", adjustable="datalim")

    vu = result.virtual_u
    axes[1, 1].axis("off")
    axes[1, 1].text(
        0.02,
        0.98,
        (
            f"slice: h(d)=n·d = {result.slice_definition.c:.6f}\n"
            f"n = {n}\n"
            f"status = {result.fiber_equivalence_status}\n"
            f"provenance = {result.slice_provenance}\n"
            f"R_a = {vu.r_a}\n"
            f"R_b = {vu.r_b}\n"
            f"U-lift tangent residual = {result.equivalence_residuals.tangent_pointing_residual:.3e}\n"
            f"child-tool diagnostic = {result.equivalence_residuals.child_tool_tangent_residual:.3e}\n"
            f"pointing residual = {result.equivalence_residuals.pointing_curve_residual:.3e}"
        ),
        va="top",
        family="monospace",
        fontsize=9,
    )
    figure.suptitle("V05A parent pointing-fiber diagnostics (SUUR)")
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _animate_task_derived_fiber(
    result: PointingSliceFiberResult,
    outpath: Path,
    *,
    steps: int = 20,
) -> None:
    """Partial task-derived fiber GIF with the animation-contract checklist."""
    geometry = result.geometry
    trace = child_branch_trace(geometry, steps=steps, step_size=0.03)
    vu = result.virtual_u
    n = np.asarray(result.slice_definition.n, dtype=float)
    p0 = np.asarray(result.slice_definition.p0, dtype=float)
    d0 = np.asarray(vu.d, dtype=float)
    ra = np.asarray(vu.r_a, dtype=float)
    rb = np.asarray(vu.r_b, dtype=float)

    figure = plt.figure(figsize=(7.2, 6.4))
    axis = figure.add_subplot(111, projection="3d")

    def _draw(frame_index: int) -> None:
        axis.cla()
        point = trace.points[min(frame_index, len(trace.points) - 1)]
        centers, _ = mechanism_state(geometry, np.asarray(point.q, dtype=float))
        # Loop skeleton.
        loop = np.vstack((centers, centers[0]))
        axis.plot(loop[:, 0], loop[:, 1], loop[:, 2], color="#333", lw=2.0)
        axis.scatter(centers[:, 0], centers[:, 1], centers[:, 2], c="#222", s=30)

        # Tool point / virtual S_v center and pointing.
        axis.scatter([p0[0]], [p0[1]], [p0[2]], c="#c40", s=55, label="tool / S_v")
        axis.quiver(p0[0], p0[1], p0[2], d0[0], d0[1], d0[2], color="#c40", length=0.25, normalize=True)
        axis.quiver(p0[0], p0[1], p0[2], ra[0], ra[1], ra[2], color="#06a", length=0.2, normalize=True)
        axis.quiver(p0[0], p0[1], p0[2], rb[0], rb[1], rb[2], color="#0a6", length=0.2, normalize=True)
        # Slice plane normal marker.
        axis.quiver(p0[0], p0[1], p0[2], n[0], n[1], n[2], color="#888", length=0.18, normalize=True)

        alpha = float(point.q[0])
        beta = float(point.q[1])
        axis.set_title(
            "task-derived fiber | param=s (not driven)\n"
            f"h(d)=n·d={result.slice_definition.c:.3f} | "
            f"s={point.arclength:.2f} | α(s)={alpha:+.2f} | β(s)={beta:+.2f}"
        )
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        axis.set_zlabel("z")
        spans = centers.max(axis=0) - centers.min(axis=0)
        mid = centers.mean(axis=0)
        radius = max(float(np.max(spans)) * 0.7, 0.35)
        axis.set_xlim(mid[0] - radius, mid[0] + radius)
        axis.set_ylim(mid[1] - radius, mid[1] + radius)
        axis.set_zlim(mid[2] - radius, mid[2] + radius)

    animation = FuncAnimation(figure, _draw, frames=len(trace.points), interval=120)
    animation.save(outpath, writer=PillowWriter(fps=8))
    plt.close(figure)


def render_v05a_html(result: PointingSliceFiberResult, outdir: Path, *, figures: dict[str, str]) -> str:
    residuals = result.equivalence_residuals
    status_class = {
        "PASS": "pass",
        "FAIL": "fail",
        "REVIEW": "review",
    }.get(result.fiber_equivalence_status, "review")
    figure_blocks = []
    for label, rel in figures.items():
        figure_blocks.append(
            f'<h3>{label}</h3><p><img src="{rel}" alt="{label}" style="max-width: 720px;"></p>'
        )
    notes = "".join(f"<li>{note}</li>" for note in result.notes)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sprint V05A — Parent-First Pointing Fiber</title>
<style>
  body {{ font-family: Georgia, "Times New Roman", serif; max-width: 920px; margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.45; color: #1a1a1a; }}
  h1, h2, h3 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.75rem 0 1rem; }}
  th, td {{ border: 1px solid #bbb; padding: 0.4rem 0.55rem; text-align: left; }}
  th {{ background: #f3f3f3; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; }}
  .pass {{ color: #0a5; font-weight: bold; }}
  .fail {{ color: #a20; font-weight: bold; }}
  .review {{ color: #a60; font-weight: bold; }}
  .note {{ background: #f7f4ea; border-left: 3px solid #c4a35a; padding: 0.65rem 0.85rem; margin: 1rem 0; }}
  ul.checklist li {{ margin: 0.25rem 0; }}
</style>
</head>
<body>
<h1>Sprint V05A — Parent-First Pointing Fiber</h1>
<p>SUUR → UUUR MVP on the intersecting-pairs aligned-terminal architecture.
SSRR-line parents and the full V05B winding atlas are deferred.</p>

<div class="note">
<strong>Gate note.</strong>
Fiber-equivalence status for the worked child:
<span class="{status_class}">{result.fiber_equivalence_status}</span>
with <code>slice_provenance={result.slice_provenance}</code>.
Only <code>PASS</code> rows are atlas-admissible. Standalone V02B–V04 geometries remain
<code>mechanism_explorer_only</code>.
</div>

<h2>Worked fiber</h2>
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td>slice_id</td><td><code>{result.slice_id}</code></td></tr>
<tr><td>family</td><td>{result.family}</td></tr>
<tr><td>parent_line</td><td>{result.parent_line}</td></tr>
<tr><td>slice</td><td><code>{result.slice_definition.formula} = {result.slice_definition.c:.8f}</code></td></tr>
<tr><td>n</td><td><code>{result.slice_definition.n}</code></td></tr>
<tr><td>architecture</td><td>{result.slice_definition.architecture}</td></tr>
<tr><td>parent rank / nullity</td><td>{residuals.parent_rank} / {residuals.parent_nullity}</td></tr>
<tr><td>dh/dq6</td><td>{residuals.dh_dq6:.3e}</td></tr>
<tr><td>accepted fiber samples</td><td>{result.fiber_segment_accepted}</td></tr>
<tr><td>child rank / nullity</td><td>{residuals.child_rank} / {residuals.child_nullity}</td></tr>
<tr><td>U-lift tangent residual</td><td>{residuals.tangent_pointing_residual:.6e}</td></tr>
<tr><td>child-tool tangent diagnostic</td><td>{residuals.child_tool_tangent_residual:.6e}</td></tr>
<tr><td>lifted (α′, β′)</td><td>({residuals.lifted_alpha_dot:.6e}, {residuals.lifted_beta_dot:.6e})</td></tr>
<tr><td>pointing-curve residual</td><td>{residuals.pointing_curve_residual:.6e}</td></tr>
<tr><td>fiber_equivalence_status</td><td class="{status_class}">{result.fiber_equivalence_status}</td></tr>
</table>

<h2>Task-derived animation contract checklist</h2>
<ul class="checklist">
<li>tool point / virtual <code>S_v</code> center</li>
<li>tool pointing direction <code>d</code></li>
<li>derived <code>R_a</code> / <code>R_b</code> axes</li>
<li>pointing-slice definition <code>h(d)=n·d=c</code></li>
<li><code>α(s)</code> / <code>β(s)</code> readouts</li>
<li>explicit branch parameter <code>param=s (not driven)</code></li>
</ul>
<p>The first GIF may be partial (short child branch) but must name these elements.</p>

<h2>Figures</h2>
{''.join(figure_blocks)}

<h2>Notes</h2>
<ul>{notes}</ul>

<h2>Deferred</h2>
<ul>
<li>V05B–V05D all-family winding atlas / Gate A mining decision</li>
<li>SSRR → USRR / URSR / URRS parent construction</li>
<li>Promoting diagnostic <code>phi</code> to a fiber parameter</li>
</ul>
</body>
</html>
"""


def build_v05a_readout(outdir: Path) -> PointingSliceFiberResult:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    result = construct_suur_uuur_pointing_fiber(
        n=PRIMARY_N,
        q0=INTERSECTING_PAIRS_REGULAR_Q,
        n_steps=8,
        step_size=0.02,
        slice_id="suur_ip_primary_n",
    )

    json_path = data_dir / "v05a_pointing_slice_fibers.json"
    payload = {
        "sprint": "V05A",
        "gate_note": (
            "SUUR→UUUR V05A MVP status recorded below; SSRR and full V05B deferred."
        ),
        "fibers": [result.to_json_dict()],
        "standalone_v02b_v04_policy": "mechanism_explorer_only",
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    parent_plot = figures_dir / "v05a_parent_fiber_diagnostics.png"
    _plot_parent_fiber_diagnostics(result, parent_plot)

    child_geom = figures_dir / "v05a_uuur_child_geometry.png"
    plot_physical_geometry_3d(result.geometry, child_geom)

    fiber_gif = figures_dir / "v05a_task_derived_fiber.gif"
    _animate_task_derived_fiber(result, fiber_gif, steps=18)

    figures = {
        "Parent fiber diagnostics": str(parent_plot.relative_to(outdir)),
        "Task-derived UUUR child geometry": str(child_geom.relative_to(outdir)),
        "Task-derived fiber animation (partial OK)": str(fiber_gif.relative_to(outdir)),
    }
    html = render_v05a_html(result, outdir, figures=figures)
    (outdir / "sprint_05a_pointing_slice_fibers.html").write_text(html, encoding="utf-8")

    # Keep a compact machine-readable summary beside the HTML.
    (data_dir / "v05a_summary.json").write_text(
        json.dumps(
            {
                "fiber_equivalence_status": result.fiber_equivalence_status,
                "slice_provenance": result.slice_provenance,
                "slice_id": result.slice_id,
                "residuals": asdict(result.equivalence_residuals),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/spatial4bar_explorer/v05a"),
        help="directory for V05A HTML/JSON/figures",
    )
    args = parser.parse_args(argv)
    result = build_v05a_readout(args.outdir)
    print(
        f"V05A {result.fiber_equivalence_status} "
        f"provenance={result.slice_provenance} "
        f"outdir={args.outdir}"
    )


if __name__ == "__main__":
    main()
