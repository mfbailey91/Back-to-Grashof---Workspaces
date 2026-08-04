"""Synthetic 6R architectures A/B/C."""

from .architecture_a import ArchitectureA
from .architecture_b import ArchitectureB
from .architecture_c import ArchitectureC
from .base import ArchitectureParams, GeometryReport

__all__ = [
    "ArchitectureA",
    "ArchitectureB",
    "ArchitectureC",
    "ArchitectureParams",
    "GeometryReport",
]
