"""Compound-parent enumeration for R1..R5 after terminal-roll quotient.

Conventions
-----------
Traversal labels run from the virtual spherical joint toward ground:

- ``P12_P34`` -> ``SRUU`` (remaining ``R5``)
- ``P12_P45`` -> ``SURU`` (remaining ``R3``)
- ``P23_P45`` -> ``SUUR`` (remaining ``R1``)

A parent is enabled only when both requested adjacent pairs are exact
non-collinear intersections. Collinear pairs never form a ``U``.
"""

from __future__ import annotations

from .axis_geometry import classify_axis_pair
from .model import (
    AxisRelationship,
    CompoundParent,
    ForwardKinematicsResult,
    PairSetId,
    ProbeConfig,
    TopologyLabel,
)

PAIR_SET_SPECS: tuple[tuple[PairSetId, TopologyLabel, tuple[tuple[int, int], ...], int], ...] = (
    ("P12_P34", "SRUU", ((1, 2), (3, 4)), 5),
    ("P12_P45", "SURU", ((1, 2), (4, 5)), 3),
    ("P23_P45", "SUUR", ((2, 3), (4, 5)), 1),
)


def adjacent_axis_relationships(
    fk: ForwardKinematicsResult,
    config: ProbeConfig,
) -> tuple[AxisRelationship, ...]:
    """Classify adjacent pairs among physical joints ``R1``..``R6``."""
    relations: list[AxisRelationship] = []
    for i in range(5):
        a = fk.joints[i]
        b = fk.joints[i + 1]
        relations.append(
            classify_axis_pair(
                a.axis,
                b.axis,
                joint_a=a.index,
                joint_b=b.index,
                incidence_tol=config.incidence_tol,
                parallel_tol=config.parallel_tol,
                ambiguous_tol=config.ambiguous_tol,
            )
        )
    return tuple(relations)


def _relation_map(
    relations: tuple[AxisRelationship, ...],
) -> dict[tuple[int, int], AxisRelationship]:
    return {(r.joint_a, r.joint_b): r for r in relations}


def enumerate_compound_parents(
    relations: tuple[AxisRelationship, ...],
) -> tuple[CompoundParent, ...]:
    """Enumerate the three combinatorial pair sets and enable exact ones."""
    rel_map = _relation_map(relations)
    parents: list[CompoundParent] = []
    for pair_set, topology, pairs, remaining in PAIR_SET_SPECS:
        reasons: list[str] = []
        enabled = True
        for ja, jb in pairs:
            rel = rel_map.get((ja, jb))
            if rel is None:
                enabled = False
                reasons.append(f"missing relation R{ja}-R{jb}")
                continue
            if rel.relation != "intersecting":
                enabled = False
                reasons.append(f"R{ja}-R{jb} is {rel.relation}, not intersecting")
        parents.append(
            CompoundParent(
                pair_set=pair_set,
                topology=topology,
                pairs=pairs,
                remaining_r=remaining,
                enabled=enabled,
                reason="ok" if enabled else "; ".join(reasons),
            )
        )
    return tuple(parents)
