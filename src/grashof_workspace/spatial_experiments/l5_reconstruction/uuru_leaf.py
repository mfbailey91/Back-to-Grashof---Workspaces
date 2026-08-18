"""Frozen-geometry exact ``UURU`` leaf: fix chart coordinate ``lambda``.

Seven coordinates ``(alpha, beta, q1..q5)`` and six closure residuals. ``lambda``
is an immutable spec field. Physical lift is the identity map ``x[2:7]``.
Certificates contain no ``h_c`` field.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3
from grashof_workspace.spatial_experiments.branch_continuation import continue_implicit_branch
from grashof_workspace.spatial_experiments.continuation import wrap_joint_delta
from grashof_workspace.spatial_experiments.fixed_position import JACOBIAN_FD_STEP_RAD
from grashof_workspace.spatial_experiments.implicit_manifold import orthonormal_tangent_basis
from grashof_workspace.spatial_experiments.jacobians import matrix_rank_report
from grashof_workspace.spatial_experiments.open_chain import OpenChainModel
from grashof_workspace.spatial_experiments.orientation_image import (
    _pointing_geodesic,
    _rotation_geodesic,
)
from grashof_workspace.spatial_experiments.parent_atlas import wrap_periodic
from grashof_workspace.spatial_experiments.rotations import axis_angle_from_rotation
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain

from .models import (
    FamilyAdmissibilityStatus,
    LeafConstructionKind,
    NaturalLeafCertificate,
    NaturalLeafSample,
    NaturalLeafSpec,
)
from .positive_control import PositiveControlArm
from .spherical_chart import SphericalClosureChart

Array = NDArray[np.floating]
CHILD_DIM = 7
CONSTRAINT_DIM = 6
NEWTON_ITERS = 25
KIND_SEQ = ("U", "U", "R", "U")
ROLE_SEQ = ("U_v", "U_phys", "R_phys", "U_phys")


def _copy_chain(chain: SerialRevoluteChain) -> SerialRevoluteChain:
    return SerialRevoluteChain(home_axes=chain.home_axes, p0=chain.p0, d0=chain.d0, R0=chain.R0)


def _rotation_error_vec(ra: Array, rb: Array) -> Array:
    axis, angle = axis_angle_from_rotation(ra.T @ rb)
    return np.asarray(axis * float(angle), dtype=float)


def geometry_hash(chart: SphericalClosureChart, lambda_fixed: float) -> str:
    payload = {
        "chart_id": chart.chart_id,
        "sequence": chart.sequence,
        "basis": np.asarray(chart.basis).round(15).tolist(),
        "reference": np.asarray(chart.reference).round(15).tolist(),
        "lambda_fixed": float(lambda_fixed),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ClosedUURULeafProblem:
    source: OpenChainModel
    independent_chain: SerialRevoluteChain
    chart: SphericalClosureChart
    lambda_fixed: float
    p_star: tuple[float, float, float]
    problem_id: str
    ambient_dimension: int = CHILD_DIM
    constraint_dimension: int = CONSTRAINT_DIM
    periodic_coordinates: tuple[bool, ...] = (True,) * CHILD_DIM
    joint_kind_sequence: tuple[str, ...] = KIND_SEQ
    joint_role_sequence: tuple[str, ...] = ROLE_SEQ

    def __post_init__(self) -> None:
        if id(self.independent_chain) == id(self.source.chain):
            raise ValueError("independent chain must be a distinct object")
        if self.joint_role_sequence != ROLE_SEQ:
            raise ValueError("R3A instantiates only U_v-U_phys-R_phys-U_phys")

    def physical_q(self, x: Array) -> tuple[float, ...]:
        arr = np.asarray(x, dtype=float).reshape(-1)
        if arr.size != CHILD_DIM:
            raise ValueError("reduced x must have seven coordinates")
        return tuple(float(v) for v in arr[2:7])

    def virtual_R(self, x: Array) -> Array:
        return self.chart.compose(float(x[0]), float(x[1]), self.lambda_fixed)

    def residual(self, x: Array) -> Array:
        q = self.physical_q(x)
        state = self.independent_chain.evaluate(q)
        r_pos = np.asarray(state.p, dtype=float) - np.asarray(self.p_star, dtype=float)
        r_ori = _rotation_error_vec(self.virtual_R(x), np.asarray(state.R, dtype=float))
        return np.concatenate([r_pos, r_ori])

    def jacobian(self, x: Array) -> Array:
        x0 = np.asarray(x, dtype=float).reshape(-1)
        r0 = self.residual(x0)
        jac = np.zeros((CONSTRAINT_DIM, CHILD_DIM), dtype=float)
        eps = JACOBIAN_FD_STEP_RAD
        for i in range(CHILD_DIM):
            xp = x0.copy()
            xp[i] += eps
            jac[:, i] = (self.residual(xp) - r0) / eps
        return jac


def correct_uuru(problem: ClosedUURULeafProblem, x: Array) -> tuple[Array, bool, float]:
    y = wrap_periodic(np.asarray(x, dtype=float), problem.periodic_coordinates)
    for _ in range(NEWTON_ITERS):
        r = problem.residual(y)
        nr = float(np.linalg.norm(r))
        if nr <= 1e-10:
            return y, True, nr
        jac = problem.jacobian(y)
        dq, *_ = np.linalg.lstsq(jac, -r, rcond=None)
        y = wrap_periodic(y + dq, problem.periodic_coordinates)
    nr = float(np.linalg.norm(problem.residual(y)))
    return y, False, nr


def problem_from_source_seed(
    arm: PositiveControlArm,
    chart: SphericalClosureChart,
    q_source: tuple[float, ...],
    p_star: tuple[float, float, float],
    *,
    leaf_id: str,
    lambda_fixed: float | None = None,
) -> tuple[ClosedUURULeafProblem, Array] | None:
    state = arm.chain.evaluate(q_source)
    coords = chart.decompose(state.R)
    if coords.singular:
        return None
    frozen = float(coords.lam if lambda_fixed is None else lambda_fixed)
    problem = ClosedUURULeafProblem(
        source=arm.model,
        independent_chain=_copy_chain(arm.chain),
        chart=chart,
        lambda_fixed=frozen,
        p_star=p_star,
        problem_id=leaf_id,
    )
    x0 = np.array((coords.alpha, coords.beta, *q_source), dtype=float)
    x, ok, _ = correct_uuru(problem, x0)
    if not ok:
        return None
    return problem, x


def child_tangent(problem: ClosedUURULeafProblem, x: Array) -> Array:
    basis = orthonormal_tangent_basis(problem.jacobian(x), expected_nullity=1)
    phys = np.asarray(basis[:, 0][2:7], dtype=float)
    norm = float(np.linalg.norm(phys))
    if norm <= 0.0:
        raise ValueError("physical child tangent vanished")
    return phys / norm


def tangent_principal_angle(a: Array, b: Array) -> float:
    ua = np.asarray(a, dtype=float).reshape(-1)
    ub = np.asarray(b, dtype=float).reshape(-1)
    na = float(np.linalg.norm(ua))
    nb = float(np.linalg.norm(ub))
    if na <= 0.0 or nb <= 0.0:
        raise ValueError("tangent vanished")
    return float(np.arccos(float(np.clip(abs(np.dot(ua / na, ub / nb)), 0.0, 1.0))))


def _sample(problem: ClosedUURULeafProblem, x: Array, s: float) -> NaturalLeafSample:
    q = problem.physical_q(x)
    state_i = problem.independent_chain.evaluate(q)
    state_s = problem.source.chain.evaluate(q)
    rv = problem.virtual_R(x)
    recovered = problem.chart.decompose(rv)
    lam_err = abs(float(np.arctan2(np.sin(recovered.lam - problem.lambda_fixed), np.cos(recovered.lam - problem.lambda_fixed))))
    for alt in recovered.alternatives:
        lam_err = min(
            lam_err,
            abs(float(np.arctan2(np.sin(alt[2] - problem.lambda_fixed), np.cos(alt[2] - problem.lambda_fixed)))),
        )
    report = matrix_rank_report(problem.jacobian(x))
    lift = float(np.linalg.norm(wrap_joint_delta(q, tuple(float(v) for v in x[2:7]))))
    return NaturalLeafSample(
        s=float(s),
        x=tuple(float(v) for v in x),
        q_source=q,
        pointing=as_vec3(state_i.d),
        lambda_recovered=recovered.lam,
        closure_residual=float(np.linalg.norm(problem.residual(x))),
        position_residual_m=float(np.linalg.norm(np.asarray(state_i.p) - np.asarray(problem.p_star))),
        orientation_error_rad=float(_rotation_geodesic(rv, np.asarray(state_i.R))),
        pointing_error_rad=float(_pointing_geodesic(state_i.d, state_s.d)),
        joint_lift_error_rad=lift,
        family_coordinate_error_rad=lam_err,
        rank_j=report.rank,
        nullity_j=report.nullity,
        chart_singularity=bool(recovered.singular),
    )


def continue_uuru_leaf(
    problem: ClosedUURULeafProblem,
    x_seed: Array,
    *,
    max_steps: int = 24,
    step_size: float = 0.08,
) -> tuple[tuple[NaturalLeafSample, ...], str, bool]:
    x, ok, _ = correct_uuru(problem, x_seed)
    if not ok:
        return (), "unresolved", False
    report = matrix_rank_report(problem.jacobian(x))
    if report.rank != 6 or report.nullity != 1:
        return (_sample(problem, x, 0.0),), "singular", False
    trace = continue_implicit_branch(
        problem,
        x,
        branch_id=f"{problem.problem_id}_leaf",
        max_steps=max_steps,
        step_size=step_size,
    )
    samples = [
        _sample(problem, np.asarray(step.x, dtype=float), step.s)
        for step in trace.steps
        if step.accepted and step.x is not None
    ]
    samples.sort(key=lambda item: item.s)
    return tuple(samples), trace.branch_status, trace.returned


def issue_leaf_certificate(
    spec: NaturalLeafSpec,
    samples: tuple[NaturalLeafSample, ...],
    *,
    branch_status: str,
    returned: bool,
    position_tol: float,
    orientation_tol: float,
    pointing_tol: float,
    lift_tol: float,
    lambda_tol: float,
    closure_tol: float,
) -> NaturalLeafCertificate:
    if not samples:
        return NaturalLeafCertificate(
            spec=spec,
            construction_status="UNRESOLVED",
            leaf_component_status="UNRESOLVED",
            family_admissibility_status=FamilyAdmissibilityStatus.UNRESOLVED,
            component_scope="none",
            branch_status=branch_status,
            returned=returned,
            samples=(),
            max_closure_residual=None,
            max_position_residual_m=None,
            max_orientation_error_rad=None,
            max_pointing_error_rad=None,
            max_joint_lift_error_rad=None,
            max_family_coordinate_error_rad=None,
            reseed=None,
            transversality=None,
            chart_overlap_status="UNRESOLVED",
            accepted_for_reconstruction=False,
            failure_or_scope_reason="no samples",
        )
    max_closure = max(s.closure_residual for s in samples)
    max_pos = max(s.position_residual_m for s in samples)
    max_ori = max(s.orientation_error_rad for s in samples)
    max_pnt = max(s.pointing_error_rad for s in samples)
    max_lift = max(s.joint_lift_error_rad for s in samples)
    max_lam = max(s.family_coordinate_error_rad for s in samples)
    exact = (
        max_closure <= closure_tol
        and max_pos <= position_tol
        and max_ori <= orientation_tol
        and max_pnt <= pointing_tol
        and max_lift <= lift_tol
        and max_lam <= lambda_tol
        and all(not s.chart_singularity for s in samples)
    )
    if exact and returned:
        status = "EXACT_ON_COMPONENT"
        scope = "component"
        reason = "complete returned branch with embedding checks"
    elif exact:
        status = "LOCAL_ONLY"
        scope = "local_branch"
        reason = "embedding checks pass; component incomplete"
    else:
        status = "REJECTED"
        scope = "none"
        reason = "embedding or lambda residual failed"
    return NaturalLeafCertificate(
        spec=spec,
        construction_status="virtual_orientation_coordinate",
        leaf_component_status=status,
        family_admissibility_status=FamilyAdmissibilityStatus.UNRESOLVED,
        component_scope=scope,
        branch_status=branch_status,
        returned=returned,
        samples=samples,
        max_closure_residual=max_closure,
        max_position_residual_m=max_pos,
        max_orientation_error_rad=max_ori,
        max_pointing_error_rad=max_pnt,
        max_joint_lift_error_rad=max_lift,
        max_family_coordinate_error_rad=max_lam,
        reseed=None,
        transversality=None,
        chart_overlap_status="UNRESOLVED",
        accepted_for_reconstruction=False,
        failure_or_scope_reason=reason,
    )


def leaf_spec_for(
    probe_id: str,
    chart: SphericalClosureChart,
    lambda_fixed: float,
    p_star: tuple[float, float, float],
    leaf_id: str,
) -> NaturalLeafSpec:
    return NaturalLeafSpec(
        leaf_id=leaf_id,
        probe_id=probe_id,
        construction_kind=LeafConstructionKind.VIRTUAL_ORIENTATION_COORDINATE,
        chart_id=chart.chart_id,
        lambda_fixed=lambda_fixed,
        p_star=p_star,
        geometry_hash=geometry_hash(chart, lambda_fixed),
        joint_kind_sequence=KIND_SEQ,
        joint_role_sequence=ROLE_SEQ,
    )
