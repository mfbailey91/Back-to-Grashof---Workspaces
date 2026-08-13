"""Active V05D runner: axis aggregation plus independent closed-mechanism gate.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05d \
      --outdir results/kinematic_decomposition/v05d
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from .axis_aggregation import build_aggregated_mechanism, detect_exact_u_pairs
from .closed_mechanism_compare import (
    ClosedMechanismComparison,
    compare_independent_closed_mechanism,
)
from .closed_mechanism_sv_uphys import build_independent_sv_uphys_rr
from .decomposition_certificate import (
    DecompositionCertificate,
    issue_axis_aggregation_certificate,
    issue_closed_mechanism_certificate,
)
from .v05_corpus import Spatial4RCorpusEntry, build_exact_u_pair_4r, build_generic_4r

Vec3 = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class _ExactUOverlay:
    source_pointing: tuple[Vec3, ...]
    reduced_pointing: tuple[Vec3, ...]
    comparison: ClosedMechanismComparison


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


def _plot_source_reduced_overlay(
    model_id: str,
    source_pointing: tuple[Vec3, ...] | list[Vec3],
    reduced_pointing: tuple[Vec3, ...] | list[Vec3],
    outpath: Path,
) -> None:
    figure = plt.figure(figsize=(6.2, 5.6))
    axis = figure.add_subplot(111, projection="3d")
    if source_pointing:
        src = np.asarray(source_pointing, dtype=float)
        axis.plot(src[:, 0], src[:, 1], src[:, 2], alpha=0.35, label="source fiber pointing")
    if reduced_pointing:
        red = np.asarray(reduced_pointing, dtype=float)
        axis.plot(red[:, 0], red[:, 1], red[:, 2], linewidth=1.8, label="mapped independent loop")
    axis.set_title(f"{model_id}: source vs independent reduced pointing")
    axis.legend(loc="upper left", fontsize="small")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_zlabel("z")
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def render_v05d_html(
    certificates: list[DecompositionCertificate],
    *,
    figures: dict[str, str],
) -> str:
    rows = []
    closed_exact = any(
        certificate.closed_mechanism_status == "EXACT_ON_COMPONENT" for certificate in certificates
    )
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
    if closed_exact:
        note = (
            "<strong>Scoped gate closed.</strong> Proximal "
            "<code>exact_u_pair_4r</code> has "
            "<code>closed_mechanism_status=EXACT_ON_COMPONENT</code> from an "
            "independent <code>S_v-U_phys-R-R</code> solve. Multi-component "
            "<code>EXACT_GLOBAL</code> and other architectures remain unresolved."
        )
        next_block = (
            "<h2>Remaining obligations</h2>"
            "<ol><li>Non-proximal pair embeddings remain unverified.</li>"
            "<li>Multi-component <code>EXACT_GLOBAL</code> remains unverified.</li>"
            "<li>V06 scientific claims remain architecture-scoped after this L4/V05 result.</li></ol>"
        )
    else:
        note = (
            "<strong>Audit correction.</strong> Exact physical-axis regrouping and "
            "closed-mechanism equivalence are different claims. The exact proximal pair may "
            "receive <code>axis_aggregation_status=EXACT_GLOBAL</code>; the independently "
            "solved <code>S_v-U_phys-R-R</code> component remains <code>UNRESOLVED</code>."
        )
        next_block = (
            "<h2>Next proof obligation</h2>"
            "<ol><li>Instantiate an independent expanded <code>S_v-U_phys-R-R</code> closure.</li>"
            "<li>Continue source and reduced components separately.</li>"
            "<li>Compare coordinate maps, tangent spaces, orientation task maps, "
            "complete component scope, and limits.</li></ol>"
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
<div class="note">{note}</div>
<table><tr><th>Source</th><th>Axis aggregation</th><th>Closed mechanism</th><th>Overall</th><th>Topology</th><th>Roles</th><th>Source motion</th></tr>{''.join(rows)}</table>
<h2>Diagnostics</h2>{figure_blocks}
{next_block}
</body></html>"""


def _issue_exact_u_closed_certificate(
    entry: Spatial4RCorpusEntry,
) -> tuple[DecompositionCertificate, _ExactUOverlay]:
    aggregation = issue_axis_aggregation_certificate(entry.model, entry.regular_q)
    candidates = detect_exact_u_pairs(entry.model)
    exact = next(candidate for candidate in candidates if candidate.exact_u_candidate)
    aggregated = build_aggregated_mechanism(entry.model, exact)
    mechanism = build_independent_sv_uphys_rr(entry.model, aggregated, entry.regular_q)
    comparison = compare_independent_closed_mechanism(entry.model, mechanism)
    certificate = issue_closed_mechanism_certificate(aggregation, comparison)

    from grashof_workspace.spatial4bar_explorer.continuation import continue_branch
    from grashof_workspace.spatial_experiments.fixed_position_continuation import (
        continue_fixed_position_fiber,
    )

    fiber = continue_fixed_position_fiber(
        entry.model,
        entry.regular_q,
        n_steps=40,
        step_size=0.03,
    )
    reduced = continue_branch(mechanism.geometry, step_size=0.03, steps=40)
    source_pointing = tuple(
        as_vec3_tuple(sample.d) for sample in fiber.accepted_samples if sample.d is not None
    )
    reduced_pointing_list: list[Vec3] = []
    for point in reduced.points:
        if not point.converged:
            continue
        q_source = mechanism.source_q_from_reduced(point.q)
        state = entry.model.chain.evaluate(q_source)
        reduced_pointing_list.append(as_vec3_tuple(state.d))
    return certificate, _ExactUOverlay(
        source_pointing=source_pointing,
        reduced_pointing=tuple(reduced_pointing_list),
        comparison=comparison,
    )


def as_vec3_tuple(values: NDArray[np.floating] | tuple[float, ...] | list[float]) -> Vec3:
    arr = np.asarray(values, dtype=float).reshape(3)
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def build_v05d_readout(outdir: Path) -> list[DecompositionCertificate]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    exact_entry = build_exact_u_pair_4r()
    generic_entry = build_generic_4r()
    certificates: list[DecompositionCertificate] = []
    figures: dict[str, str] = {}

    exact_cert, overlay = _issue_exact_u_closed_certificate(exact_entry)
    certificates.append(exact_cert)
    generic_cert = issue_axis_aggregation_certificate(generic_entry.model, generic_entry.regular_q)
    certificates.append(generic_cert)

    for cert in certificates:
        stem = cert.source_chain_id
        geometry_path = figures_dir / f"v05d_{stem}_pair_geometry.png"
        _plot_pair_geometry(cert, geometry_path)
        figures[f"{stem} pair geometry"] = str(geometry_path.relative_to(outdir))
        diagnostic_path = figures_dir / f"v05d_{stem}_regrouping_diagnostics.png"
        _plot_regrouping_diagnostics(cert, diagnostic_path)
        figures[f"{stem} regrouping diagnostics"] = str(diagnostic_path.relative_to(outdir))

    overlay_path = figures_dir / "v05d_exact_u_pair_4r_source_reduced_overlay.png"
    _plot_source_reduced_overlay(
        "exact_u_pair_4r",
        overlay.source_pointing,
        overlay.reduced_pointing,
        overlay_path,
    )
    figures["exact_u_pair_4r source/reduced overlay"] = str(overlay_path.relative_to(outdir))

    closed_exact = any(
        certificate.closed_mechanism_status == "EXACT_ON_COMPONENT" for certificate in certificates
    )
    payload = {
        "sprint": "V05D",
        "program": "kinematic_decomposition",
        "operation": "axis_aggregation_then_closed_mechanism_decomposition",
        "audit_status": (
            "CLOSED_ON_COMPONENT_EXACT_U_PAIR"
            if closed_exact
            else "HOLD_PENDING_INDEPENDENT_REDUCED_SOLVE"
        ),
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
