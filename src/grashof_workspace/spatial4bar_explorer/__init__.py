"""Spatial four-bar explorer package.

Scaffold for visual/numerical exploration of one-DOF spatial four-bar families
that arise as fibers of the aligned-terminal 6R pointing problem.
"""

from .families import ORDERED_FAMILIES, FAMILY_AXIS_CASES
from .models import ExplorerCase, OrderedFamily, ToolAxis

__all__ = [
    "ExplorerCase",
    "OrderedFamily",
    "ToolAxis",
    "ORDERED_FAMILIES",
    "FAMILY_AXIS_CASES",
]
