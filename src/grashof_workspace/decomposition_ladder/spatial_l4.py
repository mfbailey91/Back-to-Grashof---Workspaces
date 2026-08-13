"""L4 adapter: express existing V05 closed-mechanism evidence in ladder records.

This module does not re-solve the independent ``S_v-U_phys-R-R`` loop. It wraps
the audited V05D pipeline and attaches V05C orientation-curve truth for the
claimed component. Process status stays ``SCAFFOLD``; V05–V09 remains the
scientific source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos
from typing import Any

import numpy as np
from numpy.typing import NDArray

from grashof_workspace.spatial4bar_explorer.continuation import continue_branch
from grashof_workspace.spatial_experiments.axis_aggregation import (
    build_aggregated_mechanism,
    detect_exact_u_pairs,
)
from grashof_workspace.spatial_experiments.closed_mechanism_compare import (
    ClosedMechanismComparison,
    compare_independent_closed_mechanism,
    forged_identity_comparison,
)
from grashof_workspace.spatial_experiments.closed_mechanism_sv_uphys import (
    IndependentClosedMechanism,
    build_independent_sv_uphys_rr,
)
from grashof_workspace.spatial_experiments.decomposition_certificate import (
    DecompositionCertificate,
    issue_axis_aggregation_certificate,
    issue_closed_mechanism_certificate,
)
from grashof_workspace.spatial_experiments.fixed_position_continuation import (
    continue_fixed_position_fiber,
)
from grashof_workspace.spatial_experiments.open_chain import OpenChainModel
from grashof_workspace.spatial_experiments.orientation_image import (
    OrientationImageResult,
    build_orientation_image,
)
from grashof_workspace.spatial_experiments.v05_corpus import (
    Spatial4RCorpusEntry,
    build_exact_u_pair_4r,
    build_generic_4r,
)

from .models import (
    CertificateStatus,
    ChildMechanismRecord,
    EquivalenceCertificateRecord,
    LadderRung,
    LeafPredicateRecord,
    ProcessStatus,
    ReconstructionRecord,
    SourceFiberRecord,
    SourceParentRecord,
)

Mat = NDArray[np.floating]

_DEFAULT_N_STEPS = 40
_DEFAULT_STEP_SIZE = 0.03


def _status(value: str) -> CertificateStatus:
    return CertificateStatus(value)


def _nonneg(value: float | None) -> float | None:
    if value is None:
        return None
    return float(max(0.0, value))


def _rotation_geodesic(ra: Mat, rb: Mat) -> float:
    relative = rb @ ra.T
    cos_half = (float(np.trace(relative)) - 1.0) * 0.5
    return float(acos(max(-1.0, min(1.0, cos_half))))


def max_mapped_orientation_error(
    model: OpenChainModel,
    mechanism: IndependentClosedMechanism,
    orientation: OrientationImageResult,
    *,
    n_steps: int = _DEFAULT_N_STEPS,
    step_size: float = _DEFAULT_STEP_SIZE,
) -> float | None:
    """Nearest-neighbor geodesic orientation error of mapped reduced samples."""

    source_rs = [
        np.asarray(sample.R, dtype=float) for sample in orientation.samples if sample.R is not None
    ]
    if not source_rs:
        return None

    reduced = continue_branch(mechanism.geometry, step_size=step_size, steps=n_steps)
    errors: list[float] = []
    for point in reduced.points:
        if not point.converged:
            continue
        q_source = mechanism.source_q_from_reduced(point.q)
        state = model.chain.evaluate(q_source)
        r_mapped = np.asarray(state.R, dtype=float)
        errors.append(min(_rotation_geodesic(r_mapped, r_source) for r_source in source_rs))
    if not errors:
        return None
    return float(max(errors))


def _orientation_summary(orientation: OrientationImageResult) -> dict[str, Any]:
    payload = orientation.to_json_dict()
    # Keep readout compact: drop per-sample matrices from ladder JSON.
    payload.pop("samples", None)
    return payload


@dataclass(frozen=True, slots=True)
class SpatialL4EvidenceBundle:
    """Shared ladder evidence for one spatial-4R L4 architecture."""

    architecture_id: str
    parent: SourceParentRecord
    fiber: SourceFiberRecord
    child: ChildMechanismRecord | None
    certificate: EquivalenceCertificateRecord
    leaf_predicate: LeafPredicateRecord | None
    reconstruction: ReconstructionRecord
    v05_certificate: dict[str, Any]
    comparison: dict[str, Any] | None
    orientation_image: dict[str, Any] | None
    max_orientation_error_rad: float | None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "parent": self.parent.to_dict(),
            "fiber": self.fiber.to_dict(),
            "child": None if self.child is None else self.child.to_dict(),
            "certificate": self.certificate.to_dict(),
            "leaf_predicate": None
            if self.leaf_predicate is None
            else self.leaf_predicate.to_dict(),
            "reconstruction": self.reconstruction.to_dict(),
            "v05_certificate": self.v05_certificate,
            "comparison": self.comparison,
            "orientation_image": self.orientation_image,
            "max_orientation_error_rad": self.max_orientation_error_rad,
            "notes": list(self.notes),
        }


def _parent_record(
    architecture_id: str,
    p_star: tuple[float, float, float],
    fiber_id: str,
) -> SourceParentRecord:
    return SourceParentRecord(
        rung=LadderRung.L4,
        parent_id=f"{architecture_id}_fixed_position",
        source_chain_id=architecture_id,
        task_point=p_star,
        dimension=1,
        target_space="Y1 ⊂ SO(3)",
        component_ids=(fiber_id,),
        process_status=ProcessStatus.SCAFFOLD,
        notes=(
            "L4 wraps the active V05 fixed-position parent; process stays SCAFFOLD.",
            "Target is a one-parameter orientation family, not dexterous_workspace.",
        ),
    )


def _fiber_record(
    *,
    architecture_id: str,
    parent_id: str,
    fiber_id: str,
    component_id: str,
    branch_status: str,
    returned: bool,
    sample_count: int,
    task_image_status: str,
) -> SourceFiberRecord:
    return SourceFiberRecord(
        rung=LadderRung.L4,
        fiber_id=fiber_id,
        parent_id=parent_id,
        component_id=component_id,
        slice_values=(),
        branch_status=branch_status,
        returned=returned,
        source_provenance="source_derived",
        sample_count=sample_count,
        task_image_status=task_image_status,
        notes=("Direct L4 leaf: no additional task/redundancy slices.",),
    )


def _child_from_mechanism(mechanism: IndependentClosedMechanism) -> ChildMechanismRecord:
    return ChildMechanismRecord(
        child_id=f"{mechanism.architecture_id}_sv_uphys_rr",
        source_fiber_id=mechanism.component_id,
        family="S_v-U_phys-R-R",
        joint_kind_sequence=mechanism.joint_kind_sequence_semantic,
        joint_role_sequence=mechanism.joint_role_sequence_semantic,
        expected_mobility=1,
        geometry_provenance="source_derived",
        status=CertificateStatus.EXACT_ON_COMPONENT,
        notes=(
            "Semantic roles keep U_phys; explorer tool_a/tool_beta are not L4 task evidence.",
            "Solver chart is cyclic URRS for SpatialFourBarGeometry only.",
            *mechanism.notes,
        ),
    )


def _certificate_from_v05(
    *,
    fiber_id: str,
    child_id: str,
    v05_cert: DecompositionCertificate,
    comparison: ClosedMechanismComparison | None,
) -> EquivalenceCertificateRecord:
    if comparison is not None and comparison.comparison_mode != "independent_closed_loop":
        closed = CertificateStatus.UNRESOLVED
        reason = (
            "Identity-on-same-chain / non-independent comparison cannot promote "
            f"closed_mechanism_status (mode={comparison.comparison_mode})."
        )
        scope = comparison.scope
        closure = _nonneg(comparison.max_closure_residual)
        tangent = _nonneg(comparison.seed_tangent_misalignment)
        pointing = _nonneg(comparison.max_pointing_error)
    else:
        closed = _status(v05_cert.closed_mechanism_status)
        reason = v05_cert.failure_or_scope_reason
        scope = (
            comparison.scope
            if comparison is not None
            else "aggregation_only_closed_unresolved"
        )
        closure = (
            _nonneg(comparison.max_closure_residual)
            if comparison is not None
            else None
        )
        tangent = (
            _nonneg(comparison.seed_tangent_misalignment)
            if comparison is not None
            else _nonneg(v05_cert.tangent_subspace_error)
        )
        pointing = (
            _nonneg(comparison.max_pointing_error)
            if comparison is not None
            else _nonneg(v05_cert.trajectory_pointing_error)
        )

    return EquivalenceCertificateRecord(
        source_fiber_id=fiber_id,
        child_id=child_id,
        axis_aggregation_status=_status(v05_cert.axis_aggregation_status),
        closed_mechanism_status=closed,
        component_scope=scope,
        coordinate_map=v05_cert.coordinate_map,
        reconstruction_map=v05_cert.inverse_or_reconstruction_map,
        closure_error=closure,
        tangent_error=tangent,
        task_map_error=pointing,
        reason=reason,
    )


def _reconstruction_record(
    *,
    parent_id: str,
    fiber_id: str,
    certificate: EquivalenceCertificateRecord,
    orientation_error: float | None,
    curve_type: str | None,
) -> ReconstructionRecord:
    accepted = certificate.accepted_for_reconstruction
    return ReconstructionRecord(
        rung=LadderRung.L4,
        parent_id=parent_id,
        target_space="Y1 ⊂ SO(3)",
        accepted_fiber_ids=(fiber_id,) if accepted else (),
        unresolved_fiber_ids=() if accepted else (fiber_id,),
        direct_coverage_status=(
            f"orientation_curve:{curve_type}" if curve_type else "orientation_curve:unavailable"
        ),
        reconstructed_coverage_status=(
            "matched_on_component"
            if accepted
            else "unresolved_or_rejected_closed_mechanism"
        ),
        comparison_error=_nonneg(orientation_error),
        process_status=ProcessStatus.SCAFFOLD,
        certificate_status=(
            CertificateStatus.EXACT_ON_COMPONENT
            if accepted
            else CertificateStatus.UNRESOLVED
        ),
        notes=(
            "Reconstruction is the claimed Y1 orientation/pointing curve on one component.",
            "Not dexterous_workspace / full SO(3) coverage.",
            (
                "Accepted from existing V05 independent closed-mechanism certificate."
                if accepted
                else "Closed-mechanism not accepted; reconstruction remains unresolved."
            ),
        ),
    )


def build_spatial_l4_exact_u_pair_bundle(
    *,
    n_steps: int = _DEFAULT_N_STEPS,
    step_size: float = _DEFAULT_STEP_SIZE,
    entry: Spatial4RCorpusEntry | None = None,
) -> SpatialL4EvidenceBundle:
    """Wrap the proximal exact_u_pair_4r V05D closed-mechanism evidence."""

    corpus = entry or build_exact_u_pair_4r()
    model = corpus.model
    aggregation = issue_axis_aggregation_certificate(model, corpus.regular_q)
    candidates = detect_exact_u_pairs(model)
    exact = next(candidate for candidate in candidates if candidate.exact_u_candidate)
    aggregated = build_aggregated_mechanism(model, exact)
    mechanism = build_independent_sv_uphys_rr(model, aggregated, corpus.regular_q)

    fiber = continue_fixed_position_fiber(
        model,
        corpus.regular_q,
        n_steps=n_steps,
        step_size=step_size,
        component_id=mechanism.component_id,
    )
    comparison = compare_independent_closed_mechanism(
        model,
        mechanism,
        source_fiber=fiber,
        n_steps=n_steps,
        step_size=step_size,
    )
    v05_cert = issue_closed_mechanism_certificate(aggregation, comparison)
    orientation = build_orientation_image(fiber, chain=model)
    orientation_error = max_mapped_orientation_error(
        model,
        mechanism,
        orientation,
        n_steps=n_steps,
        step_size=step_size,
    )

    fiber_id = fiber.component_id
    parent = _parent_record(model.architecture_id, fiber.p_star, fiber_id)
    fiber_rec = _fiber_record(
        architecture_id=model.architecture_id,
        parent_id=parent.parent_id,
        fiber_id=fiber_id,
        component_id=fiber.component_id,
        branch_status=comparison.source_branch_status,
        returned=comparison.source_returned,
        sample_count=comparison.source_sample_count,
        task_image_status=orientation.curve_type,
    )
    child = _child_from_mechanism(mechanism)
    certificate = _certificate_from_v05(
        fiber_id=fiber_id,
        child_id=child.child_id,
        v05_cert=v05_cert,
        comparison=comparison,
    )
    leaf = LeafPredicateRecord(
        child_id=child.child_id,
        branch_status=comparison.source_branch_status,
        returned=comparison.source_returned,
        coordinate_windings=(),
        coordinate_ranges=(),
        minimum_singularity_margin=None,
        evidence_scope="leaf_predicate_only; explorer tool_alpha/tool_beta not used",
        notes=(
            "L4 leaf evidence is the independent closed-loop comparison, not U_v windings.",
        ),
    )
    reconstruction = _reconstruction_record(
        parent_id=parent.parent_id,
        fiber_id=fiber_id,
        certificate=certificate,
        orientation_error=orientation_error,
        curve_type=orientation.curve_type,
    )
    return SpatialL4EvidenceBundle(
        architecture_id=model.architecture_id,
        parent=parent,
        fiber=fiber_rec,
        child=child,
        certificate=certificate,
        leaf_predicate=leaf,
        reconstruction=reconstruction,
        v05_certificate=v05_cert.to_json_dict(),
        comparison=comparison.to_json_dict(),
        orientation_image=_orientation_summary(orientation),
        max_orientation_error_rad=orientation_error,
        notes=(
            "Existing V05 independent S_v-U_phys-R-R solve wrapped into ladder records.",
            "Scoped EXACT_ON_COMPONENT only; multi-component EXACT_GLOBAL unverified.",
            "Scientific source: docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md / V05D.",
        ),
    )


def build_spatial_l4_generic_bundle(
    *,
    entry: Spatial4RCorpusEntry | None = None,
) -> SpatialL4EvidenceBundle:
    """Aggregation-only generic_4r path: closed mechanism stays UNRESOLVED."""

    corpus = entry or build_generic_4r()
    model = corpus.model
    v05_cert = issue_axis_aggregation_certificate(model, corpus.regular_q)
    fiber = continue_fixed_position_fiber(
        model,
        corpus.regular_q,
        n_steps=_DEFAULT_N_STEPS,
        step_size=_DEFAULT_STEP_SIZE,
        component_id=f"{model.architecture_id}_component0",
    )
    orientation = build_orientation_image(fiber, chain=model)
    fiber_id = fiber.component_id
    parent = _parent_record(model.architecture_id, fiber.p_star, fiber_id)
    fiber_rec = _fiber_record(
        architecture_id=model.architecture_id,
        parent_id=parent.parent_id,
        fiber_id=fiber_id,
        component_id=fiber.component_id,
        branch_status=fiber.branch_status,
        returned=fiber.returned,
        sample_count=len(fiber.accepted_samples),
        task_image_status=orientation.curve_type,
    )
    certificate = _certificate_from_v05(
        fiber_id=fiber_id,
        child_id="none",
        v05_cert=v05_cert,
        comparison=None,
    )
    # Force closed UNRESOLVED for aggregation-only (issuer already does this).
    certificate = EquivalenceCertificateRecord(
        source_fiber_id=certificate.source_fiber_id,
        child_id="none",
        axis_aggregation_status=certificate.axis_aggregation_status,
        closed_mechanism_status=CertificateStatus.UNRESOLVED,
        component_scope="aggregation_only_no_architecture_child",
        coordinate_map=certificate.coordinate_map,
        reconstruction_map=certificate.reconstruction_map,
        closure_error=None,
        tangent_error=None,
        task_map_error=None,
        reason=(
            "generic_4r has no exact proximal U architecture child; "
            "closed_mechanism_status remains UNRESOLVED."
        ),
    )
    reconstruction = _reconstruction_record(
        parent_id=parent.parent_id,
        fiber_id=fiber_id,
        certificate=certificate,
        orientation_error=None,
        curve_type=orientation.curve_type,
    )
    return SpatialL4EvidenceBundle(
        architecture_id=model.architecture_id,
        parent=parent,
        fiber=fiber_rec,
        child=None,
        certificate=certificate,
        leaf_predicate=None,
        reconstruction=reconstruction,
        v05_certificate=v05_cert.to_json_dict(),
        comparison=None,
        orientation_image=_orientation_summary(orientation),
        max_orientation_error_rad=None,
        notes=(
            "Generic architecture rejection/absence of exact U: no L4 child promotion.",
            "Orientation curve may still be exported as source truth without a child map.",
        ),
    )


def ladder_certificate_from_forged_identity(
    *,
    entry: Spatial4RCorpusEntry | None = None,
) -> EquivalenceCertificateRecord:
    """False-pass guard: identity comparison must not accept L4 closed status."""

    corpus = entry or build_exact_u_pair_4r()
    aggregation = issue_axis_aggregation_certificate(corpus.model, corpus.regular_q)
    candidates = detect_exact_u_pairs(corpus.model)
    exact = next(candidate for candidate in candidates if candidate.exact_u_candidate)
    aggregated = build_aggregated_mechanism(corpus.model, exact)
    mechanism = build_independent_sv_uphys_rr(corpus.model, aggregated, corpus.regular_q)
    forged = forged_identity_comparison(mechanism)
    v05_cert = issue_closed_mechanism_certificate(aggregation, forged)
    return _certificate_from_v05(
        fiber_id=mechanism.component_id,
        child_id=f"{mechanism.architecture_id}_sv_uphys_rr",
        v05_cert=v05_cert,
        comparison=forged,
    )


def default_l4_equivalence_payload() -> dict[str, Any]:
    """Machine-readable L4 section for ladder readouts."""

    exact = build_spatial_l4_exact_u_pair_bundle()
    generic = build_spatial_l4_generic_bundle()
    return {
        "note": (
            "L4 wraps existing V05 closed-mechanism evidence into shared ladder records. "
            "Scientific source remains docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md "
            "and results/kinematic_decomposition/v05d/."
        ),
        "v05d_readout": "results/kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html",
        "bundles": [exact.to_dict(), generic.to_dict()],
        "summaries": [
            {
                "architecture_id": exact.architecture_id,
                "axis_aggregation_status": exact.certificate.axis_aggregation_status.value,
                "closed_mechanism_status": exact.certificate.closed_mechanism_status.value,
                "orientation_curve_type": (
                    None
                    if exact.orientation_image is None
                    else exact.orientation_image.get("curve_type")
                ),
                "reconstruction_status": exact.reconstruction.certificate_status.value,
                "max_orientation_error_rad": exact.max_orientation_error_rad,
                "independent_reduced_solve_present": bool(
                    (exact.comparison or {}).get("independent_reduced_solve_present")
                ),
            },
            {
                "architecture_id": generic.architecture_id,
                "axis_aggregation_status": generic.certificate.axis_aggregation_status.value,
                "closed_mechanism_status": generic.certificate.closed_mechanism_status.value,
                "orientation_curve_type": (
                    None
                    if generic.orientation_image is None
                    else generic.orientation_image.get("curve_type")
                ),
                "reconstruction_status": generic.reconstruction.certificate_status.value,
                "max_orientation_error_rad": generic.max_orientation_error_rad,
                "independent_reduced_solve_present": False,
            },
        ],
    }
