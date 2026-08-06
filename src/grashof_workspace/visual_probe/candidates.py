"""Coordinate-dependent candidate RRRR axis-tuple enumeration.

Conventions
-----------
For one enabled compound parent:

- 3 choices from ``S_v = {Sx, Sy, Sz}``
- 2 choices from the first universal joint coordinate axes
- 2 choices from the second universal joint coordinate axes
- 1 remaining physical revolute

Total: ``3 * 2 * 2 = 12`` candidates per enabled parent.

Enumeration is coordinate-convention-dependent and is not exhaustive over
the continuum of axes admitted by ``S_v``. Outputs are candidate ``RRRR``
axis tuples until later work proves concurrency, arc invariance, locking,
and motion equivalence.
"""

from __future__ import annotations

from .model import (
    AxisLine,
    CandidateAxis,
    CandidateTuple,
    CompoundParent,
    ForwardKinematicsResult,
)
from .transforms import normalize
from .virtual_closure import VirtualSphericalClosure


def _u_coordinate_axes(
    axis_a: AxisLine,
    axis_b: AxisLine,
    *,
    pair_label: str,
) -> tuple[tuple[str, AxisLine], tuple[str, AxisLine]]:
    """Return ordered display axes for an exact intersecting U-pair."""
    return (
        (f"{pair_label}_a", axis_a),
        (f"{pair_label}_b", axis_b),
    )


def enumerate_candidates(
    fk: ForwardKinematicsResult,
    closure: VirtualSphericalClosure,
    parents: tuple[CompoundParent, ...],
) -> tuple[CandidateTuple, ...]:
    """Expand every enabled compound parent into 12 candidate tuples."""
    s_choices = (
        ("Sx", closure.sx),
        ("Sy", closure.sy),
        ("Sz", closure.sz),
    )
    joint_axes = {j.index: j.axis for j in fk.joints}
    out: list[CandidateTuple] = []

    for parent in parents:
        if not parent.enabled:
            continue
        (i1, i2), (j1, j2) = parent.pairs
        u_first = _u_coordinate_axes(
            joint_axes[i1],
            joint_axes[i2],
            pair_label=f"U{i1}{i2}",
        )
        u_second = _u_coordinate_axes(
            joint_axes[j1],
            joint_axes[j2],
            pair_label=f"U{j1}{j2}",
        )
        remaining_axis = joint_axes[parent.remaining_r]

        for s_name, s_axis in s_choices:
            for u1_name, u1_axis in u_first:
                for u2_name, u2_axis in u_second:
                    candidate_id = (
                        f"{parent.pair_set}__{s_name}__{u1_name}__{u2_name}__R{parent.remaining_r}"
                    )
                    axes = (
                        CandidateAxis("S", s_name, s_axis),
                        CandidateAxis("U", u1_name, AxisLine(u1_axis.point, normalize(u1_axis.direction))),
                        CandidateAxis("U", u2_name, AxisLine(u2_axis.point, normalize(u2_axis.direction))),
                        CandidateAxis(
                            "R",
                            f"R{parent.remaining_r}",
                            AxisLine(remaining_axis.point, normalize(remaining_axis.direction)),
                        ),
                    )
                    out.append(
                        CandidateTuple(
                            candidate_id=candidate_id,
                            pair_set=parent.pair_set,
                            topology=parent.topology,
                            s_choice=s_name,
                            u_first_choice=u1_name,
                            u_second_choice=u2_name,
                            remaining_r=parent.remaining_r,
                            axes=axes,
                        )
                    )
    return tuple(out)
