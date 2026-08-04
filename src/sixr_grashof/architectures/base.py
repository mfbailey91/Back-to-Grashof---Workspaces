"""Shared synthetic 6R architecture interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sixr_grashof.kinematics.axes import AxisLine, are_parallel, shortest_distance
from sixr_grashof.kinematics.forward import ForwardKinematicsResult
from sixr_grashof.reductions.residuals import ConcurrencyReport, concurrency_residual


@dataclass(frozen=True, slots=True)
class ArchitectureParams:
    """Normalized link lengths and offset parameters."""

    L2: float = 1.0
    L3: float = 0.8
    Lt: float = 0.25
    epsilon_w: float = 0.0
    epsilon_s: float = 0.0

    def __post_init__(self) -> None:
        if self.L2 <= 0.0 or self.L3 <= 0.0 or self.Lt < 0.0:
            raise ValueError("L2, L3 must be positive; Lt nonnegative")
        if self.epsilon_w < 0.0 or self.epsilon_s < 0.0:
            raise ValueError("offsets must be nonnegative")


@dataclass(frozen=True, slots=True)
class GeometryReport:
    """Axis-geometry summary for Sprint 1 acceptance checks."""

    architecture_id: str
    params: ArchitectureParams
    wrist_concurrency: ConcurrencyReport
    z1_z2_distance: float
    z2_z3_parallel: bool
    z2_z3_z4_parallel: bool | None
    regional_exact_candidate: bool
    spherical_status: str


class SyntheticSixR(Protocol):
    architecture_id: str
    params: ArchitectureParams

    def forward(self, q: tuple[float, float, float, float, float, float]) -> ForwardKinematicsResult:
        ...

    def geometry_report(
        self,
        q: tuple[float, float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    ) -> GeometryReport:
        ...


def wrist_axes_from_fk(fk: ForwardKinematicsResult) -> list[AxisLine]:
    return [fk.joints[i].axis for i in (3, 4, 5)]


def build_geometry_report(
    *,
    architecture_id: str,
    params: ArchitectureParams,
    fk: ForwardKinematicsResult,
    expect_z2_z3_z4_parallel: bool | None,
    regional_exact_candidate: bool,
) -> GeometryReport:
    axes = [j.axis for j in fk.joints]
    wrist = concurrency_residual(wrist_axes_from_fk(fk), scale_L2=params.L2)
    z2_z3_par = are_parallel(axes[1], axes[2])
    z234: bool | None
    if expect_z2_z3_z4_parallel is None:
        z234 = None
    else:
        z234 = z2_z3_par and are_parallel(axes[2], axes[3])
    return GeometryReport(
        architecture_id=architecture_id,
        params=params,
        wrist_concurrency=wrist,
        z1_z2_distance=shortest_distance(axes[0], axes[1]),
        z2_z3_parallel=z2_z3_par,
        z2_z3_z4_parallel=z234,
        regional_exact_candidate=regional_exact_candidate,
        spherical_status=wrist.status,
    )
