"""Reduction diagnostics (Sprint 2).

Import ``reduce_architecture_*`` from ``sixr_grashof.reductions.engine``
(or from this package after architectures are loaded) to avoid import cycles.
"""

from .planar_fourbar import planar_fourbar_from_reduction, reduce_regional_planar
from .residuals import (
    RHO_EXACT_DEFAULT,
    RHO_INVALID_DEFAULT,
    ConcurrencyReport,
    concurrency_residual,
)
from .spherical_fourbar import angles_from_directions, reduce_spherical_orientation
from .symmetry import base_symmetry_report, detect_base_symmetry, quotient_azimuth
from .types import CombinedReduction, RegionalPlanarReduction, SphericalOrientationReduction

__all__ = [
    "RHO_EXACT_DEFAULT",
    "RHO_INVALID_DEFAULT",
    "CombinedReduction",
    "ConcurrencyReport",
    "RegionalPlanarReduction",
    "SphericalOrientationReduction",
    "angles_from_directions",
    "base_symmetry_report",
    "concurrency_residual",
    "detect_base_symmetry",
    "planar_fourbar_from_reduction",
    "quotient_azimuth",
    "reduce_regional_planar",
    "reduce_spherical_orientation",
]


def __getattr__(name: str):  # noqa: ANN001
    if name in {
        "reduce_architecture_a",
        "reduce_architecture_b",
        "reduce_architecture_c",
        "reduce_sixr",
    }:
        from . import engine

        return getattr(engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
