"""Axis relationship classification tests."""

from __future__ import annotations

from grashof_workspace.visual_probe.axis_geometry import classify_axis_pair
from grashof_workspace.visual_probe.model import AxisLine


def _classify(a: AxisLine, b: AxisLine):
    return classify_axis_pair(
        a,
        b,
        joint_a=1,
        joint_b=2,
        incidence_tol=1e-9,
        parallel_tol=1e-9,
        ambiguous_tol=1e-6,
    )


def test_intersecting_fixture() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    b = AxisLine((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    rel = _classify(a, b)
    assert rel.relation == "intersecting"
    assert rel.intersection is not None


def test_collinear_fixture() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    b = AxisLine((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))
    assert _classify(a, b).relation == "collinear"


def test_parallel_distinct_fixture() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    b = AxisLine((1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    assert _classify(a, b).relation == "parallel_distinct"


def test_skew_fixture() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    b = AxisLine((0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    assert _classify(a, b).relation == "skew"


def test_numerically_ambiguous_band() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    b = AxisLine((0.0, 1e-7, 0.0), (0.0, 0.0, 1.0))
    assert _classify(a, b).relation == "numerically_ambiguous"
