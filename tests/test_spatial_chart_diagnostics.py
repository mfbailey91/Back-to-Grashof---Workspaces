"""Tests for pointing-chart diagnostics."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.chart_diagnostics import (
    chart_differentials,
    duplicate_report,
    synthetic_collapsed_chart,
    true_forward_reverse,
)
from grashof_workspace.spatial_experiments.chart_experiments import evaluate_urlike_chart
from grashof_workspace.spatial_experiments.continuation import continue_sequential_chart
from grashof_workspace.spatial_experiments.suur_coordinates import suur_map


def test_true_reverse_starts_at_forward_endpoint() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    report = true_forward_reverse(
        chain,
        INTERSECTING_PAIRS_REGULAR_Q,
        axis="s",
        n_steps=4,
        step_size=0.03,
        architecture="IntersectingPairsAligned6R",
    )
    assert report.started_from_endpoint
    assert report.forward_accepted == 4
    assert report.reverse_accepted == 4
    assert report.passed


def test_regular_patch_has_rank_two_chart_and_pointing() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    chart = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=5, nt=5, ds=0.03, dt=0.03)
    diag = chart_differentials(chart, ds=0.03, dt=0.03)
    assert diag.n_interior >= 1
    assert diag.all_rank_two


def test_collapsed_synthetic_chart_fails_duplicate_and_rank_checks() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    chart = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=3, nt=3, ds=0.03, dt=0.03)
    collapsed = synthetic_collapsed_chart(chart.samples[0])
    dups = duplicate_report(collapsed)
    assert dups.n_duplicates > 0
    fake_chart = type(chart)(
        q0=chart.q0,
        p0=chart.p0,
        d0=chart.d0,
        q6_star=chart.q6_star,
        seed_frame=chart.seed_frame,
        samples=collapsed,
        paths=chart.paths,
        rejected_steps=(),
    )
    diag = chart_differentials(fake_chart, ds=0.03, dt=0.03)
    assert not diag.all_rank_two


def test_duplicate_detection_flags_copied_sample() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    chart = continue_sequential_chart(chain, INTERSECTING_PAIRS_REGULAR_Q, ns=3, nt=3)
    original = chart.samples[0]
    copied = original.__class__(
        s=0.99,
        t=0.99,
        path_id="dup",
        step_index=original.step_index,
        q=original.q,
        d=original.d,
        p_residual_m=original.p_residual_m,
        corrector_iterations=original.corrector_iterations,
        correction_norm=original.correction_norm,
        step_reductions=original.step_reductions,
        rank_jp=original.rank_jp,
        rank_jpd=original.rank_jpd,
        rank_jd_nred=original.rank_jd_nred,
        tangent_principal_angle_1=original.tangent_principal_angle_1,
        tangent_principal_angle_2=original.tangent_principal_angle_2,
        regular=original.regular,
        label=original.label,
    )
    report = duplicate_report((*chart.samples, copied))
    assert report.n_duplicates >= 1


def test_urlike_chart_path_does_not_invoke_suur_map(monkeypatch) -> None:
    calls: list[object] = []

    def boom(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("suur_map must not be called on the UR-like chart path")

    monkeypatch.setattr(
        "grashof_workspace.spatial_experiments.suur_coordinates.suur_map",
        boom,
    )
    monkeypatch.setattr(
        "grashof_workspace.spatial_experiments.chart_experiments.pair_intersection_distances",
        boom,
    )
    result = evaluate_urlike_chart()
    assert result["status"] == "PASS"
    assert calls == []
    # Direct suur_map remains available for IP-only diagnostics elsewhere.
    defined = suur_map(
        IntersectingPairsAligned6R.aligned().chain,
        INTERSECTING_PAIRS_REGULAR_Q[:5],
        INTERSECTING_PAIRS_REGULAR_Q[5],
    )
    assert defined.defined
    _ = URLIKE_REGULAR_Q
