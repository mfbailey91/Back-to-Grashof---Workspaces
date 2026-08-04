"""Spherical virtual four-bar reduction from concurrent wrist geometry."""

from __future__ import annotations

import math

from sixr_grashof.classification.mccarthy_soh import SphericalFourBar
from sixr_grashof.kinematics.axes import Vec3, _cross, _dot, _norm, normalize
from sixr_grashof.kinematics.forward import ForwardKinematicsResult
from sixr_grashof.reductions.residuals import (
    ConcurrencyReport,
    ReductionStatus,
    concurrency_residual,
)
from sixr_grashof.reductions.types import SphericalOrientationReduction


def _angle(u: Vec3, v: Vec3) -> float:
    c = max(-1.0, min(1.0, _dot(u, v)))
    return math.acos(c)


def _clamp_link_angle(angle: float, *, eps: float = 1e-12) -> float | None:
    """Map an angle into (0, pi]; return None if numerically zero/undefined."""
    if not math.isfinite(angle):
        return None
    a = abs(angle)
    if a <= eps:
        return None
    if a > math.pi:
        a = 2.0 * math.pi - a
    if a <= eps or a > math.pi + eps:
        return None
    return min(a, math.pi)


def meridional_normal(fk: ForwardKinematicsResult) -> Vec3 | None:
    """Return n = normalize(a2 x e_f) for Architecture A spherical construction."""
    a2 = fk.joints[1].axis.direction
    p3 = fk.joints[2].origin
    cw = fk.joints[3].origin
    forearm = (cw[0] - p3[0], cw[1] - p3[1], cw[2] - p3[2])
    if _norm(forearm) < 1e-15:
        forearm = fk.joints[3].axis.direction
    n = _cross(a2, forearm)
    if _norm(n) < 1e-15:
        return None
    return normalize(n)


def spherical_directions(fk: ForwardKinematicsResult) -> tuple[Vec3, Vec3, Vec3, Vec3] | None:
    """Return (n, a4, a5, a6) unit directions on the wrist sphere."""
    n = meridional_normal(fk)
    if n is None:
        return None
    a4 = normalize(fk.joints[3].axis.direction)
    a5 = normalize(fk.joints[4].axis.direction)
    a6 = normalize(fk.joints[5].axis.direction)
    return (n, a4, a5, a6)


def angles_from_directions(
    directions: tuple[Vec3, Vec3, Vec3, Vec3],
) -> SphericalFourBar | None:
    """Map (n,f,m,t) to (alpha, beta, gamma, eta) in McCarthy–Soh order.

    alpha = ∠(n, f)
    eta   = ∠(f, m)
    beta  = ∠(m, t)   # hand / output
    gamma = ∠(t, n)
    """
    n, f, m, t = directions
    alpha = _clamp_link_angle(_angle(n, f))
    eta = _clamp_link_angle(_angle(f, m))
    beta = _clamp_link_angle(_angle(m, t))
    gamma = _clamp_link_angle(_angle(t, n))
    if None in (alpha, eta, beta, gamma):
        return None
    assert alpha is not None and eta is not None and beta is not None and gamma is not None
    return SphericalFourBar(alpha=alpha, beta=beta, gamma=gamma, eta=eta)


def reduce_spherical_orientation(
    fk: ForwardKinematicsResult,
    *,
    scale_L2: float,
    force_status: ReductionStatus | None = None,
) -> SphericalOrientationReduction:
    """Build spherical reduction; emit no angles when status is invalid."""
    axes = [fk.joints[i].axis for i in (3, 4, 5)]
    concurrency = concurrency_residual(axes, scale_L2=scale_L2)
    status = force_status if force_status is not None else concurrency.status

    if status == "invalid":
        return SphericalOrientationReduction(
            linkage=None,
            concurrency=concurrency,
            status=status,
            directions=None,
            notes="invalid concurrency residual; spherical angles withheld",
        )

    directions = spherical_directions(fk)
    if directions is None:
        return SphericalOrientationReduction(
            linkage=None,
            concurrency=concurrency,
            status="invalid",
            directions=None,
            notes="meridional normal undefined; spherical angles withheld",
        )

    linkage = angles_from_directions(directions)
    if linkage is None:
        return SphericalOrientationReduction(
            linkage=None,
            concurrency=concurrency,
            status="invalid",
            directions=directions,
            notes="one or more spherical link angles outside (0, pi]",
        )

    return SphericalOrientationReduction(
        linkage=linkage,
        concurrency=concurrency,
        status=status,
        directions=directions,
        notes="Architecture A axis-sphere construction (docs/spherical_reduction.md)",
    )
