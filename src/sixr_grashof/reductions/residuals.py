"""Concurrency residual and exact/approximate/invalid labeling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sixr_grashof.kinematics.axes import (
    AxisLine,
    Vec3,
    least_squares_spherical_center,
    point_line_distance,
)

ReductionStatus = Literal["exact", "approximate", "invalid"]

# Named thresholds — also listed in configs/thresholds.yaml
RHO_EXACT_DEFAULT = 1.0e-9
RHO_INVALID_DEFAULT = 0.05


@dataclass(frozen=True, slots=True)
class ConcurrencyReport:
    """Spherical-cluster concurrency diagnostics."""

    center: Vec3
    residual_rho: float
    max_distance: float
    scale_L2: float
    status: ReductionStatus
    rho_exact: float
    rho_invalid: float


def concurrency_residual(
    axes: list[AxisLine],
    *,
    scale_L2: float,
    rho_exact: float = RHO_EXACT_DEFAULT,
    rho_invalid: float = RHO_INVALID_DEFAULT,
) -> ConcurrencyReport:
    """Compute ``rho_C = max_i d(c*, ell_i) / L2`` and label status."""
    if scale_L2 <= 0.0:
        raise ValueError("scale_L2 must be positive")
    if rho_exact < 0.0 or rho_invalid <= rho_exact:
        raise ValueError("require 0 <= rho_exact < rho_invalid")
    center = least_squares_spherical_center(axes)
    distances = [point_line_distance(center, axis) for axis in axes]
    max_d = max(distances)
    rho = max_d / scale_L2
    if rho <= rho_exact:
        status: ReductionStatus = "exact"
    elif rho <= rho_invalid:
        status = "approximate"
    else:
        status = "invalid"
    return ConcurrencyReport(
        center=center,
        residual_rho=rho,
        max_distance=max_d,
        scale_L2=scale_L2,
        status=status,
        rho_exact=rho_exact,
        rho_invalid=rho_invalid,
    )
