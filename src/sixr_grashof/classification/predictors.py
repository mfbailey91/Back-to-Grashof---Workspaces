"""Analytical orientation-capability predictors (Sprint 3).

Wraps McCarthy–Soh classification with explicit hand-link assignment and
reduction-status gating. Dexterity candidates are never inferred from the
Grashof product alone.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from sixr_grashof.architectures import ArchitectureA, ArchitectureParams
from sixr_grashof.classification.mccarthy_soh import (
    SphericalClassification,
    classify_spherical,
)
from sixr_grashof.reductions.engine import reduce_architecture_a
from sixr_grashof.reductions.types import CombinedReduction, SphericalOrientationReduction

HandLinkAssignment = Literal["beta", "alpha"]
DEXTERITY_CANDIDATE_TYPES = frozenset({2, 3, 10, 11})
ALPHA_CANDIDATE_TYPES = frozenset({1, 3, 9, 11})


class HandLinkRole(str, Enum):
    """Which virtual spherical link represents hand orientation."""

    BETA = "beta"  # default output-hand convention
    ALPHA = "alpha"  # sensitivity: treat input as hand link


@dataclass(frozen=True, slots=True)
class OrientationPrediction:
    """Full §6.5 analytical prediction record."""

    architecture_id: str
    joint_configuration: tuple[float, float, float, float, float, float]
    reduction_status: str
    concurrency_residual: float
    rho_w: float | None
    spherical_link_angles: tuple[float, float, float, float] | None
    T1: float | None
    T2: float | None
    T3: float | None
    T4: float | None
    sign_tuple: tuple[int, int, int, int] | None
    T_product: float | None
    grashof_family: str
    linkage_type: int | None
    linkage_name: str
    equivalent_type: int | None
    wrap_around: bool
    input_motion_class: str
    output_motion_class: str
    hand_orientation_link: str
    hand_link_motion_class: str
    dexterity_candidate_hypothesis: bool
    is_boundary: bool
    boundary_indices: tuple[int, ...]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _relabel_for_hand_assignment(
    classification: SphericalClassification,
    *,
    hand_link: HandLinkRole,
) -> tuple[str, str, bool]:
    """Return (hand_link_name, hand_motion_class, dexterity_candidate)."""
    if hand_link is HandLinkRole.BETA:
        hand_class = classification.hand_link_motion_class
        candidate = (
            classification.linkage_type in DEXTERITY_CANDIDATE_TYPES
            and hand_class == "crank"
            and not classification.is_boundary
        )
        return ("beta", hand_class, candidate)

    # Sensitivity: treat input (alpha) as the hand-orientation link.
    # Under this assignment, candidates are types where INPUT is a crank:
    # crank-rocker and double-crank → types {1, 3, 9, 11}.
    hand_class = classification.input_motion_class
    candidate = (
        classification.linkage_type in ALPHA_CANDIDATE_TYPES
        and hand_class == "crank"
        and not classification.is_boundary
    )
    return ("alpha", hand_class, candidate)


def predict_from_spherical(
    spherical: SphericalOrientationReduction,
    *,
    architecture_id: str,
    joint_configuration: tuple[float, float, float, float, float, float],
    hand_link: HandLinkRole = HandLinkRole.BETA,
    rho_w: float | None = None,
) -> OrientationPrediction:
    """Predict from a spherical reduction; withhold T_i when invalid."""
    if spherical.status == "invalid" or spherical.linkage is None:
        return OrientationPrediction(
            architecture_id=architecture_id,
            joint_configuration=joint_configuration,
            reduction_status=spherical.status,
            concurrency_residual=spherical.concurrency.residual_rho,
            rho_w=rho_w,
            spherical_link_angles=None,
            T1=None,
            T2=None,
            T3=None,
            T4=None,
            sign_tuple=None,
            T_product=None,
            grashof_family="not_applicable",
            linkage_type=None,
            linkage_name="invalid-reduction",
            equivalent_type=None,
            wrap_around=False,
            input_motion_class="not_applicable",
            output_motion_class="not_applicable",
            hand_orientation_link=hand_link.value,
            hand_link_motion_class="not_applicable",
            dexterity_candidate_hypothesis=False,
            is_boundary=False,
            boundary_indices=(),
            notes=spherical.notes or "invalid reduction; prediction withheld",
        )

    classification = classify_spherical(spherical.linkage)
    hand_name, hand_class, candidate = _relabel_for_hand_assignment(
        classification, hand_link=hand_link
    )
    # Never allow product alone to mark dexterity: candidate already requires crank hand.
    if hand_class != "crank":
        candidate = False

    return OrientationPrediction(
        architecture_id=architecture_id,
        joint_configuration=joint_configuration,
        reduction_status=spherical.status,
        concurrency_residual=spherical.concurrency.residual_rho,
        rho_w=rho_w,
        spherical_link_angles=(
            spherical.linkage.alpha,
            spherical.linkage.beta,
            spherical.linkage.gamma,
            spherical.linkage.eta,
        ),
        T1=classification.T1,
        T2=classification.T2,
        T3=classification.T3,
        T4=classification.T4,
        sign_tuple=classification.sign_tuple,
        T_product=classification.T_product,
        grashof_family=classification.grashof_family,
        linkage_type=classification.linkage_type,
        linkage_name=classification.linkage_name,
        equivalent_type=classification.equivalent_type,
        wrap_around=classification.wrap_around,
        input_motion_class=classification.input_motion_class,
        output_motion_class=classification.output_motion_class,
        hand_orientation_link=hand_name,
        hand_link_motion_class=hand_class,
        dexterity_candidate_hypothesis=candidate,
        is_boundary=classification.is_boundary,
        boundary_indices=classification.boundary_indices,
        notes=spherical.notes,
    )


def predict_orientation_capability(
    reduction: CombinedReduction,
    *,
    hand_link: HandLinkRole = HandLinkRole.BETA,
) -> OrientationPrediction:
    """Full analytical prediction from a combined regional+spherical reduction."""
    return predict_from_spherical(
        reduction.spherical,
        architecture_id=reduction.architecture_id,
        joint_configuration=reduction.joint_configuration,
        hand_link=hand_link,
        rho_w=reduction.regional.rho_w,
    )


def architecture_a_type_map(
    *,
    n_radial: int = 12,
    n_elbow: int = 8,
    params: ArchitectureParams | None = None,
    hand_link: HandLinkRole = HandLinkRole.BETA,
) -> list[OrientationPrediction]:
    """Sample Architecture A configurations and return prediction records.

    Sweeps elbow-like joints ``q2,q3`` over a grid with ``q1=q4=q5=q6=0``.
    """
    arch = ArchitectureA(params)
    rows: list[OrientationPrediction] = []
    for i in range(n_radial):
        q2 = -math.pi / 3 + (2 * math.pi / 3) * (i / max(n_radial - 1, 1))
        for j in range(n_elbow):
            q3 = -math.pi / 3 + (2 * math.pi / 3) * (j / max(n_elbow - 1, 1))
            q = (0.0, q2, q3, 0.0, 0.0, 0.0)
            reduction = reduce_architecture_a(arch, q)
            if not reduction.regional.wrist_reachable:
                continue
            rows.append(predict_orientation_capability(reduction, hand_link=hand_link))
    return rows


def write_type_map_csv(rows: list[OrientationPrediction], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "q2",
        "q3",
        "rho_w",
        "reduction_status",
        "linkage_type",
        "linkage_name",
        "grashof_family",
        "hand_orientation_link",
        "hand_link_motion_class",
        "dexterity_candidate_hypothesis",
        "T_product",
        "concurrency_residual",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "q2": row.joint_configuration[1],
                    "q3": row.joint_configuration[2],
                    "rho_w": row.rho_w if row.rho_w is not None else "",
                    "reduction_status": row.reduction_status,
                    "linkage_type": row.linkage_type,
                    "linkage_name": row.linkage_name,
                    "grashof_family": row.grashof_family,
                    "hand_orientation_link": row.hand_orientation_link,
                    "hand_link_motion_class": row.hand_link_motion_class,
                    "dexterity_candidate_hypothesis": row.dexterity_candidate_hypothesis,
                    "T_product": row.T_product,
                    "concurrency_residual": row.concurrency_residual,
                }
            )
    return path


def write_type_map_json(rows: list[OrientationPrediction], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [r.to_dict() for r in rows]
    for item in payload:
        item["joint_configuration"] = list(item["joint_configuration"])
        if item["spherical_link_angles"] is not None:
            item["spherical_link_angles"] = list(item["spherical_link_angles"])
        if item["sign_tuple"] is not None:
            item["sign_tuple"] = list(item["sign_tuple"])
        item["boundary_indices"] = list(item["boundary_indices"])
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
