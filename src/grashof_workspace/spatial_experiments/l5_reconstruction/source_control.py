"""Source-chain ``h=c`` stitching control. No ``UXXX`` child is instantiated."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3, unit_vector
from grashof_workspace.spatial_experiments.branch_continuation import continue_implicit_branch
from grashof_workspace.spatial_experiments.continuation import wrap_joint_delta
from grashof_workspace.spatial_experiments.implicit_manifold import ambient_distance
from grashof_workspace.spatial_experiments.parent_atlas import wrap_periodic
from grashof_workspace.spatial_experiments.parent_level_sets import (
    PointingLevelSetProblem,
    correct_to_levelset,
    pointing_scalar,
)

from .direct_truth import found_configurations
from .models import (
    CampaignConfig,
    DirectPointingTruth,
    FixedPointProbe,
    SourceControlCRecord,
    SourceIntervalStatus,
    json_dumps_strict,
    json_object,
    resolve_stage_budgets,
    stage_envelope,
)
from .positive_control import PositiveControlArm, build_positive_control_arm
from .sphere_grid import SphereGrid, build_sphere_grid, paint_pointings

Array = NDArray[np.floating]
Vec3 = tuple[float, float, float]
DEDUP_Q_TOL = 0.35
COVERED_SOURCE_INTERVAL_STATUSES = frozenset(
    {
        SourceIntervalStatus.RETURNED_COMPONENT_FOUND,
        SourceIntervalStatus.COMPONENT_COMPLETE,
    }
)


def classify_source_interval_status(
    *,
    returned_count: int,
    open_count: int,
    singular_count: int,
) -> SourceIntervalStatus:
    """Evidence at one ``c``. Never emits ``COMPONENT_COMPLETE``."""

    if returned_count > 0:
        return SourceIntervalStatus.RETURNED_COMPONENT_FOUND
    if open_count > 0:
        return SourceIntervalStatus.OPEN_ONLY
    if singular_count > 0:
        return SourceIntervalStatus.SINGULAR
    return SourceIntervalStatus.UNRESOLVED


def radial_normal(p_star: Vec3 | Array) -> Vec3:
    arr = np.asarray(p_star, dtype=float).reshape(3)
    return as_vec3(unit_vector((float(arr[0]), float(arr[1]), float(arr[2])), name="p_star"))


def h_value(arm: PositiveControlArm, q: tuple[float, ...], n: Vec3) -> float:
    state = arm.chain.evaluate(q)
    return pointing_scalar(state.d, n)


def directed_q_distance(
    a: tuple[tuple[float, ...], ...],
    b: tuple[tuple[float, ...], ...],
    *,
    periodic: tuple[bool, ...] = (True,) * 5,
) -> float:
    if not a:
        return 0.0 if not b else float("inf")
    if not b:
        return float("inf")
    dists = []
    for qa in a:
        dists.append(min(float(ambient_distance(np.asarray(qa), np.asarray(qb), periodic)) for qb in b))
    return max(dists)


def symmetric_q_distance(
    a: tuple[tuple[float, ...], ...],
    b: tuple[tuple[float, ...], ...],
) -> float:
    return max(directed_q_distance(a, b), directed_q_distance(b, a))


@dataclass(frozen=True, slots=True)
class SourceControlFiber:
    fiber_id: str
    c: float
    q_samples: tuple[tuple[float, ...], ...]
    pointing_samples: tuple[Vec3, ...]
    branch_status: str
    returned: bool
    max_position_residual_m: float
    max_h_residual: float

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "fiber_id": self.fiber_id,
                "c": self.c,
                "sample_count": len(self.q_samples),
                "q_samples": [list(q) for q in self.q_samples],
                "pointing_samples": [list(d) for d in self.pointing_samples],
                "branch_status": self.branch_status,
                "returned": self.returned,
                "max_position_residual_m": self.max_position_residual_m,
                "max_h_residual": self.max_h_residual,
                "construction_kind": "task_level_set_control",
            }
        )


@dataclass(frozen=True, slots=True)
class SourceControlResult:
    probe_id: str
    n: Vec3
    c_values: tuple[float, ...]
    fibers: tuple[SourceControlFiber, ...]
    pointing_samples: tuple[Vec3, ...]
    hit_cells: tuple[bool, ...]
    unresolved_c_intervals: tuple[tuple[float, float], ...]
    notes: tuple[str, ...]
    c_records: tuple[SourceControlCRecord, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return json_object(
            {
                "probe_id": self.probe_id,
                "n": list(self.n),
                "c_values": list(self.c_values),
                "fibers": [f.to_json_dict() for f in self.fibers],
                "pointing_samples": [list(d) for d in self.pointing_samples],
                "hit_cell_count": int(sum(self.hit_cells)),
                "unresolved_c_intervals": [list(iv) for iv in self.unresolved_c_intervals],
                "c_records": [item.to_json_dict() for item in self.c_records],
                "notes": list(self.notes),
                "certificate_status": None,
            }
        )


def unresolved_c_intervals_from_records(
    c_values: tuple[float, ...],
    records: tuple[SourceControlCRecord, ...] | list[SourceControlCRecord],
) -> tuple[tuple[float, float], ...]:
    """Neighbor spans of c bins that are missing, open, singular, or unresolved."""
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


def summarize_c_records(
    c_values: tuple[float, ...],
    fibers_by_c: dict[float, tuple[SourceControlFiber, ...]],
    *,
    expected_seed_counts: dict[float, int],
    projected_seed_counts: dict[float, int],
    unique: tuple[SourceControlFiber, ...],
) -> tuple[SourceControlCRecord, ...]:
    records: list[SourceControlCRecord] = []
    for c in c_values:
        group = fibers_by_c.get(float(c), ())
        kinds = [_fiber_kind(item) for item in group]
        returned = sum(1 for kind in kinds if kind == "returned")
        open_count = sum(1 for kind in kinds if kind == "open")
        singular = sum(1 for kind in kinds if kind == "singular")
        unresolved = sum(1 for kind in kinds if kind == "unresolved")
        continued = sum(1 for item in group if item.q_samples)
        unique_ids = tuple(item.fiber_id for item in unique if abs(item.c - c) <= 1e-12 and item.q_samples)
        status = classify_source_interval_status(
            returned_count=returned,
            open_count=open_count,
            singular_count=singular,
        )
        records.append(
            SourceControlCRecord(
                c=float(c),
                expected_seed_count=int(expected_seed_counts.get(float(c), 0)),
                projected_seed_count=int(projected_seed_counts.get(float(c), 0)),
                continued_component_count=continued,
                returned_count=returned,
                open_count=open_count,
                singular_count=singular,
                unresolved_count=unresolved,
                deduplicated_component_ids=unique_ids,
                parameter_interval_status=status.value,
            )
        )
    return tuple(records)


def choose_c_values(h_samples: tuple[float, ...], count: int) -> tuple[float, ...]:
    if not h_samples:
        return tuple(float(x) for x in np.linspace(-0.8, 0.8, count))
    lo = min(h_samples)
    hi = max(h_samples)
    if abs(hi - lo) < 1e-9:
        return (float(lo),)
    return tuple(float(x) for x in np.linspace(lo, hi, count))


def continue_source_fiber(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    n: Vec3,
    c: float,
    q_seed: tuple[float, ...],
    *,
    fiber_id: str,
    max_steps: int,
    step_size: float,
) -> SourceControlFiber:
    q_proj, ok, _ = correct_to_levelset(arm.model, q_seed, probe.p_star, n, c)
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
        np.asarray(q_proj, dtype=float),
        branch_id=fiber_id,
        max_steps=max_steps,
        step_size=step_size,
    )
    qs: list[tuple[float, ...]] = []
    ds: list[Vec3] = []
    pos_res: list[float] = []
    h_res: list[float] = []
    for step in trace.steps:
        if not step.accepted or step.x is None:
            continue
        q = tuple(float(v) for v in step.x)
        state = arm.chain.evaluate(q)
        qs.append(q)
        ds.append(as_vec3(state.d))
        pos_res.append(float(np.linalg.norm(np.asarray(state.p) - np.asarray(probe.p_star))))
        h_res.append(abs(pointing_scalar(state.d, n) - c))
    return SourceControlFiber(
        fiber_id=fiber_id,
        c=c,
        q_samples=tuple(qs),
        pointing_samples=tuple(ds),
        branch_status=trace.branch_status,
        returned=trace.returned,
        max_position_residual_m=max(pos_res) if pos_res else float("inf"),
        max_h_residual=max(h_res) if h_res else float("inf"),
    )


def deduplicate_fibers(fibers: tuple[SourceControlFiber, ...], *, tol: float = DEDUP_Q_TOL) -> tuple[SourceControlFiber, ...]:
    kept: list[SourceControlFiber] = []
    for fiber in fibers:
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


def build_source_control(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    discovery: DirectPointingTruth,
    *,
    c_count: int,
    confirmation_level: int,
    max_steps: int = 24,
    step_size: float = 0.08,
) -> SourceControlResult:
    n = radial_normal(probe.p_star)
    configs = found_configurations(discovery)
    h_samples = tuple(h_value(arm, q, n) for q in configs)
    c_values = choose_c_values(h_samples, c_count)
    fibers: list[SourceControlFiber] = []
    fibers_by_c: dict[float, list[SourceControlFiber]] = {}
    expected_seed_counts: dict[float, int] = {}
    projected_seed_counts: dict[float, int] = {}
    for i, c in enumerate(c_values):
        seeds = [q for q in configs if abs(h_value(arm, q, n) - c) <= 0.35] or list(configs[:3])
        if not seeds and configs:
            seeds = [min(configs, key=lambda q: abs(h_value(arm, q, n) - c))]
        chosen = seeds[:3]
        expected_seed_counts[float(c)] = len(chosen)
        projected = 0
        group: list[SourceControlFiber] = []
        for j, seed in enumerate(chosen):
            _q_proj, ok, _ = correct_to_levelset(arm.model, seed, probe.p_star, n, c)
            if ok:
                projected += 1
            fiber = continue_source_fiber(
                arm,
                probe,
                n,
                c,
                seed,
                fiber_id=f"{probe.probe_id}_c{i}_s{j}",
                max_steps=max_steps,
                step_size=step_size,
            )
            group.append(fiber)
            fibers.append(fiber)
        projected_seed_counts[float(c)] = projected
        fibers_by_c[float(c)] = group
    unique = deduplicate_fibers(tuple(fibers))
    pointings = tuple(d for fiber in unique for d in fiber.pointing_samples)
    grid = build_sphere_grid(confirmation_level)
    hits = paint_pointings(grid, pointings)
    c_records = summarize_c_records(
        c_values,
        {key: tuple(val) for key, val in fibers_by_c.items()},
        expected_seed_counts=expected_seed_counts,
        projected_seed_counts=projected_seed_counts,
        unique=unique,
    )
    unresolved = unresolved_c_intervals_from_records(c_values, c_records)
    return SourceControlResult(
        probe_id=probe.probe_id,
        n=n,
        c_values=c_values,
        fibers=unique,
        pointing_samples=pointings,
        hit_cells=hits,
        unresolved_c_intervals=unresolved,
        notes=(
            "Source h=c control; not a natural UURU child.",
            "n = p_star / ||p_star||.",
            "Unresolved c intervals come from failed or open bins, not from an empty fiber list.",
        ),
        c_records=c_records,
    )


def write_source_control_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
) -> dict[str, Any]:
    import json

    arm = build_positive_control_arm(config.geometry)
    budgets = resolve_stage_budgets(config, mode)
    records: list[dict[str, Any]] = []
    for probe in probes:
        truth_path = outdir / probe.probe_id / "direct_truth.json"
        if not truth_path.is_file():
            raise FileNotFoundError(f"missing prerequisite {truth_path}")
        raw = json.loads(truth_path.read_text(encoding="utf-8"))
        from .models import (
            DirectPointingTruth,
            PointingSolutionCluster,
            PointingSolveStatus,
            PointingTargetSolve,
        )

        def _load_truth(blob: dict[str, Any]) -> DirectPointingTruth:
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

        discovery = _load_truth(raw["discovery"])
        result = build_source_control(
            arm,
            probe,
            discovery,
            c_count=budgets.source_c_value_count,
            confirmation_level=budgets.confirmation_icosphere_level,
            max_steps=budgets.continuation_steps,
        )
        path = outdir / probe.probe_id / "source_control.json"
        path.write_text(json_dumps_strict(result.to_json_dict()), encoding="utf-8")
        records.append({"probe_id": probe.probe_id, "fiber_count": len(result.fibers)})
        _ = wrap_periodic
        _ = wrap_joint_delta
        _ = SphereGrid
    summary = {
        **stage_envelope(
            config,
            stage="source-control",
            mode=mode,
            probe_ids=tuple(p.probe_id for p in probes),
        ),
        "probes": records,
        "allows_full_campaign_disposition": budgets.allows_full_campaign_disposition,
        "limitations": []
        if budgets.allows_full_campaign_disposition
        else ["mode cannot issue full-campaign disposition"],
    }
    (outdir / "source_control.json").write_text(json_dumps_strict(summary), encoding="utf-8")
    return summary
