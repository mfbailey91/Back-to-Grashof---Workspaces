"""Interior, exterior, and boundary tests for Sprint V05A pointing-slice fibers."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial4bar_explorer.pointing_slice import (
    TANGENT_RESIDUAL_TOL,
    construct_suur_uuur_pointing_fiber,
    derive_virtual_u_axes,
)
from grashof_workspace.spatial4bar_explorer.v05a import build_v05a_readout, render_v05a_html
from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    IntersectingPairsAligned6R,
)
from grashof_workspace.spatial_experiments.fiber_constraints import (
    PRIMARY_N,
    fiber_independence_report,
)


def test_interior_regular_fiber_seed_is_independent() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    report = fiber_independence_report(chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    assert report.rank == 4
    assert report.nullity == 1
    assert report.independent
    assert abs(report.dh_dq6) <= 1e-12


def test_exterior_parallel_slice_is_not_independent() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    d0 = tuple(float(x) for x in chain.evaluate(INTERSECTING_PAIRS_REGULAR_Q).d)
    report = fiber_independence_report(chain, INTERSECTING_PAIRS_REGULAR_Q, d0)
    assert not report.independent
    assert report.rank < 4


def test_exterior_parallel_construct_raises() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    d0 = tuple(float(x) for x in chain.evaluate(INTERSECTING_PAIRS_REGULAR_Q).d)
    try:
        construct_suur_uuur_pointing_fiber(n=d0, slice_id="parallel_exterior")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_boundary_worked_uuur_child_passes_fiber_equivalence() -> None:
    result = construct_suur_uuur_pointing_fiber()
    assert result.fiber_equivalence_status == "PASS"
    assert result.slice_provenance == "task_derived"
    assert result.family == "UUUR"
    assert result.parent_line == "SUUR"
    residuals = result.equivalence_residuals
    assert residuals.tangent_pointing_residual <= TANGENT_RESIDUAL_TOL
    assert residuals.pointing_curve_residual <= 5e-3
    assert residuals.h_residual_max <= 1e-9
    assert residuals.child_rank == 6
    assert residuals.child_nullity == 1
    assert residuals.branch_sample_count >= 3
    assert result.slice_definition.formula == "h(d)=n·d"
    assert result.to_json_dict()["slice_provenance"] == "task_derived"


def test_virtual_u_axes_form_right_handed_triad() -> None:
    axes = derive_virtual_u_axes((0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    ra = np.asarray(axes.r_a)
    rb = np.asarray(axes.r_b)
    d = np.asarray(axes.d)
    assert abs(float(np.dot(ra, rb))) < 1e-12
    assert abs(float(np.dot(ra, d))) < 1e-12
    assert abs(float(np.dot(rb, d))) < 1e-12
    assert np.allclose(np.cross(ra, rb), d, atol=1e-12)


def test_v05a_html_contains_task_derived_animation_checklist(tmp_path) -> None:
    result = construct_suur_uuur_pointing_fiber()
    html = render_v05a_html(
        result,
        tmp_path,
        figures={"demo": "figures/demo.gif"},
    )
    html_cf = html.casefold()
    for phrase in (
        "task-derived animation contract checklist",
        "tool point / virtual",
        "s_v",
        "pointing direction",
        "r_a",
        "r_b",
        "h(d)=n·d=c",
        "α(s)",
        "β(s)",
        "param=s (not driven)",
        "mechanism_explorer_only",
    ):
        assert phrase.casefold() in html_cf


def test_v05a_readout_writes_artifacts(tmp_path) -> None:
    result = build_v05a_readout(tmp_path)
    assert result.fiber_equivalence_status == "PASS"
    assert (tmp_path / "data" / "v05a_pointing_slice_fibers.json").is_file()
    assert (tmp_path / "sprint_05a_pointing_slice_fibers.html").is_file()
    assert (tmp_path / "figures" / "v05a_parent_fiber_diagnostics.png").is_file()
    assert (tmp_path / "figures" / "v05a_uuur_child_geometry.png").is_file()
    assert (tmp_path / "figures" / "v05a_task_derived_fiber.gif").is_file()
    html = (tmp_path / "sprint_05a_pointing_slice_fibers.html").read_text(encoding="utf-8")
    assert "task-derived animation contract checklist" in html.casefold()
    assert "PASS" in html
