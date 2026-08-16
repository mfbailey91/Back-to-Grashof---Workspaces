"""V06D2 readout: local U_v chart and one UUUR child on exact_two_u_5r.

Not a six-family sweep, not parent completeness, not reconstruction.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06d2 \\
      --outdir results/kinematic_decomposition/v06d2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .serial_chain import SerialRevoluteChain
from .v06_corpus import (
    Spatial5RCorpusEntry,
    build_exact_two_u_5r,
    build_generic_5r,
    build_near_two_u_5r,
)
from .virtual_u_child import V06D2ArchitectureResult, evaluate_v06d2_architecture


def _arm_polyline(chain: SerialRevoluteChain, q: tuple[float, ...]) -> np.ndarray:
    axes = chain.current_axes(q)
    state = chain.evaluate(q)
    pts = [np.asarray(ax.r, dtype=float) for ax in axes]
    pts.append(np.asarray(state.p, dtype=float))
    return np.vstack(pts)


def _plot(entry: Spatial5RCorpusEntry, result: V06D2ArchitectureResult, outpath: Path) -> None:
    fig = plt.figure(figsize=(11.0, 5.2))
    ax_arm = fig.add_subplot(1, 2, 1, projection="3d")
    ax_s2 = fig.add_subplot(1, 2, 2, projection="3d")
    poly = _arm_polyline(entry.model.chain, entry.regular_q)
    ax_arm.plot(poly[:, 0], poly[:, 1], poly[:, 2], color="0.55", alpha=0.35)
    ax_arm.plot(poly[:, 0], poly[:, 1], poly[:, 2], color="C0", alpha=0.9)
    p = np.asarray(result.chart.p_star if result.chart else (0, 0, 0), dtype=float)
    if result.chart is not None:
        a = np.asarray(result.chart.a, dtype=float)
        b = np.asarray(result.chart.b, dtype=float)
        ax_arm.quiver(*p, *a, length=0.08, color="C1")
        ax_arm.quiver(*p, *b, length=0.08, color="C2")
    ax_arm.set_title("source 5R (transparent) + local U_v axes")

    if result.samples:
        pts = np.asarray([s.pointing for s in result.samples], dtype=float)
        ax_s2.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="C3", lw=2.0)
        ax_s2.scatter(pts[0, 0], pts[0, 1], pts[0, 2], c="C3", s=28)
    ax_s2.set_xlim(-1, 1)
    ax_s2.set_ylim(-1, 1)
    ax_s2.set_zlim(-1, 1)
    ax_s2.set_title("UUUR child pointing samples")
    fig.suptitle(
        f"V06D2 {result.certificate.closed_mechanism_status} — not reconstruction"
    )
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_v06d2_html(payload: dict[str, Any], *, figure_rel: str) -> str:
    exact = payload["exact_two_u_5r"]["certificate"]
    near = payload["near_two_u_5r"]["certificate"]
    generic = payload["generic_5r"]["certificate"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06D2 — virtual U and one UUUR child</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06D2 — task-derived virtual U and one UUUR child</h1>
<div class="note"><strong>ADR-041.</strong> A local <code>(d×n)</code> virtual-U chart plus
one <code>U_v-U_phys-U_phys-R</code> comparison is not parent completeness, not a
six-family atlas, and not reconstruction. Child status is issued from the
certificate, never pre-accepted. Drive is pseudo-arclength <code>s</code>
from the H3 augmented corrector (ADR-044 / ADR-045). Local equivalence is
conjunctive (ADR-043).</div>
<table>
<tr><th>architecture</th><th>axis_aggregation</th><th>closed_mechanism</th><th>status</th></tr>
<tr><td><code>exact_two_u_5r</code></td><td>{exact["axis_aggregation_status"]}</td>
<td>{exact["closed_mechanism_status"]}</td><td>{exact["status"]}</td></tr>
<tr><td><code>near_two_u_5r</code></td><td>{near["axis_aggregation_status"]}</td>
<td>{near["closed_mechanism_status"]}</td><td>{near["status"]}</td></tr>
<tr><td><code>generic_5r</code></td><td>{generic["axis_aggregation_status"]}</td>
<td>{generic["closed_mechanism_status"]}</td><td>{generic["status"]}</td></tr>
</table>
<p><img src="{figure_rel}" alt="V06D2 overlay" style="max-width:720px"></p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06d2 --outdir results/kinematic_decomposition/v06d2</code></p>
</body></html>
"""


def build_v06d2_readout(
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
    exact_entry = build_exact_two_u_5r()
    exact = evaluate_v06d2_architecture(
        exact_entry,
        max_charts=max_charts,
        discovery_bank=discovery_bank,
        confirmation_bank=confirmation_bank,
    )
    near = evaluate_v06d2_architecture(build_near_two_u_5r(), grow_source=False)
    generic = evaluate_v06d2_architecture(build_generic_5r(), grow_source=False)
    payload = {
        "exact_two_u_5r": exact.to_json_dict(),
        "near_two_u_5r": near.to_json_dict(),
        "generic_5r": generic.to_json_dict(),
        "notes": [
            "One UUUR child only; not a six-family sweep (ADR-041).",
        ],
    }
    fig_path = fig_dir / "v06d2_virtual_u_child.png"
    _plot(exact_entry, exact, fig_path)
    json_path = data_dir / "v06d2_virtual_u_child.json"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    html_path = outdir / "sprint_v06d2_virtual_u_child.html"
    html_path.write_text(
        render_v06d2_html(payload, figure_rel=str(fig_path.relative_to(outdir))),
        encoding="utf-8",
    )
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v06d2"),
    )
    args = parser.parse_args(argv)
    path = build_v06d2_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
