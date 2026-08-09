"""Exact consecutive ``RR → U_phys`` axis aggregation for spatial sources.

Axis aggregation and closed-mechanism decomposition are deliberately separate:

- exact intersecting orthogonal physical axes may be regrouped as a universal
  joint without changing the serial-chain forward map;
- that fact alone does not prove that an independently instantiated
  ``S_v-U_phys-R-R`` closed mechanism reproduces a complete source component.

The latter claim is issued by ``decomposition_certificate.py`` only after an
independent reduced solve exists; V05 currently records it as unresolved.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import (
    AxisLine,
    as_vec3,
    line_closest_points,
    line_line_distance,
    parallelism_residual,
)
from .open_chain import OpenChainModel
from .serial_chain import SerialRevoluteChain

Vec = NDArray[np.floating]

PAIR_DISTANCE_TOL_M = 1e-12
PARALLEL_CROSS_TOL = 1e-8
ORTHOGONALITY_DOT_TOL = 1e-9


def _validate_tolerances(
    *,
    distance_tol_m: float,
    parallel_tol: float,
    orthogonality_tol: float,
) -> None:
    if distance_tol_m < 0.0:
        raise ValueError("distance_tol_m must be nonnegative")
    if not 0.0 <= parallel_tol <= 1.0:
        raise ValueError("parallel_tol must lie in [0,1]")
    if not 0.0 <= orthogonality_tol <= 1.0:
        raise ValueError("orthogonality_tol must lie in [0,1]")


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
    """Role-aware exact coordinate regrouping of a spatial-4R source.

    This object is an axis-aggregation chart over the source screws.  It is not
    an independently instantiated closed mechanism.
    """

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
        """Identity coordinate regrouping for the supported proximal U chart."""
        q = tuple(float(x) for x in q_reduced)
        if len(q) != self.source.n_joints:
            raise ValueError("reduced q must have the same scalar-coordinate count as source")
        if self.pair_index != 0:
            raise NotImplementedError(
                "non-proximal RR→U coordinate embedding is unverified in this MVP"
            )
        return q

    def lift_source_to_reduced(self, q_source: tuple[float, ...]) -> tuple[float, ...]:
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
    return chain.home_axes if q is None else chain.current_axes(q)


def assess_consecutive_pair(
    chain: SerialRevoluteChain,
    pair_index: int,
    *,
    q: tuple[float, ...] | None = None,
    distance_tol_m: float = PAIR_DISTANCE_TOL_M,
    parallel_tol: float = PARALLEL_CROSS_TOL,
    orthogonality_tol: float = ORTHOGONALITY_DOT_TOL,
) -> AggregationCandidate:
    """Assess one consecutive pair for exact orthogonal-U aggregation."""
    _validate_tolerances(
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    if pair_index < 0 or pair_index >= chain.n_joints - 1:
        raise ValueError("pair_index out of range")
    axes = _axes_at(chain, q)
    a = axes[pair_index]
    b = axes[pair_index + 1]
    dist = line_line_distance(a, b)
    cross_residual = parallelism_residual(a.w, b.w)
    dot = abs(float(np.dot(np.asarray(a.w, dtype=float), np.asarray(b.w, dtype=float))))
    center_a, center_b = line_closest_points(a, b)
    center_arr = 0.5 * (center_a + center_b)
    center = as_vec3(center_arr)
    exact_intersecting = dist <= distance_tol_m
    exact_orthogonal = cross_residual >= parallel_tol and dot <= orthogonality_tol
    return AggregationCandidate(
        pair_index=pair_index,
        joint_a=pair_index,
        joint_b=pair_index + 1,
        distance_m=dist,
        parallelism_residual=cross_residual,
        orthogonality_abs_dot=dot,
        center=center,
        w_a=as_vec3(a.w),
        w_b=as_vec3(b.w),
        exact_intersecting=exact_intersecting,
        exact_orthogonal=exact_orthogonal,
        exact_u_candidate=exact_intersecting and exact_orthogonal,
    )


def detect_exact_u_pairs(
    model: OpenChainModel,
    *,
    q: tuple[float, ...] | None = None,
    distance_tol_m: float = PAIR_DISTANCE_TOL_M,
    parallel_tol: float = PARALLEL_CROSS_TOL,
    orthogonality_tol: float = ORTHOGONALITY_DOT_TOL,
) -> tuple[AggregationCandidate, ...]:
    """Return all consecutive-pair diagnostics on the source chain."""
    _validate_tolerances(
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
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
    labels = {
        0: "S_v-U_phys-R-R",
        1: "S_v-R-U_phys-R",
        2: "S_v-R-R-U_phys",
    }
    if n_joints != 4 or pair_index not in labels:
        raise NotImplementedError("role-aware labels are currently defined only for spatial 4R")
    return labels[pair_index]


def _kind_role_sequences(
    pair_index: int,
    n_joints: int = 4,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if n_joints != 4:
        raise NotImplementedError("role-aware sequences are currently defined only for 4R")
    kinds: list[str] = ["S_v"]
    roles: list[str] = ["S_v"]
    i = 0
    while i < n_joints:
        if i == pair_index:
            kinds.append("U")
            roles.append("U_phys")
            i += 2
        else:
            kinds.append("R")
            roles.append("R_phys")
            i += 1
    return tuple(kinds), tuple(roles)


def build_aggregated_mechanism(
    model: OpenChainModel,
    candidate: AggregationCandidate,
) -> AggregatedMechanismModel:
    """Build the exact role-aware axis-regrouping chart."""
    if not candidate.exact_u_candidate:
        raise ValueError("cannot aggregate a non-exact U candidate")
    kinds, roles = _kind_role_sequences(candidate.pair_index, model.n_joints)
    label = _family_label_for_pair(candidate.pair_index, model.n_joints)
    notes: tuple[str, ...] = (
        "Exact coordinate regrouping over the same source screws.",
        "Not an independently instantiated S_v-U_phys-R-R closed mechanism.",
        "U_phys is physical and must not inherit U_v/tool_a winding semantics.",
    )
    if candidate.pair_index != 0:
        notes = (*notes, "Non-proximal scalar-coordinate embedding remains unverified.")
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
    """Diagnostic residuals of the exact scalar-coordinate regrouping.

    These are *not* independent reduced-mechanism closure residuals.
    """
    q_red = aggregated.lift_source_to_reduced(q_source)
    q_emb = aggregated.embed_reduced_to_source(q_red)
    state_s = aggregated.chain.evaluate(q_source)
    state_r = aggregated.chain.evaluate(q_emb)
    return {
        "position_residual_m": float(np.linalg.norm(state_s.p - state_r.p)),
        "rotation_frobenius": float(np.linalg.norm(state_s.R - state_r.R, ord="fro")),
        "pointing_residual": float(np.linalg.norm(state_s.d - state_r.d)),
        "joint_map_residual_rad": float(
            np.linalg.norm(np.asarray(q_source, dtype=float) - np.asarray(q_emb, dtype=float))
        ),
    }


@dataclass(frozen=True, slots=True)
class FalseUTaskErrorReport:
    """Diagnostic same-coordinate error from forcing a non-exact pair to exact U."""

    architecture_id: str
    pair_index: int
    label: str
    comparison_mode: str
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


@dataclass(frozen=True, slots=True)
class ToleranceBoundaryCase:
    distance_scale: float
    orthogonality_scale: float
    target_distance_m: float
    target_abs_dot: float
    measured_distance_m: float
    measured_abs_dot: float
    accepted: bool

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def force_exact_u_surrogate_axes(
    axes: tuple[AxisLine, ...],
    pair_index: int = 0,
) -> tuple[AxisLine, ...]:
    """Project a pair onto intersecting orthogonal axes at closest-point midpoint."""
    if pair_index < 0 or pair_index >= len(axes) - 1:
        raise ValueError("pair_index out of range")
    a = axes[pair_index]
    b = axes[pair_index + 1]
    pa, pb = line_closest_points(a, b)
    center = 0.5 * (pa + pb)
    w_a = np.asarray(a.w, dtype=float)
    w_b = np.asarray(b.w, dtype=float)
    w_b_orth = w_b - float(np.dot(w_b, w_a)) * w_a
    norm = float(np.linalg.norm(w_b_orth))
    if norm <= PARALLEL_CROSS_TOL:
        raise ValueError("cannot force exact U surrogate for parallel axes")
    w_b_orth = w_b_orth / norm
    center_t = as_vec3(center)
    out = list(axes)
    out[pair_index] = AxisLine(center_t, as_vec3(w_a))
    out[pair_index + 1] = AxisLine(center_t, as_vec3(w_b_orth))
    return tuple(out)


def perturb_exact_u_pair_axes(
    axes: tuple[AxisLine, ...],
    *,
    pair_index: int = 0,
    distance_m: float = 0.0,
    orthogonality_abs_dot: float = 0.0,
) -> tuple[AxisLine, ...]:
    """Create a tolerance-relative perturbation of an exact orthogonal pair.

    ``distance_m`` is introduced along the pair normal.  The second direction
    is tilted toward the first so its absolute dot product equals the requested
    value (up to floating-point roundoff).
    """
    if distance_m < 0.0:
        raise ValueError("distance_m must be nonnegative")
    if not 0.0 <= orthogonality_abs_dot < 1.0:
        raise ValueError("orthogonality_abs_dot must lie in [0,1)")
    if pair_index < 0 or pair_index >= len(axes) - 1:
        raise ValueError("pair_index out of range")

    a = axes[pair_index]
    b = axes[pair_index + 1]
    w_a = np.asarray(a.w, dtype=float)
    w_b = np.asarray(b.w, dtype=float)
    w_b_perp = w_b - float(np.dot(w_b, w_a)) * w_a
    norm = float(np.linalg.norm(w_b_perp))
    if norm <= PARALLEL_CROSS_TOL:
        raise ValueError("reference pair must not be parallel")
    w_b_perp /= norm
    target_dot = float(orthogonality_abs_dot)
    w_b_new = np.sqrt(max(0.0, 1.0 - target_dot * target_dot)) * w_b_perp + target_dot * w_a
    w_b_new /= float(np.linalg.norm(w_b_new))
    normal = np.cross(w_a, w_b_new)
    normal /= float(np.linalg.norm(normal))
    r_b_new = np.asarray(b.r, dtype=float) + distance_m * normal

    out = list(axes)
    out[pair_index + 1] = AxisLine(
        as_vec3(r_b_new),
        as_vec3(w_b_new),
    )
    return tuple(out)


def evaluate_u_boundary_suite(
    model: OpenChainModel,
    *,
    pair_index: int = 0,
    scales: Iterable[float] = (0.0, 0.5, 1.0, 2.0, 10.0),
    distance_tol_m: float = PAIR_DISTANCE_TOL_M,
    parallel_tol: float = PARALLEL_CROSS_TOL,
    orthogonality_tol: float = ORTHOGONALITY_DOT_TOL,
) -> tuple[ToleranceBoundaryCase, ...]:
    """Evaluate a Cartesian grid around the exact distance/orthogonality boundary."""
    _validate_tolerances(
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    scale_values = tuple(float(s) for s in scales)
    if any(s < 0.0 for s in scale_values):
        raise ValueError("boundary scales must be nonnegative")
    cases: list[ToleranceBoundaryCase] = []
    for distance_scale in scale_values:
        for orthogonality_scale in scale_values:
            target_distance = distance_scale * distance_tol_m
            target_dot = min(orthogonality_scale * orthogonality_tol, 1.0 - 1e-15)
            perturbed_axes = perturb_exact_u_pair_axes(
                model.chain.home_axes,
                pair_index=pair_index,
                distance_m=target_distance,
                orthogonality_abs_dot=target_dot,
            )
            chain = SerialRevoluteChain(
                home_axes=perturbed_axes,
                p0=model.chain.p0,
                d0=model.chain.d0,
                R0=model.chain.R0,
            )
            candidate = assess_consecutive_pair(
                chain,
                pair_index,
                distance_tol_m=distance_tol_m,
                parallel_tol=parallel_tol,
                orthogonality_tol=orthogonality_tol,
            )
            cases.append(
                ToleranceBoundaryCase(
                    distance_scale=distance_scale,
                    orthogonality_scale=orthogonality_scale,
                    target_distance_m=target_distance,
                    target_abs_dot=target_dot,
                    measured_distance_m=candidate.distance_m,
                    measured_abs_dot=candidate.orthogonality_abs_dot,
                    accepted=candidate.exact_u_candidate,
                )
            )
    return tuple(cases)


def _pose_residuals(
    chain_a: SerialRevoluteChain,
    chain_b: SerialRevoluteChain,
    q: tuple[float, ...],
) -> tuple[float, float, float]:
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
    """Compare source FK to a forced exact-U surrogate at matching coordinates.

    This is a diagnostic approximation study, not a decomposition certificate
    and not an independently solved surrogate fixed-position component.
    """
    from .fixed_position_continuation import continue_fixed_position_fiber

    candidate = assess_consecutive_pair(
        model.chain,
        pair_index,
        distance_tol_m=distance_tol_m,
        parallel_tol=parallel_tol,
        orthogonality_tol=orthogonality_tol,
    )
    surrogate_axes = force_exact_u_surrogate_axes(model.chain.home_axes, pair_index=pair_index)
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
    compared = 0
    for step in fiber.accepted_samples:
        if step.q is None:
            continue
        p_res, r_res, d_res = _pose_residuals(model.chain, surrogate_chain, step.q)
        max_p = max(max_p, p_res)
        max_r = max(max_r, r_res)
        max_d = max(max_d, d_res)
        compared += 1

    return FalseUTaskErrorReport(
        architecture_id=model.architecture_id,
        pair_index=pair_index,
        label="false_u_surrogate",
        comparison_mode="same_source_coordinates_not_independent_surrogate_solve",
        distance_tol_m=distance_tol_m,
        orthogonality_tol=orthogonality_tol,
        parallel_tol=parallel_tol,
        source_distance_m=candidate.distance_m,
        source_orthogonality_abs_dot=candidate.orthogonality_abs_dot,
        source_parallelism_residual=candidate.parallelism_residual,
        exceeds_distance_tol=candidate.distance_m > distance_tol_m,
        exceeds_orthogonality_tol=candidate.orthogonality_abs_dot > orthogonality_tol,
        surrogate_center=as_vec3(surrogate_axes[pair_index].r),
        surrogate_w_a=as_vec3(surrogate_axes[pair_index].w),
        surrogate_w_b=as_vec3(surrogate_axes[pair_index + 1].w),
        seed_position_residual_m=seed_p,
        seed_rotation_frobenius=seed_r,
        seed_pointing_residual=seed_d,
        fiber_max_position_residual_m=max_p,
        fiber_max_rotation_frobenius=max_r,
        fiber_max_pointing_residual=max_d,
        fiber_samples_compared=compared,
        notes=(
            "Forced exact-U surrogate replaces the pair with intersecting orthogonal axes.",
            "The active off-axis corpus excites the candidate pair along the source fiber.",
            "Same-coordinate diagnostic only; independent surrogate continuation remains unresolved.",
            "Not an APPROXIMATE DecompositionCertificate.",
        ),
    )
