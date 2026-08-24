"""H13A opt-in source ``h=c`` policy and analytical c domain.

This module is selected only when ``source_control.policy_version`` equals
``h13_component_closure_v1``. The frozen H12 config keeps the historical
``source_control.py`` path. Seed discovery remains the H12 first-three law until
H13B.
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

from .artifacts import finalize_stage
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
    SourceControlResult,
    build_source_control,
)
from .sphere_grid import build_sphere_grid

POLICY_VERSION = H13_POLICY_VERSION
C_DOMAIN_POLICY = "analytical_regional_shell"
C_DOMAIN_FORMULA = (
    "c_min=max(-1,(rho^2+t^2-r_max^2)/(2*rho*t)); "
    "c_max=min(1,(rho^2+t^2-r_min^2)/(2*rho*t))"
)
DEFAULT_C_SLICE_FRACTION = 0.75


@dataclass(frozen=True, slots=True)
class H13ASourcePolicy:
    c_slice_max_angular_spacing_cell_fraction: float

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "policy_version": POLICY_VERSION,
                "c_domain_policy": C_DOMAIN_POLICY,
                "c_slice_max_angular_spacing_cell_fraction": (
                    self.c_slice_max_angular_spacing_cell_fraction
                ),
            }
        )


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


def load_h13_source_policy(config: CampaignConfig, mode: str | None = None) -> H13ASourcePolicy:
    del mode
    raw_value = config.raw.get("source_control", {})
    raw = raw_value if isinstance(raw_value, Mapping) else {}
    version = str(raw.get("policy_version", ""))
    if version != POLICY_VERSION:
        raise ValueError(
            f"H13 source module requires policy_version={POLICY_VERSION!r}, got {version!r}"
        )
    fraction = float(raw.get("c_slice_max_angular_spacing_cell_fraction", DEFAULT_C_SLICE_FRACTION))
    if fraction <= 0.0:
        raise ValueError("c_slice_max_angular_spacing_cell_fraction must be positive")
    return H13ASourcePolicy(c_slice_max_angular_spacing_cell_fraction=fraction)


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


def unresolved_c_intervals_from_records_h13(
    c_values: tuple[float, ...],
    records: tuple[SourceControlCRecord, ...] | list[SourceControlCRecord],
) -> tuple[tuple[float, float], ...]:
    """Neighbor spans of required bins that are missing, open, singular, or unresolved.

    Analytical endpoints marked ``CRITICAL_OR_BOUNDARY`` are not required 1-D curves.
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
    inner = build_source_control(
        arm,
        probe,
        discovery,
        c_count=budgets.source_c_value_count,
        confirmation_level=budgets.confirmation_icosphere_level,
        max_steps=budgets.continuation_steps if max_steps is None else max_steps,
        step_size=step_size,
        c_values=c_values,
    )
    records = annotate_analytical_endpoints(inner.c_values, inner.c_records)
    unresolved = unresolved_c_intervals_from_records_h13(inner.c_values, records)
    inner = replace(
        inner,
        c_records=records,
        unresolved_c_intervals=unresolved,
        notes=(
            "Source h=c control; not a natural UURU child.",
            "The required c domain comes from the analytical regional-shell oracle.",
            "Production H13 uses declared probe rho_m, not rounded Cartesian norm.",
            "Seed discovery remains the H12 first-three law until H13B.",
            "Analytical endpoints are CRITICAL_OR_BOUNDARY and are not required 1-D curves.",
        ),
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
