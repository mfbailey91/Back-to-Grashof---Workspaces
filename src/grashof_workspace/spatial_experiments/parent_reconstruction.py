"""V06E: source-fiber reconstruction vs accepted-child reconstruction.

Stage 1 paints task-derived h=c fibers onto the frozen V06C sphere grid.
Stage 2 includes only EXACT_GLOBAL / EXACT_ON_COMPONENT children (none in V06D2).
Neither stage is the 2D parent or descriptor-discovery evidence.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from math import isfinite
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .continuation import wrap_joint_delta
from .open_chain import OpenChainModel
from .orientation_image import _pointing_geodesic
from .parent_atlas import ParentAtlasResult
from .parent_level_sets import (
    CRITICAL_H_TOL,
    ParentLevelSetResult,
    SourceLevelSetFiber,
    VertexScalarRecord,
    continue_level_set,
)
from .parent_task_images import (
    CoverageLabel,
    SourceTaskImageBundle,
    SphereCellKind,
    SphereGridCell,
)

Array = NDArray[np.floating]

ACCEPTED_CHILD_STATUSES = frozenset({"EXACT_GLOBAL", "EXACT_ON_COMPONENT"})
FACTORIZATION_ALLOWED = frozenset(
    {
        "exact product",
        "fiber bundle / sequential structure",
        "conditional factorization",
        "component-limited reconstruction",
        "no valid recombination",
        "unresolved",
    }
)


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float) and not isfinite(obj):
        return None
    return obj


def _json_object(obj: dict[str, Any]) -> dict[str, Any]:
    payload = _json_safe(obj)
    if not isinstance(payload, dict):
        raise TypeError("expected a JSON object")
    return payload


def _cell_index(barys: Array, d: Array) -> int:
    v = np.asarray(d, dtype=float).reshape(3)
    nrm = float(np.linalg.norm(v))
    if nrm <= 1e-15:
        return 0
    v = v / nrm
    return int(np.argmax(barys @ v))


def paint_pointing_hits(
    grid_cells: Sequence[SphereGridCell],
    samples_d: list[tuple[float, float, float]],
) -> set[int]:
    barys = np.asarray([c.barycenter for c in grid_cells], dtype=float)
    hits: set[int] = set()
    for d in samples_d:
        hits.add(_cell_index(barys, np.asarray(d, dtype=float)))
    return hits


def _hausdorff(a: list[Array], b: list[Array]) -> float:
    if not a or not b:
        return float("inf")

    def _one_way(src: list[Array], dst: list[Array]) -> float:
        worst = 0.0
        for p in src:
            best = min(_pointing_geodesic(p, q) for q in dst)
            worst = max(worst, best)
        return worst

    return max(_one_way(a, b), _one_way(b, a))


def _seed_for_c(
    vertices: Sequence[VertexScalarRecord],
    c: float,
) -> tuple[float, ...] | None:
    for i, va in enumerate(vertices):
        for vb in vertices[i + 1 :]:
            if (va.h - c) * (vb.h - c) >= 0.0:
                continue
            t = (c - va.h) / (vb.h - va.h)
            delta = wrap_joint_delta(np.asarray(vb.q), np.asarray(va.q))
            q = np.asarray(va.q, dtype=float) + t * delta
            return tuple(float(v) for v in q)
    return None


def _extra_slice_values(level_sets: ParentLevelSetResult) -> tuple[float, ...]:
    regular_h = [v.h for v in level_sets.vertices if v.regular]
    if len(regular_h) < 2:
        return ()
    lo, hi = min(regular_h), max(regular_h)
    raw = (lo + 0.125 * (hi - lo), lo + 0.875 * (hi - lo))
    extra = []
    existing = list(level_sets.slice_values) + list(level_sets.critical_h_values)
    for c in raw:
        if any(abs(c - e) <= CRITICAL_H_TOL for e in existing):
            continue
        extra.append(float(c))
    return tuple(extra[:2])


def _continue_extra_fibers(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    level_sets: ParentLevelSetResult,
    extra_cs: tuple[float, ...],
) -> tuple[SourceLevelSetFiber, ...]:
    added: list[SourceLevelSetFiber] = []
    for c in extra_cs:
        seed = _seed_for_c(level_sets.vertices, c)
        if seed is None:
            continue
        samples, status, returned = continue_level_set(
            model, seed, atlas.p_star, level_sets.n, c
        )
        added.append(
            SourceLevelSetFiber(
                fiber_id=f"{atlas.architecture_id}_h{c:.4f}_refine",
                parent_id=level_sets.parent_id,
                parent_component_id=atlas.component_ids[0] if atlas.component_ids else None,
                n=level_sets.n,
                c=c,
                provenance="task-derived",
                branch_status=status,
                returned=returned,
                samples=samples,
                contour_id=f"refine_c{c:.4f}",
                seed_to_contour_distance=0.0,
                unresolved_reason=None if status != "unresolved" else "refine corrector failure",
                joint_limits="not_modeled",
                notes=("Adaptive extra slice; not a complete foliation.",),
            )
        )
    return tuple(added)


@dataclass(frozen=True, slots=True)
class ReconstructionMetrics:
    direct_covered: int
    direct_uncovered: int
    direct_ambiguous: int
    direct_unresolved: int
    fiber_hit_cells: int
    child_hit_cells: int
    missed_covered_fraction: float
    false_positive_fraction: float
    ambiguous_boundary_fraction: float
    hausdorff_rad: float | None
    multiplicity_discrepancy: str
    source_component_discrepancy: str
    critical_c_values: tuple[float, ...]
    unresolved_c_intervals: tuple[str, ...]
    fiber_returned: int
    fiber_open: int
    fiber_unresolved: int
    fiber_singular: int
    accepted_child_count: int
    excluded_local_only_children: int

    def to_json_dict(self) -> dict[str, Any]:
        return _json_object(
            {
                "direct_source_covered_cells": self.direct_covered,
                "direct_source_uncovered_cells": self.direct_uncovered,
                "direct_source_ambiguous_cells": self.direct_ambiguous,
                "direct_source_unresolved_cells": self.direct_unresolved,
                "source_fiber_reconstructed_cells": self.fiber_hit_cells,
                "accepted_child_reconstructed_cells": self.child_hit_cells,
                "missed_cell_fraction": self.missed_covered_fraction,
                "false_positive_fraction": self.false_positive_fraction,
                "ambiguous_boundary_fraction": self.ambiguous_boundary_fraction,
                "symmetric_angular_hausdorff_rad": self.hausdorff_rad,
                "pointing_multiplicity_discrepancy": self.multiplicity_discrepancy,
                "source_component_discrepancy": self.source_component_discrepancy,
                "critical_c_values": list(self.critical_c_values),
                "unresolved_c_intervals": list(self.unresolved_c_intervals),
                "fiber_returned_count": self.fiber_returned,
                "fiber_open_count": self.fiber_open,
                "fiber_unresolved_count": self.fiber_unresolved,
                "fiber_singular_count": self.fiber_singular,
                "accepted_child_count": self.accepted_child_count,
                "excluded_local_only_children": self.excluded_local_only_children,
            }
        )


@dataclass(frozen=True, slots=True)
class RefinementStep:
    c: float
    reason: str
    missed_fraction_before: float
    missed_fraction_after: float

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "c": self.c,
            "reason": self.reason,
            "missed_fraction_before": self.missed_fraction_before,
            "missed_fraction_after": self.missed_fraction_after,
        }


@dataclass(frozen=True, slots=True)
class ParentReconstructionResult:
    architecture_id: str
    icosphere_level: int
    coverage_label: str
    reconstruction_coverage: str
    complete_foliation: bool
    factorization_status: str
    reconstruction_law: str
    v06_program_passed: bool
    v06_gate: dict[str, bool]
    metrics: ReconstructionMetrics
    fiber_hit_cell_ids: tuple[int, ...]
    missed_covered_cell_ids: tuple[int, ...]
    refinement_history: tuple[RefinementStep, ...]
    extra_fiber_ids: tuple[str, ...]
    notes: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return _json_object(
            {
                "architecture_id": self.architecture_id,
                "certificate_status": None,
                "icosphere_level": self.icosphere_level,
                "direct_coverage_label": self.coverage_label,
                "reconstruction_coverage": self.reconstruction_coverage,
                "complete_foliation": self.complete_foliation,
                "factorization_status": self.factorization_status,
                "reconstruction_law": self.reconstruction_law,
                "v06_program_passed": self.v06_program_passed,
                "v06_gate": self.v06_gate,
                "metrics": self.metrics.to_json_dict(),
                "fiber_hit_cell_ids": list(self.fiber_hit_cell_ids),
                "missed_covered_cell_ids": list(self.missed_covered_cell_ids),
                "refinement_history": [s.to_json_dict() for s in self.refinement_history],
                "extra_fiber_ids": list(self.extra_fiber_ids),
                "joint_limits": "not_modeled",
                "notes": list(self.notes),
            }
        )


def _metrics(
    images: SourceTaskImageBundle,
    fibers: tuple[SourceLevelSetFiber, ...],
    fiber_hits: set[int],
    child_hits: set[int],
    *,
    accepted_child_count: int,
    excluded_local_only: int,
) -> tuple[ReconstructionMetrics, tuple[int, ...]]:
    cells = images.pointing.sphere_grid.cells
    covered = [c for c in cells if c.kind is SphereCellKind.COVERED]
    uncovered = [c for c in cells if c.kind is SphereCellKind.UNCOVERED]
    ambiguous = [c for c in cells if c.kind is SphereCellKind.AMBIGUOUS_BOUNDARY]
    unresolved = [c for c in cells if c.kind is SphereCellKind.UNRESOLVED]
    missed = [c.cell_id for c in covered if c.cell_id not in fiber_hits]
    fp = [c.cell_id for c in uncovered if c.cell_id in fiber_hits]
    n_cov = max(1, len(covered))
    n_unc = max(1, len(uncovered))
    n_cells = max(1, len(cells))
    fiber_d = [
        np.asarray(s.pointing, dtype=float)
        for f in fibers
        for s in f.samples
    ]
    direct_d = [np.asarray(p, dtype=float) for p in images.pointing.spherical_vertices]
    haus = None if not fiber_d or not direct_d else _hausdorff(fiber_d, direct_d)
    returned = sum(1 for f in fibers if f.returned)
    open_n = sum(1 for f in fibers if f.branch_status == "open")
    unres = sum(1 for f in fibers if f.branch_status == "unresolved")
    sing = sum(1 for f in fibers if f.branch_status == "singular")
    unresolved_c = tuple(
        f"skipped_or_open:{f.branch_status}:c={f.c:.4f}"
        for f in fibers
        if f.branch_status in {"unresolved", "open", "singular"}
    )
    metrics = ReconstructionMetrics(
        direct_covered=len(covered),
        direct_uncovered=len(uncovered),
        direct_ambiguous=len(ambiguous),
        direct_unresolved=len(unresolved),
        fiber_hit_cells=len(fiber_hits),
        child_hit_cells=len(child_hits),
        missed_covered_fraction=len(missed) / n_cov,
        false_positive_fraction=len(fp) / n_unc,
        ambiguous_boundary_fraction=len(ambiguous) / n_cells,
        hausdorff_rad=haus,
        multiplicity_discrepancy="unresolved: fiber samples are 1D traces, V06C clusters are 2D atlas vertices",
        source_component_discrepancy=(
            "one seed component represented; extra components unresolved "
            f"(atlas components={list(images.pointing.component_ids)})"
        ),
        critical_c_values=(),
        unresolved_c_intervals=unresolved_c,
        fiber_returned=returned,
        fiber_open=open_n,
        fiber_unresolved=unres,
        fiber_singular=sing,
        accepted_child_count=accepted_child_count,
        excluded_local_only_children=excluded_local_only,
    )
    return metrics, tuple(missed)


def build_parent_reconstruction(
    atlas: ParentAtlasResult,
    model: OpenChainModel,
    images: SourceTaskImageBundle,
    level_sets: ParentLevelSetResult,
    *,
    accepted_child_pointing: tuple[tuple[float, float, float], ...] = (),
    accepted_child_count: int = 0,
    excluded_local_only_children: int = 1,
) -> ParentReconstructionResult:
    """Stage 1 fiber paint vs V06C grid; stage 2 empty unless EXACT_* pointing is supplied."""

    cells = images.pointing.sphere_grid.cells
    fibers = list(level_sets.fibers)
    sample_d = [s.pointing for f in fibers for s in f.samples]
    fiber_hits = paint_pointing_hits(cells, sample_d)
    metrics, missed = _metrics(
        images,
        tuple(fibers),
        fiber_hits,
        set(),
        accepted_child_count=0,
        excluded_local_only=excluded_local_only_children,
    )
    history: list[RefinementStep] = []
    extra_ids: list[str] = []
    if missed:
        extra_cs = _extra_slice_values(level_sets)
        before = metrics.missed_covered_fraction
        extra_fibers = _continue_extra_fibers(atlas, model, level_sets, extra_cs)
        fibers.extend(extra_fibers)
        extra_ids = [f.fiber_id for f in extra_fibers]
        sample_d = [s.pointing for f in fibers for s in f.samples]
        fiber_hits = paint_pointing_hits(cells, sample_d)
        metrics, missed = _metrics(
            images,
            tuple(fibers),
            fiber_hits,
            set(),
            accepted_child_count=0,
            excluded_local_only=excluded_local_only_children,
        )
        for c in extra_cs:
            history.append(
                RefinementStep(
                    c=c,
                    reason="missed direct COVERED cells after initial D1 slices",
                    missed_fraction_before=before,
                    missed_fraction_after=metrics.missed_covered_fraction,
                )
            )
    metrics = replace(metrics, critical_c_values=level_sets.critical_h_values)
    child_hits: set[int] = set()
    if accepted_child_count > 0 and accepted_child_pointing:
        child_hits = paint_pointing_hits(cells, list(accepted_child_pointing))
        metrics = replace(
            metrics,
            child_hit_cells=len(child_hits),
            accepted_child_count=accepted_child_count,
        )
    factorization = "no valid recombination"
    if accepted_child_count == 0 and metrics.missed_covered_fraction >= 0.99:
        factorization = "unresolved"
    recon_cov = "PARTIAL"
    if images.pointing.coverage_label is CoverageLabel.UNRESOLVED:
        recon_cov = "UNRESOLVED"
    gate = {
        "independent_2d_source_parent": True,
        "frozen_orientation_and_pointing_images": True,
        "explicit_task_fiber_provenance": True,
        "compound_parent_certified_or_rejected": True,
        "source_fiber_reconstruction_compared": True,
        "child_reconstruction_only_accepted": True,
        "factorization_status_explicit": True,
        "coverage_qualified_by_declared_resolution": True,
        "critical_unresolved_limits_explicit": True,
        "complete_s2_coverage": False,
        "accepted_child_factorization": False,
        "parent_component_complete": False,
    }
    v06_passed = False
    return ParentReconstructionResult(
        architecture_id=atlas.architecture_id,
        icosphere_level=images.pointing.sphere_grid.subdivision_level,
        coverage_label=images.pointing.coverage_label.value,
        reconstruction_coverage=recon_cov,
        complete_foliation=False,
        factorization_status=factorization,
        reconstruction_law=(
            "none issued; a few open task-derived fibers are not a reconstruction law"
        ),
        v06_program_passed=v06_passed,
        v06_gate=gate,
        metrics=metrics,
        fiber_hit_cell_ids=tuple(sorted(fiber_hits)),
        missed_covered_cell_ids=missed,
        refinement_history=tuple(history),
        extra_fiber_ids=tuple(extra_ids),
        notes=(
            "V06E stage 1 paints source fibers onto the frozen V06C grid (ADR-042).",
            "V06D2 LOCAL_ONLY UUUR is excluded from stage 2.",
            "Not S^2 completeness, not exact product, not descriptor discovery (ADR-026).",
            "Joint limits not_modeled.",
        ),
    )


def reconstruction_summary(result: ParentReconstructionResult) -> dict[str, Any]:
    return {
        "architecture_id": result.architecture_id,
        "reconstruction_coverage": result.reconstruction_coverage,
        "complete_foliation": result.complete_foliation,
        "factorization_status": result.factorization_status,
        "v06_program_passed": result.v06_program_passed,
        "fiber_hit_cells": result.metrics.fiber_hit_cells,
        "missed_cell_fraction": result.metrics.missed_covered_fraction,
        "accepted_child_count": result.metrics.accepted_child_count,
        "hausdorff_rad": result.metrics.hausdorff_rad,
        "certificate_status": None,
    }
