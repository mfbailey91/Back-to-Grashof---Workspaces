from __future__ import annotations

from .models import ExplorerCase, OrderedFamily, ToolAxis

ORDERED_FAMILIES: tuple[OrderedFamily, ...] = (
    OrderedFamily.UUUR,
    OrderedFamily.UURU,
    OrderedFamily.URUU,
    OrderedFamily.USRR,
    OrderedFamily.URSR,
    OrderedFamily.URRS,
)

FAMILY_AXIS_CASES: tuple[ExplorerCase, ...] = tuple(
    ExplorerCase(family=family, tool_axis=axis)
    for family in ORDERED_FAMILIES
    for axis in (ToolAxis.A, ToolAxis.B)
)

FAMILY_PARENT_MAP: dict[OrderedFamily, str] = {
    OrderedFamily.UUUR: "SUUR -> UUUR fiber",
    OrderedFamily.UURU: "SURU -> UURU fiber",
    OrderedFamily.URUU: "SRUU -> URUU fiber",
    OrderedFamily.USRR: "SSRR -> USRR fiber",
    OrderedFamily.URSR: "SRSR -> URSR fiber",
    OrderedFamily.URRS: "SRRS -> URRS fiber",
}

FAMILY_NOTES: dict[OrderedFamily, str] = {
    OrderedFamily.UUUR: "Two universal joints plus one revolute after tool-U slicing.",
    OrderedFamily.UURU: "Mixed placement of the single revolute between universal joints.",
    OrderedFamily.URUU: "Single revolute nearest ground when loop is read from tool U.",
    OrderedFamily.USRR: "Equivalent multiset to RRUS; order preserved for inversion-sensitive analysis.",
    OrderedFamily.URSR: "Alternating U-R-S-R order in the one-DOF fiber.",
    OrderedFamily.URRS: "S joint is deepest in the chain away from the tool U.",
}
