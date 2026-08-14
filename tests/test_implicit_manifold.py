"""V06A0 tests: implicit-manifold engine on the analytical unit sphere."""

from __future__ import annotations

import json
import math

import numpy as np

from grashof_workspace.spatial_experiments.implicit_manifold import (
    AnalyticalSphereProblem,
    ProcessSoftwareStatus,
    align_tangent_basis,
    ambient_distance,
    build_hexagonal_chart,
    build_sphere_atlas,
    correct_chart_point,
    grow_manifold_atlas,
    orthonormal_tangent_basis,
    wrapped_delta,
)
from grashof_workspace.spatial_experiments.v06a0 import build_v06a0_readout


def test_wrapped_delta_periodic_and_euclidean() -> None:
    periodic = (True, False)
    a = np.array((math.pi - 0.1, 2.0))
    b = np.array((-math.pi + 0.1, 0.5))
    delta = wrapped_delta(a, b, periodic)
    assert abs(float(delta[0]) + 0.2) < 1e-9
    assert abs(float(delta[1]) - 1.5) < 1e-12
    assert ambient_distance(a, b, periodic) > 0.0


def test_sphere_tangent_is_orthonormal_nullspace() -> None:
    problem = AnalyticalSphereProblem()
    x = np.array((0.0, 0.0, 1.0))
    jac = problem.jacobian(x)
    n = orthonormal_tangent_basis(jac, expected_nullity=2)
    assert n.shape == (3, 2)
    gram = n.T @ n
    assert np.allclose(gram, np.eye(2), atol=1e-12)
    assert np.allclose(jac @ n, 0.0, atol=1e-12)
    n2 = orthonormal_tangent_basis(problem.jacobian(np.array((1.0, 0.0, 0.0))), expected_nullity=2)
    aligned = align_tangent_basis(n, n2)
    assert aligned.shape == (3, 2)
    assert np.allclose(aligned.T @ aligned, np.eye(2), atol=1e-10)


def test_chart_correction_lands_on_sphere() -> None:
    problem = AnalyticalSphereProblem()
    x_c = np.array((0.0, 0.0, 1.0))
    n_c = orthonormal_tangent_basis(problem.jacobian(x_c), expected_nullity=2)
    corr = correct_chart_point(problem, x_c, n_c, np.array((0.2, -0.15)))
    assert corr.accepted
    assert corr.x is not None
    assert corr.constraint_residual <= 1e-10
    assert abs(float(np.linalg.norm(corr.x)) - 1.0) <= 1e-9
    assert corr.rank == 1
    assert corr.nullity == 2


def test_origin_is_not_on_the_manifold() -> None:
    problem = AnalyticalSphereProblem()
    origin = np.zeros(3)
    assert abs(float(problem.residual(origin)[0]) + 1.0) < 1e-15
    n = np.eye(3)[:, :2]
    corr = correct_chart_point(problem, origin, n, np.zeros(2))
    # u=0 at the origin: predictor is origin; Newton should leave the singular set
    # or reject. Either way the origin itself is not an accepted manifold point
    # without moving off F=-1 unless correction succeeds onto the sphere.
    if corr.accepted:
        assert corr.x is not None
        assert abs(float(np.linalg.norm(corr.x)) - 1.0) <= 1e-8
        assert abs(float(np.linalg.norm(origin))) < 1e-15


def test_hex_chart_vertices_satisfy_constraint() -> None:
    problem = AnalyticalSphereProblem()
    chart = build_hexagonal_chart(
        problem, np.array((0.0, 0.0, 1.0)), chart_id="c0", radius=0.35
    )
    assert chart.accepted
    for sample in chart.samples:
        assert sample.correction.accepted
        assert sample.correction.x is not None
        assert abs(float(np.linalg.norm(sample.correction.x)) - 1.0) <= 1e-8


def test_duplicate_centers_rejected_and_overlaps_deterministic() -> None:
    atlas_a = build_sphere_atlas(radius=0.45, max_charts=24)
    atlas_b = build_sphere_atlas(radius=0.45, max_charts=24)
    assert atlas_a.process_status is ProcessSoftwareStatus.SOFTWARE_VALIDATION
    ids_a = [c.chart_id for c in atlas_a.charts]
    ids_b = [c.chart_id for c in atlas_b.charts]
    assert ids_a == ids_b
    overlap_a = [item.to_json_dict() for item in atlas_a.overlaps]
    overlap_b = [item.to_json_dict() for item in atlas_b.overlaps]
    assert overlap_a == overlap_b
    centers = [np.asarray(c.center) for c in atlas_a.charts]
    for i, ci in enumerate(centers):
        for j, cj in enumerate(centers):
            if j <= i:
                continue
            dist = float(np.linalg.norm(ci - cj))
            assert dist > 0.2
    assert len(atlas_a.rejected_duplicate_centers) >= 1


def test_sphere_one_closed_component_and_area_near_4pi() -> None:
    coarse = build_sphere_atlas(radius=0.50, max_charts=24)
    fine = build_sphere_atlas(radius=0.40, max_charts=80)
    assert coarse.component_count == 1
    assert fine.component_count == 1
    assert coarse.closed_component
    assert fine.closed_component
    assert coarse.approximate_area is not None
    assert fine.approximate_area is not None
    target = 4.0 * math.pi
    assert abs(fine.approximate_area - target) <= abs(coarse.approximate_area - target) + 1e-9
    assert abs(fine.approximate_area - target) / target < 0.08


def test_strict_json_and_v06a0_readout(tmp_path) -> None:
    atlas = grow_manifold_atlas(
        AnalyticalSphereProblem(),
        np.array((0.0, 0.0, 1.0)),
        radius=0.5,
        max_charts=12,
    )
    payload = atlas.to_json_dict()
    text = json.dumps(payload, allow_nan=False)
    assert "NaN" not in text
    assert "Infinity" not in text
    assert payload["certificate_status"] is None
    html = build_v06a0_readout(tmp_path)
    assert html.is_file()
    body = html.read_text(encoding="utf-8")
    assert "Software validation only" in body
    assert "DecompositionCertificate" in body
    json_path = tmp_path / "data" / "v06a0_unit_sphere_atlas.json"
    json.loads(json_path.read_text(encoding="utf-8"))
    assert (tmp_path / "figures" / "v06a0_unit_sphere_atlas.png").is_file()
