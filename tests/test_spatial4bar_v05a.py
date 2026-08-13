"""Tests for the retained SUUR→UUUR pointing-slice prototype."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial4bar_explorer.pointing_slice import (
    TANGENT_RESIDUAL_TOL,
    construct_suur_uuur_pointing_fiber,
    derive_virtual_u_axes,
)
from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    IntersectingPairsAligned6R,
)
from grashof_workspace.spatial_experiments.fiber_constraints import (
    PRIMARY_N,
    fiber_independence_report,
)


def test_parent_pointing_slice_is_regular() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    report = fiber_independence_report(chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    assert report.rank == 4
    assert report.nullity == 1
    assert report.independent
    assert abs(report.dh_dq6) <= 1e-12


def test_parallel_slice_is_not_independent() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    d0 = tuple(float(x) for x in chain.evaluate(INTERSECTING_PAIRS_REGULAR_Q).d)
    report = fiber_independence_report(chain, INTERSECTING_PAIRS_REGULAR_Q, d0)
    assert not report.independent
    assert report.rank < 4


def test_worked_child_does_not_claim_equivalence_pass() -> None:
    result = construct_suur_uuur_pointing_fiber()
    statuses = result.equivalence_statuses
    assert result.program_role == "V08_POINTING_SLICE_PROTOTYPE"
    assert result.slice_provenance == "task_derived"
    assert statuses.parent_slice_status == "PASS"
    assert statuses.virtual_u_chart_status == "PASS"
    assert statuses.child_reference_closure_status == "PASS"
    assert statuses.parent_child_tangent_status == "FAIL"
    assert statuses.parent_child_branch_status == "UNRESOLVED"
    assert statuses.overall_status == "REVIEW"
    assert result.fiber_equivalence_status == "REVIEW"
    assert result.equivalence_residuals.tangent_pointing_residual <= TANGENT_RESIDUAL_TOL
    assert result.equivalence_residuals.child_tool_tangent_residual > TANGENT_RESIDUAL_TOL


def test_virtual_u_axes_form_right_handed_triad() -> None:
    axes = derive_virtual_u_axes((0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    ra = np.asarray(axes.r_a)
    rb = np.asarray(axes.r_b)
    d = np.asarray(axes.d)
    assert abs(float(np.dot(ra, rb))) < 1e-12
    assert abs(float(np.dot(ra, d))) < 1e-12
    assert abs(float(np.dot(rb, d))) < 1e-12
    assert np.allclose(np.cross(ra, rb), d, atol=1e-12)


def test_json_exports_split_statuses() -> None:
    payload = construct_suur_uuur_pointing_fiber().to_json_dict()
    assert payload["fiber_equivalence_status"] == "REVIEW"
    assert payload["equivalence_statuses"]["parent_slice_status"] == "PASS"
    assert payload["equivalence_statuses"]["parent_child_tangent_status"] == "FAIL"
    assert payload["equivalence_statuses"]["parent_child_branch_status"] == "UNRESOLVED"
