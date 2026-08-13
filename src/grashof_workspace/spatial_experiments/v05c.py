"""Active V05C runner: orientation-curve truth and curve-type classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .fixed_position_continuation import continue_fixed_position_fiber
from .orientation_image import (
    OrientationImageResult,
    PointingImageResult,
    build_orientation_image,
    build_pointing_image,
)
from .v05_corpus import v05a_spatial_4r_corpus


def _plot_orientation_charts(
    orientation: OrientationImageResult,
    pointing: PointingImageResult,
    outpath: Path,
) -> None:
    figure = plt.figure(figsize=(10.0, 7.4))
    ax_quat = figure.add_subplot(2, 2, 1)
    ax_rot = figure.add_subplot(2, 2, 2)
    ax_s2 = figure.add_subplot(2, 2, 3, projection="3d")
    ax_metrics = figure.add_subplot(2, 2, 4)

    if not orientation.samples:
        for axis in (ax_quat, ax_rot, ax_metrics):
            axis.axis("off")
        ax_s2.axis("off")
        ax_quat.text(0.1, 0.5, f"{orientation.architecture_id}: no regular curve")
    else:
        sigma = np.asarray([sample.sigma for sample in orientation.samples], dtype=float)
        quaternions = np.asarray(
            [sample.quaternion for sample in orientation.samples], dtype=float
        )
        rotation_vectors = np.asarray(
            [sample.rotvec for sample in orientation.samples], dtype=float
        )
        for index, label in enumerate(("w", "x", "y", "z")):
            ax_quat.plot(sigma, quaternions[:, index], label=label)
        ax_quat.set_title("Sign-stabilized quaternion chart")
        ax_quat.set_xlabel("σ")
        ax_quat.legend(fontsize="small", ncol=4)

        for index, label in enumerate(("r_x", "r_y", "r_z")):
            ax_rot.plot(sigma, rotation_vectors[:, index], label=label)
        ax_rot.set_title("Rotation-vector chart")
        ax_rot.set_xlabel("σ")
        ax_rot.legend(fontsize="small")

        if pointing.points:
            d = np.asarray(pointing.points, dtype=float)
            ax_s2.plot(d[:, 0], d[:, 1], d[:, 2])
            ax_s2.scatter(d[0, 0], d[0, 1], d[0, 2], s=30)
        ax_s2.set_xlim(-1.1, 1.1)
        ax_s2.set_ylim(-1.1, 1.1)
        ax_s2.set_zlim(-1.1, 1.1)
        ax_s2.set_title("Pointing curve on S² (not coverage)")

        ax_metrics.axis("off")
        metrics = orientation.metrics
        ax_metrics.text(
            0.02,
            0.98,
            "\n".join(
                (
                    f"curve_type = {metrics.curve_type}",
                    f"SO(3) sampled path = {metrics.orientation_path_length_rad:.6f} rad",
                    f"S² sampled path = {metrics.pointing_path_length_rad:.6f} rad",
                    f"max pointing displacement = {metrics.max_pointing_displacement_rad:.6f} rad",
                    f"increment-axis drift = {metrics.incremental_axis_drift_rad}",
                    f"near singular = {orientation.near_singular_count}",
                )
            ),
            va="top",
            family="monospace",
            fontsize=8.5,
        )
    figure.suptitle(
        f"V05C — {orientation.architecture_id}: {orientation.curve_type}"
    )
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def render_v05c_html(
    rows: list[tuple[OrientationImageResult, PointingImageResult]],
    *,
    figures: dict[str, str],
) -> str:
    table_rows = []
    for orientation, pointing in rows:
        table_rows.append(
            "<tr>"
            f"<td><code>{orientation.architecture_id}</code></td>"
            f"<td>{orientation.status}</td>"
            f"<td><code>{orientation.curve_type}</code></td>"
            f"<td>{len(orientation.samples)}</td>"
            f"<td>{orientation.metrics.orientation_path_length_rad:.4f}</td>"
            f"<td>{pointing.path_length_rad:.4f}</td>"
            f"<td>{orientation.near_singular_count}</td>"
            "</tr>"
        )
    figure_blocks = "".join(
        f'<h3>{label}</h3><p><img src="{rel}" alt="{label}" style="max-width:760px"></p>'
        for label, rel in figures.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>V05C — Orientation Curves</title>
<style>body{{font-family:Georgia,serif;max-width:1000px;margin:2rem auto;line-height:1.45}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:.4rem;text-align:left}}code{{font-family:ui-monospace,monospace}}.note{{background:#f7f4ea;border-left:3px solid #c4a35a;padding:.7rem}}</style></head><body>
<h1>V05C — Orientation-Curve Truth</h1>
<div class="note"><strong>Audit correction.</strong> The readout now distinguishes a pure terminal-roll orbit from a nontrivial pointing curve. Sampled path lengths diagnose the curve; they are not coverage claims for <code>SO(3)</code> or <code>S²</code>.</div>
<table><tr><th>Source</th><th>Export</th><th>Curve type</th><th>Samples</th><th>SO(3) path [rad]</th><th>S² path [rad]</th><th>Near singular</th></tr>{''.join(table_rows)}</table>
<h2>Figures</h2>{figure_blocks}
</body></html>"""


def build_v05c_readout(
    outdir: Path,
    *,
    n_steps: int = 80,
    step_size: float = 0.04,
) -> list[tuple[OrientationImageResult, PointingImageResult]]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = outdir / "data"
    figures_dir = outdir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    rows: list[tuple[OrientationImageResult, PointingImageResult]] = []
    payload_rows = []
    figures: dict[str, str] = {}
    for entry in v05a_spatial_4r_corpus():
        fiber = continue_fixed_position_fiber(
            entry.model,
            entry.regular_q,
            n_steps=n_steps,
            step_size=step_size,
        )
        orientation = build_orientation_image(fiber, chain=entry.model)
        pointing = build_pointing_image(fiber)
        rows.append((orientation, pointing))
        payload_rows.append(
            {
                "fiber": {
                    "architecture_id": fiber.architecture_id,
                    "branch_status": fiber.branch_status,
                    "seed_status": fiber.seed_audit.status,
                    "motion_signature": fiber.seed_audit.motion_signature,
                },
                "orientation_image": orientation.to_json_dict(),
                "pointing_image": pointing.to_json_dict(),
            }
        )
        path = figures_dir / f"v05c_{entry.model.architecture_id}_orientation_charts.png"
        _plot_orientation_charts(orientation, pointing, path)
        figures[f"{entry.model.architecture_id} orientation charts"] = str(
            path.relative_to(outdir)
        )

    payload = {
        "sprint": "V05C",
        "program": "kinematic_decomposition",
        "audit_status": "CURVE_TYPES_EXPLICIT_NOT_COVERAGE",
        "fibers": payload_rows,
    }
    (data_dir / "v05c_orientation_curves.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (outdir / "sprint_v05c_orientation_curve.html").write_text(
        render_v05c_html(rows, figures=figures),
        encoding="utf-8",
    )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/kinematic_decomposition/v05c"),
    )
    parser.add_argument("--n-steps", type=int, default=80)
    parser.add_argument("--step-size", type=float, default=0.04)
    args = parser.parse_args(argv)
    rows = build_v05c_readout(args.outdir, n_steps=args.n_steps, step_size=args.step_size)
    for orientation, _pointing in rows:
        print(
            f"{orientation.architecture_id}: {orientation.status}, "
            f"curve={orientation.curve_type}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
