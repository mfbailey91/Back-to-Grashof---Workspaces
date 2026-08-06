"""Compound-parent enumeration tests."""

from __future__ import annotations

from grashof_workspace.visual_probe.axis_geometry import classify_axis_pair
from grashof_workspace.visual_probe.config import default_config_path, load_config
from grashof_workspace.visual_probe.forward_kinematics import forward_kinematics
from grashof_workspace.visual_probe.model import AxisLine, AxisRelationship
from grashof_workspace.visual_probe.reductions import (
    adjacent_axis_relationships,
    enumerate_compound_parents,
)


def test_synthetic_architecture_enables_all_three_parents() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    relations = adjacent_axis_relationships(fk, cfg)
    parents = enumerate_compound_parents(relations)
    assert [p.pair_set for p in parents] == ["P12_P34", "P12_P45", "P23_P45"]
    assert [p.topology for p in parents] == ["SRUU", "SURU", "SUUR"]
    assert all(p.enabled for p in parents)


def test_collinear_pair_never_enables_u() -> None:
    relations = (
        AxisRelationship(1, 2, "collinear", 0.0, (0.0, 0.0, 0.0)),
        AxisRelationship(2, 3, "intersecting", 0.0, (0.0, 0.0, 0.0)),
        AxisRelationship(3, 4, "intersecting", 0.0, (0.0, 0.0, 0.0)),
        AxisRelationship(4, 5, "intersecting", 0.0, (0.0, 0.0, 0.0)),
        AxisRelationship(5, 6, "skew", 0.1, None),
    )
    parents = enumerate_compound_parents(relations)
    by_id = {p.pair_set: p for p in parents}
    assert by_id["P12_P34"].enabled is False
    assert by_id["P12_P45"].enabled is False
    assert by_id["P23_P45"].enabled is True


def test_no_geometry_snapping_in_classification() -> None:
    a = AxisLine((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    b = AxisLine((0.0, 1e-4, 0.0), (0.0, 0.0, 1.0))
    rel = classify_axis_pair(
        a,
        b,
        joint_a=1,
        joint_b=2,
        incidence_tol=1e-9,
        parallel_tol=1e-9,
        ambiguous_tol=1e-6,
    )
    assert rel.relation == "skew"
    assert rel.intersection is None
