"""Exact consecutive RR → U_phys axis aggregation for spatial 4R sources.

Conventions
-----------
A consecutive pair ``(Ri, R{i+1})`` is an exact universal-joint candidate when,
at the evaluation configuration (home or seed)::

    dist(Ri, R{i+1}) ≤ distance_tol
    ||wi × w{i+1}|| ≥ parallel_tol   (not parallel)
    |wi · w{i+1}| ≤ orthogonality_tol  (orthogonal U chart)

The aggregated closed-loop identity is role-aware::

    S_v - U_phys - R - R

with ``joint_kind_sequence = ("S_v", "U", "R", "R")`` and
``joint_role_sequence = ("S_v", "U_phys", "R_phys", "R_phys")`` when the
aggregated pair is the proximal consecutive pair (indices 0,1).

The coordinate map for that proximal pair is the identity embedding::

    q_source = (α, β, q3, q4) = q_reduced

so FK identity is tautological on the same screws; the certificate still
records geometric residuals and fiber/tangent agreement. ``U_phys`` must not
inherit explorer ``U_v`` / ``tool_a`` winding semantics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import AxisLine, line_closest_points, line_line_distance, parallelism_residual
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

Vec = NDArray[np.floating]

PAIR_DISTANCE_TOL_M = 1e-12
PARALLEL_CROSS_TOL = 1e-8
ORTHOGONALITY_DOT_TOL = 1e-9


@dataclass(frozen=True, slots=True)
class AggregationCandidate:
    """Geometric diagnostics for one consecutive RR pair."""

    pair_index: int
    joint_a: int
    joint_b: int
    distance_m: float
    parallelism_residual: float
    orthogonality_abs_dot: float
    center: tuple[float, float, float]
    w_a: tuple[float, float, float]
    w_b: tuple[float, float, float]
    exact_intersecting: bool
    exact_orthogonal: bool
    exact_u_candidate: bool

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AggregatedMechanismModel:
    """Role-aware aggregated fixed-position representation of a 4R source."""

    architecture_id: str
    source: OpenChainModel
    pair_index: int
    family_label: str
    joint_kind_sequence: tuple[str, ...]
    joint_role_sequence: tuple[str, ...]
    u_center: tuple[float, float, float]
    u_axes: tuple[tuple[float, float, float], tuple[float, float, float]]
    candidate: AggregationCandidate
    notes: tuple[str, ...] = ()

    @property
    def chain(self) -> SerialRevoluteChain:
        return self.source.chain

    def embed_reduced_to_source(self, q_reduced: tuple[float, ...]) -> tuple[float, ...]:
        """Map reduced coordinates to source joint vector (identity for proximal U)."""
        q = tuple(float(x) for x in q_reduced)
        if len(q) != self.source.n_joints:
            raise ValueError("reduced q must have the same length as the source chain")
        if self.pair_index != 0:
            raise NotImplementedError(
                "non-proximal RR→U embedding is unverified in this MVP; "
                "only pair_index=0 (S_v-U_phys-R-R) is implemented"
            )
        return q

    def lift_source_to_reduced(self, q_source: tuple[float, ...]) -> tuple[float, ...]:
        """Inverse of ``embed_reduced_to_source`` for the proximal-U chart."""
        return self.embed_reduced_to_source(q_source)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "pair_index": self.pair_index,
            "family_label": self.family_label,
            "joint_kind_sequence": list(self.joint_kind_sequence),
            "joint_role_sequence": list(self.joint_role_sequence),
            "u_center": self.u_center,
            "u_axes": [list(a) for a in self.u_axes],
            "candidate": self.candidate.to_json_dict(),
            "notes": list(self.notes),
        }


def _axes_at(
    chain: SerialRevoluteChain,
    q: tuple[float, ...] | None,
) -> tuple[AxisLine, ...]:
    if q is None:
        return chain.home_axes
    return chain.current_axes(q)


def assess_consecutive_pair(
    chain: SerialRevoluteChain,
    pair_index: int,
    *,
    q: tuple[float, ...] | None = None,
    distance_tol_m: float = PAIR_DISTANCE_TOL_M,
    parallel_tol: float = PARALLEL_CROSS_TOL,
    orthogonality_tol: float = ORTHOGONALITY_DOT_TOL,
) -> AggregationCandidate:
    """Assess one consecutive pair for exact U aggregation."""
    if pair_index < 0 or pair_index >= chain.n_joints - 1:
        raise ValueError("pair_index out of range")
    axes = _axes_at(chain, q)
    a = axes[pair_index]
    b = axes[pair_index + 1]
    dist = line_line_distance(a, b)
    par = parallelism_residual(a.w, b.w)
    dot = abs(float(np.dot(np.asarray(a.w, dtype=float), np.asarray(b.w, dtype=float))))
    center_a, _center_b = line_closest_points(a, b)
    center = tuple(float(x) for x in center_a)
    exact_intersecting = dist <= distance_tol_m
    exact_orthogonal = par >= parallel_tol and dot <= orthogonality_tol
    exact_u = exact_intersecting and exact_orthogonal
    return AggregationCandidate(
        pair_index=pair_index,
        joint_a=pair_index,
        joint_b=pair_index + 1,
        distance_m=dist,
        parallelism_residual=par,
        orthogonality_abs_dot=dot,
        center=center,
        w_a=tuple(float(x) for x in a.w),
        w_b=tuple(float(x) for x in b.w),
        exact_intersecting=exact_intersecting,
        exact_orthogonal=exact_orthogonal,
        exact_u_candidate=exact_u,
    )


def detect_exact_u_pairs(
    model: OpenChainModel,
    *,
    q: tuple[float, ...] | None = None,
    distance_tol_m: float = PAIR_DISTANCE_TOL_M,
    parallel_tol: float = PARALLEL_CROSS_TOL,
    orthogonality_tol: float = ORTHOGONALITY_DOT_TOL,
) -> tuple[AggregationCandidate, ...]:
    """Return consecutive exact-U candidates on the source chain."""
    return tuple(
        assess_consecutive_pair(
            model.chain,
            i,
            q=q,
            distance_tol_m=distance_tol_m,
            parallel_tol=parallel_tol,
            orthogonality_tol=orthogonality_tol,
        )
        for i in range(model.n_joints - 1)
    )


def _family_label_for_pair(pair_index: int, n_joints: int = 4) -> str:
    if n_joints != 4:
        raise NotImplementedError("family labels for n!=4 are unverified")
    if pair_index == 0:
        return "S_v-U_phys-R-R"
    if pair_index == 1:
        return "S_v-R-U_phys-R"
    if pair_index == 2:
        return "S_v-R-R-U_phys"
    raise ValueError("pair_index out of range for 4R")


def _kind_role_sequences(pair_index: int, n_joints: int = 4) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Kind/role sequences for the closed-loop identity including virtual S_v."""
    if n_joints != 4 or pair_index != 0:
        # MVP implements only proximal aggregation chart for certificates.
        kinds = ("S_v",) + tuple("R" for _ in range(n_joints))
        roles = ("S_v",) + tuple("R_phys" for _ in range(n_joints))
        # Mark U slots conceptually for documentation even when embedding unverified.
        if 0 <= pair_index < n_joints - 1:
            # Replace the two R slots corresponding to the pair with U in a compressed view.
            compressed_kinds = ["S_v"]
            compressed_roles = ["S_v"]
            i = 0
            while i < n_joints:
                if i == pair_index:
                    compressed_kinds.append("U")
                    compressed_roles.append("U_phys")
                    i += 2
                else:
                    compressed_kinds.append("R")
                    compressed_roles.append("R_phys")
                    i += 1
            return tuple(compressed_kinds), tuple(compressed_roles)
        return kinds, roles
    return ("S_v", "U", "R", "R"), ("S_v", "U_phys", "R_phys", "R_phys")


def build_aggregated_mechanism(
    model: OpenChainModel,
    candidate: AggregationCandidate,
) -> AggregatedMechanismModel:
    """Build a role-aware aggregated model from an exact-U candidate."""
    if not candidate.exact_u_candidate:
        raise ValueError("cannot aggregate a non-exact U candidate")
    kinds, roles = _kind_role_sequences(candidate.pair_index, model.n_joints)
    label = _family_label_for_pair(candidate.pair_index, model.n_joints)
    notes = (
        "Aggregated chart over the same source screws; not a new serial chain.",
        "U_phys is a physical axis aggregate; not explorer U_v / tool_a semantics.",
        "Multi-component completeness beyond the scoped fiber remains unverified.",
    )
    if candidate.pair_index != 0:
        notes = (
            *notes,
            "Non-proximal embedding is recorded but FK identity map is unverified in this MVP.",
        )
    return AggregatedMechanismModel(
        architecture_id=model.architecture_id,
        source=model,
        pair_index=candidate.pair_index,
        family_label=label,
        joint_kind_sequence=kinds,
        joint_role_sequence=roles,
        u_center=candidate.center,
        u_axes=(candidate.w_a, candidate.w_b),
        candidate=candidate,
        notes=notes,
    )


def fk_identity_residuals(
    aggregated: AggregatedMechanismModel,
    q_source: tuple[float, ...],
) -> dict[str, float]:
    """Return FK residuals of the reduced↔source identity embedding."""
    q_red = aggregated.lift_source_to_reduced(q_source)
    q_emb = aggregated.embed_reduced_to_source(q_red)
    state_s = aggregated.chain.evaluate(q_source)
    state_r = aggregated.chain.evaluate(q_emb)
    p_res = float(np.linalg.norm(state_s.p - state_r.p))
    r_res = float(np.linalg.norm(state_s.R - state_r.R, ord="fro"))
    d_res = float(np.linalg.norm(state_s.d - state_r.d))
    return {
        "position_residual_m": p_res,
        "rotation_frobenius": r_res,
        "pointing_residual": d_res,
        "joint_map_residual": float(np.linalg.norm(np.asarray(q_source) - np.asarray(q_emb))),
    }


@dataclass(frozen=True, slots=True)
class FalseUTaskErrorReport:
    """Diagnostic residuals from treating a non-exact pair as exact U.

    This is **not** a DecompositionCertificate status. Label:
    ``false_u_surrogate`` under operation ``axis_aggregation``.
    """

    architecture_id: str
    pair_index: int
    label: str
    distance_tol_m: float
    orthogonality_tol: float
    parallel_tol: float
    source_distance_m: float
    source_orthogonality_abs_dot: float
    source_parallelism_residual: float
    exceeds_distance_tol: bool
    exceeds_orthogonality_tol: bool
    surrogate_center: tuple[float, float, float]
    surrogate_w_a: tuple[float, float, float]
    surrogate_w_b: tuple[float, float, float]
    seed_position_residual_m: float
    seed_rotation_frobenius: float
    seed_pointing_residual: float
    fiber_max_position_residual_m: float
    fiber_max_rotation_frobenius: float
    fiber_max_pointing_residual: float
    fiber_samples_compared: int
    notes: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def force_exact_u_surrogate_axes(
    axes: tuple[AxisLine, ...],
    pair_index: int = 0,
) -> tuple[AxisLine, ...]:
    """Project a consecutive pair onto intersecting orthogonal axes at the midpoint.

    Keeps all other axes unchanged. Raises if the pair is parallel (no unique U chart).
    """
    if pair_index < 0 or pair_index >= len(axes) - 1:
        raise ValueError("pair_index out of range")
    a = axes[pair_index]
    b = axes[pair_index + 1]
    pa, pb = line_closest_points(a, b)
    center = 0.5 * (pa + pb)
    w_a = np.asarray(a.w, dtype=float)
    w_b = np.asarray(b.w, dtype=float)
    # Orthogonalize w_b against w_a in the plane of the two directions when possible.
    w_b_orth = w_b - float(np.dot(w_b, w_a)) * w_a
    n = float(np.linalg.norm(w_b_orth))
    if n <= PARALLEL_CROSS_TOL:
        raise ValueError("cannot force exact U surrogate for parallel axes")
    w_b_orth = w_b_orth / n
    center_t = tuple(float(x) for x in center)
    forced_a = AxisLine(center_t, tuple(float(x) for x in w_a))
    forced_b = AxisLine(center_t, tuple(float(x) for x in w_b_orth))
    out = list(axes)
    out[pair_index] = forced_a
    out[pair_index + 1] = forced_b
    return tuple(out)


def _pose_residuals(chain_a: SerialRevoluteChain, chain_b: SerialRevoluteChain, q: tuple[float, ...]) -> tuple[float, float, float]:
    sa = chain_a.evaluate(q)
    sb = chain_b.evaluate(q)
    return (
        float(np.linalg.norm(sa.p - sb.p)),
        float(np.linalg.norm(sa.R - sb.R, ord="fro")),
        float(np.linalg.norm(sa.d - sb.d)),
    )


def measure_false_u_task_error(
    model: OpenChainModel,
    q0: tuple[float, ...],
    *,
    pair_index: int = 0,
    n_fiber_steps: int = 16,
    fiber_step_size: float = 0.04,
    distance_tol_m: float = PAIR_DISTANCE_TOL_M,
    parallel_tol: float = PARALLEL_CROSS_TOL,
    orthogonality_tol: float = ORTHOGONALITY_DOT_TOL,
) -> FalseUTaskErrorReport:
    """Compare source FK to a forced exact-U surrogate at seed and along the source fiber."""
    from .fixed_position_continuation import continue_fixed_position_fiber

    cand = assess_consecutive_pair(
        model.chain,
        pair_index,
        q=None,
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    surrogate_axes = force_exact_u_surrogate_axes(model.chain.home_axes, pair_index=pair_index)
    # Preserve the source home tool pose (same p0/d0/R0); only pair screws change.
    surrogate_chain = SerialRevoluteChain(
        home_axes=surrogate_axes,
        p0=model.chain.p0,
        d0=model.chain.d0,
        R0=model.chain.R0,
    )
    seed_p, seed_r, seed_d = _pose_residuals(model.chain, surrogate_chain, q0)

    fiber = continue_fixed_position_fiber(
        model,
        q0,
        n_steps=n_fiber_steps,
        step_size=fiber_step_size,
        component_id=f"{model.architecture_id}_false_u_diag",
    )
    max_p = seed_p
    max_r = seed_r
    max_d = seed_d
    n_compared = 0
    for step in fiber.accepted_samples:
        if step.q is None:
            continue
        p_res, r_res, d_res = _pose_residuals(model.chain, surrogate_chain, step.q)
        max_p = max(max_p, p_res)
        max_r = max(max_r, r_res)
        max_d = max(max_d, d_res)
        n_compared += 1

    return FalseUTaskErrorReport(
        architecture_id=model.architecture_id,
        pair_index=pair_index,
        label="false_u_surrogate",
        distance_tol_m=distance_tol_m,
        orthogonality_tol=orthogonality_tol,
        parallel_tol=parallel_tol,
        source_distance_m=cand.distance_m,
        source_orthogonality_abs_dot=cand.orthogonality_abs_dot,
        source_parallelism_residual=cand.parallelism_residual,
        exceeds_distance_tol=cand.distance_m > distance_tol_m,
        exceeds_orthogonality_tol=cand.orthogonality_abs_dot > orthogonality_tol,
        surrogate_center=tuple(float(x) for x in surrogate_axes[pair_index].r),
        surrogate_w_a=tuple(float(x) for x in surrogate_axes[pair_index].w),
        surrogate_w_b=tuple(float(x) for x in surrogate_axes[pair_index + 1].w),
        seed_position_residual_m=seed_p,
        seed_rotation_frobenius=seed_r,
        seed_pointing_residual=seed_d,
        fiber_max_position_residual_m=max_p,
        fiber_max_rotation_frobenius=max_r,
        fiber_max_pointing_residual=max_d,
        fiber_samples_compared=n_compared,
        notes=(
            "Forced exact-U surrogate replaces the consecutive pair with intersecting orthogonal axes.",
            "Residuals quantify task error of treating a non-exact pair as U_phys.",
            "Diagnostic only — not an APPROXIMATE DecompositionCertificate.",
        ),
    )
