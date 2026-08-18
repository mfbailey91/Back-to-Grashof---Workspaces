"""R3A HTML/PNG readout. Source arm remains a transparent reference."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .models import CampaignConfig, FixedPointProbe, json_dumps_strict, stage_envelope
from .positive_control import (
    build_positive_control_arm,
    evaluate_wrist_center,
    fixture_seed_for_probe,
)
from .sphere_grid import build_sphere_grid

SCAFFOLD_WATERMARK = "SCAFFOLD_NO_DATA"


def _plot_arm(ax: Any, arm: Any, q: tuple[float, ...], *, alpha: float = 0.35) -> None:
    state = arm.chain.evaluate(q)
    wrist = evaluate_wrist_center(arm, q)
    pts = [np.array([0.0, 0.0, 0.0]), wrist, np.asarray(state.p)]
    xs, ys, zs = zip(*pts)
    ax.plot(xs, ys, zs, color="#888888", alpha=alpha, linewidth=2.0)
    ax.scatter(xs, ys, zs, color="#444444", alpha=alpha)


def _watermark_axes(ax: Any, title: str) -> None:
    ax.set_title(f"{SCAFFOLD_WATERMARK}\n{title}")
    ax.text(
        0.5,
        0.5,
        SCAFFOLD_WATERMARK,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=16,
        color="#c0392b",
        alpha=0.55,
        rotation=18,
        fontweight="bold",
        zorder=10,
    )


def write_probe_figures(
    config: CampaignConfig,
    probe: FixedPointProbe,
    outdir: Path,
    *,
    generate_gif: bool = False,
) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arm = build_positive_control_arm(config.geometry)
    q = fixture_seed_for_probe(
        arm,
        probe,
        position_tol_m=config.tolerances.position_residual_m,
        pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
    )
    fig_dir = outdir / probe.probe_id / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(111, projection="3d")
    _plot_arm(ax, arm, q)
    ax.set_title(f"{probe.probe_id} pointing geometry")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    path = fig_dir / "arm_geometry.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    names.append(str(path))

    grid = build_sphere_grid(0)
    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(grid.vertices[:, 0], grid.vertices[:, 1], grid.vertices[:, 2], s=8, color="#1f77b4")
    ax.set_title(f"{probe.probe_id} pointing sphere (not dexterous)")
    path = fig_dir / "direct_pointing.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    names.append(str(path))
    for fname in (
        "source_control.png",
        "natural_leaves.png",
        "three_way_comparison.png",
        "selected_leaf_overlay.png",
        "selected_leaf_residuals.png",
    ):
        fig = plt.figure(figsize=(5, 3))
        ax = fig.add_subplot(111)
        _watermark_axes(ax, fname.replace("_", " ").replace(".png", "") + " — pointing")
        ax.plot([0, 1], [0, 0], color="#888")
        fig.tight_layout()
        fig.savefig(fig_dir / fname, dpi=100)
        plt.close(fig)
        names.append(str(fig_dir / fname))
    if generate_gif:
        from PIL import Image

        frames = [Image.open(fig_dir / "arm_geometry.png")]
        frames[0].save(fig_dir / "selected_leaf.gif", save_all=True, append_images=frames, duration=200, loop=0)
        names.append(str(fig_dir / "selected_leaf.gif"))
    items = "".join(
        f"<li><img src='figures/{Path(n).name}' alt='{SCAFFOLD_WATERMARK} {Path(n).name}'></li>"
        for n in names
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{probe.probe_id}</title></head>
<body><h1>{probe.probe_id} pointing reconstruction</h1>
<p><strong>{SCAFFOLD_WATERMARK}</strong> — placeholder panels are not reconstruction evidence.</p>
<p>L5 pointing image in S^2. Not a dexterous SO(3) claim.</p>
<p>Fixed lambda leaves are frozen-geometry UURU children. h=c is a source control only.</p>
<ul>{items}</ul>
</body></html>"""
    (outdir / probe.probe_id / "index.html").write_text(html, encoding="utf-8")
    return names


def write_render_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
    generate_gif: bool = False,
) -> dict[str, Any]:
    written: list[str] = []
    for probe in probes:
        written.extend(write_probe_figures(config, probe, outdir, generate_gif=generate_gif))
    summary_path = outdir / "five_point_summary.png"
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(7, 3))
    ax = fig.add_subplot(111)
    ax.bar(range(len(probes)), [1 if p.expected_pointing_complete else 0 for p in probes])
    ax.set_xticks(range(len(probes)))
    ax.set_xticklabels([p.probe_id for p in probes], rotation=20, ha="right")
    ax.set_title("Five-point pointing-complete oracle labels")
    fig.tight_layout()
    fig.savefig(summary_path, dpi=120)
    plt.close(fig)
    links = "".join(f'<li><a href="{p.probe_id}/index.html">{p.probe_id}</a></li>' for p in probes)
    index = f"""<!doctype html><html><head><meta charset="utf-8"><title>R3A five-point hub</title></head>
<body>
<h1>R3A L5 five-point natural-leaf reconstruction</h1>
<p>Pointing coverage in S^2. Not dexterity. Fixed-axis UUUR remains rejected as an h=c equivalence.</p>
<ul>
{links}
</ul>
<p><a href="campaign.json">campaign.json</a></p>
</body></html>
"""
    (outdir / "index.html").write_text(index, encoding="utf-8")
    payload = {
        **stage_envelope(
            config,
            stage="render",
            mode=mode,
            probe_ids=tuple(p.probe_id for p in probes),
        ),
        "figures": written,
    }
    (outdir / "render.json").write_text(json_dumps_strict(payload), encoding="utf-8")
    return payload
