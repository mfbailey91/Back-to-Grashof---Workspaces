"""Regional planar four-bar reduction."""

from __future__ import annotations

from grashof_workspace.fourbar import FourBar
from sixr_grashof.kinematics.axes import Vec3, _cross, _dot, _norm, normalize
from sixr_grashof.kinematics.forward import ForwardKinematicsResult
from sixr_grashof.reductions.residuals import ReductionStatus
from sixr_grashof.reductions.symmetry import quotient_azimuth
from sixr_grashof.reductions.types import RegionalPlanarReduction


def _project_into_arm_plane(
    point: Vec3,
    *,
    plane_normal: Vec3,
    origin: Vec3 = (0.0, 0.0, 0.0),
) -> float:
    """Return distance from origin to the projection of ``point`` into the arm plane.

    The arm plane passes through ``origin`` with unit normal ``plane_normal``.
    For Architecture A the shoulder is at the origin and the planar radius is
    the in-plane distance from the origin to the projected point.
    """
    n = normalize(plane_normal)
    rel = (point[0] - origin[0], point[1] - origin[1], point[2] - origin[2])
    # Remove normal component.
    d = _dot(rel, n)
    proj = (rel[0] - d * n[0], rel[1] - d * n[1], rel[2] - d * n[2])
    return _norm(proj)


def arm_plane_normal(fk: ForwardKinematicsResult) -> Vec3:
    """Return unit normal to the arm plane from z2 and forearm direction."""
    a2 = fk.joints[1].axis.direction
    # Forearm: from joint 3 origin toward wrist (joint 4 origin).
    p3 = fk.joints[2].origin
    cw = fk.joints[3].origin
    forearm = (cw[0] - p3[0], cw[1] - p3[1], cw[2] - p3[2])
    if _norm(forearm) < 1e-15:
        forearm = fk.joints[3].axis.direction
    n = _cross(a2, forearm)
    if _norm(n) < 1e-15:
        # Degenerate: fall back to cross(a2, world z)
        n = _cross(a2, (0.0, 0.0, 1.0))
    if _norm(n) < 1e-15:
        n = (1.0, 0.0, 0.0)
    return normalize(n)


def wrist_center_reachable(rho_w: float, L2: float, L3: float, *, tol: float = 1e-12) -> bool:
    return (abs(L2 - L3) - tol) <= rho_w <= (L2 + L3 + tol)


def reduce_regional_planar(
    fk: ForwardKinematicsResult,
    *,
    L2: float,
    L3: float,
    Lt: float,
    status: ReductionStatus = "exact",
    notes: str = "",
) -> RegionalPlanarReduction:
    """Build the regional planar reduction for a forward-kinematics state.

    Conventions (see docs/spherical_reduction.md)::

        ground = rho_p (planar tool radius)
        input  = Lt
        coupler = L3
        output = L2
    """
    cw = fk.joints[3].origin
    rho_w = _norm(cw)
    normal = arm_plane_normal(fk)
    rho_p = _project_into_arm_plane(fk.tool_position, plane_normal=normal)
    # Guard degenerate tool radius for FourBar positivity.
    ground = max(rho_p, 1e-15)
    fb = FourBar(ground=ground, input=Lt if Lt > 0.0 else 1e-15, coupler=L3, output=L2)
    return RegionalPlanarReduction(
        rho_w=rho_w,
        rho_p=rho_p,
        L2=L2,
        L3=L3,
        Lt=Lt,
        quotient_azimuth=quotient_azimuth(cw),
        wrist_reachable=wrist_center_reachable(rho_w, L2, L3),
        ground=fb.ground,
        input_length=fb.input,
        coupler_length=fb.coupler,
        output_length=fb.output,
        assemblable=fb.is_assemblable(),
        grashof_class=fb.grashof_class(),
        status=status,
        notes=notes or f"planar four-bar (ρ_p={rho_p:.6g}, Lt, L3, L2)",
    )


def planar_fourbar_from_reduction(regional: RegionalPlanarReduction) -> FourBar:
    """Reconstruct the planar FourBar from a regional reduction record."""
    return FourBar(
        ground=regional.ground,
        input=regional.input_length,
        coupler=regional.coupler_length,
        output=regional.output_length,
    )
