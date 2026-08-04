"""Shared reduction result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sixr_grashof.classification.mccarthy_soh import SphericalFourBar
from sixr_grashof.kinematics.axes import Vec3
from sixr_grashof.reductions.residuals import ConcurrencyReport, ReductionStatus

ReductionKind = Literal["regional", "spherical", "combined"]


@dataclass(frozen=True, slots=True)
class RegionalPlanarReduction:
    """Regional planar reduction at a fixed architecture state.

    Planar four-bar order (when present)::

        ground = rho_p (tool planar radius)
        input  = Lt
        coupler = L3
        output = L2
    """

    rho_w: float
    rho_p: float
    L2: float
    L3: float
    Lt: float
    quotient_azimuth: float
    wrist_reachable: bool
    ground: float
    input_length: float
    coupler_length: float
    output_length: float
    assemblable: bool
    grashof_class: str
    status: ReductionStatus
    notes: str = ""


@dataclass(frozen=True, slots=True)
class SphericalOrientationReduction:
    """Spherical virtual four-bar at a fixed architecture state."""

    linkage: SphericalFourBar | None
    concurrency: ConcurrencyReport
    status: ReductionStatus
    directions: tuple[Vec3, Vec3, Vec3, Vec3] | None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class CombinedReduction:
    """Regional + spherical reduction for one physical state."""

    architecture_id: str
    joint_configuration: tuple[float, float, float, float, float, float]
    wrist_center: Vec3
    tool_position: Vec3
    regional: RegionalPlanarReduction
    spherical: SphericalOrientationReduction
