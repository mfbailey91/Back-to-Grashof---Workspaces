"""Orientation and pointing images along a fixed-position fiber.

Conventions
-----------
- Orientation is stored as a ``3x3`` rotation matrix in ``SO(3)``.
- Quaternions are ``(w, x, y, z)`` with unit norm; adjacent samples are
  sign-stabilized so ``q_k · q_{k-1} ≥ 0``.
- Rotation vectors are ``θ u`` with ``θ ∈ [0, π]`` from the matrix logarithm.
- Pointing ``d`` is the selected unit tool axis in world frame.
- These objects are orientation/pointing *curve truth*, not coverage
  certificates for ``SO(3)`` or ``S²``.

V05 classifies the observed one-dimensional image so a pure terminal-roll orbit
cannot be confused with a nontrivial spatial-4R pointing curve.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from itertools import pairwise
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .fixed_position_continuation import FixedPositionFiberResult, FixedPositionStep
from .jacobians import matrix_rank_report, position_jacobian
from .open_chain import OpenChainModel
from .rotations import axis_angle_from_rotation
from .serial_chain import SerialRevoluteChain

Mat = NDArray[np.floating]
Vec = NDArray[np.floating]

NEAR_SINGULAR_SIGMA_TOL = 1e-6
POINTING_MATCH_TOL = 1e-6
ORIENTATION_MATCH_TOL = 1e-6
MULTIPLICITY_SCAN_CAP = 200
CURVE_ZERO_TOL_RAD = 1e-8
POINTING_CURVE_TOL_RAD = 1e-5
FIXED_AXIS_DRIFT_TOL_RAD = 5e-3

CURVE_TYPES = (
    "PURE_TERMINAL_ROLL",
    "FIXED_AXIS_ONE_PARAMETER_SUBGROUP",
    "NONTRIVIAL_POINTING_CURVE",
    "DEGENERATE_ORIENTATION_POINT",
    "SINGULAR_OR_EMPTY",
    "UNRESOLVED",
)


@dataclass(frozen=True, slots=True)
class OrientationSample:
    sigma: float
    R: tuple[tuple[float, float, float], ...]
    quaternion: tuple[float, float, float, float]
    rotvec: tuple[float, float, float]
    d: tuple[float, float, float]
    rank_jp: int
    nullity_jp: int
    sigma_min_jp: float
    near_singular: bool
    regular: bool


@dataclass(frozen=True, slots=True)
class MultiplicityReport:
    same_pointing_distinct_orientation_pairs: int
    same_orientation_distinct_pointing_pairs: int
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OrientationCurveMetrics:
    curve_type: str
    orientation_path_length_rad: float
    pointing_path_length_rad: float
    max_pointing_displacement_rad: float
    incremental_axis_drift_rad: float | None
    first_increment_axis_world: tuple[float, float, float] | None
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OrientationImageResult:
    architecture_id: str
    component_id: str
    p_star: tuple[float, float, float]
    status: str
    samples: tuple[OrientationSample, ...]
    multiplicity: MultiplicityReport
    near_singular_count: int
    metrics: OrientationCurveMetrics
    notes: tuple[str, ...]

    @property
    def curve_type(self) -> str:
        return self.metrics.curve_type

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "component_id": self.component_id,
            "p_star": self.p_star,
            "status": self.status,
            "curve_type": self.curve_type,
            "sample_count": len(self.samples),
            "near_singular_count": self.near_singular_count,
            "metrics": asdict(self.metrics),
            "multiplicity": asdict(self.multiplicity),
            "notes": list(self.notes),
            "samples": [asdict(sample) for sample in self.samples],
        }


@dataclass(frozen=True, slots=True)
class PointingImageResult:
    architecture_id: str
    component_id: str
    p_star: tuple[float, float, float]
    status: str
    points: tuple[tuple[float, float, float], ...]
    sigma: tuple[float, ...]
    path_length_rad: float
    max_displacement_rad: float
    notes: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "component_id": self.component_id,
            "p_star": self.p_star,
            "status": self.status,
            "point_count": len(self.points),
            "points": [list(p) for p in self.points],
            "sigma": list(self.sigma),
            "path_length_rad": self.path_length_rad,
            "max_displacement_rad": self.max_displacement_rad,
            "notes": list(self.notes),
        }


def _clamped_acos(value: float) -> float:
    return float(math.acos(max(-1.0, min(1.0, value))))


def rotation_matrix_to_quaternion(
    R: Mat | tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float, float]:
    """Convert ``R ∈ SO(3)`` to unit quaternion ``(w, x, y, z)``."""
    m = np.asarray(R, dtype=float).reshape(3, 3)
    trace = float(np.trace(m))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    quat = np.array([w, x, y, z], dtype=float)
    quat /= float(np.linalg.norm(quat))
    if quat[0] < 0.0:
        quat = -quat
    return (float(quat[0]), float(quat[1]), float(quat[2]), float(quat[3]))


def quaternion_to_rotation_matrix(q: tuple[float, float, float, float] | Vec) -> Mat:
    """Convert unit quaternion ``(w, x, y, z)`` to ``R ∈ SO(3)``."""
    w, x, y, z = (float(v) for v in np.asarray(q, dtype=float).reshape(4))
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=float,
    )


def rotation_matrix_to_rotvec(
    R: Mat | tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    """Return rotation vector ``θ u`` with ``θ ∈ [0, π]``."""
    axis, angle = axis_angle_from_rotation(np.asarray(R, dtype=float).reshape(3, 3))
    vec = axis * float(angle)
    return (float(vec[0]), float(vec[1]), float(vec[2]))


def _stabilize_quaternion_sequence(
    quats: list[tuple[float, float, float, float]],
) -> list[tuple[float, float, float, float]]:
    if not quats:
        return []
    out = [quats[0]]
    prev = np.asarray(quats[0], dtype=float)
    for q in quats[1:]:
        cur = np.asarray(q, dtype=float)
        if float(np.dot(prev, cur)) < 0.0:
            cur = -cur
        out.append((float(cur[0]), float(cur[1]), float(cur[2]), float(cur[3])))
        prev = cur
    return out


def _frobenius_rotation_distance(Ra: Mat, Rb: Mat) -> float:
    return float(np.linalg.norm(Ra - Rb, ord="fro"))


def _rotation_geodesic(Ra: Mat, Rb: Mat) -> float:
    relative = Rb @ Ra.T
    return _clamped_acos((float(np.trace(relative)) - 1.0) * 0.5)


def _pointing_geodesic(a: Vec, b: Vec) -> float:
    return _clamped_acos(float(np.dot(a, b)))


def _multiplicity_report(samples: tuple[OrientationSample, ...]) -> MultiplicityReport:
    n = len(samples)
    if n < 2:
        return MultiplicityReport(0, 0, ("Fewer than two samples; multiplicity not assessed.",))
    idxs = list(range(n))
    if n > MULTIPLICITY_SCAN_CAP:
        step = max(1, n // MULTIPLICITY_SCAN_CAP)
        idxs = list(range(0, n, step))[:MULTIPLICITY_SCAN_CAP]
    same_d_diff_r = 0
    same_r_diff_d = 0
    for i_pos, i in enumerate(idxs):
        si = samples[i]
        Ri = np.asarray(si.R, dtype=float)
        di = np.asarray(si.d, dtype=float)
        for j in idxs[i_pos + 1 :]:
            sj = samples[j]
            Rj = np.asarray(sj.R, dtype=float)
            dj = np.asarray(sj.d, dtype=float)
            d_close = float(np.linalg.norm(di - dj)) <= POINTING_MATCH_TOL
            r_close = _frobenius_rotation_distance(Ri, Rj) <= ORIENTATION_MATCH_TOL
            if d_close and not r_close:
                same_d_diff_r += 1
            if r_close and not d_close:
                same_r_diff_d += 1
    return MultiplicityReport(
        same_d_diff_r,
        same_r_diff_d,
        (
            "Pairwise scan over fiber samples (possibly subsampled).",
            "same_pointing_distinct_orientation indicates roll-like multiplicity about d.",
            "Not a coverage claim.",
        ),
    )


def _curve_metrics(samples: tuple[OrientationSample, ...]) -> OrientationCurveMetrics:
    if not samples:
        return OrientationCurveMetrics(
            curve_type="SINGULAR_OR_EMPTY",
            orientation_path_length_rad=0.0,
            pointing_path_length_rad=0.0,
            max_pointing_displacement_rad=0.0,
            incremental_axis_drift_rad=None,
            first_increment_axis_world=None,
            notes=("No regular orientation samples.",),
        )

    Rs = [np.asarray(sample.R, dtype=float) for sample in samples]
    ds = [np.asarray(sample.d, dtype=float) for sample in samples]
    orientation_length = sum(_rotation_geodesic(a, b) for a, b in pairwise(Rs))
    pointing_length = sum(_pointing_geodesic(a, b) for a, b in pairwise(ds))
    max_pointing = max((_pointing_geodesic(ds[0], d) for d in ds), default=0.0)

    increment_axes: list[np.ndarray] = []
    for Ra, Rb in pairwise(Rs):
        relative_world = Rb @ Ra.T
        axis, angle = axis_angle_from_rotation(relative_world)
        if abs(float(angle)) <= CURVE_ZERO_TOL_RAD:
            continue
        axis_arr = np.asarray(axis, dtype=float)
        if increment_axes and float(np.dot(increment_axes[-1], axis_arr)) < 0.0:
            axis_arr = -axis_arr
        increment_axes.append(axis_arr)

    axis_drift: float | None = None
    first_axis: tuple[float, float, float] | None = None
    if increment_axes:
        first = increment_axes[0]
        first_axis = (float(first[0]), float(first[1]), float(first[2]))
        axis_drift = max(
            (_clamped_acos(abs(float(np.dot(first, axis)))) for axis in increment_axes),
            default=0.0,
        )

    if orientation_length <= CURVE_ZERO_TOL_RAD:
        curve_type = "DEGENERATE_ORIENTATION_POINT"
    elif pointing_length <= POINTING_CURVE_TOL_RAD and max_pointing <= POINTING_CURVE_TOL_RAD:
        curve_type = "PURE_TERMINAL_ROLL"
    elif axis_drift is not None and axis_drift <= FIXED_AXIS_DRIFT_TOL_RAD:
        curve_type = "FIXED_AXIS_ONE_PARAMETER_SUBGROUP"
    elif pointing_length > POINTING_CURVE_TOL_RAD:
        curve_type = "NONTRIVIAL_POINTING_CURVE"
    else:
        curve_type = "UNRESOLVED"

    return OrientationCurveMetrics(
        curve_type=curve_type,
        orientation_path_length_rad=float(orientation_length),
        pointing_path_length_rad=float(pointing_length),
        max_pointing_displacement_rad=float(max_pointing),
        incremental_axis_drift_rad=None if axis_drift is None else float(axis_drift),
        first_increment_axis_world=first_axis,
        notes=(
            "Path lengths are sampled geodesic sums, not global coverage measures.",
            "PURE_TERMINAL_ROLL means orientation changes while the selected pointing axis is fixed.",
            "FIXED_AXIS_ONE_PARAMETER_SUBGROUP is a numerical diagnostic, not an analytical subgroup proof.",
        ),
    )


def build_orientation_image(
    fiber: FixedPositionFiberResult,
    *,
    chain: SerialRevoluteChain | OpenChainModel | None = None,
    near_singular_tol: float = NEAR_SINGULAR_SIGMA_TOL,
) -> OrientationImageResult:
    """Build orientation-curve truth from a fixed-position fiber result."""
    notes = [
        "Orientation-curve truth only; not an SO(3) coverage certificate.",
        "A scalar angle is used only when the curve type justifies it.",
        *fiber.notes,
    ]
    serial = None
    if isinstance(chain, OpenChainModel):
        serial = chain.chain
    elif chain is not None:
        serial = chain

    accepted = [step for step in fiber.accepted_samples if step.R is not None and step.d is not None]
    if fiber.seed_audit.status != "PASS" or not accepted:
        metrics = _curve_metrics(())
        return OrientationImageResult(
            architecture_id=fiber.architecture_id,
            component_id=fiber.component_id,
            p_star=fiber.p_star,
            status="FAIL" if fiber.seed_audit.status == "FAIL" else "EMPTY",
            samples=(),
            multiplicity=MultiplicityReport(0, 0, ("No orientation samples.",)),
            near_singular_count=0,
            metrics=metrics,
            notes=(*notes, "No accepted regular fiber samples for orientation export."),
        )

    raw_quats: list[tuple[float, float, float, float]] = []
    raw_meta: list[FixedPositionStep] = []
    for step in accepted:
        assert step.R is not None
        raw_quats.append(rotation_matrix_to_quaternion(step.R))
        raw_meta.append(step)
    stable_quats = _stabilize_quaternion_sequence(raw_quats)

    samples: list[OrientationSample] = []
    for step, quat in zip(raw_meta, stable_quats, strict=True):
        assert step.R is not None and step.d is not None
        if serial is not None and step.q is not None:
            report = matrix_rank_report(position_jacobian(serial, step.q))
            sigma_min = float(report.singular_values[2]) if report.rank >= 3 else 0.0
        else:
            sigma_min = 0.0 if step.rank_jp < 3 else float("nan")
        near = step.rank_jp < 3 or (not step.regular) or (
            math.isfinite(sigma_min) and sigma_min <= near_singular_tol
        )
        samples.append(
            OrientationSample(
                sigma=step.sigma,
                R=step.R,
                quaternion=quat,
                rotvec=rotation_matrix_to_rotvec(step.R),
                d=step.d,
                rank_jp=step.rank_jp,
                nullity_jp=step.nullity_jp,
                sigma_min_jp=float(sigma_min) if math.isfinite(sigma_min) else -1.0,
                near_singular=near,
                regular=step.regular,
            )
        )

    sample_tuple = tuple(samples)
    multiplicity = _multiplicity_report(sample_tuple)
    near_count = sum(1 for sample in sample_tuple if sample.near_singular)
    metrics = _curve_metrics(sample_tuple)
    return OrientationImageResult(
        architecture_id=fiber.architecture_id,
        component_id=fiber.component_id,
        p_star=fiber.p_star,
        status="EXPORTED",
        samples=sample_tuple,
        multiplicity=multiplicity,
        near_singular_count=near_count,
        metrics=metrics,
        notes=tuple(notes),
    )


def build_pointing_image(fiber: FixedPositionFiberResult) -> PointingImageResult:
    """Build pointing-curve samples on ``S²`` from the fiber (not coverage)."""
    notes = [
        "Pointing-curve projection of the orientation image; not an S² coverage certificate.",
        *fiber.notes,
    ]
    accepted = [step for step in fiber.accepted_samples if step.d is not None]
    if fiber.seed_audit.status != "PASS" or not accepted:
        return PointingImageResult(
            architecture_id=fiber.architecture_id,
            component_id=fiber.component_id,
            p_star=fiber.p_star,
            status="FAIL" if fiber.seed_audit.status == "FAIL" else "EMPTY",
            points=(),
            sigma=(),
            path_length_rad=0.0,
            max_displacement_rad=0.0,
            notes=(*notes, "No accepted pointing samples."),
        )
    points = tuple(step.d for step in accepted if step.d is not None)
    sigma = tuple(step.sigma for step in accepted)
    d_arrays = [np.asarray(point, dtype=float) for point in points]
    path_length = sum(_pointing_geodesic(a, b) for a, b in pairwise(d_arrays))
    max_displacement = max(
        (_pointing_geodesic(d_arrays[0], d) for d in d_arrays),
        default=0.0,
    )
    return PointingImageResult(
        architecture_id=fiber.architecture_id,
        component_id=fiber.component_id,
        p_star=fiber.p_star,
        status="EXPORTED",
        points=points,
        sigma=sigma,
        path_length_rad=float(path_length),
        max_displacement_rad=float(max_displacement),
        notes=tuple(notes),
    )
