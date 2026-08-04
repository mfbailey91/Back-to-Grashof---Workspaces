"""Base-azimuth symmetry detection and quotienting."""

from __future__ import annotations

import math
from dataclasses import dataclass

from sixr_grashof.kinematics.axes import AxisLine, Vec3, are_parallel, _dot, _norm


@dataclass(frozen=True, slots=True)
class BaseSymmetryReport:
    """Whether unrestricted base rotation about z1 is a valid task-space quotient."""

    justified: bool
    azimuth: float
    z1_vertical: bool
    notes: str


def _unit_xy_azimuth(point: Vec3) -> float:
    return math.atan2(point[1], point[0])


def detect_base_symmetry(
    z1: AxisLine,
    *,
    shoulder_offset: float = 0.0,
    tol: float = 1e-12,
) -> bool:
    """Return True when Architecture-A-style base quotient is justified.

    Requires ``z1`` parallel to world ``(0,0,1)`` and zero shoulder offset.
    """
    vertical = are_parallel(z1, AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)), tol=tol)
    return vertical and shoulder_offset <= tol


def quotient_azimuth(wrist_center: Vec3) -> float:
    """Return base azimuth of the wrist center in the world XY plane."""
    if _norm((wrist_center[0], wrist_center[1], 0.0)) < 1e-15:
        return 0.0
    return _unit_xy_azimuth(wrist_center)


def base_symmetry_report(
    z1: AxisLine,
    wrist_center: Vec3,
    *,
    shoulder_offset: float = 0.0,
    tol: float = 1e-12,
) -> BaseSymmetryReport:
    justified = detect_base_symmetry(z1, shoulder_offset=shoulder_offset, tol=tol)
    z1_vertical = abs(abs(_dot(z1.direction, (0.0, 0.0, 1.0))) - 1.0) <= tol
    notes = (
        "unrestricted q1 quotient justified"
        if justified
        else "base quotient not justified (offset or non-vertical z1)"
    )
    return BaseSymmetryReport(
        justified=justified,
        azimuth=quotient_azimuth(wrist_center),
        z1_vertical=z1_vertical,
        notes=notes,
    )
