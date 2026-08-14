"""V06B readout: SUUR compound parent vs near-miss control.

Axis aggregation EXACT_GLOBAL is not a complete closed-parent certificate.
SUUR is not UUUR and does not introduce U_v.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06b \\
      --outdir results/kinematic_decomposition/v06b
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .compound_parent import V06BArchitectureResult, evaluate_v06b_architecture
from .serial_chain import SerialRevoluteChain
from .v06_corpus import (
    Spatial5RCorpusEntry,
    build_exact_two_u_5r,
    build_generic_5r,
    build_near_two_u_5r,
)


def _arm_polyline(chain: SerialRevoluteChain, q: tuple[float, ...]) -> np.ndarray:
    axes = chain.current_axes(q)
    state = chain.evaluate(q)
    pts = [np.asarray(ax.r, dtype=float) for ax in axes]
    pts.append(np.asarray(state.p, dtype=float))
    return np.vstack(pts)


def _plot(
    exact_entry: Spatial5RCorpusEntry,
    near_entry: Spatial5RCorpusEntry,
    exact_result: V06BArchitectureResult,
    outpath: Path,
) -> None:
    fig = plt.figure(figsize=(11.0, 8.0))
    ax_e = fig.add_subplot(2, 2, 1, projection="3d")
    ax_n = fig.add_subplot(2, 2, 2, projection="3d")
    ax_t = fig.add_subplot(2, 2, 3)
    ax_s = fig.add_subplot(2, 2, 4)
    poly = _arm_polyline(exact_entry.model.chain, exact_entry.regular_q)
    ax_e.plot(poly[:, 0], poly[:, 1], poly[:, 2], color="C0", alpha=0.95)
    ax_e.plot(poly[:, 0], poly[:, 1], poly[:, 2], color="0.5", alpha=0.3)
    ax_e.set_title("exact_two_u_5r source (transparent overlay)")
    poly_n = _arm_polyline(near_entry.model.chain, near_entry.regular_q)
    ax_n.plot(poly_n[:, 0], poly_n[:, 1], poly_n[:, 2], color="C3", alpha=0.9)
    ax_n.set_title("near_two_u_5r control")
    labels = ["exact axis", "exact closed", "near axis", "generic axis"]
    ax_t.axis("off")
    ax_t.set_title("certificate split (ADR-039)")
    rows = [
        f"exact axis={exact_result.certificate.axis_aggregation_status}",
        f"exact closed={exact_result.certificate.closed_mechanism_status}",
        f"reduced charts={exact_result.reduced_chart_count}",
    ]
    ax_t.text(0.05, 0.6, "\n".join(rows), fontsize=10, family="monospace")
    _ = labels
    ax_s.axis("off")
    ax_s.text(
        0.05,
        0.5,
        "SUUR ≠ UUUR\nNo U_v\nLOCAL_ONLY ≠ EXACT_ON_COMPONENT",
        fontsize=11,
    )
    fig.suptitle("V06B S_v-U_phys-U_phys-R — not a complete parent")
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_html(payload: dict[str, Any], *, figure_rel: str) -> str:
    exact = payload["exact_two_u_5r"]["certificate"]
    near = payload["near_two_u_5r"]["certificate"]
    generic = payload["generic_5r"]["certificate"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06B — SUUR compound parent</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06B — structured S_v-U_phys-U_phys-R parent</h1>
<div class="note"><strong>ADR-039.</strong> Two-pair axis aggregation
<code>EXACT_GLOBAL</code> is not closed-mechanism completeness. SUUR is not
<code>UUUR</code> and does not introduce <code>U_v</code>. Near control must reject.
<code>DecompositionCertificate</code> closed status for the exact source is
<code>{exact["closed_mechanism_status"]}</code>.</div>
<table>
<tr><th>architecture</th><th>axis_aggregation</th><th>closed_mechanism</th><th>status</th></tr>
<tr><td><code>exact_two_u_5r</code></td><td>{exact["axis_aggregation_status"]}</td>
<td>{exact["closed_mechanism_status"]}</td><td>{exact["status"]}</td></tr>
<tr><td><code>near_two_u_5r</code></td><td>{near["axis_aggregation_status"]}</td>
<td>{near["closed_mechanism_status"]}</td><td>{near["status"]}</td></tr>
<tr><td><code>generic_5r</code></td><td>{generic["axis_aggregation_status"]}</td>
<td>{generic["closed_mechanism_status"]}</td><td>{generic["status"]}</td></tr>
</table>
<p><img src="{figure_rel}" alt="V06B overlay" style="max-width:720px"></p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06b --outdir results/kinematic_decomposition/v06b</code></p>
</body></html>
"""


def build_v06b_readout(outdir: Path, *, max_charts: int = 6) -> Path:
    outdir = Path(outdir)
    fig_dir = outdir / "figures"
    data_dir = outdir / "data"
    fig_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    exact_entry = build_exact_two_u_5r()
    near_entry = build_near_two_u_5r()
    generic_entry = build_generic_5r()
    exact = evaluate_v06b_architecture(exact_entry, grow_atlases=True, max_charts=max_charts)
    near = evaluate_v06b_architecture(near_entry, grow_atlases=False)
    generic = evaluate_v06b_architecture(generic_entry, grow_atlases=False)
    payload = {
        "certificate_status_note": "closed_mechanism_status is the certificate status; axis_aggregation is separate",
        "exact_two_u_5r": exact.to_json_dict(),
        "near_two_u_5r": near.to_json_dict(),
        "generic_5r": generic.to_json_dict(),
    }
    json_path = data_dir / "v06b_compound_parent.json"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    fig_path = fig_dir / "v06b_compound_parent.png"
    _plot(exact_entry, near_entry, exact, fig_path)
    html_path = outdir / "sprint_v06b_compound_parent.html"
    html_path.write_text(
        render_html(payload, figure_rel=str(fig_path.relative_to(outdir))),
        encoding="utf-8",
    )
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v06b"),
    )
    args = parser.parse_args(argv)
    path = build_v06b_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
