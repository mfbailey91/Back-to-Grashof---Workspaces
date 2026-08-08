"""Minimal continuation helpers shared by the pointing-fiber kernel.

V05A restores only the constants and angle-wrap utilities required by
``fiber_continuation``. The full fixed-position manifold continuation stack
from ``spherical_framework`` is intentionally not ported here.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

Vec = NDArray[np.floating]

POSITION_RESIDUAL_TOL_M = 1e-10
MAX_CORRECTOR_ITERS = 20
MAX_STEP_REDUCTIONS = 3
MAX_CORRECTION_NORM_RAD = 0.5
MAX_MICROSTEP = 0.005


def wrap_angle(delta: float) -> float:
    return float((delta + np.pi) % (2.0 * np.pi) - np.pi)


def wrap_joint_delta(q_a: tuple[float, ...] | Vec, q_b: tuple[float, ...] | Vec) -> Vec:
    delta = np.asarray(q_a, dtype=float).reshape(-1) - np.asarray(q_b, dtype=float).reshape(-1)
    return np.array([wrap_angle(float(x)) for x in delta], dtype=float)
