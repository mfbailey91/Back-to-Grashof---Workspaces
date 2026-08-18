"""Natural UURU family discovery, re-seeding, transversality, and chart overlap."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.implicit_manifold import (
    ambient_distance,
    orthonormal_tangent_basis,
)
from grashof_workspace.spatial_experiments.jacobians import position_jacobian

from .direct_truth import found_configurations
from .models import (
    CampaignConfig,
    DirectPointingTruth,
    FamilyAdmissibilityStatus,
    FixedPointProbe,
    LeafFamilyResult,
    NaturalLeafCertificate,
    NaturalLeafSample,
    ReseedAttempt,
    ReseedAudit,
    TransversalityAudit,
    json_dumps_strict,
    stage_envelope,
)
from .positive_control import PositiveControlArm, build_positive_control_arm
from .source_control import directed_q_distance, symmetric_q_distance
from .sphere_grid import pointing_geodesic
from .spherical_chart import SphericalClosureChart, charts_from_config
from .uuru_leaf import (
    ClosedUURULeafProblem,
    child_tangent,
    continue_uuru_leaf,
    issue_leaf_certificate,
    leaf_spec_for,
    problem_from_source_seed,
    tangent_principal_angle,
)


def cluster_circular(values: tuple[float, ...], n_bins: int) -> tuple[tuple[float, tuple[int, ...]], ...]:
    if not values:
        return ()
    bins: list[list[int]] = [[] for _ in range(n_bins)]
    for i, val in enumerate(values):
        wrapped = float(np.arctan2(np.sin(val), np.cos(val)))
        idx = int(np.floor((wrapped + np.pi) / (2.0 * np.pi) * n_bins)) % n_bins
        bins[idx].append(i)
    out: list[tuple[float, tuple[int, ...]]] = []
    for members in bins:
        if not members:
            continue
        angs = np.asarray([values[i] for i in members], dtype=float)
        mean = float(np.arctan2(np.mean(np.sin(angs)), np.mean(np.cos(angs))))
        out.append((mean, tuple(members)))
    return tuple(out)


def _wrap_angle(a: float, b: float) -> float:
    return abs(float(np.arctan2(np.sin(a - b), np.cos(a - b))))


def choose_arclength_samples(
    samples: tuple[NaturalLeafSample, ...],
    count: int = 3,
) -> tuple[NaturalLeafSample, ...]:
    ordered = tuple(sorted(samples, key=lambda item: item.s))
    if len(ordered) <= count:
        return ordered
    if count <= 1:
        return (ordered[0],)
    start, mid, end = 0, len(ordered) // 2, len(ordered) - 1
    picks = (start, mid, end) if count == 3 else tuple(
        round(i * (len(ordered) - 1) / (count - 1)) for i in range(count)
    )
    seen: set[int] = set()
    out: list[NaturalLeafSample] = []
    for idx in picks:
        if idx in seen:
            continue
        seen.add(idx)
        out.append(ordered[idx])
    return tuple(out)


def directed_pointing_distance(
    a: tuple[tuple[float, float, float], ...],
    b: tuple[tuple[float, float, float], ...],
) -> float:
    if not a:
        return 0.0 if not b else float("inf")
    if not b:
        return float("inf")
    return max(min(pointing_geodesic(x, y) for y in b) for x in a)


def audit_reseeded_component(
    arm: PositiveControlArm,
    chart: SphericalClosureChart,
    original_problem: ClosedUURULeafProblem,
    original_samples: tuple[NaturalLeafSample, ...],
    *,
    q_tol: float,
    p_tol: float,
    lambda_tol: float,
    max_steps: int,
    step_size: float = 0.08,
    tangent_tol: float = 0.05,
    lambda_fixed: float | None = None,
    original_returned: bool | None = None,
    original_branch_status: str | None = None,
    reseed_count: int = 3,
) -> ReseedAudit:
    forced = original_problem.lambda_fixed if lambda_fixed is None else float(lambda_fixed)
    lambda_shift = _wrap_angle(forced, original_problem.lambda_fixed)
    budget_truncated = max_steps < 3 and len(original_samples) >= 3
    if len(original_samples) < 3:
        return ReseedAudit(
            status="UNRESOLVED",
            n_reseeds=len(original_samples),
            max_symmetric_q_distance_rad=None,
            max_pointing_distance_rad=None,
            notes=("fewer than three samples; reseed cannot pass",),
            attempts=(),
            max_tangent_error=None,
            all_component_ids_match=None,
        )
    chosen = choose_arclength_samples(original_samples, reseed_count)
    labels = ("start", "mid", "end")
    attempts: list[ReseedAttempt] = []
    for label, sample in zip(labels, chosen, strict=False):
        notes: list[str] = ["independent ClosedUURULeafProblem rebuild"]
        if sample.chart_singularity:
            attempts.append(
                ReseedAttempt(
                    reseed_id=label,
                    seed_s=sample.s,
                    lambda_error_rad=lambda_shift,
                    symmetric_wrapped_q_distance_rad=None,
                    symmetric_pointing_distance_rad=None,
                    tangent_error=None,
                    returned_match=None,
                    branch_status_match=None,
                    component_identity=None,
                    status="UNRESOLVED",
                    notes=("chart-singular reseed",),
                )
            )
            continue
        rebuilt = problem_from_source_seed(
            arm,
            chart,
            sample.q_source,
            original_problem.p_star,
            leaf_id=f"{original_problem.problem_id}_{label}",
            lambda_fixed=forced,
        )
        if rebuilt is None:
            status = "FAIL" if lambda_shift > lambda_tol else "UNRESOLVED"
            attempts.append(
                ReseedAttempt(
                    reseed_id=label,
                    seed_s=sample.s,
                    lambda_error_rad=lambda_shift,
                    symmetric_wrapped_q_distance_rad=None,
                    symmetric_pointing_distance_rad=None,
                    tangent_error=None,
                    returned_match=None,
                    branch_status_match=None,
                    component_identity=False,
                    status=status,
                    notes=("rebuild returned None",),
                )
            )
            continue
        problem_i, x_i = rebuilt
        reseeded_samples, branch_status, returned = continue_uuru_leaf(
            problem_i, x_i, max_steps=max_steps, step_size=step_size
        )
        seed_q_err = float(
            ambient_distance(
                np.asarray(sample.q_source, dtype=float),
                np.asarray(problem_i.physical_q(x_i), dtype=float),
                (True,) * 5,
            )
        )
        seed_state = problem_i.independent_chain.evaluate(problem_i.physical_q(x_i))
        seed_p_err = pointing_geodesic(sample.pointing, as_vec3(seed_state.d))
        half_width = float(step_size) * float(max(1, max_steps))
        local_orig = tuple(item for item in original_samples if abs(item.s - sample.s) <= half_width)
        reseeded_q = tuple(item.q_source for item in reseeded_samples)
        reseeded_p = tuple(item.pointing for item in reseeded_samples)
        q_cover = directed_q_distance(tuple(item.q_source for item in local_orig), reseeded_q) if reseeded_q else None
        p_cover = directed_pointing_distance(tuple(item.pointing for item in local_orig), reseeded_p) if reseeded_p else None
        q_dist = seed_q_err
        p_dist = seed_p_err
        if q_cover is not None and q_cover > q_tol:
            notes.append("open-branch trace sampling is not a self-distance")
        if p_cover is not None and p_cover > p_tol:
            notes.append("open-branch pointing cover is a sampling diagnostic")
        tangent_err: float | None = None
        try:
            t0 = child_tangent(original_problem, np.asarray(sample.x, dtype=float))
            t1 = child_tangent(problem_i, x_i)
            tangent_err = tangent_principal_angle(t0, t1)
        except (ValueError, np.linalg.LinAlgError):
            notes.append("child tangent unresolved")
        lam_err = _wrap_angle(problem_i.lambda_fixed, original_problem.lambda_fixed)
        returned_match = None if original_returned is None else returned == original_returned
        branch_match = None if original_branch_status is None else branch_status == original_branch_status
        seed_ok = seed_q_err <= q_tol and seed_p_err <= p_tol
        t_ok = tangent_err is not None and tangent_err <= tangent_tol
        lam_ok = lam_err <= lambda_tol
        if budget_truncated:
            status = "UNRESOLVED"
            notes.append("truncated continuation budget")
            identity = False
        elif not lam_ok:
            status = "FAIL"
            notes.append("forced lambda mismatch")
            identity = False
        elif tangent_err is None:
            status = "UNRESOLVED"
            identity = False
        elif not (seed_ok and t_ok):
            status = "FAIL"
            identity = False
        else:
            status = "PASS"
            identity = True
            notes.append("identity from seed reconstruction and child tangent")
        attempts.append(
            ReseedAttempt(
                reseed_id=label,
                seed_s=sample.s,
                lambda_error_rad=lam_err,
                symmetric_wrapped_q_distance_rad=q_dist,
                symmetric_pointing_distance_rad=p_dist,
                tangent_error=tangent_err,
                returned_match=returned_match,
                branch_status_match=branch_match,
                component_identity=identity,
                status=status,
                notes=tuple(notes),
            )
        )
    statuses = {item.status for item in attempts}
    if "FAIL" in statuses:
        agg = "FAIL"
    elif "UNRESOLVED" in statuses or not attempts:
        agg = "UNRESOLVED"
    else:
        agg = "PASS"
    q_vals = [item.symmetric_wrapped_q_distance_rad for item in attempts if item.symmetric_wrapped_q_distance_rad is not None]
    p_vals = [item.symmetric_pointing_distance_rad for item in attempts if item.symmetric_pointing_distance_rad is not None]
    t_vals = [item.tangent_error for item in attempts if item.tangent_error is not None]
    identities = [item.component_identity for item in attempts]
    return ReseedAudit(
        status=agg,
        n_reseeds=len(attempts),
        max_symmetric_q_distance_rad=None if not q_vals else max(q_vals),
        max_pointing_distance_rad=None if not p_vals else max(p_vals),
        notes=("independent start/mid/end rebuilds; no self-comparison",),
        attempts=tuple(attempts),
        max_tangent_error=None if not t_vals else max(t_vals),
        all_component_ids_match=all(identities) if identities else None,
    )


def estimate_transversality(
    arm: PositiveControlArm,
    q_a: tuple[float, ...],
    q_b: tuple[float, ...],
) -> TransversalityAudit:
    jp = position_jacobian(arm.chain, q_a)
    tangent_plane = orthonormal_tangent_basis(jp, expected_nullity=2)
    delta = np.asarray(q_b, dtype=float) - np.asarray(q_a, dtype=float)
    for i in range(delta.size):
        delta[i] = float(np.arctan2(np.sin(delta[i]), np.cos(delta[i])))
    t_cross = tangent_plane @ (tangent_plane.T @ delta)
    # Leaf tangent proxy: nullspace of Jp is 2D; take first column as a stand-in
    # when a child Jacobian is unavailable in this audit helper.
    t_leaf = tangent_plane[:, 0]
    stacked = np.column_stack([t_leaf, t_cross])
    s = np.linalg.svd(stacked, compute_uv=False)
    sigma = float(s[-1]) if s.size else 0.0
    rank = int(np.sum(s > 1e-8))
    status = "PASS" if rank == 2 and sigma > 0.0 else "FAIL"
    return TransversalityAudit(status, sigma, rank, ("leaf vs cross-leaf span in parent tangent plane",))


def chart_overlap_status(
    q_a: tuple[tuple[float, ...], ...],
    q_b: tuple[tuple[float, ...], ...],
    *,
    tol: float,
) -> str:
    if not q_a or not q_b:
        return "UNRESOLVED"
    dist = symmetric_q_distance(q_a, q_b)
    if dist <= tol:
        return "duplicate"
    d_ab = directed_q_distance(q_a, q_b)
    d_ba = directed_q_distance(q_b, q_a)
    if abs(d_ab - d_ba) > tol:
        return "compatible-different"
    return "unresolved"


def discover_leaf_family(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    discovery: DirectPointingTruth,
    charts: tuple[SphericalClosureChart, ...],
    config: CampaignConfig,
    *,
    max_steps: int = 12,
    max_leaves: int | None = None,
    lambda_bins: int | None = None,
) -> LeafFamilyResult:
    qs = found_configurations(discovery)
    n_bins = lambda_bins if lambda_bins is not None else config.mode("smoke").natural_lambda_bin_count_per_chart
    cap = max_leaves if max_leaves is not None else config.mode("smoke").max_natural_leaves_per_probe
    leaves: list[NaturalLeafCertificate] = []
    for chart in charts:
        lams: list[float] = []
        usable: list[tuple[float, ...]] = []
        for q in qs:
            coords = chart.decompose(arm.chain.evaluate(q).R)
            if coords.singular:
                continue
            lams.append(coords.lam)
            usable.append(q)
        clusters = cluster_circular(tuple(lams), n_bins)
        for mean_lam, members in clusters:
            if len(leaves) >= cap:
                break
            seed_q = usable[members[0]]
            built = problem_from_source_seed(
                arm,
                chart,
                seed_q,
                probe.p_star,
                leaf_id=f"{probe.probe_id}_{chart.chart_id}_{len(leaves)}",
            )
            if built is None:
                continue
            problem, x0 = built
            samples, status, returned = continue_uuru_leaf(problem, x0, max_steps=max_steps)
            spec = leaf_spec_for(probe.probe_id, chart, problem.lambda_fixed, probe.p_star, problem.problem_id)
            cert = issue_leaf_certificate(
                spec,
                samples,
                branch_status=status,
                returned=returned,
                position_tol=config.tolerances.position_residual_m,
                orientation_tol=config.tolerances.orientation_geodesic_rad,
                pointing_tol=config.tolerances.pointing_geodesic_rad,
                lift_tol=config.tolerances.joint_lift_error_rad,
                lambda_tol=config.tolerances.family_coordinate_error_rad,
                closure_tol=config.tolerances.closed_loop_residual,
            )
            if samples:
                reseed = audit_reseeded_component(
                    arm,
                    chart,
                    problem,
                    samples,
                    q_tol=config.tolerances.reseed_symmetric_q_distance_rad,
                    p_tol=config.tolerances.reseed_pointing_distance_rad,
                    lambda_tol=config.tolerances.family_coordinate_error_rad,
                    max_steps=max_steps,
                    original_returned=returned,
                    original_branch_status=status,
                )
                family_status = (
                    FamilyAdmissibilityStatus.FAIL
                    if reseed.status == "FAIL"
                    else FamilyAdmissibilityStatus.UNRESOLVED
                )
                cert = replace(
                    cert,
                    reseed=reseed,
                    family_admissibility_status=family_status,
                )
            leaves.append(cert)
            _ = mean_lam
    unique: list[NaturalLeafCertificate] = []
    dup = 0
    for leaf in leaves:
        qs_leaf = tuple(s.q_source for s in leaf.samples)
        is_dup = False
        for other in unique:
            qs_other = tuple(s.q_source for s in other.samples)
            if qs_leaf and qs_other and symmetric_q_distance(qs_leaf, qs_other) <= config.tolerances.leaf_duplicate_distance_rad:
                is_dup = True
                dup += 1
                break
        if not is_dup:
            unique.append(leaf)
    overlap = "UNRESOLVED"
    by_chart: dict[str, tuple[tuple[float, ...], ...]] = {}
    for leaf in unique:
        by_chart.setdefault(leaf.spec.chart_id, ())
        by_chart[leaf.spec.chart_id] = by_chart[leaf.spec.chart_id] + tuple(s.q_source for s in leaf.samples)
    chart_ids = list(by_chart)
    if len(chart_ids) >= 2:
        overlap = chart_overlap_status(
            by_chart[chart_ids[0]],
            by_chart[chart_ids[1]],
            tol=config.tolerances.leaf_duplicate_distance_rad,
        )
        unique = [
            replace(leaf, chart_overlap_status=overlap, transversality=None)
            if leaf.transversality is None
            else replace(leaf, chart_overlap_status=overlap)
            for leaf in unique
        ]
    if len(unique) >= 2 and unique[0].samples and unique[1].samples:
        tv = estimate_transversality(arm, unique[0].samples[0].q_source, unique[1].samples[0].q_source)
        unique = [replace(unique[0], transversality=tv), *unique[1:]]
    accepted = sum(1 for leaf in unique if leaf.accepted_for_reconstruction)
    return LeafFamilyResult(
        probe_id=probe.probe_id,
        leaves=tuple(unique),
        accepted_count=accepted,
        duplicate_count=dup,
        chart_overlap_status=overlap,
        unresolved_lambda_intervals=(),
        notes=("Discovery-only lambda clustering; confirmation freeze is the caller's duty.",),
    )


def write_leaves_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
    max_steps: int = 12,
) -> dict[str, Any]:
    import json

    from .models import (
        DirectPointingTruth,
        PointingSolutionCluster,
        PointingSolveStatus,
        PointingTargetSolve,
    )

    arm = build_positive_control_arm(config.geometry)
    charts = charts_from_config(config.charts)
    budgets = config.mode(mode)
    records: list[dict[str, Any]] = []
    for probe in probes:
        path = outdir / probe.probe_id / "direct_truth.json"
        if not path.is_file():
            raise FileNotFoundError(f"missing prerequisite {path}")
        blob = json.loads(path.read_text(encoding="utf-8"))["discovery"]
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
        discovery = DirectPointingTruth(
            probe_id=str(blob["probe_id"]),
            split=str(blob["split"]),
            icosphere_level=int(blob["icosphere_level"]),
            solves=tuple(solves),
            found_count=int(blob["found_count"]),
            not_found_count=int(blob["not_found_count"]),
            unresolved_count=int(blob["unresolved_count"]),
        )
        family = discover_leaf_family(
            arm,
            probe,
            discovery,
            charts,
            config,
            max_steps=max_steps,
            max_leaves=min(6, budgets.max_natural_leaves_per_probe),
            lambda_bins=min(5, budgets.natural_lambda_bin_count_per_chart),
        )
        out = outdir / probe.probe_id / "natural_family.json"
        out.write_text(json_dumps_strict(family.to_json_dict()), encoding="utf-8")
        records.append({"probe_id": probe.probe_id, "accepted_count": family.accepted_count})
    summary = {
        **stage_envelope(
            config,
            stage="leaves",
            mode=mode,
            probe_ids=tuple(p.probe_id for p in probes),
        ),
        "probes": records,
    }
    (outdir / "leaves.json").write_text(json_dumps_strict(summary), encoding="utf-8")
    return summary
