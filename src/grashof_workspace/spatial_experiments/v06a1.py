"""V06A1 readout: one local hexagonal chart of generic_5r.

Representation status LOCAL_PATCH. Not a complete parent, not S^2 coverage,
and not a DecompositionCertificate.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a1 \\
      --outdir results/kinematic_decomposition/v06a1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .parent_local import (
    FixedPositionParentResult,
    build_generic_5r_local_patch,
)
from .serial_chain import SerialRevoluteChain
from .v06_corpus import build_generic_5r


def _arm_polyline(chain: SerialRevoluteChain, q: tuple[float, ...]) -> np.ndarray:
    axes = chain.current_axes(q)
    state = chain.evaluate(q)
    pts = [np.asarray(ax.r, dtype=float) for ax in axes]
    pts.append(np.asarray(state.p, dtype=float))
    return np.vstack(pts)


def _plot_local_patch(result: FixedPositionParentResult, chain: SerialRevoluteChain, outpath: Path) -> None:
    accepted = [v for v in result.vertices if v.accepted]
    fig = plt.figure(figsize=(11.0, 8.0))
    ax_arm = fig.add_subplot(2, 2, 1, projection="3d")
    ax_u = fig.add_subplot(2, 2, 2)
    ax_s2 = fig.add_subplot(2, 2, 3, projection="3d")
    ax_m = fig.add_subplot(2, 2, 4)

    for i, vertex in enumerate(accepted):
        poly = _arm_polyline(chain, vertex.q)
        alpha = 0.25 if i else 0.9
        ax_arm.plot(poly[:, 0], poly[:, 1], poly[:, 2], color="0.4", alpha=alpha)
    ax_arm.set_title("source 5R (transparent) + local chart poses")
    ax_arm.set_xlabel("x")
    ax_arm.set_ylabel("y")
    ax_arm.set_zlabel("z")

    us = np.asarray([v.u for v in accepted], dtype=float)
    ax_u.scatter(us[:, 0], us[:, 1], c="C0")
    ax_u.set_aspect("equal")
    ax_u.set_title("local chart coordinates u")
    ax_u.set_xlabel("u1")
    ax_u.set_ylabel("u2")

    ds = np.asarray([v.pointing for v in accepted], dtype=float)
    ax_s2.scatter(ds[:, 0], ds[:, 1], ds[:, 2], c="C1")
    u = np.linspace(0.0, 2.0 * np.pi, 24)
    v = np.linspace(0.0, np.pi, 12)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax_s2.plot_wireframe(xs, ys, zs, linewidth=0.3, alpha=0.3)
    ax_s2.set_title("mapped pointing (not coverage)")

    residuals = [v.p_residual_m or 0.0 for v in accepted]
    ranks_p = [v.rank_jp for v in accepted]
    ranks_d = [v.rank_jd_np for v in accepted]
    ax_m.plot(residuals, label="||p-p*||")
    ax_m.plot(ranks_p, label="rank Jp")
    ax_m.plot(ranks_d, label="rank(Jd Np)")
    ax_m.set_title("residual and ranks")
    ax_m.legend(fontsize=8)

    fig.suptitle("V06A1 LOCAL_PATCH — generic_5r (not a complete parent)")
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def render_v06a1_html(result: FixedPositionParentResult, *, figure_rel: str) -> str:
    n_acc = sum(1 for v in result.vertices if v.accepted)
    res = "—" if result.max_p_residual_m is None else f"{result.max_p_residual_m:.3e}"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V06A1 — generic_5r local parent patch</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; line-height: 1.45; }}
code {{ font-family: ui-monospace, monospace; }}
.note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
table {{ border-collapse: collapse; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
</style></head><body>
<h1>V06A1 — One local generic_5r parent chart</h1>
<div class="note"><strong>LOCAL_PATCH (ADR-036).</strong> One hexagonal chart of
<code>{result.architecture_id}</code> at a regular seed. This is
<code>{result.representation_status.value}</code>, not a complete parent component,
not <code>S^2</code> coverage, and not a <code>DecompositionCertificate</code>.
<code>component_ids</code> are empty. Joint limits are <code>{result.joint_limits}</code>.</div>
<table>
<tr><th>accepted samples</th><td>{n_acc}</td></tr>
<tr><th>max position residual (m)</th><td>{res}</td></tr>
<tr><th>seed FD Jp error</th><td>{result.seed_fd_jp_error:.3e} (verified={result.seed_fd_verified})</td></tr>
<tr><th>fibers</th><td>{len(result.fiber_ids)}</td></tr>
<tr><th>chart id</th><td><code>{None if result.chart is None else result.chart.chart_id}</code></td></tr>
</table>
<p><img src="{figure_rel}" alt="local patch" style="max-width:720px"></p>
<p>Reproduce:
<code>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a1 --outdir results/kinematic_decomposition/v06a1</code></p>
</body></html>
"""


def build_v06a1_readout(outdir: Path) -> Path:
    outdir = Path(outdir)
    fig_dir = outdir / "figures"
    data_dir = outdir / "data"
    fig_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    entry = build_generic_5r()
    result = build_generic_5r_local_patch(entry)
    fig_path = fig_dir / "v06a1_generic_5r_local_patch.png"
    _plot_local_patch(result, entry.model.chain, fig_path)
    json_path = data_dir / "v06a1_generic_5r_local_patch.json"
    json_path.write_text(
        json.dumps(result.to_json_dict(), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    html_path = outdir / "sprint_v06a1_local_parent_patch.html"
    html_path.write_text(
        render_v06a1_html(result, figure_rel=str(fig_path.relative_to(outdir))),
        encoding="utf-8",
    )
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v06a1"),
    )
    args = parser.parse_args(argv)
    path = build_v06a1_readout(args.outdir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
