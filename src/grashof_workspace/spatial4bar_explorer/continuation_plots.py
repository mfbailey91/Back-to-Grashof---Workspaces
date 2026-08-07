from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from .closure import ClosureAudit, mechanism_state
from .continuation import ContinuationTrace
from .geometry import SpatialFourBarGeometry


def plot_reference_mobility_audit(audits: list[ClosureAudit], outpath: Path) -> None:
    labels = [audit.family for audit in audits]
    values = [audit.smallest_nonzero_singular_value for audit in audits]
    figure = plt.figure(figsize=(8.5, 4.8))
    axis = figure.add_subplot(111)
    axis.bar(labels, values)
    axis.set_xlabel("Ordered family")
    axis.set_ylabel("Smallest nonzero singular value")
    axis.set_title("V03A reference closure mobility audit")
    for index, audit in enumerate(audits):
        axis.text(index, values[index], f"n={audit.jacobian_nullity}", ha="center", va="bottom")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def plot_continuation_coordinates(trace: ContinuationTrace, outpath: Path) -> None:
    arclength = [point.arclength for point in trace.points]
    values = np.asarray([point.q for point in trace.points], dtype=float)
    figure = plt.figure(figsize=(9.5, 5.2))
    axis = figure.add_subplot(111)
    for index, name in enumerate(trace.coordinate_names):
        axis.plot(arclength, values[:, index], label=name)
    axis.set_xlabel("Continuation arclength")
    axis.set_ylabel("Joint coordinate [rad]")
    axis.set_title(f"{trace.family}: seven scalar coordinates along one branch segment")
    axis.legend(loc="best", fontsize="small", ncol=2)
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def plot_closure_residual(trace: ContinuationTrace, outpath: Path) -> None:
    arclength = [point.arclength for point in trace.points]
    values = [max(point.closure_norm, 1e-18) for point in trace.points]
    figure = plt.figure(figsize=(8.0, 4.5))
    axis = figure.add_subplot(111)
    axis.semilogy(arclength, values)
    axis.set_xlabel("Continuation arclength")
    axis.set_ylabel("Closure residual norm")
    axis.set_title(f"{trace.family}: closure error along continued branch")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def plot_singularity_margin(trace: ContinuationTrace, outpath: Path) -> None:
    arclength = [point.arclength for point in trace.points]
    values = [point.smallest_singular_value for point in trace.points]
    figure = plt.figure(figsize=(8.0, 4.5))
    axis = figure.add_subplot(111)
    axis.plot(arclength, values)
    axis.set_xlabel("Continuation arclength")
    axis.set_ylabel("Smallest nonzero singular value")
    axis.set_title(f"{trace.family}: local closure-Jacobian margin")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def plot_tool_coordinate_phase(trace: ContinuationTrace, outpath: Path) -> None:
    alpha_index = trace.coordinate_names.index("tool_alpha")
    beta_index = trace.coordinate_names.index("tool_beta")
    values = np.asarray([point.q for point in trace.points], dtype=float)
    figure = plt.figure(figsize=(5.8, 5.4))
    axis = figure.add_subplot(111)
    axis.plot(values[:, alpha_index], values[:, beta_index], marker=".")
    axis.set_xlabel("tool_a [rad]")
    axis.set_ylabel("tool_b [rad]")
    axis.set_title(f"{trace.family}: local tool-U coordinate path")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def _display_axis_name(name: str) -> str:
    """Map solver chart names to the tool_a / tool_b readout convention."""
    if name == "tool_alpha":
        return "tool_a"
    if name == "tool_beta":
        return "tool_b"
    return name


def _axis_style(name: str) -> dict[str, float | str]:
    if name == "tool_alpha":
        return {"color": "#1f77b4", "linewidth": 2.6, "alpha": 1.0}
    if name == "tool_beta":
        return {"color": "#ff7f0e", "linewidth": 2.6, "alpha": 1.0}
    return {"color": "#888888", "linewidth": 1.0, "alpha": 0.5}


def _branch_frame_title(
    family: str,
    arclength: float,
    q: tuple[float, ...],
    coordinate_names: tuple[str, ...],
) -> str:
    alpha = float(q[coordinate_names.index("tool_alpha")])
    beta = float(q[coordinate_names.index("tool_beta")])
    return (
        f"{family} branch: s={arclength:.2f} | "
        f"tool_a={alpha:+.2f} rad | tool_b={beta:+.2f} rad"
    )


def _draw_state(
    axis: Any,
    geometry: SpatialFourBarGeometry,
    q: tuple[float, ...],
    *,
    limits: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    title: str,
    axis_artists: list[Any] | None = None,
) -> list[Any]:
    """Draw or update one mechanism pose on a 3D axis.

    When ``axis_artists`` is None, create artists (static snapshot). When provided,
    update existing Line3D artists in place (animation frames).

    Virtual tool axes are drawn as highlighted ``tool_a`` / ``tool_b`` lines; other
    scalar chart axes remain muted.
    """
    centers, axis_lines = mechanism_state(geometry, np.asarray(q, dtype=float))
    cycle = [0, 1, 2, 3, 0]
    axis_extent = 0.32 * geometry.reference_length
    if axis_artists is None:
        artists: list[Any] = []
        (link_line,) = axis.plot(
            centers[cycle, 0],
            centers[cycle, 1],
            centers[cycle, 2],
            marker="o",
            linewidth=2.0,
        )
        artists.append(link_line)
        for origin, direction, name in axis_lines:
            start = origin - axis_extent * direction
            end = origin + axis_extent * direction
            style = _axis_style(name)
            (axis_line,) = axis.plot(
                (start[0], end[0]),
                (start[1], end[1]),
                (start[2], end[2]),
                color=style["color"],
                linewidth=style["linewidth"],
                alpha=style["alpha"],
            )
            artists.append(axis_line)
            label = _display_axis_name(name)
            weight = "bold" if name in {"tool_alpha", "tool_beta"} else "normal"
            axis.text(
                end[0],
                end[1],
                end[2],
                label,
                fontsize=8 if weight == "bold" else 7,
                fontweight=weight,
                color=style["color"],
            )
        axis.set_xlim(*limits[0])
        axis.set_ylim(*limits[1])
        axis.set_zlim(*limits[2])
        axis.set_box_aspect((1.0, 1.0, 1.0))
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        axis.set_zlabel("z")
        axis.set_title(title)
        return artists

    link_line = axis_artists[0]
    link_line.set_data_3d(centers[cycle, 0], centers[cycle, 1], centers[cycle, 2])
    for artist, (origin, direction, _name) in zip(axis_artists[1:], axis_lines, strict=True):
        start = origin - axis_extent * direction
        end = origin + axis_extent * direction
        artist.set_data_3d((start[0], end[0]), (start[1], end[1]), (start[2], end[2]))
    axis.set_title(title)
    return axis_artists

def _plot_state(
    geometry: SpatialFourBarGeometry,
    q: tuple[float, ...],
    outpath: Path,
    *,
    title: str,
    limits: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> None:
    figure = plt.figure(figsize=(7.0, 6.0))
    axis = figure.add_subplot(111, projection="3d")
    _draw_state(axis, geometry, q, limits=limits, title=title)
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def branch_snapshot_limits(
    geometry: SpatialFourBarGeometry, trace: ContinuationTrace
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    all_centers: list[np.ndarray] = []
    stride = max(1, len(trace.points) // 12)
    for point in trace.points[::stride]:
        centers, _ = mechanism_state(geometry, np.asarray(point.q, dtype=float))
        all_centers.append(centers)
    stacked = np.vstack(all_centers)
    minimum = stacked.min(axis=0)
    maximum = stacked.max(axis=0)
    center = 0.5 * (minimum + maximum)
    half = max(float(np.max(maximum - minimum)) * 0.62, geometry.reference_length * 0.75)
    return tuple((float(center[index] - half), float(center[index] + half)) for index in range(3))  # type: ignore[return-value]


def plot_branch_snapshots(
    geometry: SpatialFourBarGeometry,
    trace: ContinuationTrace,
    outdir: Path,
    *,
    count: int = 5,
) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    if count < 2:
        indices = [0]
    else:
        indices = sorted(
            {round(index * (len(trace.points) - 1) / (count - 1)) for index in range(count)}
        )
    limits = branch_snapshot_limits(geometry, trace)
    paths: list[Path] = []
    for index in indices:
        point = trace.points[index]
        path = outdir / f"{geometry.family.value.lower()}_branch_{index:03d}.png"
        _plot_state(
            geometry,
            point.q,
            path,
            title=_branch_frame_title(
                geometry.family.value,
                point.arclength,
                point.q,
                trace.coordinate_names,
            ),
            limits=limits,
        )
        paths.append(path)
    return paths


def animate_branch(
    geometry: SpatialFourBarGeometry,
    trace: ContinuationTrace,
    outpath: Path,
    *,
    stride: int | None = None,
    fps: int = 12,
    dpi: int = 110,
) -> Path:
    """Write a looping GIF of the mechanism along a continued one-DOF branch.

    Frames advance by continuation arclength, not by a claimed crank input.
    Highlighted ``tool_a`` / ``tool_b`` axes and live angles are shown each frame.
    """
    outpath.parent.mkdir(parents=True, exist_ok=True)
    points = [point for point in trace.points if point.converged]
    if not points:
        raise ValueError("trace has no converged points to animate")
    frame_stride = stride if stride is not None else max(1, len(points) // 35)
    frames = points[::frame_stride]
    if frames[-1] is not points[-1]:
        frames.append(points[-1])
    limits = branch_snapshot_limits(geometry, trace)
    names = trace.coordinate_names

    figure = plt.figure(figsize=(7.0, 6.0))
    axis = figure.add_subplot(111, projection="3d")
    artists = _draw_state(
        axis,
        geometry,
        frames[0].q,
        limits=limits,
        title=_branch_frame_title(
            geometry.family.value,
            frames[0].arclength,
            frames[0].q,
            names,
        ),
    )
    figure.tight_layout()

    def _update(frame_index: int) -> list[Any]:
        point = frames[frame_index]
        return _draw_state(
            axis,
            geometry,
            point.q,
            limits=limits,
            title=_branch_frame_title(
                geometry.family.value,
                point.arclength,
                point.q,
                names,
            ),
            axis_artists=artists,
        )

    animation = FuncAnimation(figure, _update, frames=len(frames), interval=1000 / fps, blit=False)
    animation.save(outpath, writer=PillowWriter(fps=fps), dpi=dpi)
    plt.close(figure)
    return outpath