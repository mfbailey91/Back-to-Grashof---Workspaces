"""Tests for McCarthy–Soh sign-pattern ↔ type bijection."""

from __future__ import annotations

from sixr_grashof.classification import (
    SphericalFourBar,
    all_sign_patterns_unique,
    classify_spherical,
    lookup_type,
    type_table,
)


def test_sixteen_sign_patterns_are_unique() -> None:
    assert all_sign_patterns_unique()


def test_every_nonzero_sign_pattern_maps_to_one_type() -> None:
    seen: set[int] = set()
    for row in type_table():
        signs = tuple(int(s) for s in row["signs"])  # type: ignore[arg-type]
        found = lookup_type(signs)
        assert found is not None
        assert int(found["type"]) == int(row["type"])
        seen.add(int(row["type"]))
    assert seen == set(range(1, 17))


def test_t4_negative_correspondence() -> None:
    for k in range(1, 9):
        pos = next(r for r in type_table() if int(r["type"]) == k)
        neg = next(r for r in type_table() if int(r["type"]) == k + 8)
        pos_signs = tuple(int(s) for s in pos["signs"])  # type: ignore[arg-type]
        neg_signs = tuple(int(s) for s in neg["signs"])  # type: ignore[arg-type]
        assert neg_signs == tuple(-s for s in pos_signs[:3]) + (-1,)
        assert int(neg["equivalent_type"]) == k
        assert pos["input"] == neg["input"]
        assert pos["output"] == neg["output"]


def test_grashof_product_never_alone_marks_dexterity() -> None:
    # Type 1: Grashof crank-rocker — product > 0 but hand link is rocker.
    result = classify_spherical(SphericalFourBar(0.5, 1.0, 1.2, 0.8))
    assert result.grashof_family == "grashof"
    assert result.T_product > 0.0
    assert result.linkage_type == 1
    assert result.hand_link_motion_class == "rocker"
    assert result.dexterity_candidate_hypothesis is False


def test_boundary_when_Ti_zero() -> None:
    # Construct T3 ≈ 0: eta + beta = gamma + alpha
    linkage = SphericalFourBar(alpha=0.5, beta=0.5, gamma=0.5, eta=0.5)
    result = classify_spherical(linkage)
    assert result.is_boundary
    assert result.grashof_family == "change-point"
