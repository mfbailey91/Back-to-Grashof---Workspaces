"""Parent-first pointing-slice prototype: ``S_v`` parent → task-derived ``U_v`` chart.

This module is retained as a V08-oriented prototype, not active V05 source-chain
evidence.  It distinguishes five separate checks:

1. parent pointing-level-set regularity;
2. local virtual-U chart validity;
3. child reference closure/mobility;
4. parent-child tangent agreement;
5. parent-child branch equivalence.

The previous implementation collapsed these into one ``PASS`` even though the
child-tool tangent residual was much larger than tolerance and no global branch
comparison had been performed.  The statuses are now exported independently.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    IntersectingPairsAligned6R,
)
from grashof_workspace.spatial_experiments.axis_geometry import (
    line_closest_points,
    line_line_distance,
)
from grashof_workspace.spatial_experiments.fiber_constraints import (
    PRIMARY_N,
    FiberIndependenceReport,
    fiber_independence_report,
    pointing_scalar,
    reduced_fiber_tangent,
)
from grashof_workspace.spatial_experiments.fiber_continuation import FiberSegment, continue_fiber
from grashof_workspace.spatial_experiments.jacobians import pointing_jacobian
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain

from .closure import audit_reference_geometry, closure_jacobian, null_tangent
from .continuation import continue_branch
from .geometry import (
    Frame3,
    JointGeometry,
    JointKind,
    LinkGeometry,
    SpatialFourBarGeometry,
    Vec3,
    cross,
    dot,
    normalize,
    scale,
)
from .models import OrderedFamily

Array = NDArray[np.floating]

TANGENT_RESIDUAL_TOL = 5e-3
POINTING_CURVE_TOL = 5e-3
H_RESIDUAL_TOL = 1e-9
PAIR_DISTANCE_TOL_M = 1e-9
CHILD_CLOSURE_TOL = 1e-9


@dataclass(frozen=True)
class SliceDefinition:
    """Explicit pointing-slice metadata."""

    n: Vec3
    c: float
    formula: str
    architecture: str
    q0: tuple[float, ...]
    p0: Vec3
    d0: Vec3
    q6_star: float


@dataclass(frozen=True)
class VirtualUAxes:
    """Orthonormal local tool-U chart at a pointing-fiber seed."""

    r_a: Vec3
    r_b: Vec3
    d: Vec3
    n: Vec3
    convention: str = "R_b=normalize(n×d); R_a=normalize(R_b×d); frame=(R_a,R_b,d)"


@dataclass(frozen=True)
class FiberEquivalenceResiduals:
    parent_rank: int
    parent_nullity: int
    dh_dq6: float
    h_residual_max: float
    tangent_pointing_residual: float
    child_tool_tangent_residual: float
    pointing_curve_residual: float
    child_closure_norm: float
    child_rank: int
    child_nullity: int
    branch_sample_count: int
    lifted_alpha_dot: float
    lifted_beta_dot: float


@dataclass(frozen=True)
class FiberEquivalenceStatuses:
    parent_slice_status: str
    virtual_u_chart_status: str
    child_reference_closure_status: str
    parent_child_tangent_status: str
    parent_child_branch_status: str
    overall_status: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PointingSliceFiberResult:
    slice_id: str
    family: str
    parent_line: str
    slice_definition: SliceDefinition
    virtual_u: VirtualUAxes
    geometry: SpatialFourBarGeometry
    independence: FiberIndependenceReport
    fiber_segment_accepted: int
    equivalence_residuals: FiberEquivalenceResiduals
    equivalence_statuses: FiberEquivalenceStatuses
    fiber_equivalence_status: str
    slice_provenance: str
    program_role: str
    notes: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "family": self.family,
            "parent_line": self.parent_line,
            "slice_definition": asdict(self.slice_definition),
            "virtual_u": asdict(self.virtual_u),
            "independence": asdict(self.independence),
            "fiber_segment_accepted": self.fiber_segment_accepted,
            "equivalence_residuals": asdict(self.equivalence_residuals),
            "equivalence_statuses": asdict(self.equivalence_statuses),
            "fiber_equivalence_status": self.fiber_equivalence_status,
            "slice_provenance": self.slice_provenance,
            "program_role": self.program_role,
            "notes": list(self.notes),
            "geometry_centers": [joint.center for joint in self.geometry.joints],
            "geometry_joint_kinds": [joint.kind.value for joint in self.geometry.joints],
        }


def _as_vec3(values: Array | tuple[float, ...] | list[float]) -> Vec3:
    arr = np.asarray(values, dtype=float).reshape(3)
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def derive_virtual_u_axes(n: Vec3 | Array, d: Vec3 | Array) -> VirtualUAxes:
    """Return orthonormal ``(R_a, R_b, d)`` for a local pointing chart."""
    n_hat = normalize(_as_vec3(n))
    d_hat = normalize(_as_vec3(d))
    cross_nd = cross(n_hat, d_hat)
    if math.sqrt(dot(cross_nd, cross_nd)) <= 1e-8:
        raise ValueError("cannot derive virtual U axes when n is parallel to d")
    r_b = normalize(cross_nd)
    r_a = normalize(cross(r_b, d_hat))
    if dot(cross(r_a, r_b), d_hat) < 0.0:
        r_a = scale(r_a, -1.0)
    return VirtualUAxes(r_a=r_a, r_b=r_b, d=d_hat, n=n_hat)


def _orthonormal_u_frame(w0: Vec3, w1: Vec3) -> Frame3:
    """Build a U frame whose x/y span the plane of ``w0``, ``w1``."""
    x_axis = normalize(w0)
    y_raw = cross(cross(x_axis, w1), x_axis)
    if math.sqrt(dot(y_raw, y_raw)) <= 1e-12:
        helper = (0.0, 0.0, 1.0) if abs(x_axis[2]) < 0.9 else (0.0, 1.0, 0.0)
        y_raw = cross(x_axis, helper)
    y_axis = normalize(y_raw)
    z_axis = normalize(cross(x_axis, y_axis))
    return (x_axis, y_axis, z_axis)


def _revolute_frame(direction: Vec3) -> Frame3:
    z_axis = normalize(direction)
    helper = (0.0, 0.0, 1.0) if abs(z_axis[2]) < 0.9 else (0.0, 1.0, 0.0)
    x_axis = normalize(cross(helper, z_axis))
    y_axis = normalize(cross(z_axis, x_axis))
    return (x_axis, y_axis, z_axis)


def build_uuur_child_from_suur_seed(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    virtual_u: VirtualUAxes,
) -> SpatialFourBarGeometry:
    """Emit a candidate ``UUUR`` reference geometry from one SUUR seed chart."""
    q_t = tuple(float(x) for x in np.asarray(q0, dtype=float).reshape(6))
    state = chain.evaluate(q_t)
    axes = chain.current_axes(q_t)
    dist_ua = line_line_distance(axes[0], axes[1])
    dist_ub = line_line_distance(axes[2], axes[3])
    if dist_ua > PAIR_DISTANCE_TOL_M or dist_ub > PAIR_DISTANCE_TOL_M:
        raise ValueError(
            f"SUUR pairs are not concurrent at seed (UA={dist_ua}, UB={dist_ub}); "
            "free-SUUR extraction remains unverified"
        )
    ua_center = _as_vec3(line_closest_points(axes[0], axes[1])[0])
    ub_center = _as_vec3(line_closest_points(axes[2], axes[3])[0])
    r5_center = _as_vec3(axes[4].r)
    tool_center = _as_vec3(state.p)

    joints = (
        JointGeometry(
            name="J1_tool_Uv",
            kind=JointKind.U,
            center=tool_center,
            frame=(virtual_u.r_a, virtual_u.r_b, virtual_u.d),
        ),
        JointGeometry(
            name="J2_UA",
            kind=JointKind.U,
            center=ua_center,
            frame=_orthonormal_u_frame(_as_vec3(axes[0].w), _as_vec3(axes[1].w)),
        ),
        JointGeometry(
            name="J3_UB",
            kind=JointKind.U,
            center=ub_center,
            frame=_orthonormal_u_frame(_as_vec3(axes[2].w), _as_vec3(axes[3].w)),
        ),
        JointGeometry(
            name="J4_R5",
            kind=JointKind.R,
            center=r5_center,
            frame=_revolute_frame(_as_vec3(axes[4].w)),
        ),
    )
    links = (
        LinkGeometry("L12", 0, 1),
        LinkGeometry("L23", 1, 2),
        LinkGeometry("L34", 2, 3),
        LinkGeometry("L41_ground", 3, 0),
    )
    geometry = SpatialFourBarGeometry(
        family=OrderedFamily.UUUR,
        joints=joints,
        links=links,
        ground_link=3,
        tool_joint=0,
    )
    errors = geometry.validation_errors()
    if errors:
        raise ValueError(f"invalid task-derived UUUR geometry: {errors}")
    return geometry


def _tool_pointing_rate_from_child_tangent(
    virtual_u: VirtualUAxes,
    child_tangent: Array,
) -> Array:
    alpha_dot = float(child_tangent[0])
    beta_dot = float(child_tangent[1])
    ra = np.asarray(virtual_u.r_a, dtype=float)
    rb = np.asarray(virtual_u.r_b, dtype=float)
    d = np.asarray(virtual_u.d, dtype=float)
    return alpha_dot * np.cross(ra, d) + beta_dot * np.cross(rb, d)


def _parent_level_set_residual(
    segment: FiberSegment,
    n: Vec3,
) -> float:
    """Check only that the parent samples remain on their declared small circle."""
    n_arr = np.asarray(n, dtype=float)
    c = float(segment.c)
    residuals: list[float] = []
    for step in segment.accepted_samples:
        if step.d is None:
            continue
        d = np.asarray(step.d, dtype=float)
        radial = d - c * n_arr
        radial -= float(np.dot(radial, n_arr)) * n_arr
        radial_norm = float(np.linalg.norm(radial))
        if radial_norm < 1e-14:
            predicted = c * n_arr
        else:
            predicted = c * n_arr + math.sqrt(max(0.0, 1.0 - c * c)) * (
                radial / radial_norm
            )
        residuals.append(float(np.linalg.norm(d - predicted)))
    return max(residuals) if residuals else float("inf")


def evaluate_fiber_equivalence(
    chain: SerialRevoluteChain,
    q0: tuple[float, ...],
    n: Vec3,
    *,
    geometry: SpatialFourBarGeometry,
    virtual_u: VirtualUAxes,
    independence: FiberIndependenceReport,
    segment: FiberSegment,
    tangent_tol: float = TANGENT_RESIDUAL_TOL,
    pointing_tol: float = POINTING_CURVE_TOL,
) -> tuple[FiberEquivalenceStatuses, FiberEquivalenceResiduals]:
    """Evaluate separate parent, chart, child, tangent, and branch statuses."""
    q_t = tuple(float(x) for x in np.asarray(q0, dtype=float).reshape(6))
    parent_tangent = reduced_fiber_tangent(chain, q_t, n)
    parent_dd = pointing_jacobian(chain, q_t) @ parent_tangent

    child_audit = audit_reference_geometry(geometry)
    child_jacobian = closure_jacobian(geometry, np.zeros(7, dtype=float))
    child_tangent, _ = null_tangent(child_jacobian)
    child_dd = _tool_pointing_rate_from_child_tangent(virtual_u, child_tangent)

    ra = np.asarray(virtual_u.r_a, dtype=float)
    rb = np.asarray(virtual_u.r_b, dtype=float)
    d = np.asarray(virtual_u.d, dtype=float)
    basis = np.column_stack((np.cross(ra, d), np.cross(rb, d)))
    coefficients, *_ = np.linalg.lstsq(basis, parent_dd, rcond=None)
    parent_dd_in_u = basis @ coefficients
    chart_residual = float(np.linalg.norm(parent_dd - parent_dd_in_u))

    if float(np.dot(child_dd, parent_dd_in_u)) < 0.0:
        child_dd = -child_dd
    parent_speed = float(np.linalg.norm(parent_dd_in_u))
    child_speed = float(np.linalg.norm(child_dd))
    if parent_speed > 1e-12 and child_speed > 1e-12:
        child_tool_residual = float(
            np.linalg.norm(parent_dd_in_u - child_dd * (parent_speed / child_speed))
        )
    else:
        child_tool_residual = float(np.linalg.norm(parent_dd_in_u - child_dd))

    h_residuals: list[float] = []
    for step in segment.accepted_samples:
        if step.q is None:
            continue
        h_residuals.append(abs(pointing_scalar(chain, step.q, n) - segment.c))
        if step.h_residual is not None:
            h_residuals.append(abs(float(step.h_residual)))
    h_residual_max = max(h_residuals) if h_residuals else float("inf")
    level_set_residual = _parent_level_set_residual(segment, n)

    residuals = FiberEquivalenceResiduals(
        parent_rank=independence.rank,
        parent_nullity=independence.nullity,
        dh_dq6=independence.dh_dq6,
        h_residual_max=h_residual_max,
        tangent_pointing_residual=chart_residual,
        child_tool_tangent_residual=child_tool_residual,
        pointing_curve_residual=level_set_residual,
        child_closure_norm=child_audit.closure_norm,
        child_rank=child_audit.jacobian_rank,
        child_nullity=child_audit.jacobian_nullity,
        branch_sample_count=len(segment.accepted_samples),
        lifted_alpha_dot=float(coefficients[0]),
        lifted_beta_dot=float(coefficients[1]),
    )

    parent_ok = (
        independence.independent
        and independence.rank == 4
        and independence.nullity == 1
        and independence.dh_dq6_vanishes
        and h_residual_max <= H_RESIDUAL_TOL
        and level_set_residual <= pointing_tol
        and residuals.branch_sample_count >= 3
    )
    chart_ok = chart_residual <= tangent_tol
    child_reference_ok = (
        child_audit.closure_norm <= CHILD_CLOSURE_TOL
        and child_audit.jacobian_rank == 6
        and child_audit.jacobian_nullity == 1
    )
    tangent_ok = child_tool_residual <= tangent_tol

    parent_status = "PASS" if parent_ok else "FAIL"
    chart_status = "PASS" if chart_ok else "FAIL"
    child_reference_status = "PASS" if child_reference_ok else "FAIL"
    tangent_status = "PASS" if tangent_ok else "FAIL"
    branch_status = "UNRESOLVED"

    if not parent_ok or not chart_ok or not child_reference_ok:
        overall = "FAIL"
    elif tangent_ok and branch_status == "PASS":
        overall = "PASS"
    else:
        overall = "REVIEW"

    statuses = FiberEquivalenceStatuses(
        parent_slice_status=parent_status,
        virtual_u_chart_status=chart_status,
        child_reference_closure_status=child_reference_status,
        parent_child_tangent_status=tangent_status,
        parent_child_branch_status=branch_status,
        overall_status=overall,
        notes=(
            "The local U_v chart spanning the S² tangent plane is not a child-mechanism equivalence proof.",
            "pointing_curve_residual is a parent level-set check, not parent-child branch agreement.",
            "Global child branch comparison has not been implemented.",
        ),
    )
    return statuses, residuals


def construct_suur_uuur_pointing_fiber(
    *,
    n: Vec3 = PRIMARY_N,
    q0: tuple[float, ...] = INTERSECTING_PAIRS_REGULAR_Q,
    n_steps: int = 6,
    step_size: float = 0.025,
    slice_id: str = "suur_ip_primary_n",
) -> PointingSliceFiberResult:
    """Worked pointing-slice prototype on the intersecting-pairs architecture."""
    architecture = IntersectingPairsAligned6R.aligned()
    chain = architecture.chain
    q_t = tuple(float(x) for x in q0)
    independence = fiber_independence_report(chain, q_t, n)
    state0 = chain.evaluate(q_t)
    n_hat = independence.n
    notes: list[str] = [
        "V08-oriented pointing-slice prototype; not active V05 source-chain evidence.",
        "Compound UA/UB frames are orthonormalized charts of intersecting pairs.",
        "Exact free-SUUR mechanism identity beyond this seed chart is unverified.",
        "Parent-child tangent and branch statuses are exported separately.",
    ]

    if not independence.independent:
        raise ValueError(
            f"pointing slice is not independent at seed (rank={independence.rank}, "
            f"nullity={independence.nullity}, n×d={independence.n_cross_d_norm})"
        )

    virtual_u = derive_virtual_u_axes(n_hat, _as_vec3(state0.d))
    geometry = build_uuur_child_from_suur_seed(chain, q_t, virtual_u)
    segment = continue_fiber(chain, q_t, n_hat, n_steps=n_steps, step_size=step_size)
    statuses, residuals = evaluate_fiber_equivalence(
        chain,
        q_t,
        n_hat,
        geometry=geometry,
        virtual_u=virtual_u,
        independence=independence,
        segment=segment,
    )
    slice_definition = SliceDefinition(
        n=n_hat,
        c=float(segment.c),
        formula="h(d)=n·d",
        architecture="IntersectingPairsAligned6R",
        q0=q_t,
        p0=_as_vec3(state0.p),
        d0=_as_vec3(state0.d),
        q6_star=q_t[-1],
    )
    return PointingSliceFiberResult(
        slice_id=slice_id,
        family=OrderedFamily.UUUR.value,
        parent_line="SUUR",
        slice_definition=slice_definition,
        virtual_u=virtual_u,
        geometry=geometry,
        independence=independence,
        fiber_segment_accepted=len(segment.accepted_samples),
        equivalence_residuals=residuals,
        equivalence_statuses=statuses,
        fiber_equivalence_status=statuses.overall_status,
        slice_provenance="task_derived",
        program_role="V08_POINTING_SLICE_PROTOTYPE",
        notes=tuple(notes),
    )


def child_branch_trace(
    geometry: SpatialFourBarGeometry,
    *,
    steps: int = 24,
    step_size: float = 0.03,
) -> object:
    """Short child continuation used for prototype diagnostic plots."""
    return continue_branch(geometry, steps=steps, step_size=step_size, direction=1)
