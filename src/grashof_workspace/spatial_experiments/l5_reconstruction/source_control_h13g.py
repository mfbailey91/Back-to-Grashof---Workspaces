"""R3A-H13G evidence-safe source ``h=c`` corrective path.

H13G is an opt-in diagnostic policy. It does not replace the H12 hub, does not
freeze an H13 source policy, and does not authorize interpretation of natural
UURU leaves.

Corrections relative to the H13A--F diagnostic path:

* the shared continuation engine must expose genuinely opposite signed rays;
* ray-local termination evidence is preserved before interval classification;
* projected seeds are traced by a trace-and-cover loop rather than truncated as
  though local seed clusters were components;
* only locally justified projection failures are blocking evidence; and
* occupancy is refined through corrected source-Q midpoints, never through
  unconstrained great-circle interpolation.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.branch_continuation import (
    RETURN_MIN_ARC,
    BranchTrace,
    ImplicitBranchProblem,
    branch_tangent,
    continue_implicit_branch,
)
from grashof_workspace.spatial_experiments.continuation import wrap_joint_delta
from grashof_workspace.spatial_experiments.implicit_manifold import ambient_distance
from grashof_workspace.spatial_experiments.parent_level_sets import (
    PointingLevelSetProblem,
    correct_to_levelset,
    pointing_scalar,
)

from .artifacts import finalize_stage
from .direct_truth import found_configurations
from .models import (
    CampaignConfig,
    DirectPointingTruth,
    FixedPointProbe,
    SourceControlCRecord,
    SourceTraceTermination,
    json_dumps_strict,
    json_object,
    resolve_stage_budgets,
    stage_envelope,
)
from .positive_control import PositiveControlArm, build_positive_control_arm
from .source_control import (
    H13G_POLICY_VERSION,
    SourceControlFiber,
    SourceControlResult,
    h_value,
    radial_normal,
)
from .source_control_h13 import (
    _load_discovery,
    analytical_c_interval,
    choose_analytical_c_values,
    classify_source_interval_status_h13,
    cluster_wrapped_q,
    confirmation_c_slice_spacing_rad,
    deduplicate_fibers_h13,
    unresolved_c_intervals_from_records_h13,
    wrapped_q_distance,
)
from .sphere_grid import build_sphere_grid, paint_pointings, pointing_geodesic

POLICY_VERSION = H13G_POLICY_VERSION
C_DOMAIN_POLICY = "analytical_regional_shell"
TRACE_COUNT_SEMANTICS = "trace_attempts_not_expected_components"
DEFAULT_C_SLICE_FRACTION = 0.75
Vec3 = tuple[float, float, float]
Q = tuple[float, ...]


@dataclass(frozen=True, slots=True)
class H13GSourcePolicy:
    c_slice_max_angular_spacing_cell_fraction: float
    discovery_q_precluster_tol_rad: float
    seed_h_window: float
    seed_precluster_q_tol_rad: float
    seed_projected_q_tol_rad: float
    dedup_q_tol_rad: float
    trace_cover_q_tol_rad: float
    max_seed_candidates_per_c: int
    max_source_traces_per_c: int
    endpoint_state_tol_rad: float
    endpoint_tangent_abs_dot_min: float
    curve_segment_fraction: float
    continuation_step_size: float
    kinematic_refinement_max_depth: int

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "policy_version": POLICY_VERSION,
                "c_domain_policy": C_DOMAIN_POLICY,
                "c_slice_max_angular_spacing_cell_fraction": (
                    self.c_slice_max_angular_spacing_cell_fraction
                ),
                "discovery_q_precluster_tol_rad": self.discovery_q_precluster_tol_rad,
                "seed_h_window": self.seed_h_window,
                "seed_precluster_q_tol_rad": self.seed_precluster_q_tol_rad,
                "seed_projected_q_tol_rad": self.seed_projected_q_tol_rad,
                "dedup_q_tol_rad": self.dedup_q_tol_rad,
                "trace_cover_q_tol_rad": self.trace_cover_q_tol_rad,
                "max_seed_candidates_per_c": self.max_seed_candidates_per_c,
                "max_source_traces_per_c": self.max_source_traces_per_c,
                "endpoint_state_tol_rad": self.endpoint_state_tol_rad,
                "endpoint_tangent_abs_dot_min": self.endpoint_tangent_abs_dot_min,
                "curve_segment_fraction": self.curve_segment_fraction,
                "continuation_step_size": self.continuation_step_size,
                "kinematic_refinement_max_depth": self.kinematic_refinement_max_depth,
            }
        )


@dataclass(frozen=True, slots=True)
class ProjectionDiscovery:
    candidate_configuration_count: int
    required_candidate_count: int
    exploratory_candidate_count: int
    projection_attempt_count: int
    projected_configuration_count: int
    projected_seed_cluster_count: int
    projected_seed_clusters: tuple[Q, ...]
    candidate_budget_exhausted: bool
    blocking_projection_failure_count: int
    diagnostic_projection_failure_count: int


@dataclass(frozen=True, slots=True)
class TraceCoverResult:
    fibers: tuple[SourceControlFiber, ...]
    trace_attempt_count: int
    explained_projected_seed_count: int
    failed_trace_seed_count: int
    unexplained_projected_seeds: tuple[Q, ...]
    trace_budget_exhausted: bool


@dataclass(frozen=True, slots=True)
class H13GTraceDiagnostic:
    termination: SourceTraceTermination
    closed: bool
    budget_exhausted: bool
    positive_accepted_steps: int
    negative_accepted_steps: int
    accepted_arclength: float
    endpoint_state_distance: float | None
    endpoint_tangent_abs_dot: float | None
    positive_ray_termination: str | None
    negative_ray_termination: str | None
    rejection_reason_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class KinematicRasterization:
    q_samples: tuple[Q, ...]
    pointings: tuple[Vec3, ...]
    complete: bool
    correction_failure_count: int
    depth_budget_exhausted: bool
    max_position_residual_m: float
    max_h_residual: float


@dataclass(frozen=True, slots=True)
class H13GSourceControlResult:
    inner: SourceControlResult
    analytical_c_interval: tuple[float, float]
    requested_c_value_count: int
    c_slice_max_angular_spacing_rad: float
    raw_pointing_sample_count: int
    rasterization_max_segment_rad: float
    policy: H13GSourcePolicy

    def to_json_dict(self) -> dict[str, Any]:
        payload = dict(self.inner.to_json_dict())
        payload.update(
            {
                "analytical_c_interval": list(self.analytical_c_interval),
                "c_domain_policy": C_DOMAIN_POLICY,
                "requested_c_value_count": self.requested_c_value_count,
                "effective_c_value_count": len(self.inner.c_values),
                "c_slice_max_angular_spacing_rad": self.c_slice_max_angular_spacing_rad,
                "raw_pointing_sample_count": self.raw_pointing_sample_count,
                "rasterized_pointing_sample_count": len(self.inner.pointing_samples),
                "rasterization_max_segment_rad": self.rasterization_max_segment_rad,
                "policy": self.policy.to_json_dict(),
            }
        )
        return json_object(payload)


def _mode_value(
    raw: Mapping[str, Any],
    key: str,
    mode: str,
    default: float,
) -> float:
    value = raw.get(key, default)
    if isinstance(value, Mapping):
        value = value.get(mode, default)
    if isinstance(default, int):
        return int(value)
    return float(value)


def load_h13g_source_policy(config: CampaignConfig, mode: str) -> H13GSourcePolicy:
    raw_value = config.raw.get("source_control", {})
    raw = raw_value if isinstance(raw_value, Mapping) else {}
    version = str(raw.get("policy_version", ""))
    if version != POLICY_VERSION:
        raise ValueError(
            f"H13G source module requires policy_version={POLICY_VERSION!r}, got {version!r}"
        )
    policy = H13GSourcePolicy(
        c_slice_max_angular_spacing_cell_fraction=float(
            _mode_value(
                raw,
                "c_slice_max_angular_spacing_cell_fraction",
                mode,
                DEFAULT_C_SLICE_FRACTION,
            )
        ),
        discovery_q_precluster_tol_rad=float(
            _mode_value(raw, "discovery_q_precluster_tol_rad", mode, 0.15)
        ),
        seed_h_window=float(_mode_value(raw, "seed_h_window", mode, 0.35)),
        seed_precluster_q_tol_rad=float(
            _mode_value(raw, "seed_precluster_q_tol_rad", mode, 0.35)
        ),
        seed_projected_q_tol_rad=float(
            _mode_value(raw, "seed_projected_q_tol_rad", mode, 0.20)
        ),
        dedup_q_tol_rad=float(_mode_value(raw, "dedup_q_tol_rad", mode, 0.35)),
        trace_cover_q_tol_rad=float(
            _mode_value(raw, "trace_cover_q_tol_rad", mode, 0.35)
        ),
        max_seed_candidates_per_c=int(
            _mode_value(raw, "max_seed_candidates_per_c", mode, 256)
        ),
        max_source_traces_per_c=int(
            _mode_value(raw, "max_source_traces_per_c", mode, 12)
        ),
        endpoint_state_tol_rad=float(
            _mode_value(raw, "endpoint_state_tol_rad", mode, 0.10)
        ),
        endpoint_tangent_abs_dot_min=float(
            _mode_value(raw, "endpoint_tangent_abs_dot_min", mode, 0.85)
        ),
        curve_segment_fraction=float(
            _mode_value(raw, "curve_segment_fraction", mode, 0.50)
        ),
        continuation_step_size=float(
            _mode_value(raw, "continuation_step_size", mode, 0.08)
        ),
        kinematic_refinement_max_depth=int(
            _mode_value(raw, "kinematic_refinement_max_depth", mode, 8)
        ),
    )
    positive = (
        policy.c_slice_max_angular_spacing_cell_fraction,
        policy.discovery_q_precluster_tol_rad,
        policy.seed_h_window,
        policy.seed_precluster_q_tol_rad,
        policy.seed_projected_q_tol_rad,
        policy.dedup_q_tol_rad,
        policy.trace_cover_q_tol_rad,
        policy.endpoint_state_tol_rad,
        policy.endpoint_tangent_abs_dot_min,
        policy.curve_segment_fraction,
        policy.continuation_step_size,
    )
    if any(value <= 0.0 for value in positive):
        raise ValueError("H13G tolerances and spacing fractions must be positive")
    if policy.max_seed_candidates_per_c <= 0 or policy.max_source_traces_per_c <= 0:
        raise ValueError("H13G candidate and trace budgets must be positive")
    if policy.kinematic_refinement_max_depth <= 0:
        raise ValueError("H13G kinematic refinement depth must be positive")
    if policy.endpoint_tangent_abs_dot_min > 1.0:
        raise ValueError("endpoint tangent absolute-dot threshold must be <= 1")
    return policy


def _required_candidate_indices(
    arm: PositiveControlArm,
    configurations: tuple[Q, ...],
    n: Vec3,
    c: float,
    *,
    seed_h_window: float,
) -> frozenset[int]:
    required = {
        index
        for index, q in enumerate(configurations)
        if abs(h_value(arm, q, n) - c) <= seed_h_window
    }
    if not required and configurations:
        required.add(
            min(
                range(len(configurations)),
                key=lambda index: abs(h_value(arm, configurations[index], n) - c),
            )
        )
    return frozenset(required)


def discover_projected_source_seeds(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    n: Vec3,
    c: float,
    configurations: tuple[Q, ...],
    *,
    policy: H13GSourcePolicy,
) -> ProjectionDiscovery:
    preclustered = cluster_wrapped_q(
        configurations,
        tol=policy.seed_precluster_q_tol_rad,
    )
    required_indices = _required_candidate_indices(
        arm,
        preclustered,
        n,
        c,
        seed_h_window=policy.seed_h_window,
    )
    ordered_indices = tuple(
        sorted(
            range(len(preclustered)),
            key=lambda index: (
                index not in required_indices,
                abs(h_value(arm, preclustered[index], n) - c),
                preclustered[index],
            ),
        )
    )
    attempted_indices = ordered_indices[: policy.max_seed_candidates_per_c]
    projected: list[Q] = []
    blocking_failures = 0
    diagnostic_failures = 0
    for index in attempted_indices:
        seed = preclustered[index]
        q_projected, ok, _ = correct_to_levelset(arm.model, seed, probe.p_star, n, c)
        if ok:
            projected.append(tuple(float(value) for value in q_projected))
        elif index in required_indices:
            blocking_failures += 1
        else:
            diagnostic_failures += 1
    projected_clusters = cluster_wrapped_q(
        projected,
        tol=policy.seed_projected_q_tol_rad,
    )
    return ProjectionDiscovery(
        candidate_configuration_count=len(preclustered),
        required_candidate_count=len(required_indices),
        exploratory_candidate_count=max(0, len(preclustered) - len(required_indices)),
        projection_attempt_count=len(attempted_indices),
        projected_configuration_count=len(projected),
        projected_seed_cluster_count=len(projected_clusters),
        projected_seed_clusters=projected_clusters,
        candidate_budget_exhausted=(
            len(preclustered) > policy.max_seed_candidates_per_c
        ),
        blocking_projection_failure_count=blocking_failures,
        diagnostic_projection_failure_count=diagnostic_failures,
    )


def _seed_to_fiber_distance(seed: Q, fiber: SourceControlFiber) -> float:
    if not fiber.q_samples:
        return float("inf")
    return min(wrapped_q_distance(seed, sample) for sample in fiber.q_samples)


def trace_and_cover_projected_seeds(
    projected_seeds: tuple[Q, ...],
    *,
    max_traces: int,
    cover_tol_rad: float,
    trace_builder: Callable[[Q, int], SourceControlFiber],
) -> TraceCoverResult:
    """Trace unexplained projected seeds; one fiber may explain many seed samples."""

    pending = list(projected_seeds)
    fibers: list[SourceControlFiber] = []
    explained = 0
    failed = 0
    while pending and len(fibers) < max_traces:
        seed = pending[0]
        fiber = trace_builder(seed, len(fibers))
        fibers.append(fiber)
        if not fiber.q_samples:
            failed += 1
            pending = pending[1:]
            continue
        remaining: list[Q] = []
        removed = 0
        for candidate in pending:
            if _seed_to_fiber_distance(candidate, fiber) <= cover_tol_rad:
                removed += 1
            else:
                remaining.append(candidate)
        if removed <= 0:
            removed = 1
            remaining = pending[1:]
        explained += removed
        pending = remaining
    return TraceCoverResult(
        fibers=tuple(fibers),
        trace_attempt_count=len(fibers),
        explained_projected_seed_count=explained,
        failed_trace_seed_count=failed,
        unexplained_projected_seeds=tuple(pending),
        trace_budget_exhausted=bool(pending),
    )


def _ray_termination(trace: BranchTrace, direction: str) -> str | None:
    for record in trace.ray_records:
        if record.direction == direction:
            return record.termination
    return None


def source_trace_diagnostic_h13g(
    problem: ImplicitBranchProblem,
    trace: BranchTrace,
    *,
    policy: H13GSourcePolicy,
) -> H13GTraceDiagnostic:
    accepted = tuple(step for step in trace.steps if step.accepted and step.x is not None)
    positive = tuple(step for step in accepted if step.s > 1e-12)
    negative = tuple(step for step in accepted if step.s < -1e-12)
    rejected = Counter(
        str(step.rejection_reason)
        for step in trace.steps
        if not step.accepted and step.rejection_reason is not None
    )
    positive_arc = max((float(step.s) for step in positive), default=0.0)
    negative_arc = abs(min((float(step.s) for step in negative), default=0.0))
    accepted_arclength = positive_arc + negative_arc
    positive_term = _ray_termination(trace, "positive")
    negative_term = _ray_termination(trace, "negative")
    ray_terms = {term for term in (positive_term, negative_term) if term is not None}
    budget_exhausted = "BUDGET_EXHAUSTED" in ray_terms
    endpoint_distance: float | None = None
    endpoint_tangent_abs_dot: float | None = None
    closed = bool(trace.returned)
    termination = SourceTraceTermination.RETURNED_TO_SEED
    if not trace.returned:
        endpoint_meeting_eligible = bool(
            positive_term == "BUDGET_EXHAUSTED"
            and negative_term == "BUDGET_EXHAUSTED"
            and positive
            and negative
        )
        if endpoint_meeting_eligible:
            x_positive = np.asarray(max(positive, key=lambda step: step.s).x, dtype=float)
            x_negative = np.asarray(min(negative, key=lambda step: step.s).x, dtype=float)
            endpoint_distance = float(
                ambient_distance(x_positive, x_negative, problem.periodic_coordinates)
            )
            try:
                t_positive = branch_tangent(problem, x_positive)
                t_negative = branch_tangent(problem, x_negative)
                endpoint_tangent_abs_dot = abs(float(np.dot(t_positive, t_negative)))
            except (ValueError, np.linalg.LinAlgError):
                endpoint_tangent_abs_dot = None
            closed = bool(
                accepted_arclength >= RETURN_MIN_ARC
                and endpoint_distance <= policy.endpoint_state_tol_rad
                and endpoint_tangent_abs_dot is not None
                and endpoint_tangent_abs_dot >= policy.endpoint_tangent_abs_dot_min
            )
        if closed:
            termination = SourceTraceTermination.PLUS_MINUS_ENDPOINTS_CLOSED
        elif "SINGULAR" in ray_terms:
            termination = SourceTraceTermination.SINGULAR_OR_CRITICAL_ENDPOINT
        elif "CORRECTOR_FAILURE" in ray_terms:
            termination = SourceTraceTermination.CORRECTOR_FAILURE
        elif budget_exhausted:
            termination = SourceTraceTermination.BUDGET_EXHAUSTED
        else:
            termination = SourceTraceTermination.OPEN_UNCLASSIFIED
    return H13GTraceDiagnostic(
        termination=termination,
        closed=closed,
        budget_exhausted=budget_exhausted,
        positive_accepted_steps=len(positive),
        negative_accepted_steps=len(negative),
        accepted_arclength=accepted_arclength,
        endpoint_state_distance=endpoint_distance,
        endpoint_tangent_abs_dot=endpoint_tangent_abs_dot,
        positive_ray_termination=positive_term,
        negative_ray_termination=negative_term,
        rejection_reason_counts=dict(rejected),
    )


def continue_source_fiber_h13g(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    n: Vec3,
    c: float,
    q_seed: Q,
    *,
    fiber_id: str,
    max_steps: int,
    policy: H13GSourcePolicy,
) -> SourceControlFiber:
    q_projected, ok, _ = correct_to_levelset(arm.model, q_seed, probe.p_star, n, c)
    if not ok:
        return SourceControlFiber(
            fiber_id=fiber_id,
            c=c,
            q_samples=(),
            pointing_samples=(),
            branch_status="unresolved",
            returned=False,
            max_position_residual_m=float("inf"),
            max_h_residual=float("inf"),
            closed=False,
            termination_status=SourceTraceTermination.PROJECTION_FAILED.value,
            rejection_reason_counts={},
        )
    problem = PointingLevelSetProblem(
        model=arm.model,
        p_star=probe.p_star,
        n=n,
        c=c,
        problem_id=fiber_id,
    )
    try:
        trace = continue_implicit_branch(
            problem,
            np.asarray(q_projected, dtype=float),
            branch_id=fiber_id,
            max_steps=max_steps,
            step_size=policy.continuation_step_size,
        )
    except ValueError:
        q_fail = tuple(float(value) for value in q_projected)
        state = arm.chain.evaluate(q_fail)
        return SourceControlFiber(
            fiber_id=fiber_id,
            c=c,
            q_samples=(q_fail,),
            pointing_samples=(as_vec3(state.d),),
            branch_status="singular",
            returned=False,
            max_position_residual_m=float(
                np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star))
            ),
            max_h_residual=abs(pointing_scalar(state.d, n) - c),
            closed=False,
            termination_status=SourceTraceTermination.SINGULAR_OR_CRITICAL_ENDPOINT.value,
            rejection_reason_counts={},
            positive_ray_termination="SINGULAR",
            negative_ray_termination=None,
        )
    diagnostic = source_trace_diagnostic_h13g(problem, trace, policy=policy)
    qs: list[Q] = []
    directions: list[Vec3] = []
    position_residuals: list[float] = []
    h_residuals: list[float] = []
    for step in trace.steps:
        if not step.accepted or step.x is None:
            continue
        q = tuple(float(value) for value in step.x)
        state = arm.chain.evaluate(q)
        qs.append(q)
        directions.append(as_vec3(state.d))
        position_residuals.append(
            float(np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star)))
        )
        h_residuals.append(abs(pointing_scalar(state.d, n) - c))
    branch_status = "returned" if diagnostic.closed else str(trace.branch_status)
    if diagnostic.termination is SourceTraceTermination.BUDGET_EXHAUSTED:
        branch_status = "budget_exhausted"
    return SourceControlFiber(
        fiber_id=fiber_id,
        c=c,
        q_samples=tuple(qs),
        pointing_samples=tuple(directions),
        branch_status=branch_status,
        returned=bool(trace.returned),
        max_position_residual_m=(
            max(position_residuals) if position_residuals else float("inf")
        ),
        max_h_residual=max(h_residuals) if h_residuals else float("inf"),
        closed=diagnostic.closed,
        termination_status=diagnostic.termination.value,
        budget_exhausted=diagnostic.budget_exhausted,
        positive_accepted_steps=diagnostic.positive_accepted_steps,
        negative_accepted_steps=diagnostic.negative_accepted_steps,
        accepted_arclength=diagnostic.accepted_arclength,
        endpoint_state_distance=diagnostic.endpoint_state_distance,
        endpoint_tangent_abs_dot=diagnostic.endpoint_tangent_abs_dot,
        rejection_reason_counts=diagnostic.rejection_reason_counts,
        positive_ray_termination=diagnostic.positive_ray_termination,
        negative_ray_termination=diagnostic.negative_ray_termination,
    )


def _wrapped_midpoint(a: Q, b: Q) -> Q:
    qa = np.asarray(a, dtype=float)
    mid = qa + 0.5 * wrap_joint_delta(b, a)
    wrapped = np.arctan2(np.sin(mid), np.cos(mid))
    return tuple(float(value) for value in wrapped)


def _refine_segment(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    n: Vec3,
    c: float,
    q_a: Q,
    d_a: Vec3,
    q_b: Q,
    d_b: Vec3,
    *,
    max_segment_rad: float,
    max_depth: int,
    depth: int,
) -> tuple[list[tuple[Q, Vec3]], int, bool]:
    if pointing_geodesic(d_a, d_b) <= max_segment_rad:
        return [(q_b, d_b)], 0, False
    if depth >= max_depth:
        return [(q_b, d_b)], 0, True
    q_guess = _wrapped_midpoint(q_a, q_b)
    q_mid, ok, _ = correct_to_levelset(arm.model, q_guess, probe.p_star, n, c)
    if not ok:
        return [(q_b, d_b)], 1, False
    q_mid_tuple = tuple(float(value) for value in q_mid)
    d_mid = as_vec3(arm.chain.evaluate(q_mid_tuple).d)
    left, left_failures, left_budget = _refine_segment(
        arm,
        probe,
        n,
        c,
        q_a,
        d_a,
        q_mid_tuple,
        d_mid,
        max_segment_rad=max_segment_rad,
        max_depth=max_depth,
        depth=depth + 1,
    )
    right, right_failures, right_budget = _refine_segment(
        arm,
        probe,
        n,
        c,
        q_mid_tuple,
        d_mid,
        q_b,
        d_b,
        max_segment_rad=max_segment_rad,
        max_depth=max_depth,
        depth=depth + 1,
    )
    return (
        [*left, *right],
        left_failures + right_failures,
        left_budget or right_budget,
    )


def rasterize_fiber_kinematically(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    n: Vec3,
    fiber: SourceControlFiber,
    *,
    max_segment_rad: float,
    max_depth: int,
) -> KinematicRasterization:
    if not fiber.q_samples:
        return KinematicRasterization(
            q_samples=(),
            pointings=(),
            complete=False,
            correction_failure_count=1,
            depth_budget_exhausted=False,
            max_position_residual_m=float("inf"),
            max_h_residual=float("inf"),
        )
    pairs = list(zip(fiber.q_samples, fiber.pointing_samples, strict=True))
    out: list[tuple[Q, Vec3]] = [pairs[0]]
    correction_failures = 0
    depth_budget = False
    segment_pairs = list(pairwise(pairs))
    if fiber.closed or fiber.returned:
        segment_pairs.append((pairs[-1], pairs[0]))
    for pair_index, ((q_a, d_a), (q_b, d_b)) in enumerate(segment_pairs):
        refined, failures, exhausted = _refine_segment(
            arm,
            probe,
            n,
            fiber.c,
            q_a,
            d_a,
            q_b,
            d_b,
            max_segment_rad=max_segment_rad,
            max_depth=max_depth,
            depth=0,
        )
        correction_failures += failures
        depth_budget = depth_budget or exhausted
        final_closure = fiber.closed or fiber.returned
        for item_index, item in enumerate(refined):
            closes_to_first = (
                final_closure
                and pair_index == len(segment_pairs) - 1
                and item_index == len(refined) - 1
            )
            if not closes_to_first:
                out.append(item)
    position_residuals: list[float] = []
    h_residuals: list[float] = []
    for q, direction in out:
        state = arm.chain.evaluate(q)
        position_residuals.append(
            float(np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star)))
        )
        h_residuals.append(abs(pointing_scalar(direction, n) - fiber.c))
    return KinematicRasterization(
        q_samples=tuple(item[0] for item in out),
        pointings=tuple(item[1] for item in out),
        complete=correction_failures == 0 and not depth_budget,
        correction_failure_count=correction_failures,
        depth_budget_exhausted=depth_budget,
        max_position_residual_m=max(position_residuals),
        max_h_residual=max(h_residuals),
    )


def _fiber_kind(fiber: SourceControlFiber) -> str:
    if fiber.closed:
        return "closed"
    if fiber.termination_status == SourceTraceTermination.BUDGET_EXHAUSTED.value:
        return "budget_exhausted"
    if fiber.termination_status == SourceTraceTermination.SINGULAR_OR_CRITICAL_ENDPOINT.value:
        return "singular"
    if fiber.termination_status in {
        SourceTraceTermination.PROJECTION_FAILED.value,
        SourceTraceTermination.CORRECTOR_FAILURE.value,
    } or not fiber.q_samples:
        return "unresolved"
    return "open"


def summarize_c_records_h13g(
    c_values: tuple[float, ...],
    *,
    projections: dict[float, ProjectionDiscovery],
    covers: dict[float, TraceCoverResult],
    fibers: tuple[SourceControlFiber, ...],
) -> tuple[SourceControlCRecord, ...]:
    records: list[SourceControlCRecord] = []
    for index, c in enumerate(c_values):
        projection = projections[float(c)]
        cover = covers[float(c)]
        group = tuple(item for item in fibers if abs(item.c - c) <= 1e-12)
        kinds = tuple(_fiber_kind(item) for item in group)
        returned = sum(1 for item in group if item.returned)
        endpoint_closed = sum(
            1
            for item in group
            if item.termination_status
            == SourceTraceTermination.PLUS_MINUS_ENDPOINTS_CLOSED.value
        )
        closed = sum(1 for kind in kinds if kind == "closed")
        budget_count = sum(1 for kind in kinds if kind == "budget_exhausted")
        open_count = sum(1 for kind in kinds if kind == "open")
        singular = sum(1 for kind in kinds if kind == "singular")
        trace_unresolved = sum(1 for kind in kinds if kind == "unresolved")
        rasterization_incomplete = sum(
            1 for item in group if item.rasterization_complete is False
        )
        unresolved = (
            trace_unresolved
            + projection.blocking_projection_failure_count
            + rasterization_incomplete
        )
        corrector_failures = sum(
            1
            for item in group
            if item.termination_status == SourceTraceTermination.CORRECTOR_FAILURE.value
        )
        required = not (
            abs(c - c_values[0]) <= 1e-12 or abs(c - c_values[-1]) <= 1e-12
        )
        aggregate_budget = (
            projection.candidate_budget_exhausted or cover.trace_budget_exhausted
        )
        status = classify_source_interval_status_h13(
            closed_count=closed,
            open_count=open_count,
            singular_count=singular,
            unresolved_count=unresolved,
            budget_exhausted_count=budget_count,
            seed_budget_exhausted=aggregate_budget,
            required=required,
        )
        records.append(
            SourceControlCRecord(
                c=float(c),
                expected_seed_count=cover.trace_attempt_count,
                projected_seed_count=projection.projected_configuration_count,
                continued_component_count=sum(1 for item in group if item.q_samples),
                returned_count=returned,
                open_count=open_count,
                singular_count=singular,
                unresolved_count=unresolved,
                deduplicated_component_ids=tuple(
                    item.fiber_id for item in group if item.q_samples
                ),
                parameter_interval_status=status.value,
                candidate_seed_count=projection.candidate_configuration_count,
                projection_attempt_count=projection.projection_attempt_count,
                attempted_seed_count=cover.trace_attempt_count,
                projected_seed_cluster_count=projection.projected_seed_cluster_count,
                projection_failure_count=(
                    projection.blocking_projection_failure_count
                    + projection.diagnostic_projection_failure_count
                ),
                seed_budget_exhausted=aggregate_budget,
                required=required,
                domain_boundary=index in {0, len(c_values) - 1},
                closed_count=closed,
                endpoint_closed_count=endpoint_closed,
                budget_exhausted_count=budget_count,
                corrector_failure_count=corrector_failures,
                closure_kind_counts=dict(
                    Counter(
                        item.termination_status
                        for item in group
                        if item.termination_status is not None
                    )
                ),
                seed_count_semantics=TRACE_COUNT_SEMANTICS,
                required_candidate_count=projection.required_candidate_count,
                exploratory_candidate_count=projection.exploratory_candidate_count,
                candidate_budget_exhausted=projection.candidate_budget_exhausted,
                blocking_projection_failure_count=(
                    projection.blocking_projection_failure_count
                ),
                diagnostic_projection_failure_count=(
                    projection.diagnostic_projection_failure_count
                ),
                trace_attempt_count=cover.trace_attempt_count,
                explained_projected_seed_count=(
                    cover.explained_projected_seed_count
                ),
                failed_trace_seed_count=cover.failed_trace_seed_count,
                unexplained_projected_seed_count=len(
                    cover.unexplained_projected_seeds
                ),
                trace_budget_exhausted=cover.trace_budget_exhausted,
                rasterization_incomplete_count=rasterization_incomplete,
            )
        )
    return tuple(records)


def build_source_control_h13g(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    discovery: DirectPointingTruth,
    *,
    config: CampaignConfig,
    mode: str,
    max_steps: int | None = None,
) -> H13GSourceControlResult:
    policy = load_h13g_source_policy(config, mode)
    budgets = resolve_stage_budgets(config, mode)
    interval = analytical_c_interval(arm, probe)
    spacing = confirmation_c_slice_spacing_rad(
        budgets.confirmation_icosphere_level,
        policy.c_slice_max_angular_spacing_cell_fraction,
    )
    c_values = choose_analytical_c_values(
        interval,
        budgets.source_c_value_count,
        max_angular_spacing_rad=spacing,
    )
    n = radial_normal(probe.p_star)
    discovery_configs = cluster_wrapped_q(
        found_configurations(discovery),
        tol=policy.discovery_q_precluster_tol_rad,
    )
    steps = budgets.continuation_steps if max_steps is None else max_steps
    projections: dict[float, ProjectionDiscovery] = {}
    covers: dict[float, TraceCoverResult] = {}
    traced: list[SourceControlFiber] = []
    for c_index, c in enumerate(c_values):
        projection = discover_projected_source_seeds(
            arm,
            probe,
            n,
            c,
            discovery_configs,
            policy=policy,
        )
        projections[float(c)] = projection

        def trace_builder(
            seed: Q,
            trace_index: int,
            *,
            c_value: float = float(c),
            bin_index: int = int(c_index),
        ) -> SourceControlFiber:
            return continue_source_fiber_h13g(
                arm,
                probe,
                n,
                c_value,
                seed,
                fiber_id=f"{probe.probe_id}_c{bin_index}_t{trace_index}",
                max_steps=steps,
                policy=policy,
            )

        cover = trace_and_cover_projected_seeds(
            projection.projected_seed_clusters,
            max_traces=policy.max_source_traces_per_c,
            cover_tol_rad=policy.trace_cover_q_tol_rad,
            trace_builder=trace_builder,
        )
        covers[float(c)] = cover
        traced.extend(cover.fibers)
    unique = deduplicate_fibers_h13(tuple(traced), tol=policy.dedup_q_tol_rad)
    grid = build_sphere_grid(budgets.confirmation_icosphere_level)
    max_segment = policy.curve_segment_fraction * grid.max_cell_diameter_rad
    enriched: list[SourceControlFiber] = []
    raw_pointing_count = 0
    for fiber in unique:
        raw_pointing_count += len(fiber.pointing_samples)
        raster = rasterize_fiber_kinematically(
            arm,
            probe,
            n,
            fiber,
            max_segment_rad=max_segment,
            max_depth=policy.kinematic_refinement_max_depth,
        )
        enriched.append(
            replace(
                fiber,
                rasterized_pointing_samples=raster.pointings,
                rasterization_complete=raster.complete,
                rasterization_failure_count=raster.correction_failure_count,
                rasterization_budget_exhausted=raster.depth_budget_exhausted,
                max_rasterized_position_residual_m=(
                    raster.max_position_residual_m
                ),
                max_rasterized_h_residual=raster.max_h_residual,
            )
        )
    fibers = tuple(enriched)
    pointings = tuple(
        direction
        for fiber in fibers
        for direction in (fiber.rasterized_pointing_samples or fiber.pointing_samples)
    )
    hits = paint_pointings(grid, pointings)
    records = summarize_c_records_h13g(
        c_values,
        projections=projections,
        covers=covers,
        fibers=fibers,
    )
    unresolved = unresolved_c_intervals_from_records_h13(c_values, records)
    inner = SourceControlResult(
        probe_id=probe.probe_id,
        n=n,
        c_values=c_values,
        fibers=fibers,
        pointing_samples=pointings,
        hit_cells=hits,
        unresolved_c_intervals=unresolved,
        notes=(
            "H13G source h=c control; not a natural UURU child.",
            "The H12 compact hub remains authoritative and is not replaced.",
            "Opposite-ray semantics are regression-locked in the shared continuation engine.",
            "Ray-local termination is serialized before interval classification.",
            "Projected samples are consumed by trace-and-cover; they are not called components.",
            "Only locally justified projection failures are blocking evidence.",
            "Rasterized occupancy uses corrected source-Q midpoints and preserves p=p* and h=c.",
            "H13G is diagnostic and cannot issue a full-campaign disposition.",
            f"seed_count_semantics={TRACE_COUNT_SEMANTICS}.",
        ),
        c_records=records,
    )
    return H13GSourceControlResult(
        inner=inner,
        analytical_c_interval=interval,
        requested_c_value_count=budgets.source_c_value_count,
        c_slice_max_angular_spacing_rad=spacing,
        raw_pointing_sample_count=raw_pointing_count,
        rasterization_max_segment_rad=max_segment,
        policy=policy,
    )


def write_source_control_stage_h13g(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
) -> dict[str, Any]:
    arm = build_positive_control_arm(config.geometry)
    budgets = resolve_stage_budgets(config, mode)
    records: list[dict[str, Any]] = []
    for probe in probes:
        truth_path = outdir / probe.probe_id / "direct_truth.json"
        if not truth_path.is_file():
            raise FileNotFoundError(f"missing prerequisite {truth_path}")
        raw = json.loads(truth_path.read_text(encoding="utf-8"))
        discovery = _load_discovery(raw["discovery"])
        result = build_source_control_h13g(
            arm,
            probe,
            discovery,
            config=config,
            mode=mode,
        )
        path = outdir / probe.probe_id / "source_control.json"
        path.write_text(json_dumps_strict(result.to_json_dict()), encoding="utf-8")
        records.append(
            {"probe_id": probe.probe_id, "fiber_count": len(result.inner.fibers)}
        )
    summary = {
        **stage_envelope(
            config,
            stage="source-control",
            mode=mode,
            probe_ids=tuple(probe.probe_id for probe in probes),
        ),
        "probes": records,
        "source_control_policy_version": POLICY_VERSION,
        "allows_full_campaign_disposition": budgets.allows_full_campaign_disposition,
        "limitations": [
            "H13G is a diagnostic corrective policy and cannot issue full-campaign disposition"
        ],
    }
    return finalize_stage(
        outdir,
        summary,
        config=config,
        stage="source-control",
        mode=mode,
        probe_ids=tuple(probe.probe_id for probe in probes),
    )
