"""Synthetic spatial-6R corpus for the V07 fixed-position orientation program.

Conventions match V05/V06: home axes in world frame ``W``, off-axis tool origin so
the fixed-position nullspace is not pure terminal roll. This module provides
geometry + seed audits only. It does **not** construct a three-dimensional
``FixedPositionParentResult`` (V07A), freeze an SO(3) reference (Gate K3), or
claim dexterous workspace coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .aligned_6r import frame_from_pointing
from .axis_geometry import AxisLine, as_mat3, as_vec3, point_axis_distance
from .fixed_position import (
    FixedPositionSeedAudit,
    audit_fixed_position_seed,
    pose_fixed_position_problem,
)
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

GENERIC_6R_REGULAR_Q = (0.35, -0.40, 0.45, -0.30, 0.25, 0.20)
ACTIVE_TOOL_TRANSVERSE_OFFSET_M = 0.06
ACTIVE_TOOL_AXIAL_OFFSET_M = 0.05


def _r_phys_roles(n: int) -> tuple[str, ...]:
    return tuple("R_phys" for _ in range(n))


def _r_kinds(n: int) -> tuple[str, ...]:
    return tuple("R" for _ in range(n))


def generic_6r_home_axes() -> tuple[AxisLine, ...]:
    """Six generically skew revolute axes (no designed intersections or alignment)."""

    return (
        AxisLine((0.00, 0.00, 0.00), (0.00, 0.00, 1.00)),
        AxisLine((0.12, 0.05, 0.22), (1.00, 0.20, 0.08)),
        AxisLine((0.28, -0.08, 0.40), (0.18, 1.00, 0.12)),
        AxisLine((0.45, 0.10, 0.55), (-0.15, 0.25, 1.00)),
        AxisLine((0.58, -0.04, 0.68), (0.12, -0.18, 1.00)),
        AxisLine((0.72, 0.08, 0.82), (-0.10, 0.22, 0.95)),
    )


def _stable_transverse(last: AxisLine) -> np.ndarray:
    w = np.asarray(last.w, dtype=float)
    helper = np.array((0.0, 0.0, 1.0)) if abs(float(w[2])) < 0.9 else np.array((0.0, 1.0, 0.0))
    transverse = np.cross(helper, w)
    norm = float(np.linalg.norm(transverse))
    if norm <= 1e-15:
        raise ValueError("failed to construct terminal-axis transverse direction")
    return transverse / norm


def _chain_from_axes(
    axes: tuple[AxisLine, ...],
    *,
    axial_offset_m: float = ACTIVE_TOOL_AXIAL_OFFSET_M,
    transverse_offset_m: float = ACTIVE_TOOL_TRANSVERSE_OFFSET_M,
) -> SerialRevoluteChain:
    if axial_offset_m < 0.0:
        raise ValueError("axial_offset_m must be nonnegative")
    if transverse_offset_m < 0.0:
        raise ValueError("transverse_offset_m must be nonnegative")
    last = axes[-1]
    w = np.asarray(last.w, dtype=float)
    transverse = _stable_transverse(last)
    p0_arr = (
        np.asarray(last.r, dtype=float)
        + axial_offset_m * w
        + transverse_offset_m * transverse
    )
    p0 = as_vec3(p0_arr)
    d0 = as_vec3(w)
    return SerialRevoluteChain(
        home_axes=axes,
        p0=p0,
        d0=d0,
        R0=as_mat3(np.asarray(frame_from_pointing(d0), dtype=float)),
    )


@dataclass(frozen=True, slots=True)
class Spatial6RCorpusEntry:
    """Named spatial-6R corpus member with a default fixed-position seed."""

    model: OpenChainModel
    regular_q: tuple[float, ...]
    terminal_axis_offset_m: float
    notes: tuple[str, ...] = ()


def build_generic_6r() -> Spatial6RCorpusEntry:
    """Off-axis generic 6R source for V07/L6 scaffold seed audits."""

    axes = generic_6r_home_axes()
    chain = _chain_from_axes(axes)
    axis_distance = point_axis_distance(chain.p0, axes[-1])
    notes = (
        "V07/L6 scaffold corpus: geometry + seed audit only.",
        "Not a FixedPositionParentResult / frozen SO(3) orientation reference.",
        "Non-aligned: no intentional consecutive intersecting pairs or terminal-roll design.",
        f"terminal_tool_axis_distance_m={axis_distance:.6e}",
    )
    model = OpenChainModel(
        architecture_id="generic_6r",
        chain=chain,
        joint_kind_sequence=_r_kinds(6),
        joint_role_sequence=_r_phys_roles(6),
        notes=notes,
    )
    return Spatial6RCorpusEntry(
        model=model,
        regular_q=GENERIC_6R_REGULAR_Q,
        terminal_axis_offset_m=axis_distance,
        notes=notes,
    )


def audit_fixed_position_seed_6r(
    entry: Spatial6RCorpusEntry,
) -> FixedPositionSeedAudit:
    """Audit a spatial-6R fixed-position seed (expect rank 3, nullity 3 when regular)."""

    problem = pose_fixed_position_problem(entry.model, entry.regular_q)
    return audit_fixed_position_seed(problem)


def seed_audit_summary(audit: FixedPositionSeedAudit) -> dict[str, Any]:
    """Compact JSON-safe seed audit for ladder readouts (not an SO(3) parent)."""

    return {
        "architecture_id": audit.architecture_id,
        "status": audit.status,
        "regular": audit.regular,
        "rank_jp": audit.rank_jp,
        "nullity_jp": audit.nullity_jp,
        "p_star": list(audit.p_star),
        "p_residual_m": audit.p_residual_m,
        "motion_signature": audit.motion_signature,
        "finite_difference_verified": audit.finite_difference_verified,
        "notes": [
            "Seed audit only; does not represent a frozen SO(3) orientation reference.",
            "Gate K3 / ADR-013: freeze a decomposition-free SO(3) reference before V08/V09.",
            "ADR-024: do not treat 1D traces as the M=3 parent.",
        ],
    }
