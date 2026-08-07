from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .closure import closure_jacobian, closure_residual, null_tangent, scalar_axes
from .geometry import SpatialFourBarGeometry

Array = np.ndarray


@dataclass(frozen=True)
class ContinuationPoint:
    step_index: int
    arclength: float
    q: tuple[float, ...]
    closure_norm: float
    smallest_singular_value: float
    converged: bool
    newton_iterations: int


@dataclass(frozen=True)
class ContinuationTrace:
    family: str
    coordinate_names: tuple[str, ...]
    points: tuple[ContinuationPoint, ...]
    step_size: float
    direction: int

    @property
    def converged_fraction(self) -> float:
        if not self.points:
            return 0.0
        return sum(point.converged for point in self.points) / len(self.points)


def _corrector(
    geometry: SpatialFourBarGeometry,
    q_initial: Array,
    q_predictor: Array,
    tangent: Array,
    *,
    tolerance: float,
    max_iterations: int,
) -> tuple[Array, bool, int]:
    q = q_initial.copy()
    for iteration in range(1, max_iterations + 1):
        residual = closure_residual(geometry, q)
        arc_residual = float(np.dot(tangent, q - q_predictor))
        augmented = np.concatenate((residual, np.array((arc_residual,))))
        if float(np.linalg.norm(augmented)) < tolerance:
            return q, True, iteration
        jacobian = closure_jacobian(geometry, q)
        augmented_jacobian = np.vstack((jacobian, tangent))
        delta, *_ = np.linalg.lstsq(augmented_jacobian, -augmented, rcond=None)
        q = q + delta
        if float(np.linalg.norm(delta)) < tolerance * 0.1:
            if float(np.linalg.norm(closure_residual(geometry, q))) < tolerance * 10.0:
                return q, True, iteration
    return q, False, max_iterations


def continue_branch(
    geometry: SpatialFourBarGeometry,
    *,
    step_size: float = 0.04,
    steps: int = 60,
    direction: int = 1,
    tolerance: float = 1e-10,
    max_iterations: int = 12,
) -> ContinuationTrace:
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or +1")
    coordinate_names = tuple(axis.name for axis in scalar_axes(geometry))
    q = np.zeros(len(coordinate_names), dtype=float)
    jacobian = closure_jacobian(geometry, q)
    tangent, singular_values = null_tangent(jacobian)
    tangent *= float(direction)
    points: list[ContinuationPoint] = [
        ContinuationPoint(
            step_index=0,
            arclength=0.0,
            q=tuple(float(value) for value in q),
            closure_norm=float(np.linalg.norm(closure_residual(geometry, q))),
            smallest_singular_value=float(singular_values[-1]),
            converged=True,
            newton_iterations=0,
        )
    ]
    for step_index in range(1, steps + 1):
        q_predictor = q + step_size * tangent
        q_candidate, converged, iterations = _corrector(
            geometry,
            q_predictor,
            q_predictor,
            tangent,
            tolerance=tolerance,
            max_iterations=max_iterations,
        )
        if not converged:
            points.append(
                ContinuationPoint(
                    step_index=step_index,
                    arclength=step_index * step_size,
                    q=tuple(float(value) for value in q_candidate),
                    closure_norm=float(np.linalg.norm(closure_residual(geometry, q_candidate))),
                    smallest_singular_value=0.0,
                    converged=False,
                    newton_iterations=iterations,
                )
            )
            break
        q = q_candidate
        jacobian = closure_jacobian(geometry, q)
        next_tangent, singular_values = null_tangent(jacobian, previous=tangent)
        tangent = next_tangent
        points.append(
            ContinuationPoint(
                step_index=step_index,
                arclength=step_index * step_size,
                q=tuple(float(value) for value in q),
                closure_norm=float(np.linalg.norm(closure_residual(geometry, q))),
                smallest_singular_value=float(singular_values[-1]),
                converged=True,
                newton_iterations=iterations,
            )
        )
    return ContinuationTrace(
        family=geometry.family.value,
        coordinate_names=coordinate_names,
        points=tuple(points),
        step_size=step_size,
        direction=direction,
    )
