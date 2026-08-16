"""V06E readout: source-fiber reconstruction vs empty accepted-child reconstruction.

Not S^2 completeness, not an exact product, not descriptor discovery.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06e \\
      --outdir results/kinematic_decomposition/v06e
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .parent_atlas import build_generic_5r_parent_atlas
from .parent_level_sets import ParentLevelSetResult, build_parent_level_sets
from .parent_reconstruction import ParentReconstructionResult, build_parent_reconstruction
from .parent_task_images import SourceTaskImageBundle, SphereCellKind, build_source_task_images
from .v06_corpus import build_generic_5r


def _plot(
    images: SourceTaskImageBundle,
    level_sets: ParentLevelSetResult,
    result: ParentReconstructionResult,
    outpath: Path,
) -> None:
    fig = plt.figure(figsize=(11.0, 5.2))
    ax_grid = fig.add_subplot(1, 2, 1, projection="3d")
    ax_child = fig.add_subplot(1, 2, 2, projection="3d")
    missed = set(result.missed_covered_cell_ids)
    hits = set(result.fiber_hit_cell_ids)
    for cell in images.pointing.sphere_grid.cells:
        pts = np.asarray(cell.vertices, dtype=float)
        if cell.cell_id in missed:
            color, alpha = "#cc0000", 0.45
        elif cell.cell_id in hits:
            color, alpha = "#6aa84f", 0.4
        elif cell.kind is SphereCellKind.COVERED:
            color, alpha = "#9fc5e8", 0.25
        else:
            color, alpha = "#dddddd", 0.06
        ax_grid.add_collection3d(
            Poly3DCollection([pts], alpha=alpha, facecolor=color, edgecolor="0.5", linewidth=0.2)
        )
    for fiber in level_sets.fibers:
        if not fiber.samples:
            continue
        arr = np.asarray([s.pointing for s in fiber.samples], dtype=float)
        ax_grid.plot(arr[:, 0], arr[:, 1], arr[:, 2], color="C3", lw=1.2, alpha=0.85)
    ax_grid.set_title("V06C grid + source-fiber traces")
    ax_grid.set_xlim(-1, 1)
    ax_grid.set_ylim(-1, 1)
    ax_grid.set_zlim(-1, 1)
    ax_child.set_title("accepted-child reconstruction (empty)")
    ax_child.set_xlim(-1, 1)
    ax_child.set_ylim(-1, 1)
    ax_child.set_zlim(-1, 1)
    ax_child.text2D(0.15, 0.5, "no EXACT_* children", transform=ax_child.transAxes)
    fig.suptitle(
        f"V06E {result.factorization_status} — V06 not passed"
    )
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_v06e_html(result: ParentReconstructionResult, *, figure_rel: str) -> str:
    m = result.metrics
    gate_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in result.v06_gate.items()
    )
    miss = "unevaluable" if m.missed_covered_fraction is None else f"{m.missed_covered_fraction:.3f}"
    fp = "unevaluable" if m.false_positive_fraction is None else f"{m.false_positive_fraction:.3f}"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06E — reconstruction closeout</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06E — source-fiber vs accepted-child reconstruction</h1>
<div class="note"><strong>ADR-042 / ADR-043 / ADR-047.</strong> Painting task-derived fibers onto the frozen
V06C grid is not parent completeness. Empty interior <code>COVERED</code> cells make the
miss metric unevaluable. Empty accepted children keep factorization
<code>unresolved</code> (not <code>no valid recombination</code>).
No <code>EXACT_GLOBAL</code> / <code>EXACT_ON_COMPONENT</code> children exist.
Descriptor discovery stays blocked (ADR-026). V06 program gate:
<strong>not passed</strong>. V07A held.</div>
<table>
<tr><th>direct coverage</th><td>{result.coverage_label}</td></tr>
<tr><th>reconstruction coverage</th><td>{result.reconstruction_coverage}</td></tr>
<tr><th>complete foliation</th><td>{result.complete_foliation}</td></tr>
<tr><th>factorization</th><td>{result.factorization_status}</td></tr>
<tr><th>fiber-hit / missed COVERED fraction</th>
<td>{m.fiber_hit_cells} / {miss}</td></tr>
<tr><th>false-positive fraction</th><td>{fp}</td></tr>
<tr><th>coverage comparison</th>
<td>{"evaluable" if m.coverage_comparison_evaluable else "unevaluable"} — {m.coverage_comparison_reason}</td></tr>
<tr><th>accepted children</th><td>{m.accepted_child_count}</td></tr>
<tr><th>Hausdorff (rad)</th><td>{m.hausdorff_rad}</td></tr>
<tr><th>icosphere level</th><td>{result.icosphere_level}</td></tr>
</table>
<h2>V06 gate checklist</h2>
<table><tr><th>item</th><th>met</th></tr>{gate_rows}</table>
<p><img src="{figure_rel}" alt="V06E reconstruction" style="max-width:720px"></p>
<h2>Prior V06 artifacts</h2>
<p>
<a href="../v06a0/sprint_v06a0_implicit_manifold.html">A0</a> ·
<a href="../v06a1/sprint_v06a1_local_parent_patch.html">A1</a> ·
<a href="../v06a2/sprint_v06a2_parent_atlas.html">A2</a> ·
<a href="../v06c/sprint_v06c_source_images.html">C</a> ·
<a href="../v06b/sprint_v06b_compound_parent.html">B</a> ·
<a href="../v06d1/sprint_v06d1_level_sets.html">D1</a> ·
<a href="../v06d2/sprint_v06d2_virtual_u_child.html">D2</a>
</p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06e --outdir results/kinematic_decomposition/v06e</code></p>
</body></html>
"""


def build_v06e_readout(
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
    images = build_source_task_images(atlas, entry.model)
    level_sets = build_parent_level_sets(atlas, entry.model)
    result = build_parent_reconstruction(atlas, entry.model, images, level_sets)
    fig_path = fig_dir / "v06e_reconstruction_comparison.png"
    _plot(images, level_sets, result, fig_path)
    payload = {
        "atlas": {
            "representation_status": atlas.representation_status.value,
            "certificate_status": None,
        },
        "reconstruction": result.to_json_dict(),
    }
    json_path = data_dir / "v06e_reconstruction.json"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    html_path = outdir / "sprint_v06e_reconstruction.html"
    html_path.write_text(
        render_v06e_html(result, figure_rel=str(fig_path.relative_to(outdir))),
        encoding="utf-8",
    )
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v06e"),
    )
    args = parser.parse_args(argv)
    path = build_v06e_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
