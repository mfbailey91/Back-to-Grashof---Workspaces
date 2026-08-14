"""V06D1 readout: task-derived h=c source fibers of generic_5r.

Not U_v, not UUUR, not parent completeness, not reconstruction.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06d1 \\
      --outdir results/kinematic_decomposition/v06d1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .parent_atlas import ParentAtlasResult, build_generic_5r_parent_atlas
from .parent_level_sets import ParentLevelSetResult, build_parent_level_sets
from .v06_corpus import build_generic_5r


def _plot_level_sets(result: ParentLevelSetResult, atlas: ParentAtlasResult, outpath: Path) -> None:
    fig = plt.figure(figsize=(10.5, 5.2))
    ax_mesh = fig.add_subplot(1, 2, 1, projection="3d")
    ax_fiber = fig.add_subplot(1, 2, 2, projection="3d")

    verts = [v for v in atlas.vertices if v.accepted]
    if verts:
        pts = np.asarray([v.pointing for v in verts], dtype=float)
        ax_mesh.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c="0.65", s=8, alpha=0.35)
        ax_fiber.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c="0.75", s=6, alpha=0.2)

    colors = ("C0", "C1", "C2")
    for i, sl in enumerate(result.slices):
        color = colors[i % 3]
        for contour in sl.contours:
            matching = [f for f in result.fibers if f.contour_id == contour.component_id]
            if matching and matching[0].samples:
                arr = np.asarray([s.pointing for s in matching[0].samples], dtype=float)
                ax_mesh.plot(arr[:, 0], arr[:, 1], arr[:, 2], color=color, alpha=0.55, lw=1.2)

    overlay = next((f for f in result.fibers if f.samples), None)
    if overlay is not None:
        arr = np.asarray([s.pointing for s in overlay.samples], dtype=float)
        ax_fiber.plot(arr[:, 0], arr[:, 1], arr[:, 2], color="C3", lw=2.0)
        ax_fiber.scatter(arr[0, 0], arr[0, 1], arr[0, 2], c="C3", s=30)

    for ax in (ax_mesh, ax_fiber):
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_zlim(-1, 1)
        ax.set_xlabel("d_x")
        ax.set_ylabel("d_y")
        ax.set_zlabel("d_z")
    ax_mesh.set_title("parent pointing (transparent) + slice contours")
    ax_fiber.set_title("one continued source fiber")
    fig.suptitle("V06D1 task-derived h=c fibers — not a 2D parent")
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_v06d1_html(result: ParentLevelSetResult, *, figure_rel: str, atlas_status: str) -> str:
    fiber_rows = "".join(
        f"<tr><td><code>{f.fiber_id}</code></td><td>{f.c:.4f}</td>"
        f"<td>{f.branch_status}</td><td>{len(f.samples)}</td></tr>"
        for f in result.fibers
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06D1 — task-derived source level sets</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06D1 — task-derived source level sets</h1>
<div class="note"><strong>ADR-040.</strong> Fibers of <code>h(d)=n·d = c</code> are
source evidence for a declared slice on a <code>{atlas_status}</code> atlas.
They are not parent completeness, not <code>U_v</code>, and not child reconstruction.
Not a complete foliation. Joint limits <code>not_modeled</code>.</div>
<table>
<tr><th>n</th><td>{result.n}</td></tr>
<tr><th>ε_h</th><td>{result.eps_h}</td></tr>
<tr><th>regular vertices</th><td>{sum(1 for v in result.vertices if v.regular)} / {len(result.vertices)}</td></tr>
<tr><th>slice values</th><td>{", ".join(f"{c:.4f}" for c in result.slice_values)}</td></tr>
<tr><th>fiber count</th><td>{len(result.fibers)}</td></tr>
<tr><th>complete foliation</th><td>{result.complete_foliation}</td></tr>
</table>
<table>
<tr><th>fiber_id</th><th>c</th><th>branch</th><th>samples</th></tr>
{fiber_rows}
</table>
<p><img src="{figure_rel}" alt="V06D1 level sets" style="max-width:720px"></p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06d1 --outdir results/kinematic_decomposition/v06d1</code></p>
</body></html>
"""


def build_v06d1_readout(
    outdir: Path,
    *,
    max_charts: int = 6,
    discovery_bank: int = 16,
    confirmation_bank: int = 16,
) -> Path:
    outdir = Path(outdir)
    fig_dir = outdir / "figures"
    data_dir = outdir / "data"
    fig_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    entry = build_generic_5r()
    atlas = build_generic_5r_parent_atlas(
        entry,
        max_charts=max_charts,
        discovery_bank=discovery_bank,
        confirmation_bank=confirmation_bank,
    )
    result = build_parent_level_sets(atlas, entry.model)
    fig_path = fig_dir / "v06d1_generic_5r_level_sets.png"
    _plot_level_sets(result, atlas, fig_path)
    json_path = data_dir / "v06d1_generic_5r_level_sets.json"
    payload = {
        "atlas": {
            "representation_status": atlas.representation_status.value,
            "chart_count": len(atlas.charts),
            "component_ids": list(atlas.component_ids),
            "fiber_ids": [f.fiber_id for f in result.fibers],
            "certificate_status": None,
        },
        "level_sets": result.to_json_dict(),
    }
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    html_path = outdir / "sprint_v06d1_level_sets.html"
    html_path.write_text(
        render_v06d1_html(
            result,
            figure_rel=str(fig_path.relative_to(outdir)),
            atlas_status=atlas.representation_status.value,
        ),
        encoding="utf-8",
    )
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v06d1"),
    )
    args = parser.parse_args(argv)
    path = build_v06d1_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
