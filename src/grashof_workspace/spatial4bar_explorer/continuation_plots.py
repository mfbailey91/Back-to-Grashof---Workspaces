from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

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
    axis.set_xlabel("tool_alpha [rad]")
    axis.set_ylabel("tool_beta [rad]")
    axis.set_title(f"{trace.family}: local tool-U coordinate path")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def _plot_state(
    geometry: SpatialFourBarGeometry,
    q: tuple[float, ...],
    outpath: Path,
    *,
    title: str,
    limits: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> None:
    centers, axis_lines = mechanism_state(geometry, np.asarray(q, dtype=float))
    figure = plt.figure(figsize=(7.0, 6.0))
    axis = figure.add_subplot(111, projection="3d")
    cycle = [0, 1, 2, 3, 0]
    axis.plot(centers[cycle, 0], centers[cycle, 1], centers[cycle, 2], marker="o", linewidth=2.0)
    axis_extent = 0.32 * geometry.reference_length
    for origin, direction, name in axis_lines:
        start = origin - axis_extent * direction
        end = origin + axis_extent * direction
        axis.plot((start[0], end[0]), (start[1], end[1]), (start[2], end[2]), linewidth=1.0, alpha=0.65)
        axis.text(end[0], end[1], end[2], name, fontsize=7)
    axis.set_xlim(*limits[0])
    axis.set_ylim(*limits[1])
    axis.set_zlim(*limits[2])
    axis.set_box_aspect((1.0, 1.0, 1.0))
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_zlabel("z")
    axis.set_title(title)
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def branch_snapshot_limits(geometry: SpatialFourBarGeometry, trace: ContinuationTrace) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
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
        indices = sorted(set(round(index * (len(trace.points) - 1) / (count - 1)) for index in range(count)))
    limits = branch_snapshot_limits(geometry, trace)
    paths: list[Path] = []
    for index in indices:
        point = trace.points[index]
        path = outdir / f"{geometry.family.value.lower()}_branch_{index:03d}.png"
        _plot_state(
            geometry,
            point.q,
            path,
            title=f"{geometry.family.value} branch: s={point.arclength:.2f}",
            limits=limits,
        )
        paths.append(path)
    return paths
