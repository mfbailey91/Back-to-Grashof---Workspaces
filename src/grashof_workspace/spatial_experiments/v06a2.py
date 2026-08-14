"""V06A2 readout: generic_5r multi-chart parent atlas + component discovery.

Representation is not a complete parent and not a DecompositionCertificate.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a2 \\
      --outdir results/kinematic_decomposition/v06a2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .parent_atlas import (
    CONFIRM_BANK,
    DEFAULT_MAX_CHARTS,
    DISCOVERY_BANK,
    ParentAtlasResult,
    build_generic_5r_parent_atlas,
)
from .serial_chain import SerialRevoluteChain
from .v06_corpus import build_generic_5r


def _arm_polyline(chain: SerialRevoluteChain, q: tuple[float, ...]) -> np.ndarray:
    axes = chain.current_axes(q)
    state = chain.evaluate(q)
    pts = [np.asarray(ax.r, dtype=float) for ax in axes]
    pts.append(np.asarray(state.p, dtype=float))
    return np.vstack(pts)


def _plot_atlas(result: ParentAtlasResult, chain: SerialRevoluteChain, outpath: Path) -> None:
    accepted = [v for v in result.vertices if v.accepted]
    fig = plt.figure(figsize=(11.0, 8.0))
    ax_arm = fig.add_subplot(2, 2, 1, projection="3d")
    ax_s2 = fig.add_subplot(2, 2, 2, projection="3d")
    ax_m = fig.add_subplot(2, 2, 3)
    ax_f = fig.add_subplot(2, 2, 4)

    for i, vertex in enumerate(accepted[:: max(1, len(accepted) // 24)]):
        poly = _arm_polyline(chain, vertex.q)
        ax_arm.plot(poly[:, 0], poly[:, 1], poly[:, 2], color="0.45", alpha=0.25)
    seed_poly = _arm_polyline(chain, result.seed_q)
    ax_arm.plot(seed_poly[:, 0], seed_poly[:, 1], seed_poly[:, 2], color="C0", alpha=0.95)
    ax_arm.set_title("source 5R (transparent) + atlas poses")

    if accepted:
        ds = np.asarray([v.pointing for v in accepted], dtype=float)
        ax_s2.scatter(ds[:, 0], ds[:, 1], ds[:, 2], c="C1", s=12)
    u = np.linspace(0.0, 2.0 * np.pi, 24)
    v = np.linspace(0.0, np.pi, 12)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax_s2.plot_wireframe(xs, ys, zs, linewidth=0.3, alpha=0.3)
    ax_s2.set_title("mapped pointing (not coverage)")

    residuals = [v.p_residual_m or 0.0 for v in accepted]
    ax_m.plot(residuals, label="||p-p*||")
    ax_m.plot([v.rank_jp for v in accepted], label="rank Jp")
    ax_m.plot([v.rank_jd_np for v in accepted], label="rank(Jd Np)")
    ax_m.set_title("vertex residual and ranks")
    ax_m.legend(fontsize=8)

    kinds = ["OPEN", "SINGULAR", "BUDGET_LIMITED"]
    counts = [
        sum(1 for f in result.frontiers if f.kind.value == k) for k in kinds
    ]
    ax_f.bar(kinds, counts)
    ax_f.set_title(f"frontiers; charts={len(result.charts)}")

    fig.suptitle(
        f"V06A2 {result.representation_status.value} — generic_5r (not a complete parent)"
    )
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_v06a2_html(result: ParentAtlasResult, *, figure_rel: str) -> str:
    res = "—" if result.max_p_residual_m is None else f"{result.max_p_residual_m:.3e}"
    comps = ", ".join(result.component_ids) or "(none)"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06A2 — generic_5r parent atlas</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06A2 — generic_5r parent atlas</h1>
<div class="note"><strong>ADR-037.</strong> Representation status
<code>{result.representation_status.value}</code> is not a complete parent,
not <code>S^2</code> coverage, and not a <code>DecompositionCertificate</code>.
Discovery <code>{result.discovery.status.value}</code>. Fibers are empty.
Joint limits are <code>{result.joint_limits}</code>.</div>
<table>
<tr><th>charts</th><td>{len(result.charts)}</td></tr>
<tr><th>overlaps</th><td>{len(result.overlaps)}</td></tr>
<tr><th>frontiers</th><td>{len(result.frontiers)}</td></tr>
<tr><th>component_ids</th><td><code>{comps}</code></td></tr>
<tr><th>discovery bank / confirm</th><td>{result.discovery.bank_size} / {result.discovery.confirmation_bank_size}</td></tr>
<tr><th>projected / unattached</th><td>{result.discovery.projected_seed_count} / {result.discovery.unattached_seed_count}</td></tr>
<tr><th>max position residual (m)</th><td>{res}</td></tr>
<tr><th>seed FD Jp error</th><td>{result.seed_fd_jp_error:.3e} (verified={result.seed_fd_verified})</td></tr>
<tr><th>fibers</th><td>{len(result.fiber_ids)}</td></tr>
</table>
<p><img src="{figure_rel}" alt="parent atlas" style="max-width:720px"></p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a2 --outdir results/kinematic_decomposition/v06a2</code></p>
</body></html>
"""


def build_v06a2_readout(
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
    result = build_generic_5r_parent_atlas(
        entry,
        max_charts=max_charts,
        discovery_bank=discovery_bank,
        confirmation_bank=confirmation_bank,
    )
    fig_path = fig_dir / "v06a2_generic_5r_parent_atlas.png"
    _plot_atlas(result, entry.model.chain, fig_path)
    json_path = data_dir / "v06a2_generic_5r_parent_atlas.json"
    json_path.write_text(
        json.dumps(result.to_json_dict(), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    html_path = outdir / "sprint_v06a2_parent_atlas.html"
    html_path.write_text(
        render_v06a2_html(result, figure_rel=str(fig_path.relative_to(outdir))),
        encoding="utf-8",
    )
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v06a2"),
    )
    args = parser.parse_args(argv)
    path = build_v06a2_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
