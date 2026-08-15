"""V06D1: task-derived pointing level-set fibers of a 5R source parent.

h(d)=n·d on the V06A2 atlas. These fibers are not the 2D parent, not U_v, and
not child reconstruction.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import as_vec3
from .branch_continuation import continue_implicit_branch
from .continuation import wrap_joint_delta
from .implicit_manifold import ambient_distance, orthonormal_tangent_basis
from .jacobians import matrix_rank_report, pointing_jacobian, position_jacobian
from .open_chain import OpenChainModel
from .orientation_image import rotation_matrix_to_quaternion
from .parent_atlas import ParentAtlasResult, wrap_periodic

Array = NDArray[np.floating]

EPS_H = 1e-4
CRITICAL_H_TOL = 1e-3
LEVELSET_NEWTON_ITERS = 20
LEVELSET_STEPS = 40
LEVELSET_STEP = 0.05
SEAM_NODE_TOL = 5e-3
FIBER_DUP_TOL = 0.35
N_DEFAULT = (0.0, 0.0, 1.0)
N_FALLBACK = (1.0, 0.0, 0.0)


class ContourKind(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    BOUNDARY_TOUCHING = "BOUNDARY_TOUCHING"
    CRITICAL_TOUCHING = "CRITICAL_TOUCHING"
    UNRESOLVED = "UNRESOLVED"


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float) and not isfinite(obj):
        return None
    return obj


def _json_object(obj: dict[str, Any]) -> dict[str, Any]:
    payload = _json_safe(obj)
    if not isinstance(payload, dict):
        raise TypeError("expected a JSON object")
    return payload


def choose_slice_normal(d_seed: tuple[float, float, float]) -> tuple[float, float, float]:
    d = np.asarray(d_seed, dtype=float)
    n = np.asarray(N_DEFAULT, dtype=float)
    if abs(float(np.dot(d, n))) > 0.95:
        n = np.asarray(N_FALLBACK, dtype=float)
    n = n / float(np.linalg.norm(n))
    return as_vec3(n)


def pointing_scalar(d: tuple[float, float, float] | Array, n: tuple[float, float, float]) -> float:
    return float(np.dot(np.asarray(d, dtype=float), np.asarray(n, dtype=float)))


def levelset_residual(
    model: OpenChainModel,
    q: tuple[float, ...],
    p_star: tuple[float, float, float],
    n: tuple[float, float, float],
    c: float,
) -> Array:
    state = model.chain.evaluate(q)
    r_p = np.asarray(state.p, dtype=float) - np.asarray(p_star, dtype=float)
    r_h = np.array((pointing_scalar(state.d, n) - c,), dtype=float)
    return np.asarray(np.concatenate([r_p, r_h]), dtype=float)


def levelset_jacobian(
    model: OpenChainModel,
    q: tuple[float, ...],
    n: tuple[float, float, float],
) -> Array:
    jp = position_jacobian(model.chain, q)
    jd = pointing_jacobian(model.chain, q)
    gh = np.asarray(n, dtype=float).reshape(1, 3) @ jd
    stacked = np.vstack((jp, gh))
    return np.asarray(stacked, dtype=float)


def parent_gradient_h(
    model: OpenChainModel,
    q: tuple[float, ...],
    n: tuple[float, float, float],
) -> Array:
    jp = position_jacobian(model.chain, q)
    n_p = orthonormal_tangent_basis(jp, expected_nullity=2)
    jd = pointing_jacobian(model.chain, q)
    grad = n_p.T @ (jd.T @ np.asarray(n, dtype=float))
    return np.asarray(grad, dtype=float)


def correct_to_levelset(
    model: OpenChainModel,
    q: tuple[float, ...],
    p_star: tuple[float, float, float],
    n: tuple[float, float, float],
    c: float,
) -> tuple[tuple[float, ...], bool, float]:
    x = np.asarray(q, dtype=float).copy()
    periodic = (True,) * len(q)
    for _ in range(LEVELSET_NEWTON_ITERS):
        qt = tuple(float(v) for v in x)
        r = levelset_residual(model, qt, p_star, n, c)
        nr = float(np.linalg.norm(r))
        if nr <= 1e-10:
            return qt, True, nr
        jac = levelset_jacobian(model, qt, n)
        dq, *_ = np.linalg.lstsq(jac, -r, rcond=None)
        x = wrap_periodic(x + dq, periodic)
    qt = tuple(float(v) for v in x)
    return qt, False, float(np.linalg.norm(levelset_residual(model, qt, p_star, n, c)))


@dataclass(frozen=True, slots=True)
class PointingLevelSetProblem:
    """Task-derived 1D branch ``p(q)=p*`` and ``n·d=c``. Equations unchanged."""

    model: OpenChainModel
    p_star: tuple[float, float, float]
    n: tuple[float, float, float]
    c: float
    problem_id: str
    ambient_dimension: int = 5
    constraint_dimension: int = 4
    periodic_coordinates: tuple[bool, ...] = (True, True, True, True, True)

    def residual(self, x: Array) -> Array:
        q = tuple(float(v) for v in np.asarray(x, dtype=float).reshape(-1))
        return levelset_residual(self.model, q, self.p_star, self.n, self.c)

    def jacobian(self, x: Array) -> Array:
        q = tuple(float(v) for v in np.asarray(x, dtype=float).reshape(-1))
        return levelset_jacobian(self.model, q, self.n)


@dataclass(frozen=True, slots=True)
class VertexScalarRecord:
    q: tuple[float, ...]
    pointing: tuple[float, float, float]
    h: float
    grad_h_norm: float
    regular: bool
    chart_id: str
    on_chart_boundary: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "q": list(self.q),
            "pointing": list(self.pointing),
            "h": self.h,
            "grad_h_norm": self.grad_h_norm,
            "regular": self.regular,
            "chart_id": self.chart_id,
            "on_chart_boundary": self.on_chart_boundary,
        }


@dataclass(frozen=True, slots=True)
class ContourComponent:
    component_id: str
    kind: ContourKind
    seeds: tuple[tuple[float, ...], ...]
    segment_count: int

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "kind": self.kind.value,
            "seeds": [list(s) for s in self.seeds],
            "segment_count": self.segment_count,
        }


@dataclass(frozen=True, slots=True)
class LevelSetSlice:
    c: float
    contours: tuple[ContourComponent, ...]
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "c": self.c,
            "contours": [item.to_json_dict() for item in self.contours],
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class FiberSample:
    sigma: float
    q: tuple[float, ...]
    pointing: tuple[float, float, float]
    quaternion: tuple[float, float, float, float]
    rank_jfc: int
    nullity_jfc: int
    residual: float

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "sigma": self.sigma,
            "q": list(self.q),
            "pointing": list(self.pointing),
            "quaternion": list(self.quaternion),
            "rank_jfc": self.rank_jfc,
            "nullity_jfc": self.nullity_jfc,
            "residual": self.residual,
        }


@dataclass(frozen=True, slots=True)
class SourceLevelSetFiber:
    fiber_id: str
    parent_id: str
    parent_component_id: str | None
    n: tuple[float, float, float]
    c: float
    provenance: str
    branch_status: str
    returned: bool
    samples: tuple[FiberSample, ...]
    contour_id: str
    seed_to_contour_distance: float
    unresolved_reason: str | None
    joint_limits: str
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_object(
            {
                "fiber_id": self.fiber_id,
                "parent_id": self.parent_id,
                "parent_component_id": self.parent_component_id,
                "n": list(self.n),
                "c": self.c,
                "provenance": self.provenance,
                "branch_status": self.branch_status,
                "returned": self.returned,
                "sample_count": len(self.samples),
                "samples": [s.to_json_dict() for s in self.samples],
                "contour_id": self.contour_id,
                "seed_to_contour_distance": self.seed_to_contour_distance,
                "unresolved_reason": self.unresolved_reason,
                "joint_limits": self.joint_limits,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class ParentLevelSetResult:
    architecture_id: str
    parent_id: str
    n: tuple[float, float, float]
    eps_h: float
    vertices: tuple[VertexScalarRecord, ...]
    critical_h_values: tuple[float, ...]
    slice_values: tuple[float, ...]
    slices: tuple[LevelSetSlice, ...]
    fibers: tuple[SourceLevelSetFiber, ...]
    complete_foliation: bool
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_object(
            {
                "architecture_id": self.architecture_id,
                "parent_id": self.parent_id,
                "certificate_status": None,
                "n": list(self.n),
                "eps_h": self.eps_h,
                "vertex_count": len(self.vertices),
                "regular_vertex_count": sum(1 for v in self.vertices if v.regular),
                "critical_h_values": list(self.critical_h_values),
                "slice_values": list(self.slice_values),
                "slices": [s.to_json_dict() for s in self.slices],
                "fibers": [f.to_json_dict() for f in self.fibers],
                "complete_foliation": self.complete_foliation,
                "notes": list(self.notes),
            }
        )


def _lerp_wrap(qa: Array, qb: Array, t: float) -> Array:
    delta = wrap_joint_delta(qb, qa)
    out = np.asarray(qa, dtype=float) + float(t) * delta
    return np.asarray(out, dtype=float)


def _vertex_field(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    n: tuple[float, float, float],
) -> list[VertexScalarRecord]:
    records: list[VertexScalarRecord] = []
    offset = 0
    for chart in atlas.charts:
        n_samp = sum(1 for s in chart.samples if s.correction.x is not None)
        chunk = atlas.vertices[offset : offset + n_samp]
        offset += n_samp
        samples = [s for s in chart.samples if s.correction.x is not None]
        for sample, diag in zip(samples, chunk, strict=True):
            if not diag.accepted:
                continue
            try:
                g = parent_gradient_h(model, diag.q, n)
            except ValueError:
                continue
            gnorm = float(np.linalg.norm(g))
            records.append(
                VertexScalarRecord(
                    q=diag.q,
                    pointing=diag.pointing,
                    h=pointing_scalar(diag.pointing, n),
                    grad_h_norm=gnorm,
                    regular=gnorm > EPS_H,
                    chart_id=chart.chart_id,
                    on_chart_boundary=sample.local_index != 0,
                )
            )
    return records


def _choose_slices(records: list[VertexScalarRecord]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    regular_h = [v.h for v in records if v.regular]
    critical_h = tuple(sorted({round(v.h, 6) for v in records if not v.regular}))
    if len(regular_h) < 2:
        return (), critical_h
    lo, hi = min(regular_h), max(regular_h)
    raw = (lo + 0.25 * (hi - lo), lo + 0.5 * (hi - lo), lo + 0.75 * (hi - lo))
    slices = []
    for c in raw:
        if any(abs(c - ch) <= CRITICAL_H_TOL for ch in critical_h):
            continue
        slices.append(float(c))
    return tuple(slices), critical_h


def _extract_contours(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    n: tuple[float, float, float],
    c: float,
    field: dict[tuple[str, int], VertexScalarRecord],
) -> tuple[ContourComponent, ...]:
    if atlas.stitch is not None and atlas.stitch.faces:
        return _extract_contours_stitched(atlas, model, n, c)
    return _extract_contours_by_chart(atlas, model, n, c, field)


def _extract_contours_stitched(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    n: tuple[float, float, float],
    c: float,
) -> tuple[ContourComponent, ...]:
    stitch = atlas.stitch
    assert stitch is not None
    hs: list[float] = []
    regular: list[bool] = []
    for vert in stitch.vertices:
        state = model.chain.evaluate(vert.q)
        hs.append(pointing_scalar(state.d, n))
        try:
            g = parent_gradient_h(model, vert.q, n)
            regular.append(float(np.linalg.norm(g)) > EPS_H)
        except ValueError:
            regular.append(False)
    nodes: list[tuple[float, ...]] = []
    segments: list[tuple[int, int]] = []
    node_meta: list[str] = []

    def _add_node(q: tuple[float, ...], meta: str) -> int:
        for i, existing in enumerate(nodes):
            if ambient_distance(np.asarray(q), np.asarray(existing), (True,) * 5) < SEAM_NODE_TOL:
                return i
        nodes.append(q)
        node_meta.append(meta)
        return len(nodes) - 1

    for face in stitch.faces:
        crossings: list[int] = []
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            ha, hb = hs[a], hs[b]
            if (ha - c) * (hb - c) >= 0.0:
                continue
            t = (c - ha) / (hb - ha)
            q_lin = _lerp_wrap(np.asarray(stitch.vertices[a].q), np.asarray(stitch.vertices[b].q), t)
            q_hat, ok, _res = correct_to_levelset(
                model, tuple(float(v) for v in q_lin), atlas.p_star, n, c
            )
            meta = "ok" if ok else "unresolved"
            if stitch.vertices[a].global_frontier or stitch.vertices[b].global_frontier:
                meta = "boundary"
            if (not regular[a]) or (not regular[b]):
                meta = "critical"
            crossings.append(_add_node(q_hat if ok else tuple(float(v) for v in q_lin), meta))
        if len(crossings) == 2:
            segments.append((crossings[0], crossings[1]))
    return _components_from_segments(nodes, segments, node_meta, c)


def _extract_contours_by_chart(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    n: tuple[float, float, float],
    c: float,
    field: dict[tuple[str, int], VertexScalarRecord],
) -> tuple[ContourComponent, ...]:
    nodes: list[tuple[float, ...]] = []
    segments: list[tuple[int, int]] = []
    node_meta: list[str] = []

    def _add_node(q: tuple[float, ...], meta: str) -> int:
        for i, existing in enumerate(nodes):
            if ambient_distance(np.asarray(q), np.asarray(existing), (True,) * 5) < SEAM_NODE_TOL:
                return i
        nodes.append(q)
        node_meta.append(meta)
        return len(nodes) - 1

    for chart in atlas.charts:
        local: dict[int, tuple[float, VertexScalarRecord]] = {}
        for sample in chart.samples:
            if sample.correction.x is None:
                continue
            rec = field.get((chart.chart_id, sample.local_index))
            if rec is None:
                continue
            local[sample.local_index] = (rec.h, rec)
        for face in chart.triangles:
            if any(idx not in local for idx in face):
                continue
            crossings: list[int] = []
            for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
                ha, rec_a = local[a]
                hb, rec_b = local[b]
                if (ha - c) * (hb - c) >= 0.0:
                    continue
                t = (c - ha) / (hb - ha)
                q_lin = _lerp_wrap(np.asarray(rec_a.q), np.asarray(rec_b.q), t)
                q_hat, ok, _res = correct_to_levelset(
                    model, tuple(float(v) for v in q_lin), atlas.p_star, n, c
                )
                meta = "ok" if ok else "unresolved"
                if rec_a.on_chart_boundary or rec_b.on_chart_boundary:
                    meta = "boundary"
                if (not rec_a.regular) or (not rec_b.regular):
                    meta = "critical"
                crossings.append(_add_node(q_hat if ok else tuple(float(v) for v in q_lin), meta))
            if len(crossings) == 2:
                segments.append((crossings[0], crossings[1]))
    return _components_from_segments(nodes, segments, node_meta, c)


def _components_from_segments(
    nodes: list[tuple[float, ...]],
    segments: list[tuple[int, int]],
    node_meta: list[str],
    c: float,
) -> tuple[ContourComponent, ...]:
    adj: dict[int, set[int]] = defaultdict(set)
    for a, b in segments:
        adj[a].add(b)
        adj[b].add(a)
    seen: set[int] = set()
    components: list[ContourComponent] = []
    cid = 0
    for i in range(len(nodes)):
        if i in seen:
            continue
        stack = [i]
        comp: list[int] = []
        while stack:
            j = stack.pop()
            if j in seen:
                continue
            seen.add(j)
            comp.append(j)
            stack.extend(adj[j] - seen)
        if not comp:
            continue
        kinds = {node_meta[j] for j in comp}
        degrees = [len(adj[j]) for j in comp]
        if "unresolved" in kinds:
            kind = ContourKind.UNRESOLVED
        elif "critical" in kinds:
            kind = ContourKind.CRITICAL_TOUCHING
        elif "boundary" in kinds:
            kind = ContourKind.BOUNDARY_TOUCHING
        elif all(d == 2 for d in degrees) and len(comp) >= 3:
            kind = ContourKind.CLOSED
        else:
            kind = ContourKind.OPEN
        seeds = tuple(nodes[j] for j in comp[:1])
        components.append(
            ContourComponent(
                component_id=f"c{c:.4f}_comp{cid}",
                kind=kind,
                seeds=seeds,
                segment_count=sum(1 for a, b in segments if a in comp and b in comp),
            )
        )
        cid += 1
    return tuple(components)


def _fiber_sample(
    model: OpenChainModel,
    q: tuple[float, ...],
    n: tuple[float, float, float],
    c: float,
    p_star: tuple[float, float, float],
    sigma: float,
) -> FiberSample:
    state = model.chain.evaluate(q)
    jac = levelset_jacobian(model, q, n)
    report = matrix_rank_report(jac)
    res = float(np.linalg.norm(levelset_residual(model, q, p_star, n, c)))
    return FiberSample(
        sigma=sigma,
        q=q,
        pointing=as_vec3(state.d),
        quaternion=rotation_matrix_to_quaternion(np.asarray(state.R, dtype=float)),
        rank_jfc=report.rank,
        nullity_jfc=report.nullity,
        residual=res,
    )


def continue_level_set(
    model: OpenChainModel,
    q0: tuple[float, ...],
    p_star: tuple[float, float, float],
    n: tuple[float, float, float],
    c: float,
    *,
    n_steps: int = LEVELSET_STEPS,
    step: float = LEVELSET_STEP,
) -> tuple[tuple[FiberSample, ...], str, bool]:
    q_seed, ok, _res0 = correct_to_levelset(model, q0, p_star, n, c)
    if not ok:
        return (), "unresolved", False
    jac0 = levelset_jacobian(model, q_seed, n)
    report0 = matrix_rank_report(jac0)
    if report0.rank != 4 or report0.nullity != 1:
        return (_fiber_sample(model, q_seed, n, c, p_star, 0.0),), "singular", False
    problem = PointingLevelSetProblem(
        model=model,
        p_star=p_star,
        n=n,
        c=c,
        problem_id=f"{model.architecture_id}_h{c:.4f}",
    )
    trace = continue_implicit_branch(
        problem,
        np.asarray(q_seed, dtype=float),
        branch_id=f"{model.architecture_id}_levelset_c{c:.4f}",
        max_steps=n_steps,
        step_size=step,
    )
    samples = [
        _fiber_sample(
            model,
            tuple(float(v) for v in step.x),
            n,
            c,
            p_star,
            step.s,
        )
        for step in trace.steps
        if step.accepted and step.x is not None
    ]
    samples.sort(key=lambda s: s.sigma)
    return tuple(samples), trace.branch_status, trace.returned


def _symmetric_wrapped_set_distance(
    a: list[Array],
    b: list[Array],
    periodic: tuple[bool, ...],
) -> float:
    if not a or not b:
        return float("inf")

    def _one(src: list[Array], dst: list[Array]) -> float:
        worst = 0.0
        for q in src:
            best = min(ambient_distance(q, p, periodic) for p in dst)
            worst = max(worst, best)
        return worst

    return max(_one(a, b), _one(b, a))


def _dedup_fibers(fibers: list[SourceLevelSetFiber]) -> list[SourceLevelSetFiber]:
    kept: list[SourceLevelSetFiber] = []
    periodic = (True,) * 5
    for fiber in fibers:
        qs = [np.asarray(s.q, dtype=float) for s in fiber.samples]
        is_dup = False
        for prior in kept:
            if abs(prior.c - fiber.c) > 1e-12:
                continue
            ps = [np.asarray(s.q, dtype=float) for s in prior.samples]
            if _symmetric_wrapped_set_distance(qs, ps, periodic) <= FIBER_DUP_TOL:
                is_dup = True
                break
        if not is_dup:
            kept.append(fiber)
    return kept


def build_parent_level_sets(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    *,
    parent_id: str | None = None,
) -> ParentLevelSetResult:
    seed_d = next((v.pointing for v in atlas.vertices if v.accepted), (0.0, 0.0, 1.0))
    n = choose_slice_normal(seed_d)
    records = _vertex_field(atlas, model, n)
    slices, critical = _choose_slices(records)
    field: dict[tuple[str, int], VertexScalarRecord] = {}
    for chart in atlas.charts:
        for sample in chart.samples:
            if sample.correction.x is None:
                continue
            q = tuple(float(v) for v in sample.correction.x)
            match = next((r for r in records if r.chart_id == chart.chart_id and r.q == q), None)
            if match is not None:
                field[(chart.chart_id, sample.local_index)] = match

    pid = parent_id or f"{atlas.architecture_id}_pointing_parent"
    comp_id = atlas.component_ids[0] if atlas.component_ids else None
    slice_rows: list[LevelSetSlice] = []
    fibers: list[SourceLevelSetFiber] = []
    for c in slices:
        contours = _extract_contours(atlas, model, n, c, field)
        slice_rows.append(
            LevelSetSlice(
                c=c,
                contours=contours,
                notes=("Not a complete foliation.",),
            )
        )
        for contour in contours:
            if not contour.seeds:
                continue
            samples, status, returned = continue_level_set(
                model, contour.seeds[0], atlas.p_star, n, c
            )
            dist = 0.0
            if samples:
                dist = ambient_distance(
                    np.asarray(samples[min(range(len(samples)), key=lambda i: abs(samples[i].sigma))].q),
                    np.asarray(contour.seeds[0]),
                    (True,) * 5,
                )
            fibers.append(
                SourceLevelSetFiber(
                    fiber_id=f"{atlas.architecture_id}_h{c:.4f}_{contour.component_id}",
                    parent_id=pid,
                    parent_component_id=comp_id,
                    n=n,
                    c=c,
                    provenance="task-derived",
                    branch_status=status,
                    returned=returned,
                    samples=samples,
                    contour_id=contour.component_id,
                    seed_to_contour_distance=dist,
                    unresolved_reason=None if status != "unresolved" else "corrector or rank failure",
                    joint_limits="not_modeled",
                    notes=(
                        "Task-derived h(d)=n·d fiber; not U_v and not the 2D parent.",
                        f"contour_kind={contour.kind.value}",
                        "One continued branch per global contour after seam stitch (ADR-046).",
                    ),
                )
            )
    fibers = _dedup_fibers(fibers)
    return ParentLevelSetResult(
        architecture_id=atlas.architecture_id,
        parent_id=pid,
        n=n,
        eps_h=EPS_H,
        vertices=tuple(records),
        critical_h_values=critical,
        slice_values=slices,
        slices=tuple(slice_rows),
        fibers=tuple(fibers),
        complete_foliation=False,
        notes=(
            "V06D1 source level sets on a budget-limited parent atlas.",
            "Not a complete foliation, not U_v, not reconstruction.",
        ),
    )


def level_set_summary(result: ParentLevelSetResult) -> dict[str, Any]:
    return {
        "architecture_id": result.architecture_id,
        "n": list(result.n),
        "slice_values": list(result.slice_values),
        "fiber_count": len(result.fibers),
        "complete_foliation": result.complete_foliation,
        "regular_vertex_count": sum(1 for v in result.vertices if v.regular),
        "provenance": "task-derived",
        "certificate_status": None,
    }
