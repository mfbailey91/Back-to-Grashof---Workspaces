"""Positive-control U-R-U 5R arm, analytical pointing oracle, and probe seeds.

Conventions
-----------
Home axes (metres, world frame)::

    R1: z at origin
    R2: y at origin
    R3: y at (L1, 0, 0)
    R4: z at (L1+L2, 0, 0)
    R5: y at (L1+L2, 0, 0)

Home pointing is ``+x``. The wrist center is invariant under R4/R5. Analytic
fixture seeds are for initializing fixed-position problems only; they are not
used as the direct-truth acceptance path.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, atan2, cos, sin, sqrt
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial_experiments.aligned_6r import frame_from_pointing
from grashof_workspace.spatial_experiments.axis_aggregation import (
    SURU_FAMILY_LABEL,
    build_suru_multi_aggregation,
)
from grashof_workspace.spatial_experiments.axis_geometry import AxisLine, as_vec3, unit_vector
from grashof_workspace.spatial_experiments.fixed_position import (
    audit_fixed_position_seed,
    pose_fixed_position_problem,
)
from grashof_workspace.spatial_experiments.open_chain import OpenChainModel
from grashof_workspace.spatial_experiments.rotations import rotate_point_about_axis
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain

from .models import (
    AnalyticalDirectionOracleResult,
    AnalyticalPointingCompletenessResult,
    CampaignConfig,
    CompletenessLabel,
    FixedPointProbe,
    L5PositiveControlGeometry,
    OracleFeasibility,
    json_dumps_strict,
)

Array = NDArray[np.floating]
Vec3 = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class PositiveControlArm:
    geometry: L5PositiveControlGeometry
    model: OpenChainModel

    @property
    def chain(self) -> SerialRevoluteChain:
        return self.model.chain


def home_axes(geometry: L5PositiveControlGeometry) -> tuple[AxisLine, ...]:
    l1 = geometry.L1
    l2 = geometry.L2
    return (
        AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        AxisLine((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        AxisLine((l1, 0.0, 0.0), (0.0, 1.0, 0.0)),
        AxisLine((l1 + l2, 0.0, 0.0), (0.0, 0.0, 1.0)),
        AxisLine((l1 + l2, 0.0, 0.0), (0.0, 1.0, 0.0)),
    )


def build_positive_control_arm(geometry: L5PositiveControlGeometry) -> PositiveControlArm:
    axes = home_axes(geometry)
    d0 = as_vec3(unit_vector(geometry.home_pointing, name="home pointing"))
    p0 = as_vec3(geometry.home_tool_point)
    chain = SerialRevoluteChain(home_axes=axes, p0=p0, d0=d0, R0=frame_from_pointing(d0))
    model = OpenChainModel(
        architecture_id=geometry.architecture_id,
        chain=chain,
        joint_kind_sequence=("R", "R", "R", "R", "R"),
        joint_role_sequence=("R_phys", "R_phys", "R_phys", "R_phys", "R_phys"),
        notes=(
            "Positive-control SURU 5R. Joint limits not_modeled.",
            "Physical aggregation SURU is a separate operation.",
        ),
    )
    return PositiveControlArm(geometry=geometry, model=model)


def evaluate_wrist_center(
    arm: PositiveControlArm,
    q: tuple[float, ...] | Array,
) -> Array:
    """Image of the home wrist center under proximal joints R1–R3 only."""

    q_t = tuple(float(v) for v in np.asarray(q, dtype=float).reshape(-1))
    w = np.asarray(arm.geometry.home_wrist_center, dtype=float).copy()
    for i in range(2, -1, -1):
        w = np.asarray(rotate_point_about_axis(w, arm.chain.home_axes[i], q_t[i]), dtype=float)
    return w


def direction_oracle(
    geometry: L5PositiveControlGeometry,
    p_star: Array | Vec3,
    d_target: Array | Vec3,
    *,
    margin_tol_m: float,
) -> AnalyticalDirectionOracleResult:
    p = np.asarray(p_star, dtype=float).reshape(3)
    d_arr = np.asarray(d_target, dtype=float).reshape(3)
    d = np.asarray(unit_vector((float(d_arr[0]), float(d_arr[1]), float(d_arr[2])), name="d_target"))
    wrist = p - geometry.tool_offset * d
    radius = float(np.linalg.norm(wrist))
    inner = radius - geometry.r_min
    outer = geometry.r_max - radius
    margin = min(inner, outer)
    if abs(inner) <= margin_tol_m or abs(outer) <= margin_tol_m:
        feasibility = OracleFeasibility.BOUNDARY
    elif inner >= 0.0 and outer >= 0.0:
        feasibility = OracleFeasibility.FEASIBLE
    else:
        feasibility = OracleFeasibility.INFEASIBLE
    return AnalyticalDirectionOracleResult(
        p_star=as_vec3(p),
        d_target=as_vec3(d),
        wrist=as_vec3(wrist),
        wrist_radius=radius,
        feasibility=feasibility,
        margin_m=margin,
    )


def point_completeness_oracle(
    geometry: L5PositiveControlGeometry,
    p_star: Array | Vec3,
    *,
    margin_tol_m: float,
) -> AnalyticalPointingCompletenessResult:
    p = np.asarray(p_star, dtype=float).reshape(3)
    rho = float(np.linalg.norm(p))
    inner_margin = abs(rho - geometry.tool_offset) - geometry.r_min
    outer_margin = geometry.r_max - (rho + geometry.tool_offset)
    if abs(inner_margin) <= margin_tol_m or abs(outer_margin) <= margin_tol_m:
        label = CompletenessLabel.BOUNDARY
        complete = False
    elif inner_margin >= 0.0 and outer_margin >= 0.0:
        label = CompletenessLabel.COMPLETE
        complete = True
    else:
        label = CompletenessLabel.PARTIAL
        complete = False
    return AnalyticalPointingCompletenessResult(
        p_star=as_vec3(p),
        rho=rho,
        inner_margin_m=inner_margin,
        outer_margin_m=outer_margin,
        label=label,
        complete=complete,
    )


def _wrap(angle: float) -> float:
    return float(atan2(sin(angle), cos(angle)))


def _seed_pointing_direction(probe: FixedPointProbe) -> Array:
    p = np.asarray(probe.p_star, dtype=float)
    nrm = float(np.linalg.norm(p))
    if nrm <= 0.0:
        raise ValueError("p_star must be nonzero")
    radial = p / nrm
    if probe.seed_pointing_policy == "radial_inward":
        return -radial
    return radial


def _solve_regional_3r(geometry: L5PositiveControlGeometry, wrist: Array) -> tuple[float, float, float]:
    l1 = geometry.L1
    l2 = geometry.L2
    wx, wy, wz = (float(wrist[0]), float(wrist[1]), float(wrist[2]))
    r_xy = sqrt(wx * wx + wy * wy)
    q1 = 0.0 if r_xy <= 1e-15 else atan2(wy, wx)
    x_prime = r_xy
    z_prime = wz
    reach2 = x_prime * x_prime + z_prime * z_prime
    reach = sqrt(reach2)
    if reach < abs(l1 - l2) - 1e-12 or reach > l1 + l2 + 1e-12:
        raise ValueError("wrist target outside regional 3R shell")
    cos_q3 = (reach2 - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)
    cos_q3 = max(-1.0, min(1.0, cos_q3))
    q3 = acos(cos_q3)
    alpha = atan2(-z_prime, x_prime)
    q2 = alpha - atan2(l2 * sin(q3), l1 + l2 * cos(q3))
    return _wrap(q1), _wrap(q2), _wrap(q3)


def _proximal_rotation(q1: float, q2: float, q3: float) -> Array:
    cy2, sy2 = cos(q2), sin(q2)
    ry2 = np.array([[cy2, 0.0, sy2], [0.0, 1.0, 0.0], [-sy2, 0.0, cy2]], dtype=float)
    cy3, sy3 = cos(q3), sin(q3)
    ry3 = np.array([[cy3, 0.0, sy3], [0.0, 1.0, 0.0], [-sy3, 0.0, cy3]], dtype=float)
    cz, sz = cos(q1), sin(q1)
    rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=float)
    return np.asarray(rz @ ry2 @ ry3, dtype=float)


def _solve_wrist_2r(r_prox: Array, d_target: Array) -> tuple[float, float]:
    d_local = r_prox.T @ np.asarray(d_target, dtype=float).reshape(3)
    d_local = d_local / float(np.linalg.norm(d_local))
    sin_q5 = float(-d_local[2])
    sin_q5 = max(-1.0, min(1.0, sin_q5))
    q5 = float(np.arcsin(sin_q5))
    cos_q5 = float(np.cos(q5))
    if abs(cos_q5) <= 1e-12:
        q4 = 0.0
    else:
        q4 = atan2(float(d_local[1]) / cos_q5, float(d_local[0]) / cos_q5)
    return _wrap(q4), _wrap(q5)


def analytic_seed_configuration(
    geometry: L5PositiveControlGeometry,
    probe: FixedPointProbe,
) -> tuple[float, ...]:
    d = _seed_pointing_direction(probe)
    p = np.asarray(probe.p_star, dtype=float)
    wrist = p - geometry.tool_offset * d
    q1, q2, q3 = _solve_regional_3r(geometry, wrist)
    r_prox = _proximal_rotation(q1, q2, q3)
    q4, q5 = _solve_wrist_2r(r_prox, d)
    return (q1, q2, q3, q4, q5)


def fixture_seed_for_probe(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    *,
    position_tol_m: float,
    pointing_tol_rad: float,
) -> tuple[float, ...]:
    q = analytic_seed_configuration(arm.geometry, probe)
    state = arm.chain.evaluate(q)
    pos_err = float(np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star)))
    d_target = _seed_pointing_direction(probe)
    dot = float(np.clip(np.dot(state.d, d_target), -1.0, 1.0))
    pnt_err = float(np.arccos(dot))
    if pos_err > position_tol_m or pnt_err > pointing_tol_rad:
        raise ValueError(
            f"analytic seed failed for {probe.probe_id}: pos={pos_err} pointing={pnt_err}"
        )
    return q


def write_fixture_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
) -> dict[str, Any]:
    arm = build_positive_control_arm(config.geometry)
    margin = config.tolerances.strict_analytical_boundary_margin_m
    records: list[dict[str, Any]] = []
    for probe in probes:
        q_seed = fixture_seed_for_probe(
            arm,
            probe,
            position_tol_m=config.tolerances.position_residual_m,
            pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
        )
        posed = pose_fixed_position_problem(arm.model, q_seed)
        audit = audit_fixed_position_seed(posed)
        agg = build_suru_multi_aggregation(arm.model, q_seed)
        completeness = point_completeness_oracle(config.geometry, probe.p_star, margin_tol_m=margin)
        probe_dir = outdir / probe.probe_id
        payload = {
            "probe": probe.to_json_dict(),
            "seed_configuration": list(q_seed),
            "completeness": completeness.to_json_dict(),
            "rank_jp": audit.rank_jp,
            "nullity_jp": audit.nullity_jp,
            "aggregation": agg.to_json_dict(),
            "family_label": SURU_FAMILY_LABEL,
        }
        path = probe_dir / "fixture.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_dumps_strict(payload), encoding="utf-8")
        records.append(payload)
    summary = {
        "program_id": config.program_id,
        "config_hash": config.config_hash,
        "stage": "fixture",
        "probes": records,
    }
    (outdir / "fixture.json").write_text(json_dumps_strict(summary), encoding="utf-8")
    return summary
