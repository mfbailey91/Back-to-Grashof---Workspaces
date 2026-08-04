"""Plotting helpers for analytical planar workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge

from .planar3r import Planar3R


def _annotate_radius(axis: Any, radius: float, label: str) -> None:
    if radius <= 0.0:
        return
    axis.add_patch(
        Circle(
            (0.0, 0.0),
            radius,
            fill=False,
            linestyle="--",
            linewidth=0.9,
            alpha=0.55,
        )
    )
    axis.text(
        radius * 0.7071,
        radius * 0.7071,
        label,
        fontsize=8,
        ha="left",
        va="bottom",
    )


def plot_workspace(
    robot: Planar3R,
    output: str | Path,
    *,
    title: str | None = None,
) -> Path:
    """Plot reachable and dexterous position workspaces with radial labels."""
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    reachable_inner, reachable_outer = robot.reachable_radial_interval()
    dexterous = robot.dexterous_radial_intervals()

    figure, axis = plt.subplots(figsize=(7, 7))

    if reachable_inner == 0.0:
        axis.add_patch(
            Circle(
                (0.0, 0.0),
                reachable_outer,
                alpha=0.16,
                label="reachable workspace",
            )
        )
    else:
        axis.add_patch(
            Wedge(
                (0.0, 0.0),
                reachable_outer,
                0.0,
                360.0,
                width=reachable_outer - reachable_inner,
                alpha=0.16,
                label="reachable workspace",
            )
        )

    for index, (inner, outer) in enumerate(dexterous):
        label = "dexterous workspace" if index == 0 else None
        if inner == outer:
            axis.add_patch(
                Circle(
                    (0.0, 0.0),
                    outer,
                    fill=False,
                    linewidth=2.0,
                    alpha=0.9,
                    label=label or "dexterous boundary",
                )
            )
            continue
        if inner == 0.0:
            patch = Circle((0.0, 0.0), outer, alpha=0.42, label=label)
        else:
            patch = Wedge(
                (0.0, 0.0),
                outer,
                0.0,
                360.0,
                width=outer - inner,
                alpha=0.42,
                label=label,
            )
        axis.add_patch(patch)

    annotated: set[float] = set()
    if reachable_inner > 0.0:
        _annotate_radius(axis, reachable_inner, f"r_in={reachable_inner:g}")
        annotated.add(round(reachable_inner, 12))
    _annotate_radius(axis, reachable_outer, f"r_out={reachable_outer:g}")
    annotated.add(round(reachable_outer, 12))

    for index, (inner, outer) in enumerate(dexterous):
        for radius, tag in ((inner, "d"), (outer, "d")):
            key = round(radius, 12)
            if radius <= 0.0 or key in annotated:
                continue
            _annotate_radius(axis, radius, f"{tag}{index}:{radius:g}")
            annotated.add(key)

    limit = reachable_outer * 1.08
    axis.set_xlim(-limit, limit)
    axis.set_ylim(-limit, limit)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_title(
        title
        or (
            f"Planar 3R workspace: l1={robot.l1:g}, l2={robot.l2:g}, "
            f"l3={robot.l3:g}"
        )
    )
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right")
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)

    return output_path
