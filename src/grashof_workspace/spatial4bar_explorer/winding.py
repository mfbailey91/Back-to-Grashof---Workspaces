from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .cycle_continuation import CycleTrace, continue_until_return_bidirectional, unwrap_angles
from .families import FAMILY_AXIS_CASES
from .geometry import PhysicalGeometrySample, SpatialFourBarGeometry
from .models import BranchClass, BranchResult, ExplorerCase, OrderedFamily, ToolAxis

Array = np.ndarray


def compute_windings(
    unwrapped_q: Array,
    coordinate_names: tuple[str, ...],
) -> tuple[int | None, int | None]:
    """Return (w_alpha, w_beta) = round(Δθ̃ / 2π) from an unwrapped cycle series."""
    values = np.asarray(unwrapped_q, dtype=float)
    if values.ndim != 2 or values.shape[0] < 2:
        return None, None
    names = list(coordinate_names)
    alpha_index = names.index("tool_alpha")
    beta_index = names.index("tool_beta")
    delta = values[-1] - values[0]
    two_pi = 2.0 * math.pi
    w_alpha = round(float(delta[alpha_index]) / two_pi)
    w_beta = round(float(delta[beta_index]) / two_pi)
    return w_alpha, w_beta


def classify_tool_axis(
    winding: int | None,
    *,
    returned: bool,
    status: str,
) -> BranchClass:
    """Link-specific full-rotation test for one tool-U coordinate."""
    if status == "invalid":
        return BranchClass.INVALID
    if status == "change_point":
        return BranchClass.CHANGE_POINT
    if not returned or winding is None:
        return BranchClass.OPEN_BRANCH
    if abs(winding) >= 1:
        return BranchClass.CRANK
    return BranchClass.ROCKER


def tool_ranges(unwrapped_q: Array, coordinate_names: tuple[str, ...]) -> tuple[float | None, float | None]:
    values = np.asarray(unwrapped_q, dtype=float)
    if values.ndim != 2 or values.shape[0] == 0:
        return None, None
    names = list(coordinate_names)
    alpha = values[:, names.index("tool_alpha")]
    beta = values[:, names.index("tool_beta")]
    return float(alpha.max() - alpha.min()), float(beta.max() - beta.min())


@dataclass(frozen=True)
class WindingClassification:
    sample_id: str
    family: str
    cycle: CycleTrace
    w_alpha: int | None
    w_beta: int | None
    class_alpha: BranchClass
    class_beta: BranchClass
    tool_range_alpha: float | None
    tool_range_beta: float | None
    notes: tuple[str, ...]

    def branch_results(self) -> tuple[BranchResult, BranchResult]:
        """Emit one BranchResult per tool-axis explorer case (same mechanism solve)."""
        notes = list(self.notes)
        alpha_case = ExplorerCase(family=OrderedFamily(self.family), tool_axis=ToolAxis.A)
        beta_case = ExplorerCase(family=OrderedFamily(self.family), tool_axis=ToolAxis.B)
        return (
            BranchResult(
                sample_id=self.sample_id,
                case=alpha_case,
                branch_id=f"{self.sample_id}_cycle_d{self.cycle.direction}",
                branch_closed=self.cycle.returned,
                singularity_count=1 if self.cycle.status == "change_point" else 0,
                w_alpha=self.w_alpha,
                w_beta=self.w_beta,
                class_alpha=self.class_alpha,
                class_beta=self.class_beta,
                tool_range_alpha=self.tool_range_alpha,
                tool_range_beta=self.tool_range_beta,
                notes=[*notes, "tool_axis=a"],
            ),
            BranchResult(
                sample_id=self.sample_id,
                case=beta_case,
                branch_id=f"{self.sample_id}_cycle_d{self.cycle.direction}",
                branch_closed=self.cycle.returned,
                singularity_count=1 if self.cycle.status == "change_point" else 0,
                w_alpha=self.w_alpha,
                w_beta=self.w_beta,
                class_alpha=self.class_alpha,
                class_beta=self.class_beta,
                tool_range_alpha=self.tool_range_alpha,
                tool_range_beta=self.tool_range_beta,
                notes=[*notes, "tool_axis=b"],
            ),
        )


def classify_cycle(sample_id: str, cycle: CycleTrace) -> WindingClassification:
    unwrapped = np.asarray(cycle.unwrapped_q, dtype=float)
    if cycle.returned:
        w_alpha, w_beta = compute_windings(unwrapped, cycle.coordinate_names)
    else:
        w_alpha, w_beta = None, None
    class_alpha = classify_tool_axis(w_alpha, returned=cycle.returned, status=cycle.status)
    class_beta = classify_tool_axis(w_beta, returned=cycle.returned, status=cycle.status)
    range_alpha, range_beta = tool_ranges(unwrapped, cycle.coordinate_names)
    notes = [
        f"cycle_status={cycle.status}",
        f"direction={cycle.direction}",
        f"points={len(cycle.points)}",
        "source=continued_branch_winding",
    ]
    return WindingClassification(
        sample_id=sample_id,
        family=cycle.family,
        cycle=cycle,
        w_alpha=w_alpha,
        w_beta=w_beta,
        class_alpha=class_alpha,
        class_beta=class_beta,
        tool_range_alpha=range_alpha,
        tool_range_beta=range_beta,
        notes=tuple(notes),
    )


def classify_physical_sample(
    sample: PhysicalGeometrySample,
    *,
    step_size: float = 0.05,
    max_steps: int = 2000,
    leave_tol: float = 0.35,
    return_tol: float = 0.08,
) -> WindingClassification:
    cycle = continue_until_return_bidirectional(
        sample.geometry,
        step_size=step_size,
        max_steps=max_steps,
        leave_tol=leave_tol,
        return_tol=return_tol,
    )
    return classify_cycle(sample.sample_id, cycle)


def classify_geometry(
    geometry: SpatialFourBarGeometry,
    *,
    sample_id: str,
    step_size: float = 0.05,
    max_steps: int = 2000,
) -> WindingClassification:
    cycle = continue_until_return_bidirectional(
        geometry, step_size=step_size, max_steps=max_steps
    )
    return classify_cycle(sample_id, cycle)


def select_crank_and_rocker_examples(
    classifications: list[WindingClassification],
) -> tuple[WindingClassification | None, WindingClassification | None]:
    """Pick one sample showing a crank tool axis and one showing a rocker tool axis."""
    crank_example: WindingClassification | None = None
    rocker_example: WindingClassification | None = None
    for item in classifications:
        if (
            rocker_example is None
            and (item.class_alpha is BranchClass.ROCKER or item.class_beta is BranchClass.ROCKER)
            and item.class_alpha is not BranchClass.CRANK
            and item.class_beta is not BranchClass.CRANK
        ):
            rocker_example = item
    for item in classifications:
        if crank_example is None and (
            item.class_alpha is BranchClass.CRANK or item.class_beta is BranchClass.CRANK
        ):
            crank_example = item
        if rocker_example is None and (
            item.class_alpha is BranchClass.ROCKER or item.class_beta is BranchClass.ROCKER
        ):
            rocker_example = item
        if crank_example is not None and rocker_example is not None:
            break
    return crank_example, rocker_example


def uuur_cases() -> tuple[ExplorerCase, ...]:
    return tuple(case for case in FAMILY_AXIS_CASES if case.family is OrderedFamily.UUUR)


# Re-export unwrap for tests / callers that import from winding.
__all__ = [
    "WindingClassification",
    "classify_cycle",
    "classify_geometry",
    "classify_physical_sample",
    "classify_tool_axis",
    "compute_windings",
    "select_crank_and_rocker_examples",
    "tool_ranges",
    "unwrap_angles",
    "uuur_cases",
]
