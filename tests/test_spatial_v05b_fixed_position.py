"""Interior, exterior, and boundary tests for active V05B fixed-position fibers."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.fixed_position import (
    audit_fixed_position_seed,
    pose_fixed_position_problem,
)
from grashof_workspace.spatial_experiments.fixed_position_continuation import (
    continue_fixed_position_fiber,
)
from grashof_workspace.spatial_experiments.v05_corpus import (
    build_exact_u_pair_4r,
    build_generic_4r,
    build_singular_4r,
)
from grashof_workspace.spatial_experiments.v05b import build_v05b_readout, render_v05b_html


def test_interior_generic_4r_seed_is_regular() -> None:
    entry = build_generic_4r()
    problem = pose_fixed_position_problem(entry.model, entry.regular_q)
    audit = audit_fixed_position_seed(problem)
    assert audit.rank_jp == 3
    assert audit.nullity_jp == 1
    assert audit.regular
    assert audit.status == "PASS"
    assert audit.virtual_closure_kind == "S_v"
    assert audit.p_residual_m <= 1e-12


def test_interior_exact_u_pair_seed_is_regular() -> None:
    entry = build_exact_u_pair_4r()
    problem = pose_fixed_position_problem(entry.model, entry.regular_q)
    audit = audit_fixed_position_seed(problem)
    assert audit.regular
    assert audit.rank_jp == 3
    assert audit.nullity_jp == 1


def test_exterior_singular_parallel_seed_fails() -> None:
    entry = build_singular_4r()
    problem = pose_fixed_position_problem(entry.model, entry.regular_q)
    audit = audit_fixed_position_seed(problem)
    assert not audit.regular
    assert audit.status == "FAIL"
    assert audit.rank_jp < 3


def test_boundary_continued_fiber_keeps_position_tolerance() -> None:
    entry = build_generic_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=16, step_size=0.04)
    assert fiber.seed_audit.status == "PASS"
    assert fiber.virtual_closure_kind == "S_v"
    assert fiber.architecture_id == "generic_4r"
    assert len(fiber.accepted_samples) >= 5
    assert all(step.p_residual_m <= 1e-9 for step in fiber.accepted_samples)
    assert fiber.branch_status in {"returned", "open", "budget_limited"}
    payload = fiber.to_json_dict()
    assert payload["architecture_id"] == "generic_4r"
    assert tuple(payload["p_star"]) == fiber.p_star
    assert payload["virtual_closure_kind"] == "S_v"


def test_rejected_seed_fiber_has_no_accepted_samples() -> None:
    entry = build_singular_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=8)
    assert fiber.branch_status == "rejected_seed"
    assert fiber.accepted_samples == ()
    assert fiber.returned is False


def test_v05b_html_and_readout(tmp_path) -> None:
    fibers = build_v05b_readout(tmp_path, n_steps=12, step_size=0.05)
    assert len(fibers) == 4
    assert any(f.seed_audit.status == "PASS" for f in fibers)
    assert any(f.seed_audit.status == "FAIL" for f in fibers)
    html = render_v05b_html(fibers, figures={"demo": "figures/demo.png"})
    assert "Active V05B" in html
    assert "mechanism_explorer_only" in html
    assert "S_v" in html
    assert (tmp_path / "data" / "v05b_fixed_position_fibers.json").is_file()
    assert (tmp_path / "sprint_v05b_fixed_position_fiber.html").is_file()
