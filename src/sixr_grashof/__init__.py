"""Synthetic 6R spherical Grashof research package (Sprints 0–1)."""

from .classification import (
    SphericalClassification,
    SphericalFourBar,
    classify_spherical,
    evaluate_T,
)

__all__ = [
    "SphericalClassification",
    "SphericalFourBar",
    "classify_spherical",
    "evaluate_T",
]

__version__ = "0.1.0"
