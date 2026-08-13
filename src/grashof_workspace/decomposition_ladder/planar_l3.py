"""L3 adapter for the trusted planar 3R → exact planar 4R calibration.

This module does not replace the existing analytical kernel. It wraps one
radius-level result in the decomposition-ladder vocabulary so later spatial
rungs can be compared against a known exact example.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from grashof_workspace.planar3r import DEFAULT_TOL, Planar3R

from .models import CertificateStatus, LadderRung


@dataclass(frozen=True, slots=True)
class PlanarL3CalibrationResult:
    """Exact source/child/predicate/reconstruction record at one radius."""

    rung: LadderRung
    rho: float
    source_chain: str
    source_lengths: tuple[float, float, float]
    source_parent_mobility: int
    target_space: str
    virtual_closure: str
    child_family: str
    child_loop_lengths: tuple[float, float, float, float]
    assemblable: bool
    grashof_class: str
    inversion_type: str
    designated_input_can_fully_rotate: bool
    dexterous: bool
    decomposition_status: CertificateStatus
    certificate_scope: str
    predicate_reconstruction_match: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rung"] = self.rung.value
        payload["decomposition_status"] = self.decomposition_status.value
        return payload


def evaluate_planar_l3(
    arm: Planar3R,
    rho: float,
    *,
    tol: float = DEFAULT_TOL,
) -> PlanarL3CalibrationResult:
    """Evaluate the exact L3 decomposition contract at Cartesian radius ``rho``."""

    linkage = arm.fourbar_at_radius(rho)
    state = arm.mechanism_state(rho, tol=tol)
    rotatable = linkage.input_can_fully_rotate(tol=tol)
    dexterous = arm.is_dexterous_radius(rho, tol=tol)
    return PlanarL3CalibrationResult(
        rung=LadderRung.L3,
        rho=float(rho),
        source_chain="planar 3R",
        source_lengths=(arm.l1, arm.l2, arm.l3),
        source_parent_mobility=1,
        target_space="SO(2)",
        virtual_closure="exact virtual revolute closure R_v at p*",
        child_family="planar 4R",
        child_loop_lengths=linkage.lengths,
        assemblable=state.assemblable,
        grashof_class=state.grashof_class,
        inversion_type=state.inversion_type,
        designated_input_can_fully_rotate=rotatable,
        dexterous=dexterous,
        decomposition_status=CertificateStatus.EXACT_GLOBAL,
        certificate_scope=(
            "exact 3R↔4R map at this radius, including non-assemblable exterior radii; "
            "dexterity/rotatability are separate predicates"
        ),
        predicate_reconstruction_match=rotatable == dexterous,
        notes=(
            "Exact designated-link rotatability, not the textual Grashof label, is the predicate.",
            "This is the trusted calibration rung for the ladder interfaces.",
            "EXACT_GLOBAL certifies the analytical map, not workspace membership.",
        ),
    )


def evaluate_planar_l3_radii(
    arm: Planar3R,
    radii: tuple[float, ...],
    *,
    tol: float = DEFAULT_TOL,
) -> tuple[PlanarL3CalibrationResult, ...]:
    """Evaluate a deterministic set of planar calibration radii."""

    return tuple(evaluate_planar_l3(arm, rho, tol=tol) for rho in radii)
