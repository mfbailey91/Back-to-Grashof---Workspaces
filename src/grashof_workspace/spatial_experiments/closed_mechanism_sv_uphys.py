"""Independent ``S_v-U_phys-R-R`` closed-mechanism geometry for V05.

Builds a *separate* spatial four-bar from a proximal exact ``RR→U_phys``
aggregation.  Does not reuse ``AggregatedMechanismModel.chain`` as the closed
solver object.

Solver chart (cyclic ``URRS``): ``U_phys, R_phys, R_phys, S_v``.

Geometry is assembled at the source seed pose (current axes + ``p*``) so the
independent chart seed is the zero vector.  Physical reduced angles are
interpreted as deltas from the source seed.  Semantic origin remains ``S_v``.
``U_phys`` must not inherit ``U_v`` / ``tool_a`` task-winding semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from grashof_workspace.spatial4bar_explorer.closure import audit_reference_geometry
from grashof_workspace.spatial4bar_explorer.geometry import (
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
from grashof_workspace.spatial4bar_explorer.models import OrderedFamily
from grashof_workspace.spatial_experiments.axis_aggregation import (
    PAIR_DISTANCE_TOL_M,
    AggregatedMechanismModel,
)
from grashof_workspace.spatial_experiments.axis_geometry import (
    as_vec3,
    line_closest_points,
    line_line_distance,
)
from grashof_workspace.spatial_experiments.open_chain import OpenChainModel

PHYSICAL_COORD_COUNT = 4


def _as_frame_vec(values: tuple[float, ...] | list[float] | np.ndarray) -> Vec3:
    arr = np.asarray(values, dtype=float).reshape(3)
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def _orthonormal_u_frame(w0: Vec3, w1: Vec3) -> Frame3:
    x_axis = normalize(w0)
    y_raw = cross(cross(x_axis, w1), x_axis)
    if (dot(y_raw, y_raw)) ** 0.5 <= 1e-12:
        helper: Vec3 = (0.0, 0.0, 1.0) if abs(x_axis[2]) < 0.9 else (0.0, 1.0, 0.0)
        y_raw = cross(x_axis, helper)
    y_axis = normalize(y_raw)
    if dot(y_axis, w1) < 0.0:
        y_axis = scale(y_axis, -1.0)
    z_axis = normalize(cross(x_axis, y_axis))
    return (x_axis, y_axis, z_axis)


def _revolute_frame(direction: Vec3) -> Frame3:
    z_axis = normalize(direction)
    helper: Vec3 = (0.0, 0.0, 1.0) if abs(z_axis[2]) < 0.9 else (0.0, 1.0, 0.0)
    x_axis = normalize(cross(helper, z_axis))
    y_axis = normalize(cross(z_axis, x_axis))
    return (x_axis, y_axis, z_axis)


def _spherical_frame() -> Frame3:
    return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


@dataclass(frozen=True, slots=True)
class IndependentClosedMechanism:
    """Source-derived independent closed loop with role-aware provenance."""

    architecture_id: str
    component_id: str
    pair_index: int
    family_label: str
    semantic_origin_role: str
    joint_kind_sequence_semantic: tuple[str, ...]
    joint_role_sequence_semantic: tuple[str, ...]
    joint_kind_sequence_solver: tuple[str, ...]
    joint_role_sequence_solver: tuple[str, ...]
    p_star: tuple[float, float, float]
    q_seed_source: tuple[float, ...]
    q_seed_reduced: tuple[float, ...]
    geometry: SpatialFourBarGeometry
    source_chain_object_id: int
    geometry_object_id: int
    provenance: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.pair_index != 0:
            raise NotImplementedError("MVP supports proximal pair_index=0 only")
        if self.provenance != "source_derived":
            raise ValueError("independent closed mechanism must be source_derived")
        if self.geometry_object_id == self.source_chain_object_id:
            raise ValueError("closed geometry must be a distinct object from the source chain")
        if self.geometry.family is not OrderedFamily.URRS:
            raise ValueError("solver chart must be cyclic URRS")
        if "U_v" in self.joint_role_sequence_semantic or "U_v" in self.joint_role_sequence_solver:
            raise ValueError("U_v is forbidden on the V05 closed-mechanism MVP")

    def source_q_from_reduced(self, q_reduced: tuple[float, ...] | np.ndarray) -> tuple[float, ...]:
        """Map reduced physical deltas to absolute source joint angles."""

        q = tuple(float(x) for x in np.asarray(q_reduced, dtype=float).reshape(-1))
        if len(q) != 7:
            raise ValueError("reduced q must have seven scalar coordinates")
        seed = self.q_seed_source
        return (seed[0] + q[0], seed[1] + q[1], seed[2] + q[2], seed[3] + q[3])

    def reduced_physical_from_source(self, q_source: tuple[float, ...] | np.ndarray) -> tuple[float, ...]:
        q = tuple(float(x) for x in np.asarray(q_source, dtype=float).reshape(-1))
        if len(q) != 4:
            raise ValueError("source q must have four joint coordinates")
        seed = self.q_seed_source
        return (q[0] - seed[0], q[1] - seed[1], q[2] - seed[2], q[3] - seed[3])

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "component_id": self.component_id,
            "pair_index": self.pair_index,
            "family_label": self.family_label,
            "semantic_origin_role": self.semantic_origin_role,
            "joint_kind_sequence_semantic": list(self.joint_kind_sequence_semantic),
            "joint_role_sequence_semantic": list(self.joint_role_sequence_semantic),
            "joint_kind_sequence_solver": list(self.joint_kind_sequence_solver),
            "joint_role_sequence_solver": list(self.joint_role_sequence_solver),
            "p_star": list(self.p_star),
            "q_seed_source": list(self.q_seed_source),
            "q_seed_reduced": list(self.q_seed_reduced),
            "solver_family": self.geometry.family.value,
            "provenance": self.provenance,
            "source_chain_object_id": self.source_chain_object_id,
            "geometry_object_id": self.geometry_object_id,
            "notes": list(self.notes),
        }


def build_independent_sv_uphys_rr(
    model: OpenChainModel,
    aggregated: AggregatedMechanismModel,
    q_seed: tuple[float, ...],
    *,
    component_id: str | None = None,
) -> IndependentClosedMechanism:
    """Instantiate an independent ``S_v-U_phys-R-R`` loop at the source seed pose."""

    if aggregated.pair_index != 0:
        raise NotImplementedError("non-proximal independent closed solves are unverified")
    if not aggregated.candidate.exact_u_candidate:
        raise ValueError("independent closed solve requires an exact U aggregation candidate")
    if model.n_joints != 4:
        raise ValueError("MVP supports spatial 4R sources only")
    if aggregated.source.architecture_id != model.architecture_id:
        raise ValueError("aggregated model must match the source architecture")

    q0 = tuple(float(x) for x in q_seed)
    if len(q0) != 4:
        raise ValueError("q_seed must have four coordinates")

    state = model.chain.evaluate(q0)
    p_star = as_vec3(state.p)
    axes = model.chain.current_axes(q0)
    dist = line_line_distance(axes[0], axes[1])
    if dist > PAIR_DISTANCE_TOL_M:
        raise ValueError(f"proximal RR pair is not concurrent at seed (distance={dist})")

    u_center = _as_frame_vec(line_closest_points(axes[0], axes[1])[0])
    joints = (
        JointGeometry(
            name="J_Uphys",
            kind=JointKind.U,
            center=u_center,
            frame=_orthonormal_u_frame(_as_frame_vec(axes[0].w), _as_frame_vec(axes[1].w)),
        ),
        JointGeometry(
            name="J_R3",
            kind=JointKind.R,
            center=_as_frame_vec(axes[2].r),
            frame=_revolute_frame(_as_frame_vec(axes[2].w)),
        ),
        JointGeometry(
            name="J_R4",
            kind=JointKind.R,
            center=_as_frame_vec(axes[3].r),
            frame=_revolute_frame(_as_frame_vec(axes[3].w)),
        ),
        JointGeometry(
            name="J_Sv",
            kind=JointKind.S,
            center=p_star,
            frame=_spherical_frame(),
        ),
    )
    links = (
        LinkGeometry("L_U_R3", 0, 1),
        LinkGeometry("L_R3_R4", 1, 2),
        LinkGeometry("L_R4_Sv", 2, 3),
        LinkGeometry("L_Sv_U_ground", 3, 0),
    )
    geometry = SpatialFourBarGeometry(
        family=OrderedFamily.URRS,
        joints=joints,
        links=links,
        ground_link=3,
        tool_joint=0,
    )
    errors = geometry.validation_errors()
    if errors:
        raise ValueError(f"invalid independent URRS geometry: {errors}")
    audit = audit_reference_geometry(geometry)
    if audit.closure_norm > 1e-9 or audit.jacobian_rank != 6 or audit.jacobian_nullity != 1:
        raise ValueError(
            f"independent closed geometry is not a regular 1-DOF leaf "
            f"(closure={audit.closure_norm}, rank={audit.jacobian_rank}, "
            f"nullity={audit.jacobian_nullity})"
        )

    cid = component_id or f"{model.architecture_id}_component0"
    return IndependentClosedMechanism(
        architecture_id=model.architecture_id,
        component_id=cid,
        pair_index=0,
        family_label="S_v-U_phys-R-R",
        semantic_origin_role="S_v",
        joint_kind_sequence_semantic=("S_v", "U", "R", "R"),
        joint_role_sequence_semantic=("S_v", "U_phys", "R_phys", "R_phys"),
        joint_kind_sequence_solver=("U", "R", "R", "S"),
        joint_role_sequence_solver=("U_phys", "R_phys", "R_phys", "S_v"),
        p_star=p_star,
        q_seed_source=q0,
        q_seed_reduced=(0.0,) * 7,
        geometry=geometry,
        source_chain_object_id=id(model.chain),
        geometry_object_id=id(geometry),
        provenance="source_derived",
        notes=(
            "Independent SpatialFourBarGeometry distinct from AggregatedMechanismModel.chain.",
            "Assembled at the source seed pose; reduced physical angles are seed deltas.",
            "Solver chart is cyclic URRS; semantic origin remains S_v.",
            "U_phys must not inherit U_v/tool_a winding semantics.",
            (
                f"Reference assembly closure_norm={audit.closure_norm:.3e}, "
                f"rank={audit.jacobian_rank}, nullity={audit.jacobian_nullity}."
            ),
        ),
    )
