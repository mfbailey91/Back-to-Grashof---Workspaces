"""Minimal V05A synthetic spatial-4R corpus for fixed-position fiber work.

Conventions
-----------
All models are ``SerialRevoluteChain`` instances with four home axes in world
frame ``W``. Task point ``p0`` and pointing ``d0`` are expressed in ``W``.
No URDF import. The ``exact_u_pair_4r`` architecture plants an exact consecutive
intersecting orthogonal pair for V05D aggregation certificates.
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
SINGULAR_4R_Q = (0.0, 0.0, 0.0, 0.0)


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
    """Return the minimal exact V05A corpus used by active V05B."""
    return (
        build_generic_4r(),
        build_exact_u_pair_4r(),
        build_singular_4r(),
    )
