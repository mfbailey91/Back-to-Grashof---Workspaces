"""Spatial four-bar explorer package.

Scaffold for visual/numerical exploration of one-DOF spatial four-bar families
that arise as fibers of the aligned-terminal 6R pointing problem.
"""

from .families import FAMILY_AXIS_CASES, ORDERED_FAMILIES
from .models import ExplorerCase, OrderedFamily, ToolAxis

__all__ = [
    "FAMILY_AXIS_CASES",
    "ORDERED_FAMILIES",
    "ExplorerCase",
    "OrderedFamily",
    "ToolAxis",
]
