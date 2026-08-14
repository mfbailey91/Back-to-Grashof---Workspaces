"""V06C readout: source orientation surface and pointing image of generic_5r.

Not a V05 curve, not all of SO(3), not S^2 coverage, not a DecompositionCertificate.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06c \\
      --outdir results/kinematic_decomposition/v06c
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .parent_atlas import (
    CONFIRM_BANK,
    DEFAULT_MAX_CHARTS,
    DISCOVERY_BANK,
    build_generic_5r_parent_atlas,
)
from .parent_task_images import (
    SphereCellKind,
    SourceTaskImageBundle,
    build_source_task_images,
)
from .v06_corpus import build_generic_5r


def _arm_polyline(chain, q: tuple[float, ...]) -> np.ndarray:
    axes = chain.current_axes(q)
    state = chain.evaluate(q)
    pts = [np.asarray(ax.r, dtype=float) for ax in axes]
    pts.append(np.asarray(state.p, dtype=float))
    return np.vstack(pts)


def _plot_images(bundle: SourceTaskImageBundle, chain, seed_q, outpath: Path) -> None:
    fig = plt.figure(figsize=(11.0, 8.0))
    ax_arm = fig.add_subplot(2, 2, 1, projection="3d")
    ax_s2 = fig.add_subplot(2, 2, 2, projection="3d")
    ax_grid = fig.add_subplot(2, 2, 3, projection="3d")
    ax_q = fig.add_subplot(2, 2, 4)

    verts = bundle.orientation.vertices
    for vertex in verts[:: max(1, len(verts) // 24)] if verts else []:
        poly = _arm_polyline(chain, vertex.q)
        ax_arm.plot(poly[:, 0], poly[:, 1], poly[:, 2], color="0.45", alpha=0.25)
    seed_poly = _arm_polyline(chain, seed_q)
    ax_arm.plot(seed_poly[:, 0], seed_poly[:, 1], seed_poly[:, 2], color="C0", alpha=0.95)
    ax_arm.set_title("source 5R (transparent) + image poses")

    for tri in bundle.pointing.mapped_triangles:
        pts = np.asarray(tri.pointing, dtype=float)
        ax_s2.add_collection3d(
            Poly3DCollection([pts], alpha=0.35, facecolor="C1", edgecolor="0.3", linewidth=0.3)
        )
    ax_s2.set_title("mapped pointing triangles (not coverage)")
    ax_s2.set_xlim(-1, 1)
    ax_s2.set_ylim(-1, 1)
    ax_s2.set_zlim(-1, 1)

    colors = {
        SphereCellKind.COVERED: "#6aa84f",
        SphereCellKind.UNCOVERED: "#cccccc",
        SphereCellKind.AMBIGUOUS_BOUNDARY: "#e69138",
        SphereCellKind.UNRESOLVED: "#cc0000",
    }
    for cell in bundle.pointing.sphere_grid.cells:
        pts = np.asarray(cell.vertices, dtype=float)
        ax_grid.add_collection3d(
            Poly3DCollection(
                [pts],
                alpha=0.35 if cell.kind is not SphereCellKind.UNCOVERED else 0.08,
                facecolor=colors[cell.kind],
                edgecolor="0.5",
                linewidth=0.2,
            )
        )
    ax_grid.set_title("icosphere cells (declared resolution)")
    ax_grid.set_xlim(-1, 1)
    ax_grid.set_ylim(-1, 1)
    ax_grid.set_zlim(-1, 1)

    quats = np.asarray([v.quaternion for v in verts], dtype=float) if verts else np.zeros((0, 4))
    rotvecs = np.asarray([v.rotvec for v in verts], dtype=float) if verts else np.zeros((0, 3))
    if len(quats):
        ax_q.scatter(quats[:, 1], quats[:, 2], c="C0", s=12, label="quat y vs z")
        ax_q.scatter(rotvecs[:, 0], rotvecs[:, 1], c="C1", s=12, marker="+", label="rotvec x vs y")
    ax_q.set_title("orientation chart (not SO(3) coverage)")
    ax_q.legend(fontsize=8)

    fig.suptitle(
        f"V06C {bundle.pointing.coverage_label.value} — generic_5r source images"
    )
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_v06c_html(bundle: SourceTaskImageBundle, *, figure_rel: str, atlas_status: str) -> str:
    grid = bundle.pointing.sphere_grid
    covered = sum(1 for c in grid.cells if c.kind is SphereCellKind.COVERED)
    uncovered = sum(1 for c in grid.cells if c.kind is SphereCellKind.UNCOVERED)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06C — generic_5r source images</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06C — source orientation and pointing truth</h1>
<div class="note"><strong>ADR-038.</strong> These are decomposition-free source task images
of a <code>{atlas_status}</code> atlas. They are not V05 orientation curves, not all of
<code>SO(3)</code>, not <code>S^2</code> completeness, and not a
<code>DecompositionCertificate</code>. Coverage label
<code>{bundle.pointing.coverage_label.value}</code>.</div>
<table>
<tr><th>orientation vertices</th><td>{len(bundle.orientation.vertices)}</td></tr>
<tr><th>orientation edges</th><td>{len(bundle.orientation.edges)}</td></tr>
<tr><th>mapped spherical triangles</th><td>{len(bundle.pointing.mapped_triangles)}</td></tr>
<tr><th>unresolved faces</th><td>{bundle.pointing.unresolved_face_count}</td></tr>
<tr><th>icosphere level / cells</th><td>{grid.subdivision_level} / {grid.cell_count}</td></tr>
<tr><th>max cell diameter (rad)</th><td>{grid.max_cell_diameter_rad:.4f}</td></tr>
<tr><th>covered / uncovered cells</th><td>{covered} / {uncovered}</td></tr>
<tr><th>critical / near-critical vertices</th><td>{len(bundle.pointing.critical_vertex_ids)} / {len(bundle.pointing.near_critical_vertex_ids)}</td></tr>
</table>
<p><img src="{figure_rel}" alt="source images" style="max-width:720px"></p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06c --outdir results/kinematic_decomposition/v06c</code></p>
</body></html>
"""


def build_v06c_readout(
    outdir: Path,
    *,
    max_charts: int = DEFAULT_MAX_CHARTS,
    discovery_bank: int = DISCOVERY_BANK,
    confirmation_bank: int = CONFIRM_BANK,
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
    bundle = build_source_task_images(atlas, entry.model)
    fig_path = fig_dir / "v06c_generic_5r_source_images.png"
    _plot_images(bundle, entry.model.chain, atlas.seed_q, fig_path)
    json_path = data_dir / "v06c_generic_5r_source_images.json"
    payload = {
        "atlas": {
            "representation_status": atlas.representation_status.value,
            "chart_count": len(atlas.charts),
            "component_ids": list(atlas.component_ids),
            "fiber_ids": list(atlas.fiber_ids),
            "certificate_status": None,
        },
        "images": bundle.to_json_dict(),
    }
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    html_path = outdir / "sprint_v06c_source_images.html"
    html_path.write_text(
        render_v06c_html(
            bundle,
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
        default=Path("results/kinematic_decomposition/v06c"),
    )
    args = parser.parse_args(argv)
    path = build_v06c_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
