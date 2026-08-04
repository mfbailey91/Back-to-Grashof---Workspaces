"""Multi-start numerical inverse kinematics for synthetic 6R arms."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np
from scipy.optimize import least_squares

from sixr_grashof.kinematics.axes import Vec3
from sixr_grashof.kinematics.forward import ForwardKinematicsResult
from sixr_grashof.sampling.orientations import geodesic_angle, rotation_from_mat4

IkStatus = Literal["solved", "unreachable", "solver_failed"]
JointConfig = tuple[float, float, float, float, float, float]


class _Params(Protocol):
    L2: float
    L3: float
    Lt: float


class ForwardArm(Protocol):
    params: _Params

    def forward(self, q: JointConfig) -> ForwardKinematicsResult: ...


@dataclass(frozen=True, slots=True)
class IkSolution:
    """One IK attempt result."""

    status: IkStatus
    configuration: JointConfig | None
    position_error: float
    orientation_error: float
    residual_norm: float
    branch_id: int
    singularity_flag: bool
    notes: str = ""


def _as_q(x: np.ndarray) -> JointConfig:
    return (float(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5]))


def pose_residual(
    arm: ForwardArm,
    q: np.ndarray,
    target_p: Vec3,
    target_R: np.ndarray,
    *,
    position_weight: float = 1.0,
    orientation_weight: float = 1.0,
) -> np.ndarray:
    """6-vector residual: 3 position + 3 orientation (skew of R_err)."""
    fk = arm.forward(_as_q(q))
    p = fk.tool_position
    R = rotation_from_mat4(fk.tool_transform)
    dp = np.array(
        [
            position_weight * (p[0] - target_p[0]),
            position_weight * (p[1] - target_p[1]),
            position_weight * (p[2] - target_p[2]),
        ]
    )
    Re = R.T @ target_R
    # vee(skew-symmetric part)
    ori = orientation_weight * np.array(
        [Re[2, 1] - Re[1, 2], Re[0, 2] - Re[2, 0], Re[1, 0] - Re[0, 1]]
    )
    return np.concatenate([dp, 0.5 * ori])


def wrist_center_from_pose(target_p: Vec3, target_R: np.ndarray, Lt: float) -> Vec3:
    """Architecture A/B tool is offset ``Lt`` along tool z (column 2 of R)."""
    a6 = (float(target_R[0, 2]), float(target_R[1, 2]), float(target_R[2, 2]))
    return (
        target_p[0] - Lt * a6[0],
        target_p[1] - Lt * a6[1],
        target_p[2] - Lt * a6[2],
    )


def regional_reachable_wrist(
    cw: Vec3,
    *,
    L2: float,
    L3: float,
    tol: float = 1e-6,
) -> bool:
    """True if wrist-center distance from origin lies in [|L2-L3|, L2+L3]."""
    rho = math.sqrt(cw[0] ** 2 + cw[1] ** 2 + cw[2] ** 2)
    lo = abs(L2 - L3) - tol
    hi = L2 + L3 + tol
    return lo <= rho <= hi


def is_wrist_singularity(q: JointConfig, *, tol: float = 1e-3) -> bool:
    """Spherical-wrist singularity when |sin(q5)| is small."""
    return abs(math.sin(q[4])) < tol


def analytical_seed_architecture_a(
    target_p: Vec3,
    target_R: np.ndarray,
    *,
    L2: float,
    L3: float,
    Lt: float,
) -> JointConfig | None:
    """Construct a planar+wrist seed for Architecture A when regionally feasible."""
    cw = wrist_center_from_pose(target_p, target_R, Lt)
    if not regional_reachable_wrist(cw, L2=L2, L3=L3):
        return None
    x, y, z = cw
    q1 = math.atan2(y, x)
    c1, s1 = math.cos(q1), math.sin(q1)
    x_p = c1 * x + s1 * y
    rho_xz = math.hypot(x_p, z)
    if rho_xz < 1e-12:
        return None
    # FK: Cw = Ry(q2) * (L2 + L3 cos q3, 0, -L3 sin q3)
    cos_el = (rho_xz * rho_xz - L2 * L2 - L3 * L3) / (2.0 * L2 * L3)
    cos_el = max(-1.0, min(1.0, cos_el))
    q3 = math.acos(cos_el)
    ax = L2 + L3 * math.cos(q3)
    az = -L3 * math.sin(q3)
    den = ax * ax + az * az
    if den < 1e-12:
        return None
    c2 = (ax * x_p + az * z) / den
    s2 = (az * x_p - ax * z) / den
    q2 = math.atan2(s2, c2)
    return (q1, q2, q3, 0.0, 0.0, 0.0)


def multi_start_seeds(
    base: JointConfig,
    *,
    n_extra: int = 7,
    seed: int = 0,
    analytical: JointConfig | None = None,
) -> list[np.ndarray]:
    """Base seed plus deterministic perturbations."""
    rng = np.random.default_rng(seed)
    seeds = [np.array(base, dtype=float)]
    if analytical is not None:
        seeds.append(np.array(analytical, dtype=float))
    for _ in range(n_extra):
        delta = rng.uniform(-math.pi, math.pi, size=6)
        seeds.append(np.array(base, dtype=float) + 0.35 * delta)
    q = np.array(base, dtype=float)
    for dq5 in (math.pi / 2, -math.pi / 2, math.pi):
        qq = q.copy()
        qq[4] = dq5
        seeds.append(qq)
    return seeds


def solve_ik(
    arm: ForwardArm,
    target_p: Vec3,
    target_R: np.ndarray,
    *,
    seed: JointConfig = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    n_starts: int = 8,
    rng_seed: int = 0,
    pos_tol: float = 1e-4,
    ori_tol: float = 1e-3,
    geometric_precheck: bool = True,
) -> IkSolution:
    """Multi-start least-squares IK with geometric precheck when applicable."""
    params = arm.params
    analytical: JointConfig | None = None
    if geometric_precheck:
        cw = wrist_center_from_pose(target_p, target_R, params.Lt)
        if not regional_reachable_wrist(cw, L2=params.L2, L3=params.L3):
            return IkSolution(
                status="unreachable",
                configuration=None,
                position_error=float("inf"),
                orientation_error=float("inf"),
                residual_norm=float("inf"),
                branch_id=-1,
                singularity_flag=False,
                notes="wrist center outside regional annulus",
            )
        analytical = analytical_seed_architecture_a(
            target_p, target_R, L2=params.L2, L3=params.L3, Lt=params.Lt
        )

    starts = multi_start_seeds(
        seed, n_extra=max(0, n_starts - 1), seed=rng_seed, analytical=analytical
    )
    best: IkSolution | None = None
    for branch_id, x0 in enumerate(starts):

        def fun(x: np.ndarray, _arm: ForwardArm = arm) -> np.ndarray:
            return pose_residual(_arm, x, target_p, target_R)

        try:
            res = least_squares(fun, x0, method="lm", max_nfev=200)
        except Exception as exc:  # noqa: BLE001 — solver robustness
            candidate = IkSolution(
                status="solver_failed",
                configuration=None,
                position_error=float("inf"),
                orientation_error=float("inf"),
                residual_norm=float("inf"),
                branch_id=branch_id,
                singularity_flag=False,
                notes=f"optimizer exception: {exc}",
            )
            if best is None:
                best = candidate
            continue

        q = _as_q(res.x)
        fk = arm.forward(q)
        p = fk.tool_position
        R = rotation_from_mat4(fk.tool_transform)
        perr = math.sqrt(
            (p[0] - target_p[0]) ** 2
            + (p[1] - target_p[1]) ** 2
            + (p[2] - target_p[2]) ** 2
        )
        oerr = geodesic_angle(R, target_R)
        rnorm = float(np.linalg.norm(res.fun))
        ok = perr <= pos_tol and oerr <= ori_tol
        candidate = IkSolution(
            status="solved" if ok else "solver_failed",
            configuration=q if ok else None,
            position_error=perr,
            orientation_error=oerr,
            residual_norm=rnorm,
            branch_id=branch_id,
            singularity_flag=is_wrist_singularity(q) if ok else False,
            notes="converged" if ok else "residual above tolerance",
        )
        if best is None or (
            (candidate.status == "solved" and best.status != "solved")
            or (
                candidate.status == best.status
                and candidate.residual_norm < best.residual_norm
            )
        ):
            best = candidate
        if candidate.status == "solved":
            return candidate

    assert best is not None
    return best


def discover_branches(
    arm: ForwardArm,
    target_p: Vec3,
    target_R: np.ndarray,
    *,
    seed: JointConfig = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    n_starts: int = 12,
    rng_seed: int = 0,
    cluster_tol: float = 0.15,
) -> list[IkSolution]:
    """Return distinct solved branches (joint-space clustered)."""
    starts = multi_start_seeds(seed, n_extra=max(0, n_starts - 1), seed=rng_seed)
    solved: list[IkSolution] = []
    for branch_id, x0 in enumerate(starts):
        sol = solve_ik(
            arm,
            target_p,
            target_R,
            seed=_as_q(x0),
            n_starts=1,
            rng_seed=rng_seed + branch_id,
            geometric_precheck=(branch_id == 0),
        )
        if sol.status != "solved" or sol.configuration is None:
            continue
        q = np.array(sol.configuration)
        duplicate = False
        for prev in solved:
            assert prev.configuration is not None
            d = np.linalg.norm(
                np.arctan2(
                    np.sin(q - np.array(prev.configuration)),
                    np.cos(q - np.array(prev.configuration)),
                )
            )
            if d < cluster_tol:
                duplicate = True
                break
        if not duplicate:
            solved.append(
                IkSolution(
                    status="solved",
                    configuration=sol.configuration,
                    position_error=sol.position_error,
                    orientation_error=sol.orientation_error,
                    residual_norm=sol.residual_norm,
                    branch_id=len(solved),
                    singularity_flag=sol.singularity_flag,
                    notes=sol.notes,
                )
            )
    return solved
