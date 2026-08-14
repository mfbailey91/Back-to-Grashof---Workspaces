"""Tests for the V07 synthetic spatial-6R corpus seed audit."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.v07_corpus import (
    audit_fixed_position_seed_6r,
    build_generic_6r,
    seed_audit_summary,
)


def test_generic_6r_seed_has_rank3_nullity3() -> None:
    entry = build_generic_6r()
    assert entry.model.n_joints == 6
    assert entry.model.architecture_id == "generic_6r"
    assert entry.terminal_axis_offset_m > 1e-6

    audit = audit_fixed_position_seed_6r(entry)
    assert audit.status == "PASS"
    assert audit.regular
    assert audit.rank_jp == 3
    assert audit.nullity_jp == 3
    assert audit.finite_difference_verified


def test_seed_audit_summary_refuses_so3_parent_claim() -> None:
    audit = audit_fixed_position_seed_6r(build_generic_6r())
    summary = seed_audit_summary(audit)
    notes = " ".join(summary["notes"]).casefold()
    assert summary["nullity_jp"] == 3
    assert "frozen so(3)" in notes
    assert "gate k3" in notes
