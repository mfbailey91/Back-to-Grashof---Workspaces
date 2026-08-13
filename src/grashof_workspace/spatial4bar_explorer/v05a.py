"""Retained pointing-slice prototype (formerly active V05A).

This artifact is now labeled ``V08_POINTING_SLICE_PROTOTYPE``.  It validates the
parent level set and local virtual-U chart, but it does not claim SUUR→UUUR
mechanism equivalence while the child tangent fails and global branch
correspondence is unresolved.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

from .geometry_plots import plot_physical_geometry_3d
from .pointing_slice import PointingSliceFiberResult, construct_suur_uuur_pointing_fiber


def _plot_status_diagnostics(result: PointingSliceFiberResult, outpath: Path) -> None:
    residuals = result.equivalence_residuals
    statuses = result.equivalence_statuses
    labels = (
        "U-chart tangent residual",
        "child-tool tangent residual",
        "parent level-set residual",
        "child closure residual",
    )
    values = (
        max(residuals.tangent_pointing_residual, 1e-18),
        max(residuals.child_tool_tangent_residual, 1e-18),
        max(residuals.pointing_curve_residual, 1e-18),
        max(residuals.child_closure_norm, 1e-18),
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.6))
    axes[0].semilogy(range(len(labels)), values, "o-")
    axes[0].set_xticks(range(len(labels)))
    axes[0].set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    axes[0].set_title("Residuals: chart validity ≠ child equivalence")
    axes[1].axis("off")
    axes[1].text(
        0.02,
        0.98,
        "\n".join(
            (
                f"program_role = {result.program_role}",
                f"parent_slice = {statuses.parent_slice_status}",
                f"virtual_u_chart = {statuses.virtual_u_chart_status}",
                f"child_reference_closure = {statuses.child_reference_closure_status}",
                f"parent_child_tangent = {statuses.parent_child_tangent_status}",
                f"parent_child_branch = {statuses.parent_child_branch_status}",
                f"overall = {statuses.overall_status}",
            )
        ),
        va="top",
        family="monospace",
    )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def render_v05a_html(
    result: PointingSliceFiberResult,
    outdir: Path,
    *,
    figures: dict[str, str],
) -> str:
    _ = outdir
    statuses = result.equivalence_statuses
    residuals = result.equivalence_residuals
    figure_blocks = "".join(
        f'<h3>{label}</h3><p><img src="{path}" alt="{label}" style="max-width:720px"></p>'
        for label, path in figures.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Pointing-Slice Prototype Audit</title>
<style>body{{font-family:Georgia,serif;max-width:950px;margin:2rem auto;line-height:1.45}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:.4rem;text-align:left}}code{{font-family:ui-monospace,monospace}}.note{{background:#f7f4ea;border-left:3px solid #c4a35a;padding:.7rem}}</style></head><body>
<h1>Pointing-Slice Prototype — Split Equivalence Status</h1>
<div class="note">This is a <code>{result.program_role}</code>, not active spatial-4R V05 evidence. The parent slice and local <code>U_v</code> chart pass, but the candidate child tangent fails and global parent-child branch equivalence is unresolved.</div>
<table>
<tr><th>Check</th><th>Status</th></tr>
<tr><td>Parent pointing slice</td><td>{statuses.parent_slice_status}</td></tr>
<tr><td>Local virtual-U chart</td><td>{statuses.virtual_u_chart_status}</td></tr>
<tr><td>Child reference closure/mobility</td><td>{statuses.child_reference_closure_status}</td></tr>
<tr><td>Parent-child tangent</td><td>{statuses.parent_child_tangent_status}</td></tr>
<tr><td>Parent-child branch</td><td>{statuses.parent_child_branch_status}</td></tr>
<tr><td>Overall</td><td>{statuses.overall_status}</td></tr>
</table>
<p>Child-tool tangent residual: <code>{residuals.child_tool_tangent_residual:.6e}</code>. Local chart residual: <code>{residuals.tangent_pointing_residual:.6e}</code>.</p>
<h2>Figures</h2>{figure_blocks}
</body></html>"""


def build_v05a_readout(outdir: Path) -> PointingSliceFiberResult:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    result = construct_suur_uuur_pointing_fiber()
    payload = {
        "artifact": "POINTING_SLICE_PROTOTYPE",
        "program_role": result.program_role,
        "audit_note": (
            "Parent slice and local U_v chart are valid; parent-child tangent fails; "
            "branch equivalence is unresolved."
        ),
        "fibers": [result.to_json_dict()],
        "standalone_policy": "prototype_only_not_workspace_evidence",
    }
    (data_dir / "v05a_pointing_slice_fibers.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    diagnostics = figures_dir / "v05a_equivalence_status_diagnostics.png"
    _plot_status_diagnostics(result, diagnostics)
    child_geometry = figures_dir / "v05a_uuur_child_geometry.png"
    plot_physical_geometry_3d(result.geometry, child_geometry)
    figures = {
        "Split equivalence diagnostics": str(diagnostics.relative_to(outdir)),
        "Candidate UUUR reference geometry": str(child_geometry.relative_to(outdir)),
    }
    (outdir / "sprint_05a_pointing_slice_fibers.html").write_text(
        render_v05a_html(result, outdir, figures=figures),
        encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/spatial4bar_explorer/v05a"),
    )
    args = parser.parse_args(argv)
    result = build_v05a_readout(args.outdir)
    print(
        f"pointing-slice prototype overall={result.fiber_equivalence_status}, "
        f"tangent={result.equivalence_statuses.parent_child_tangent_status}, "
        f"branch={result.equivalence_statuses.parent_child_branch_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
