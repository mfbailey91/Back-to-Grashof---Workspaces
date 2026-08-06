"""Candidate RRRR enumeration tests."""

from __future__ import annotations

from grashof_workspace.visual_probe.candidates import enumerate_candidates
from grashof_workspace.visual_probe.config import default_config_path, load_config
from grashof_workspace.visual_probe.forward_kinematics import forward_kinematics
from grashof_workspace.visual_probe.reductions import (
    adjacent_axis_relationships,
    enumerate_compound_parents,
)
from grashof_workspace.visual_probe.virtual_closure import virtual_spherical_closure


def test_three_parents_yield_thirty_six_unique_candidates() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    parents = enumerate_compound_parents(adjacent_axis_relationships(fk, cfg))
    assert sum(1 for p in parents if p.enabled) == 3
    cands = enumerate_candidates(fk, virtual_spherical_closure(fk), parents)
    assert len(cands) == 36
    assert len({c.candidate_id for c in cands}) == 36


def test_each_candidate_has_s_two_u_and_remaining_r() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    parents = enumerate_compound_parents(adjacent_axis_relationships(fk, cfg))
    cands = enumerate_candidates(fk, virtual_spherical_closure(fk), parents)
    for c in cands:
        roles = [a.role for a in c.axes]
        assert roles == ["S", "U", "U", "R"]
        assert c.axes[3].source_id == f"R{c.remaining_r}"
        assert all(a.source_id for a in c.axes)
