"""Topology-derived spherical candidate axes and branch invariants.

Conventions
-----------
Intersecting-pairs reduced parent::

    S − UA − UB − R5
    UA = (R1, R2)   UB = (R3, R4)

Fiber tangent ``t = (t1…t5, 0)``. ``Ω_S = Σ_{i=1}^{5} t_i ω_i`` through ``p0``.
Exact concurrency uses one branch-global center ``c*``, not per-sample fits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import (
    AxisLine,
    line_intersection_point,
    line_line_distance,
    point_axis_distance,
    unit_vector,
)
from .fiber_constraints import reduced_fiber_tangent
from .fiber_continuation import FiberSegment
from .rotations import rotation_about_axis
from .serial_chain import SerialRevoluteChain

Vec = NDArray[np.floating]

PAIR_CENTER_TOL_M = 1e-12
EFFECTIVE_RATE_TOL = 1e-8
GLOBAL_CONCURRENCY_TOL_M = 1e-8
CENTER_DRIFT_TOL_M = 1e-8
ARC_DRIFT_TOL_RAD = 1e-6
BODY_FIXED_AXIS_TOL_RAD = 1e-6
COORDINATE_LOCK_TOL_RAD = 1e-6
CONCURRENCY_APPROX_M = 1e-6
ARC_APPROX_RAD = 1e-4

# Backward-compatible names used by experiment manifests.
CONCURRENCY_EXACT_M = GLOBAL_CONCURRENCY_TOL_M
ARC_EXACT_RAD = ARC_DRIFT_TOL_RAD

PHYSICAL_TUPLES_R1_TO_R5: tuple[tuple[int, int, int, int], ...] = tuple(
    (int(a), int(b), int(c), int(d)) for a, b, c, d in combinations(range(5), 4)
)


@dataclass(frozen=True, slots=True)
class TopologyAxes:
    s: AxisLine
    ua: AxisLine
    ub: AxisLine
    r5: AxisLine
    omega_s_norm: float
    omega_ua_norm: float
    omega_ub_norm: float
    omega_r5_rate: float
    dist_ua_m: float
    dist_ub_m: float
    well_posed: bool
    reason: str

    @property
    def sv(self) -> AxisLine:
        return self.s

    def ordered(self) -> tuple[AxisLine, AxisLine, AxisLine, AxisLine]:
        return (self.s, self.ua, self.ub, self.r5)


@dataclass(frozen=True, slots=True)
class StationInvariant:
    sigma: float
    residual_to_cstar_m: float
    sample_center_drift_m: float
    arcs_rad: tuple[float, float, float, float]
    body_fixed_drift_rad: float
    well_posed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class SphericalInvariantReport:
    architecture: str
    n: tuple[float, float, float]
    construction: str
    n_stations: int
    global_center: tuple[float, float, float] | None
    global_rms_m: float
    global_max_m: float
    max_center_drift_m: float
    max_arc_residual_rad: float
    max_body_fixed_drift_rad: float
    simple_lock_ranges: tuple[float, float, float, float, float]
    simple_lock_passed: bool
    locking_policy: str
    locking: str
    verdict: str
    stations: tuple[StationInvariant, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ExploratoryTupleReport:
    indices: tuple[int, int, int, int]
    label: str
    global_rms_m: float
    global_max_m: float
    max_center_drift_m: float
    max_arc_residual_rad: float


def effective_compound_axis(
    w_a: tuple[float, ...] | Vec,
    w_b: tuple[float, ...] | Vec,
    qdot_a: float,
    qdot_b: float,
    center: tuple[float, float, float],
    *,
    rate_tol: float = EFFECTIVE_RATE_TOL,
) -> tuple[AxisLine | None, float]:
    """Return the fiber-induced compound axis through ``center``."""
    omega = np.asarray(w_a, dtype=float).reshape(3) * float(qdot_a) + np.asarray(
        w_b, dtype=float
    ).reshape(3) * float(qdot_b)
    norm = float(np.linalg.norm(omega))
    if norm <= rate_tol:
        return None, norm
    return AxisLine(center, tuple(float(x) for x in omega)), norm


def cumulative_link_rotations(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
) -> tuple[NDArray[np.floating], ...]:
    """Return ``(I, R_after_1, …, R_after_n)`` using home-axis space exponentials."""
    q_t = tuple(float(x) for x in np.asarray(q, dtype=float).reshape(chain.n_joints))
    rotations = [np.eye(3, dtype=float)]
    acc = np.eye(3, dtype=float)
    for i, home in enumerate(chain.home_axes):
        acc = acc @ rotation_about_axis(home.w, q_t[i])
        rotations.append(acc.copy())
    return tuple(rotations)


def topology_spherical_axes(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | Vec,
    p0: tuple[float, ...] | Vec,
    qdot: tuple[float, ...] | Vec | None = None,
    n: tuple[float, ...] | Vec | None = None,
    *,
    pair_tol_m: float = PAIR_CENTER_TOL_M,
    rate_tol: float = EFFECTIVE_RATE_TOL,
    previous: TopologyAxes | None = None,
) -> TopologyAxes:
    """Return ``(S, UA, UB, R5)`` candidate axes."""
    dummy = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    if chain.n_joints != 6:
        return TopologyAxes(dummy, dummy, dummy, dummy, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False, "not_6r")
    q_t = tuple(float(x) for x in np.asarray(q, dtype=float).reshape(6))
    p0_t = tuple(float(x) for x in np.asarray(p0, dtype=float).reshape(3))
    axes = chain.current_axes(q_t)
    dist_ua = line_line_distance(axes[0], axes[1])
    dist_ub = line_line_distance(axes[2], axes[3])
    if dist_ua > pair_tol_m or dist_ub > pair_tol_m:
        return TopologyAxes(
            dummy, dummy, dummy, axes[4], 0.0, 0.0, 0.0, 0.0, dist_ua, dist_ub, False, "pair_centers_undefined"
        )
    c_ua = line_intersection_point(axes[0], axes[1], tol_m=pair_tol_m)
    c_ub = line_intersection_point(axes[2], axes[3], tol_m=pair_tol_m)
    if c_ua is None or c_ub is None:
        return TopologyAxes(
            dummy, dummy, dummy, axes[4], 0.0, 0.0, 0.0, 0.0, dist_ua, dist_ub, False, "pair_centers_undefined"
        )
    if qdot is None:
        if n is None:
            raise ValueError("n is required when qdot is omitted")
        qdot_arr = reduced_fiber_tangent(chain, q_t, n)
    else:
        qdot_arr = np.asarray(qdot, dtype=float).reshape(6)
    ua_axis, ua_norm = effective_compound_axis(
        axes[0].w, axes[1].w, float(qdot_arr[0]), float(qdot_arr[1]), c_ua, rate_tol=rate_tol
    )
    ub_axis, ub_norm = effective_compound_axis(
        axes[2].w, axes[3].w, float(qdot_arr[2]), float(qdot_arr[3]), c_ub, rate_tol=rate_tol
    )
    omega_s = np.zeros(3, dtype=float)
    for idx in range(5):
        omega_s = omega_s + float(qdot_arr[idx]) * axes[idx].w_array
    s_norm = float(np.linalg.norm(omega_s))
    r5_rate = abs(float(qdot_arr[4]))
    if ua_axis is None or ub_axis is None or s_norm <= rate_tol:
        return TopologyAxes(
            dummy,
            ua_axis or dummy,
            ub_axis or dummy,
            axes[4],
            s_norm,
            ua_norm,
            ub_norm,
            r5_rate,
            dist_ua,
            dist_ub,
            False,
            "effective_rate_degenerate",
        )
    s_axis = AxisLine(p0_t, tuple(float(x) for x in omega_s))
    r5_axis = axes[4]
    if previous is not None:
        s_axis = _sign_align_axis(s_axis, previous.s)
        ua_axis = _sign_align_axis(ua_axis, previous.ua)
        ub_axis = _sign_align_axis(ub_axis, previous.ub)
        r5_axis = _sign_align_axis(r5_axis, previous.r5)
    return TopologyAxes(
        s_axis,
        ua_axis,
        ub_axis,
        r5_axis,
        s_norm,
        ua_norm,
        ub_norm,
        r5_rate,
        dist_ua,
        dist_ub,
        True,
        "defined",
    )


def _sign_align_axis(axis: AxisLine, reference: AxisLine) -> AxisLine:
    if float(np.dot(axis.w_array, reference.w_array)) < 0.0:
        return AxisLine(axis.r, tuple(float(-x) for x in axis.w))
    return axis


def spherical_arc_angles(
    axes: TopologyAxes,
    *,
    seed: TopologyAxes | None = None,
) -> tuple[float, float, float, float]:
    """Return cycle angles ``(S, UA, UB, R5)`` in ``(0, π]``."""
    ordered = list(axes.ordered())
    if seed is not None:
        ordered = [
            _sign_align_axis(axis, ref) for axis, ref in zip(ordered, seed.ordered(), strict=True)
        ]
    dirs = [axis.w_array for axis in ordered]
    angles: list[float] = []
    for i, direction in enumerate(dirs):
        nxt = dirs[(i + 1) % 4]
        cos = float(np.clip(np.dot(unit_vector(direction), unit_vector(nxt)), -1.0, 1.0))
        angles.append(max(0.0, float(np.arccos(cos))))
    return (angles[0], angles[1], angles[2], angles[3])


def arc_residual(
    angles: tuple[float, float, float, float],
    seed_angles: tuple[float, float, float, float],
) -> float:
    delta = np.asarray(angles, dtype=float) - np.asarray(seed_angles, dtype=float)
    return float(np.linalg.norm(delta))


def fit_global_center(axis_groups: list[tuple[AxisLine, ...]] | tuple[tuple[AxisLine, ...], ...]) -> Vec:
    """Return the least-squares center common to all supplied axes."""
    blocks_a: list[NDArray[np.floating]] = []
    blocks_b: list[NDArray[np.floating]] = []
    for group in axis_groups:
        for axis in group:
            direction = axis.w_array.reshape(3, 1)
            projector = np.eye(3) - direction @ direction.T
            blocks_a.append(projector)
            blocks_b.append(projector @ axis.r_array.reshape(3, 1))
    stacked_a = np.vstack(blocks_a)
    stacked_b = np.vstack(blocks_b).reshape(-1)
    center, *_ = np.linalg.lstsq(stacked_a, stacked_b, rcond=None)
    return center


def line_center_residual(axis: AxisLine, center: Vec) -> float:
    return point_axis_distance(center, axis)


def simple_lock_ranges(qs: list[tuple[float, ...]]) -> tuple[float, float, float, float, float]:
    arr = np.asarray(qs, dtype=float)
    ranges = arr.max(axis=0)[:5] - arr.min(axis=0)[:5]
    return (
        float(ranges[0]),
        float(ranges[1]),
        float(ranges[2]),
        float(ranges[3]),
        float(ranges[4]),
    )


def body_fixed_axis_drift(
    chain: SerialRevoluteChain,
    q: tuple[float, ...],
    axes: TopologyAxes,
    seed_q: tuple[float, ...],
    seed_axes: TopologyAxes,
) -> float:
    """Return max angular drift of effective axes in adjacent body frames."""
    rot = cumulative_link_rotations(chain, q)
    rot0 = cumulative_link_rotations(chain, seed_q)
    pairs = (
        (axes.s, seed_axes.s, 0, 5),
        (axes.ua, seed_axes.ua, 0, 2),
        (axes.ub, seed_axes.ub, 2, 4),
        (axes.r5, seed_axes.r5, 4, 5),
    )
    max_drift = 0.0
    for axis, seed_axis, proximal, distal in pairs:
        for body in (proximal, distal):
            current = rot[body].T @ axis.w_array
            reference = rot0[body].T @ seed_axis.w_array
            if float(np.dot(current, reference)) < 0.0:
                current = -current
            cos = float(np.clip(np.dot(unit_vector(current), unit_vector(reference)), -1.0, 1.0))
            max_drift = max(max_drift, max(0.0, float(np.arccos(cos))))
    return max_drift


def _classify(
    global_max_m: float,
    global_rms_m: float,
    max_drift_m: float,
    max_arc: float,
    max_body: float,
) -> str:
    exact = (
        global_max_m <= GLOBAL_CONCURRENCY_TOL_M
        and global_rms_m <= GLOBAL_CONCURRENCY_TOL_M
        and max_drift_m <= CENTER_DRIFT_TOL_M
        and max_arc <= ARC_DRIFT_TOL_RAD
        and max_body <= BODY_FIXED_AXIS_TOL_RAD
    )
    if exact:
        return "exact"
    approx = (
        global_max_m <= CONCURRENCY_APPROX_M
        and max_drift_m <= CONCURRENCY_APPROX_M
        and max_arc <= ARC_APPROX_RAD
        and max_body <= ARC_APPROX_RAD
    )
    if approx:
        return "approximate"
    return "fail"


def fiber_spherical_invariants(
    chain: SerialRevoluteChain,
    segment: FiberSegment,
    *,
    architecture: str,
    n: tuple[float, float, float],
) -> SphericalInvariantReport:
    """Evaluate global-center concurrency, arcs, and axis legitimacy on an IP fiber."""
    p0 = segment.p0
    accepted = [step for step in segment.accepted_samples if step.q is not None]
    empty = SphericalInvariantReport(
        architecture=architecture,
        n=n,
        construction="s_ua_ub_r5",
        n_stations=len(accepted),
        global_center=None,
        global_rms_m=float("inf"),
        global_max_m=float("inf"),
        max_center_drift_m=float("inf"),
        max_arc_residual_rad=float("inf"),
        max_body_fixed_drift_rad=float("inf"),
        simple_lock_ranges=(0.0, 0.0, 0.0, 0.0, 0.0),
        simple_lock_passed=False,
        locking_policy="body_fixed_effective_axis",
        locking="unresolved",
        verdict="unresolved",
    )
    if not accepted:
        return empty
    built: list[tuple[float, tuple[float, ...], TopologyAxes]] = []
    previous: TopologyAxes | None = None
    for step in accepted:
        axes = topology_spherical_axes(chain, step.q, p0, n=n, previous=previous)
        if not axes.well_posed:
            return SphericalInvariantReport(
                architecture=architecture,
                n=n,
                construction="s_ua_ub_r5",
                n_stations=len(accepted),
                global_center=None,
                global_rms_m=float("inf"),
                global_max_m=float("inf"),
                max_center_drift_m=float("inf"),
                max_arc_residual_rad=float("inf"),
                max_body_fixed_drift_rad=float("inf"),
                simple_lock_ranges=(0.0, 0.0, 0.0, 0.0, 0.0),
                simple_lock_passed=False,
                locking_policy="body_fixed_effective_axis",
                locking="unresolved",
                verdict="unresolved",
                stations=(
                    StationInvariant(
                        step.sigma,
                        float("inf"),
                        float("inf"),
                        (float("nan"), float("nan"), float("nan"), float("nan")),
                        float("inf"),
                        False,
                        axes.reason,
                    ),
                ),
            )
        built.append((step.sigma, step.q, axes))
        previous = axes
    _seed_sigma, seed_q, seed_axes = min(built, key=lambda item: abs(item[0]))
    seed_angles = spherical_arc_angles(seed_axes)
    groups = [item[2].ordered() for item in built]
    center = fit_global_center(groups)
    residuals = [line_center_residual(axis, center) for group in groups for axis in group]
    global_rms = float(np.sqrt(np.mean(np.square(residuals))))
    global_max = max(residuals)
    stations: list[StationInvariant] = []
    max_drift = 0.0
    max_arc = 0.0
    max_body = 0.0
    for sigma, q_t, axes in built:
        sample_center = fit_global_center((axes.ordered(),))
        drift = float(np.linalg.norm(sample_center - center))
        max_drift = max(max_drift, drift)
        angles = spherical_arc_angles(axes, seed=seed_axes)
        arc = arc_residual(angles, seed_angles)
        max_arc = max(max_arc, arc)
        body = body_fixed_axis_drift(chain, q_t, axes, seed_q, seed_axes)
        max_body = max(max_body, body)
        stations.append(
            StationInvariant(
                sigma=sigma,
                residual_to_cstar_m=max(line_center_residual(axis, center) for axis in axes.ordered()),
                sample_center_drift_m=drift,
                arcs_rad=angles,
                body_fixed_drift_rad=body,
                well_posed=True,
                reason="defined",
            )
        )
    ranges = simple_lock_ranges([q for _, q, _ in built])
    simple_ok = ranges[0] <= COORDINATE_LOCK_TOL_RAD or ranges[1] <= COORDINATE_LOCK_TOL_RAD
    simple_ok = simple_ok and (ranges[2] <= COORDINATE_LOCK_TOL_RAD or ranges[3] <= COORDINATE_LOCK_TOL_RAD)
    locking_ok = max_body <= BODY_FIXED_AXIS_TOL_RAD
    return SphericalInvariantReport(
        architecture=architecture,
        n=n,
        construction="s_ua_ub_r5",
        n_stations=len(accepted),
        global_center=(float(center[0]), float(center[1]), float(center[2])),
        global_rms_m=global_rms,
        global_max_m=global_max,
        max_center_drift_m=max_drift,
        max_arc_residual_rad=max_arc,
        max_body_fixed_drift_rad=max_body,
        simple_lock_ranges=ranges,
        simple_lock_passed=simple_ok,
        locking_policy="body_fixed_effective_axis",
        locking="pass" if locking_ok else "fail",
        verdict=_classify(global_max, global_rms, max_drift, max_arc, max_body),
        stations=tuple(stations),
    )


def exploratory_fixed_tuple_scan(
    chain: SerialRevoluteChain,
    segment: FiberSegment,
) -> tuple[ExploratoryTupleReport, ...]:
    """Scan fixed physical 4-subsets of ``R1…R5``. Not an exact RRRR claim."""
    accepted = [step for step in segment.accepted_samples if step.q is not None]
    reports: list[ExploratoryTupleReport] = []
    for indices in PHYSICAL_TUPLES_R1_TO_R5:
        groups: list[tuple[AxisLine, ...]] = []
        previous: tuple[AxisLine, ...] | None = None
        for step in accepted:
            current = chain.current_axes(step.q)
            axes = tuple(current[i] for i in indices)
            if previous is not None:
                axes = tuple(_sign_align_axis(axis, ref) for axis, ref in zip(axes, previous, strict=True))
            groups.append(axes)
            previous = axes
        if not groups:
            continue
        center = fit_global_center(groups)
        residuals = [line_center_residual(axis, center) for group in groups for axis in group]
        rms = float(np.sqrt(np.mean(np.square(residuals)))) if residuals else float("inf")
        max_res = max(residuals) if residuals else float("inf")
        drifts = []
        seed_axes = groups[0]
        seed_angles = _tuple_arc_angles(seed_axes)
        max_arc = 0.0
        for group in groups:
            sample_center = fit_global_center((group,))
            drifts.append(float(np.linalg.norm(sample_center - center)))
            max_arc = max(max_arc, arc_residual(_tuple_arc_angles(group, seed_axes), seed_angles))
        reports.append(
            ExploratoryTupleReport(
                indices=indices,
                label="-".join(f"R{i + 1}" for i in indices),
                global_rms_m=rms,
                global_max_m=max_res,
                max_center_drift_m=max(drifts) if drifts else float("inf"),
                max_arc_residual_rad=max_arc,
            )
        )
    return tuple(reports)


def _tuple_arc_angles(
    axes: tuple[AxisLine, ...],
    seed: tuple[AxisLine, ...] | None = None,
) -> tuple[float, float, float, float]:
    ordered = list(axes)
    if seed is not None:
        ordered = [_sign_align_axis(axis, ref) for axis, ref in zip(ordered, seed, strict=True)]
    dirs = [axis.w_array for axis in ordered]
    angles: list[float] = []
    for i, direction in enumerate(dirs):
        nxt = dirs[(i + 1) % 4]
        cos = float(np.clip(np.dot(unit_vector(direction), unit_vector(nxt)), -1.0, 1.0))
        angles.append(max(0.0, float(np.arccos(cos))))
    return (angles[0], angles[1], angles[2], angles[3])
