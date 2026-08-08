"""Minimal V05A synthetic spatial-4R corpus for fixed-position fiber work.

Conventions
-----------
All models are ``SerialRevoluteChain`` instances with four home axes in world
frame ``W``. Task point ``p0`` and pointing ``d0`` are expressed in ``W``.
No URDF import. ``exact_u_pair_4r`` plants an exact consecutive intersecting
orthogonal pair (V05D). ``near_aligned_u_pair_4r`` is an intentional near-miss
that must be rejected as exact ``U`` (V05E).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .aligned_6r import frame_from_pointing
from .axis_geometry import AxisLine, line_line_distance, parallelism_residual
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

GENERIC_4R_REGULAR_Q = (0.40, -0.35, 0.55, -0.25)
EXACT_U_PAIR_REGULAR_Q = (0.30, -0.45, 0.50, 0.20)
NEAR_ALIGNED_U_PAIR_REGULAR_Q = (0.30, -0.45, 0.50, 0.20)
SINGULAR_4R_Q = (0.0, 0.0, 0.0, 0.0)

# Planted near-miss relative to exact_u_pair_4r (above V05D exact tols).
NEAR_ALIGNED_MISS_M = 1e-4
NEAR_ALIGNED_TILT_RAD = 1e-3


def _r_phys_roles(n: int) -> tuple[str, ...]:
    return tuple("R_phys" for _ in range(n))


def _r_kinds(n: int) -> tuple[str, ...]:
    return tuple("R" for _ in range(n))


def generic_4r_home_axes() -> tuple[AxisLine, ...]:
    """Four generically skew revolute axes (no designed intersections)."""
    return (
        AxisLine((0.00, 0.00, 0.00), (0.00, 0.00, 1.00)),
        AxisLine((0.12, 0.05, 0.22), (1.00, 0.20, 0.08)),
        AxisLine((0.28, -0.08, 0.40), (0.18, 1.00, 0.12)),
        AxisLine((0.45, 0.10, 0.55), (-0.15, 0.25, 1.00)),
    )


def exact_u_pair_4r_home_axes() -> tuple[AxisLine, ...]:
    """R1∩R2 exact orthogonal U-candidate; R3,R4 generically placed."""
    ua = (0.00, 0.00, 0.20)
    return (
        AxisLine(ua, (0.00, 0.00, 1.00)),
        AxisLine(ua, (1.00, 0.00, 0.00)),
        AxisLine((0.30, 0.08, 0.42), (0.20, 1.00, 0.10)),
        AxisLine((0.48, -0.06, 0.58), (-0.10, 0.22, 1.00)),
    )


def near_aligned_u_pair_4r_home_axes() -> tuple[AxisLine, ...]:
    """Near-miss of exact_u_pair: common-perpendicular offset + tilt of R2.

    R2 is offset by ``NEAR_ALIGNED_MISS_M`` along +ŷ and tilted by
    ``NEAR_ALIGNED_TILT_RAD`` about ŷ so both pair distance and ``|w1·w2|``
    exceed exact aggregation tolerances while remaining visually near-U.
    """
    base = exact_u_pair_4r_home_axes()
    a0 = base[0]
    r2 = (
        float(a0.r[0]),
        float(a0.r[1] + NEAR_ALIGNED_MISS_M),
        float(a0.r[2]),
    )
    # Rotate exact w2=(1,0,0) about ŷ by a small tilt → nonzero |w1·w2|.
    c = float(np.cos(NEAR_ALIGNED_TILT_RAD))
    s = float(np.sin(NEAR_ALIGNED_TILT_RAD))
    w2 = (c, 0.0, -s)
    return (
        a0,
        AxisLine(r2, w2),
        base[2],
        base[3],
    )


def singular_4r_home_axes() -> tuple[AxisLine, ...]:
    """All four axes parallel — position Jacobian rank drops generically."""
    w = (0.00, 0.00, 1.00)
    return (
        AxisLine((0.00, 0.00, 0.00), w),
        AxisLine((0.20, 0.00, 0.00), w),
        AxisLine((0.40, 0.00, 0.00), w),
        AxisLine((0.60, 0.00, 0.00), w),
    )


def _chain_from_axes(axes: tuple[AxisLine, ...], tool_offset_m: float = 0.05) -> SerialRevoluteChain:
    last = axes[-1]
    w = np.asarray(last.w, dtype=float)
    p0 = tuple(float(x) for x in (np.asarray(last.r, dtype=float) + tool_offset_m * w))
    d0 = tuple(float(x) for x in w)
    return SerialRevoluteChain(home_axes=axes, p0=p0, d0=d0, R0=frame_from_pointing(d0))


@dataclass(frozen=True, slots=True)
class Spatial4RCorpusEntry:
    """Named corpus member with a default seed configuration."""

    model: OpenChainModel
    regular_q: tuple[float, ...]
    expected_regular: bool


def build_generic_4r() -> Spatial4RCorpusEntry:
    axes = generic_4r_home_axes()
    chain = _chain_from_axes(axes)
    model = OpenChainModel(
        architecture_id="generic_4r",
        chain=chain,
        joint_kind_sequence=_r_kinds(4),
        joint_role_sequence=_r_phys_roles(4),
        notes=("No intentional consecutive intersecting pairs.",),
    )
    return Spatial4RCorpusEntry(model=model, regular_q=GENERIC_4R_REGULAR_Q, expected_regular=True)


def build_exact_u_pair_4r() -> Spatial4RCorpusEntry:
    axes = exact_u_pair_4r_home_axes()
    chain = _chain_from_axes(axes)
    dist = line_line_distance(axes[0], axes[1])
    par = parallelism_residual(axes[0].w, axes[1].w)
    model = OpenChainModel(
        architecture_id="exact_u_pair_4r",
        chain=chain,
        joint_kind_sequence=_r_kinds(4),
        joint_role_sequence=_r_phys_roles(4),
        notes=(
            "Exact consecutive orthogonal intersecting RR at J1/J2 (U_phys candidate).",
            "Aggregation certificate issued by active V05D.",
            f"pair_distance={dist:.3e}, pair_parallelism={par:.3e}",
        ),
    )
    return Spatial4RCorpusEntry(model=model, regular_q=EXACT_U_PAIR_REGULAR_Q, expected_regular=True)


def build_near_aligned_u_pair_4r() -> Spatial4RCorpusEntry:
    axes = near_aligned_u_pair_4r_home_axes()
    chain = _chain_from_axes(axes)
    dist = line_line_distance(axes[0], axes[1])
    par = parallelism_residual(axes[0].w, axes[1].w)
    dot = abs(float(np.dot(np.asarray(axes[0].w, dtype=float), np.asarray(axes[1].w, dtype=float))))
    model = OpenChainModel(
        architecture_id="near_aligned_u_pair_4r",
        chain=chain,
        joint_kind_sequence=_r_kinds(4),
        joint_role_sequence=_r_phys_roles(4),
        notes=(
            "Intentional near-miss of exact RR→U at J1/J2; must not be treated as exact U_phys.",
            "Active V05E rejection + false-U surrogate task-error diagnostic.",
            f"pair_distance={dist:.3e}, pair_parallelism={par:.3e}, |w·w'|={dot:.3e}",
            f"planted_miss_m={NEAR_ALIGNED_MISS_M:.3e}, planted_tilt_rad={NEAR_ALIGNED_TILT_RAD:.3e}",
        ),
    )
    return Spatial4RCorpusEntry(
        model=model,
        regular_q=NEAR_ALIGNED_U_PAIR_REGULAR_Q,
        expected_regular=True,
    )


def build_singular_4r() -> Spatial4RCorpusEntry:
    axes = singular_4r_home_axes()
    chain = _chain_from_axes(axes, tool_offset_m=0.08)
    model = OpenChainModel(
        architecture_id="singular_4r_parallel",
        chain=chain,
        joint_kind_sequence=_r_kinds(4),
        joint_role_sequence=_r_phys_roles(4),
        notes=("All axes parallel; exterior / rank-deficient counterexample.",),
    )
    return Spatial4RCorpusEntry(model=model, regular_q=SINGULAR_4R_Q, expected_regular=False)


def v05a_spatial_4r_corpus() -> tuple[Spatial4RCorpusEntry, ...]:
    """Return the minimal exact V05A corpus used by active V05B–E."""
    return (
        build_generic_4r(),
        build_exact_u_pair_4r(),
        build_near_aligned_u_pair_4r(),
        build_singular_4r(),
    )
