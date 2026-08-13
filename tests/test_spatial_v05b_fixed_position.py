"""Interior, exterior, boundary, and special-case tests for active V05B."""

from __future__ import annotations

import numpy as np

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
    build_terminal_roll_control_4r,
)
from grashof_workspace.spatial_experiments.v05b import build_v05b_readout, render_v05b_html


def test_active_generic_4r_seed_is_regular_and_nontrivial() -> None:
    entry = build_generic_4r()
    audit = audit_fixed_position_seed(pose_fixed_position_problem(entry.model, entry.regular_q))
    assert audit.status == "PASS"
    assert audit.rank_jp == 3
    assert audit.nullity_jp == 1
    assert audit.finite_difference_verified
    assert audit.finite_difference_jp_error_fro <= 1e-7
    assert audit.terminal_axis_distance_m > 1e-3
    assert audit.jp_column_norms[-1] > 1e-3
    assert audit.upstream_tangent_norm is not None and audit.upstream_tangent_norm > 1e-3
    assert audit.pointing_speed is not None and audit.pointing_speed > 1e-3
    assert audit.motion_signature == "NONTRIVIAL_POINTING_CURVE"


def test_terminal_roll_control_is_explicit_special_case() -> None:
    entry = build_terminal_roll_control_4r()
    audit = audit_fixed_position_seed(pose_fixed_position_problem(entry.model, entry.regular_q))
    assert audit.status == "PASS"
    assert audit.rank_jp == 3
    assert audit.nullity_jp == 1
    assert audit.terminal_axis_distance_m <= 1e-10
    assert audit.jp_column_norms[-1] <= 1e-10
    assert audit.terminal_tangent_alignment_error is not None
    assert audit.terminal_tangent_alignment_error <= 1e-8
    assert audit.upstream_tangent_norm is not None and audit.upstream_tangent_norm <= 1e-8
    assert audit.pointing_speed is not None and audit.pointing_speed <= 1e-8
    assert audit.motion_signature == "PURE_TERMINAL_ROLL"


def test_exact_u_pair_seed_is_regular_and_nontrivial() -> None:
    entry = build_exact_u_pair_4r()
    audit = audit_fixed_position_seed(pose_fixed_position_problem(entry.model, entry.regular_q))
    assert audit.status == "PASS"
    assert audit.rank_jp == 3
    assert audit.nullity_jp == 1
    assert audit.motion_signature == "NONTRIVIAL_POINTING_CURVE"


def test_singular_parallel_seed_fails() -> None:
    entry = build_singular_4r()
    audit = audit_fixed_position_seed(pose_fixed_position_problem(entry.model, entry.regular_q))
    assert not audit.regular
    assert audit.status == "FAIL"
    assert audit.rank_jp < 3
    assert audit.motion_signature == "SINGULAR_OR_EMPTY"


def test_pseudo_arclength_continuation_keeps_both_constraints() -> None:
    entry = build_generic_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=12, step_size=0.03)
    assert fiber.seed_audit.status == "PASS"
    assert len(fiber.plus.accepted) >= 3
    assert len(fiber.minus.accepted) >= 3
    for step in fiber.accepted_samples:
        assert step.p_residual_m <= 1e-9
        assert step.arclength_residual_rad <= 1e-9
        assert step.augmented_condition < 1e12

    q0 = np.asarray(entry.regular_q, dtype=float)
    q_plus = np.asarray(fiber.plus.accepted[1].q, dtype=float)
    q_minus = np.asarray(fiber.minus.accepted[1].q, dtype=float)
    delta_plus = q_plus - q0
    delta_minus = q_minus - q0
    assert float(np.dot(delta_plus, delta_minus)) < 0.0
    assert fiber.plus.accepted[1].sigma > 0.0
    assert fiber.minus.accepted[1].sigma < 0.0


def test_rejected_seed_fiber_has_no_accepted_samples() -> None:
    entry = build_singular_4r()
    fiber = continue_fixed_position_fiber(entry.model, entry.regular_q, n_steps=8)
    assert fiber.branch_status == "rejected_seed"
    assert fiber.accepted_samples == ()
    assert fiber.returned is False


def test_v05b_html_and_readout(tmp_path) -> None:
    fibers = build_v05b_readout(tmp_path, n_steps=8, step_size=0.03)
    assert len(fibers) == 5
    by_id = {fiber.architecture_id: fiber for fiber in fibers}
    assert by_id["generic_4r"].seed_audit.motion_signature == "NONTRIVIAL_POINTING_CURVE"
    assert by_id["terminal_roll_control_4r"].seed_audit.motion_signature == "PURE_TERMINAL_ROLL"
    assert by_id["singular_4r_parallel"].seed_audit.status == "FAIL"
    html = render_v05b_html(fibers, figures={"demo": "figures/demo.png"})
    assert "Active V05B" in html
    assert "S_v" in html
    assert (tmp_path / "data" / "v05b_fixed_position_fibers.json").is_file()
    assert (tmp_path / "sprint_v05b_fixed_position_fiber.html").is_file()
