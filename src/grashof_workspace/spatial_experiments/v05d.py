"""Active V05D runner: exact RR→U axis aggregation without loop overclaim.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05d \
      --outdir results/kinematic_decomposition/v05d
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

from .decomposition_certificate import DecompositionCertificate, issue_axis_aggregation_certificate
from .v05_corpus import build_exact_u_pair_4r, build_generic_4r


def _plot_pair_geometry(cert: DecompositionCertificate, outpath: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    candidates = cert.candidates
    pair_indices = [candidate.pair_index for candidate in candidates]
    distances = [max(candidate.distance_m, 1e-18) for candidate in candidates]
    dots = [max(candidate.orthogonality_abs_dot, 1e-18) for candidate in candidates]

    axes[0].semilogy(pair_indices, distances, "o-")
    axes[0].set_title(f"{cert.source_chain_id}: consecutive-pair distance")
    axes[0].set_xlabel("pair index")
    axes[0].set_ylabel("distance [m]")
    axes[0].set_xticks(pair_indices)

    axes[1].semilogy(pair_indices, dots, "s-")
    axes[1].set_title("orthogonality residual |wᵢ·wᵢ₊₁|")
    axes[1].set_xlabel("pair index")
    axes[1].set_xticks(pair_indices)

    figure.suptitle(
        "V05D — "
        f"axis={cert.axis_aggregation_status}, "
        f"closed mechanism={cert.closed_mechanism_status}"
    )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _plot_regrouping_diagnostics(cert: DecompositionCertificate, outpath: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.0, 4.4))
    diagnostics = cert.coordinate_regrouping_residuals
    if not diagnostics:
        axis.axis("off")
        axis.text(
            0.05,
            0.55,
            f"{cert.source_chain_id}\nno exact coordinate regrouping",
            family="monospace",
        )
    else:
        labels = list(diagnostics)
        values = [max(abs(float(diagnostics[label])), 1e-18) for label in labels]
        axis.semilogy(range(len(labels)), values, "o-")
        axis.set_xticks(range(len(labels)))
        axis.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        axis.set_ylabel("diagnostic residual")
        axis.set_title("Same-source coordinate-regrouping sanity checks")
        axis.text(
            0.02,
            0.96,
            "Not independent closed-loop evidence",
            transform=axis.transAxes,
            va="top",
            fontsize=9,
        )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def render_v05d_html(
    certificates: list[DecompositionCertificate],
    *,
    figures: dict[str, str],
) -> str:
    rows = []
    for cert in certificates:
        roles = ",".join(cert.joint_role_sequence) if cert.aggregated else "—"
        motion = cert.rank_and_nullity_checks.get("motion_signature", "—")
        rows.append(
            "<tr>"
            f"<td><code>{cert.source_chain_id}</code></td>"
            f"<td><code>{cert.axis_aggregation_status}</code></td>"
            f"<td><code>{cert.closed_mechanism_status}</code></td>"
            f"<td><code>{cert.status}</code></td>"
            f"<td><code>{cert.reduced_topology}</code></td>"
            f"<td><code>{roles}</code></td>"
            f"<td><code>{motion}</code></td>"
            "</tr>"
        )
    figure_blocks = "".join(
        f'<h3>{label}</h3><p><img src="{rel}" alt="{label}" style="max-width:720px"></p>'
        for label, rel in figures.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>V05D — Exact Axis Aggregation Audit</title>
<style>
body {{ font-family: Georgia, serif; max-width: 1000px; margin: 2rem auto; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; }} th,td {{ border:1px solid #bbb; padding:.4rem; text-align:left; }}
code {{ font-family: ui-monospace, monospace; }} .note {{ background:#f7f4ea; border-left:3px solid #c4a35a; padding:.7rem; }}
</style></head><body>
<h1>V05D — Axis Aggregation and Decomposition Status</h1>
<div class="note"><strong>Audit correction.</strong> Exact physical-axis regrouping and
closed-mechanism equivalence are different claims. The exact proximal pair may receive
<code>axis_aggregation_status=EXACT_GLOBAL</code>; the independently solved
<code>S_v-U_phys-R-R</code> component remains <code>UNRESOLVED</code>.</div>
<table><tr><th>Source</th><th>Axis aggregation</th><th>Closed mechanism</th><th>Overall</th><th>Topology</th><th>Roles</th><th>Source motion</th></tr>{''.join(rows)}</table>
<h2>Diagnostics</h2>{figure_blocks}
<h2>Next proof obligation</h2>
<ol><li>Instantiate an independent expanded <code>S_v-U_phys-R-R</code> closure.</li>
<li>Continue source and reduced components separately.</li>
<li>Compare coordinate maps, tangent spaces, orientation task maps, complete component scope, and limits.</li></ol>
</body></html>"""


def build_v05d_readout(outdir: Path) -> list[DecompositionCertificate]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    entries = (build_exact_u_pair_4r(), build_generic_4r())
    certificates: list[DecompositionCertificate] = []
    figures: dict[str, str] = {}
    for entry in entries:
        cert = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
        certificates.append(cert)
        stem = entry.model.architecture_id
        geometry_path = figures_dir / f"v05d_{stem}_pair_geometry.png"
        _plot_pair_geometry(cert, geometry_path)
        figures[f"{stem} pair geometry"] = str(geometry_path.relative_to(outdir))
        diagnostic_path = figures_dir / f"v05d_{stem}_regrouping_diagnostics.png"
        _plot_regrouping_diagnostics(cert, diagnostic_path)
        figures[f"{stem} regrouping diagnostics"] = str(diagnostic_path.relative_to(outdir))

    payload = {
        "sprint": "V05D",
        "program": "kinematic_decomposition",
        "operation": "axis_aggregation_then_closed_mechanism_decomposition",
        "audit_status": "HOLD_PENDING_INDEPENDENT_REDUCED_SOLVE",
        "certificates": [certificate.to_json_dict() for certificate in certificates],
    }
    (data_dir / "v05d_axis_aggregation.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (outdir / "sprint_v05d_axis_aggregation.html").write_text(
        render_v05d_html(certificates, figures=figures),
        encoding="utf-8",
    )
    return certificates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05d"),
    )
    args = parser.parse_args(argv)
    certificates = build_v05d_readout(args.outdir)
    for cert in certificates:
        print(
            f"{cert.source_chain_id}: axis={cert.axis_aggregation_status}, "
            f"closed={cert.closed_mechanism_status}, overall={cert.status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
