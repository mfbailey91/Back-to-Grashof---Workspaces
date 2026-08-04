"""Reproducible Matplotlib visualizations for synthetic 6R axes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from sixr_grashof.architectures.base import GeometryReport
from sixr_grashof.kinematics.forward import ForwardKinematicsResult

_INK = "#1a1f24"
_LINK = "#4a5560"
_COLORS = ["#1a1f24", "#a34848", "#2f6f8f", "#1f7a6c", "#8b6914", "#c47b2c"]


def _add(
    u: tuple[float, float, float],
    v: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (u[0] + v[0], u[1] + v[1], u[2] + v[2])


def _scale(u: tuple[float, float, float], s: float) -> tuple[float, float, float]:
    return (u[0] * s, u[1] * s, u[2] * s)


def _draw_robot_on_axis(
    ax: Any,
    fk: ForwardKinematicsResult,
    report: GeometryReport,
    *,
    axis_length: float,
    title: str | None,
) -> None:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []

    chain = [j.origin for j in fk.joints] + [fk.tool_position]
    ax.plot(
        [p[0] for p in chain],
        [p[1] for p in chain],
        [p[2] for p in chain],
        color=_LINK,
        linewidth=2.0,
        alpha=0.85,
        label="links",
    )

    for joint, color in zip(fk.joints, _COLORS, strict=True):
        p = joint.origin
        d = joint.axis.direction
        p0 = _add(p, _scale(d, -0.5 * axis_length))
        p1 = _add(p, _scale(d, 0.5 * axis_length))
        ax.plot(
            [p0[0], p1[0]],
            [p0[1], p1[1]],
            [p0[2], p1[2]],
            color=color,
            linewidth=2.8,
            label=f"z{joint.index}",
        )
        ax.scatter([p[0]], [p[1]], [p[2]], color=color, s=36)
        xs.extend([p0[0], p1[0], p[0]])
        ys.extend([p0[1], p1[1], p[1]])
        zs.extend([p0[2], p1[2], p[2]])

    c = report.wrist_concurrency.center
    ax.scatter([c[0]], [c[1]], [c[2]], color=_INK, marker="*", s=140, label="c*")
    xs.append(c[0])
    ys.append(c[1])
    zs.append(c[2])
    tool = fk.tool_position
    ax.scatter([tool[0]], [tool[1]], [tool[2]], color="#a34848", marker="o", s=55, label="tool")
    xs.append(tool[0])
    ys.append(tool[1])
    zs.append(tool[2])

    default_title = (
        f"Arch {report.architecture_id} | spherical={report.spherical_status} | "
        f"ρ={report.wrist_concurrency.residual_rho:.3e}"
    )
    ax.set_title(title or default_title, fontsize=10, color=_INK)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")

    mid_x = 0.5 * (min(xs) + max(xs))
    mid_y = 0.5 * (min(ys) + max(ys))
    mid_z = 0.5 * (min(zs) + max(zs))
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 0.5) * 0.55
    ax.set_xlim(mid_x - span, mid_x + span)
    ax.set_ylim(mid_y - span, mid_y + span)
    ax.set_zlim(mid_z - span, mid_z + span)


def plot_robot_with_links(
    fk: ForwardKinematicsResult,
    report: GeometryReport,
    *,
    ax: Any | None = None,
    axis_length: float = 0.35,
    title: str | None = None,
) -> Any:
    """Draw links + axes onto an existing or new 3D axes."""
    owns = ax is None
    if ax is None:
        fig = plt.figure(figsize=(8, 7))
        ax = fig.add_subplot(111, projection="3d")
    _draw_robot_on_axis(ax, fk, report, axis_length=axis_length, title=title)
    if owns:
        ax.legend(loc="upper left", fontsize=8, frameon=False)
    return ax


def plot_robot_axes(
    fk: ForwardKinematicsResult,
    report: GeometryReport,
    *,
    axis_length: float = 0.35,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot joint origins, link chain, axis directions, and wrist-center candidate."""
    fig = plt.figure(figsize=(8, 7))
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, projection="3d")
    plot_robot_with_links(fk, report, ax=ax, axis_length=axis_length)
    ax.legend(loc="upper left", fontsize=8, frameon=False)

    out_path: Path | None = None
    if output is not None:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return out_path


def format_geometry_report(report: GeometryReport) -> str:
    w = report.wrist_concurrency
    lines = [
        f"architecture_id: {report.architecture_id}",
        f"L2={report.params.L2}, L3={report.params.L3}, Lt={report.params.Lt}",
        f"epsilon_w={report.params.epsilon_w}, epsilon_s={report.params.epsilon_s}",
        f"z1_z2_distance: {report.z1_z2_distance:.6e}",
        f"z2_z3_parallel: {report.z2_z3_parallel}",
        f"z2_z3_z4_parallel: {report.z2_z3_z4_parallel}",
        f"regional_exact_candidate: {report.regional_exact_candidate}",
        f"wrist_center: {w.center}",
        f"concurrency_residual_rho: {w.residual_rho:.6e}",
        f"spherical_status: {report.spherical_status}",
        f"rho_exact={w.rho_exact}, rho_invalid={w.rho_invalid}",
    ]
    return "\n".join(lines)
