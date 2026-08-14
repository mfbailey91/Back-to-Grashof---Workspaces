"""V06A1: one local hexagonal chart of a spatial-5R fixed-position parent.

Representation status is ``LOCAL_PATCH``. This is not a complete parent
component, not an ``S^2`` coverage claim, and not a ``DecompositionCertificate``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .fixed_position import (
    JACOBIAN_FD_ERROR_TOL,
    JACOBIAN_FD_STEP_RAD,
    POSITION_RESIDUAL_TOL_M,
    pose_fixed_position_problem,
)
from .implicit_manifold import (
    ChartRecord,
    TaskEvaluation,
    build_hexagonal_chart,
    orthonormal_tangent_basis,
)
from .jacobians import (
    central_difference_jacobians,
    matrix_rank_report,
    pointing_jacobian,
    position_jacobian,
)
from .open_chain import OpenChainModel
from .v06_corpus import Spatial5RCorpusEntry, build_generic_5r

Array = NDArray[np.floating]

LOCAL_CHART_RADIUS_RAD = 0.18
LOCAL_CHART_ID = "generic_5r_local_hex_000"


class ParentRepresentationStatus(str, Enum):
    """How completely the source parent is represented. Not a certificate."""

    SEED_ONLY = "SEED_ONLY"
    LOCAL_PATCH = "LOCAL_PATCH"
    ATLAS_OPEN_FRONTIER = "ATLAS_OPEN_FRONTIER"
    CLOSED_COMPONENT_AT_DECLARED_RESOLUTION = "CLOSED_COMPONENT_AT_DECLARED_RESOLUTION"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class FixedPositionParentProblem:
    """Implicit manifold ``p(q)-p*=0`` on an open serial chain."""

    model: OpenChainModel
    p_star: tuple[float, float, float]
    problem_id: str
    ambient_dimension: int
    constraint_dimension: int = 3
    intrinsic_dimension: int = 2
    coordinate_names: tuple[str, ...] = ()
    periodic_coordinates: tuple[bool, ...] = ()

    @classmethod
    def from_model(cls, model: OpenChainModel, q0: tuple[float, ...]) -> FixedPositionParentProblem:
        posed = pose_fixed_position_problem(model, q0)
        n = model.n_joints
        return cls(
            model=model,
            p_star=posed.p_star,
            problem_id=f"{model.architecture_id}_fixed_position_parent",
            ambient_dimension=n,
            coordinate_names=tuple(f"q{i + 1}" for i in range(n)),
            periodic_coordinates=tuple(True for _ in range(n)),
        )

    def residual(self, x: Array) -> Array:
        q = tuple(float(v) for v in np.asarray(x, dtype=float).reshape(-1))
        state = self.model.chain.evaluate(q)
        return np.asarray(state.p, dtype=float) - np.asarray(self.p_star, dtype=float)

    def jacobian(self, x: Array) -> Array:
        q = tuple(float(v) for v in np.asarray(x, dtype=float).reshape(-1))
        return position_jacobian(self.model.chain, q)

    def evaluate_task(self, x: Array) -> TaskEvaluation:
        q = tuple(float(v) for v in np.asarray(x, dtype=float).reshape(-1))
        state = self.model.chain.evaluate(q)
        rflat = tuple(float(v) for v in np.asarray(state.R, dtype=float).reshape(-1))
        d = tuple(float(v) for v in np.asarray(state.d, dtype=float).reshape(-1))
        return TaskEvaluation(
            values=rflat + d,
            labels=tuple(f"R{i}" for i in range(9)) + ("dx", "dy", "dz"),
            notes=("orientation and pointing at q; not a coverage certificate",),
        )


@dataclass(frozen=True, slots=True)
class ParentVertexDiagnostics:
    """Per-vertex parent and pointing-rank diagnostics (separate claims)."""

    q: tuple[float, ...]
    u: tuple[float, float]
    p_residual_m: float | None
    np_shape: tuple[int, int]
    rank_jp: int
    nullity_jp: int
    jp_singular_values: tuple[float, ...]
    rank_jd_np: int
    jd_np_singular_values: tuple[float, ...]
    pointing: tuple[float, float, float]
    condition_number: float | None
    accepted: bool
    rejection_reason: str | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "q": list(self.q),
            "u": list(self.u),
            "p_residual_m": self.p_residual_m,
            "np_shape": list(self.np_shape),
            "rank_jp": self.rank_jp,
            "nullity_jp": self.nullity_jp,
            "jp_singular_values": list(self.jp_singular_values),
            "rank_jd_np": self.rank_jd_np,
            "jd_np_singular_values": list(self.jd_np_singular_values),
            "pointing": list(self.pointing),
            "condition_number": self.condition_number,
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
        }


@dataclass(frozen=True, slots=True)
class FixedPositionParentResult:
    """Source-parent representation. Not a DecompositionCertificate."""

    architecture_id: str
    p_star: tuple[float, float, float]
    representation_status: ParentRepresentationStatus
    component_ids: tuple[str, ...]
    fiber_ids: tuple[str, ...]
    chart: ChartRecord | None
    vertices: tuple[ParentVertexDiagnostics, ...]
    seed_q: tuple[float, ...]
    seed_fd_jp_error: float
    seed_fd_verified: bool
    joint_limits: str
    max_p_residual_m: float | None
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "p_star": list(self.p_star),
            "representation_status": self.representation_status.value,
            "certificate_status": None,
            "component_ids": list(self.component_ids),
            "fiber_ids": list(self.fiber_ids),
            "chart": None if self.chart is None else self.chart.to_json_dict(),
            "vertices": [v.to_json_dict() for v in self.vertices],
            "seed_q": list(self.seed_q),
            "seed_fd_jp_error": self.seed_fd_jp_error,
            "seed_fd_verified": self.seed_fd_verified,
            "joint_limits": self.joint_limits,
            "max_p_residual_m": self.max_p_residual_m,
            "notes": list(self.notes),
        }


def _vertex_diagnostics(
    problem: FixedPositionParentProblem,
    q: Array,
    u: tuple[float, float],
    *,
    condition_number: float | None,
    accepted: bool,
    rejection_reason: str | None,
) -> ParentVertexDiagnostics:
    q_t = tuple(float(v) for v in np.asarray(q, dtype=float).reshape(-1))
    state = problem.model.chain.evaluate(q_t)
    residual = float(np.linalg.norm(np.asarray(state.p) - np.asarray(problem.p_star)))
    jp = position_jacobian(problem.model.chain, q_t)
    jd = pointing_jacobian(problem.model.chain, q_t)
    report_p = matrix_rank_report(jp)
    n_p = orthonormal_tangent_basis(jp, expected_nullity=problem.intrinsic_dimension)
    jd_np = jd @ n_p
    report_d = matrix_rank_report(jd_np)
    return ParentVertexDiagnostics(
        q=q_t,
        u=u,
        p_residual_m=residual,
        np_shape=(int(n_p.shape[0]), int(n_p.shape[1])),
        rank_jp=report_p.rank,
        nullity_jp=report_p.nullity,
        jp_singular_values=report_p.singular_values,
        rank_jd_np=report_d.rank,
        jd_np_singular_values=report_d.singular_values,
        pointing=tuple(float(v) for v in np.asarray(state.d, dtype=float).reshape(-1)),
        condition_number=condition_number,
        accepted=accepted and residual <= POSITION_RESIDUAL_TOL_M,
        rejection_reason=rejection_reason,
    )


def build_generic_5r_local_patch(
    entry: Spatial5RCorpusEntry | None = None,
    *,
    radius: float = LOCAL_CHART_RADIUS_RAD,
) -> FixedPositionParentResult:
    """One hexagonal chart of ``generic_5r`` at the regular seed. Not an atlas."""

    corpus = entry or build_generic_5r()
    model = corpus.model
    q0 = corpus.regular_q
    problem = FixedPositionParentProblem.from_model(model, q0)
    jp0 = position_jacobian(model.chain, q0)
    jp_fd, _jd_fd = central_difference_jacobians(model.chain, q0, JACOBIAN_FD_STEP_RAD)
    fd_error = float(np.linalg.norm(jp0 - jp_fd, ord="fro"))
    fd_ok = fd_error <= JACOBIAN_FD_ERROR_TOL

    chart = build_hexagonal_chart(
        problem,
        np.asarray(q0, dtype=float),
        chart_id=LOCAL_CHART_ID,
        radius=radius,
        n_rings=1,
    )
    vertices: list[ParentVertexDiagnostics] = []
    for sample in chart.samples:
        if sample.correction.x is None:
            vertices.append(
                ParentVertexDiagnostics(
                    q=q0,
                    u=sample.u,
                    p_residual_m=None,
                    np_shape=(5, 0),
                    rank_jp=0,
                    nullity_jp=5,
                    jp_singular_values=(),
                    rank_jd_np=0,
                    jd_np_singular_values=(),
                    pointing=(0.0, 0.0, 0.0),
                    condition_number=sample.correction.condition_number,
                    accepted=False,
                    rejection_reason=sample.correction.rejection_reason,
                )
            )
            continue
        vertices.append(
            _vertex_diagnostics(
                problem,
                np.asarray(sample.correction.x, dtype=float),
                sample.u,
                condition_number=sample.correction.condition_number,
                accepted=sample.correction.accepted,
                rejection_reason=sample.correction.rejection_reason,
            )
        )
    accepted_residuals = [v.p_residual_m for v in vertices if v.accepted and v.p_residual_m is not None]
    status = (
        ParentRepresentationStatus.LOCAL_PATCH
        if chart.accepted and accepted_residuals
        else ParentRepresentationStatus.REJECTED
    )
    return FixedPositionParentResult(
        architecture_id=model.architecture_id,
        p_star=problem.p_star,
        representation_status=status,
        component_ids=(),
        fiber_ids=(),
        chart=chart,
        vertices=tuple(vertices),
        seed_q=tuple(float(v) for v in q0),
        seed_fd_jp_error=fd_error,
        seed_fd_verified=fd_ok,
        joint_limits="not_modeled",
        max_p_residual_m=max(accepted_residuals) if accepted_residuals else None,
        notes=(
            "V06A1 LOCAL_PATCH: one hexagonal chart at a regular generic_5r seed.",
            "Not a complete parent component and not S^2 coverage.",
            "rank(Jd Np) is reported separately from rank(Jp).",
            "Joint limits not_modeled; coordinates treated as T^5.",
            "No fibers or closed-mechanism children are emitted.",
        ),
    )


def parent_local_summary(result: FixedPositionParentResult) -> dict[str, Any]:
    ranks = [v.rank_jd_np for v in result.vertices if v.accepted]
    return {
        "architecture_id": result.architecture_id,
        "representation_status": result.representation_status.value,
        "chart_id": None if result.chart is None else result.chart.chart_id,
        "chart_count": 0 if result.chart is None else 1,
        "accepted_sample_count": sum(1 for v in result.vertices if v.accepted),
        "max_p_residual_m": result.max_p_residual_m,
        "pointing_rank_min": min(ranks) if ranks else None,
        "pointing_rank_max": max(ranks) if ranks else None,
        "component_ids": list(result.component_ids),
        "fiber_ids": list(result.fiber_ids),
        "joint_limits": result.joint_limits,
    }
