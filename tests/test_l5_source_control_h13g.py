"""R3A-H13G evidence-safe source-control corrections."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from grashof_workspace.spatial_experiments.branch_continuation import (
    ParabolaProblem,
    UnitCircleProblem,
    continue_implicit_branch,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    SourceTraceTermination,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    SourceControlFiber,
    h13_source_policy_requested,
    h13g_source_policy_requested,
    h_value,
    radial_normal,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control_h13g import (
    TRACE_COUNT_SEMANTICS,
    H13GSourcePolicy,
    continue_source_fiber_h13g,
    load_h13g_source_policy,
    rasterize_fiber_kinematically,
    source_trace_diagnostic_h13g,
    trace_and_cover_projected_seeds,
)
from grashof_workspace.spatial_experiments.parent_level_sets import (
    PointingLevelSetProblem,
    pointing_scalar,
)

REPO = Path(__file__).resolve().parents[1]
H12_CONFIG = REPO / "configs" / "l5_positive_control_v1.json"
H13F_CONFIG = REPO / "configs" / "l5_positive_control_h13_source_v1.json"
H13G_CONFIG = REPO / "configs" / "l5_positive_control_h13g_source_pilot_v1.json"


def _policy(**overrides: float) -> H13GSourcePolicy:
    values: dict[str, float] = {
        "c_slice_max_angular_spacing_cell_fraction": 0.75,
        "discovery_q_precluster_tol_rad": 0.15,
        "seed_h_window": 0.35,
        "seed_precluster_q_tol_rad": 0.35,
        "seed_projected_q_tol_rad": 0.20,
        "dedup_q_tol_rad": 0.35,
        "trace_cover_q_tol_rad": 0.20,
        "max_seed_candidates_per_c": 24,
        "max_source_traces_per_c": 3,
        "endpoint_state_tol_rad": 0.10,
        "endpoint_tangent_abs_dot_min": 0.85,
        "curve_segment_fraction": 0.50,
        "continuation_step_size": 0.08,
        "kinematic_refinement_max_depth": 4,
    }
    values.update(overrides)
    return H13GSourcePolicy(
        c_slice_max_angular_spacing_cell_fraction=float(
            values["c_slice_max_angular_spacing_cell_fraction"]
        ),
        discovery_q_precluster_tol_rad=float(values["discovery_q_precluster_tol_rad"]),
        seed_h_window=float(values["seed_h_window"]),
        seed_precluster_q_tol_rad=float(values["seed_precluster_q_tol_rad"]),
        seed_projected_q_tol_rad=float(values["seed_projected_q_tol_rad"]),
        dedup_q_tol_rad=float(values["dedup_q_tol_rad"]),
        trace_cover_q_tol_rad=float(values["trace_cover_q_tol_rad"]),
        max_seed_candidates_per_c=int(values["max_seed_candidates_per_c"]),
        max_source_traces_per_c=int(values["max_source_traces_per_c"]),
        endpoint_state_tol_rad=float(values["endpoint_state_tol_rad"]),
        endpoint_tangent_abs_dot_min=float(values["endpoint_tangent_abs_dot_min"]),
        curve_segment_fraction=float(values["curve_segment_fraction"]),
        continuation_step_size=float(values["continuation_step_size"]),
        kinematic_refinement_max_depth=int(values["kinematic_refinement_max_depth"]),
    )


def _fiber(fiber_id: str, qs: tuple[tuple[float, ...], ...]) -> SourceControlFiber:
    return SourceControlFiber(
        fiber_id=fiber_id,
        c=0.0,
        q_samples=qs,
        pointing_samples=tuple((1.0, 0.0, 0.0) for _ in qs),
        branch_status="returned",
        returned=True,
        max_position_residual_m=0.0,
        max_h_residual=0.0,
        closed=True,
        termination_status=SourceTraceTermination.RETURNED_TO_SEED.value,
    )


def test_h13g_is_separate_and_diagnostic_only() -> None:
    h12 = load_campaign_config(H12_CONFIG)
    h13f = load_campaign_config(H13F_CONFIG)
    h13g = load_campaign_config(H13G_CONFIG)
    assert h13_source_policy_requested(h12) is False
    assert h13g_source_policy_requested(h12) is False
    assert h13_source_policy_requested(h13f) is True
    assert h13g_source_policy_requested(h13f) is False
    assert h13g_source_policy_requested(h13g) is True
    assert h13_source_policy_requested(h13g) is False
    assert h13g.schema_version == "r3a_l5_positive_control_h13g_source_pilot_v1"
    for mode in ("ci", "smoke", "full"):
        assert h13g.mode(mode).allows_full_campaign_disposition is False
    policy = load_h13g_source_policy(h13g, "full")
    assert policy.max_source_traces_per_c == 16
    assert policy.kinematic_refinement_max_depth == 8


def test_trace_and_cover_consumes_many_samples_with_one_fiber() -> None:
    seeds = (
        (0.00, 0.0, 0.0, 0.0, 0.0),
        (0.05, 0.0, 0.0, 0.0, 0.0),
        (0.10, 0.0, 0.0, 0.0, 0.0),
        (2.00, 0.0, 0.0, 0.0, 0.0),
    )

    def builder(seed: tuple[float, ...], trace_index: int) -> SourceControlFiber:
        if trace_index == 0:
            return _fiber("component_a", seeds[:3])
        return _fiber("component_b", (seed,))

    result = trace_and_cover_projected_seeds(
        seeds,
        max_traces=2,
        cover_tol_rad=0.11,
        trace_builder=builder,
    )
    assert result.trace_attempt_count == 2
    assert result.explained_projected_seed_count == 4
    assert result.unexplained_projected_seeds == ()
    assert result.trace_budget_exhausted is False


def test_trace_budget_blocks_only_when_unexplained_samples_remain() -> None:
    seeds = (
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0, 0.0, 0.0),
    )
    result = trace_and_cover_projected_seeds(
        seeds,
        max_traces=1,
        cover_tol_rad=0.1,
        trace_builder=lambda seed, _: _fiber("first", (seed,)),
    )
    assert result.trace_attempt_count == 1
    assert len(result.unexplained_projected_seeds) == 1
    assert result.trace_budget_exhausted is True


def test_real_opposite_rays_do_not_false_close_an_open_branch() -> None:
    problem = ParabolaProblem()
    trace = continue_implicit_branch(
        problem,
        np.array((0.0, 0.0)),
        max_steps=2,
        step_size=0.1,
    )
    diagnostic = source_trace_diagnostic_h13g(problem, trace, policy=_policy())
    assert diagnostic.closed is False
    assert diagnostic.termination is SourceTraceTermination.BUDGET_EXHAUSTED
    assert diagnostic.positive_ray_termination == "BUDGET_EXHAUSTED"
    assert diagnostic.negative_ray_termination == "BUDGET_EXHAUSTED"


def test_h13g_endpoint_closure_requires_two_budget_exhausted_rays() -> None:
    problem = UnitCircleProblem()
    trace = continue_implicit_branch(
        problem,
        np.array((1.0, 0.0)),
        max_steps=1,
        step_size=0.1,
    )
    diagnostic = source_trace_diagnostic_h13g(problem, trace, policy=_policy())
    assert diagnostic.closed is False
    assert diagnostic.termination is SourceTraceTermination.BUDGET_EXHAUSTED


def test_corrected_rasterization_preserves_position_and_h() -> None:
    config = load_campaign_config(H13G_CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    n = radial_normal(probe.p_star)
    seed = analytic_seed_configuration(arm.geometry, probe)
    c = h_value(arm, seed, n)
    problem = PointingLevelSetProblem(
        model=arm.model,
        p_star=probe.p_star,
        n=n,
        c=c,
        problem_id="raster_seed",
    )
    # The analytic home seed is rank-deficient; step along a null direction to a
    # regular chart before tracing, then rasterize that real fiber.
    vt = np.linalg.svd(
        np.asarray(problem.jacobian(np.asarray(seed, dtype=float)), dtype=float),
        full_matrices=True,
    )[2]
    regular_seed = tuple(float(value) for value in np.asarray(seed, dtype=float) + 0.2 * vt[-2])
    fiber = continue_source_fiber_h13g(
        arm,
        probe,
        n,
        c,
        regular_seed,
        fiber_id="raster_fixture",
        max_steps=3,
        policy=_policy(kinematic_refinement_max_depth=6),
    )
    assert fiber.q_samples
    assert fiber.termination_status != SourceTraceTermination.SINGULAR_OR_CRITICAL_ENDPOINT.value
    raster = rasterize_fiber_kinematically(
        arm,
        probe,
        n,
        fiber,
        max_segment_rad=0.05,
        max_depth=6,
    )
    assert raster.q_samples
    assert len(raster.q_samples) == len(raster.pointings)
    for q, direction in zip(raster.q_samples, raster.pointings, strict=True):
        state = arm.chain.evaluate(q)
        assert np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star)) <= 1e-8
        assert abs(pointing_scalar(direction, n) - c) <= 1e-8
    assert raster.max_position_residual_m <= 1e-8
    assert raster.max_h_residual <= 1e-8


def test_h13g_seed_count_vocabulary_is_not_component_vocabulary() -> None:
    assert TRACE_COUNT_SEMANTICS == "trace_attempts_not_expected_components"
