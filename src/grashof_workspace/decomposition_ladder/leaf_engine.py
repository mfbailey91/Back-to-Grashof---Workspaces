"""Adapter from source-derived ladder fibers to the existing spatial four-bar leaf solver.

The existing spatial-four-bar explorer remains the numerical leaf engine. This
adapter requires a real ``EquivalenceCertificateRecord`` before a winding result
can be promoted beyond ``mechanism_explorer_only`` / unresolved correspondence.
Caller-supplied status strings alone cannot promote evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from grashof_workspace.spatial4bar_explorer.geometry import SpatialFourBarGeometry
from grashof_workspace.spatial4bar_explorer.winding import classify_geometry

from .models import EquivalenceCertificateRecord, UDriveContract
from .u_drive import free_branch_contract


@dataclass(frozen=True, slots=True)
class LeafSolveRequest:
    """One certified or exploratory one-DOF child solve request."""

    geometry: SpatialFourBarGeometry
    sample_id: str
    source_rung: str
    source_parent_id: str
    source_component_id: str
    slice_id: str
    source_provenance: str
    certificate: EquivalenceCertificateRecord | None = None
    drive_contract: UDriveContract = field(default_factory=free_branch_contract)


@dataclass(frozen=True, slots=True)
class LeafSolveResult:
    """Winding result plus source-chain evidence qualification."""

    sample_id: str
    family: str
    source_rung: str
    source_parent_id: str
    source_component_id: str
    slice_id: str
    source_provenance: str
    evidence_scope: str
    axis_aggregation_status: str | None
    closed_mechanism_status: str | None
    drive_contract: UDriveContract
    cycle_status: str
    returned: bool
    direction: int
    coordinate_names: tuple[str, ...]
    w_alpha: int | None
    w_beta: int | None
    class_alpha: str
    class_beta: str
    tool_range_alpha: float | None
    tool_range_beta: float | None
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "family": self.family,
            "source_rung": self.source_rung,
            "source_parent_id": self.source_parent_id,
            "source_component_id": self.source_component_id,
            "slice_id": self.slice_id,
            "source_provenance": self.source_provenance,
            "evidence_scope": self.evidence_scope,
            "axis_aggregation_status": self.axis_aggregation_status,
            "closed_mechanism_status": self.closed_mechanism_status,
            "drive_contract": self.drive_contract.to_dict(),
            "cycle_status": self.cycle_status,
            "returned": self.returned,
            "direction": self.direction,
            "coordinate_names": list(self.coordinate_names),
            "w_alpha": self.w_alpha,
            "w_beta": self.w_beta,
            "class_alpha": self.class_alpha,
            "class_beta": self.class_beta,
            "tool_range_alpha": self.tool_range_alpha,
            "tool_range_beta": self.tool_range_beta,
            "notes": list(self.notes),
        }


def _evidence_scope(request: LeafSolveRequest) -> str:
    """Qualify evidence using a real certificate object, never caller strings alone."""

    if request.source_provenance == "mechanism_explorer_only":
        return "mechanism_explorer_only"
    if request.certificate is None:
        return "unresolved_source_correspondence"
    if (
        request.certificate.accepted_for_reconstruction
        and request.source_provenance == "source_derived"
    ):
        return "source_chain_evidence"
    return "unresolved_source_correspondence"


def solve_spatial_fourbar_leaf(
    request: LeafSolveRequest,
    *,
    step_size: float = 0.05,
    max_steps: int = 2000,
) -> LeafSolveResult:
    """Run the current four-bar branch/winding solver with provenance intact."""

    classification = classify_geometry(
        request.geometry,
        sample_id=request.sample_id,
        step_size=step_size,
        max_steps=max_steps,
    )
    cycle = classification.cycle
    scope = _evidence_scope(request)
    certificate = request.certificate
    notes = (
        *classification.notes,
        f"drive_mode={request.drive_contract.mode.value}",
        f"evidence_scope={scope}",
        "alpha and beta are read from the same one-DOF returned branch",
        "promotion requires EquivalenceCertificateRecord.accepted_for_reconstruction",
    )
    return LeafSolveResult(
        sample_id=request.sample_id,
        family=classification.family,
        source_rung=request.source_rung,
        source_parent_id=request.source_parent_id,
        source_component_id=request.source_component_id,
        slice_id=request.slice_id,
        source_provenance=request.source_provenance,
        evidence_scope=scope,
        axis_aggregation_status=(
            None if certificate is None else certificate.axis_aggregation_status.value
        ),
        closed_mechanism_status=(
            None if certificate is None else certificate.closed_mechanism_status.value
        ),
        drive_contract=request.drive_contract,
        cycle_status=cycle.status,
        returned=cycle.returned,
        direction=cycle.direction,
        coordinate_names=cycle.coordinate_names,
        w_alpha=classification.w_alpha,
        w_beta=classification.w_beta,
        class_alpha=classification.class_alpha.value,
        class_beta=classification.class_beta.value,
        tool_range_alpha=classification.tool_range_alpha,
        tool_range_beta=classification.tool_range_beta,
        notes=notes,
    )
