"""Planar four-bar pose sampling for visualization (not classification).

Loop order matches ``FourBar`` / planar-3R reduction:

    ground_a (base) --output(l1)-- P --coupler(l2)-- input_tip --input(l3)-- ground_b (EE)

Ground pivots sit on the x-axis at ``(0, 0)`` and ``(ground, 0)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, atan2, cos, isfinite, pi, sin, sqrt

from .fourbar import FourBar

Vec2 = tuple[float, float]


@dataclass(frozen=True, slots=True)
class FourBarPose:
    """One assembled planar four-bar configuration."""

    input_angle: float
    ground_a: Vec2
    ground_b: Vec2
    input_tip: Vec2
    coupler_output_joint: Vec2
    branch: str
    terminal_orientation: float

    def to_dict(self) -> dict[str, object]:
        return {
            "input_angle": self.input_angle,
            "ground_a": list(self.ground_a),
            "ground_b": list(self.ground_b),
            "input_tip": list(self.input_tip),
            "coupler_output_joint": list(self.coupler_output_joint),
            "branch": self.branch,
            "terminal_orientation": self.terminal_orientation,
        }


def _circle_intersections(
    c1: Vec2,
    r1: float,
    c2: Vec2,
    r2: float,
    *,
    tol: float = 1e-12,
) -> tuple[Vec2, ...]:
    x1, y1 = c1
    x2, y2 = c2
    dx = x2 - x1
    dy = y2 - y1
    dist = sqrt(dx * dx + dy * dy)
    if dist > r1 + r2 + tol or dist < abs(r1 - r2) - tol:
        return ()
    if dist <= tol:
        return ()

    a = (r1 * r1 - r2 * r2 + dist * dist) / (2.0 * dist)
    h_sq = r1 * r1 - a * a
    if h_sq < -tol:
        return ()
    h = sqrt(max(0.0, h_sq))
    xm = x1 + a * dx / dist
    ym = y1 + a * dy / dist
    rx = -dy * (h / dist)
    ry = dx * (h / dist)
    p_plus = (xm + rx, ym + ry)
    p_minus = (xm - rx, ym - ry)
    if h <= tol:
        return (p_plus,)
    return (p_plus, p_minus)


def _branch_sign(ground_a: Vec2, input_tip: Vec2, joint: Vec2) -> float:
    ax, ay = ground_a
    bx, by = input_tip
    px, py = joint
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax)


def pose_at_input_angle(
    linkage: FourBar,
    theta: float,
    *,
    branch: str = "open",
    tol: float = 1e-12,
) -> FourBarPose | None:
    """Assemble the loop at designated-input angle ``theta``.

    ``branch`` is ``\"open\"`` (nonnegative cross product of ground_a→tip×ground_a→P)
    or ``\"crossed\"``.
    """

    if branch not in {"open", "crossed"}:
        raise ValueError("branch must be 'open' or 'crossed'")
    if not linkage.is_assemblable(tol=tol):
        return None

    ground_a = (0.0, 0.0)
    ground_b = (float(linkage.ground), 0.0)
    input_tip = (
        ground_b[0] + linkage.input * cos(theta),
        ground_b[1] + linkage.input * sin(theta),
    )
    candidates = _circle_intersections(
        ground_a,
        linkage.output,
        input_tip,
        linkage.coupler,
        tol=tol,
    )
    if not candidates:
        return None

    if len(candidates) == 1:
        joint = candidates[0]
        chosen_branch = "open" if _branch_sign(ground_a, input_tip, joint) >= -tol else "crossed"
        if chosen_branch != branch and abs(_branch_sign(ground_a, input_tip, joint)) > tol:
            return None
    else:
        ordered = sorted(
            candidates,
            key=lambda point: _branch_sign(ground_a, input_tip, point),
            reverse=True,
        )
        joint = ordered[0] if branch == "open" else ordered[1]

    return FourBarPose(
        input_angle=float(theta),
        ground_a=ground_a,
        ground_b=ground_b,
        input_tip=input_tip,
        coupler_output_joint=joint,
        branch=branch,
        terminal_orientation=float(theta),
    )


def admissible_input_angle_interval(
    linkage: FourBar,
    *,
    tol: float = 1e-12,
) -> tuple[float, float] | None:
    """Return a closed admissible input-angle interval, or ``None`` if empty.

    Full rotation is reported as ``(0, 2π)``. Rocker cases return the continuous
    interval of angles where the coupler-output chain can close.
    """

    if not linkage.is_assemblable(tol=tol):
        return None
    if linkage.input_can_fully_rotate(tol=tol):
        return (0.0, 2.0 * pi)

    g = linkage.ground
    a = linkage.input
    connector_min, connector_max = linkage.connector_distance_bounds()
    # d^2 = g^2 + a^2 + 2 g a cos(theta)
    denom = 2.0 * g * a
    if abs(denom) <= tol:
        # Coincident or vanishing input: only theta that keeps tip assemblable.
        tip_dist = abs(g)  # tip coincides with ground_b distance from A ≈ g when a≈0 invalid
        if connector_min - tol <= tip_dist <= connector_max + tol:
            return (0.0, 2.0 * pi)
        return None

    def _cos_for_distance(distance: float) -> float:
        return (distance * distance - g * g - a * a) / denom

    # d increases with cos(theta) when g,a > 0, so admissible cosines lie in
    # [cos(connector_min), cos(connector_max)] intersected with [-1, 1].
    cos_min_req = _cos_for_distance(connector_min)
    cos_max_req = _cos_for_distance(connector_max)
    low = max(-1.0, min(cos_min_req, cos_max_req))
    high = min(1.0, max(cos_min_req, cos_max_req))
    if high < low - tol:
        return None
    low = max(-1.0, low)
    high = min(1.0, high)
    if high < low:
        return None

    # cos decreases on [0, pi]: cos in [low, high] ↔ theta in [theta_high, theta_low].
    theta_high = acos(max(-1.0, min(1.0, high)))
    theta_low = acos(max(-1.0, min(1.0, low)))
    if theta_low + tol >= theta_high:
        return (float(theta_high), float(theta_low))
    return None


def sample_admissible_input_angles(
    linkage: FourBar,
    count: int,
    *,
    branch: str = "open",
    tol: float = 1e-12,
) -> tuple[float, ...]:
    """Sample admissible designated-input angles that assemble on ``branch``."""

    if count < 2:
        raise ValueError("count must be at least 2")
    interval = admissible_input_angle_interval(linkage, tol=tol)
    if interval is None:
        return ()

    start, end = interval
    if linkage.input_can_fully_rotate(tol=tol):
        # Exclude the duplicate endpoint at 2π.
        return tuple(start + (end - start) * index / count for index in range(count))

    if end - start <= tol:
        mid = 0.5 * (start + end)
        pose = pose_at_input_angle(linkage, mid, branch=branch, tol=tol)
        return (mid,) if pose is not None else ()

    angles: list[float] = []
    for index in range(count):
        theta = start + (end - start) * index / (count - 1)
        if pose_at_input_angle(linkage, theta, branch=branch, tol=tol) is not None:
            angles.append(theta)
    # Also try the mirrored rocker interval on the lower half-plane if primary is sparse.
    if len(angles) < max(2, count // 4):
        mirror_start = -end
        mirror_end = -start
        for index in range(count):
            theta = mirror_start + (mirror_end - mirror_start) * index / (count - 1)
            # Wrap into (-pi, pi] then to [0, 2pi)
            wrapped = (theta + pi) % (2.0 * pi) - pi
            if wrapped < 0.0:
                wrapped += 2.0 * pi
            if pose_at_input_angle(linkage, wrapped, branch=branch, tol=tol) is not None:
                angles.append(wrapped)
        angles = sorted(set(angles))
        if len(angles) > count:
            step = max(1, len(angles) // count)
            angles = angles[::step][:count]
    return tuple(angles)


def sample_poses(
    linkage: FourBar,
    count: int,
    *,
    branch: str = "open",
    tol: float = 1e-12,
) -> tuple[FourBarPose, ...]:
    """Return assembled poses for admissible input samples."""

    poses: list[FourBarPose] = []
    for theta in sample_admissible_input_angles(linkage, count, branch=branch, tol=tol):
        pose = pose_at_input_angle(linkage, theta, branch=branch, tol=tol)
        if pose is not None:
            poses.append(pose)
    return tuple(poses)


def pose_polyline(pose: FourBarPose) -> tuple[Vec2, ...]:
    """Closed polyline for drawing the reduced loop."""

    return (
        pose.ground_a,
        pose.coupler_output_joint,
        pose.input_tip,
        pose.ground_b,
        pose.ground_a,
    )


def angle_span(angles: tuple[float, ...]) -> float:
    """Return the covered input-angle span in radians (0 if empty)."""

    if not angles:
        return 0.0
    return float(max(angles) - min(angles))


def is_finite_pose(pose: FourBarPose) -> bool:
    values = (
        pose.input_angle,
        *pose.ground_a,
        *pose.ground_b,
        *pose.input_tip,
        *pose.coupler_output_joint,
        pose.terminal_orientation,
    )
    return all(isfinite(value) for value in values)


def solve_planar_2r(
    target: Vec2,
    length_a: float,
    length_b: float,
    *,
    elbow_up: bool = True,
    tol: float = 1e-12,
) -> tuple[Vec2, Vec2] | None:
    """Return ``(elbow, target)`` for a 2R chain from the origin, or ``None``."""

    x, y = target
    dist = sqrt(x * x + y * y)
    if dist > length_a + length_b + tol or dist < abs(length_a - length_b) - tol:
        return None
    if dist <= tol:
        return None
    cos_elbow = (length_a * length_a + dist * dist - length_b * length_b) / (
        2.0 * length_a * dist
    )
    cos_elbow = max(-1.0, min(1.0, cos_elbow))
    base_angle = atan2(y, x)
    offset = acos(cos_elbow)
    q1 = base_angle + offset if elbow_up else base_angle - offset
    elbow = (length_a * cos(q1), length_a * sin(q1))
    return (elbow, target)
