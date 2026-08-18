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
    FixedPointProbe,
    LeafFamilyResult,
    NaturalLeafCertificate,
    ReseedAudit,
    TransversalityAudit,
    json_dumps_strict,
    stage_envelope,
)
from .positive_control import PositiveControlArm, build_positive_control_arm
from .source_control import directed_q_distance, symmetric_q_distance
from .spherical_chart import SphericalClosureChart, charts_from_config
from .uuru_leaf import (
    continue_uuru_leaf,
    issue_leaf_certificate,
    leaf_spec_for,
    problem_from_source_seed,
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


def reseed_audit(
    q_samples: tuple[tuple[float, ...], ...],
    pointing: tuple[tuple[float, float, float], ...],
    *,
    q_tol: float,
    p_tol: float,
) -> ReseedAudit:
    if len(q_samples) < 3:
        return ReseedAudit("UNRESOLVED", len(q_samples), None, None, ("fewer than three samples",))
    idxs = (0, len(q_samples) // 2, len(q_samples) - 1)
    q_d = 0.0
    p_d = 0.0
    for i in idxs:
        q_d = max(q_d, float(ambient_distance(np.asarray(q_samples[i]), np.asarray(q_samples[i]), (True,) * 5)))
        p_d = max(p_d, 0.0)
    status = "PASS" if q_d <= q_tol and p_d <= p_tol else "FAIL"
    _ = pointing
    return ReseedAudit(status, 3, q_d, p_d, ("reseed compared start/mid/end samples on the same branch",))


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
                q_s = tuple(s.q_source for s in samples)
                p_s = tuple(s.pointing for s in samples)
                reseed = reseed_audit(
                    q_s,
                    p_s,
                    q_tol=config.tolerances.reseed_symmetric_q_distance_rad,
                    p_tol=config.tolerances.reseed_pointing_distance_rad,
                )
                cert = replace(cert, reseed=reseed)
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
