"""H13 opt-in source ``h=c`` policy: analytical c, projected seeds, honest traces.

This module is selected only when ``source_control.policy_version`` equals
``h13_component_closure_v1``. The frozen H12 config keeps the historical
``source_control.py`` path, including the silent first-three seed rule.
Curve rasterization remains H13D.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from math import acos, ceil, cos
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
    PointingSolutionCluster,
    PointingSolveStatus,
    PointingTargetSolve,
    SourceControlCRecord,
    SourceIntervalStatus,
    SourceTraceTermination,
    json_dumps_strict,
    json_object,
    resolve_stage_budgets,
    stage_envelope,
)
from .positive_control import PositiveControlArm, build_positive_control_arm
from .source_control import (
    H13_POLICY_VERSION,
    SourceControlFiber,
    SourceControlResult,
    directed_q_distance,
    h_value,
    radial_normal,
)
from .sphere_grid import build_sphere_grid, paint_pointings

POLICY_VERSION = H13_POLICY_VERSION
C_DOMAIN_POLICY = "analytical_regional_shell"
C_DOMAIN_FORMULA = (
    "c_min=max(-1,(rho^2+t^2-r_max^2)/(2*rho*t)); "
    "c_max=min(1,(rho^2+t^2-r_min^2)/(2*rho*t))"
)
SEED_COUNT_SEMANTICS = "attempted_projected_seed_clusters_not_expected_components"
DEFAULT_C_SLICE_FRACTION = 0.75
COVERED_H13_INTERVAL_STATUSES = frozenset(
    {
        SourceIntervalStatus.RETURNED_SET_FOUND,
        SourceIntervalStatus.COMPONENT_COMPLETE,
    }
)
Vec3 = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class H13ASourcePolicy:
    c_slice_max_angular_spacing_cell_fraction: float
    discovery_q_precluster_tol_rad: float
    seed_h_window: float
    seed_precluster_q_tol_rad: float
    seed_projected_q_tol_rad: float
    dedup_q_tol_rad: float
    max_seed_candidates_per_c: int
    max_seed_clusters_per_c: int
    endpoint_state_tol_rad: float
    endpoint_tangent_abs_dot_min: float

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
                "max_seed_candidates_per_c": self.max_seed_candidates_per_c,
                "max_seed_clusters_per_c": self.max_seed_clusters_per_c,
                "endpoint_state_tol_rad": self.endpoint_state_tol_rad,
                "endpoint_tangent_abs_dot_min": self.endpoint_tangent_abs_dot_min,
            }
        )


@dataclass(frozen=True, slots=True)
class SourceTraceDiagnostic:
    termination: SourceTraceTermination
    closed: bool
    budget_exhausted: bool
    positive_accepted_steps: int
    negative_accepted_steps: int
    accepted_arclength: float
    endpoint_state_distance: float | None
    endpoint_tangent_abs_dot: float | None
    rejection_reason_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class SourceSeedDiscovery:
    candidate_configuration_count: int
    projection_attempt_count: int
    projected_configuration_count: int
    projected_seed_cluster_count: int
    seed_clusters: tuple[tuple[float, ...], ...]
    budget_exhausted: bool


@dataclass(frozen=True, slots=True)
class H13ASourceControlResult:
    inner: SourceControlResult
    analytical_c_interval: tuple[float, float]
    requested_c_value_count: int
    c_slice_max_angular_spacing_rad: float
    policy: H13ASourcePolicy

    def to_json_dict(self) -> dict[str, Any]:
        payload = dict(self.inner.to_json_dict())
        payload.update(
            {
                "analytical_c_interval": list(self.analytical_c_interval),
                "c_domain_formula": C_DOMAIN_FORMULA,
                "c_domain_policy": C_DOMAIN_POLICY,
                "requested_c_value_count": self.requested_c_value_count,
                "effective_c_value_count": len(self.inner.c_values),
                "c_slice_max_angular_spacing_rad": self.c_slice_max_angular_spacing_rad,
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


def load_h13_source_policy(config: CampaignConfig, mode: str | None = None) -> H13ASourcePolicy:
    raw_value = config.raw.get("source_control", {})
    raw = raw_value if isinstance(raw_value, Mapping) else {}
    version = str(raw.get("policy_version", ""))
    if version != POLICY_VERSION:
        raise ValueError(
            f"H13 source module requires policy_version={POLICY_VERSION!r}, got {version!r}"
        )
    resolved_mode = "ci" if mode is None else mode
    policy = H13ASourcePolicy(
        c_slice_max_angular_spacing_cell_fraction=float(
            _mode_value(
                raw,
                "c_slice_max_angular_spacing_cell_fraction",
                resolved_mode,
                DEFAULT_C_SLICE_FRACTION,
            )
        ),
        discovery_q_precluster_tol_rad=float(
            _mode_value(raw, "discovery_q_precluster_tol_rad", resolved_mode, 0.15)
        ),
        seed_h_window=float(_mode_value(raw, "seed_h_window", resolved_mode, 0.35)),
        seed_precluster_q_tol_rad=float(
            _mode_value(raw, "seed_precluster_q_tol_rad", resolved_mode, 0.35)
        ),
        seed_projected_q_tol_rad=float(
            _mode_value(raw, "seed_projected_q_tol_rad", resolved_mode, 0.20)
        ),
        dedup_q_tol_rad=float(_mode_value(raw, "dedup_q_tol_rad", resolved_mode, 0.35)),
        max_seed_candidates_per_c=int(
            _mode_value(raw, "max_seed_candidates_per_c", resolved_mode, 256)
        ),
        max_seed_clusters_per_c=int(
            _mode_value(raw, "max_seed_clusters_per_c", resolved_mode, 12)
        ),
        endpoint_state_tol_rad=float(
            _mode_value(raw, "endpoint_state_tol_rad", resolved_mode, 0.10)
        ),
        endpoint_tangent_abs_dot_min=float(
            _mode_value(raw, "endpoint_tangent_abs_dot_min", resolved_mode, 0.85)
        ),
    )
    positive = (
        policy.c_slice_max_angular_spacing_cell_fraction,
        policy.discovery_q_precluster_tol_rad,
        policy.seed_h_window,
        policy.seed_precluster_q_tol_rad,
        policy.seed_projected_q_tol_rad,
        policy.dedup_q_tol_rad,
        policy.endpoint_state_tol_rad,
        policy.endpoint_tangent_abs_dot_min,
    )
    if any(value <= 0.0 for value in positive):
        raise ValueError("H13 source policy tolerances and spacing fractions must be positive")
    if policy.max_seed_candidates_per_c <= 0 or policy.max_seed_clusters_per_c <= 0:
        raise ValueError("H13 source seed budgets must be positive")
    if policy.endpoint_tangent_abs_dot_min > 1.0:
        raise ValueError("endpoint tangent absolute-dot threshold must be <= 1")
    return policy


def analytical_c_interval(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
) -> tuple[float, float]:
    """Exact feasible interval of ``c=n·d`` using declared ``rho_m``, not ``||p*||``."""

    rho = float(probe.rho)
    tool = float(arm.geometry.tool_offset)
    if rho <= 0.0 or tool <= 0.0:
        raise ValueError("analytical c interval requires positive rho and tool offset")
    denominator = 2.0 * rho * tool
    lo = (rho * rho + tool * tool - arm.geometry.r_max**2) / denominator
    hi = (rho * rho + tool * tool - arm.geometry.r_min**2) / denominator
    lo = max(-1.0, float(lo))
    hi = min(1.0, float(hi))
    if lo > hi + 1e-12:
        raise ValueError(f"empty analytical c interval for {probe.probe_id}: {(lo, hi)}")
    if lo > hi:
        midpoint = 0.5 * (lo + hi)
        return midpoint, midpoint
    return lo, hi


def choose_analytical_c_values(
    c_interval: tuple[float, float],
    requested_count: int,
    *,
    max_angular_spacing_rad: float,
) -> tuple[float, ...]:
    """Include analytical endpoints and satisfy a pointing-angle slice spacing."""

    if requested_count <= 0:
        raise ValueError("source c count must be positive")
    if max_angular_spacing_rad <= 0.0:
        raise ValueError("source c angular spacing must be positive")
    lo, hi = float(c_interval[0]), float(c_interval[1])
    if lo > hi:
        raise ValueError("source c interval must be ordered")
    theta_min = acos(float(np.clip(hi, -1.0, 1.0)))
    theta_max = acos(float(np.clip(lo, -1.0, 1.0)))
    required_count = ceil((theta_max - theta_min) / max_angular_spacing_rad) + 1
    count = max(requested_count, required_count)
    if count == 1 or abs(theta_max - theta_min) <= 1e-12:
        return (0.5 * (lo + hi),)
    theta = np.linspace(theta_max, theta_min, count)
    values = tuple(float(cos(float(item))) for item in theta)
    return (lo, *values[1:-1], hi)


def confirmation_c_slice_spacing_rad(confirmation_level: int, fraction: float) -> float:
    grid = build_sphere_grid(confirmation_level)
    return float(fraction * grid.max_cell_diameter_rad)


def wrapped_q_distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return float(np.linalg.norm(wrap_joint_delta(a, b)))


def cluster_wrapped_q(
    configurations: tuple[tuple[float, ...], ...] | list[tuple[float, ...]],
    *,
    tol: float,
) -> tuple[tuple[float, ...], ...]:
    """Greedy deterministic clustering in wrapped source Q."""

    representatives: list[tuple[float, ...]] = []
    for item in configurations:
        q = tuple(float(value) for value in item)
        if all(wrapped_q_distance(q, rep) > tol for rep in representatives):
            representatives.append(q)
    return tuple(representatives)


def project_source_seed_clusters(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    n: Vec3,
    c: float,
    configurations: tuple[tuple[float, ...], ...],
    *,
    policy: H13ASourcePolicy,
) -> SourceSeedDiscovery:
    """Project candidate source configurations and expose every truncation cap."""

    ordered = tuple(
        sorted(
            configurations,
            key=lambda q: (
                abs(h_value(arm, q, n) - c) > policy.seed_h_window,
                abs(h_value(arm, q, n) - c),
                tuple(float(value) for value in q),
            ),
        )
    )
    candidates = cluster_wrapped_q(ordered, tol=policy.seed_precluster_q_tol_rad)
    attempted = candidates[: policy.max_seed_candidates_per_c]
    projected: list[tuple[float, ...]] = []
    for seed in attempted:
        q_projected, ok, _ = correct_to_levelset(arm.model, seed, probe.p_star, n, c)
        if ok:
            projected.append(tuple(float(value) for value in q_projected))
    projected_clusters = cluster_wrapped_q(projected, tol=policy.seed_projected_q_tol_rad)
    budget_exhausted = (
        len(candidates) > policy.max_seed_candidates_per_c
        or len(projected_clusters) > policy.max_seed_clusters_per_c
    )
    return SourceSeedDiscovery(
        candidate_configuration_count=len(candidates),
        projection_attempt_count=len(attempted),
        projected_configuration_count=len(projected),
        projected_seed_cluster_count=len(projected_clusters),
        seed_clusters=projected_clusters[: policy.max_seed_clusters_per_c],
        budget_exhausted=budget_exhausted,
    )


def source_trace_diagnostic(
    problem: ImplicitBranchProblem,
    trace: BranchTrace,
    *,
    max_steps: int,
    policy: H13ASourcePolicy,
) -> SourceTraceDiagnostic:
    """Separate seed return, two-ray closure, singularity, failure, and budget."""

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
    budget_exhausted = len(positive) >= max_steps or len(negative) >= max_steps
    endpoint_distance: float | None = None
    endpoint_tangent_abs_dot: float | None = None
    closed = bool(trace.returned)
    termination = SourceTraceTermination.RETURNED_TO_SEED
    if not trace.returned:
        if positive and negative:
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
        elif budget_exhausted:
            termination = SourceTraceTermination.BUDGET_EXHAUSTED
        elif trace.branch_status == "singular" or rejected.get("singular", 0) > 0:
            termination = SourceTraceTermination.SINGULAR_OR_CRITICAL_ENDPOINT
        elif trace.branch_status == "unresolved" or rejected.get("corrector_failed", 0) > 0:
            termination = SourceTraceTermination.CORRECTOR_FAILURE
        else:
            termination = SourceTraceTermination.OPEN_UNCLASSIFIED
    return SourceTraceDiagnostic(
        termination=termination,
        closed=closed,
        budget_exhausted=budget_exhausted,
        positive_accepted_steps=len(positive),
        negative_accepted_steps=len(negative),
        accepted_arclength=accepted_arclength,
        endpoint_state_distance=endpoint_distance,
        endpoint_tangent_abs_dot=endpoint_tangent_abs_dot,
        rejection_reason_counts=dict(rejected),
    )


def continue_source_fiber_h13(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    n: Vec3,
    c: float,
    q_seed: tuple[float, ...],
    *,
    fiber_id: str,
    max_steps: int,
    step_size: float,
    policy: H13ASourcePolicy,
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
            budget_exhausted=False,
            positive_accepted_steps=0,
            negative_accepted_steps=0,
            accepted_arclength=0.0,
            endpoint_state_distance=None,
            endpoint_tangent_abs_dot=None,
            rejection_reason_counts={},
        )
    problem = PointingLevelSetProblem(
        model=arm.model,
        p_star=probe.p_star,
        n=n,
        c=c,
        problem_id=fiber_id,
    )
    trace = continue_implicit_branch(
        problem,
        np.asarray(q_projected, dtype=float),
        branch_id=fiber_id,
        max_steps=max_steps,
        step_size=step_size,
    )
    diagnostic = source_trace_diagnostic(
        problem,
        trace,
        max_steps=max_steps,
        policy=policy,
    )
    qs: list[tuple[float, ...]] = []
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
    )


def _fiber_quality(fiber: SourceControlFiber) -> tuple[int, int, int, float, float, str]:
    closed = fiber.closed or fiber.returned
    return (
        0 if closed else 1,
        0 if fiber.q_samples else 1,
        -len(fiber.q_samples),
        fiber.max_position_residual_m,
        fiber.max_h_residual,
        fiber.fiber_id,
    )


def deduplicate_fibers_h13(
    fibers: tuple[SourceControlFiber, ...],
    *,
    tol: float,
) -> tuple[SourceControlFiber, ...]:
    kept: list[SourceControlFiber] = []
    ordered = sorted(fibers, key=lambda fiber: (fiber.c, *_fiber_quality(fiber)))
    for fiber in ordered:
        if not fiber.q_samples:
            kept.append(fiber)
            continue
        duplicate = False
        for other in kept:
            if not other.q_samples or abs(other.c - fiber.c) > 1e-9:
                continue
            d_ab = directed_q_distance(fiber.q_samples, other.q_samples)
            d_ba = directed_q_distance(other.q_samples, fiber.q_samples)
            if max(d_ab, d_ba) <= tol and abs(d_ab - d_ba) <= tol:
                duplicate = True
                break
        if not duplicate:
            kept.append(fiber)
    return tuple(kept)


def _is_analytical_endpoint(c: float, c_values: tuple[float, ...]) -> bool:
    return abs(c - c_values[0]) <= 1e-12 or abs(c - c_values[-1]) <= 1e-12


def annotate_analytical_endpoints(
    c_values: tuple[float, ...],
    records: tuple[SourceControlCRecord, ...],
) -> tuple[SourceControlCRecord, ...]:
    if not c_values:
        return records
    out: list[SourceControlCRecord] = []
    for record in records:
        if _is_analytical_endpoint(float(record.c), c_values):
            out.append(
                replace(
                    record,
                    parameter_interval_status=SourceIntervalStatus.CRITICAL_OR_BOUNDARY.value,
                    required=False,
                    domain_boundary=True,
                )
            )
        else:
            out.append(record)
    return tuple(out)


def classify_source_interval_status_h13(
    *,
    closed_count: int,
    open_count: int,
    singular_count: int,
    unresolved_count: int,
    budget_exhausted_count: int,
    seed_budget_exhausted: bool,
    required: bool,
) -> SourceIntervalStatus:
    """Classify one c slice from deduplicated trace evidence."""

    if not required:
        return SourceIntervalStatus.CRITICAL_OR_BOUNDARY
    if seed_budget_exhausted or budget_exhausted_count > 0:
        return SourceIntervalStatus.BUDGET_EXHAUSTED
    total = closed_count + open_count + singular_count + unresolved_count
    if total <= 0:
        return SourceIntervalStatus.UNRESOLVED
    if closed_count == total:
        return SourceIntervalStatus.RETURNED_SET_FOUND
    if closed_count > 0:
        return SourceIntervalStatus.MIXED_UNRESOLVED
    populated = sum(count > 0 for count in (open_count, singular_count, unresolved_count))
    if populated > 1:
        return SourceIntervalStatus.MIXED_UNRESOLVED
    if singular_count > 0:
        return SourceIntervalStatus.SINGULAR
    if open_count > 0:
        return SourceIntervalStatus.OPEN_ONLY
    return SourceIntervalStatus.UNRESOLVED


def classify_h13b_interval_status(
    *,
    required: bool,
    seed_budget_exhausted: bool,
    returned_count: int,
    open_count: int,
    singular_count: int,
) -> SourceIntervalStatus:
    """H13B wrapper: seed-cap blocking plus H13C interval law."""

    return classify_source_interval_status_h13(
        closed_count=returned_count,
        open_count=open_count,
        singular_count=singular_count,
        unresolved_count=0,
        budget_exhausted_count=0,
        seed_budget_exhausted=seed_budget_exhausted,
        required=required,
    )


def _merge_linear_intervals(
    intervals: tuple[tuple[float, float], ...] | list[tuple[float, float]],
    *,
    tol: float = 1e-12,
) -> tuple[tuple[float, float], ...]:
    ordered = sorted((min(lo, hi), max(lo, hi)) for lo, hi in intervals)
    if not ordered:
        return ()
    merged: list[tuple[float, float]] = [ordered[0]]
    for lo, hi in ordered[1:]:
        prior_lo, prior_hi = merged[-1]
        if lo <= prior_hi + tol:
            merged[-1] = (prior_lo, max(prior_hi, hi))
        else:
            merged.append((lo, hi))
    return tuple((float(lo), float(hi)) for lo, hi in merged)


def unresolved_c_intervals_from_records_h13(
    c_values: tuple[float, ...],
    records: tuple[SourceControlCRecord, ...] | list[SourceControlCRecord],
) -> tuple[tuple[float, float], ...]:
    """Neighbor spans of required bins that are missing or not covered.

    Analytical endpoints marked ``CRITICAL_OR_BOUNDARY`` are not required 1-D curves.
    ``RETURNED_COMPONENT_FOUND`` is historical JSON only and is not a covered H13 status.
    Adjacent unresolved spans are merged.
    """

    if not c_values:
        return ()
    covered = {status.value for status in COVERED_H13_INTERVAL_STATUSES}
    by_c = {float(item.c): item for item in records}
    intervals: list[tuple[float, float]] = []
    for i, c in enumerate(c_values):
        rec = by_c.get(float(c))
        status = None if rec is None else rec.parameter_interval_status
        if isinstance(status, SourceIntervalStatus):
            status = status.value
        if rec is not None and not rec.required:
            continue
        if (
            rec is not None
            and status == SourceIntervalStatus.CRITICAL_OR_BOUNDARY.value
            and _is_analytical_endpoint(float(c), c_values)
        ):
            continue
        if rec is not None and status in covered:
            continue
        lo = c_values[i - 1] if i > 0 else c
        hi = c_values[i + 1] if i + 1 < len(c_values) else c
        intervals.append((float(lo), float(hi)))
    return _merge_linear_intervals(intervals)


def _fiber_kind(fiber: SourceControlFiber) -> str:
    if fiber.termination_status is None:
        if fiber.closed or fiber.returned or fiber.branch_status == "returned":
            return "closed"
        if fiber.branch_status == "singular":
            return "singular"
        if fiber.branch_status == "unresolved" or not fiber.q_samples:
            return "unresolved"
        return "open"
    status = SourceTraceTermination(fiber.termination_status)
    if fiber.closed:
        return "closed"
    if status is SourceTraceTermination.BUDGET_EXHAUSTED:
        return "budget_exhausted"
    if status is SourceTraceTermination.SINGULAR_OR_CRITICAL_ENDPOINT:
        return "singular"
    if status in {
        SourceTraceTermination.PROJECTION_FAILED,
        SourceTraceTermination.CORRECTOR_FAILURE,
    } or not fiber.q_samples:
        return "unresolved"
    return "open"


def summarize_c_records_h13(
    c_values: tuple[float, ...],
    *,
    seed_discoveries: dict[float, SourceSeedDiscovery],
    unique: tuple[SourceControlFiber, ...],
) -> tuple[SourceControlCRecord, ...]:
    records: list[SourceControlCRecord] = []
    for index, c in enumerate(c_values):
        discovery = seed_discoveries[float(c)]
        group = tuple(item for item in unique if abs(item.c - c) <= 1e-12)
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
        projection_failures = max(
            0,
            discovery.projection_attempt_count - discovery.projected_configuration_count,
        )
        unresolved = sum(1 for kind in kinds if kind == "unresolved") + projection_failures
        corrector_failures = sum(
            1
            for item in group
            if item.termination_status == SourceTraceTermination.CORRECTOR_FAILURE.value
        )
        continued = sum(1 for item in group if item.q_samples)
        required = not _is_analytical_endpoint(float(c), c_values)
        boundary = len(c_values) == 1 or index in {0, len(c_values) - 1}
        status = classify_source_interval_status_h13(
            closed_count=closed,
            open_count=open_count,
            singular_count=singular,
            unresolved_count=unresolved,
            budget_exhausted_count=budget_count,
            seed_budget_exhausted=discovery.budget_exhausted,
            required=required,
        )
        attempted = len(discovery.seed_clusters)
        records.append(
            SourceControlCRecord(
                c=float(c),
                expected_seed_count=attempted,
                projected_seed_count=discovery.projected_configuration_count,
                continued_component_count=continued,
                returned_count=returned,
                open_count=open_count,
                singular_count=singular,
                unresolved_count=unresolved,
                deduplicated_component_ids=tuple(
                    item.fiber_id for item in group if item.q_samples
                ),
                parameter_interval_status=status.value,
                candidate_seed_count=discovery.candidate_configuration_count,
                projection_attempt_count=discovery.projection_attempt_count,
                attempted_seed_count=attempted,
                projected_seed_cluster_count=discovery.projected_seed_cluster_count,
                projection_failure_count=projection_failures,
                seed_budget_exhausted=discovery.budget_exhausted,
                required=required,
                domain_boundary=boundary,
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
            )
        )
    return tuple(records)


def build_source_control_h13(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    discovery: DirectPointingTruth,
    *,
    config: CampaignConfig,
    mode: str,
    max_steps: int | None = None,
    step_size: float = 0.08,
) -> H13ASourceControlResult:
    policy = load_h13_source_policy(config, mode)
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
    fibers: list[SourceControlFiber] = []
    seed_discoveries: dict[float, SourceSeedDiscovery] = {}
    for c_index, c in enumerate(c_values):
        seed_record = project_source_seed_clusters(
            arm,
            probe,
            n,
            c,
            discovery_configs,
            policy=policy,
        )
        seed_discoveries[float(c)] = seed_record
        for seed_index, seed in enumerate(seed_record.seed_clusters):
            fibers.append(
                continue_source_fiber_h13(
                    arm,
                    probe,
                    n,
                    c,
                    seed,
                    fiber_id=f"{probe.probe_id}_c{c_index}_s{seed_index}",
                    max_steps=steps,
                    step_size=step_size,
                    policy=policy,
                )
            )
    unique = deduplicate_fibers_h13(tuple(fibers), tol=policy.dedup_q_tol_rad)
    pointings = tuple(direction for fiber in unique for direction in fiber.pointing_samples)
    grid = build_sphere_grid(budgets.confirmation_icosphere_level)
    hits = paint_pointings(grid, pointings)
    records = summarize_c_records_h13(
        c_values,
        seed_discoveries=seed_discoveries,
        unique=unique,
    )
    unresolved = unresolved_c_intervals_from_records_h13(c_values, records)
    inner = SourceControlResult(
        probe_id=probe.probe_id,
        n=n,
        c_values=c_values,
        fibers=unique,
        pointing_samples=pointings,
        hit_cells=hits,
        unresolved_c_intervals=unresolved,
        notes=(
            "Source h=c control; not a natural UURU child.",
            "The required c domain comes from the analytical regional-shell oracle.",
            "Production H13 uses declared probe rho_m, not rounded Cartesian norm.",
            "Projected source-Q seed clusters replace the H12 first-three seed rule.",
            "Candidate and projected-cluster caps are explicit interval blockers.",
            "Analytical endpoints are CRITICAL_OR_BOUNDARY and are not required 1-D curves.",
            "Plus/minus endpoint meeting is distinct from seed return.",
            "A budget-exhausted trace is not a genuinely noncompact branch.",
            "RETURNED_SET_FOUND is declared-budget evidence, not component completeness.",
            f"seed_count_semantics={SEED_COUNT_SEMANTICS}.",
        ),
        c_records=records,
    )
    return H13ASourceControlResult(
        inner=inner,
        analytical_c_interval=interval,
        requested_c_value_count=budgets.source_c_value_count,
        c_slice_max_angular_spacing_rad=spacing,
        policy=policy,
    )


def _load_discovery(blob: dict[str, Any]) -> DirectPointingTruth:
    solves = []
    for item in blob["solves"]:
        clusters = tuple(
            PointingSolutionCluster(
                cluster_id=str(c["cluster_id"]),
                q_representative=tuple(float(v) for v in c["q_representative"]),
                members=tuple(tuple(float(v) for v in m) for m in c["members"]),
                seed_sources=tuple(str(s) for s in c["seed_sources"]),
                position_residual_m=float(c["position_residual_m"]),
                pointing_geodesic_rad=float(c["pointing_geodesic_rad"]),
            )
            for c in item["clusters"]
        )
        solves.append(
            PointingTargetSolve(
                target_index=int(item["target_index"]),
                d_target=as_vec3(tuple(float(v) for v in item["d_target"])),
                status=PointingSolveStatus(item["status"]),
                clusters=clusters,
                best_position_residual_m=item["best_position_residual_m"],
                best_pointing_geodesic_rad=item["best_pointing_geodesic_rad"],
                n_starts=int(item["n_starts"]),
            )
        )
    return DirectPointingTruth(
        probe_id=str(blob["probe_id"]),
        split=str(blob["split"]),
        icosphere_level=int(blob["icosphere_level"]),
        solves=tuple(solves),
        found_count=int(blob["found_count"]),
        not_found_count=int(blob["not_found_count"]),
        unresolved_count=int(blob["unresolved_count"]),
    )


def write_source_control_stage_h13(
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
        result = build_source_control_h13(
            arm,
            probe,
            discovery,
            config=config,
            mode=mode,
        )
        path = outdir / probe.probe_id / "source_control.json"
        path.write_text(json_dumps_strict(result.to_json_dict()), encoding="utf-8")
        records.append({"probe_id": probe.probe_id, "fiber_count": len(result.inner.fibers)})
    summary = {
        **stage_envelope(
            config,
            stage="source-control",
            mode=mode,
            probe_ids=tuple(p.probe_id for p in probes),
        ),
        "probes": records,
        "source_control_policy_version": POLICY_VERSION,
        "allows_full_campaign_disposition": budgets.allows_full_campaign_disposition,
        "limitations": []
        if budgets.allows_full_campaign_disposition
        else ["mode cannot issue full-campaign disposition"],
    }
    return finalize_stage(
        outdir,
        summary,
        config=config,
        stage="source-control",
        mode=mode,
        probe_ids=tuple(p.probe_id for p in probes),
    )
