"""Tests for topology-derived spherical candidate axes."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.aligned_6r import REGULAR_Q, GenericAligned6R
from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from grashof_workspace.spatial_experiments.axis_geometry import (
    AxisLine,
    line_intersection_point,
    line_line_distance,
    point_axis_distance,
)
from grashof_workspace.spatial_experiments.fiber_constraints import PRIMARY_N, reduced_fiber_tangent
from grashof_workspace.spatial_experiments.fiber_continuation import continue_fiber
from grashof_workspace.spatial_experiments.spherical_invariants import (
    COORDINATE_LOCK_TOL_RAD,
    EFFECTIVE_RATE_TOL,
    GLOBAL_CONCURRENCY_TOL_M,
    PAIR_CENTER_TOL_M,
    PHYSICAL_TUPLES_R1_TO_R5,
    arc_residual,
    body_fixed_axis_drift,
    effective_compound_axis,
    exploratory_fixed_tuple_scan,
    fiber_spherical_invariants,
    fit_global_center,
    line_center_residual,
    spherical_arc_angles,
    topology_spherical_axes,
)
from grashof_workspace.spatial_experiments.suur_coordinates import suur_map


def test_line_intersection_interior_exterior_boundary() -> None:
    shared = (0.1, -0.2, 0.3)
    a = AxisLine(shared, (0.0, 0.0, 1.0))
    b = AxisLine(shared, (1.0, 0.0, 0.0))
    point = line_intersection_point(a, b)
    assert point is not None
    assert np.allclose(point, shared, atol=1e-15)
    skew = AxisLine((1.0, 1.0, 0.0), (1.0, 0.0, 0.0))
    assert line_intersection_point(AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)), skew) is None
    offset = AxisLine((0.0, PAIR_CENTER_TOL_M, 0.0), (1.0, 0.0, 0.0))
    vertical = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    dist = line_line_distance(vertical, offset)
    assert line_intersection_point(vertical, offset, tol_m=dist) is not None
    assert line_intersection_point(vertical, offset, tol_m=0.5 * dist) is None


def test_effective_compound_axis_interior_exterior_equality() -> None:
    center = (0.0, 0.0, 0.28)
    w1 = (0.0, 0.0, 1.0)
    w2 = (1.0, 0.0, 0.0)
    axis, norm = effective_compound_axis(w1, w2, 1.0, 0.0, center)
    assert axis is not None
    assert abs(norm - 1.0) <= 1e-15
    assert np.allclose(axis.w, w1)
    missing, zero_norm = effective_compound_axis(w1, w2, 0.0, 0.0, center)
    assert missing is None
    assert zero_norm == 0.0
    boundary, boundary_norm = effective_compound_axis(
        w1, w2, EFFECTIVE_RATE_TOL + 1e-12, 0.0, center
    )
    assert boundary is not None
    assert boundary_norm > EFFECTIVE_RATE_TOL


def test_fit_global_center_interior_exterior_boundary() -> None:
    origin = (0.0, 0.0, 0.0)
    concurrent = (
        AxisLine(origin, (1.0, 0.0, 0.0)),
        AxisLine(origin, (0.0, 1.0, 0.0)),
        AxisLine(origin, (0.0, 0.0, 1.0)),
        AxisLine(origin, (1.0, 1.0, 0.0)),
    )
    center = fit_global_center((concurrent,))
    assert float(np.linalg.norm(center)) <= 1e-14
    assert max(line_center_residual(axis, center) for axis in concurrent) <= 1e-14

    offset = (
        AxisLine((0.0, 0.1, 0.0), (1.0, 0.0, 0.0)),
        AxisLine((0.0, -0.1, 0.0), (1.0, 0.0, 0.0)),
        AxisLine((0.1, 0.0, 0.0), (0.0, 1.0, 0.0)),
        AxisLine((-0.1, 0.0, 0.0), (0.0, 1.0, 0.0)),
    )
    exterior = fit_global_center((offset,))
    assert max(line_center_residual(axis, exterior) for axis in offset) >= 0.05

    boundary = AxisLine((0.0, GLOBAL_CONCURRENCY_TOL_M, 0.0), (1.0, 0.0, 0.0))
    assert abs(line_center_residual(boundary, np.zeros(3)) - GLOBAL_CONCURRENCY_TOL_M) <= 1e-18


def test_ip_seed_axes_are_well_posed() -> None:
    model = IntersectingPairsAligned6R.aligned()
    q0 = INTERSECTING_PAIRS_REGULAR_Q
    p0 = model.chain.evaluate(q0).p
    axes = topology_spherical_axes(model.chain, q0, p0, n=PRIMARY_N)
    assert axes.well_posed
    assert point_axis_distance(p0, axes.s) <= 1e-15
    tangent = reduced_fiber_tangent(model.chain, q0, PRIMARY_N)
    live = model.chain.current_axes(q0)
    omega_s = sum((float(tangent[i]) * live[i].w_array for i in range(5)), start=np.zeros(3))
    assert float(np.linalg.norm(np.cross(axes.s.w_array, omega_s))) <= 1e-12 * float(
        np.linalg.norm(omega_s)
    )
    angles = spherical_arc_angles(axes)
    assert all(0.0 <= angle <= np.pi for angle in angles)
    assert arc_residual(angles, angles) == 0.0
    assert body_fixed_axis_drift(model.chain, q0, axes, q0, axes) == 0.0


def test_generic_skew_axes_are_undefined() -> None:
    generic = GenericAligned6R.aligned()
    q_g = REGULAR_Q
    p_g = generic.chain.evaluate(q_g).p
    generic_axes = topology_spherical_axes(generic.chain, q_g, p_g, n=PRIMARY_N)
    assert not generic_axes.well_posed
    assert generic_axes.reason == "pair_centers_undefined"


def test_fiber_invariants_report_is_complete() -> None:
    model = IntersectingPairsAligned6R.aligned()
    segment = continue_fiber(model.chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    report = fiber_spherical_invariants(
        model.chain,
        segment,
        architecture="IntersectingPairsAligned6R",
        n=PRIMARY_N,
    )
    assert report.n_stations == len(segment.accepted_samples)
    assert report.construction == "s_ua_ub_r5"
    assert report.locking_policy == "body_fixed_effective_axis"
    assert report.locking in {"pass", "fail", "unresolved"}
    assert report.verdict in {"exact", "approximate", "fail", "unresolved"}
    assert report.global_center is not None
    assert np.isfinite(report.global_rms_m)
    assert np.isfinite(report.global_max_m)
    assert np.isfinite(report.max_center_drift_m)
    assert np.isfinite(report.max_arc_residual_rad)
    assert np.isfinite(report.max_body_fixed_drift_rad)
    assert not report.simple_lock_passed
    assert all(span > COORDINATE_LOCK_TOL_RAD for span in report.simple_lock_ranges)


def test_exploratory_fixed_tuple_scan_holds_tuples_fixed() -> None:
    model = URLikeAligned6R.aligned()
    segment = continue_fiber(model.chain, URLIKE_REGULAR_Q, PRIMARY_N)
    reports = exploratory_fixed_tuple_scan(model.chain, segment)
    assert len(reports) == len(PHYSICAL_TUPLES_R1_TO_R5)
    labels = {item.label for item in reports}
    assert labels == {"-".join(f"R{i + 1}" for i in indices) for indices in PHYSICAL_TUPLES_R1_TO_R5}


def test_general_invariant_path_does_not_call_suur(monkeypatch) -> None:
    model = IntersectingPairsAligned6R.aligned()

    def _boom(*_args, **_kwargs):
        raise AssertionError("suur_map must stay out of the spherical invariant path")

    monkeypatch.setattr(
        "grashof_workspace.spatial_experiments.suur_coordinates.suur_map",
        _boom,
    )
    segment = continue_fiber(model.chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    fiber_spherical_invariants(
        model.chain,
        segment,
        architecture="IntersectingPairsAligned6R",
        n=PRIMARY_N,
    )
    tangent = reduced_fiber_tangent(model.chain, INTERSECTING_PAIRS_REGULAR_Q, PRIMARY_N)
    assert float(np.linalg.norm(tangent)) > 0.0
    assert callable(suur_map)
