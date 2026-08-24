"""H13 opt-in source ``h=c`` policy: analytical c domain and projected seed discovery.

This module is selected only when ``source_control.policy_version`` equals
``h13_component_closure_v1``. The frozen H12 config keeps the historical
``source_control.py`` path, including the silent first-three seed rule.
Trace termination honesty and curve rasterization remain H13C–H13D.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from math import acos, ceil, cos
from pathlib import Path
from typing import Any

import numpy as np

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.continuation import wrap_joint_delta
from grashof_workspace.spatial_experiments.parent_level_sets import correct_to_levelset

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
    json_dumps_strict,
    json_object,
    resolve_stage_budgets,
    stage_envelope,
)
from .positive_control import PositiveControlArm, build_positive_control_arm
from .source_control import (
    COVERED_SOURCE_INTERVAL_STATUSES,
    H13_POLICY_VERSION,
    SourceControlFiber,
    SourceControlResult,
    classify_source_interval_status,
    continue_source_fiber,
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
            }
        )


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
    )
    positive = (
        policy.c_slice_max_angular_spacing_cell_fraction,
        policy.discovery_q_precluster_tol_rad,
        policy.seed_h_window,
        policy.seed_precluster_q_tol_rad,
        policy.seed_projected_q_tol_rad,
        policy.dedup_q_tol_rad,
    )
    if any(value <= 0.0 for value in positive):
        raise ValueError("H13 source policy tolerances and spacing fractions must be positive")
    if policy.max_seed_candidates_per_c <= 0 or policy.max_seed_clusters_per_c <= 0:
        raise ValueError("H13 source seed budgets must be positive")
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


def _fiber_quality(fiber: SourceControlFiber) -> tuple[int, int, int, float, float, str]:
    return (
        0 if fiber.returned else 1,
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
                )
            )
        else:
            out.append(record)
    return tuple(out)


def classify_h13b_interval_status(
    *,
    required: bool,
    seed_budget_exhausted: bool,
    returned_count: int,
    open_count: int,
    singular_count: int,
) -> SourceIntervalStatus:
    if not required:
        return SourceIntervalStatus.CRITICAL_OR_BOUNDARY
    if seed_budget_exhausted:
        return SourceIntervalStatus.BUDGET_EXHAUSTED
    return classify_source_interval_status(
        returned_count=returned_count,
        open_count=open_count,
        singular_count=singular_count,
    )


def unresolved_c_intervals_from_records_h13(
    c_values: tuple[float, ...],
    records: tuple[SourceControlCRecord, ...] | list[SourceControlCRecord],
) -> tuple[tuple[float, float], ...]:
    """Neighbor spans of required bins that are missing, open, singular, or unresolved.

    Analytical endpoints marked ``CRITICAL_OR_BOUNDARY`` are not required 1-D curves.
    ``BUDGET_EXHAUSTED`` is not a covered interval.
    """

    if not c_values:
        return ()
    covered = {status.value for status in COVERED_SOURCE_INTERVAL_STATUSES}
    by_c = {float(item.c): item for item in records}
    out: list[tuple[float, float]] = []
    for i, c in enumerate(c_values):
        rec = by_c.get(float(c))
        status = None if rec is None else rec.parameter_interval_status
        if isinstance(status, SourceIntervalStatus):
            status = status.value
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
        out.append((float(lo), float(hi)))
    return tuple(out)


def _fiber_kind(fiber: SourceControlFiber) -> str:
    if fiber.returned or fiber.branch_status == "returned":
        return "returned"
    if fiber.branch_status == "singular":
        return "singular"
    if fiber.branch_status == "unresolved" or not fiber.q_samples:
        return "unresolved"
    return "open"


def summarize_c_records_h13(
    c_values: tuple[float, ...],
    *,
    seed_discoveries: dict[float, SourceSeedDiscovery],
    unique: tuple[SourceControlFiber, ...],
) -> tuple[SourceControlCRecord, ...]:
    records: list[SourceControlCRecord] = []
    for c in c_values:
        discovery = seed_discoveries[float(c)]
        group = tuple(item for item in unique if abs(item.c - c) <= 1e-12)
        kinds = [_fiber_kind(item) for item in group]
        returned = sum(1 for kind in kinds if kind == "returned")
        open_count = sum(1 for kind in kinds if kind == "open")
        singular = sum(1 for kind in kinds if kind == "singular")
        unresolved = sum(1 for kind in kinds if kind == "unresolved")
        continued = sum(1 for item in group if item.q_samples)
        required = not _is_analytical_endpoint(float(c), c_values)
        status = classify_h13b_interval_status(
            required=required,
            seed_budget_exhausted=discovery.budget_exhausted,
            returned_count=returned,
            open_count=open_count,
            singular_count=singular,
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
                projection_failure_count=(
                    discovery.projection_attempt_count - discovery.projected_configuration_count
                ),
                seed_budget_exhausted=discovery.budget_exhausted,
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
                continue_source_fiber(
                    arm,
                    probe,
                    n,
                    c,
                    seed,
                    fiber_id=f"{probe.probe_id}_c{c_index}_s{seed_index}",
                    max_steps=steps,
                    step_size=step_size,
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
