"""Natural UURU family discovery, re-seeding, transversality, and chart overlap."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
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

from .artifacts import finalize_stage
from .direct_truth import found_configurations
from .models import (
    ACCEPTED_CHILD_STATUSES,
    CampaignConfig,
    ChartAtlasPolicy,
    ChartOverlapAudit,
    DirectPointingTruth,
    FamilyAdmissibilityStatus,
    FamilyIntervalRecord,
    FixedPointProbe,
    IntervalStatus,
    LeafFamilyResult,
    LeafPairStatus,
    NaturalLeafCertificate,
    NaturalLeafSample,
    ReseedAttempt,
    ReseedAudit,
    ReseedDisposition,
    ReseedScope,
    TransversalityAudit,
    json_dumps_strict,
    resolve_stage_budgets,
    stage_envelope,
)
from .positive_control import PositiveControlArm, build_positive_control_arm
from .source_control import symmetric_q_distance
from .sphere_grid import pointing_geodesic
from .spherical_chart import SphericalClosureChart, canonical_chart, charts_from_config
from .uuru_leaf import (
    ClosedUURULeafProblem,
    child_tangent,
    continue_uuru_leaf,
    issue_leaf_certificate,
    leaf_spec_for,
    problem_from_source_seed,
    tangent_principal_angle,
)

BLOCKING_INTERVAL_STATUSES = frozenset(
    {
        IntervalStatus.UNSAMPLED,
        IntervalStatus.UNRESOLVED,
        IntervalStatus.CRITICAL_OR_BOUNDARY,
    }
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


def symmetric_pointing_distance(
    a: tuple[tuple[float, float, float], ...],
    b: tuple[tuple[float, float, float], ...],
) -> float:
    return max(directed_pointing_distance(a, b), directed_pointing_distance(b, a))


def classify_reseed_attempt(
    *,
    lambda_ok: bool,
    seed_q_ok: bool,
    seed_pointing_ok: bool,
    tangent_ok: bool,
    tangent_unresolved: bool = False,
    singular: bool = False,
    rebuild_failed: bool = False,
    budget_truncated: bool = False,
    original_returned: bool | None,
    reseeded_returned: bool,
    original_branch_status: str | None,
    reseeded_branch_status: str,
    symmetric_q: float | None,
    symmetric_p: float | None,
    q_tol: float,
    p_tol: float,
) -> tuple[ReseedScope, ReseedDisposition, bool | None, bool | None, bool | None, tuple[str, ...]]:
    """Local seed consistency vs complete-component identity."""

    notes: list[str] = []
    returned_match = None if original_returned is None else reseeded_returned == original_returned
    branch_match = None if original_branch_status is None else reseeded_branch_status == original_branch_status
    if singular:
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.UNRESOLVED,
            returned_match,
            branch_match,
            None,
            ("chart-singular reseed",),
        )
    if rebuild_failed:
        if not lambda_ok:
            return (
                ReseedScope.LOCAL,
                ReseedDisposition.FAIL,
                returned_match,
                branch_match,
                False,
                ("rebuild returned None", "forced lambda mismatch"),
            )
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.UNRESOLVED,
            returned_match,
            branch_match,
            False,
            ("rebuild returned None",),
        )
    if budget_truncated:
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.UNRESOLVED,
            returned_match,
            branch_match,
            False,
            ("truncated continuation budget",),
        )
    if not lambda_ok:
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.FAIL,
            returned_match,
            branch_match,
            False,
            ("forced lambda mismatch",),
        )
    if tangent_unresolved:
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.UNRESOLVED,
            returned_match,
            branch_match,
            False,
            ("child tangent unresolved",),
        )
    local_pass = lambda_ok and seed_q_ok and seed_pointing_ok and tangent_ok
    if not local_pass:
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.FAIL,
            returned_match,
            branch_match,
            False,
            ("local seed or tangent mismatch",),
        )
    notes.append("local seed reconstruction and child tangent")
    open_or_unknown = original_returned is not True or not reseeded_returned
    symmetric_q_ok = symmetric_q is not None and symmetric_q <= q_tol
    symmetric_p_ok = symmetric_p is not None and symmetric_p <= p_tol
    identity = bool(
        returned_match is True
        and branch_match is True
        and original_returned is True
        and reseeded_returned
        and symmetric_q_ok
        and symmetric_p_ok
    )
    if open_or_unknown:
        notes.append("open or unknown return; component identity forbidden")
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.LOCAL_PASS,
            returned_match,
            branch_match,
            False,
            tuple(notes),
        )
    if not (symmetric_q_ok and symmetric_p_ok and returned_match is True and branch_match is True and identity):
        notes.append("local pass without symmetric branch-set identity")
        return (
            ReseedScope.LOCAL,
            ReseedDisposition.LOCAL_PASS,
            returned_match,
            branch_match,
            False,
            tuple(notes),
        )
    notes.append("symmetric branch-set and circuit identity")
    return (
        ReseedScope.COMPONENT,
        ReseedDisposition.COMPONENT_PASS,
        returned_match,
        branch_match,
        True,
        tuple(notes),
    )


def aggregate_reseed_disposition(attempts: tuple[ReseedAttempt, ...] | list[ReseedAttempt]) -> ReseedDisposition:
    if not attempts:
        return ReseedDisposition.UNRESOLVED
    statuses = {item.disposition for item in attempts}
    if ReseedDisposition.FAIL in statuses:
        return ReseedDisposition.FAIL
    if ReseedDisposition.UNRESOLVED in statuses:
        return ReseedDisposition.UNRESOLVED
    if statuses == {ReseedDisposition.COMPONENT_PASS}:
        return ReseedDisposition.COMPONENT_PASS
    return ReseedDisposition.LOCAL_PASS


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
    original_q = tuple(item.q_source for item in original_samples)
    original_p = tuple(item.pointing for item in original_samples)
    if len(original_samples) < 3:
        return ReseedAudit(
            disposition=ReseedDisposition.UNRESOLVED,
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
            scope, disposition, returned_match, branch_match, identity, extra = classify_reseed_attempt(
                lambda_ok=lambda_shift <= lambda_tol,
                seed_q_ok=False,
                seed_pointing_ok=False,
                tangent_ok=False,
                singular=True,
                original_returned=original_returned,
                reseeded_returned=False,
                original_branch_status=original_branch_status,
                reseeded_branch_status="unresolved",
                symmetric_q=None,
                symmetric_p=None,
                q_tol=q_tol,
                p_tol=p_tol,
            )
            attempts.append(
                ReseedAttempt(
                    reseed_id=label,
                    seed_s=sample.s,
                    local_seed_q_error=None,
                    local_seed_pointing_error=None,
                    local_lambda_error=lambda_shift,
                    local_tangent_error=None,
                    symmetric_branch_q_distance=None,
                    symmetric_branch_pointing_distance=None,
                    return_status_match=returned_match,
                    branch_status_match=branch_match,
                    circuit_or_component_match=identity,
                    scope=scope,
                    disposition=disposition,
                    notes=extra,
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
            scope, disposition, returned_match, branch_match, identity, extra = classify_reseed_attempt(
                lambda_ok=lambda_shift <= lambda_tol,
                seed_q_ok=False,
                seed_pointing_ok=False,
                tangent_ok=False,
                rebuild_failed=True,
                original_returned=original_returned,
                reseeded_returned=False,
                original_branch_status=original_branch_status,
                reseeded_branch_status="unresolved",
                symmetric_q=None,
                symmetric_p=None,
                q_tol=q_tol,
                p_tol=p_tol,
            )
            attempts.append(
                ReseedAttempt(
                    reseed_id=label,
                    seed_s=sample.s,
                    local_seed_q_error=None,
                    local_seed_pointing_error=None,
                    local_lambda_error=lambda_shift,
                    local_tangent_error=None,
                    symmetric_branch_q_distance=None,
                    symmetric_branch_pointing_distance=None,
                    return_status_match=returned_match,
                    branch_status_match=branch_match,
                    circuit_or_component_match=identity,
                    scope=scope,
                    disposition=disposition,
                    notes=(*notes, *extra),
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
        reseeded_q = tuple(item.q_source for item in reseeded_samples)
        reseeded_p = tuple(item.pointing for item in reseeded_samples)
        q_sym = symmetric_q_distance(original_q, reseeded_q) if reseeded_q else None
        p_sym = symmetric_pointing_distance(original_p, reseeded_p) if reseeded_p else None
        tangent_err: float | None = None
        tangent_unresolved = False
        try:
            t0 = child_tangent(original_problem, np.asarray(sample.x, dtype=float))
            t1 = child_tangent(problem_i, x_i)
            tangent_err = tangent_principal_angle(t0, t1)
        except (ValueError, np.linalg.LinAlgError):
            tangent_unresolved = True
            notes.append("child tangent unresolved")
        lam_err = _wrap_angle(problem_i.lambda_fixed, original_problem.lambda_fixed)
        scope, disposition, returned_match, branch_match, identity, extra = classify_reseed_attempt(
            lambda_ok=lam_err <= lambda_tol,
            seed_q_ok=seed_q_err <= q_tol,
            seed_pointing_ok=seed_p_err <= p_tol,
            tangent_ok=tangent_err is not None and tangent_err <= tangent_tol,
            tangent_unresolved=tangent_unresolved,
            budget_truncated=budget_truncated,
            original_returned=original_returned,
            reseeded_returned=returned,
            original_branch_status=original_branch_status,
            reseeded_branch_status=branch_status,
            symmetric_q=q_sym,
            symmetric_p=p_sym,
            q_tol=q_tol,
            p_tol=p_tol,
        )
        attempts.append(
            ReseedAttempt(
                reseed_id=label,
                seed_s=sample.s,
                local_seed_q_error=seed_q_err,
                local_seed_pointing_error=seed_p_err,
                local_lambda_error=lam_err,
                local_tangent_error=tangent_err,
                symmetric_branch_q_distance=q_sym,
                symmetric_branch_pointing_distance=p_sym,
                return_status_match=returned_match,
                branch_status_match=branch_match,
                circuit_or_component_match=identity,
                scope=scope,
                disposition=disposition,
                notes=(*notes, *extra),
            )
        )
    agg = aggregate_reseed_disposition(attempts)
    q_vals = [item.symmetric_branch_q_distance for item in attempts if item.symmetric_branch_q_distance is not None]
    p_vals = [
        item.symmetric_branch_pointing_distance
        for item in attempts
        if item.symmetric_branch_pointing_distance is not None
    ]
    t_vals = [item.local_tangent_error for item in attempts if item.local_tangent_error is not None]
    seed_q_vals = [item.local_seed_q_error for item in attempts if item.local_seed_q_error is not None]
    seed_p_vals = [item.local_seed_pointing_error for item in attempts if item.local_seed_pointing_error is not None]
    identities = [item.circuit_or_component_match for item in attempts]
    return ReseedAudit(
        disposition=agg,
        n_reseeds=len(attempts),
        max_symmetric_q_distance_rad=None if not q_vals else max(q_vals),
        max_pointing_distance_rad=None if not p_vals else max(p_vals),
        notes=(
            "independent start/mid/end rebuilds; seed errors are local; symmetric distances are branch-set",
        ),
        attempts=tuple(attempts),
        max_tangent_error=None if not t_vals else max(t_vals),
        all_component_ids_match=all(identities) if identities else None,
        max_local_seed_q_error=None if not seed_q_vals else max(seed_q_vals),
        max_local_seed_pointing_error=None if not seed_p_vals else max(seed_p_vals),
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


def _stamp_chart_overlap(
    audit: ChartOverlapAudit,
    *,
    chart_id_a: str | None,
    chart_id_b: str | None,
    required: bool,
    claim_scope: str,
) -> ChartOverlapAudit:
    return replace(
        audit,
        chart_id_a=chart_id_a,
        chart_id_b=chart_id_b,
        required=required,
        claim_scope=claim_scope,
    )


def summarize_chart_overlap(audits: tuple[ChartOverlapAudit, ...] | list[ChartOverlapAudit]) -> ChartOverlapAudit:
    items = tuple(audits)
    required = tuple(item for item in items if item.required)
    if not required:
        if items:
            return items[0]
        return ChartOverlapAudit(
            status="UNRESOLVED",
            required=False,
            claim_scope="declared_chart_domain_only",
            notes=("no required chart pairs",),
        )
    incompatible = tuple(item for item in required if item.status == "INCOMPATIBLE")
    if incompatible:
        return incompatible[0]
    unresolved = tuple(item for item in required if item.status == "UNRESOLVED")
    if unresolved:
        return unresolved[0]
    compatible = tuple(item for item in required if item.status == "COMPATIBLE")
    if compatible:
        return compatible[0]
    return required[0]


def _family_chart_overlap(
    arm: PositiveControlArm,
    works: tuple[LeafWorkRecord, ...],
    *,
    q_tol: float,
    rotation_tol: float,
    pointing_tol: float,
    lambda_tol: float,
) -> tuple[ChartOverlapAudit, ...]:
    by_chart: dict[str, list[LeafWorkRecord]] = {}
    for work in works:
        by_chart.setdefault(work.chart.chart_id, []).append(work)
    chart_ids = list(by_chart)
    if len(chart_ids) < 2:
        return (
            ChartOverlapAudit(
                status="UNRESOLVED",
                required=False,
                claim_scope="declared_chart_domain_only",
                notes=("fewer than two charts",),
            ),
        )
    audits: list[ChartOverlapAudit] = []
    for i, id_a in enumerate(chart_ids):
        for id_b in chart_ids[i + 1 :]:
            group_a = by_chart[id_a]
            group_b = by_chart[id_b]
            qs_a = tuple(sample.q_source for work in group_a for sample in work.certificate.samples)
            qs_b = tuple(sample.q_source for work in group_b for sample in work.certificate.samples)
            p_a = tuple(sample.pointing for work in group_a for sample in work.certificate.samples)
            p_b = tuple(sample.pointing for work in group_b for sample in work.certificate.samples)
            raw = audit_chart_overlap(
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
            audits.append(
                _stamp_chart_overlap(
                    raw,
                    chart_id_a=id_a,
                    chart_id_b=id_b,
                    required=True,
                    claim_scope="multi_chart_declared_domain",
                )
            )
    if not audits:
        return (
            ChartOverlapAudit(
                status="UNRESOLVED",
                required=False,
                claim_scope="declared_chart_domain_only",
                notes=("no cross-chart pairs",),
            ),
        )
    return tuple(audits)


def neighbor_audits_by_leaf(
    audits: tuple[TransversalityAudit, ...] | list[TransversalityAudit],
) -> dict[str, list[TransversalityAudit]]:
    out: dict[str, list[TransversalityAudit]] = {}
    for item in audits:
        for leaf_id in (item.leaf_id_a, item.leaf_id_b):
            if leaf_id:
                out.setdefault(leaf_id, []).append(item)
    return out


def chart_audits_by_leaf(
    leaves: tuple[NaturalLeafCertificate, ...],
    audits: tuple[ChartOverlapAudit, ...] | list[ChartOverlapAudit],
) -> dict[str, list[ChartOverlapAudit]]:
    out: dict[str, list[ChartOverlapAudit]] = {leaf.spec.leaf_id: [] for leaf in leaves}
    for leaf in leaves:
        chart_id = leaf.spec.chart_id
        for audit in audits:
            ids = {audit.chart_id_a, audit.chart_id_b} - {None}
            if not ids or chart_id in ids:
                out[leaf.spec.leaf_id].append(audit)
    return out


def _as_overlap_audits(
    overlap: ChartOverlapAudit | tuple[ChartOverlapAudit, ...] | list[ChartOverlapAudit],
) -> tuple[ChartOverlapAudit, ...]:
    if isinstance(overlap, ChartOverlapAudit):
        return (overlap,)
    return tuple(overlap)


def recompute_family_acceptance(
    leaves: tuple[NaturalLeafCertificate, ...],
    neighbor_audits: tuple[TransversalityAudit, ...],
    overlap: ChartOverlapAudit | tuple[ChartOverlapAudit, ...] | list[ChartOverlapAudit],
) -> tuple[NaturalLeafCertificate, ...]:
    overlap_audits = _as_overlap_audits(overlap)
    neighbors = neighbor_audits_by_leaf(neighbor_audits)
    charts = chart_audits_by_leaf(leaves, overlap_audits)
    updated: list[NaturalLeafCertificate] = []
    for leaf in leaves:
        leaf_id = leaf.spec.leaf_id
        incident_neighbors = neighbors.get(leaf_id, [])
        incident_charts = charts.get(leaf_id, [])
        reseed_disp = None if leaf.reseed is None else leaf.reseed.disposition
        reseed_ok = reseed_disp is ReseedDisposition.COMPONENT_PASS
        neighbor_fail = any(item.status == "FAIL" for item in incident_neighbors)
        neighbor_ok = bool(incident_neighbors) and all(item.status == "PASS" for item in incident_neighbors)
        required_charts = [item for item in incident_charts if item.required]
        chart_fail = any(item.status == "INCOMPATIBLE" for item in required_charts)
        chart_ok = all(item.status == "COMPATIBLE" for item in required_charts)
        if reseed_disp is ReseedDisposition.FAIL or neighbor_fail or chart_fail:
            family = FamilyAdmissibilityStatus.FAIL
        elif reseed_ok and neighbor_ok and chart_ok:
            family = FamilyAdmissibilityStatus.PASS
        else:
            family = FamilyAdmissibilityStatus.UNRESOLVED
        component_ok = leaf.leaf_component_status in ACCEPTED_CHILD_STATUSES
        accepted = bool(component_ok and reseed_ok and neighbor_ok and chart_ok)
        stamp = next(
            (item for item in incident_neighbors if item.status == "FAIL"),
            next(iter(incident_neighbors), None),
        )
        summary = summarize_chart_overlap(incident_charts if incident_charts else overlap_audits)
        updated.append(
            replace(
                leaf,
                family_admissibility_status=family,
                accepted_for_reconstruction=accepted,
                transversality=stamp if stamp is not None else leaf.transversality,
                chart_overlap_status=summary.status,
            )
        )
    return tuple(updated)


def _lambda_bin_index(value: float, n_bins: int) -> int:
    wrapped = float(np.arctan2(np.sin(value), np.cos(value)))
    return int(np.floor((wrapped + np.pi) / (2.0 * np.pi) * n_bins)) % n_bins


def circular_lambda_bin_edges(n_bins: int) -> tuple[tuple[float, float], ...]:
    if n_bins <= 0:
        return ()
    width = 2.0 * np.pi / n_bins
    edges: list[tuple[float, float]] = []
    for i in range(n_bins):
        lo = -np.pi + i * width
        hi = np.pi if i + 1 == n_bins else -np.pi + (i + 1) * width
        edges.append((float(lo), float(hi)))
    return tuple(edges)


def _as_interval_status(value: IntervalStatus | str) -> IntervalStatus:
    if isinstance(value, IntervalStatus):
        return value
    return IntervalStatus(str(value))


def classify_interval_status(
    *,
    required: bool,
    members: tuple[NaturalLeafCertificate, ...],
    budget_exhausted: bool,
    critical: tuple[float, ...],
) -> IntervalStatus:
    if members:
        if any(leaf.accepted_for_reconstruction for leaf in members):
            return IntervalStatus.SAMPLED_ADMISSIBLE
        if critical:
            return IntervalStatus.CRITICAL_OR_BOUNDARY
        if any(leaf.leaf_component_status in ACCEPTED_CHILD_STATUSES for leaf in members):
            return IntervalStatus.SAMPLED_COMPONENT
        return IntervalStatus.SAMPLED_LOCAL
    if not required:
        return IntervalStatus.NOT_REQUIRED
    if budget_exhausted:
        return IntervalStatus.UNRESOLVED
    return IntervalStatus.UNSAMPLED


def audit_family_intervals(
    leaves: tuple[NaturalLeafCertificate, ...],
    *,
    n_bins: int,
    chart_ids: tuple[str, ...],
    occupied: set[tuple[str, int]] | frozenset[tuple[str, int]] | None = None,
    seed_counts: Mapping[tuple[str, int], int] | None = None,
    exhausted: set[tuple[str, int]] | frozenset[tuple[str, int]] | None = None,
    duplicate_groups: tuple[tuple[str, ...], ...] = (),
) -> tuple[FamilyIntervalRecord, ...]:
    """Initialize every configured chart×bin, then overlay sampled leaves.

    Occupancy comes from canonical chart assignment, never from discovered
    leaves alone. ``SAMPLED_ADMISSIBLE`` is not ``COMPLETE``.
    """

    edges = circular_lambda_bin_edges(n_bins)
    occupied_keys = frozenset(occupied or ())
    exhausted_keys = frozenset(exhausted or ())
    counts = dict(seed_counts or {})
    records: list[FamilyIntervalRecord] = []
    for chart_id in chart_ids:
        chart_leaves = tuple(leaf for leaf in leaves if leaf.spec.chart_id == chart_id)
        for i, (lo, hi) in enumerate(edges):
            key = (chart_id, i)
            members = tuple(
                leaf
                for leaf in chart_leaves
                if _lambda_bin_index(leaf.spec.lambda_fixed, n_bins) == i
            )
            required = key in occupied_keys
            accepted = tuple(leaf.spec.leaf_id for leaf in members if leaf.accepted_for_reconstruction)
            rejected = tuple(leaf.spec.leaf_id for leaf in members if leaf.leaf_component_status == "REJECTED")
            unresolved = tuple(
                leaf.spec.leaf_id
                for leaf in members
                if leaf.spec.leaf_id not in accepted and leaf.spec.leaf_id not in rejected
            )
            sampled = tuple(leaf.spec.lambda_fixed for leaf in members)
            critical = tuple(
                leaf.spec.lambda_fixed
                for leaf in members
                if any(sample.chart_singularity for sample in leaf.samples)
            )
            budget_exhausted = key in exhausted_keys
            status = classify_interval_status(
                required=required,
                members=members,
                budget_exhausted=budget_exhausted,
                critical=critical,
            )
            component_counts = dict(Counter(leaf.leaf_component_status for leaf in members))
            admissibility_counts = dict(
                Counter(leaf.family_admissibility_status.value for leaf in members)
            )
            records.append(
                FamilyIntervalRecord(
                    chart_id=chart_id,
                    lambda_interval=(lo, hi),
                    sampled_lambda_values=sampled,
                    accepted_leaf_ids=accepted,
                    rejected_leaf_ids=rejected,
                    unresolved_leaf_ids=unresolved,
                    duplicate_groups=duplicate_groups,
                    critical_values=critical,
                    birth_death_merge_events=(),
                    interval_status=status,
                    required=required,
                    seed_count=int(counts.get(key, 0)),
                    leaf_count=len(members),
                    component_status_counts=component_counts,
                    admissibility_status_counts=admissibility_counts,
                    budget_exhausted=budget_exhausted,
                )
            )
    return tuple(records)


def interval_coverage_ok(records: tuple[FamilyIntervalRecord, ...]) -> bool:
    return not any(
        item.required and _as_interval_status(item.interval_status) in BLOCKING_INTERVAL_STATUSES
        for item in records
    )


def apply_interval_coverage_gate(
    leaves: tuple[NaturalLeafCertificate, ...],
    records: tuple[FamilyIntervalRecord, ...],
) -> tuple[tuple[NaturalLeafCertificate, ...], tuple[tuple[float, float], ...]]:
    """Block the natural union when a required interval is missing or unresolved.

    Does not rewrite honest ``SAMPLED_*`` rows. ``NOT_REQUIRED`` never blocks.
    """

    gaps = tuple(
        item.lambda_interval
        for item in records
        if item.required and _as_interval_status(item.interval_status) in BLOCKING_INTERVAL_STATUSES
    )
    if gaps:
        leaves = tuple(replace(leaf, accepted_for_reconstruction=False) for leaf in leaves)
    return leaves, gaps


def _canonical_occupancy(
    arm: PositiveControlArm,
    charts: tuple[SphericalClosureChart, ...],
    qs: tuple[tuple[float, ...], ...],
    *,
    n_bins: int,
    policy: ChartAtlasPolicy,
) -> dict[tuple[str, int], list[tuple[tuple[float, ...], float]]]:
    occupied: dict[tuple[str, int], list[tuple[tuple[float, ...], float]]] = {}
    by_id = {chart.chart_id: chart for chart in charts}
    for q in qs:
        rotation = arm.chain.evaluate(q).R
        chart_id = canonical_chart(charts, rotation, policy=policy)
        if chart_id is None:
            continue
        coords = by_id[chart_id].decompose(rotation)
        key = (chart_id, _lambda_bin_index(coords.lam, n_bins))
        occupied.setdefault(key, []).append((q, float(coords.lam)))
    return occupied


def discover_leaf_family(
    arm: PositiveControlArm,
    probe: FixedPointProbe,
    discovery: DirectPointingTruth,
    charts: tuple[SphericalClosureChart, ...],
    config: CampaignConfig,
    *,
    max_steps: int = 12,
    max_leaves: int | None = None,
    max_leaves_per_chart: int | None = None,
    lambda_bins: int | None = None,
    reseed_count: int | None = None,
) -> LeafFamilyResult:
    qs = found_configurations(discovery)
    smoke = config.mode("smoke")
    n_bins = lambda_bins if lambda_bins is not None else smoke.natural_lambda_bin_count_per_chart
    per_chart_cap = (
        max_leaves_per_chart if max_leaves_per_chart is not None else smoke.max_natural_leaves_per_chart
    )
    total_cap = max_leaves if max_leaves is not None else smoke.max_natural_leaves_per_probe
    n_reseed = reseed_count if reseed_count is not None else smoke.reseed_samples_per_leaf
    policy = config.chart_atlas_policy
    occupancy = _canonical_occupancy(arm, charts, qs, n_bins=n_bins, policy=policy)
    seed_counts = {key: len(seeds) for key, seeds in occupancy.items()}
    exhausted: set[tuple[str, int]] = set()
    works: list[LeafWorkRecord] = []
    for chart in charts:
        chart_count = 0
        for bin_index in range(n_bins):
            key = (chart.chart_id, bin_index)
            seeds = occupancy.get(key)
            if not seeds:
                continue
            if chart_count >= per_chart_cap or len(works) >= total_cap:
                exhausted.add(key)
                continue
            built = None
            for candidate_q, _lam in seeds:
                built = problem_from_source_seed(
                    arm,
                    chart,
                    candidate_q,
                    probe.p_star,
                    leaf_id=f"{probe.probe_id}_{chart.chart_id}_{len(works)}",
                )
                if built is not None:
                    break
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
            cert = replace(cert, responsible_chart_id=chart.chart_id)
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
                    reseed_count=n_reseed,
                )
                family_status = (
                    FamilyAdmissibilityStatus.FAIL
                    if reseed.disposition is ReseedDisposition.FAIL
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
            chart_count += 1
    unique_works, dup, labels = dedup_work_records(
        works,
        q_tol=config.tolerances.leaf_duplicate_distance_rad,
    )
    neighbor_audits = audit_all_neighbors(
        arm,
        unique_works,
        sigma_min=config.tolerances.minimum_transversality_sigma,
    )
    overlap_audits = _family_chart_overlap(
        arm,
        unique_works,
        q_tol=config.tolerances.leaf_duplicate_distance_rad,
        rotation_tol=config.tolerances.orientation_geodesic_rad,
        pointing_tol=config.tolerances.pointing_geodesic_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
    )
    overlap = summarize_chart_overlap(overlap_audits)
    leaves = recompute_family_acceptance(
        tuple(item.certificate for item in unique_works),
        neighbor_audits,
        overlap_audits,
    )
    chart_ids = tuple(item.chart_id for item in config.charts)
    lambda_intervals = audit_family_intervals(
        leaves,
        n_bins=n_bins,
        chart_ids=chart_ids,
        occupied=set(occupancy),
        seed_counts=seed_counts,
        exhausted=exhausted,
    )
    leaves, unresolved_lambda = apply_interval_coverage_gate(leaves, lambda_intervals)
    accepted = sum(1 for leaf in leaves if leaf.accepted_for_reconstruction)
    return LeafFamilyResult(
        probe_id=probe.probe_id,
        leaves=leaves,
        accepted_count=accepted,
        duplicate_count=dup,
        chart_overlap_status=overlap.status,
        unresolved_lambda_intervals=unresolved_lambda,
        notes=(
            "Canonical chart occupancy; confirmation freeze is the caller's duty.",
            "Neighbor transversality uses child Jacobians; chart overlap is source-Q correspondence.",
            "Circular lambda bins; SAMPLED_ADMISSIBLE is not COMPLETE; not a global foliation.",
            "birth/death/merge events are not classified.",
        ),
        neighbor_audits=neighbor_audits,
        chart_overlap=overlap,
        chart_overlap_audits=overlap_audits,
        duplicate_classifications=tuple(item.value for item in labels),
        lambda_intervals=lambda_intervals,
    )


def write_leaves_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
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
    budgets = resolve_stage_budgets(config, mode)
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
            max_steps=budgets.continuation_steps,
            max_leaves=budgets.max_natural_leaves_per_probe,
            max_leaves_per_chart=budgets.max_natural_leaves_per_chart,
            lambda_bins=budgets.natural_lambda_bin_count_per_chart,
            reseed_count=budgets.reseed_samples_per_leaf,
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
        "allows_full_campaign_disposition": budgets.allows_full_campaign_disposition,
        "limitations": []
        if budgets.allows_full_campaign_disposition
        else ["mode cannot issue full-campaign disposition"],
    }
    return finalize_stage(
        outdir,
        summary,
        config=config,
        stage="leaves",
        mode=mode,
        probe_ids=tuple(p.probe_id for p in probes),
    )
