"""Exact rotated Z–Y–Z virtual-spherical chart. Geometry is frozen per leaf."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from grashof_workspace.spatial_experiments.axis_geometry import AxisLine, as_vec3, unit_vector
from grashof_workspace.spatial_experiments.orientation_image import _rotation_geodesic

from .models import ChartAtlasPolicy, SphericalClosureChartRecord

Array = NDArray[np.floating]
Mat3 = Array
Vec3 = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class ChartCoordinates:
    alpha: float
    beta: float
    lam: float
    singular: bool
    alternatives: tuple[tuple[float, float, float], ...]


@dataclass(frozen=True, slots=True)
class SphericalClosureChart:
    chart_id: str
    basis: Mat3
    reference: Mat3
    sequence: str = "ZYZ"
    singularity_tol: float = 1e-6

    @classmethod
    def from_record(cls, record: SphericalClosureChartRecord) -> SphericalClosureChart:
        return cls(
            chart_id=record.chart_id,
            basis=np.asarray(record.basis, dtype=float),
            reference=np.asarray(record.reference, dtype=float),
            sequence=record.sequence,
            singularity_tol=record.singularity_tol,
        )

    def compose(self, alpha: float, beta: float, lam: float) -> Mat3:
        relative = Rotation.from_euler("zyz", [alpha, beta, lam]).as_matrix()
        return np.asarray(self.basis @ relative @ self.basis.T @ self.reference, dtype=float)

    def decompose(self, R: Array) -> ChartCoordinates:
        c = np.asarray(self.basis, dtype=float)
        ref = np.asarray(self.reference, dtype=float)
        rel = c.T @ np.asarray(R, dtype=float) @ ref.T @ c
        rot = Rotation.from_matrix(rel)
        alpha, beta, lam = (float(v) for v in rot.as_euler("zyz"))
        singular = bool(abs(np.sin(beta)) <= self.singularity_tol)
        alt = (
            (float(np.arctan2(np.sin(alpha + np.pi), np.cos(alpha + np.pi))), float(-beta),
             float(np.arctan2(np.sin(lam + np.pi), np.cos(lam + np.pi)))),
        )
        return ChartCoordinates(alpha=alpha, beta=beta, lam=lam, singular=singular, alternatives=alt)

    def virtual_u_axes(self, center: Vec3) -> tuple[AxisLine, AxisLine]:
        col = np.asarray(self.basis[:, 2], dtype=float).reshape(3)
        z = as_vec3(unit_vector((float(col[0]), float(col[1]), float(col[2])), name="chart z"))
        coly = np.asarray(self.basis[:, 1], dtype=float).reshape(3)
        y = as_vec3(unit_vector((float(coly[0]), float(coly[1]), float(coly[2])), name="chart y"))
        return AxisLine(center, z), AxisLine(center, y)

    def round_trip_error(self, R: Array) -> float:
        coords = self.decompose(R)
        reconstructed = self.compose(coords.alpha, coords.beta, coords.lam)
        return float(_rotation_geodesic(np.asarray(R, dtype=float), reconstructed))


def charts_from_config(records: tuple[SphericalClosureChartRecord, ...]) -> tuple[SphericalClosureChart, ...]:
    return tuple(SphericalClosureChart.from_record(item) for item in records)


def chart_quality(chart: SphericalClosureChart, R: Array) -> float:
    """Nonsingularity score ``|sin(beta)|`` in this chart."""

    coords = chart.decompose(R)
    return float(abs(np.sin(coords.beta)))


def canonical_chart(
    charts: tuple[SphericalClosureChart, ...] | list[SphericalClosureChart],
    R: Array,
    *,
    policy: ChartAtlasPolicy,
    tie_break_order: tuple[str, ...] | None = None,
) -> str | None:
    """Responsible chart: max ``|sin(beta)|`` among nonsingular charts.

    Ties break by ``tie_break_order`` (configured chart-id order). All-singular
    orientations return ``None`` and are not seeded.
    """

    if policy.canonical_assignment != "max_abs_sin_beta":
        raise ValueError(f"unsupported canonical_assignment {policy.canonical_assignment}")
    order = tie_break_order if tie_break_order is not None else policy.chart_ids
    rank = {chart_id: i for i, chart_id in enumerate(order)}
    eligible: list[tuple[str, float]] = []
    for chart in charts:
        quality = chart_quality(chart, R)
        if quality > policy.singularity_margin:
            eligible.append((chart.chart_id, quality))
    if not eligible:
        return None
    eligible.sort(key=lambda item: (-item[1], rank.get(item[0], 10**9), item[0]))
    return eligible[0][0]


def charts_in_overlap_band(
    charts: tuple[SphericalClosureChart, ...] | list[SphericalClosureChart],
    R: Array,
    *,
    policy: ChartAtlasPolicy,
    canonical_id: str | None = None,
) -> tuple[str, ...]:
    """Charts within ``overlap_margin`` of the canonical quality. Not occupancy."""

    responsible = canonical_id
    if responsible is None:
        responsible = canonical_chart(charts, R, policy=policy)
    if responsible is None:
        return ()
    by_id = {chart.chart_id: chart for chart in charts}
    peak = chart_quality(by_id[responsible], R)
    band: list[str] = []
    for chart in charts:
        quality = chart_quality(chart, R)
        if quality > policy.singularity_margin and abs(quality - peak) <= policy.overlap_margin:
            band.append(chart.chart_id)
    return tuple(band)
