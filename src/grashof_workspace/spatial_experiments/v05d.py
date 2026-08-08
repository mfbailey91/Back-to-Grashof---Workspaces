"""Active V05D runner: exact RR→U axis aggregation certificates.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05d \\
      --outdir results/kinematic_decomposition/v05d
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from .decomposition_certificate import DecompositionCertificate, issue_axis_aggregation_certificate
from .fixed_position_continuation import continue_fixed_position_fiber
from .v05_corpus import Spatial4RCorpusEntry, build_exact_u_pair_4r, build_generic_4r


def _plot_residuals(cert: DecompositionCertificate, outpath: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    cands = cert.candidates
    pair_idx = [c.pair_index for c in cands]
    dists = [max(c.distance_m, 1e-18) for c in cands]
    dots = [max(c.orthogonality_abs_dot, 1e-18) for c in cands]

    axes[0].semilogy(pair_idx, dists, "o-", label="pair distance")
    axes[0].set_title(f"{cert.source_chain_id}: consecutive pair distance")
    axes[0].set_xlabel("pair index (i,i+1)")
    axes[0].set_ylabel("distance [m]")
    axes[0].set_xticks(pair_idx)

    axes[1].semilogy(pair_idx, dots, "s-", color="#c40", label="|w·w'|")
    axes[1].set_title("orthogonality |w_i · w_{i+1}|")
    axes[1].set_xlabel("pair index")
    axes[1].set_xticks(pair_idx)

    figure.suptitle(
        f"V05D axis aggregation — status={cert.status} | topology={cert.reduced_topology}"
    )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _plot_source_vs_reduced_fiber(entry: Spatial4RCorpusEntry, cert: DecompositionCertificate, outpath: Path) -> None:
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=20, step_size=0.04)
    samples = [s for s in fiber.accepted_samples if s.q is not None]
    figure, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    if not samples or cert.aggregated is None:
        for ax in axes:
            ax.axis("off")
        axes[0].text(0.05, 0.5, f"{cert.source_chain_id}: no certified overlay\nstatus={cert.status}")
        figure.suptitle("V05D source vs reduced (empty)")
        figure.tight_layout()
        figure.savefig(outpath, dpi=160)
        plt.close(figure)
        return

    sigma = np.asarray([s.sigma for s in samples], dtype=float)
    p_res = []
    map_res = []
    agg = cert.aggregated
    p_star = np.asarray(fiber.p_star, dtype=float)
    for step in samples:
        assert step.q is not None
        q_e = agg.embed_reduced_to_source(agg.lift_source_to_reduced(step.q))
        state_s = agg.chain.evaluate(step.q)
        state_r = agg.chain.evaluate(q_e)
        p_res.append(max(float(np.linalg.norm(state_s.p - p_star)), float(np.linalg.norm(state_r.p - p_star)), 1e-18))
        map_res.append(max(float(np.linalg.norm(np.asarray(step.q) - np.asarray(q_e))), 1e-18))

    axes[0].semilogy(sigma, p_res, "o-", ms=3)
    axes[0].set_title("||p − p*|| source/reduced identity chart")
    axes[0].set_xlabel("σ")
    axes[0].set_ylabel("m")

    axes[1].semilogy(sigma, map_res, "s-", ms=3, color="#06a")
    axes[1].set_title("||q_source − embed(lift(q))||")
    axes[1].set_xlabel("σ")

    figure.suptitle(
        f"V05D source↔reduced residuals — {cert.source_chain_id} ({cert.reduced_topology})"
    )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _animate_overlay(entry: Spatial4RCorpusEntry, cert: DecompositionCertificate, outpath: Path) -> None:
    if cert.aggregated is None:
        return
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=16, step_size=0.05)
    samples = [s for s in fiber.accepted_samples if s.q is not None]
    if not samples:
        return
    stride = max(1, len(samples) // 20)
    frames = samples[::stride]
    chain = entry.model.chain
    p_star = np.asarray(fiber.p_star, dtype=float)
    u_center = np.asarray(cert.aggregated.u_center, dtype=float)

    figure = plt.figure(figsize=(7.0, 6.0))
    axis = figure.add_subplot(111, projection="3d")

    def _draw(frame_index: int) -> None:
        axis.cla()
        step = frames[frame_index]
        assert step.q is not None
        state = chain.evaluate(step.q)
        origins = np.asarray([line.r for line in state.axes], dtype=float)
        pts = np.vstack([origins, state.p.reshape(1, 3)])
        axis.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="#333", lw=2.0)
        for i, line in enumerate(state.axes):
            r = np.asarray(line.r, dtype=float)
            w = np.asarray(line.w, dtype=float)
            color = "#0a5" if i < 2 else "#06a"
            axis.quiver(r[0], r[1], r[2], w[0], w[1], w[2], length=0.12, normalize=True, color=color)
        axis.scatter([u_center[0]], [u_center[1]], [u_center[2]], c="#0a5", s=70, label="U_phys center")
        axis.scatter([p_star[0]], [p_star[1]], [p_star[2]], c="#c40", s=55, label="S_v")
        axis.set_title(
            f"{cert.source_chain_id} | {cert.reduced_topology}\n"
            f"σ={step.sigma:+.2f} | DecompositionCertificate={cert.status}"
        )
        mid = pts.mean(axis=0)
        radius = max(float(np.max(pts.max(axis=0) - pts.min(axis=0))) * 0.7, 0.35)
        axis.set_xlim(mid[0] - radius, mid[0] + radius)
        axis.set_ylim(mid[1] - radius, mid[1] + radius)
        axis.set_zlim(mid[2] - radius, mid[2] + radius)

    animation = FuncAnimation(figure, _draw, frames=len(frames), interval=120)
    animation.save(outpath, writer=PillowWriter(fps=8))
    plt.close(figure)


def render_v05d_html(
    certificates: list[DecompositionCertificate],
    *,
    figures: dict[str, str],
) -> str:
    rows = []
    for cert in certificates:
        roles = ",".join(cert.joint_role_sequence) if cert.aggregated else "—"
        rows.append(
            "<tr>"
            f"<td><code>{cert.source_chain_id}</code></td>"
            f"<td><code>{cert.status}</code></td>"
            f"<td><code>{cert.reduced_topology}</code></td>"
            f"<td><code>{roles}</code></td>"
            f"<td>{cert.tangent_subspace_error}</td>"
            f"<td>{cert.trajectory_reconstruction_error}</td>"
            "</tr>"
        )
    figure_blocks = []
    for label, rel in figures.items():
        figure_blocks.append(
            f'<h3>{label}</h3><p><img src="{rel}" alt="{label}" style="max-width: 720px;"></p>'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Active V05D — Exact Axis Aggregation</title>
<style>
  body {{ font-family: Georgia, "Times New Roman", serif; max-width: 920px; margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.45; color: #1a1a1a; }}
  h1, h2, h3 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.75rem 0 1rem; }}
  th, td {{ border: 1px solid #bbb; padding: 0.4rem 0.55rem; text-align: left; font-size: 0.92em; }}
  th {{ background: #f3f3f3; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.88em; }}
  .note {{ background: #f7f4ea; border-left: 3px solid #c4a35a; padding: 0.65rem 0.85rem; margin: 1rem 0; }}
</style>
</head>
<body>
<h1>Active V05D — Exact Axis Aggregation</h1>
<p>
Exact consecutive <code>RR→U</code> aggregation on the spatial-4R corpus, issuing a
<code>DecompositionCertificate</code> with role-aware <code>S_v-U_phys-R-R</code>
(not explorer <code>U_v</code> / <code>tool_a</code> winding semantics).
</p>
<div class="note">
<strong>Gate note.</strong>
<code>exact_u_pair_4r</code> should certify on the scoped fiber component
(<code>EXACT_ON_COMPONENT</code>); <code>generic_4r</code> is rejected.
Multi-component completeness remains unverified. V05E near-aligned rejection suite remains open.
</div>
<h2>Certificates</h2>
<table>
<tr><th>Architecture</th><th>Status</th><th>Topology</th><th>Roles</th><th>Tangent err</th><th>Trajectory err</th></tr>
{''.join(rows)}
</table>
<h2>Figures</h2>
{''.join(figure_blocks)}
<h2>Deferred</h2>
<ul>
<li>V05E near-aligned rejection corpus</li>
<li>Non-proximal <code>S_v-R-U_phys-R</code> / <code>S_v-R-R-U_phys</code> embedding certificates</li>
<li>Historical all-family winding atlas (V10)</li>
</ul>
</body>
</html>
"""


def build_v05d_readout(
    outdir: Path,
    *,
    n_fiber_steps: int = 24,
    fiber_step_size: float = 0.04,
) -> list[DecompositionCertificate]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    entries = (build_exact_u_pair_4r(), build_generic_4r())
    certificates: list[DecompositionCertificate] = []
    figures: dict[str, str] = {}

    for entry in entries:
        cert = issue_axis_aggregation_certificate(
            entry.model,
            entry.regular_q,
            n_fiber_steps=n_fiber_steps,
            fiber_step_size=fiber_step_size,
        )
        certificates.append(cert)
        stem = entry.model.architecture_id
        geo = figures_dir / f"v05d_{stem}_pair_geometry.png"
        _plot_residuals(cert, geo)
        figures[f"{stem} pair geometry"] = str(geo.relative_to(outdir))
        res = figures_dir / f"v05d_{stem}_source_reduced_residuals.png"
        _plot_source_vs_reduced_fiber(entry, cert, res)
        figures[f"{stem} source vs reduced"] = str(res.relative_to(outdir))
        if cert.aggregated is not None:
            gif = figures_dir / f"v05d_{stem}_overlay.gif"
            _animate_overlay(entry, cert, gif)
            if gif.exists():
                figures[f"{stem} overlay"] = str(gif.relative_to(outdir))

    payload = {
        "sprint": "V05D",
        "program": "kinematic_decomposition",
        "operation": "axis_aggregation",
        "gate_note": (
            "Active V05D exact RR→U aggregation; EXACT_ON_COMPONENT on scoped fiber; "
            "V05E near-aligned rejection remains open."
        ),
        "certificates": [c.to_json_dict() for c in certificates],
        "explorer_policy": "mechanism_explorer_only for spatial4bar_explorer/v05a",
    }
    (data_dir / "v05d_axis_aggregation.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    html = render_v05d_html(certificates, figures=figures)
    (outdir / "sprint_v05d_axis_aggregation.html").write_text(html, encoding="utf-8")
    return certificates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Active V05D exact axis aggregation readout")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05d"),
    )
    parser.add_argument("--n-fiber-steps", type=int, default=24)
    parser.add_argument("--fiber-step-size", type=float, default=0.04)
    args = parser.parse_args(argv)
    certs = build_v05d_readout(
        args.outdir,
        n_fiber_steps=args.n_fiber_steps,
        fiber_step_size=args.fiber_step_size,
    )
    for cert in certs:
        print(f"{cert.source_chain_id}: {cert.status} ({cert.reduced_topology})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
