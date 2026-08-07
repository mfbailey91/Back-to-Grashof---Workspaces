from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from .closure import closure_jacobian, closure_residual, mechanism_state, null_tangent, scalar_axes
from .geometry import SpatialFourBarGeometry
from .models import ToolAxis

Array = np.ndarray


@dataclass(frozen=True)
class AxisDrivePoint:
    target_angle: float
    q: tuple[float, ...]
    closure_norm: float
    smallest_singular_value: float
    converged: bool
    newton_iterations: int


@dataclass(frozen=True)
class AxisDriveTrace:
    family: str
    tool_axis: str
    coordinate_name: str
    points: tuple[AxisDrivePoint, ...]
    target_step: float
    requested_angle: float
    reached_angle: float
    full_input_turn: bool
    status: str

    @property
    def converged_points(self) -> tuple[AxisDrivePoint, ...]:
        return tuple(point for point in self.points if point.converged)


def _coordinate_index(geometry: SpatialFourBarGeometry, tool_axis: ToolAxis) -> int:
    target_name = "tool_alpha" if tool_axis is ToolAxis.A else "tool_beta"
    names = [axis.name for axis in scalar_axes(geometry)]
    return names.index(target_name)


def _correct_with_fixed_coordinate(
    geometry: SpatialFourBarGeometry,
    q_initial: Array,
    *,
    coordinate_index: int,
    target_angle: float,
    tolerance: float,
    max_iterations: int,
) -> tuple[Array, bool, int]:
    q = np.asarray(q_initial, dtype=float).copy()
    q[coordinate_index] = target_angle
    free = [index for index in range(q.size) if index != coordinate_index]
    for iteration in range(1, max_iterations + 1):
        residual = closure_residual(geometry, q)
        if float(np.linalg.norm(residual)) < tolerance:
            return q, True, iteration
        jacobian = closure_jacobian(geometry, q)
        reduced = jacobian[:, free]
        delta, *_ = np.linalg.lstsq(reduced, -residual, rcond=None)
        q[free] += delta
        q[coordinate_index] = target_angle
        if (
            float(np.linalg.norm(delta)) < tolerance * 0.1
            and float(np.linalg.norm(closure_residual(geometry, q))) < tolerance * 10.0
        ):
            return q, True, iteration
    return q, False, max_iterations


def drive_tool_axis(
    geometry: SpatialFourBarGeometry,
    tool_axis: ToolAxis,
    *,
    requested_angle: float = 2.0 * math.pi,
    target_step: float = 0.08,
    tolerance: float = 1e-10,
    max_iterations: int = 18,
    singularity_tol: float = 1e-5,
    min_target_step: float = 1e-3,
) -> AxisDriveTrace:
    """Prescribe tool-A or tool-B and solve the remaining six closure coordinates.

    This is a designated-input visualization/diagnostic.  It restores the V02
    interpretation of ``tool_a`` and ``tool_b`` as two rotatability questions
    on the same physical UXXX mechanism.

    Completing 0 -> 2π is strong visual evidence that the selected input can
    circulate on the followed assembly branch.  Winding from returned-cycle
    continuation remains the authoritative V04 branch-topology classification.
    """
    if requested_angle <= 0.0:
        raise ValueError("requested_angle must be positive")
    if target_step <= 0.0:
        raise ValueError("target_step must be positive")
    if min_target_step <= 0.0 or min_target_step > target_step:
        raise ValueError("min_target_step must be in (0, target_step]")

    coordinate_index = _coordinate_index(geometry, tool_axis)
    coordinate_name = "tool_alpha" if tool_axis is ToolAxis.A else "tool_beta"
    q = np.zeros(len(scalar_axes(geometry)), dtype=float)

    initial_jacobian = closure_jacobian(geometry, q)
    initial_tangent, initial_singular_values = null_tangent(initial_jacobian)
    points: list[AxisDrivePoint] = [
        AxisDrivePoint(
            target_angle=0.0,
            q=tuple(float(value) for value in q),
            closure_norm=float(np.linalg.norm(closure_residual(geometry, q))),
            smallest_singular_value=float(initial_singular_values[-1]),
            converged=True,
            newton_iterations=0,
        )
    ]

    status = "completed_full_input_turn"
    current_angle = 0.0
    step = float(target_step)
    tangent = initial_tangent
    while current_angle < requested_angle - 1e-12:
        target = min(current_angle + step, requested_angle)
        delta_input = target - current_angle
        component = float(tangent[coordinate_index])
        if abs(component) > 1e-8:
            predictor = q + tangent * (delta_input / component)
        else:
            predictor = q.copy()
        predictor[coordinate_index] = target
        candidate, converged, iterations = _correct_with_fixed_coordinate(
            geometry,
            predictor,
            coordinate_index=coordinate_index,
            target_angle=float(target),
            tolerance=tolerance,
            max_iterations=max_iterations,
        )
        if not converged and step > min_target_step + 1e-15:
            step = max(min_target_step, 0.5 * step)
            continue

        jacobian = closure_jacobian(geometry, candidate)
        tangent, singular_values = null_tangent(jacobian, previous=tangent)
        singular_margin = float(singular_values[-1])
        closure_norm = float(np.linalg.norm(closure_residual(geometry, candidate)))
        points.append(
            AxisDrivePoint(
                target_angle=float(target),
                q=tuple(float(value) for value in candidate),
                closure_norm=closure_norm,
                smallest_singular_value=singular_margin,
                converged=converged,
                newton_iterations=iterations,
            )
        )
        if not converged:
            status = "blocked_or_corrector_failure"
            break
        q = candidate
        current_angle = float(target)
        if singular_margin < singularity_tol and current_angle < requested_angle - 1e-12:
            status = "turning_or_change_point"
            break
        step = min(target_step, step * 1.5)

    converged_points = [point for point in points if point.converged]
    reached = converged_points[-1].target_angle if converged_points else 0.0
    full_turn = reached >= requested_angle - 1e-8
    if full_turn:
        status = "completed_full_input_turn"

    return AxisDriveTrace(
        family=geometry.family.value,
        tool_axis=tool_axis.value,
        coordinate_name=coordinate_name,
        points=tuple(points),
        target_step=target_step,
        requested_angle=requested_angle,
        reached_angle=float(reached),
        full_input_turn=full_turn,
        status=status,
    )


def plot_axis_drive_coordinates(trace: AxisDriveTrace, outpath: Path) -> Path:
    points = trace.converged_points
    if not points:
        raise ValueError("trace has no converged points")
    targets = [point.target_angle for point in points]
    values = np.asarray([point.q for point in points], dtype=float)
    figure = plt.figure(figsize=(9.2, 5.0))
    axis = figure.add_subplot(111)
    for index in range(values.shape[1]):
        axis.plot(targets, values[:, index], label=f"q{index + 1}")
    selected = "A / alpha" if trace.tool_axis == ToolAxis.A.value else "B / beta"
    axis.set_xlabel(f"Prescribed tool-{selected} input [rad]")
    axis.set_ylabel("Solved scalar coordinates [rad]")
    axis.set_title(
        f"{trace.family}: prescribed tool-{selected} closure drive "
        f"({trace.status}, reached {trace.reached_angle:.2f} rad)"
    )
    axis.legend(loc="best", fontsize="x-small", ncol=2)
    figure.tight_layout()
    figure.savefig(outpath, dpi=165)
    plt.close(figure)
    return outpath


def _path_limits(
    geometry: SpatialFourBarGeometry,
    points: tuple[AxisDrivePoint, ...],
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    centers_all: list[Array] = []
    for point in points:
        centers, _ = mechanism_state(geometry, np.asarray(point.q, dtype=float))
        centers_all.append(centers)
    stacked = np.vstack(centers_all)
    minimum = stacked.min(axis=0)
    maximum = stacked.max(axis=0)
    center = 0.5 * (minimum + maximum)
    half = max(float(np.max(maximum - minimum)) * 0.62, geometry.reference_length * 0.75)
    return tuple(
        (float(center[index] - half), float(center[index] + half))
        for index in range(3)
    )  # type: ignore[return-value]


def _draw_axis_drive_state(
    axis: Any,
    geometry: SpatialFourBarGeometry,
    point: AxisDrivePoint,
    *,
    tool_axis: str,
    limits: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    artists: list[Any] | None = None,
) -> list[Any]:
    centers, axis_lines = mechanism_state(geometry, np.asarray(point.q, dtype=float))
    cycle = [0, 1, 2, 3, 0]
    axis_extent = 0.32 * geometry.reference_length
    selected_name = "tool_alpha" if tool_axis == ToolAxis.A.value else "tool_beta"

    if artists is None:
        created: list[Any] = []
        (link_line,) = axis.plot(
            centers[cycle, 0],
            centers[cycle, 1],
            centers[cycle, 2],
            marker="o",
            linewidth=2.0,
        )
        created.append(link_line)
        for origin, direction, name in axis_lines:
            start = origin - axis_extent * direction
            end = origin + axis_extent * direction
            width = 3.0 if name == selected_name else 1.0
            alpha = 1.0 if name == selected_name else 0.45
            (axis_line,) = axis.plot(
                (start[0], end[0]),
                (start[1], end[1]),
                (start[2], end[2]),
                linewidth=width,
                alpha=alpha,
            )
            created.append(axis_line)
            axis.text(end[0], end[1], end[2], name, fontsize=7)
        axis.set_xlim(*limits[0])
        axis.set_ylim(*limits[1])
        axis.set_zlim(*limits[2])
        axis.set_box_aspect((1.0, 1.0, 1.0))
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        axis.set_zlabel("z")
        return created

    artists[0].set_data_3d(
        centers[cycle, 0],
        centers[cycle, 1],
        centers[cycle, 2],
    )
    for artist, (origin, direction, _name) in zip(artists[1:], axis_lines, strict=True):
        start = origin - axis_extent * direction
        end = origin + axis_extent * direction
        artist.set_data_3d(
            (start[0], end[0]),
            (start[1], end[1]),
            (start[2], end[2]),
        )
    return artists


def animate_axis_drive(
    geometry: SpatialFourBarGeometry,
    trace: AxisDriveTrace,
    outpath: Path,
    *,
    fps: int = 12,
    dpi: int = 105,
) -> Path:
    points = trace.converged_points
    if not points:
        raise ValueError("trace has no converged points to animate")
    stride = max(1, len(points) // 45)
    frames = list(points[::stride])
    if frames[-1] is not points[-1]:
        frames.append(points[-1])

    limits = _path_limits(geometry, tuple(frames))
    figure = plt.figure(figsize=(7.0, 6.0))
    axis = figure.add_subplot(111, projection="3d")
    artists = _draw_axis_drive_state(
        axis,
        geometry,
        frames[0],
        tool_axis=trace.tool_axis,
        limits=limits,
    )
    selected = "A / alpha" if trace.tool_axis == ToolAxis.A.value else "B / beta"

    def update(frame_index: int) -> list[Any]:
        point = frames[frame_index]
        updated = _draw_axis_drive_state(
            axis,
            geometry,
            point,
            tool_axis=trace.tool_axis,
            limits=limits,
            artists=artists,
        )
        axis.set_title(
            f"{trace.family} | prescribed tool-{selected}: "
            f"{point.target_angle:.2f} rad | {trace.status}"
        )
        return updated

    update(0)
    animation = FuncAnimation(
        figure,
        update,
        frames=len(frames),
        interval=1000 / fps,
        blit=False,
    )
    animation.save(outpath, writer=PillowWriter(fps=fps), dpi=dpi)
    plt.close(figure)
    return outpath
