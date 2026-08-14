"""V06A0 readout: analytical unit-sphere validation of the implicit-manifold engine.

Software validation only. Does not construct a spatial-5R parent or issue a
DecompositionCertificate.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a0 \\
      --outdir results/kinematic_decomposition/v06a0
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .implicit_manifold import build_sphere_atlas


def _plot_atlas(atlas, outpath: Path) -> None:
    fig = plt.figure(figsize=(8.2, 7.2))
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    for chart in atlas.charts:
        pts = chart.accepted_points()
        if not pts:
            continue
        xyz = np.vstack(pts)
        ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], s=12)
        center = np.asarray(chart.center)
        ax.scatter([center[0]], [center[1]], [center[2]], s=36, marker="o")
    u = np.linspace(0.0, 2.0 * np.pi, 40)
    v = np.linspace(0.0, np.pi, 20)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_wireframe(xs, ys, zs, linewidth=0.3, alpha=0.35)
    ax.set_title("V06A0 unit-sphere atlas (software validation)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_v06a0_html(atlas, *, figure_rel: str) -> str:
    area = "—" if atlas.approximate_area is None else f"{atlas.approximate_area:.4f}"
    target = "—" if atlas.area_target is None else f"{atlas.area_target:.4f}"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06A0 — Implicit manifold engine (unit sphere)</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06A0 — Generic two-dimensional manifold engine</h1>
<div class="note"><strong>Software validation only (ADR-035).</strong> The analytical unit
sphere validates charts, overlaps, and atlas growth. This is
<code>{atlas.process_status.value}</code>, not a
<code>DecompositionCertificate</code> and not a spatial-5R
<code>FixedPositionParentResult</code>. L5 reconstruction remains unresolved.</div>
<table>
<tr><th>problem</th><td><code>{atlas.problem_id}</code></td></tr>
<tr><th>charts</th><td>{len(atlas.charts)}</td></tr>
<tr><th>components</th><td>{atlas.component_count}</td></tr>
<tr><th>closed component</th><td>{atlas.closed_component}</td></tr>
<tr><th>approximate hull area</th><td>{area} (target {target})</td></tr>
<tr><th>declared chart radius</th><td>{atlas.declared_chart_radius}</td></tr>
<tr><th>rejected duplicate centers</th><td>{len(atlas.rejected_duplicate_centers)}</td></tr>
</table>
<p><img src="{figure_rel}" alt="sphere atlas" style="max-width:720px"></p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a0 --outdir results/kinematic_decomposition/v06a0</code></p>
</body></html>
"""


def build_v06a0_readout(outdir: Path) -> Path:
    outdir = Path(outdir)
    fig_dir = outdir / "figures"
    data_dir = outdir / "data"
    fig_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    atlas = build_sphere_atlas()
    fig_path = fig_dir / "v06a0_unit_sphere_atlas.png"
    _plot_atlas(atlas, fig_path)
    payload = atlas.to_json_dict()
    json_path = data_dir / "v06a0_unit_sphere_atlas.json"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    html_path = outdir / "sprint_v06a0_implicit_manifold.html"
    html_path.write_text(
        render_v06a0_html(atlas, figure_rel=str(fig_path.relative_to(outdir))),
        encoding="utf-8",
    )
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v06a0"),
    )
    args = parser.parse_args(argv)
    path = build_v06a0_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
