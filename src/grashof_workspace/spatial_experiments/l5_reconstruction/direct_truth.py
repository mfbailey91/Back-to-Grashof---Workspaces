"""Independent source-chain target-direction IK (decomposition-free truth).

The analytical oracle is compared after solving and is not a confirmation seed
source. Statuses remain numerical: FOUND / NOT_FOUND_AT_DECLARED_BUDGET /
UNRESOLVED.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares
from scipy.stats.qmc import Sobol

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.continuation import wrap_joint_delta
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain

from .models import (
    CampaignConfig,
    DirectPointingTruth,
    FixedPointProbe,
    OracleFeasibility,
    PointingSolutionCluster,
    PointingSolveStatus,
    PointingTargetSolve,
    json_dumps_strict,
    json_object,
    stage_envelope,
)
from .positive_control import (
    PositiveControlArm,
    analytic_seed_configuration,
    build_positive_control_arm,
    direction_oracle,
)
from .sphere_grid import build_sphere_grid, pointing_geodesic

Array = NDArray[np.floating]
Vec3 = tuple[float, float, float]
POSITION_SCALE_M = 1.0
CLUSTER_TOL_RAD = 0.05


def _wrap_q(q: Array | tuple[float, ...]) -> tuple[float, ...]:
    arr = np.asarray(q, dtype=float).reshape(-1)
    return tuple(float(np.arctan2(np.sin(v), np.cos(v))) for v in arr)


def pointing_residual(
    chain: SerialRevoluteChain,
    q: Array | tuple[float, ...],
    p_star: Array,
    d_target: Array,
) -> Array:
    state = chain.evaluate(tuple(float(v) for v in np.asarray(q, dtype=float)))
    r_position = (np.asarray(state.p, dtype=float) - np.asarray(p_star, dtype=float)) / POSITION_SCALE_M
    r_cross = np.cross(np.asarray(state.d, dtype=float), np.asarray(d_target, dtype=float))
    r_antipode = np.array([1.0 - float(np.dot(state.d, d_target))], dtype=float)
    return np.concatenate([r_position, r_cross, r_antipode])


def _accept_state(
    chain: SerialRevoluteChain,
    q: tuple[float, ...],
    p_star: Array,
    d_target: Array,
    *,
    position_tol_m: float,
    pointing_tol_rad: float,
) -> tuple[bool, float, float]:
    state = chain.evaluate(q)
    pos = float(np.linalg.norm(np.asarray(state.p) - p_star))
    geo = pointing_geodesic(state.d, d_target)
    dot = float(np.dot(state.d, d_target))
    ok = pos <= position_tol_m and geo <= pointing_tol_rad and dot > 0.0
    return ok, pos, geo


def _solve_from(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    p_star: Array,
    d_target: Array,
    *,
    max_nfev: int,
    position_tol_m: float,
    pointing_tol_rad: float,
) -> tuple[tuple[float, ...] | None, float, float]:
    def fun(x: Array) -> Array:
        return pointing_residual(chain, x, p_star, d_target)

    try:
        result = least_squares(fun, np.asarray(q0, dtype=float), max_nfev=max_nfev, xtol=1e-10, ftol=1e-10)
    except (ValueError, np.linalg.LinAlgError, RuntimeError):
        return None, float("inf"), float("inf")
    q = _wrap_q(result.x)
    ok, pos, geo = _accept_state(
        chain, q, p_star, d_target, position_tol_m=position_tol_m, pointing_tol_rad=pointing_tol_rad
    )
    if ok:
        return q, pos, geo
    return None, pos, geo


def _sobol_starts(count: int, seed: int, scramble: bool) -> tuple[tuple[float, ...], ...]:
    engine = Sobol(d=5, scramble=scramble, seed=seed)
    raw = engine.random(count)
    mapped = 2.0 * pi * raw - pi
    return tuple(_wrap_q(row) for row in mapped)


def _cluster_solutions(
    chain: SerialRevoluteChain,
    p_star: Array,
    d_target: Array,
    solutions: list[tuple[tuple[float, ...], str, float, float]],
) -> tuple[PointingSolutionCluster, ...]:
    unused = list(solutions)
    clusters: list[PointingSolutionCluster] = []
    cid = 0
    while unused:
        q0, src0, pos0, geo0 = unused.pop(0)
        members = [q0]
        sources = [src0]
        rest: list[tuple[tuple[float, ...], str, float, float]] = []
        for item in unused:
            if float(np.linalg.norm(wrap_joint_delta(item[0], q0))) <= CLUSTER_TOL_RAD:
                members.append(item[0])
                sources.append(item[1])
            else:
                rest.append(item)
        unused = rest
        best = min(members, key=lambda q: _accept_state(chain, q, p_star, d_target, position_tol_m=1e9, pointing_tol_rad=1e9)[1])
        ok, pos, geo = _accept_state(chain, best, p_star, d_target, position_tol_m=1e9, pointing_tol_rad=1e9)
        clusters.append(
            PointingSolutionCluster(
                cluster_id=f"c{cid}",
                q_representative=best,
                members=tuple(members),
                seed_sources=tuple(sources),
                position_residual_m=pos,
                pointing_geodesic_rad=geo,
            )
        )
        cid += 1
        _ = ok
        _ = pos0
        _ = geo0
        _ = src0
    return tuple(clusters)


def solve_target(
    chain: SerialRevoluteChain,
    p_star: Array,
    d_target: Array,
    *,
    starts: list[tuple[tuple[float, ...], str]],
    max_nfev: int,
    position_tol_m: float,
    pointing_tol_rad: float,
    target_index: int,
) -> PointingTargetSolve:
    found: list[tuple[tuple[float, ...], str, float, float]] = []
    n_starts = 0
    unresolved = False
    for q0, source in starts:
        n_starts += 1
        q, pos, geo = _solve_from(
            chain,
            q0,
            p_star,
            d_target,
            max_nfev=max_nfev,
            position_tol_m=position_tol_m,
            pointing_tol_rad=pointing_tol_rad,
        )
        if q is None and not np.isfinite(pos):
            unresolved = True
            continue
        if q is not None:
            found.append((q, source, pos, geo))
    if found:
        clusters = _cluster_solutions(chain, p_star, d_target, found)
        best_pos = min(c.position_residual_m for c in clusters)
        best_geo = min(c.pointing_geodesic_rad for c in clusters)
        status = PointingSolveStatus.FOUND
    elif unresolved and not found:
        clusters = ()
        best_pos = None
        best_geo = None
        status = PointingSolveStatus.UNRESOLVED
    else:
        clusters = ()
        best_pos = None
        best_geo = None
        status = PointingSolveStatus.NOT_FOUND_AT_DECLARED_BUDGET
    return PointingTargetSolve(
        target_index=target_index,
        d_target=as_vec3(d_target),
        status=status,
        clusters=clusters,
        best_position_residual_m=best_pos,
        best_pointing_geodesic_rad=best_geo,
        n_starts=n_starts,
    )


def build_direct_pointing_truth(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    config: CampaignConfig,
    *,
    split: str,
    icosphere_level: int | None = None,
    sobol_count: int | None = None,
    max_nfev: int | None = None,
    target_indices: tuple[int, ...] | None = None,
    neighbor_propagate: bool = True,
) -> DirectPointingTruth:
    if split not in {"discovery", "confirmation"}:
        raise ValueError("split must be discovery or confirmation")
    level = icosphere_level if icosphere_level is not None else (
        config.mode("smoke").discovery_icosphere_level
        if split == "discovery"
        else config.mode("smoke").confirmation_icosphere_level
    )
    # Use the named campaign mode budgets when the caller does not override.
    count = sobol_count if sobol_count is not None else config.mode("smoke").sobol_seed_count_per_target
    nfev = max_nfev if max_nfev is not None else config.mode("smoke").max_nfev_per_start
    seed = config.sobol_seed_discovery if split == "discovery" else config.sobol_seed_confirmation
    grid = build_sphere_grid(level)
    indices = target_indices if target_indices is not None else tuple(range(grid.vertices.shape[0]))
    sobol = _sobol_starts(count, seed, config.sobol_scramble)
    probe_seed = analytic_seed_configuration(arm.geometry, probe)
    p_star = np.asarray(probe.p_star, dtype=float)
    solved_by_vertex: dict[int, tuple[float, ...]] = {}
    solves: list[PointingTargetSolve] = []
    for idx in indices:
        d = grid.vertices[idx]
        starts: list[tuple[tuple[float, ...], str]] = []
        if neighbor_propagate:
            for nb in grid.adjacency[idx]:
                if nb in solved_by_vertex:
                    starts.append((solved_by_vertex[nb], "solved_neighbor"))
        starts.append((probe_seed, "probe_seed"))
        starts.extend((q, "sobol_bank") for q in sobol)
        solve = solve_target(
            arm.chain,
            p_star,
            d,
            starts=starts,
            max_nfev=nfev,
            position_tol_m=config.tolerances.position_residual_m,
            pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
            target_index=idx,
        )
        solves.append(solve)
        if solve.status is PointingSolveStatus.FOUND and solve.clusters:
            solved_by_vertex[idx] = solve.clusters[0].q_representative
    found = sum(1 for s in solves if s.status is PointingSolveStatus.FOUND)
    not_found = sum(1 for s in solves if s.status is PointingSolveStatus.NOT_FOUND_AT_DECLARED_BUDGET)
    unresolved = sum(1 for s in solves if s.status is PointingSolveStatus.UNRESOLVED)
    return DirectPointingTruth(
        probe_id=probe.probe_id,
        split=split,
        icosphere_level=level,
        solves=tuple(solves),
        found_count=found,
        not_found_count=not_found,
        unresolved_count=unresolved,
    )


@dataclass(frozen=True, slots=True)
class DirectOracleAgreement:
    n_found: int
    n_strict_oracle_infeasible_found: int
    n_strict_oracle_feasible_missing: int
    notes: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "n_found": self.n_found,
                "n_strict_oracle_infeasible_found": self.n_strict_oracle_infeasible_found,
                "n_strict_oracle_feasible_missing": self.n_strict_oracle_feasible_missing,
                "notes": list(self.notes),
            }
        )


def compare_direct_truth_to_oracle(
    truth: DirectPointingTruth,
    geometry: Any,
    p_star: Vec3,
    *,
    margin_tol_m: float,
) -> DirectOracleAgreement:
    false_pos = 0
    misses = 0
    for solve in truth.solves:
        oracle = direction_oracle(geometry, p_star, solve.d_target, margin_tol_m=margin_tol_m)
        if (
            solve.status is PointingSolveStatus.FOUND
            and oracle.feasibility is OracleFeasibility.INFEASIBLE
            and oracle.margin_m <= -margin_tol_m
        ):
            false_pos += 1
        if (
            oracle.feasibility is OracleFeasibility.FEASIBLE
            and oracle.margin_m >= margin_tol_m
            and solve.status is PointingSolveStatus.NOT_FOUND_AT_DECLARED_BUDGET
        ):
            misses += 1
    return DirectOracleAgreement(
        n_found=truth.found_count,
        n_strict_oracle_infeasible_found=false_pos,
        n_strict_oracle_feasible_missing=misses,
        notes=(
            "Oracle comparison is post-solve and does not rewrite numerical statuses.",
            "NOT_FOUND_AT_DECLARED_BUDGET is distinct from oracle UNREACHABLE.",
        ),
    )


def found_configurations(truth: DirectPointingTruth) -> tuple[tuple[float, ...], ...]:
    out: list[tuple[float, ...]] = []
    for solve in truth.solves:
        if solve.status is not PointingSolveStatus.FOUND:
            continue
        for cluster in solve.clusters:
            out.append(cluster.q_representative)
    return tuple(out)


def write_truth_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
    target_limit: int | None = None,
    sobol_count: int | None = None,
    max_nfev: int | None = None,
) -> dict[str, Any]:
    arm = build_positive_control_arm(config.geometry)
    budgets = config.mode(mode)
    n_sobol = budgets.sobol_seed_count_per_target if sobol_count is None else sobol_count
    nfev = budgets.max_nfev_per_start if max_nfev is None else max_nfev
    records: list[dict[str, Any]] = []
    for probe in probes:
        indices: tuple[int, ...] | None = None
        if target_limit is not None:
            grid = build_sphere_grid(budgets.discovery_icosphere_level)
            indices = tuple(range(min(target_limit, grid.vertices.shape[0])))
        discovery = build_direct_pointing_truth(
            arm,
            probe,
            config,
            split="discovery",
            icosphere_level=budgets.discovery_icosphere_level,
            sobol_count=n_sobol,
            max_nfev=nfev,
            target_indices=indices,
        )
        confirmation = build_direct_pointing_truth(
            arm,
            probe,
            config,
            split="confirmation",
            icosphere_level=budgets.confirmation_icosphere_level,
            sobol_count=n_sobol,
            max_nfev=nfev,
            target_indices=indices,
        )
        agreement = compare_direct_truth_to_oracle(
            confirmation,
            config.geometry,
            probe.p_star,
            margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m,
        )
        payload = {
            "probe_id": probe.probe_id,
            "discovery": discovery.to_json_dict(),
            "confirmation": confirmation.to_json_dict(),
            "oracle_agreement": agreement.to_json_dict(),
        }
        path = outdir / probe.probe_id / "direct_truth.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_dumps_strict(payload), encoding="utf-8")
        records.append({"probe_id": probe.probe_id, "found_confirmation": confirmation.found_count})
    summary = {
        **stage_envelope(
            config,
            stage="truth",
            mode=mode,
            probe_ids=tuple(p.probe_id for p in probes),
        ),
        "probes": records,
    }
    (outdir / "truth.json").write_text(json_dumps_strict(summary), encoding="utf-8")
    return summary
