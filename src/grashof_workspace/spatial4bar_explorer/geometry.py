from __future__ import annotations

import math
import random
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from .models import GeometryDescriptor, OrderedFamily

Vec3 = tuple[float, float, float]
Frame3 = tuple[Vec3, Vec3, Vec3]


class JointKind(str, Enum):
    R = "R"
    U = "U"
    S = "S"


@dataclass(frozen=True)
class JointGeometry:
    """Joint center plus an orthonormal reference frame at one assembled pose.

    Motion-axis convention:
    - R: frame z-axis
    - U: frame x- then y-axis
    - S: frame x-, y-, z-axis

    The frame is stored even for R joints so Sprint V03 can derive fixed
    inter-joint link transforms from the same reference assembly.
    """

    name: str
    kind: JointKind
    center: Vec3
    frame: Frame3

    @property
    def motion_axes(self) -> tuple[Vec3, ...]:
        x_axis, y_axis, z_axis = self.frame
        if self.kind is JointKind.R:
            return (z_axis,)
        if self.kind is JointKind.U:
            return (x_axis, y_axis)
        return (x_axis, y_axis, z_axis)

    @property
    def primary_axis(self) -> Vec3:
        return self.motion_axes[0]


@dataclass(frozen=True)
class LinkGeometry:
    name: str
    joint_a: int
    joint_b: int


@dataclass(frozen=True)
class SpatialFourBarGeometry:
    family: OrderedFamily
    joints: tuple[JointGeometry, JointGeometry, JointGeometry, JointGeometry]
    links: tuple[LinkGeometry, LinkGeometry, LinkGeometry, LinkGeometry]
    ground_link: int = 3
    tool_joint: int = 0

    @property
    def reference_length(self) -> float:
        lengths = [
            distance(self.joints[link.joint_a].center, self.joints[link.joint_b].center)
            for link in self.links
        ]
        return sum(lengths) / len(lengths)

    def validation_errors(self, tol: float = 1e-9) -> list[str]:
        errors: list[str] = []
        expected = tuple(JointKind(letter) for letter in self.family.value)
        actual = tuple(joint.kind for joint in self.joints)
        if actual != expected:
            errors.append(f"family/joint mismatch: expected {expected}, got {actual}")
        if self.joints[self.tool_joint].kind is not JointKind.U:
            errors.append("tool joint must be U")
        if len(self.links) != 4:
            errors.append("four-bar must contain four links")
        if self.reference_length <= tol:
            errors.append("reference length must be positive")

        expected_edges = {(0, 1), (1, 2), (2, 3), (0, 3)}
        actual_edges = {
            tuple(sorted((link.joint_a, link.joint_b)))
            for link in self.links
        }
        if actual_edges != expected_edges:
            errors.append(f"links do not form the expected 4-cycle: {actual_edges}")

        for joint in self.joints:
            frame = joint.frame
            for axis_index, axis in enumerate(frame):
                if abs(norm(axis) - 1.0) > 1e-7:
                    errors.append(f"{joint.name} frame axis {axis_index} is not unit")
            for i in range(3):
                for j in range(i + 1, 3):
                    if abs(dot(frame[i], frame[j])) > 1e-7:
                        errors.append(f"{joint.name} frame axes {i}/{j} are not orthogonal")
            if joint.kind is JointKind.U and abs(dot(*joint.motion_axes)) > 1e-7:
                errors.append(f"{joint.name} U axes are not perpendicular")

        for link in self.links:
            if distance(self.joints[link.joint_a].center, self.joints[link.joint_b].center) <= tol:
                errors.append(f"{link.name} has coincident joint centers")
        return errors

    @property
    def is_valid_reference_geometry(self) -> bool:
        return not self.validation_errors()


@dataclass(frozen=True)
class PhysicalGeometrySample:
    sample_id: str
    family: OrderedFamily
    inversion: str
    seed: int
    geometry: SpatialFourBarGeometry
    descriptors: tuple[GeometryDescriptor, ...]
    provenance: str = "physical_geometry_v02b"

    def descriptor_map(self) -> dict[str, float | int | str | bool]:
        return {descriptor.name: descriptor.value for descriptor in self.descriptors}


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def subtract(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: Vec3) -> float:
    return math.sqrt(dot(a, a))


def normalize(a: Vec3) -> Vec3:
    length = norm(a)
    if length <= 1e-15:
        raise ValueError("cannot normalize zero vector")
    return scale(a, 1.0 / length)


def distance(a: Vec3, b: Vec3) -> float:
    return norm(subtract(a, b))


def angle_deg(a: Vec3, b: Vec3) -> float:
    cosine = max(-1.0, min(1.0, dot(normalize(a), normalize(b))))
    return math.degrees(math.acos(cosine))


def point_to_axis_distance(point: Vec3, axis_origin: Vec3, axis_direction: Vec3) -> float:
    unit = normalize(axis_direction)
    delta = subtract(point, axis_origin)
    rejection = subtract(delta, scale(unit, dot(delta, unit)))
    return norm(rejection)


def line_to_line_distance(
    origin_a: Vec3,
    direction_a: Vec3,
    origin_b: Vec3,
    direction_b: Vec3,
) -> float:
    a = normalize(direction_a)
    b = normalize(direction_b)
    normal = cross(a, b)
    normal_norm = norm(normal)
    delta = subtract(origin_b, origin_a)
    if normal_norm < 1e-12:
        return norm(cross(delta, a))
    return abs(dot(delta, normalize(normal)))


def signed_tetrahedral_volume(a: Vec3, b: Vec3, c: Vec3, d: Vec3) -> float:
    return dot(subtract(b, a), cross(subtract(c, a), subtract(d, a))) / 6.0


def rotation_matrix_xyz(rx: float, ry: float, rz: float) -> tuple[Vec3, Vec3, Vec3]:
    """Return row-major Rz @ Ry @ Rx for radian rotations."""
    sx, cx = math.sin(rx), math.cos(rx)
    sy, cy = math.sin(ry), math.cos(ry)
    sz, cz = math.sin(rz), math.cos(rz)
    return (
        (cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx),
        (sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx),
        (-sy, cy * sx, cy * cx),
    )


def mat_vec(matrix: tuple[Vec3, Vec3, Vec3], vector: Vec3) -> Vec3:
    return (
        dot(matrix[0], vector),
        dot(matrix[1], vector),
        dot(matrix[2], vector),
    )


def rotate_frame(frame: Frame3, rx: float, ry: float, rz: float) -> Frame3:
    rotation = rotation_matrix_xyz(rx, ry, rz)
    return tuple(normalize(mat_vec(rotation, axis)) for axis in frame)  # type: ignore[return-value]


def frame_from_euler_deg(rx: float, ry: float, rz: float) -> Frame3:
    radians = tuple(math.radians(value) for value in (rx, ry, rz))
    rotation = rotation_matrix_xyz(*radians)
    # Matrix columns are the rotated local basis vectors expressed in world.
    return (
        normalize((rotation[0][0], rotation[1][0], rotation[2][0])),
        normalize((rotation[0][1], rotation[1][1], rotation[2][1])),
        normalize((rotation[0][2], rotation[1][2], rotation[2][2])),
    )


def canonical_geometry(family: OrderedFamily) -> SpatialFourBarGeometry:
    """Create one exact reference assembly for an ordered spatial four-bar family.

    The reference assembly is intentionally generic and asymmetric. Compound
    joints are represented by exactly intersecting orthogonal axes at a common
    center. No crank/mobility claim is made here; V03 will solve closure.
    """
    family_bias = sum(ord(character) for character in family.value) % 19
    centers: tuple[Vec3, Vec3, Vec3, Vec3] = (
        (0.0, 0.0, 0.0),
        (1.35, 0.18, 0.24),
        (1.92, 1.12, 0.61),
        (0.28, 1.41, -0.17),
    )
    base_eulers = (
        (8.0, -12.0, 15.0),
        (31.0, 18.0, -22.0),
        (-27.0, 37.0, 29.0),
        (43.0, -16.0, 52.0),
    )
    kinds = tuple(JointKind(letter) for letter in family.value)
    joints: list[JointGeometry] = []
    for index, (kind, center, angles) in enumerate(zip(kinds, centers, base_eulers, strict=True)):
        bias = (family_bias - 9) * (index + 1) * 0.35
        frame = frame_from_euler_deg(angles[0] + bias, angles[1] - 0.4 * bias, angles[2] + 0.2 * bias)
        joints.append(JointGeometry(name=f"J{index + 1}", kind=kind, center=center, frame=frame))
    links = (
        LinkGeometry("L12", 0, 1),
        LinkGeometry("L23", 1, 2),
        LinkGeometry("L34", 2, 3),
        LinkGeometry("L41_ground", 3, 0),
    )
    geometry = SpatialFourBarGeometry(family=family, joints=tuple(joints), links=links)  # type: ignore[arg-type]
    errors = geometry.validation_errors()
    if errors:
        raise ValueError(f"invalid canonical geometry for {family.value}: {errors}")
    return geometry


def perturb_geometry(
    geometry: SpatialFourBarGeometry,
    *,
    seed: int,
    center_scale: float = 0.12,
    angle_scale_deg: float = 9.0,
) -> SpatialFourBarGeometry:
    """Perturb centers and complete joint frames while preserving joint topology.

    J1 remains at the origin to remove irrelevant global translation. Because
    whole orthonormal frames are rotated, U and S internal axis constraints are
    preserved exactly.
    """
    rng = random.Random(seed)
    joints: list[JointGeometry] = []
    for index, joint in enumerate(geometry.joints):
        if index == 0:
            center = joint.center
        else:
            center = add(
                joint.center,
                (
                    rng.uniform(-center_scale, center_scale),
                    rng.uniform(-center_scale, center_scale),
                    rng.uniform(-center_scale, center_scale),
                ),
            )
        angle_scale = math.radians(angle_scale_deg)
        frame = rotate_frame(
            joint.frame,
            rng.uniform(-angle_scale, angle_scale),
            rng.uniform(-angle_scale, angle_scale),
            rng.uniform(-angle_scale, angle_scale),
        )
        joints.append(JointGeometry(joint.name, joint.kind, center, frame))
    perturbed = SpatialFourBarGeometry(
        family=geometry.family,
        joints=tuple(joints),  # type: ignore[arg-type]
        links=geometry.links,
        ground_link=geometry.ground_link,
        tool_joint=geometry.tool_joint,
    )
    errors = perturbed.validation_errors()
    if errors:
        raise ValueError(f"perturbation produced invalid reference geometry: {errors}")
    return perturbed


def stable_family_seed(family: OrderedFamily) -> int:
    return sum((index + 1) * ord(character) for index, character in enumerate(family.value))


def iter_joint_motion_axes(geometry: SpatialFourBarGeometry) -> Iterable[tuple[JointGeometry, int, Vec3]]:
    for joint in geometry.joints:
        for axis_index, axis in enumerate(joint.motion_axes):
            yield joint, axis_index, axis
