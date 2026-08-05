"""Generic synthetic aligned-terminal 6R model.

Home axes are deliberately skew (no designed spherical wrist or shoulder).
The task point lies on home ``R6`` and the pointing direction is parallel to
``w6``. Configurations are joint vectors in radians; no IK is performed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .axis_geometry import AxisLine, parallelism_residual, point_axis_distance, unit_vector
from .serial_chain import SerialRevoluteChain

REGULAR_Q = (0.35, -0.42, 0.55, 0.28, -0.33, 0.70)
SINGULAR_SEARCH_SEED = 17


def _frame_from_pointing(d: tuple[float, float, float]) -> tuple[tuple[float, float, float], ...]:
    z = unit_vector(d, name="pointing")
    helper = np.array([1.0, 0.0, 0.0], dtype=float)
    if abs(float(np.dot(helper, z))) > 0.9:
        helper = np.array([0.0, 1.0, 0.0], dtype=float)
    x = np.cross(helper, z)
    x = x / float(np.linalg.norm(x))
    y = np.cross(z, x)
    R = np.column_stack([x, y, z])
    return tuple(tuple(float(R[i, j]) for j in range(3)) for i in range(3))


def generic_home_axes() -> tuple[AxisLine, ...]:
    """Return six deterministic generically skew home axes in ``W``."""
    return (
        AxisLine((0.00, 0.00, 0.00), (0.00, 0.00, 1.00)),
        AxisLine((0.08, 0.03, 0.26), (1.00, 0.18, 0.06)),
        AxisLine((0.24, -0.07, 0.47), (0.22, 1.00, 0.14)),
        AxisLine((0.41, 0.11, 0.57), (-0.12, 0.33, 1.00)),
        AxisLine((0.53, -0.13, 0.71), (1.00, -0.22, 0.16)),
        AxisLine((0.58, 0.02, 0.78), (0.12, 0.08, 1.00)),
    )


@dataclass(frozen=True, slots=True)
class GenericAligned6R:
    """Aligned-terminal generic 6R built from explicit home axes."""

    chain: SerialRevoluteChain
    task_point: tuple[float, float, float]
    is_aligned: bool

    @classmethod
    def aligned(cls) -> GenericAligned6R:
        axes = generic_home_axes()
        r6 = np.asarray(axes[5].r, dtype=float)
        w6 = np.asarray(axes[5].w, dtype=float)
        p0 = tuple(float(x) for x in (r6 + 0.04 * w6))
        d0 = tuple(float(x) for x in w6)
        chain = SerialRevoluteChain(home_axes=axes, p0=p0, d0=d0, R0=_frame_from_pointing(d0))
        return cls(chain=chain, task_point=p0, is_aligned=True)

    @classmethod
    def off_axis_task_point(cls, offset_m: float = 0.03) -> GenericAligned6R:
        base = cls.aligned()
        w6 = np.asarray(base.chain.home_axes[5].w, dtype=float)
        helper = np.array([1.0, 0.0, 0.0], dtype=float)
        if abs(float(np.dot(helper, w6))) > 0.9:
            helper = np.array([0.0, 1.0, 0.0], dtype=float)
        transverse = np.cross(w6, helper)
        transverse = transverse / float(np.linalg.norm(transverse))
        p0 = tuple(float(x) for x in (np.asarray(base.task_point) + offset_m * transverse))
        chain = SerialRevoluteChain(
            home_axes=base.chain.home_axes,
            p0=p0,
            d0=base.chain.d0,
            R0=base.chain.R0,
        )
        return cls(chain=chain, task_point=p0, is_aligned=False)

    @classmethod
    def misaligned_pointing(cls, tilt_rad: float = 0.25) -> GenericAligned6R:
        base = cls.aligned()
        w6 = np.asarray(base.chain.home_axes[5].w, dtype=float)
        helper = np.array([1.0, 0.0, 0.0], dtype=float)
        if abs(float(np.dot(helper, w6))) > 0.9:
            helper = np.array([0.0, 1.0, 0.0], dtype=float)
        transverse = np.cross(w6, helper)
        transverse = transverse / float(np.linalg.norm(transverse))
        d0_vec = np.cos(tilt_rad) * w6 + np.sin(tilt_rad) * transverse
        d0 = tuple(float(x) for x in d0_vec)
        R0 = _frame_from_pointing(d0)
        chain = SerialRevoluteChain(
            home_axes=base.chain.home_axes,
            p0=base.task_point,
            d0=d0,
            R0=R0,
        )
        return cls(chain=chain, task_point=base.task_point, is_aligned=False)

    def home_alignment_residuals(self) -> tuple[float, float]:
        axis6 = self.chain.home_axes[5]
        dist = point_axis_distance(self.task_point, axis6)
        par = parallelism_residual(self.chain.d0, axis6.w)
        return dist, par
