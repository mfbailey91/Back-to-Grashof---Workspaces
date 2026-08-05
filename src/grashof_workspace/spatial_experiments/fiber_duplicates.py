"""Pairwise wrap-distance duplicate scan on one-dimensional fibers.

Conventions
-----------
Distinct accepted stations satisfy ``|σ_i - σ_j| > 1e-12``. A duplicate is a
wrap-aware joint distance at or below ``1e-6`` rad. This scan is independent of
the two-dimensional chart ``duplicate_report``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .continuation import wrap_joint_delta
from .fiber_continuation import FiberSegment, FiberStep

SIGMA_DISTINCT_TOL = 1e-12
DUPLICATE_TOL_RAD = 1e-6


@dataclass(frozen=True, slots=True)
class FiberDuplicateReport:
    n_stations: int
    n_pairs_checked: int
    n_duplicates: int
    min_nn_distance: float
    duplicate_pairs: tuple[tuple[float, float, float], ...]
    passed: bool


def fiber_duplicate_report(
    steps: tuple[FiberStep, ...] | list[FiberStep] | FiberSegment,
    *,
    tol_rad: float = DUPLICATE_TOL_RAD,
    sigma_tol: float = SIGMA_DISTINCT_TOL,
) -> FiberDuplicateReport:
    """Return the all-pairs wrap-distance duplicate report.

    Interior: distinct configurations at distinct ``σ`` pass.
    Exterior: wrap-equivalent repeats at distinct ``σ`` fail.
    Boundary: ``||Δq|| = tol_rad`` counts as a duplicate.
    """
    if isinstance(steps, FiberSegment):
        items = [step for step in steps.accepted_samples if step.q is not None]
    else:
        items = [step for step in steps if step.accepted and step.q is not None]
    pairs: list[tuple[float, float, float]] = []
    nearest = float("inf")
    checked = 0
    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            if abs(left.sigma - right.sigma) <= sigma_tol:
                continue
            checked += 1
            dist = float(np.linalg.norm(wrap_joint_delta(left.q, right.q)))
            nearest = min(nearest, dist)
            if dist <= tol_rad:
                pairs.append((left.sigma, right.sigma, dist))
    return FiberDuplicateReport(
        n_stations=len(items),
        n_pairs_checked=checked,
        n_duplicates=len(pairs),
        min_nn_distance=0.0 if checked == 0 else nearest,
        duplicate_pairs=tuple(pairs),
        passed=len(pairs) == 0 and checked > 0,
    )
