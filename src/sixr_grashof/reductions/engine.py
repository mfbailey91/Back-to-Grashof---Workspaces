"""Top-level reduction entry points for Architectures A/B/C."""

from __future__ import annotations

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.architectures.base import wrist_axes_from_fk
from sixr_grashof.reductions.planar_fourbar import reduce_regional_planar
from sixr_grashof.reductions.residuals import concurrency_residual
from sixr_grashof.reductions.spherical_fourbar import reduce_spherical_orientation
from sixr_grashof.reductions.symmetry import base_symmetry_report
from sixr_grashof.reductions.types import CombinedReduction

JointConfig = tuple[float, float, float, float, float, float]


def reduce_architecture_a(
    arch: ArchitectureA,
    q: JointConfig,
) -> CombinedReduction:
    """Exact regional + spherical reduction for Architecture A."""
    fk = arch.forward(q)
    p = arch.params
    sym = base_symmetry_report(fk.joints[0].axis, fk.joints[3].origin, shoulder_offset=0.0)
    regional = reduce_regional_planar(
        fk,
        L2=p.L2,
        L3=p.L3,
        Lt=p.Lt,
        status="exact",
        notes=sym.notes,
    )
    spherical = reduce_spherical_orientation(fk, scale_L2=p.L2)
    return CombinedReduction(
        architecture_id="A",
        joint_configuration=q,
        wrist_center=fk.joints[3].origin,
        tool_position=fk.tool_position,
        regional=regional,
        spherical=spherical,
    )


def reduce_architecture_b(
    arch: ArchitectureB,
    q: JointConfig,
) -> CombinedReduction:
    """Regional candidate + residual-gated spherical reduction for Architecture B."""
    fk = arch.forward(q)
    p = arch.params
    wrist = concurrency_residual(wrist_axes_from_fk(fk), scale_L2=p.L2)
    regional = reduce_regional_planar(
        fk,
        L2=p.L2,
        L3=p.L3,
        Lt=p.Lt,
        status="exact" if p.epsilon_w == 0.0 else "approximate",
        notes=f"Architecture B epsilon_w={p.epsilon_w}",
    )
    spherical = reduce_spherical_orientation(fk, scale_L2=p.L2)
    # Force invalid spherical emission when residual says invalid.
    if wrist.status == "invalid":
        spherical = reduce_spherical_orientation(fk, scale_L2=p.L2, force_status="invalid")
    return CombinedReduction(
        architecture_id="B",
        joint_configuration=q,
        wrist_center=fk.joints[3].origin,
        tool_position=fk.tool_position,
        regional=regional,
        spherical=spherical,
    )


def reduce_architecture_c(
    arch: ArchitectureC,
    q: JointConfig,
) -> CombinedReduction:
    """Shoulder-offset regional note + exact spherical wrist for Architecture C."""
    fk = arch.forward(q)
    p = arch.params
    sym = base_symmetry_report(
        fk.joints[0].axis,
        fk.joints[3].origin,
        shoulder_offset=p.epsilon_s,
    )
    regional = reduce_regional_planar(
        fk,
        L2=p.L2,
        L3=p.L3,
        Lt=p.Lt,
        status="exact" if p.epsilon_s == 0.0 else "approximate",
        notes=sym.notes,
    )
    spherical = reduce_spherical_orientation(fk, scale_L2=p.L2)
    return CombinedReduction(
        architecture_id="C",
        joint_configuration=q,
        wrist_center=fk.joints[3].origin,
        tool_position=fk.tool_position,
        regional=regional,
        spherical=spherical,
    )


def reduce_sixr(
    architecture_id: str,
    q: JointConfig,
    *,
    params: ArchitectureParams | None = None,
) -> CombinedReduction:
    """Dispatch reduction by architecture id ``A``|``B``|``C``."""
    p = params or ArchitectureParams()
    if architecture_id == "A":
        return reduce_architecture_a(ArchitectureA(ArchitectureParams(L2=p.L2, L3=p.L3, Lt=p.Lt)), q)
    if architecture_id == "B":
        return reduce_architecture_b(
            ArchitectureB(ArchitectureParams(L2=p.L2, L3=p.L3, Lt=p.Lt, epsilon_w=p.epsilon_w)),
            q,
        )
    if architecture_id == "C":
        return reduce_architecture_c(
            ArchitectureC(ArchitectureParams(L2=p.L2, L3=p.L3, Lt=p.Lt, epsilon_s=p.epsilon_s)),
            q,
        )
    raise ValueError(f"unknown architecture_id {architecture_id!r}")
