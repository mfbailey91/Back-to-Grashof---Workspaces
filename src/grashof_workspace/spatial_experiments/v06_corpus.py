"""Synthetic spatial-5R corpus for the V06 fixed-position parent program.

Conventions match V05: home axes in world frame ``W``, off-axis tool origin so
the fixed-position nullspace is not pure terminal roll. This module provides
geometry + seed audits only. It does **not** construct a two-dimensional
``FixedPositionParentResult`` (V06A) or claim complete pointing-parent coverage.
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

GENERIC_5R_REGULAR_Q = (0.35, -0.40, 0.45, -0.30, 0.25)
EXACT_TWO_U_REGULAR_Q = (0.30, -0.35, 0.40, -0.25, 0.20)
NEAR_TWO_U_REGULAR_Q = EXACT_TWO_U_REGULAR_Q
ACTIVE_TOOL_TRANSVERSE_OFFSET_M = 0.06
ACTIVE_TOOL_AXIAL_OFFSET_M = 0.05
NEAR_TWO_U_MISS_M = 1e-4
NEAR_TWO_U_TILT_RAD = 1e-3


def _r_phys_roles(n: int) -> tuple[str, ...]:
    return tuple("R_phys" for _ in range(n))


def _r_kinds(n: int) -> tuple[str, ...]:
    return tuple("R" for _ in range(n))


def generic_5r_home_axes() -> tuple[AxisLine, ...]:
    """Five generically skew revolute axes (no designed intersections)."""

    return (
        AxisLine((0.00, 0.00, 0.00), (0.00, 0.00, 1.00)),
        AxisLine((0.12, 0.05, 0.22), (1.00, 0.20, 0.08)),
        AxisLine((0.28, -0.08, 0.40), (0.18, 1.00, 0.12)),
        AxisLine((0.45, 0.10, 0.55), (-0.15, 0.25, 1.00)),
        AxisLine((0.58, -0.04, 0.68), (0.12, -0.18, 1.00)),
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
class Spatial5RCorpusEntry:
    """Named spatial-5R corpus member with a default fixed-position seed."""

    model: OpenChainModel
    regular_q: tuple[float, ...]
    terminal_axis_offset_m: float
    notes: tuple[str, ...] = ()


def build_generic_5r() -> Spatial5RCorpusEntry:
    """Off-axis generic 5R source for V06/L5 scaffold seed audits."""

    axes = generic_5r_home_axes()
    chain = _chain_from_axes(axes)
    axis_distance = point_axis_distance(chain.p0, axes[-1])
    notes = (
        "V06/L5 scaffold corpus: geometry + seed audit only.",
        "Not a FixedPositionParentResult / complete 2D pointing parent.",
        "No intentional consecutive intersecting pairs.",
        f"terminal_tool_axis_distance_m={axis_distance:.6e}",
    )
    model = OpenChainModel(
        architecture_id="generic_5r",
        chain=chain,
        joint_kind_sequence=_r_kinds(5),
        joint_role_sequence=_r_phys_roles(5),
        notes=notes,
    )
    return Spatial5RCorpusEntry(
        model=model,
        regular_q=GENERIC_5R_REGULAR_Q,
        terminal_axis_offset_m=axis_distance,
        notes=notes,
    )


def exact_two_u_5r_home_axes() -> tuple[AxisLine, ...]:
    """J1/J2 and J3/J4 are exact intersecting orthogonal U_phys pairs."""

    c1 = (0.00, 0.00, 0.20)
    c2 = (0.32, 0.06, 0.48)
    return (
        AxisLine(c1, (0.00, 0.00, 1.00)),
        AxisLine(c1, (1.00, 0.00, 0.00)),
        AxisLine(c2, (0.00, 0.00, 1.00)),
        AxisLine(c2, (0.00, 1.00, 0.00)),
        AxisLine((0.55, -0.05, 0.70), (0.15, -0.20, 1.00)),
    )


def near_two_u_5r_home_axes() -> tuple[AxisLine, ...]:
    """Exact two-U geometry with J3/J4 perturbed past aggregation tolerance."""

    base = exact_two_u_5r_home_axes()
    a3 = base[2]
    r4 = (
        float(a3.r[0]),
        float(a3.r[1] + NEAR_TWO_U_MISS_M),
        float(a3.r[2]),
    )
    c = float(np.cos(NEAR_TWO_U_TILT_RAD))
    s = float(np.sin(NEAR_TWO_U_TILT_RAD))
    w4 = (s, c, 0.0)
    return (base[0], base[1], a3, AxisLine(r4, w4), base[4])


def _entry_from_axes(
    *,
    architecture_id: str,
    axes: tuple[AxisLine, ...],
    regular_q: tuple[float, ...],
    extra_notes: tuple[str, ...],
) -> Spatial5RCorpusEntry:
    chain = _chain_from_axes(axes)
    axis_distance = point_axis_distance(chain.p0, axes[-1])
    notes = (
        *extra_notes,
        f"terminal_tool_axis_distance_m={axis_distance:.6e}",
    )
    model = OpenChainModel(
        architecture_id=architecture_id,
        chain=chain,
        joint_kind_sequence=_r_kinds(5),
        joint_role_sequence=_r_phys_roles(5),
        notes=notes,
    )
    return Spatial5RCorpusEntry(
        model=model,
        regular_q=regular_q,
        terminal_axis_offset_m=axis_distance,
        notes=notes,
    )


def build_exact_two_u_5r() -> Spatial5RCorpusEntry:
    """Off-axis 5R with two non-overlapping exact U_phys pairs."""

    return _entry_from_axes(
        architecture_id="exact_two_u_5r",
        axes=exact_two_u_5r_home_axes(),
        regular_q=EXACT_TWO_U_REGULAR_Q,
        extra_notes=(
            "V06B structured source: J1/J2 and J3/J4 exact intersecting orthogonal U_phys.",
            "Not a complete 2D parent and not a UUUR child.",
        ),
    )


def build_near_two_u_5r() -> Spatial5RCorpusEntry:
    """Near-miss control: second U pair must be rejected as exact aggregation."""

    return _entry_from_axes(
        architecture_id="near_two_u_5r",
        axes=near_two_u_5r_home_axes(),
        regular_q=NEAR_TWO_U_REGULAR_Q,
        extra_notes=(
            "V06B near control: J3/J4 perturbed beyond exact U tolerances.",
            "Must not receive EXACT_GLOBAL two-pair aggregation.",
        ),
    )


def audit_fixed_position_seed_5r(
    entry: Spatial5RCorpusEntry,
) -> FixedPositionSeedAudit:
    """Audit a spatial-5R fixed-position seed (expect rank 3, nullity 2 when regular)."""

    problem = pose_fixed_position_problem(entry.model, entry.regular_q)
    return audit_fixed_position_seed(problem)


def seed_audit_summary(audit: FixedPositionSeedAudit) -> dict[str, Any]:
    """Compact JSON-safe seed audit for ladder readouts (not a parent chart)."""

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
            "Seed audit only; does not represent the complete two-dimensional parent.",
            "Gate K2 / ADR-024: do not treat 1D traces as the M=2 parent.",
        ],
    }
