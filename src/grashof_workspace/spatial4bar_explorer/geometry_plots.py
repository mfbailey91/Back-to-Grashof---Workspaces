from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from .geometry import SpatialFourBarGeometry, add, iter_joint_motion_axes, scale, subtract


def plot_physical_geometry_3d(geometry: SpatialFourBarGeometry, outpath: Path) -> None:
    """Render one reference assembly with link centerlines and all motion axes."""
    figure = plt.figure(figsize=(7.5, 6.0))
    axis = figure.add_subplot(111, projection="3d")

    for link_index, link in enumerate(geometry.links):
        start = geometry.joints[link.joint_a].center
        end = geometry.joints[link.joint_b].center
        linewidth = 3.0 if link_index == geometry.ground_link else 1.8
        axis.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            [start[2], end[2]],
            linewidth=linewidth,
        )

    axis_scale = 0.34 * geometry.reference_length
    for joint, _, direction in iter_joint_motion_axes(geometry):
        start = subtract(joint.center, scale(direction, axis_scale))
        end = add(joint.center, scale(direction, axis_scale))
        axis.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            [start[2], end[2]],
            linestyle="--",
            linewidth=1.2,
        )

    for joint in geometry.joints:
        center = joint.center
        axis.scatter([center[0]], [center[1]], [center[2]], s=35)
        axis.text(center[0], center[1], center[2], f" {joint.name}:{joint.kind.value}")

    centers = [joint.center for joint in geometry.joints]
    xs = [center[0] for center in centers]
    ys = [center[1] for center in centers]
    zs = [center[2] for center in centers]
    span = max(
        max(xs) - min(xs),
        max(ys) - min(ys),
        max(zs) - min(zs),
        geometry.reference_length,
    )
    midpoint = (
        (max(xs) + min(xs)) / 2.0,
        (max(ys) + min(ys)) / 2.0,
        (max(zs) + min(zs)) / 2.0,
    )
    half = 0.62 * span
    axis.set_xlim(midpoint[0] - half, midpoint[0] + half)
    axis.set_ylim(midpoint[1] - half, midpoint[1] + half)
    axis.set_zlim(midpoint[2] - half, midpoint[2] + half)
    axis.set_box_aspect((1.0, 1.0, 1.0))
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_zlabel("z")
    axis.set_title(f"Physical reference geometry: {geometry.family.value}")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)
