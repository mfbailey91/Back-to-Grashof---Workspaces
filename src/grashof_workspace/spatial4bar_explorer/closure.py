from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .geometry import JointKind, SpatialFourBarGeometry

Array = np.ndarray


@dataclass(frozen=True)
class ScalarAxis:
    coordinate_index: int
    joint_index: int
    joint_name: str
    joint_kind: JointKind
    local_axis_index: int
    name: str
    origin: tuple[float, float, float]
    direction: tuple[float, float, float]


@dataclass(frozen=True)
class ClosureAudit:
    family: str
    coordinate_count: int
    closure_norm: float
    jacobian_rank: int
    jacobian_nullity: int
    singular_values: tuple[float, ...]
    smallest_nonzero_singular_value: float
    status: str


def scalar_axes(geometry: SpatialFourBarGeometry) -> tuple[ScalarAxis, ...]:
    """Expand R/U/S joints into seven ordered revolute coordinates.

    The expansion is a solver coordinate chart:
    R -> z, U -> x then y, S -> x then y then z.
    It does not assign a physical preferred axis to an S joint.
    """
    axes: list[ScalarAxis] = []
    index = 0
    for joint_index, joint in enumerate(geometry.joints):
        for local_axis_index, direction in enumerate(joint.motion_axes):
            if joint_index == geometry.tool_joint and joint.kind is JointKind.U:
                coordinate_name = "tool_alpha" if local_axis_index == 0 else "tool_beta"
            else:
                coordinate_name = f"{joint.name.lower()}_{joint.kind.value.lower()}{local_axis_index + 1}"
            axes.append(
                ScalarAxis(
                    coordinate_index=index,
                    joint_index=joint_index,
                    joint_name=joint.name,
                    joint_kind=joint.kind,
                    local_axis_index=local_axis_index,
                    name=coordinate_name,
                    origin=joint.center,
                    direction=direction,
                )
            )
            index += 1
    if len(axes) != 7:
        raise ValueError(f"expected seven scalar rotational coordinates, got {len(axes)}")
    return tuple(axes)


def _skew(vector: Array) -> Array:
    x, y, z = vector
    return np.array(((0.0, -z, y), (z, 0.0, -x), (-y, x, 0.0)), dtype=float)


def _rotation_about_axis(direction: Array, angle: float) -> Array:
    axis = direction / np.linalg.norm(direction)
    k = _skew(axis)
    return np.asarray(np.eye(3) + math.sin(angle) * k + (1.0 - math.cos(angle)) * (k @ k), dtype=float)


def revolute_transform(origin: tuple[float, float, float], direction: tuple[float, float, float], angle: float) -> Array:
    point = np.asarray(origin, dtype=float)
    axis = np.asarray(direction, dtype=float)
    rotation = _rotation_about_axis(axis, angle)
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = point - rotation @ point
    return transform


def closure_transform(geometry: SpatialFourBarGeometry, q: Array) -> Array:
    axes = scalar_axes(geometry)
    q_array = np.asarray(q, dtype=float)
    if q_array.shape != (len(axes),):
        raise ValueError(f"expected q shape ({len(axes)},), got {q_array.shape}")
    transform = np.eye(4)
    for axis, angle in zip(axes, q_array, strict=True):
        transform = transform @ revolute_transform(axis.origin, axis.direction, float(angle))
    return transform


def _so3_log(rotation: Array) -> Array:
    cosine = float(np.clip((np.trace(rotation) - 1.0) / 2.0, -1.0, 1.0))
    angle = math.acos(cosine)
    vee = np.array(
        (
            rotation[2, 1] - rotation[1, 2],
            rotation[0, 2] - rotation[2, 0],
            rotation[1, 0] - rotation[0, 1],
        ),
        dtype=float,
    )
    if angle < 1e-9:
        return 0.5 * vee
    sine = math.sin(angle)
    if abs(sine) < 1e-8:
        # This branch is not expected during local V03 correction, but the
        # eigenvector fallback keeps the residual finite near pi.
        values, vectors = np.linalg.eig(rotation)
        index = int(np.argmin(np.abs(values - 1.0)))
        axis = np.real(vectors[:, index])
        axis /= np.linalg.norm(axis)
        return angle * axis
    return angle * vee / (2.0 * sine)


def closure_residual(geometry: SpatialFourBarGeometry, q: Array) -> Array:
    transform = closure_transform(geometry, q)
    translation = transform[:3, 3]
    rotation_vector = _so3_log(transform[:3, :3])
    return np.concatenate((translation, rotation_vector))


def closure_jacobian(geometry: SpatialFourBarGeometry, q: Array, *, step: float = 1e-7) -> Array:
    q_array = np.asarray(q, dtype=float)
    jacobian = np.zeros((6, q_array.size), dtype=float)
    for index in range(q_array.size):
        plus = q_array.copy()
        minus = q_array.copy()
        plus[index] += step
        minus[index] -= step
        jacobian[:, index] = (
            closure_residual(geometry, plus) - closure_residual(geometry, minus)
        ) / (2.0 * step)
    return jacobian


def null_tangent(jacobian: Array, *, previous: Array | None = None) -> tuple[Array, Array]:
    _, singular_values, vh = np.linalg.svd(jacobian, full_matrices=True)
    tangent = vh[-1, :]
    tangent /= np.linalg.norm(tangent)
    if previous is not None and float(np.dot(tangent, previous)) < 0.0:
        tangent = -tangent
    return tangent, singular_values


def audit_reference_geometry(geometry: SpatialFourBarGeometry, *, rank_tol: float = 1e-7) -> ClosureAudit:
    q0 = np.zeros(len(scalar_axes(geometry)))
    residual = closure_residual(geometry, q0)
    jacobian = closure_jacobian(geometry, q0)
    singular_values = np.linalg.svd(jacobian, compute_uv=False)
    rank = int(np.sum(singular_values > rank_tol))
    nullity = int(jacobian.shape[1] - rank)
    smallest_nonzero = float(singular_values[rank - 1]) if rank else 0.0
    status = "PASS" if np.linalg.norm(residual) < 1e-9 and rank == 6 and nullity == 1 else "REVIEW"
    return ClosureAudit(
        family=geometry.family.value,
        coordinate_count=q0.size,
        closure_norm=float(np.linalg.norm(residual)),
        jacobian_rank=rank,
        jacobian_nullity=nullity,
        singular_values=tuple(float(value) for value in singular_values),
        smallest_nonzero_singular_value=smallest_nonzero,
        status=status,
    )


def transform_point(transform: Array, point: tuple[float, float, float]) -> Array:
    homogeneous = np.array((*point, 1.0), dtype=float)
    return np.asarray((transform @ homogeneous)[:3], dtype=float)


def transform_direction(transform: Array, direction: tuple[float, float, float]) -> Array:
    return np.asarray(transform[:3, :3] @ np.asarray(direction, dtype=float), dtype=float)


def mechanism_state(geometry: SpatialFourBarGeometry, q: Array) -> tuple[Array, tuple[tuple[Array, Array, str], ...]]:
    """Return moving joint-center positions and current scalar-axis lines.

    J1 and J4 lie on the fixed ground link. The moving-chain center positions
    are evaluated immediately before each topological joint motion. The axis
    list includes internal U/S chart axes at their current orientations.
    """
    q_array = np.asarray(q, dtype=float)
    axes = scalar_axes(geometry)
    current = np.eye(4)
    centers = np.zeros((4, 3), dtype=float)
    axis_lines: list[tuple[Array, Array, str]] = []
    axis_cursor = 0
    for joint_index, joint in enumerate(geometry.joints):
        if joint_index == 0:
            centers[joint_index] = np.asarray(joint.center, dtype=float)
        else:
            centers[joint_index] = transform_point(current, joint.center)
        local_current = current.copy()
        for _ in joint.motion_axes:
            axis = axes[axis_cursor]
            origin = transform_point(local_current, axis.origin)
            direction = transform_direction(local_current, axis.direction)
            direction /= np.linalg.norm(direction)
            axis_lines.append((origin, direction, axis.name))
            local_current = local_current @ revolute_transform(axis.origin, axis.direction, float(q_array[axis_cursor]))
            axis_cursor += 1
        current = local_current
    # Both endpoints of L41 are fixed by ground; report exact ground positions.
    centers[0] = np.asarray(geometry.joints[0].center, dtype=float)
    centers[3] = np.asarray(geometry.joints[3].center, dtype=float)
    return centers, tuple(axis_lines)
