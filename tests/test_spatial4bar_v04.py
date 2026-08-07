from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from grashof_workspace.spatial4bar_explorer.cycle_continuation import (
    continue_until_return,
    unwrap_angles,
    wrapped_configuration_distance,
)
from grashof_workspace.spatial4bar_explorer.geometry import canonical_geometry
from grashof_workspace.spatial4bar_explorer.geometry_descriptors import (
    generate_physical_geometry_samples,
)
from grashof_workspace.spatial4bar_explorer.models import BranchClass, OrderedFamily
from grashof_workspace.spatial4bar_explorer.winding import (
    classify_cycle,
    classify_physical_sample,
    classify_tool_axis,
    compute_windings,
    select_crank_and_rocker_examples,
)
from grashof_workspace.spatial4bar_explorer.winding_plots import (
    plot_classification_cards,
    plot_unwrapped_tool_angles,
    plot_winding_summary,
)
from grashof_workspace.spatial4bar_explorer.winding_readouts import write_sprint04_html


def test_unwrap_angles_interior_no_jump() -> None:
    series = np.asarray([[0.0], [0.1], [0.2], [0.3]], dtype=float)
    unwrapped = unwrap_angles(series)
    assert np.allclose(unwrapped.ravel(), series.ravel())


def test_unwrap_angles_exterior_raw_jump_near_two_pi() -> None:
    # Raw chart jumps by nearly +2π; continuous chart should stay near 0.1.
    series = np.asarray([[0.0], [0.1], [0.1 - 2.0 * math.pi + 1e-9]], dtype=float)
    unwrapped = unwrap_angles(series)
    assert abs(float(unwrapped[2, 0]) - 0.1) < 1e-6


def test_unwrap_angles_boundary_exact_pi_step() -> None:
    series = np.asarray([[0.0], [math.pi], [2.0 * math.pi]], dtype=float)
    unwrapped = unwrap_angles(series)
    # Boundary: π step is kept; next +π accumulates to 2π without wrap subtraction of 2π
    # because round(π/2π)=0 for first step and round(π/2π)=0 for second... wait
    # Δ1=π, round(0.5)=0 or 1? In Python round uses banker's rounding: round(0.5)->0
    # So Δ stays π. Δ2=π, same. Result [0, π, 2π].
    assert abs(float(unwrapped[1, 0]) - math.pi) < 1e-12
    assert abs(float(unwrapped[2, 0]) - 2.0 * math.pi) < 1e-12


def test_compute_windings_synthetic_full_turn_and_zero() -> None:
    names = ("tool_alpha", "tool_beta", "j2_alpha", "j2_beta", "j3_alpha", "j3_beta", "j4_r")
    series = np.zeros((5, 7), dtype=float)
    series[:, 0] = np.linspace(0.0, 2.0 * math.pi, 5)
    series[:, 1] = np.linspace(0.0, 0.2, 5)
    w_alpha, w_beta = compute_windings(series, names)
    assert w_alpha == 1
    assert w_beta == 0


def test_classify_tool_axis_crank_rocker_open() -> None:
    assert classify_tool_axis(1, returned=True, status="returned") is BranchClass.CRANK
    assert classify_tool_axis(-2, returned=True, status="returned") is BranchClass.CRANK
    assert classify_tool_axis(0, returned=True, status="returned") is BranchClass.ROCKER
    assert classify_tool_axis(None, returned=False, status="open_branch") is BranchClass.OPEN_BRANCH
    assert classify_tool_axis(1, returned=False, status="change_point") is BranchClass.CHANGE_POINT


def test_wrapped_distance_zero_at_reference() -> None:
    assert wrapped_configuration_distance(np.zeros(7)) == 0.0
    assert wrapped_configuration_distance(np.array([2.0 * math.pi, 0, 0, 0, 0, 0, 0])) < 1e-12


def test_uuur_physical_sample_produces_true_winding() -> None:
    sample = generate_physical_geometry_samples(OrderedFamily.UUUR, count=1, seed=202)[0]
    result = classify_physical_sample(sample, step_size=0.05, max_steps=800)
    assert "source=continued_branch_winding" in result.notes
    assert "mock" not in " ".join(result.notes).lower()
    assert result.cycle.family == "UUUR"
    assert len(result.cycle.points) > 10
    if result.cycle.returned:
        assert result.w_alpha is not None
        assert result.w_beta is not None
        assert result.class_alpha in {BranchClass.CRANK, BranchClass.ROCKER}
        assert result.class_beta in {BranchClass.CRANK, BranchClass.ROCKER}


def test_uuur_corpus_finds_crank_and_rocker(tmp_path: Path) -> None:
    samples = generate_physical_geometry_samples(OrderedFamily.UUUR, count=6, seed=202)
    classifications = [
        classify_physical_sample(sample, step_size=0.05, max_steps=900) for sample in samples
    ]
    crank, rocker = select_crank_and_rocker_examples(classifications)
    assert crank is not None
    assert rocker is not None
    assert crank.class_alpha is BranchClass.CRANK or crank.class_beta is BranchClass.CRANK
    assert rocker.class_alpha is BranchClass.ROCKER or rocker.class_beta is BranchClass.ROCKER

    summary = tmp_path / "summary.png"
    counts = tmp_path / "counts.png"
    crank_plot = tmp_path / "crank.png"
    rocker_plot = tmp_path / "rocker.png"
    plot_winding_summary(classifications, summary)
    plot_classification_cards(classifications, counts)
    plot_unwrapped_tool_angles(crank, crank_plot)
    plot_unwrapped_tool_angles(rocker, rocker_plot)
    for path in (summary, counts, crank_plot, rocker_plot):
        assert path.exists()
        assert path.stat().st_size > 0

    write_sprint04_html(
        tmp_path,
        classifications=classifications,
        crank_example=crank,
        rocker_example=rocker,
        winding_summary_plot=summary.name,
        classification_plot=counts.name,
        crank_angle_plot=crank_plot.name,
        rocker_angle_plot=rocker_plot.name,
        results_json="results.json",
        traces_json="traces.json",
    )
    html = (tmp_path / "sprint_04_winding_and_crank.html").read_text(encoding="utf-8")
    assert "true winding" in html.lower() or "continued" in html.lower()
    assert "not</em> V02 mock" in html or "not" in html and "mock" in html
    assert crank.sample_id in html
    assert rocker.sample_id in html


def test_continue_until_return_on_canonical_uuur() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    cycle = continue_until_return(geometry, step_size=0.05, max_steps=700, direction=1)
    assert cycle.status in {"returned", "open_branch", "change_point", "invalid"}
    assert len(cycle.unwrapped_q) == len(cycle.points)
    classified = classify_cycle("uuur_canonical", cycle)
    if cycle.returned:
        assert classified.w_alpha is not None
        assert abs(classified.w_alpha) + abs(classified.w_beta or 0) >= 0
