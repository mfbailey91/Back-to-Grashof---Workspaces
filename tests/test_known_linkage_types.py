"""Hand-calculated fixtures for all 16 spherical linkage types."""

from __future__ import annotations

import math

import pytest

from sixr_grashof.classification import (
    SphericalFourBar,
    classify_spherical,
    evaluate_T,
    fixtures,
)


@pytest.mark.parametrize("row", fixtures(), ids=lambda r: str(r["label"]))
def test_fixture_classifies_to_expected_type(row: dict[str, object]) -> None:
    linkage = SphericalFourBar(
        float(row["alpha"]),  # type: ignore[arg-type]
        float(row["beta"]),  # type: ignore[arg-type]
        float(row["gamma"]),  # type: ignore[arg-type]
        float(row["eta"]),  # type: ignore[arg-type]
    )
    result = classify_spherical(linkage)
    assert result.linkage_type == int(row["type"])
    assert result.hand_orientation_link == "beta"
    assert result.input_motion_class in {"crank", "rocker"}
    assert result.hand_link_motion_class in {"crank", "rocker"}


def test_architecture_a_worked_closure() -> None:
    """Gate-1 fixture from docs/theory.md §7."""
    linkage = SphericalFourBar(0.5, 1.0, 1.2, 0.8)
    t1, t2, t3, t4 = evaluate_T(linkage)
    assert t1 == pytest.approx(0.5)
    assert t2 == pytest.approx(0.9)
    assert t3 == pytest.approx(0.1)
    assert t4 == pytest.approx(2.0 * math.pi - 3.5)
    result = classify_spherical(linkage)
    assert result.linkage_type == 1
    assert result.linkage_name == "crank-rocker"
    assert result.input_motion_class == "crank"
    assert result.hand_link_motion_class == "rocker"
    assert result.wrap_around is False


def test_type2_and_type3_are_dexterity_candidates_under_hypothesis() -> None:
    type2 = classify_spherical(SphericalFourBar(1.0, 0.5, 1.2, 0.8))
    type3 = classify_spherical(SphericalFourBar(1.2, 0.8, 0.5, 1.0))
    assert type2.linkage_type == 2
    assert type3.linkage_type == 3
    assert type2.hand_link_motion_class == "crank"
    assert type3.hand_link_motion_class == "crank"
    assert type2.dexterity_candidate_hypothesis is True
    assert type3.dexterity_candidate_hypothesis is True


def test_grashof_double_rocker_not_dexterous_from_product() -> None:
    result = classify_spherical(SphericalFourBar(1.0, 1.2, 0.8, 0.5))
    assert result.linkage_type == 4
    assert result.grashof_family == "grashof"
    assert result.hand_link_motion_class == "rocker"
    assert result.dexterity_candidate_hypothesis is False


def test_interior_exterior_boundary_for_T4() -> None:
    # Interior wrap-around: sum > 2π
    wrap = SphericalFourBar(2.2, 2.0, 1.5, 1.5)
    assert evaluate_T(wrap)[3] < 0.0
    # Exterior non-wrap: sum < 2π
    plain = SphericalFourBar(0.5, 1.0, 1.2, 0.8)
    assert evaluate_T(plain)[3] > 0.0
    # Boundary: sum = 2π → T4 = 0
    # 2.0+1.0+1.5+π- wait: need alpha+beta+gamma+eta = 2π with each in (0,π]
    half = math.pi / 2
    boundary = SphericalFourBar(half, half, half, half)  # sum = 2π
    assert evaluate_T(boundary)[3] == pytest.approx(0.0)
    assert classify_spherical(boundary).is_boundary
