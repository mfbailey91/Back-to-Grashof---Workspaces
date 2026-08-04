"""Linkage-type table helpers and crank/rocker reports."""

from __future__ import annotations

from .mccarthy_soh import (
    SphericalClassification,
    SphericalFourBar,
    classify_spherical,
    fixtures,
    lookup_type,
    type_table,
)

__all__ = [
    "SphericalClassification",
    "SphericalFourBar",
    "all_sign_patterns_unique",
    "classify_spherical",
    "fixtures",
    "lookup_type",
    "type_table",
]


def all_sign_patterns_unique() -> bool:
    """Return True if the 16 nonzero sign patterns are bijective with types 1–16."""
    rows = type_table()
    signs: list[tuple[int, ...]] = []
    types: list[int] = []
    for row in rows:
        raw_signs = row["signs"]
        if not isinstance(raw_signs, list):
            raise TypeError("signs must be a list")
        signs.append(tuple(int(s) for s in raw_signs))
        raw_type = row["type"]
        if isinstance(raw_type, bool) or not isinstance(raw_type, int):
            raise TypeError("type must be an int")
        types.append(raw_type)
    return len(set(signs)) == 16 and len(set(types)) == 16 and set(types) == set(range(1, 17))
