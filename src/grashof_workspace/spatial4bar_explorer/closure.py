from __future__ import annotations

"""SE(3) loop-closure residual for one-DOF spatial four-bars.

Conventions (must match V02B geometry objects):
- Joint order around the loop: J1,J2,J3,J4 indexed 0..3.
- Tool joint index is always 0 and is a `U` joint.
- Ground link is link index 3 connecting joints 3 and 0.
- Motion axes: `R` uses frame z; `U` uses frame x then y; `S` uses x,y,z.
- Joint angles are relative to the stored reference assembly (q=0).
- UUUR packing of `joint_angles`:
  [u0_alpha, u0_beta, u1_alpha, u1_beta, u2_alpha, u2_beta, r3_theta]
- Loop product: Exp0 A01 Exp1 A12 Exp2 A23 Exp3 A30 = I at assembly,
  where Aij are fixed link transforms taken from the reference pose.

Only `OrderedFamily.UUUR` is verified in Sprint V03. Other families raise.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares

from .geometry import JointKind, SpatialFourBarGeometry
from .models import OrderedFamily

Array = NDArray[np.float64]

UUUR_DOF = 7
CLOSURE_DIM = 6
SINGULAR_SIGMA_TOL = 1e-4


@dataclass(frozen=True)
class ClosureProblem:
    geometry: SpatialFourBarGeometry
    link_transforms: tuple[Array, Array, Array, Array]
    joint_axis_counts: tuple[int, int, int, int]

    @property
    def n_dof(self) -> int:
        return sum(self.joint_axis_counts)


def _as_vec(value: tuple[float, float, float]) -> Array:
    return np.asarray(value, dtype=float)


def pose_from_frame(center: tuple[float, float, float], frame: tuple[tuple[float, float, float], ...]) -> Array:
    """Build a 4x4 pose whose columns are the joint frame axes."""
    pose = np.eye(4, dtype=float)
    pose[:3, 0] = _as_vec(frame[0])
    pose[:3, 1] = _as_vec(frame[1])
    pose[:3, 2] = _as_vec(frame[2])
    pose[:3, 3] = _as_vec(center)
    return pose


def invert_pose(pose: Array) -> Array:
    rotation = pose[:3, :3]
    translation = pose[:3, 3]
    inverse = np.eye(4, dtype=float)
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -rotation.T @ translation
    return inverse


def axis_angle_rotation(axis: Array, angle: float) -> Array:
    unit = axis / np.linalg.norm(axis)
    x, y, z = unit
    c = np.cos(angle)
    s = np.sin(angle)
    c1 = 1.0 - c
    return np.array(
        [
            [c + x * x * c1, x * y * c1 - z * s, x * z * c1 + y * s],
            [y * x * c1 + z * s, c + y * y * c1, y * z * c1 - x * s],
            [z * x * c1 - y * s, z * y * c1 + x * s, c + z * z * c1],
        ],
        dtype=float,
    )


def joint_exponential(geometry: SpatialFourBarGeometry, joint_index: int, angles: Array) -> Array:
    """Body-fixed joint motion relative to the reference assembly.

    Axes are the local joint-frame basis, not world directions:
    - R: local z
    - U: local x then local y
    - S: local x, y, z
    """
    joint = geometry.joints[joint_index]
    transform = np.eye(4, dtype=float)
    if joint.kind is JointKind.R:
        local_axes = (np.array([0.0, 0.0, 1.0]),)
    elif joint.kind is JointKind.U:
        local_axes = (np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
    else:
        local_axes = (
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
        )
    if len(angles) != len(local_axes):
        raise ValueError(f"joint {joint_index} expected {len(local_axes)} angles, got {len(angles)}")
    for axis, angle in zip(local_axes, angles, strict=True):
        rotation = axis_angle_rotation(axis, float(angle))
        local = np.eye(4, dtype=float)
        local[:3, :3] = rotation
        transform = transform @ local
    return transform


def rotation_log(rotation: Array) -> Array:
    """Principal so(3) logarithm as a 3-vector (axis * angle)."""
    trace = np.clip((np.trace(rotation) - 1.0) / 2.0, -1.0, 1.0)
    angle = float(np.arccos(trace))
    if angle < 1e-12:
        return np.zeros(3, dtype=float)
    if abs(angle - np.pi) < 1e-8:
        # Near-π: use eigenvector of R corresponding to +1 as axis.
        vals, vecs = np.linalg.eig(rotation)
        axis = np.real(vecs[:, np.argmin(np.abs(vals - 1.0))])
        axis = axis / np.linalg.norm(axis)
        return axis * angle
    skew = (rotation - rotation.T) * (angle / (2.0 * np.sin(angle)))
    return np.array([skew[2, 1], skew[0, 2], skew[1, 0]], dtype=float)


def se3_log(pose: Array) -> Array:
    """Map SE(3) pose to a 6-vector (translation residual, rotation log)."""
    return np.concatenate([pose[:3, 3], rotation_log(pose[:3, :3])])


def build_uuur_closure_problem(geometry: SpatialFourBarGeometry) -> ClosureProblem:
    if geometry.family is not OrderedFamily.UUUR:
        raise NotImplementedError(
            "Sprint V03 verifies UUUR only; other families are unverified for closure."
        )
    kinds = tuple(joint.kind for joint in geometry.joints)
    if kinds != (JointKind.U, JointKind.U, JointKind.U, JointKind.R):
        raise ValueError(f"UUUR expected joint kinds U,U,U,R; got {kinds}")

    poses = tuple(
        pose_from_frame(joint.center, joint.frame) for joint in geometry.joints
    )
    link_transforms = (
        invert_pose(poses[0]) @ poses[1],
        invert_pose(poses[1]) @ poses[2],
        invert_pose(poses[2]) @ poses[3],
        invert_pose(poses[3]) @ poses[0],
    )
    axis_counts = tuple(len(joint.motion_axes) for joint in geometry.joints)
    if sum(axis_counts) != UUUR_DOF:
        raise ValueError(f"UUUR must have {UUUR_DOF} DOF, got {sum(axis_counts)}")
    return ClosureProblem(
        geometry=geometry,
        link_transforms=link_transforms,
        joint_axis_counts=axis_counts,  # type: ignore[arg-type]
    )


def split_uuur_angles(angles: Array) -> tuple[Array, Array, Array, Array]:
    if len(angles) != UUUR_DOF:
        raise ValueError(f"UUUR angles must have length {UUUR_DOF}")
    return angles[0:2], angles[2:4], angles[4:6], angles[6:7]


def loop_pose(problem: ClosureProblem, angles: Array) -> Array:
    q0, q1, q2, q3 = split_uuur_angles(angles)
    a01, a12, a23, a30 = problem.link_transforms
    return (
        joint_exponential(problem.geometry, 0, q0)
        @ a01
        @ joint_exponential(problem.geometry, 1, q1)
        @ a12
        @ joint_exponential(problem.geometry, 2, q2)
        @ a23
        @ joint_exponential(problem.geometry, 3, q3)
        @ a30
    )


def closure_residual(problem: ClosureProblem, angles: Array) -> Array:
    """Named 6D SE(3) loop-closure residual for UUUR."""
    return se3_log(loop_pose(problem, np.asarray(angles, dtype=float)))


def residual_norm(problem: ClosureProblem, angles: Array) -> float:
    return float(np.linalg.norm(closure_residual(problem, angles)))


def numerical_jacobian(
    problem: ClosureProblem,
    angles: Array,
    *,
    free_index: int | None = None,
    eps: float = 1e-7,
) -> Array:
    base = np.asarray(angles, dtype=float)
    residual0 = closure_residual(problem, base)
    indices = [i for i in range(len(base)) if i != free_index]
    jac = np.zeros((CLOSURE_DIM, len(indices)), dtype=float)
    for col, index in enumerate(indices):
        stepped = base.copy()
        stepped[index] += eps
        jac[:, col] = (closure_residual(problem, stepped) - residual0) / eps
    return jac


def smallest_singular_value(
    problem: ClosureProblem,
    angles: Array,
    *,
    free_index: int,
) -> float:
    jac = numerical_jacobian(problem, angles, free_index=free_index)
    if jac.size == 0:
        return 0.0
    singular_values = np.linalg.svd(jac, compute_uv=False)
    return float(singular_values[-1])


def is_near_singular(
    problem: ClosureProblem,
    angles: Array,
    *,
    free_index: int,
    tol: float = SINGULAR_SIGMA_TOL,
) -> bool:
    return smallest_singular_value(problem, angles, free_index=free_index) < tol


@dataclass(frozen=True)
class SeedSolveResult:
    success: bool
    angles: Array
    residual_norm: float
    message: str


def solve_seed_assembly(
    problem: ClosureProblem,
    *,
    initial: Array | None = None,
    max_nfev: int = 80,
) -> SeedSolveResult:
    """Local corrector for a UUUR seed.

    The V02B reference pose corresponds to the zero angle vector and is an
    exact assembly up to numerical roundoff. Nearby initial guesses are refined
    with a bounded least-squares corrector.
    """
    x0 = np.zeros(problem.n_dof, dtype=float) if initial is None else np.asarray(initial, dtype=float)

    def objective(angles: Array) -> Array:
        return closure_residual(problem, angles)

    # Underdetermined (6 residuals, 7 DOF): prefer TRF over LM.
    if float(np.linalg.norm(objective(x0))) < 1e-12:
        return SeedSolveResult(
            success=True,
            angles=x0.copy(),
            residual_norm=float(np.linalg.norm(objective(x0))),
            message="reference assembly accepted without correction",
        )

    result = least_squares(objective, x0, method="trf", ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=max_nfev)
    angles = np.asarray(result.x, dtype=float)
    norm = float(np.linalg.norm(result.fun))
    success = bool(result.success) and norm < 1e-8
    return SeedSolveResult(
        success=success,
        angles=angles,
        residual_norm=norm,
        message=str(result.message),
    )


def corrupt_link_transform(problem: ClosureProblem, *, scale: float = 0.35) -> ClosureProblem:
    """Exterior helper: break one fixed link transform so the reference pose fails."""
    broken = [matrix.copy() for matrix in problem.link_transforms]
    broken[1][:3, 3] = broken[1][:3, 3] + np.array([scale, -scale, scale], dtype=float)
    # Also twist the relative orientation so the zero-angle pose is far from assembly.
    twist = axis_angle_rotation(np.array([0.0, 0.0, 1.0]), 0.9)
    rot = np.eye(4, dtype=float)
    rot[:3, :3] = twist
    broken[1] = broken[1] @ rot
    return ClosureProblem(
        geometry=problem.geometry,
        link_transforms=(broken[0], broken[1], broken[2], broken[3]),
        joint_axis_counts=problem.joint_axis_counts,
    )
