from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .closure import closure_jacobian, closure_residual, null_tangent, scalar_axes
from .continuation import ContinuationPoint, ContinuationTrace, _corrector
from .geometry import SpatialFourBarGeometry

Array = np.ndarray


@dataclass(frozen=True)
class CycleTrace:
    """One continued attempt to return to the reference assembly.

    Conventions:
    - ``q`` on each point is the solver chart used by the corrector (may drift by 2π).
    - ``unwrapped_q`` is the continuous chart used for winding.
    - ``returned`` is true only after leaving ``leave_tol`` and re-entering ``return_tol``.
    """

    family: str
    coordinate_names: tuple[str, ...]
    points: tuple[ContinuationPoint, ...]
    unwrapped_q: tuple[tuple[float, ...], ...]
    step_size: float
    direction: int
    returned: bool
    leave_index: int | None
    return_index: int | None
    status: str

    def as_continuation_trace(self) -> ContinuationTrace:
        return ContinuationTrace(
            family=self.family,
            coordinate_names=self.coordinate_names,
            points=self.points,
            step_size=self.step_size,
            direction=self.direction,
        )


def wrapped_configuration_distance(q: Array, q_ref: Array | None = None) -> float:
    """Euclidean distance after wrapping each coordinate into (-π, π]."""
    reference = np.zeros_like(q) if q_ref is None else np.asarray(q_ref, dtype=float)
    delta = np.asarray(q, dtype=float) - reference
    wrapped = np.mod(delta + math.pi, 2.0 * math.pi) - math.pi
    return float(np.linalg.norm(wrapped))


def unwrap_angles(series: Array) -> Array:
    """Nearest-2π unwrap along axis 0 for each coordinate column.

    Named recurrence (docs/SPRINT_V04_WINDING_AND_CRANK_ATLAS.md):
    Δ_k = θ_k − θ_{k−1},  θ̃_k = θ̃_{k−1} + (Δ_k − 2π round(Δ_k / 2π)).
    """
    values = np.asarray(series, dtype=float)
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    if values.shape[0] == 0:
        return values.copy()
    unwrapped = np.empty_like(values)
    unwrapped[0] = values[0]
    two_pi = 2.0 * math.pi
    for index in range(1, values.shape[0]):
        delta = values[index] - values[index - 1]
        delta -= two_pi * np.round(delta / two_pi)
        unwrapped[index] = unwrapped[index - 1] + delta
    return unwrapped


def _append_point(
    points: list[ContinuationPoint],
    *,
    step_index: int,
    arclength: float,
    q: Array,
    geometry: SpatialFourBarGeometry,
    singular_value: float,
    converged: bool,
    newton_iterations: int,
) -> None:
    points.append(
        ContinuationPoint(
            step_index=step_index,
            arclength=arclength,
            q=tuple(float(value) for value in q),
            closure_norm=float(np.linalg.norm(closure_residual(geometry, q))),
            smallest_singular_value=float(singular_value),
            converged=converged,
            newton_iterations=newton_iterations,
        )
    )


def continue_until_return(
    geometry: SpatialFourBarGeometry,
    *,
    step_size: float = 0.05,
    max_steps: int = 2000,
    direction: int = 1,
    leave_tol: float = 0.35,
    return_tol: float = 0.08,
    tolerance: float = 1e-10,
    max_iterations: int = 12,
    singularity_tol: float = 1e-4,
) -> CycleTrace:
    """Pseudo-arclength continue until wrapped return to q=0, or budget exhausted."""
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or +1")
    coordinate_names = tuple(axis.name for axis in scalar_axes(geometry))
    q = np.zeros(len(coordinate_names), dtype=float)
    jacobian = closure_jacobian(geometry, q)
    tangent, singular_values = null_tangent(jacobian)
    tangent *= float(direction)
    points: list[ContinuationPoint] = []
    _append_point(
        points,
        step_index=0,
        arclength=0.0,
        q=q,
        geometry=geometry,
        singular_value=float(singular_values[-1]),
        converged=True,
        newton_iterations=0,
    )
    left = False
    leave_index: int | None = None
    return_index: int | None = None
    status = "open_branch"
    for step_index in range(1, max_steps + 1):
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
            _append_point(
                points,
                step_index=step_index,
                arclength=step_index * step_size,
                q=q_candidate,
                geometry=geometry,
                singular_value=0.0,
                converged=False,
                newton_iterations=iterations,
            )
            status = "invalid"
            break
        q = q_candidate
        jacobian = closure_jacobian(geometry, q)
        next_tangent, singular_values = null_tangent(jacobian, previous=tangent)
        if float(singular_values[-1]) < singularity_tol:
            _append_point(
                points,
                step_index=step_index,
                arclength=step_index * step_size,
                q=q,
                geometry=geometry,
                singular_value=float(singular_values[-1]),
                converged=True,
                newton_iterations=iterations,
            )
            status = "change_point"
            break
        tangent = next_tangent
        _append_point(
            points,
            step_index=step_index,
            arclength=step_index * step_size,
            q=q,
            geometry=geometry,
            singular_value=float(singular_values[-1]),
            converged=True,
            newton_iterations=iterations,
        )
        distance = wrapped_configuration_distance(q)
        if not left and distance > leave_tol:
            left = True
            leave_index = step_index
            continue
        if left and distance < return_tol:
            return_index = step_index
            status = "returned"
            break

    raw = np.asarray([point.q for point in points], dtype=float)
    unwrapped = unwrap_angles(raw)
    return CycleTrace(
        family=geometry.family.value,
        coordinate_names=coordinate_names,
        points=tuple(points),
        unwrapped_q=tuple(tuple(float(value) for value in row) for row in unwrapped),
        step_size=step_size,
        direction=direction,
        returned=status == "returned",
        leave_index=leave_index,
        return_index=return_index,
        status=status,
    )


def continue_until_return_bidirectional(
    geometry: SpatialFourBarGeometry,
    *,
    step_size: float = 0.05,
    max_steps: int = 2000,
    leave_tol: float = 0.35,
    return_tol: float = 0.08,
    tolerance: float = 1e-10,
    max_iterations: int = 12,
    singularity_tol: float = 1e-4,
) -> CycleTrace:
    """Try +1 direction first; if no return, try −1 once."""
    primary = continue_until_return(
        geometry,
        step_size=step_size,
        max_steps=max_steps,
        direction=1,
        leave_tol=leave_tol,
        return_tol=return_tol,
        tolerance=tolerance,
        max_iterations=max_iterations,
        singularity_tol=singularity_tol,
    )
    if primary.returned:
        return primary
    secondary = continue_until_return(
        geometry,
        step_size=step_size,
        max_steps=max_steps,
        direction=-1,
        leave_tol=leave_tol,
        return_tol=return_tol,
        tolerance=tolerance,
        max_iterations=max_iterations,
        singularity_tol=singularity_tol,
    )
    if secondary.returned:
        return secondary
    primary_len = sum(point.converged for point in primary.points)
    secondary_len = sum(point.converged for point in secondary.points)
    return primary if primary_len >= secondary_len else secondary
