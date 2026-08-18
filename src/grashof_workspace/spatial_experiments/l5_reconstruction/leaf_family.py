"""Natural UURU family discovery, re-seeding, transversality, and chart overlap."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.continuation import wrap_joint_delta
from grashof_workspace.spatial_experiments.implicit_manifold import (
    ambient_distance,
    orthonormal_tangent_basis,
)
from grashof_workspace.spatial_experiments.jacobians import position_jacobian
from grashof_workspace.spatial_experiments.orientation_image import _rotation_geodesic

from .direct_truth import found_configurations
from .models import (
    ACCEPTED_CHILD_STATUSES,
    CampaignConfig,
    ChartOverlapAudit,
    DirectPointingTruth,
    FamilyAdmissibilityStatus,
    FixedPointProbe,
    LeafFamilyResult,
    LeafPairStatus,
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


@dataclass(frozen=True, slots=True)
class LeafWorkRecord:
    certificate: NaturalLeafCertificate
    problem: ClosedUURULeafProblem
    seed_x: tuple[float, ...]
    seed_q: tuple[float, ...]
    chart: SphericalClosureChart
    lambda_fixed: float


SourceQEntry = tuple[str, str, tuple[tuple[float, ...], ...], NDArray[np.floating] | None]


def _signed_wrap(a: float, b: float) -> float:
    return float(np.arctan2(np.sin(a - b), np.cos(a - b)))


def _lambda_gap(recovered_lam: float, alternatives: tuple[tuple[float, float, float], ...], frozen: float) -> float:
    err = abs(_signed_wrap(recovered_lam, frozen))
    for alt in alternatives:
        err = min(err, abs(_signed_wrap(alt[2], frozen)))
    return err


def nearest_sample_pair(
    samples_a: tuple[NaturalLeafSample, ...],
    samples_b: tuple[NaturalLeafSample, ...],
) -> tuple[NaturalLeafSample, NaturalLeafSample] | None:
    if not samples_a or not samples_b:
        return None
    best: tuple[NaturalLeafSample, NaturalLeafSample] | None = None
    best_d = float("inf")
    periodic = (True,) * 5
    for sa in samples_a:
        for sb in samples_b:
            dist = float(ambient_distance(np.asarray(sa.q_source, dtype=float), np.asarray(sb.q_source, dtype=float), periodic))
            if dist < best_d:
                best_d = dist
                best = (sa, sb)
    return best


def circular_neighbor_pairs(leaf_ids: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    n = len(leaf_ids)
    if n < 2:
        return ()
    if n == 2:
        return ((leaf_ids[0], leaf_ids[1]),)
    return tuple((leaf_ids[i], leaf_ids[(i + 1) % n]) for i in range(n))


def classify_source_components(
    q_a: tuple[tuple[float, ...], ...],
    q_b: tuple[tuple[float, ...], ...],
    t_a: NDArray[np.floating] | None,
    t_b: NDArray[np.floating] | None,
    *,
    q_tol: float,
    tangent_tol: float,
) -> LeafPairStatus:
    if not q_a or not q_b:
        return LeafPairStatus.UNRESOLVED
    dist = symmetric_q_distance(q_a, q_b)
    if t_a is None or t_b is None:
        return LeafPairStatus.UNRESOLVED
    try:
        angle = tangent_principal_angle(t_a, t_b)
    except ValueError:
        return LeafPairStatus.UNRESOLVED
    if dist <= q_tol:
        if angle <= tangent_tol:
            return LeafPairStatus.DUPLICATE_SAME_COMPONENT
        return LeafPairStatus.CROSSING_DIFFERENT_TANGENT
    return LeafPairStatus.DISTINCT_COMPATIBLE


def dedup_source_q_leaves(
    entries: tuple[SourceQEntry, ...] | list[SourceQEntry],
    *,
    q_tol: float,
    tangent_tol: float,
) -> tuple[tuple[SourceQEntry, ...], int, tuple[LeafPairStatus, ...]]:
    kept: list[SourceQEntry] = []
    dropped = 0
    labels: list[LeafPairStatus] = []
    for entry in entries:
        chart_id, _leaf_id, qs, tangent = entry
        duplicate = False
        for other in kept:
            if other[0] != chart_id:
                continue
            status = classify_source_components(
                qs, other[2], tangent, other[3], q_tol=q_tol, tangent_tol=tangent_tol
            )
            labels.append(status)
            if status is LeafPairStatus.DUPLICATE_SAME_COMPONENT:
                duplicate = True
                dropped += 1
                break
        if not duplicate:
            kept.append(entry)
    return tuple(kept), dropped, tuple(labels)


def _leaf_tangent(work: LeafWorkRecord, sample: NaturalLeafSample | None = None) -> NDArray[np.floating] | None:
    chosen = sample if sample is not None else (work.certificate.samples[0] if work.certificate.samples else None)
    if chosen is None:
        return None
    try:
        return child_tangent(work.problem, np.asarray(chosen.x, dtype=float))
    except (ValueError, np.linalg.LinAlgError):
        return None


def dedup_work_records(
    works: tuple[LeafWorkRecord, ...] | list[LeafWorkRecord],
    *,
    q_tol: float,
    tangent_tol: float = 0.05,
) -> tuple[tuple[LeafWorkRecord, ...], int, tuple[LeafPairStatus, ...]]:
    entries: list[SourceQEntry] = []
    by_id: dict[str, LeafWorkRecord] = {}
    for work in works:
        leaf_id = work.certificate.spec.leaf_id
        by_id[leaf_id] = work
        qs = tuple(item.q_source for item in work.certificate.samples)
        entries.append((work.chart.chart_id, leaf_id, qs, _leaf_tangent(work)))
    kept_entries, dropped, labels = dedup_source_q_leaves(tuple(entries), q_tol=q_tol, tangent_tol=tangent_tol)
    kept = tuple(by_id[item[1]] for item in kept_entries)
    return kept, dropped, labels


def audit_neighbor_transversality(
    arm: PositiveControlArm,
    work_a: LeafWorkRecord,
    work_b: LeafWorkRecord,
    *,
    sigma_min: float,
) -> TransversalityAudit:
    notes = ["child Jacobian tangent"]
    pair_ids = (
        work_a.certificate.spec.leaf_id,
        work_b.certificate.spec.leaf_id,
        work_a.lambda_fixed,
        work_b.lambda_fixed,
    )
    nearest = nearest_sample_pair(work_a.certificate.samples, work_b.certificate.samples)
    if nearest is None:
        return TransversalityAudit(
            "UNRESOLVED",
            None,
            None,
            ("missing samples for neighbor pair",),
            pair_ids[0],
            pair_ids[1],
            pair_ids[2],
            pair_ids[3],
        )
    sample_a, sample_b = nearest
    try:
        t_s = child_tangent(work_a.problem, np.asarray(sample_a.x, dtype=float))
    except (ValueError, np.linalg.LinAlgError):
        return TransversalityAudit(
            "UNRESOLVED",
            None,
            None,
            ("child tangent unresolved",),
            pair_ids[0],
            pair_ids[1],
            pair_ids[2],
            pair_ids[3],
        )
    delta_lambda = _signed_wrap(work_b.lambda_fixed, work_a.lambda_fixed)
    if abs(delta_lambda) <= 1e-12:
        return TransversalityAudit(
            "UNRESOLVED",
            None,
            None,
            (*notes, "delta_lambda vanished"),
            pair_ids[0],
            pair_ids[1],
            pair_ids[2],
            pair_ids[3],
        )
    delta_q = np.asarray(wrap_joint_delta(sample_b.q_source, sample_a.q_source), dtype=float)
    t_raw = delta_q / delta_lambda
    try:
        tangent_plane = orthonormal_tangent_basis(
            position_jacobian(arm.chain, sample_a.q_source),
            expected_nullity=2,
        )
    except (ValueError, np.linalg.LinAlgError):
        return TransversalityAudit(
            "UNRESOLVED",
            None,
            None,
            (*notes, "parent nullspace unresolved"),
            pair_ids[0],
            pair_ids[1],
            pair_ids[2],
            pair_ids[3],
        )
    t_s_plane = tangent_plane @ (tangent_plane.T @ t_s)
    ts_norm = float(np.linalg.norm(t_s_plane))
    if ts_norm <= 1e-12:
        return TransversalityAudit(
            "UNRESOLVED",
            None,
            None,
            (*notes, "child tangent vanished in the parent plane"),
            pair_ids[0],
            pair_ids[1],
            pair_ids[2],
            pair_ids[3],
        )
    t_s_plane = t_s_plane / ts_norm
    t_proj = tangent_plane @ (tangent_plane.T @ t_raw)
    t_cross = t_proj - float(np.dot(t_proj, t_s_plane)) * t_s_plane
    cross_norm = float(np.linalg.norm(t_cross))
    if cross_norm <= 1e-12:
        return TransversalityAudit(
            "FAIL",
            0.0,
            1,
            (*notes, "cross-leaf direction colinear with child tangent"),
            pair_ids[0],
            pair_ids[1],
            pair_ids[2],
            pair_ids[3],
        )
    stacked = np.column_stack([t_s_plane, t_cross])
    singular = np.linalg.svd(stacked, compute_uv=False)
    sigma = float(singular[-1]) if singular.size else 0.0
    rank = int(np.sum(singular > 1e-8))
    status = "PASS" if rank == 2 and sigma >= sigma_min else "FAIL"
    return TransversalityAudit(
        status,
        sigma,
        rank,
        tuple(notes),
        pair_ids[0],
        pair_ids[1],
        pair_ids[2],
        pair_ids[3],
    )


def audit_all_neighbors(
    arm: PositiveControlArm,
    works: tuple[LeafWorkRecord, ...] | list[LeafWorkRecord],
    *,
    sigma_min: float,
) -> tuple[TransversalityAudit, ...]:
    by_chart: dict[str, list[LeafWorkRecord]] = {}
    for work in works:
        by_chart.setdefault(work.chart.chart_id, []).append(work)
    audits: list[TransversalityAudit] = []
    for group in by_chart.values():
        ordered = sorted(
            group,
            key=lambda item: float(np.arctan2(np.sin(item.lambda_fixed), np.cos(item.lambda_fixed))),
        )
        by_id = {item.certificate.spec.leaf_id: item for item in ordered}
        pairs = circular_neighbor_pairs(tuple(item.certificate.spec.leaf_id for item in ordered))
        for id_a, id_b in pairs:
            audits.append(
                audit_neighbor_transversality(arm, by_id[id_a], by_id[id_b], sigma_min=sigma_min)
            )
    return tuple(audits)


def audit_chart_overlap(
    arm: PositiveControlArm,
    chart_a: SphericalClosureChart,
    chart_b: SphericalClosureChart,
    qs_a: tuple[tuple[float, ...], ...],
    qs_b: tuple[tuple[float, ...], ...],
    pointings_a: tuple[tuple[float, float, float], ...],
    pointings_b: tuple[tuple[float, float, float], ...],
    *,
    lambda_a: float,
    lambda_b: float,
    q_tol: float,
    rotation_tol: float,
    pointing_tol: float,
    lambda_tol: float,
) -> ChartOverlapAudit:
    notes = ["source-Q correspondence first; task-space overlap is not compatibility"]
    if not qs_a or not qs_b:
        return ChartOverlapAudit(status="UNRESOLVED", notes=("empty source-Q set",))
    q_dist = symmetric_q_distance(qs_a, qs_b)
    source_q = bool(q_dist <= q_tol)
    p_dist = max(
        directed_pointing_distance(pointings_a, pointings_b),
        directed_pointing_distance(pointings_b, pointings_a),
    ) if pointings_a and pointings_b else float("inf")
    pointing_ok = bool(p_dist <= pointing_tol) if pointings_a and pointings_b else None
    if not source_q:
        notes.append("disjoint source-Q; pointing overlap does not certify chart copies")
        return ChartOverlapAudit(
            status="UNRESOLVED",
            source_q_correspondence=False,
            recovered_rotation_correspondence=None,
            chart_coordinate_transform=None,
            family_parameter_correspondence=None,
            component_identity=False,
            pointing_set_correspondence=pointing_ok,
            notes=tuple(notes),
        )
    rotation_errors: list[float] = []
    transform_errors: list[float] = []
    lambda_ok = True
    singular = False
    first = True
    for q in qs_a:
        state = arm.chain.evaluate(q)
        r_src = np.asarray(state.R, dtype=float)
        ca = chart_a.decompose(r_src)
        cb = chart_b.decompose(r_src)
        if ca.singular or cb.singular:
            singular = True
            continue
        ra = chart_a.compose(ca.alpha, ca.beta, ca.lam)
        rb = chart_b.compose(cb.alpha, cb.beta, cb.lam)
        rotation_errors.append(max(_rotation_geodesic(r_src, ra), _rotation_geodesic(r_src, rb)))
        transform_errors.append(_rotation_geodesic(ra, rb))
        if _lambda_gap(ca.lam, ca.alternatives, lambda_a) > lambda_tol:
            lambda_ok = False
        if first:
            if _lambda_gap(cb.lam, cb.alternatives, lambda_b) > lambda_tol:
                lambda_ok = False
            first = False
    if not rotation_errors:
        return ChartOverlapAudit(
            status="UNRESOLVED",
            source_q_correspondence=True,
            component_identity=True,
            pointing_set_correspondence=pointing_ok,
            notes=(*notes, "chart-singular overlap samples"),
        )
    rotation_ok = max(rotation_errors) <= rotation_tol
    transform_ok = max(transform_errors) <= rotation_tol
    if singular:
        notes.append("some overlap samples were chart-singular and skipped")
    if rotation_ok and transform_ok and lambda_ok and pointing_ok:
        status = "COMPATIBLE"
    elif not rotation_ok or not transform_ok or pointing_ok is False:
        status = "INCOMPATIBLE"
    else:
        status = "UNRESOLVED"
    return ChartOverlapAudit(
        status=status,
        source_q_correspondence=True,
        recovered_rotation_correspondence=rotation_ok,
        chart_coordinate_transform=transform_ok,
        family_parameter_correspondence=lambda_ok,
        component_identity=True,
        pointing_set_correspondence=pointing_ok,
        notes=tuple(notes),
    )


def _family_chart_overlap(
    arm: PositiveControlArm,
    works: tuple[LeafWorkRecord, ...],
    *,
    q_tol: float,
    rotation_tol: float,
    pointing_tol: float,
    lambda_tol: float,
) -> ChartOverlapAudit:
    by_chart: dict[str, list[LeafWorkRecord]] = {}
    for work in works:
        by_chart.setdefault(work.chart.chart_id, []).append(work)
    chart_ids = list(by_chart)
    if len(chart_ids) < 2:
        return ChartOverlapAudit(status="UNRESOLVED", notes=("fewer than two charts",))
    audits: list[ChartOverlapAudit] = []
    for i, id_a in enumerate(chart_ids):
        for id_b in chart_ids[i + 1 :]:
            group_a = by_chart[id_a]
            group_b = by_chart[id_b]
            qs_a = tuple(sample.q_source for work in group_a for sample in work.certificate.samples)
            qs_b = tuple(sample.q_source for work in group_b for sample in work.certificate.samples)
            p_a = tuple(sample.pointing for work in group_a for sample in work.certificate.samples)
            p_b = tuple(sample.pointing for work in group_b for sample in work.certificate.samples)
            audits.append(
                audit_chart_overlap(
                    arm,
                    group_a[0].chart,
                    group_b[0].chart,
                    qs_a,
                    qs_b,
                    p_a,
                    p_b,
                    lambda_a=group_a[0].lambda_fixed,
                    lambda_b=group_b[0].lambda_fixed,
                    q_tol=q_tol,
                    rotation_tol=rotation_tol,
                    pointing_tol=pointing_tol,
                    lambda_tol=lambda_tol,
                )
            )
    if not audits:
        return ChartOverlapAudit(status="UNRESOLVED", notes=("no cross-chart pairs",))
    incompatible = tuple(item for item in audits if item.status == "INCOMPATIBLE")
    if incompatible:
        return incompatible[0]
    compatible = tuple(item for item in audits if item.status == "COMPATIBLE")
    if compatible:
        return compatible[0]
    return audits[0]


def recompute_family_acceptance(
    leaves: tuple[NaturalLeafCertificate, ...],
    neighbor_audits: tuple[TransversalityAudit, ...],
    overlap: ChartOverlapAudit,
) -> tuple[NaturalLeafCertificate, ...]:
    neighbor_statuses = {item.status for item in neighbor_audits}
    neighbor_fail = "FAIL" in neighbor_statuses
    neighbor_all_pass = bool(neighbor_audits) and neighbor_statuses <= {"PASS"}
    overlap_fail = overlap.status == "INCOMPATIBLE"
    overlap_ok = overlap.status in {"COMPATIBLE", "UNRESOLVED"}
    updated: list[NaturalLeafCertificate] = []
    for leaf in leaves:
        reseed_status = None if leaf.reseed is None else leaf.reseed.status
        if reseed_status == "FAIL" or neighbor_fail or overlap_fail:
            family = FamilyAdmissibilityStatus.FAIL
        elif reseed_status == "PASS" and neighbor_all_pass and overlap_ok:
            family = FamilyAdmissibilityStatus.PASS
        else:
            family = FamilyAdmissibilityStatus.UNRESOLVED
        component_ok = leaf.leaf_component_status in ACCEPTED_CHILD_STATUSES
        accepted = bool(component_ok and family is FamilyAdmissibilityStatus.PASS and neighbor_all_pass)
        stamp = next(
            (
                item
                for item in neighbor_audits
                if item.status == "FAIL" and leaf.spec.leaf_id in {item.leaf_id_a, item.leaf_id_b}
            ),
            next(
                (
                    item
                    for item in neighbor_audits
                    if leaf.spec.leaf_id in {item.leaf_id_a, item.leaf_id_b}
                ),
                None,
            ),
        )
        updated.append(
            replace(
                leaf,
                family_admissibility_status=family,
                accepted_for_reconstruction=accepted,
                transversality=stamp if stamp is not None else leaf.transversality,
                chart_overlap_status=overlap.status,
            )
        )
    return tuple(updated)


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
    works: list[LeafWorkRecord] = []
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
            if len(works) >= cap:
                break
            seed_q = usable[members[0]]
            built = problem_from_source_seed(
                arm,
                chart,
                seed_q,
                probe.p_star,
                leaf_id=f"{probe.probe_id}_{chart.chart_id}_{len(works)}",
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
            works.append(
                LeafWorkRecord(
                    certificate=cert,
                    problem=problem,
                    seed_x=tuple(float(v) for v in x0),
                    seed_q=tuple(float(v) for v in problem.physical_q(x0)),
                    chart=chart,
                    lambda_fixed=float(problem.lambda_fixed),
                )
            )
            _ = mean_lam
    unique_works, dup, labels = dedup_work_records(
        works,
        q_tol=config.tolerances.leaf_duplicate_distance_rad,
    )
    neighbor_audits = audit_all_neighbors(
        arm,
        unique_works,
        sigma_min=config.tolerances.minimum_transversality_sigma,
    )
    overlap = _family_chart_overlap(
        arm,
        unique_works,
        q_tol=config.tolerances.leaf_duplicate_distance_rad,
        rotation_tol=config.tolerances.orientation_geodesic_rad,
        pointing_tol=config.tolerances.pointing_geodesic_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
    )
    leaves = recompute_family_acceptance(
        tuple(item.certificate for item in unique_works),
        neighbor_audits,
        overlap,
    )
    accepted = sum(1 for leaf in leaves if leaf.accepted_for_reconstruction)
    return LeafFamilyResult(
        probe_id=probe.probe_id,
        leaves=leaves,
        accepted_count=accepted,
        duplicate_count=dup,
        chart_overlap_status=overlap.status,
        unresolved_lambda_intervals=(),
        notes=(
            "Discovery-only lambda clustering; confirmation freeze is the caller's duty.",
            "Neighbor transversality uses child Jacobians; chart overlap is source-Q correspondence.",
        ),
        neighbor_audits=neighbor_audits,
        chart_overlap=overlap,
        duplicate_classifications=tuple(item.value for item in labels),
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
