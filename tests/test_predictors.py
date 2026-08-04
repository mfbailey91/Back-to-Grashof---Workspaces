"""Sprint 3 analytical predictor tests."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.architectures import ArchitectureA, ArchitectureB, ArchitectureParams
from sixr_grashof.classification import SphericalFourBar, classify_spherical, fixtures
from sixr_grashof.classification.predictors import (
    HandLinkRole,
    architecture_a_type_map,
    predict_from_spherical,
    predict_orientation_capability,
    write_type_map_csv,
    write_type_map_json,
)
from sixr_grashof.reductions import reduce_architecture_a, reduce_architecture_b
from sixr_grashof.reductions.residuals import ConcurrencyReport
from sixr_grashof.reductions.types import SphericalOrientationReduction

ZERO = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_fixtures_still_classify_via_predictor_path() -> None:
    for row in fixtures():
        linkage = SphericalFourBar(
            float(row["alpha"]),  # type: ignore[arg-type]
            float(row["beta"]),  # type: ignore[arg-type]
            float(row["gamma"]),  # type: ignore[arg-type]
            float(row["eta"]),  # type: ignore[arg-type]
        )
        expected = classify_spherical(linkage)
        spherical = SphericalOrientationReduction(
            linkage=linkage,
            concurrency=_exact_concurrency(),
            status="exact",
            directions=None,
        )
        pred = predict_from_spherical(
            spherical,
            architecture_id="fixture",
            joint_configuration=ZERO,
        )
        assert pred.linkage_type == expected.linkage_type
        assert pred.linkage_type == int(row["type"])  # type: ignore[arg-type]


def _exact_concurrency() -> ConcurrencyReport:
    return ConcurrencyReport(
        center=(0.0, 0.0, 0.0),
        residual_rho=0.0,
        max_distance=0.0,
        scale_L2=1.0,
        status="exact",
        rho_exact=1e-9,
        rho_invalid=0.05,
    )


def test_grashof_double_rocker_never_auto_dexterous() -> None:
    # Fixture type 4: grashof-double-rocker (both rockers).
    row = next(r for r in fixtures() if int(r["type"]) == 4)  # type: ignore[arg-type]
    linkage = SphericalFourBar(
        float(row["alpha"]),  # type: ignore[arg-type]
        float(row["beta"]),  # type: ignore[arg-type]
        float(row["gamma"]),  # type: ignore[arg-type]
        float(row["eta"]),  # type: ignore[arg-type]
    )
    spherical = SphericalOrientationReduction(
        linkage=linkage,
        concurrency=_exact_concurrency(),
        status="exact",
        directions=None,
    )
    pred = predict_from_spherical(
        spherical,
        architecture_id="fixture",
        joint_configuration=ZERO,
    )
    assert pred.grashof_family == "grashof"
    assert pred.hand_link_motion_class == "rocker"
    assert pred.T_product is not None and pred.T_product > 0
    assert pred.dexterity_candidate_hypothesis is False


def test_hand_link_assignment_changes_prediction_traceably() -> None:
    # Type 1 crank-rocker: beta=rocker (not candidate); alpha=crank (candidate under alt).
    row = next(r for r in fixtures() if int(r["type"]) == 1)  # type: ignore[arg-type]
    linkage = SphericalFourBar(
        float(row["alpha"]),  # type: ignore[arg-type]
        float(row["beta"]),  # type: ignore[arg-type]
        float(row["gamma"]),  # type: ignore[arg-type]
        float(row["eta"]),  # type: ignore[arg-type]
    )
    spherical = SphericalOrientationReduction(
        linkage=linkage,
        concurrency=_exact_concurrency(),
        status="exact",
        directions=None,
    )
    beta = predict_from_spherical(
        spherical, architecture_id="fixture", joint_configuration=ZERO, hand_link=HandLinkRole.BETA
    )
    alpha = predict_from_spherical(
        spherical, architecture_id="fixture", joint_configuration=ZERO, hand_link=HandLinkRole.ALPHA
    )
    assert beta.hand_orientation_link == "beta"
    assert alpha.hand_orientation_link == "alpha"
    assert beta.hand_link_motion_class == "rocker"
    assert alpha.hand_link_motion_class == "crank"
    assert beta.dexterity_candidate_hypothesis is False
    assert alpha.dexterity_candidate_hypothesis is True


def test_architecture_a_home_prediction() -> None:
    reduction = reduce_architecture_a(ArchitectureA(), ZERO)
    pred = predict_orientation_capability(reduction)
    assert pred.reduction_status == "exact"
    assert pred.linkage_type == 11
    assert pred.hand_orientation_link == "beta"
    assert pred.hand_link_motion_class == "crank"
    assert pred.dexterity_candidate_hypothesis is True
    assert pred.rho_w is not None and pred.rho_w > 0


def test_invalid_reduction_withholds_prediction() -> None:
    reduction = reduce_architecture_b(ArchitectureB(ArchitectureParams(epsilon_w=0.20)), ZERO)
    if reduction.spherical.status != "invalid":
        spherical = SphericalOrientationReduction(
            linkage=None,
            concurrency=reduction.spherical.concurrency,
            status="invalid",
            directions=None,
            notes="forced invalid",
        )
        pred = predict_from_spherical(
            spherical, architecture_id="B", joint_configuration=ZERO
        )
    else:
        pred = predict_orientation_capability(reduction)
    assert pred.dexterity_candidate_hypothesis is False
    assert pred.spherical_link_angles is None
    assert pred.linkage_type is None


def test_type_map_writes(tmp_path: Path) -> None:
    rows = architecture_a_type_map(n_radial=3, n_elbow=3)
    assert len(rows) >= 1
    csv_path = write_type_map_csv(rows, tmp_path / "map.csv")
    json_path = write_type_map_json(rows, tmp_path / "map.json")
    assert csv_path.is_file()
    assert json_path.is_file()
    text = csv_path.read_text(encoding="utf-8")
    assert "linkage_type" in text
    assert "rho_w" in text
