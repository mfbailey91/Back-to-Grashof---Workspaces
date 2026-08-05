"""Path and sample types for sequential fixed-position continuation.

Conventions
-----------
Chart coordinates ``(s, t)`` parameterize sequential predictor-corrector
steps on ``p(q)=p0`` with ``q6`` frozen. Joint order is ``(q1,...,q6)``
in radians. Pointing ``d`` is the unit terminal axis in the space frame.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Mat = NDArray[np.floating]


@dataclass(frozen=True, slots=True)
class TransportedTangentFrame:
    """Orthonormal reduced tangent frame aligned to the previous accepted step."""

    q: tuple[float, ...]
    basis: tuple[tuple[float, ...], tuple[float, ...]]
    principal_angles_rad: tuple[float, ...]

    def as_matrix(self) -> Mat:
        return np.column_stack(
            [np.asarray(self.basis[0], dtype=float), np.asarray(self.basis[1], dtype=float)]
        )


@dataclass(frozen=True, slots=True)
class ContinuationStep:
    """One attempted sequential predictor-corrector step."""

    s: float
    t: float
    path_id: str
    step_index: int
    q_pred: tuple[float, ...] | None
    q: tuple[float, ...] | None
    d: tuple[float, float, float] | None
    p_residual_m: float
    corrector_iterations: int
    correction_norm: float
    step_reductions: int
    rank_jp: int
    rank_jpd: int
    rank_jd_nred: int
    tangent_principal_angle_1: float
    tangent_principal_angle_2: float
    regular: bool
    label: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class ContinuationPath:
    path_id: str
    steps: tuple[ContinuationStep, ...]

    @property
    def accepted(self) -> tuple[ContinuationStep, ...]:
        return tuple(step for step in self.steps if step.accepted)

    @property
    def rejected(self) -> tuple[ContinuationStep, ...]:
        return tuple(step for step in self.steps if not step.accepted)


@dataclass(frozen=True, slots=True)
class ChartSample:
    s: float
    t: float
    path_id: str
    step_index: int
    q: tuple[float, ...]
    d: tuple[float, float, float]
    p_residual_m: float
    corrector_iterations: int
    correction_norm: float
    step_reductions: int
    rank_jp: int
    rank_jpd: int
    rank_jd_nred: int
    tangent_principal_angle_1: float
    tangent_principal_angle_2: float
    regular: bool
    label: str
