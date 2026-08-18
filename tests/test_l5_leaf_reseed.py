"""Real leaf re-seeding: independent rebuilds, not self-distance."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    audit_reseeded_component,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    FamilyAdmissibilityStatus,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    continue_uuru_leaf,
    issue_leaf_certificate,
    leaf_spec_for,
    problem_from_source_seed,
)

CONFIG = "configs/l5_positive_control_v1.json"


def _continued_leaf(*, max_steps: int = 8):
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q = analytic_seed_configuration(config.geometry, probe)
    chart = charts_from_config(config.charts)[0]
    built = problem_from_source_seed(arm, chart, q, probe.p_star, leaf_id="reseed_leaf")
    assert built is not None
    problem, x0 = built
    samples, status, returned = continue_uuru_leaf(problem, x0, max_steps=max_steps, step_size=0.08)
    assert len(samples) >= 3
    return config, arm, chart, problem, samples, status, returned


def test_same_component_reseed_is_not_self_distance() -> None:
    config, arm, chart, problem, samples, _status, _returned = _continued_leaf(max_steps=8)
    audit = audit_reseeded_component(
        arm,
        chart,
        problem,
        samples,
        q_tol=config.tolerances.reseed_symmetric_q_distance_rad,
        p_tol=config.tolerances.reseed_pointing_distance_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
        max_steps=8,
        step_size=0.08,
    )
    assert audit.n_reseeds == 3
    assert len(audit.attempts) == 3
    seed_s = [item.seed_s for item in audit.attempts]
    assert seed_s[0] <= seed_s[1] <= seed_s[2]
    assert {item.reseed_id for item in audit.attempts} == {"start", "mid", "end"}
    assert audit.status == "PASS"
    assert audit.reseed_status == "PASS"
    assert audit.max_symmetric_q_distance_rad is not None
    notes = " ".join(audit.notes)
    assert "independent" in notes.lower()
    assert audit.attempts[0].seed_s != audit.attempts[-1].seed_s
    spec = leaf_spec_for("P1_DEEP_COMPLETE", chart, problem.lambda_fixed, problem.p_star, problem.problem_id)
    cert = issue_leaf_certificate(
        spec,
        samples,
        branch_status="open",
        returned=False,
        position_tol=1e-6,
        orientation_tol=1e-5,
        pointing_tol=1e-5,
        lift_tol=1e-8,
        lambda_tol=1e-5,
        closure_tol=1e-6,
    )
    assert cert.family_admissibility_status is FamilyAdmissibilityStatus.UNRESOLVED
    assert cert.accepted_for_reconstruction is False


def test_wrong_lambda_reseed_fails() -> None:
    config, arm, chart, problem, samples, _status, _returned = _continued_leaf(max_steps=6)
    audit = audit_reseeded_component(
        arm,
        chart,
        problem,
        samples,
        q_tol=config.tolerances.reseed_symmetric_q_distance_rad,
        p_tol=config.tolerances.reseed_pointing_distance_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
        max_steps=6,
        step_size=0.08,
        lambda_fixed=float(problem.lambda_fixed + 0.4),
    )
    assert audit.status == "FAIL"
    assert audit.reseed_status != "PASS"


def test_fewer_than_three_samples_is_unresolved() -> None:
    config, arm, chart, problem, samples, _status, _returned = _continued_leaf(max_steps=6)
    audit = audit_reseeded_component(
        arm,
        chart,
        problem,
        samples[:2],
        q_tol=config.tolerances.reseed_symmetric_q_distance_rad,
        p_tol=config.tolerances.reseed_pointing_distance_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
        max_steps=6,
        step_size=0.08,
    )
    assert audit.status == "UNRESOLVED"
    assert audit.status != "PASS"


def test_truncated_budget_is_unresolved() -> None:
    config, arm, chart, problem, samples, _status, _returned = _continued_leaf(max_steps=8)
    audit = audit_reseeded_component(
        arm,
        chart,
        problem,
        samples,
        q_tol=config.tolerances.reseed_symmetric_q_distance_rad,
        p_tol=config.tolerances.reseed_pointing_distance_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
        max_steps=1,
        step_size=0.08,
    )
    assert audit.status == "UNRESOLVED"
    assert audit.status != "PASS"


def test_forced_lambda_is_preserved_on_rebuild() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q = analytic_seed_configuration(config.geometry, probe)
    chart = charts_from_config(config.charts)[0]
    original = problem_from_source_seed(arm, chart, q, probe.p_star, leaf_id="orig")
    assert original is not None
    problem, _x0 = original
    rebuilt = problem_from_source_seed(
        arm,
        chart,
        q,
        probe.p_star,
        leaf_id="forced",
        lambda_fixed=problem.lambda_fixed,
    )
    assert rebuilt is not None
    forced, _xf = rebuilt
    assert forced.lambda_fixed == problem.lambda_fixed
    assert id(forced.independent_chain) != id(arm.chain)
    assert float(np.linalg.norm(forced.residual(_xf))) <= 1e-8
