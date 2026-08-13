"""Workspace exemplar visualization for planar 3R ↔ reduced four-bar comparison.

Visualization aid only: reuses analytical Planar3R / FourBar predicates and does
not change workspace classification or issue certificates.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from math import cos, hypot, sin
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

from .fourbar import FourBar
from .fourbar_poses import (
    FourBarPose,
    angle_span,
    pose_polyline,
    sample_poses,
    solve_planar_2r,
)
from .planar3r import DEFAULT_TOL, Planar3R, RadialMechanismState

Vec2 = tuple[float, float]


@dataclass(frozen=True, slots=True)
class WorkspaceExemplar:
    """One representative Cartesian workspace probe."""

    name: str
    point_xy: tuple[float, float]
    classification: str
    radial_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "point_xy": list(self.point_xy),
            "classification": self.classification,
            "radial_value": self.radial_value,
        }


@dataclass(frozen=True, slots=True)
class ExemplarCaseData:
    """Geometry and samples for one exemplar render."""

    exemplar: WorkspaceExemplar
    arm: Planar3R
    linkage: FourBar
    state: RadialMechanismState
    poses: tuple[FourBarPose, ...]
    orientation_samples: tuple[float, ...]
    orientation_coverage_type: str
    sampled_coverage_fraction: float | None
    serial_ghost_joints: tuple[Vec2, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "exemplar": self.exemplar.to_dict(),
            "arm_lengths": [self.arm.l1, self.arm.l2, self.arm.l3],
            "linkage_lengths": list(self.linkage.lengths),
            "state": asdict(self.state),
            "pose_count": len(self.poses),
            "orientation_samples": list(self.orientation_samples),
            "orientation_coverage_type": self.orientation_coverage_type,
            "sampled_coverage_fraction": self.sampled_coverage_fraction,
            "serial_ghost_joints": [list(point) for point in self.serial_ghost_joints],
            "input_angle_span": angle_span(self.orientation_samples),
        }


def _point_on_ray(rho: float, ray_angle: float) -> Vec2:
    return (float(rho * cos(ray_angle)), float(rho * sin(ray_angle)))


def _finite_dexterous_intervals(
    arm: Planar3R,
    *,
    tol: float = DEFAULT_TOL,
) -> tuple[tuple[float, float], ...]:
    return tuple(
        (inner, outer)
        for inner, outer in arm.dexterous_radial_intervals(tol=tol)
        if outer - inner > tol
    )


def _reachable_nondexterous_segments(
    arm: Planar3R,
    *,
    tol: float = DEFAULT_TOL,
) -> tuple[tuple[float, float], ...]:
    reachable_inner, reachable_outer = arm.reachable_radial_interval()
    dexterous = sorted(_finite_dexterous_intervals(arm, tol=tol))
    segments: list[tuple[float, float]] = []
    cursor = reachable_inner
    for inner, outer in dexterous:
        if inner - cursor > tol:
            segments.append((cursor, min(inner, reachable_outer)))
        cursor = max(cursor, outer)
    if reachable_outer - cursor > tol:
        segments.append((cursor, reachable_outer))
    return tuple(
        (a, b)
        for a, b in segments
        if b - a > tol and arm.is_reachable_radius(0.5 * (a + b), tol=tol)
    )


def select_workspace_exemplars(
    arm: Planar3R,
    *,
    include_boundary: bool = True,
    prefer_same_ray: bool = True,
    ray_angle: float = 0.0,
    tol: float = DEFAULT_TOL,
) -> tuple[WorkspaceExemplar, ...]:
    """Pick representative workspace points on one ray when practical."""

    del prefer_same_ray  # always same-ray in this MVP
    dexterous = _finite_dexterous_intervals(arm, tol=tol)
    if not dexterous:
        raise ValueError("arm has no positive-width dexterous interval for inside exemplar")
    nondex = _reachable_nondexterous_segments(arm, tol=tol)
    if not nondex:
        raise ValueError("arm has no reachable non-dexterous segment for outside exemplar")

    d_inner, d_outer = dexterous[0]
    inside_rho = 0.5 * (d_inner + d_outer)
    n_inner, n_outer = nondex[-1]
    outside_rho = 0.5 * (n_inner + n_outer)
    boundary_rho = d_outer

    exemplars = [
        WorkspaceExemplar(
            name="inside",
            point_xy=_point_on_ray(inside_rho, ray_angle),
            classification="dexterous",
            radial_value=inside_rho,
        ),
        WorkspaceExemplar(
            name="outside",
            point_xy=_point_on_ray(outside_rho, ray_angle),
            classification="reachable_nondexterous",
            radial_value=outside_rho,
        ),
    ]
    if include_boundary:
        exemplars.append(
            WorkspaceExemplar(
                name="boundary",
                point_xy=_point_on_ray(boundary_rho, ray_angle),
                classification="boundary",
                radial_value=boundary_rho,
            )
        )
    return tuple(exemplars)


def _serial_ghost_joints(
    arm: Planar3R,
    point_xy: Vec2,
    seed_pose: FourBarPose,
    *,
    tol: float = DEFAULT_TOL,
) -> tuple[Vec2, ...]:
    """Ghost serial chain: base → elbow → wrist → EE using seed terminal heading."""

    ee = point_xy
    # Map reduced-loop coordinates (ground along +x of length rho) into world with EE at point.
    rho = hypot(*ee)
    if rho <= tol:
        return ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), ee)

    # Reduced ground_b is EE; input_tip is wrist in the reduced frame.
    # Rotate/translate reduced frame so ground_a→ground_b aligns with base→EE.
    gx = ee[0] / rho
    gy = ee[1] / rho
    # Rotation taking (1,0) to (gx, gy)
    tip_local = seed_pose.input_tip
    wrist = (
        tip_local[0] * gx - tip_local[1] * gy,
        tip_local[0] * gy + tip_local[1] * gx,
    )
    # Prefer analytical 2R to the wrist so the ghost uses physical l1,l2.
    solved = solve_planar_2r(wrist, arm.l1, arm.l2, elbow_up=True, tol=tol)
    if solved is None:
        solved = solve_planar_2r(wrist, arm.l1, arm.l2, elbow_up=False, tol=tol)
    if solved is None:
        # Fall back to reduced output/coupler joints mapped into world.
        joint_local = seed_pose.coupler_output_joint
        elbow = (
            joint_local[0] * gx - joint_local[1] * gy,
            joint_local[0] * gy + joint_local[1] * gx,
        )
        return ((0.0, 0.0), elbow, wrist, ee)
    elbow, _ = solved
    return ((0.0, 0.0), elbow, wrist, ee)


def _coverage_type(exemplar: WorkspaceExemplar, state: RadialMechanismState) -> str:
    if exemplar.name == "boundary" or exemplar.classification == "boundary":
        return "critical"
    if state.dexterous:
        return "full"
    if state.assemblable:
        return "partial"
    raise ValueError(f"exemplar {exemplar.name} is not assemblable")


def build_exemplar_case(
    arm: Planar3R,
    exemplar: WorkspaceExemplar,
    *,
    samples: int = 72,
    tol: float = DEFAULT_TOL,
) -> ExemplarCaseData:
    """Build reduced-motion samples and ghost serial joints for one exemplar."""

    rho = exemplar.radial_value
    if rho is None:
        rho = hypot(*exemplar.point_xy)
    linkage = arm.fourbar_at_radius(rho)
    state = arm.mechanism_state(rho, tol=tol)
    if not state.assemblable:
        raise ValueError(f"exemplar {exemplar.name} at rho={rho} is not assemblable")

    poses = sample_poses(linkage, samples, branch="open", tol=tol)
    if not poses:
        poses = sample_poses(linkage, samples, branch="crossed", tol=tol)
    if not poses:
        raise ValueError(f"no assembled poses for exemplar {exemplar.name} at rho={rho}")

    seed = poses[len(poses) // 2]
    ghost = _serial_ghost_joints(arm, exemplar.point_xy, seed, tol=tol)
    coverage = _coverage_type(exemplar, state)
    fraction = arm.sampled_orientation_coverage(
        exemplar.point_xy[0],
        exemplar.point_xy[1],
        samples=max(36, samples),
        tol=tol,
    )
    return ExemplarCaseData(
        exemplar=exemplar,
        arm=arm,
        linkage=linkage,
        state=state,
        poses=poses,
        orientation_samples=tuple(pose.terminal_orientation for pose in poses),
        orientation_coverage_type=coverage,
        sampled_coverage_fraction=fraction,
        serial_ghost_joints=ghost,
    )


def _draw_case_on_axis(axis: Any, case: ExemplarCaseData, *, pose_index: int | None = None) -> None:
    pose = case.poses[0 if pose_index is None else pose_index]
    ghost = case.serial_ghost_joints
    gx = [point[0] for point in ghost]
    gy = [point[1] for point in ghost]
    axis.plot(gx, gy, color="#888888", linewidth=2.0, alpha=0.45, solid_capstyle="round")
    axis.scatter(gx, gy, color="#888888", s=18, alpha=0.45, zorder=2)

    # Map reduced pose into world so ground_b coincides with EE.
    ee = case.exemplar.point_xy
    rho = hypot(*ee) if hypot(*ee) > 1e-15 else 1.0
    gx_hat = ee[0] / rho
    gy_hat = ee[1] / rho

    def _map_point(local: Vec2) -> Vec2:
        return (
            local[0] * gx_hat - local[1] * gy_hat,
            local[0] * gy_hat + local[1] * gx_hat,
        )

    mapped = FourBarPose(
        input_angle=pose.input_angle,
        ground_a=_map_point(pose.ground_a),
        ground_b=_map_point(pose.ground_b),
        input_tip=_map_point(pose.input_tip),
        coupler_output_joint=_map_point(pose.coupler_output_joint),
        branch=pose.branch,
        terminal_orientation=pose.terminal_orientation,
    )
    loop = pose_polyline(mapped)
    xs = [point[0] for point in loop]
    ys = [point[1] for point in loop]
    axis.plot(xs, ys, color="#1f4e79", linewidth=2.8, solid_capstyle="round", zorder=3)
    axis.scatter(
        [mapped.ground_a[0], mapped.ground_b[0]],
        [mapped.ground_a[1], mapped.ground_b[1]],
        color="#c0392b",
        s=36,
        zorder=4,
        label="ground pivots",
    )
    axis.scatter([ee[0]], [ee[1]], color="#d35400", s=55, zorder=5, marker="o")
    axis.add_patch(Circle((0.0, 0.0), 0.03 * max(case.arm.l1, 1.0), color="#333333"))
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.25)
    title = (
        f"{case.exemplar.name} | {case.exemplar.classification}\n"
        f"p=({case.exemplar.point_xy[0]:.3g}, {case.exemplar.point_xy[1]:.3g})  "
        f"coverage={case.orientation_coverage_type}"
    )
    axis.set_title(title, fontsize=10)


def _axis_limits_for_cases(cases: tuple[ExemplarCaseData, ...]) -> tuple[float, float, float, float]:
    xs: list[float] = [0.0]
    ys: list[float] = [0.0]
    for case in cases:
        for point in case.serial_ghost_joints:
            xs.append(point[0])
            ys.append(point[1])
        for pose in case.poses:
            for local in (
                pose.ground_a,
                pose.ground_b,
                pose.input_tip,
                pose.coupler_output_joint,
            ):
                ee = case.exemplar.point_xy
                rho = hypot(*ee) if hypot(*ee) > 1e-15 else 1.0
                gx_hat = ee[0] / rho
                gy_hat = ee[1] / rho
                xs.append(local[0] * gx_hat - local[1] * gy_hat)
                ys.append(local[0] * gy_hat + local[1] * gx_hat)
    pad = 0.15 * max(1.0, max(xs) - min(xs), max(ys) - min(ys))
    return (min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad)


def render_exemplar_static(case: ExemplarCaseData, out_path: Path) -> Path:
    """Render one static exemplar image."""

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(5.2, 5.0))
    _draw_case_on_axis(axis, case, pose_index=len(case.poses) // 2)
    xmin, xmax, ymin, ymax = _axis_limits_for_cases((case,))
    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    span = angle_span(case.orientation_samples)
    axis.text(
        0.02,
        0.02,
        f"input span ≈ {span:.2f} rad\nsampled coverage={case.sampled_coverage_fraction:.3f}",
        transform=axis.transAxes,
        fontsize=8,
        va="bottom",
    )
    figure.tight_layout()
    figure.savefig(out_path, dpi=160)
    plt.close(figure)
    return out_path


def animate_exemplar_case(
    case: ExemplarCaseData,
    out_path: Path,
    *,
    show_ghost_manipulator: bool = True,
) -> Path:
    """Animate admissible reduced four-bar motion for one exemplar."""

    del show_ghost_manipulator  # ghost always drawn lightly
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(5.2, 5.0))
    xmin, xmax, ymin, ymax = _axis_limits_for_cases((case,))

    def _draw(frame_index: int) -> None:
        axis.cla()
        _draw_case_on_axis(axis, case, pose_index=frame_index)
        axis.set_xlim(xmin, xmax)
        axis.set_ylim(ymin, ymax)
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        axis.text(
            0.02,
            0.02,
            f"coverage={case.orientation_coverage_type}",
            transform=axis.transAxes,
            fontsize=9,
            va="bottom",
        )

    animation = FuncAnimation(figure, _draw, frames=len(case.poses), interval=80)
    animation.save(out_path, writer=PillowWriter(fps=12))
    plt.close(figure)
    return out_path


def render_workspace_exemplar_comparison(
    cases: tuple[ExemplarCaseData, ...],
    out_path: Path,
) -> Path:
    """Render a multi-column comparison figure."""

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = len(cases)
    figure, axes = plt.subplots(1, count, figsize=(4.6 * count, 4.8), squeeze=False)
    xmin, xmax, ymin, ymax = _axis_limits_for_cases(cases)
    for axis, case in zip(axes[0], cases, strict=True):
        _draw_case_on_axis(axis, case, pose_index=len(case.poses) // 2)
        axis.set_xlim(xmin, xmax)
        axis.set_ylim(ymin, ymax)
        span = angle_span(case.orientation_samples)
        axis.text(
            0.02,
            0.02,
            f"coverage={case.orientation_coverage_type}\nspan≈{span:.2f} rad",
            transform=axis.transAxes,
            fontsize=8,
            va="bottom",
        )
    figure.suptitle(
        "Workspace exemplars: reduced four-bar behavior vs classification",
        fontsize=12,
    )
    figure.tight_layout()
    figure.savefig(out_path, dpi=160)
    plt.close(figure)
    return out_path


def render_workspace_exemplars(
    arm: Planar3R,
    out_dir: Path,
    *,
    include_boundary: bool = True,
    samples: int = 72,
    ray_angle: float = 0.0,
    animate: bool = True,
) -> dict[str, Path]:
    """Select exemplars, render artifacts, and write a JSON summary."""

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    exemplars = select_workspace_exemplars(
        arm,
        include_boundary=include_boundary,
        ray_angle=ray_angle,
    )
    cases = tuple(
        build_exemplar_case(arm, exemplar, samples=samples) for exemplar in exemplars
    )
    paths: dict[str, Path] = {}
    for case in cases:
        name = case.exemplar.name
        paths[f"{name}_static"] = render_exemplar_static(
            case, out_dir / f"{name}_static.png"
        )
        if animate:
            paths[f"{name}_animation"] = animate_exemplar_case(
                case, out_dir / f"{name}_animation.gif"
            )
    paths["comparison"] = render_workspace_exemplar_comparison(
        cases, out_dir / "comparison.png"
    )

    payload = {
        "program": "workspace_exemplars",
        "note": (
            "Visualization aid for the trusted planar 3R↔4R map; "
            "not a DecompositionCertificate path."
        ),
        "arm_lengths": [arm.l1, arm.l2, arm.l3],
        "ray_angle": ray_angle,
        "include_boundary": include_boundary,
        "samples": samples,
        "cases": [case.to_dict() for case in cases],
    }
    json_path = out_dir / "exemplars.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    paths["json"] = json_path
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render planar workspace exemplars comparing reduced four-bar motion "
            "inside / outside / boundary of the dexterous set."
        )
    )
    parser.add_argument("--l1", type=float, default=2.0)
    parser.add_argument("--l2", type=float, default=2.0)
    parser.add_argument("--l3", type=float, default=1.0)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/workspace_exemplars"))
    parser.add_argument("--samples", type=int, default=72)
    parser.add_argument("--ray-angle", type=float, default=0.0)
    parser.add_argument(
        "--include-boundary",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include the dexterous-boundary exemplar (default: true)",
    )
    parser.add_argument(
        "--animate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write per-exemplar GIFs (default: true)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    arm = Planar3R(args.l1, args.l2, args.l3)
    paths = render_workspace_exemplars(
        arm,
        args.out_dir,
        include_boundary=args.include_boundary,
        samples=args.samples,
        ray_angle=args.ray_angle,
        animate=args.animate,
    )
    for label, path in sorted(paths.items()):
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
