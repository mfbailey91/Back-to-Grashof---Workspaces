"""Representative workspace / Cartesian position samples (Sprint 4–5)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from sixr_grashof.architectures import ArchitectureA, ArchitectureParams
from sixr_grashof.kinematics.axes import Vec3


@dataclass(frozen=True, slots=True)
class WorkspaceSample:
    """One fixed Cartesian tool position with a joint seed that reaches it."""

    position: Vec3
    joint_seed: tuple[float, float, float, float, float, float]
    label: str
    rho_w: float


def architecture_a_position_from_q(
    q: tuple[float, float, float, float, float, float],
    *,
    params: ArchitectureParams | None = None,
) -> WorkspaceSample:
    arch = ArchitectureA(params)
    fk = arch.forward(q)
    cw = fk.joints[3].origin
    rho = math.sqrt(cw[0] ** 2 + cw[1] ** 2 + cw[2] ** 2)
    return WorkspaceSample(
        position=fk.tool_position,
        joint_seed=q,
        label=f"q=({','.join(f'{v:.3f}' for v in q)})",
        rho_w=rho,
    )


def architecture_a_workspace_samples(
    *,
    params: ArchitectureParams | None = None,
) -> list[WorkspaceSample]:
    """Small deterministic set of reachable Architecture A tool positions."""
    seeds = [
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (0.0, 0.25, -0.35, 0.0, 0.2, 0.0),
        (0.4, -0.2, 0.3, 0.1, -0.15, 0.05),
        (math.pi / 5, 0.35, -0.25, -0.2, 0.3, -0.1),
        (-0.3, 0.15, 0.2, 0.0, 0.0, 0.4),
    ]
    return [architecture_a_position_from_q(q, params=params) for q in seeds]


def radial_grid_positions(
    *,
    n_radial: int = 6,
    n_elbow: int = 5,
    params: ArchitectureParams | None = None,
) -> list[WorkspaceSample]:
    """Grid over ``(q2, q3)`` with other joints zero (Architecture A)."""
    arch = ArchitectureA(params)
    out: list[WorkspaceSample] = []
    for i in range(n_radial):
        q2 = -math.pi / 3 + (2 * math.pi / 3) * (i / max(n_radial - 1, 1))
        for j in range(n_elbow):
            q3 = -math.pi / 3 + (2 * math.pi / 3) * (j / max(n_elbow - 1, 1))
            q = (0.0, q2, q3, 0.0, 0.0, 0.0)
            fk = arch.forward(q)
            cw = fk.joints[3].origin
            rho = math.sqrt(cw[0] ** 2 + cw[1] ** 2 + cw[2] ** 2)
            out.append(
                WorkspaceSample(
                    position=fk.tool_position,
                    joint_seed=q,
                    label=f"q2={q2:.3f},q3={q3:.3f}",
                    rho_w=rho,
                )
            )
    return out
