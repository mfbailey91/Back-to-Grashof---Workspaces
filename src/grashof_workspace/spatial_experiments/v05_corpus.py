"""Synthetic spatial-4R corpus for the V05 fixed-position program.

Conventions
-----------
All models are ``SerialRevoluteChain`` instances with four home axes in world
frame ``W``. Task point ``p0`` and pointing ``d0`` are expressed in ``W``.
No URDF import.

The active regular cases deliberately place the tool origin *off* the terminal
axis.  This prevents the one-dimensional fixed-position nullspace from
collapsing to the trivial terminal-roll direction ``e4``.  A separate
``terminal_roll_control_4r`` retains the on-axis special case as a regression
control.

``exact_u_pair_4r`` plants an exact consecutive intersecting orthogonal pair
(V05D). ``near_aligned_u_pair_4r`` is an intentional near-miss that must be
rejected as exact ``U`` (V05E).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .aligned_6r import frame_from_pointing
from .axis_geometry import (
    AxisLine,
    as_mat3,
    as_vec3,
    line_line_distance,
    parallelism_residual,
    point_axis_distance,
)
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

GENERIC_4R_REGULAR_Q = (0.40, -0.35, 0.55, -0.25)
EXACT_U_PAIR_REGULAR_Q = (0.30, -0.45, 0.50, 0.20)
NEAR_ALIGNED_U_PAIR_REGULAR_Q = (0.30, -0.45, 0.50, 0.20)
TERMINAL_ROLL_CONTROL_Q = GENERIC_4R_REGULAR_Q
SINGULAR_4R_Q = (0.0, 0.0, 0.0, 0.0)

# Active V05 cases: nonzero transverse tool offset excites coupled source motion.
ACTIVE_TOOL_TRANSVERSE_OFFSET_M = 0.06
ACTIVE_TOOL_AXIAL_OFFSET_M = 0.05
TERMINAL_ROLL_TRANSVERSE_OFFSET_M = 0.0

# Planted near-miss relative to exact_u_pair_4r (well outside exact tolerances).
# This remains the easy exterior control; tolerance-relative cases belong in V05E.
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
    """Near-miss of exact_u_pair: common-perpendicular offset + tilt of R2."""
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


def _stable_transverse(last: AxisLine) -> np.ndarray:
    """Return a deterministic unit direction perpendicular to ``last.w``."""
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
    """Build a chain with a controlled terminal-axis tool offset.

    ``transverse_offset_m > 0`` creates the active nontrivial V05 geometry.
    ``transverse_offset_m == 0`` is the aligned terminal-roll control.
    The pointing direction remains aligned with the terminal axis so V05 can
    distinguish changing pointing caused by coupled upstream motion from the
    explicit roll symmetry of the terminal joint itself.
    """
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
    return SerialRevoluteChain(home_axes=axes, p0=p0, d0=d0, R0=as_mat3(np.asarray(frame_from_pointing(d0), dtype=float)))


@dataclass(frozen=True, slots=True)
class Spatial4RCorpusEntry:
    """Named corpus member with a default seed and expected curve behavior."""

    model: OpenChainModel
    regular_q: tuple[float, ...]
    expected_regular: bool
    expected_curve_type: str
    terminal_axis_offset_m: float


def _entry(
    *,
    architecture_id: str,
    axes: tuple[AxisLine, ...],
    regular_q: tuple[float, ...],
    expected_regular: bool,
    expected_curve_type: str,
    transverse_offset_m: float,
    notes: tuple[str, ...],
    axial_offset_m: float = ACTIVE_TOOL_AXIAL_OFFSET_M,
) -> Spatial4RCorpusEntry:
    chain = _chain_from_axes(
        axes,
        axial_offset_m=axial_offset_m,
        transverse_offset_m=transverse_offset_m,
    )
    axis_distance = point_axis_distance(chain.p0, axes[-1])
    model = OpenChainModel(
        architecture_id=architecture_id,
        chain=chain,
        joint_kind_sequence=_r_kinds(4),
        joint_role_sequence=_r_phys_roles(4),
        notes=(
            *notes,
            f"terminal_tool_axis_distance_m={axis_distance:.6e}",
            f"expected_curve_type={expected_curve_type}",
        ),
    )
    return Spatial4RCorpusEntry(
        model=model,
        regular_q=regular_q,
        expected_regular=expected_regular,
        expected_curve_type=expected_curve_type,
        terminal_axis_offset_m=axis_distance,
    )


def build_generic_4r() -> Spatial4RCorpusEntry:
    """Nontrivial generic 4R source: the tool point is off the final axis."""
    return _entry(
        architecture_id="generic_4r",
        axes=generic_4r_home_axes(),
        regular_q=GENERIC_4R_REGULAR_Q,
        expected_regular=True,
        expected_curve_type="NONTRIVIAL_POINTING_CURVE",
        transverse_offset_m=ACTIVE_TOOL_TRANSVERSE_OFFSET_M,
        notes=("No intentional consecutive intersecting pairs.",),
    )


def build_terminal_roll_control_4r() -> Spatial4RCorpusEntry:
    """Special-case control whose fixed-position nullspace is terminal roll."""
    return _entry(
        architecture_id="terminal_roll_control_4r",
        axes=generic_4r_home_axes(),
        regular_q=TERMINAL_ROLL_CONTROL_Q,
        expected_regular=True,
        expected_curve_type="PURE_TERMINAL_ROLL",
        transverse_offset_m=TERMINAL_ROLL_TRANSVERSE_OFFSET_M,
        notes=(
            "Tool origin lies on R4 and pointing is collinear with R4.",
            "Expected fixed-position tangent is the explicit terminal-roll direction e4.",
        ),
    )


def build_exact_u_pair_4r() -> Spatial4RCorpusEntry:
    axes = exact_u_pair_4r_home_axes()
    dist = line_line_distance(axes[0], axes[1])
    par = parallelism_residual(axes[0].w, axes[1].w)
    return _entry(
        architecture_id="exact_u_pair_4r",
        axes=axes,
        regular_q=EXACT_U_PAIR_REGULAR_Q,
        expected_regular=True,
        expected_curve_type="NONTRIVIAL_POINTING_CURVE",
        transverse_offset_m=ACTIVE_TOOL_TRANSVERSE_OFFSET_M,
        notes=(
            "Exact consecutive orthogonal intersecting RR at J1/J2 (U_phys candidate).",
            "Aggregation geometry certificate is issued by V05D; closed-mechanism equivalence is separate.",
            f"pair_distance={dist:.3e}, pair_parallelism={par:.3e}",
        ),
    )


def build_near_aligned_u_pair_4r() -> Spatial4RCorpusEntry:
    axes = near_aligned_u_pair_4r_home_axes()
    dist = line_line_distance(axes[0], axes[1])
    par = parallelism_residual(axes[0].w, axes[1].w)
    dot = abs(float(np.dot(np.asarray(axes[0].w, dtype=float), np.asarray(axes[1].w, dtype=float))))
    return _entry(
        architecture_id="near_aligned_u_pair_4r",
        axes=axes,
        regular_q=NEAR_ALIGNED_U_PAIR_REGULAR_Q,
        expected_regular=True,
        expected_curve_type="NONTRIVIAL_POINTING_CURVE",
        transverse_offset_m=ACTIVE_TOOL_TRANSVERSE_OFFSET_M,
        notes=(
            "Intentional near-miss of exact RR→U at J1/J2; must not be treated as exact U_phys.",
            "V05E rejection + false-U surrogate task-error diagnostic.",
            f"pair_distance={dist:.3e}, pair_parallelism={par:.3e}, |w·w'|={dot:.3e}",
            f"planted_miss_m={NEAR_ALIGNED_MISS_M:.3e}, planted_tilt_rad={NEAR_ALIGNED_TILT_RAD:.3e}",
        ),
    )


def build_singular_4r() -> Spatial4RCorpusEntry:
    return _entry(
        architecture_id="singular_4r_parallel",
        axes=singular_4r_home_axes(),
        regular_q=SINGULAR_4R_Q,
        expected_regular=False,
        expected_curve_type="SINGULAR_OR_EMPTY",
        transverse_offset_m=ACTIVE_TOOL_TRANSVERSE_OFFSET_M,
        axial_offset_m=0.08,
        notes=("All axes parallel; exterior / rank-deficient counterexample.",),
    )


def v05a_spatial_4r_corpus() -> tuple[Spatial4RCorpusEntry, ...]:
    """Return active V05 sources plus the explicit terminal-roll control."""
    return (
        build_generic_4r(),
        build_terminal_roll_control_4r(),
        build_exact_u_pair_4r(),
        build_near_aligned_u_pair_4r(),
        build_singular_4r(),
    )
