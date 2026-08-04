"""Plotting helpers for analytical planar workspaces and mechanism states."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Wedge

from .planar3r import Planar3R, RadialMechanismState

_TRACKS = (
    ("reachable", "reachable"),
    ("assemblable", "assemblable"),
    ("grashof", "Grashof class"),
    ("inversion", "inversion"),
    ("rotate", "input rotates"),
    ("dexterous", "dexterous"),
)


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
            axis.add_patch(Circle((0.0, 0.0), outer, alpha=0.42, label=label))
        else:
            axis.add_patch(
                Wedge(
                    (0.0, 0.0),
                    outer,
                    0.0,
                    360.0,
                    width=outer - inner,
                    alpha=0.42,
                    label=label,
                )
            )

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


def _grashof_color(label: str) -> str:
    return {
        "grashof": "#2a9d8f",
        "change-point": "#e9c46a",
        "non-grashof": "#e76f51",
        "non-assemblable": "#6c757d",
    }.get(label, "#adb5bd")


def _bool_color(flag: bool) -> str:
    return "#264653" if flag else "#ced4da"


def plot_radial_mechanism_state(
    robot: Planar3R,
    output: str | Path,
    *,
    states: list[RadialMechanismState] | None = None,
    title: str | None = None,
) -> Path:
    """Plot aligned radial bands for mechanism and dexterity state."""
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if states is None:
        _, reachable_outer = robot.reachable_radial_interval()
        limit = reachable_outer * 1.05 + 1e-9
        sample_count = 401
        radii = [limit * index / (sample_count - 1) for index in range(sample_count)]
        states = [robot.mechanism_state(rho) for rho in radii]

    figure, axis = plt.subplots(figsize=(10, 5))
    track_height = 0.8
    for track_index, (key, label) in enumerate(_TRACKS):
        y0 = len(_TRACKS) - track_index - 1
        for index, state in enumerate(states[:-1]):
            rho0 = state.rho
            rho1 = states[index + 1].rho
            width = rho1 - rho0
            if key == "reachable":
                color = _bool_color(state.reachable)
            elif key == "assemblable":
                color = _bool_color(state.assemblable)
            elif key == "grashof":
                color = _grashof_color(state.grashof_class)
            elif key == "inversion":
                color = "#457b9d" if state.assemblable else "#adb5bd"
            elif key == "rotate":
                color = _bool_color(state.input_can_fully_rotate)
            else:
                color = _bool_color(state.dexterous)
            axis.add_patch(
                Rectangle((rho0, y0), width, track_height, color=color, linewidth=0)
            )
        axis.text(-0.02 * max(state.rho for state in states), y0 + 0.25, label, ha="right")

    boundaries = {0.0, *robot.reachable_radial_interval()}
    for inner, outer in robot.dexterous_radial_intervals():
        boundaries.add(inner)
        boundaries.add(outer)
    rho_max = max(state.rho for state in states)
    for radius in sorted(boundaries):
        if radius < 0.0 or radius > rho_max + 1e-12:
            continue
        axis.axvline(radius, color="black", linewidth=0.8, alpha=0.55)
        axis.text(radius, len(_TRACKS) + 0.05, f"{radius:g}", rotation=90, fontsize=7, va="bottom")

    axis.set_xlim(0.0, rho_max)
    axis.set_ylim(-0.2, len(_TRACKS) + 0.8)
    axis.set_yticks([])
    axis.set_xlabel(r"$\rho$")
    axis.set_title(
        title
        or (
            f"Radial mechanism state: l1={robot.l1:g}, l2={robot.l2:g}, "
            f"l3={robot.l3:g}"
        )
    )
    # Explicit note that Grashof alone is not dexterity
    axis.text(
        0.01,
        -0.08,
        "Dark bands: true / Grashof. Dexterity uses input rotation, not Grashof alone.",
        transform=axis.transAxes,
        fontsize=8,
    )
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)
    return output_path
