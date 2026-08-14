"""V06C: decomposition-free source orientation surface and pointing image.

These objects are two-dimensional task images of a source parent atlas. They are
not V05 orientation *curves*, not all of SO(3), not S^2 completeness, and not
DecompositionCertificates.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from math import acos, isfinite, sqrt
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .implicit_manifold import ambient_distance
from .open_chain import OpenChainModel
from .orientation_image import (
    NEAR_SINGULAR_SIGMA_TOL,
    _pointing_geodesic,
    _rotation_geodesic,
    rotation_matrix_to_quaternion,
    rotation_matrix_to_rotvec,
)
from .parent_atlas import ParentAtlasResult, wrap_periodic
from .parent_local import ParentRepresentationStatus, ParentVertexDiagnostics

Array = NDArray[np.floating]

DEFAULT_ICOSPHERE_LEVEL = 2
POINTING_CLUSTER_TOL_RAD = 0.12
NEAR_CRITICAL_RANK = 2


class CoverageLabel(str, Enum):
    """Declared-resolution pointing coverage. Not a certificate."""

    COVERED_AT_DECLARED_RESOLUTION = "COVERED_AT_DECLARED_RESOLUTION"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    UNRESOLVED = "UNRESOLVED"


class SphereCellKind(str, Enum):
    COVERED = "COVERED"
    UNCOVERED = "UNCOVERED"
    AMBIGUOUS_BOUNDARY = "AMBIGUOUS_BOUNDARY"
    UNRESOLVED = "UNRESOLVED"


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: _json_safe(val) for key, val in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(val) for val in obj]
    if isinstance(obj, float) and not isfinite(obj):
        return None
    return obj


def _clamped_acos(value: float) -> float:
    return float(acos(max(-1.0, min(1.0, value))))


@dataclass(frozen=True, slots=True)
class OrientationSurfaceVertex:
    vertex_id: int
    chart_id: str
    component_id: str | None
    q: tuple[float, ...]
    R: tuple[tuple[float, float, float], ...]
    quaternion: tuple[float, float, float, float]
    rotvec: tuple[float, float, float]
    rank_jp: int
    rank_jd_np: int
    sigma_min_jd_np: float | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "vertex_id": self.vertex_id,
            "chart_id": self.chart_id,
            "component_id": self.component_id,
            "q": list(self.q),
            "R": [list(row) for row in self.R],
            "quaternion": list(self.quaternion),
            "rotvec": list(self.rotvec),
            "rank_jp": self.rank_jp,
            "rank_jd_np": self.rank_jd_np,
            "sigma_min_jd_np": self.sigma_min_jd_np,
        }


@dataclass(frozen=True, slots=True)
class OrientationEdge:
    vertex_a: int
    vertex_b: int
    geodesic_rad: float
    chart_id: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "vertex_a": self.vertex_a,
            "vertex_b": self.vertex_b,
            "geodesic_rad": self.geodesic_rad,
            "chart_id": self.chart_id,
        }


@dataclass(frozen=True, slots=True)
class ParentOrientationSurfaceResult:
    architecture_id: str
    p_star: tuple[float, float, float]
    component_ids: tuple[str, ...]
    vertices: tuple[OrientationSurfaceVertex, ...]
    edges: tuple[OrientationEdge, ...]
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_safe(
            {
                "architecture_id": self.architecture_id,
                "p_star": list(self.p_star),
                "component_ids": list(self.component_ids),
                "certificate_status": None,
                "vertex_count": len(self.vertices),
                "edge_count": len(self.edges),
                "vertices": [v.to_json_dict() for v in self.vertices],
                "edges": [e.to_json_dict() for e in self.edges],
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class MappedSphericalTriangle:
    chart_id: str
    component_id: str | None
    source_face: tuple[int, int, int]
    vertex_ids: tuple[int, int, int]
    pointing: tuple[tuple[float, float, float], ...]
    barycenter: tuple[float, float, float]
    unresolved: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "component_id": self.component_id,
            "source_face": list(self.source_face),
            "vertex_ids": list(self.vertex_ids),
            "pointing": [list(p) for p in self.pointing],
            "barycenter": list(self.barycenter),
            "unresolved": self.unresolved,
        }


@dataclass(frozen=True, slots=True)
class PointingBoundaryEdge:
    vertex_a: int
    vertex_b: int
    pointing_a: tuple[float, float, float]
    pointing_b: tuple[float, float, float]
    geodesic_rad: float
    source: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "vertex_a": self.vertex_a,
            "vertex_b": self.vertex_b,
            "pointing_a": list(self.pointing_a),
            "pointing_b": list(self.pointing_b),
            "geodesic_rad": self.geodesic_rad,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class PointingMultiplicityCluster:
    cluster_id: int
    pointing: tuple[float, float, float]
    distinct_q_count: int
    vertex_ids: tuple[int, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "pointing": list(self.pointing),
            "distinct_q_count": self.distinct_q_count,
            "vertex_ids": list(self.vertex_ids),
        }


@dataclass(frozen=True, slots=True)
class SphereGridCell:
    cell_id: int
    kind: SphereCellKind
    vertices: tuple[tuple[float, float, float], ...]
    barycenter: tuple[float, float, float]
    hit_count: int
    multiplicity: int
    representative_q: tuple[float, ...] | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "kind": self.kind.value,
            "vertices": [list(v) for v in self.vertices],
            "barycenter": list(self.barycenter),
            "hit_count": self.hit_count,
            "multiplicity": self.multiplicity,
            "representative_q": None if self.representative_q is None else list(self.representative_q),
        }


@dataclass(frozen=True, slots=True)
class DeclaredResolutionSphereGrid:
    construction: str
    subdivision_level: int
    vertex_count: int
    cell_count: int
    max_cell_diameter_rad: float
    cells: tuple[SphereGridCell, ...]

    def to_json_dict(self) -> dict[str, Any]:
        covered = sum(1 for c in self.cells if c.kind is SphereCellKind.COVERED)
        uncovered = sum(1 for c in self.cells if c.kind is SphereCellKind.UNCOVERED)
        ambiguous = sum(1 for c in self.cells if c.kind is SphereCellKind.AMBIGUOUS_BOUNDARY)
        unresolved = sum(1 for c in self.cells if c.kind is SphereCellKind.UNRESOLVED)
        return _json_safe(
            {
                "construction": self.construction,
                "subdivision_level": self.subdivision_level,
                "vertex_count": self.vertex_count,
                "cell_count": self.cell_count,
                "max_cell_diameter_rad": self.max_cell_diameter_rad,
                "covered_cell_count": covered,
                "uncovered_cell_count": uncovered,
                "ambiguous_boundary_cell_count": ambiguous,
                "unresolved_cell_count": unresolved,
                "cells": [c.to_json_dict() for c in self.cells],
            }
        )


@dataclass(frozen=True, slots=True)
class ParentPointingImageResult:
    architecture_id: str
    p_star: tuple[float, float, float]
    component_ids: tuple[str, ...]
    coverage_label: CoverageLabel
    spherical_vertices: tuple[tuple[float, float, float], ...]
    mapped_triangles: tuple[MappedSphericalTriangle, ...]
    boundary_curves: tuple[PointingBoundaryEdge, ...]
    critical_vertex_ids: tuple[int, ...]
    near_critical_vertex_ids: tuple[int, ...]
    multiplicity: tuple[PointingMultiplicityCluster, ...]
    unresolved_face_count: int
    sphere_grid: DeclaredResolutionSphereGrid
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return _json_safe(
            {
                "architecture_id": self.architecture_id,
                "p_star": list(self.p_star),
                "component_ids": list(self.component_ids),
                "certificate_status": None,
                "coverage_label": self.coverage_label.value,
                "spherical_vertices": [list(p) for p in self.spherical_vertices],
                "mapped_triangles": [t.to_json_dict() for t in self.mapped_triangles],
                "boundary_curves": [e.to_json_dict() for e in self.boundary_curves],
                "critical_vertex_ids": list(self.critical_vertex_ids),
                "near_critical_vertex_ids": list(self.near_critical_vertex_ids),
                "multiplicity": [m.to_json_dict() for m in self.multiplicity],
                "unresolved_face_count": self.unresolved_face_count,
                "sphere_grid": self.sphere_grid.to_json_dict(),
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class SourceTaskImageBundle:
    atlas_representation_status: str
    orientation: ParentOrientationSurfaceResult
    pointing: ParentPointingImageResult

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "atlas_representation_status": self.atlas_representation_status,
            "certificate_status": None,
            "orientation": self.orientation.to_json_dict(),
            "pointing": self.pointing.to_json_dict(),
        }


def build_icosphere(level: int = DEFAULT_ICOSPHERE_LEVEL) -> tuple[Array, tuple[tuple[int, int, int], ...]]:
    """Regular icosahedron recursively subdivided onto the unit sphere."""

    if level < 0:
        raise ValueError("icosphere subdivision level must be nonnegative")
    t = (1.0 + sqrt(5.0)) / 2.0
    raw = np.array(
        [
            (-1.0, t, 0.0),
            (1.0, t, 0.0),
            (-1.0, -t, 0.0),
            (1.0, -t, 0.0),
            (0.0, -1.0, t),
            (0.0, 1.0, t),
            (0.0, -1.0, -t),
            (0.0, 1.0, -t),
            (t, 0.0, -1.0),
            (t, 0.0, 1.0),
            (-t, 0.0, -1.0),
            (-t, 0.0, 1.0),
        ],
        dtype=float,
    )
    verts = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    faces: list[tuple[int, int, int]] = [
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1),
    ]
    midpoint_cache: dict[tuple[int, int], int] = {}

    def _mid(a: int, b: int) -> int:
        key = (a, b) if a < b else (b, a)
        if key in midpoint_cache:
            return midpoint_cache[key]
        nonlocal verts
        mid = verts[a] + verts[b]
        mid = mid / float(np.linalg.norm(mid))
        idx = int(verts.shape[0])
        verts = np.vstack([verts, mid])
        midpoint_cache[key] = idx
        return idx

    for _ in range(level):
        midpoint_cache.clear()
        nxt: list[tuple[int, int, int]] = []
        for i, j, k in faces:
            a = _mid(i, j)
            b = _mid(j, k)
            c = _mid(k, i)
            nxt.extend(((i, a, c), (j, b, a), (k, c, b), (a, b, c)))
        faces = nxt
    return verts, tuple(faces)


def _face_barycenter(verts: Array, face: tuple[int, int, int]) -> Array:
    p = verts[list(face)].mean(axis=0)
    n = float(np.linalg.norm(p))
    return p / n if n > 0.0 else p


def _max_cell_diameter(verts: Array, faces: tuple[tuple[int, int, int], ...]) -> float:
    diam = 0.0
    for i, j, k in faces:
        for a, b in ((i, j), (j, k), (k, i)):
            diam = max(diam, _clamped_acos(float(np.dot(verts[a], verts[b]))))
    return diam


def _diag_lookup(atlas: ParentAtlasResult) -> dict[tuple[str, tuple[float, ...]], ParentVertexDiagnostics]:
    # Vertices are appended chart-major in the same sample order as charts.
    out: dict[tuple[str, tuple[float, ...]], ParentVertexDiagnostics] = {}
    offset = 0
    for chart in atlas.charts:
        n_samples = sum(1 for s in chart.samples if s.correction.x is not None)
        chunk = atlas.vertices[offset : offset + n_samples]
        offset += n_samples
        for sample, diag in zip(
            [s for s in chart.samples if s.correction.x is not None],
            chunk,
            strict=True,
        ):
            q = tuple(float(v) for v in sample.correction.x)  # type: ignore[union-attr]
            out[(chart.chart_id, q)] = diag
    return out


def _stabilize_from_adjacency(
    raw: list[tuple[float, float, float, float]],
    edges: list[tuple[int, int]],
    seed: int,
) -> list[tuple[float, float, float, float]]:
    n = len(raw)
    adj: dict[int, list[int]] = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    out = [raw[i] for i in range(n)]
    seen = [False] * n
    queue: deque[int] = deque([seed])
    seen[seed] = True
    while queue:
        i = queue.popleft()
        qi = np.asarray(out[i], dtype=float)
        for j in adj[i]:
            if seen[j]:
                continue
            qj = np.asarray(out[j], dtype=float)
            if float(np.dot(qi, qj)) < 0.0:
                qj = -qj
                out[j] = (float(qj[0]), float(qj[1]), float(qj[2]), float(qj[3]))
            seen[j] = True
            queue.append(j)
    for i, flag in enumerate(seen):
        if flag:
            continue
        q = np.asarray(out[i], dtype=float)
        if q[0] < 0.0:
            q = -q
            out[i] = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))
    return out


def _cluster_pointing(
    vertices: list[OrientationSurfaceVertex],
    pointing: list[Array],
    *,
    tol: float,
) -> tuple[PointingMultiplicityCluster, ...]:
    n = len(vertices)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            if _pointing_geodesic(pointing[i], pointing[j]) <= tol:
                union(i, j)
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    clusters: list[PointingMultiplicityCluster] = []
    periodic = (True,) * 5
    for cid, members in enumerate(sorted(groups.values(), key=lambda g: g[0])):
        mean = np.mean([pointing[i] for i in members], axis=0)
        mean = mean / float(np.linalg.norm(mean))
        qs: list[Array] = []
        for i in members:
            q = np.asarray(vertices[i].q, dtype=float)
            if not any(ambient_distance(q, other, periodic) <= 1e-6 for other in qs):
                qs.append(q)
        clusters.append(
            PointingMultiplicityCluster(
                cluster_id=cid,
                pointing=tuple(float(v) for v in mean),
                distinct_q_count=len(qs),
                vertex_ids=tuple(members),
            )
        )
    return tuple(clusters)


def _image_coverage_label(atlas: ParentAtlasResult) -> CoverageLabel:
    closed = ParentRepresentationStatus.CLOSED_COMPONENT_AT_DECLARED_RESOLUTION
    if atlas.representation_status is closed:
        return CoverageLabel.UNRESOLVED
    return CoverageLabel.PARTIAL_COVERAGE


def build_source_task_images(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    *,
    icosphere_level: int = DEFAULT_ICOSPHERE_LEVEL,
) -> SourceTaskImageBundle:
    """Project a source parent atlas into SO(3) and S^2. No child input."""

    component_id = atlas.component_ids[0] if atlas.component_ids else None
    diag_by_q = _diag_lookup(atlas)
    vertices: list[OrientationSurfaceVertex] = []
    pointing_vecs: list[Array] = []
    index_of: dict[tuple[str, int], int] = {}
    raw_quats: list[tuple[float, float, float, float]] = []
    rotations: list[Array] = []

    for chart in atlas.charts:
        for sample in chart.samples:
            if sample.correction.x is None:
                continue
            q = tuple(float(v) for v in sample.correction.x)
            diag = diag_by_q.get((chart.chart_id, q))
            if diag is None or not diag.accepted:
                continue
            state = model.chain.evaluate(q)
            rmat = np.asarray(state.R, dtype=float).reshape(3, 3)
            d = np.asarray(diag.pointing, dtype=float)
            nrm = float(np.linalg.norm(d))
            if nrm > 0.0:
                d = d / nrm
            vid = len(vertices)
            index_of[(chart.chart_id, sample.local_index)] = vid
            raw_quats.append(rotation_matrix_to_quaternion(rmat))
            rotations.append(rmat)
            pointing_vecs.append(d)
            sigmas = diag.jd_np_singular_values
            sigma_min = min(sigmas) if sigmas else None
            vertices.append(
                OrientationSurfaceVertex(
                    vertex_id=vid,
                    chart_id=chart.chart_id,
                    component_id=component_id,
                    q=q,
                    R=tuple(tuple(float(v) for v in row) for row in rmat),
                    quaternion=raw_quats[-1],
                    rotvec=rotation_matrix_to_rotvec(rmat),
                    rank_jp=diag.rank_jp,
                    rank_jd_np=diag.rank_jd_np,
                    sigma_min_jd_np=sigma_min,
                )
            )

    adj_edges: list[tuple[int, int]] = []
    orient_edges: list[OrientationEdge] = []
    mapped: list[MappedSphericalTriangle] = []
    unresolved_faces = 0
    edge_use: dict[tuple[int, int], int] = defaultdict(int)

    for chart in atlas.charts:
        local_ok = {
            s.local_index: s.correction.accepted and s.correction.x is not None
            for s in chart.samples
        }
        for face in chart.triangles:
            ids = []
            ok = True
            for loc in face:
                key = (chart.chart_id, loc)
                if key not in index_of or not local_ok.get(loc, False):
                    ok = False
                    break
                ids.append(index_of[key])
            if not ok:
                unresolved_faces += 1
                continue
            a, b, c = ids
            for u, v in ((a, b), (b, c), (c, a)):
                pair = (u, v) if u < v else (v, u)
                if pair not in edge_use:
                    adj_edges.append(pair)
                    geo = _rotation_geodesic(rotations[pair[0]], rotations[pair[1]])
                    orient_edges.append(
                        OrientationEdge(pair[0], pair[1], geo, chart.chart_id)
                    )
                edge_use[pair] += 1
            bary = pointing_vecs[a] + pointing_vecs[b] + pointing_vecs[c]
            bn = float(np.linalg.norm(bary))
            bary = bary / bn if bn > 0.0 else bary
            near_crit = any(
                vertices[i].rank_jd_np < NEAR_CRITICAL_RANK
                or (
                    vertices[i].sigma_min_jd_np is not None
                    and vertices[i].sigma_min_jd_np < NEAR_SINGULAR_SIGMA_TOL
                )
                for i in (a, b, c)
            )
            mapped.append(
                MappedSphericalTriangle(
                    chart_id=chart.chart_id,
                    component_id=component_id,
                    source_face=face,
                    vertex_ids=(a, b, c),
                    pointing=tuple(tuple(float(v) for v in pointing_vecs[i]) for i in (a, b, c)),
                    barycenter=tuple(float(v) for v in bary),
                    unresolved=near_crit,
                )
            )

    # Overlap edges: connect chart centers when overlap exists.
    center_ids: dict[str, int] = {}
    for chart in atlas.charts:
        key = (chart.chart_id, 0)
        if key in index_of:
            center_ids[chart.chart_id] = index_of[key]
    for overlap in atlas.overlaps:
        ia = center_ids.get(overlap.chart_a)
        ib = center_ids.get(overlap.chart_b)
        if ia is None or ib is None:
            continue
        pair = (ia, ib) if ia < ib else (ib, ia)
        if pair not in edge_use:
            adj_edges.append(pair)
            geo = _rotation_geodesic(rotations[pair[0]], rotations[pair[1]])
            orient_edges.append(
                OrientationEdge(pair[0], pair[1], geo, f"{overlap.chart_a}+{overlap.chart_b}")
            )
            edge_use[pair] += 1

    seed = 0
    stable = _stabilize_from_adjacency(raw_quats, adj_edges, seed) if vertices else []
    vertices = [
        OrientationSurfaceVertex(
            vertex_id=v.vertex_id,
            chart_id=v.chart_id,
            component_id=v.component_id,
            q=v.q,
            R=v.R,
            quaternion=stable[i],
            rotvec=v.rotvec,
            rank_jp=v.rank_jp,
            rank_jd_np=v.rank_jd_np,
            sigma_min_jd_np=v.sigma_min_jd_np,
        )
        for i, v in enumerate(vertices)
    ]

    critical = tuple(
        v.vertex_id for v in vertices if v.rank_jd_np < NEAR_CRITICAL_RANK
    )
    near_critical = tuple(
        v.vertex_id
        for v in vertices
        if v.sigma_min_jd_np is not None
        and v.sigma_min_jd_np < NEAR_SINGULAR_SIGMA_TOL
        and v.vertex_id not in critical
    )

    boundary: list[PointingBoundaryEdge] = []
    for (a, b), count in edge_use.items():
        if count != 1:
            continue
        is_face_edge = any({a, b} <= set(tri.vertex_ids) for tri in mapped)
        if not is_face_edge:
            continue
        pa = pointing_vecs[a]
        pb = pointing_vecs[b]
        boundary.append(
            PointingBoundaryEdge(
                vertex_a=a,
                vertex_b=b,
                pointing_a=tuple(float(v) for v in pa),
                pointing_b=tuple(float(v) for v in pb),
                geodesic_rad=_pointing_geodesic(pa, pb),
                source="mapped_triangle_boundary",
            )
        )
    for fr in atlas.frontiers:
        if fr.q is None:
            continue
        qn = wrap_periodic(np.asarray(fr.q, dtype=float), (True,) * len(fr.q))
        best = None
        best_d = None
        for v in vertices:
            d = ambient_distance(qn, np.asarray(v.q, dtype=float), (True,) * len(v.q))
            if best_d is None or d < best_d:
                best_d = d
                best = v
        if best is None or best_d is None or best_d > 0.25:
            continue
        dvec = pointing_vecs[best.vertex_id]
        boundary.append(
            PointingBoundaryEdge(
                vertex_a=best.vertex_id,
                vertex_b=best.vertex_id,
                pointing_a=tuple(float(v) for v in dvec),
                pointing_b=tuple(float(v) for v in dvec),
                geodesic_rad=0.0,
                source=f"atlas_frontier_{fr.kind.value}",
            )
        )

    multiplicity = _cluster_pointing(vertices, pointing_vecs, tol=POINTING_CLUSTER_TOL_RAD)

    ico_verts, ico_faces = build_icosphere(icosphere_level)
    barys = np.vstack([_face_barycenter(ico_verts, f) for f in ico_faces])
    max_diam = _max_cell_diameter(ico_verts, ico_faces)
    hits: dict[int, list[MappedSphericalTriangle]] = defaultdict(list)
    for tri in mapped:
        b = np.asarray(tri.barycenter, dtype=float)
        cell = int(np.argmax(barys @ b))
        hits[cell].append(tri)

    neighbors: dict[int, set[int]] = defaultdict(set)
    edge_to_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for fi, face in enumerate(ico_faces):
        for u, v in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge_to_faces[(u, v) if u < v else (v, u)].append(fi)
    for faces_here in edge_to_faces.values():
        if len(faces_here) == 2:
            a, b = faces_here
            neighbors[a].add(b)
            neighbors[b].add(a)

    cells: list[SphereGridCell] = []
    for fi, face in enumerate(ico_faces):
        assigned = hits.get(fi, [])
        unresolved_hit = any(t.unresolved for t in assigned)
        hit_n = len(assigned)
        qs: list[Array] = []
        periodic = (True,) * 5
        for tri in assigned:
            for vid in tri.vertex_ids:
                q = np.asarray(vertices[vid].q, dtype=float)
                if not any(ambient_distance(q, other, periodic) <= 1e-6 for other in qs):
                    qs.append(q)
        if unresolved_hit:
            kind = SphereCellKind.UNRESOLVED
        elif hit_n == 0:
            kind = SphereCellKind.UNCOVERED
        else:
            kind = SphereCellKind.COVERED
        cells.append(
            SphereGridCell(
                cell_id=fi,
                kind=kind,
                vertices=tuple(tuple(float(x) for x in ico_verts[i]) for i in face),
                barycenter=tuple(float(x) for x in barys[fi]),
                hit_count=hit_n,
                multiplicity=len(qs),
                representative_q=None if not qs else tuple(float(v) for v in qs[0]),
            )
        )
    for cell in list(cells):
        if cell.kind is not SphereCellKind.COVERED:
            continue
        if any(cells[n].kind is SphereCellKind.UNCOVERED for n in neighbors[cell.cell_id]):
            cells[cell.cell_id] = SphereGridCell(
                cell_id=cell.cell_id,
                kind=SphereCellKind.AMBIGUOUS_BOUNDARY,
                vertices=cell.vertices,
                barycenter=cell.barycenter,
                hit_count=cell.hit_count,
                multiplicity=cell.multiplicity,
                representative_q=cell.representative_q,
            )

    grid = DeclaredResolutionSphereGrid(
        construction="regular_icosahedron_geodesic_subdivision",
        subdivision_level=icosphere_level,
        vertex_count=int(ico_verts.shape[0]),
        cell_count=len(ico_faces),
        max_cell_diameter_rad=max_diam,
        cells=tuple(cells),
    )
    coverage = _image_coverage_label(atlas)
    spherical = tuple(tuple(float(v) for v in p) for p in pointing_vecs)
    orientation = ParentOrientationSurfaceResult(
        architecture_id=atlas.architecture_id,
        p_star=atlas.p_star,
        component_ids=atlas.component_ids,
        vertices=tuple(vertices),
        edges=tuple(orient_edges),
        notes=(
            "Two-dimensional orientation image in SO(3); not all of SO(3).",
            "Not a V05 orientation curve; no curve_type is assigned.",
            "Quaternions are adjacency-stabilized from the seed chart center.",
        ),
    )
    pointing = ParentPointingImageResult(
        architecture_id=atlas.architecture_id,
        p_star=atlas.p_star,
        component_ids=atlas.component_ids,
        coverage_label=coverage,
        spherical_vertices=spherical,
        mapped_triangles=tuple(mapped),
        boundary_curves=tuple(boundary),
        critical_vertex_ids=critical,
        near_critical_vertex_ids=near_critical,
        multiplicity=multiplicity,
        unresolved_face_count=unresolved_faces,
        sphere_grid=grid,
        notes=(
            "Pointing image d=R z_T of the source atlas; not S^2 completeness.",
            f"coverage_label={coverage.value} because atlas is {atlas.representation_status.value}.",
            "rank(Jd Np) is retained separately from rank(Jp).",
            "No child, aggregation, or U_v input is used.",
        ),
    )
    return SourceTaskImageBundle(
        atlas_representation_status=atlas.representation_status.value,
        orientation=orientation,
        pointing=pointing,
    )


def source_task_image_summary(bundle: SourceTaskImageBundle) -> dict[str, Any]:
    grid = bundle.pointing.sphere_grid
    return {
        "atlas_representation_status": bundle.atlas_representation_status,
        "coverage_label": bundle.pointing.coverage_label.value,
        "orientation_vertex_count": len(bundle.orientation.vertices),
        "mapped_triangle_count": len(bundle.pointing.mapped_triangles),
        "unresolved_face_count": bundle.pointing.unresolved_face_count,
        "icosphere_level": grid.subdivision_level,
        "icosphere_cell_count": grid.cell_count,
        "max_cell_diameter_rad": grid.max_cell_diameter_rad,
        "covered_cell_count": sum(1 for c in grid.cells if c.kind is SphereCellKind.COVERED),
        "uncovered_cell_count": sum(1 for c in grid.cells if c.kind is SphereCellKind.UNCOVERED),
        "ambiguous_boundary_cell_count": sum(
            1 for c in grid.cells if c.kind is SphereCellKind.AMBIGUOUS_BOUNDARY
        ),
        "certificate_status": None,
    }
