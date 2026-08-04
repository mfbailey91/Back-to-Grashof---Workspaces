"""Fixed-position orientation capability experiment (Sprint 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from sixr_grashof.architectures import ArchitectureParams
from sixr_grashof.io.schemas import ExperimentRecord
from sixr_grashof.kinematics.ik import JointConfig, solve_ik
from sixr_grashof.reductions.engine import reduce_sixr
from sixr_grashof.sampling.orientations import (
    SampleResolution,
    geodesic_angle,
    sample_orientations,
)
from sixr_grashof.sampling.workspace import WorkspaceSample

COVERAGE_DEXTERITY_THRESHOLD = 0.70
COMPONENT_FRACTION_THRESHOLD = 0.85


@dataclass(frozen=True, slots=True)
class FixedPositionResult:
    """Numerical orientation capability at one Cartesian position."""

    record: ExperimentRecord
    feasible_indices: tuple[int, ...]
    statuses: tuple[str, ...]
    component_labels: tuple[int, ...]
    eligible_solve_rate: float


def _union_find_components(n: int, edges: list[tuple[int, int]]) -> list[int]:
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in edges:
        union(a, b)
    roots = [find(i) for i in range(n)]
    remap: dict[int, int] = {}
    labels: list[int] = []
    for r in roots:
        if r not in remap:
            remap[r] = len(remap)
        labels.append(remap[r])
    return labels


def orientation_adjacency(
    rotations: list[np.ndarray],
    feasible: list[int],
    *,
    radius_factor: float = 2.5,
) -> tuple[list[tuple[int, int]], list[int], float]:
    """Build SO(3) adjacency among feasible samples; return edges, labels, radius."""
    if len(feasible) <= 1:
        return [], [0] * len(feasible), 0.0
    Rs = [rotations[i] for i in feasible]
    m = len(Rs)
    # nearest-neighbor distances
    nn = []
    for i in range(m):
        best = float("inf")
        for j in range(m):
            if i == j:
                continue
            best = min(best, geodesic_angle(Rs[i], Rs[j]))
        nn.append(best)
    radius = float(np.median(nn)) * radius_factor if nn else 0.0
    edges: list[tuple[int, int]] = []
    for i in range(m):
        for j in range(i + 1, m):
            if geodesic_angle(Rs[i], Rs[j]) <= radius:
                edges.append((i, j))
    labels = _union_find_components(m, edges)
    return edges, labels, radius


def run_fixed_position_experiment(
    arm: Any,
    sample: WorkspaceSample,
    *,
    resolution: SampleResolution = "coarse",
    seed: int = 0,
    n_ik_starts: int = 6,
    architecture_id: str = "A",
    params: ArchitectureParams | None = None,
    orientation_count: int | None = None,
) -> FixedPositionResult:
    """Sample orientations at fixed tool position and estimate coverage/connectivity."""
    rotations = sample_orientations(resolution, seed=seed, count=orientation_count)
    statuses: list[str] = []
    feasible: list[int] = []
    singularities = 0
    seed_q: JointConfig = sample.joint_seed

    for i, R in enumerate(rotations):
        sol = solve_ik(
            arm,
            sample.position,
            R,
            seed=seed_q,
            n_starts=n_ik_starts,
            rng_seed=seed + i,
        )
        statuses.append(sol.status)
        if sol.status == "solved":
            feasible.append(i)
            if sol.singularity_flag:
                singularities += 1
            if sol.configuration is not None:
                seed_q = sol.configuration  # warm-start continuation

    _, labels, _ = orientation_adjacency(rotations, feasible)
    n = len(rotations)
    n_solved = len(feasible)
    n_unreach = sum(1 for s in statuses if s == "unreachable")
    n_fail = sum(1 for s in statuses if s == "solver_failed")
    coverage = n_solved / n if n else 0.0
    eligible = n_solved + n_fail
    eligible_rate = n_solved / eligible if eligible else 0.0
    n_comp = len(set(labels)) if labels else 0
    if n_solved == 0:
        n_comp = 0
        largest_frac = 0.0
    else:
        counts = np.bincount(np.array(labels, dtype=int))
        largest_frac = float(counts.max()) / n_solved

    # Strict dexterity: high solve rate among geometrically eligible orientations
    # and a dominant connected component among solved samples.
    strict = (
        eligible_rate >= COVERAGE_DEXTERITY_THRESHOLD
        and largest_frac >= COMPONENT_FRACTION_THRESHOLD
        and n_comp >= 1
        and eligible >= max(8, n // 10)
    )

    # Analytical side (may be filled more completely in Sprint 5)
    p = params or arm.params
    aid = architecture_id if architecture_id in {"A", "B", "C"} else str(architecture_id)[0]
    reduction = reduce_sixr(aid, sample.joint_seed, params=p)
    link = reduction.spherical.linkage
    angles = None if link is None else (link.alpha, link.beta, link.gamma, link.eta)

    record = ExperimentRecord(
        architecture_id=aid,
        offset_parameters={
            "epsilon_w": getattr(p, "epsilon_w", 0.0),
            "epsilon_s": getattr(p, "epsilon_s", 0.0),
            "L2": p.L2,
            "L3": p.L3,
            "Lt": p.Lt,
        },
        position=sample.position,
        position_branch_id=sample.label,
        joint_configuration_seed=sample.joint_seed,
        regional_reduction_status=reduction.regional.status,
        regional_reachable=reduction.regional.wrist_reachable,
        spherical_reduction_status=reduction.spherical.status,
        concurrency_residual=reduction.spherical.concurrency.residual_rho,
        spherical_link_angles=angles,
        T1=None,
        T2=None,
        T3=None,
        T4=None,
        T_sign_tuple=None,
        T_product=None,
        linkage_type=None,
        input_motion_class=None,
        output_motion_class=None,
        hand_link_motion_class=None,
        analytical_prediction=None,
        orientation_sample_count=n,
        orientation_coverage=coverage,
        orientation_component_count=n_comp,
        strict_sampled_dexterity=strict,
        singularity_flags=singularities,
        solved_count=n_solved,
        unreachable_count=n_unreach,
        solver_failed_count=n_fail,
        prediction_outcome="not_applicable",
        sample_resolution=resolution,
        random_seed=seed,
        notes="Sprint 4 fixed-position numerical ground truth",
        extras={"eligible_solve_rate": eligible_rate},
    )
    return FixedPositionResult(
        record=record,
        feasible_indices=tuple(feasible),
        statuses=tuple(statuses),
        component_labels=tuple(labels),
        eligible_solve_rate=eligible_rate,
    )
