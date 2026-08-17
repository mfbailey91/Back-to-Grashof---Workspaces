"""Icosphere direction grid, spherical cells, and curve-union painting.

Cell labels are local to the R3A confirmation sphere. They are not parent-atlas
coverage decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial_experiments.axis_geometry import unit_vector
from grashof_workspace.spatial_experiments.parent_task_images import (
    _face_barycenter,
    _max_cell_diameter,
    build_icosphere,
)

from .models import CellClass, L5PositiveControlGeometry, OracleFeasibility
from .positive_control import direction_oracle

Array = NDArray[np.floating]
Vec3 = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class SphereGrid:
    level: int
    vertices: Array
    faces: tuple[tuple[int, int, int], ...]
    barycenters: Array
    max_cell_diameter_rad: float
    adjacency: tuple[tuple[int, ...], ...]


def build_sphere_grid(level: int) -> SphereGrid:
    verts, faces = build_icosphere(level)
    bary = np.vstack([_face_barycenter(verts, face) for face in faces])
    adj: list[set[int]] = [set() for _ in range(verts.shape[0])]
    for i, j, k in faces:
        adj[i].update((j, k))
        adj[j].update((i, k))
        adj[k].update((i, j))
    return SphereGrid(
        level=level,
        vertices=np.asarray(verts, dtype=float),
        faces=tuple(faces),
        barycenters=np.asarray(bary, dtype=float),
        max_cell_diameter_rad=float(_max_cell_diameter(verts, faces)),
        adjacency=tuple(tuple(sorted(n)) for n in adj),
    )


def _unit3(values: Array | Vec3, *, name: str) -> Array:
    arr = np.asarray(values, dtype=float).reshape(3)
    return unit_vector((float(arr[0]), float(arr[1]), float(arr[2])), name=name)


def pointing_geodesic(a: Array | Vec3, b: Array | Vec3) -> float:
    ua = np.asarray(_unit3(a, name="a"))
    ub = np.asarray(_unit3(b, name="b"))
    return float(np.arccos(float(np.clip(np.dot(ua, ub), -1.0, 1.0))))


def _triple(a: Array, b: Array, c: Array) -> float:
    return float(np.dot(a, np.cross(b, c)))


def face_contains(d: Array, a: Array, b: Array, c: Array, *, tol: float = 1e-12) -> bool:
    s0 = _triple(a, b, c)
    if abs(s0) <= tol:
        return False
    s1 = _triple(d, b, c)
    s2 = _triple(a, d, c)
    s3 = _triple(a, b, d)
    if s0 > 0.0:
        return s1 >= -tol and s2 >= -tol and s3 >= -tol
    return s1 <= tol and s2 <= tol and s3 <= tol


def hit_face_indices(grid: SphereGrid, pointing: Array | Vec3) -> tuple[int, ...]:
    d = np.asarray(_unit3(pointing, name="d"))
    hits = [
        i
        for i, face in enumerate(grid.faces)
        if face_contains(d, grid.vertices[face[0]], grid.vertices[face[1]], grid.vertices[face[2]])
    ]
    if hits:
        return tuple(hits)
    dots = grid.barycenters @ d
    return (int(np.argmax(dots)),)


def classify_cells(
    grid: SphereGrid,
    geometry: L5PositiveControlGeometry,
    p_star: Vec3,
    *,
    margin_tol_m: float,
) -> tuple[CellClass, ...]:
    labels: list[CellClass] = []
    for i, face in enumerate(grid.faces):
        samples = [grid.vertices[j] for j in face]
        samples.append(grid.barycenters[i])
        feas = [
            direction_oracle(geometry, p_star, s, margin_tol_m=margin_tol_m)
            for s in samples
        ]
        margins = [item.margin_m for item in feas]
        states = [item.feasibility for item in feas]
        if all(s is OracleFeasibility.FEASIBLE and m >= margin_tol_m for s, m in zip(states, margins)):
            labels.append(CellClass.STRICT_COVERED)
        elif all(s is OracleFeasibility.INFEASIBLE and m <= -margin_tol_m for s, m in zip(states, margins)):
            labels.append(CellClass.STRICT_UNCOVERED)
        else:
            labels.append(CellClass.AMBIGUOUS_BOUNDARY)
    return tuple(labels)


def paint_pointings(grid: SphereGrid, pointings: tuple[Vec3, ...]) -> tuple[bool, ...]:
    hits = [False] * len(grid.faces)
    for d in pointings:
        for idx in hit_face_indices(grid, d):
            hits[idx] = True
    return tuple(hits)
