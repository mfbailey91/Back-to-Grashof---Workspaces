"""Matplotlib orthographic step plots for the visual probe.

Isolated from ``grashof_workspace.plotting``. Each scene payload can be
rendered to a reproducible PNG via the CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def _rot_project(
    points: np.ndarray,
    yaw: float = 0.7,
    pitch: float = 0.4,
) -> np.ndarray:
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=float)
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cp, -sp], [0.0, sp, cp]], dtype=float)
    out = points @ ry.T @ rx.T
    return np.asarray(out, dtype=float)


def _draw_axis(
    ax: Any,
    axis: dict[str, Any],
    length: float,
    color: Any,
    label: str = "",
    *,
    lw: float = 1.8,
    ls: str = "-",
) -> None:
    p = np.asarray(axis["point"], dtype=float)
    d = np.asarray(axis["direction"], dtype=float)
    a = p - length * d
    b = p + length * d
    pts = _rot_project(np.vstack([a, b]))
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, ls=ls)
    if label:
        ax.text(pts[1, 0], pts[1, 1], f" {label}", color="#333333", fontsize=8)


def render_scene_figure(scene: dict[str, Any]) -> Figure:
    """Render one orthographic step plot from a scene payload."""
    fig, ax = plt.subplots(figsize=(7.2, 5.4), dpi=120)
    fk = scene.get("fk") or {}
    length = float(fk.get("axis_length", 0.3))
    opacity = float(scene["arm_opacity"]) if scene.get("arm_opacity") is not None else 1.0
    show_links = scene.get("show_links", True)
    show_centers = scene.get("show_joint_centers", True)
    show_axes = scene.get("show_axes", True)
    show_task = scene.get("show_task", True)
    selected = set(scene.get("selected_joint_indices") or [])
    dim = bool(scene.get("dim_unselected_axes"))
    label_all = bool(scene.get("label_all_axes"))

    if scene.get("fk_ghost") and show_links:
        ghost = scene["fk_ghost"]
        go = float(scene.get("ghost_opacity", 0.25))
        for link in ghost.get("links") or []:
            pts = _rot_project(np.asarray([link["start"], link["end"]], dtype=float))
            ax.plot(pts[:, 0], pts[:, 1], color=(0.4, 0.4, 0.4, go), lw=2.0)

    if show_links:
        for link in fk.get("links") or []:
            pts = _rot_project(np.asarray([link["start"], link["end"]], dtype=float))
            ax.plot(pts[:, 0], pts[:, 1], color=(0.15, 0.15, 0.15, opacity), lw=2.4)

    for joint in fk.get("joints") or []:
        origin = np.asarray(joint["origin"], dtype=float)
        o2 = _rot_project(origin.reshape(1, 3))[0]
        idx = int(joint["index"])
        if show_centers:
            ax.scatter([o2[0]], [o2[1]], c=[[0.1, 0.1, 0.1, opacity]], s=18, zorder=3)
            ax.text(o2[0], o2[1], f" {joint['label']}", fontsize=8, color="#222")
        if show_axes:
            is_sel = (not selected) or (idx in selected)
            if not is_sel and scene.get("show_unselected_axes") is False:
                continue
            color: Any
            if selected and dim and not is_sel:
                color = (0.55, 0.55, 0.55, 0.35)
            elif is_sel and selected:
                color = "#0b6e4f"
            else:
                color = (0.12, 0.35, 0.63, opacity)
            label = joint["label"] if (label_all or (selected and idx in selected)) else ""
            ls = "--" if (scene.get("show_roll") and idx == 6) else "-"
            _draw_axis(ax, joint["axis"], length, color, label, ls=ls)

    if show_task and fk.get("tool_point") is not None:
        p = np.asarray(fk["tool_point"], dtype=float)
        d = np.asarray(fk["pointing"], dtype=float)
        tip = p + 0.8 * length * d
        pts = _rot_project(np.vstack([p, tip]))
        ax.scatter([pts[0, 0]], [pts[0, 1]], c="#b00020", s=28, zorder=4)
        ax.plot(pts[:, 0], pts[:, 1], color="#b00020", lw=2.0)
        ax.text(pts[0, 0], pts[0, 1], " p", color="#b00020", fontsize=9)
        ax.text(pts[1, 0], pts[1, 1], " d", color="#b00020", fontsize=9)

    closure = scene.get("closure")
    if closure and scene.get("show_closure_center", True):
        c = np.asarray(closure["center"], dtype=float)
        c2 = _rot_project(c.reshape(1, 3))[0]
        ax.scatter([c2[0]], [c2[1]], c="#6a1b9a", s=36, zorder=4)
        ax.text(c2[0], c2[1], " S_v", color="#6a1b9a", fontsize=9)
    if closure and scene.get("show_closure_axes", bool(closure)):
        for name, axis in (closure.get("axes") or {}).items():
            _draw_axis(ax, axis, 0.7 * length, "#8e24aa", name)

    if scene.get("show_roll") and scene.get("roll"):
        _draw_axis(ax, scene["roll"]["axis"], length, "#b45000", scene["roll"]["label"], ls="--")

    if scene.get("candidate") and scene["candidate"].get("axes"):
        colors = {"S": "#6a1b9a", "U": "#0b6e4f", "R": "#1565c0"}
        for item in scene["candidate"]["axes"]:
            _draw_axis(
                ax,
                item["axis"],
                length,
                colors.get(item["role"], "#333"),
                item["source_id"],
                lw=2.4,
            )

    if scene.get("show_intersections"):
        for rel in scene.get("relations") or []:
            if rel.get("intersection") is None:
                continue
            p = np.asarray(rel["intersection"], dtype=float)
            p2 = _rot_project(p.reshape(1, 3))[0]
            ax.scatter([p2[0]], [p2[1]], c="#c62828", s=40, marker="x", zorder=5)
            ax.text(
                p2[0],
                p2[1],
                f" R{rel['joint_a']}∩R{rel['joint_b']}",
                color="#c62828",
                fontsize=8,
            )

    frame_len = float(fk.get("frame_length", 0.08))

    def _draw_frame(frame: dict[str, Any], *, scale: float = 1.0) -> None:
        o = np.asarray(frame["origin_world"], dtype=float)
        for key, color, suffix in (
            ("local_x", "#c62828", ".X"),
            ("local_y", "#2e7d32", ".Y"),
            ("local_z", "#1565c0", ".Z"),
        ):
            d = np.asarray(frame[key], dtype=float)
            tip = o + scale * frame_len * d
            pts = _rot_project(np.vstack([o, tip]))
            ax.plot(pts[:, 0], pts[:, 1], color=color, lw=2.0)
            ax.text(pts[1, 0], pts[1, 1], f" {frame['label']}{suffix}", color=color, fontsize=7)

    if scene.get("show_world_frame") and fk.get("world_frame"):
        _draw_frame(fk["world_frame"], scale=1.6)
    if scene.get("show_local_frames"):
        for fr in fk.get("local_frames") or []:
            _draw_frame(fr)

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title(scene.get("title", scene.get("scene_id", "scene")), fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return fig


def write_scene_plot(path: Path, scene: dict[str, Any]) -> Path:
    """Write one scene PNG and close the figure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig = render_scene_figure(scene)
    fig.savefig(path, bbox_inches="tight", facecolor="#f7f5f1")
    plt.close(fig)
    return path
