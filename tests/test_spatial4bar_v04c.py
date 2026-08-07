from __future__ import annotations

from grashof_workspace.spatial4bar_explorer.v04b import OrientationSweepRun
from grashof_workspace.spatial4bar_explorer.v04c import (
    BudgetResolutionRun,
    budget_resolution_label,
    compare_axis_order_symmetry,
    compare_half_turn_periodicity,
    transition_intervals,
)


def _row(
    phi: float,
    *,
    order: str = "ab",
    status: str = "returned",
    wa: int | None = -1,
    wb: int | None = 0,
    ca: str = "crank",
    cb: str = "rocker",
    cov_a: float | None = 1.0,
    cov_b: float | None = 0.3,
) -> OrientationSweepRun:
    return OrientationSweepRun(
        phi_deg=phi,
        axis_order=order,
        audit_status="PASS",
        jacobian_rank=6,
        jacobian_nullity=1,
        returned=status == "returned",
        status=status,
        w_alpha=wa,
        w_beta=wb,
        class_alpha=ca,
        class_beta=cb,
        coverage_alpha=cov_a,
        coverage_beta=cov_b,
        points=100,
    )


def test_axis_order_symmetry_applies_shift_and_beta_sign() -> None:
    ab = [
        _row(90.0, wa=-1, wb=0),
        _row(150.0, wa=0, wb=-1, ca="rocker", cb="crank", cov_a=0.4, cov_b=1.0),
    ]
    ba = [
        _row(0.0, order="ba", wa=-1, wb=0),
        _row(60.0, order="ba", wa=0, wb=1, ca="rocker", cb="crank", cov_a=0.4, cov_b=1.0),
    ]
    rows = compare_axis_order_symmetry(ab, ba)
    assert len(rows) == 2
    assert all(row.passed for row in rows)


def test_half_turn_periodicity_uses_winding_magnitude() -> None:
    rows = [
        _row(0.0, wa=-1, wb=0),
        _row(180.0, wa=1, wb=0),
    ]
    comparisons = compare_half_turn_periodicity(rows)
    assert len(comparisons) == 1
    assert comparisons[0].passed


def test_budget_resolution_distinguishes_late_return() -> None:
    rows = [
        BudgetResolutionRun(
            120.0,
            "ab",
            1600,
            False,
            "open_branch",
            None,
            None,
            "open_branch",
            "open_branch",
            1601,
        ),
        BudgetResolutionRun(120.0, "ab", 3200, True, "returned", -1, 0, "crank", "rocker", 2200),
    ]
    assert budget_resolution_label(rows) == "budget_limited_return"


def test_transition_intervals_only_select_state_changes() -> None:
    rows = [
        _row(0.0, ca="crank", cb="rocker"),
        _row(30.0, wa=0, wb=0, ca="rocker", cb="rocker"),
        _row(60.0, wa=0, wb=0, ca="rocker", cb="rocker"),
        _row(90.0, wa=0, wb=-1, ca="rocker", cb="crank"),
        _row(180.0, wa=0, wb=-1, ca="rocker", cb="crank"),
    ]
    assert transition_intervals(rows) == [(0.0, 30.0), (60.0, 90.0)]
