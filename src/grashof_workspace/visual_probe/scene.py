"""Scene payload builders for static HTML export."""

from __future__ import annotations

from typing import Any

from .candidates import enumerate_candidates
from .model import (
    CandidateTuple,
    CompoundParent,
    ForwardKinematicsResult,
    ProbeConfig,
)
from .reductions import adjacent_axis_relationships, enumerate_compound_parents
from .virtual_closure import (
    TerminalRollDisplay,
    VirtualSphericalClosure,
    terminal_roll_display,
    virtual_spherical_closure,
)


def _vec(v: tuple[float, float, float]) -> list[float]:
    return [float(v[0]), float(v[1]), float(v[2])]


def _axis(axis: Any) -> dict[str, Any]:
    return {"point": _vec(axis.point), "direction": _vec(axis.direction)}


def fk_payload(fk: ForwardKinematicsResult, config: ProbeConfig) -> dict[str, Any]:
    return {
        "q": list(fk.q),
        "tool_point": _vec(fk.tool_point),
        "pointing": _vec(fk.pointing),
        "axis_length": config.axis_length,
        "frame_length": config.frame_length,
        "joints": [
            {
                "index": j.index,
                "label": j.label,
                "origin": _vec(j.origin),
                "axis": _axis(j.axis),
            }
            for j in fk.joints
        ],
        "links": [
            {"start": _vec(a), "end": _vec(b)} for a, b in fk.link_endpoints
        ],
    }


def closure_payload(closure: VirtualSphericalClosure) -> dict[str, Any]:
    return {
        "center": _vec(closure.center),
        "axes": {
            "Sx": _axis(closure.sx),
            "Sy": _axis(closure.sy),
            "Sz": _axis(closure.sz),
        },
    }


def roll_payload(roll: TerminalRollDisplay) -> dict[str, Any]:
    return {
        "axis": _axis(roll.axis),
        "pointing": _vec(roll.pointing),
        "label": roll.label,
        "style": roll.style,
    }


def build_scene_a(fk: ForwardKinematicsResult, config: ProbeConfig) -> dict[str, Any]:
    return {
        "scene_id": "01_physical_manipulator",
        "title": "Scene A — Physical manipulator",
        "kind": "physical",
        "disclaimer": (
            "Visual probe only. Not production code and not a spherical-four-bar certificate."
        ),
        "fk": fk_payload(fk, config),
        "notes": [
            "Link centerlines, joint centers J1–J6, frames, extended revolute axes.",
            "Task point p and pointing direction d shown at the tool.",
        ],
    }


def build_scene_b(
    fk: ForwardKinematicsResult,
    config: ProbeConfig,
    closure: VirtualSphericalClosure,
) -> dict[str, Any]:
    return {
        "scene_id": "02_virtual_spherical_closure",
        "title": "Scene B — Virtual spherical closure",
        "kind": "virtual_closure",
        "disclaimer": (
            "Visual probe only. Not production code and not a spherical-four-bar certificate."
        ),
        "fk": fk_payload(fk, config),
        "arm_opacity": 0.35,
        "closure": closure_payload(closure),
        "notes": [
            "Virtual S_v centered at task point p with tool-aligned Sx, Sy, Sz.",
            "Coordinate decomposition is display-only, not an intrinsic axis count.",
        ],
    }


def build_scene_c(
    fk: ForwardKinematicsResult,
    fk_roll: ForwardKinematicsResult,
    config: ProbeConfig,
    roll: TerminalRollDisplay,
) -> dict[str, Any]:
    return {
        "scene_id": "03_terminal_roll_quotient",
        "title": "Scene C — Terminal-roll quotient",
        "kind": "terminal_roll",
        "disclaimer": (
            "Visual probe only. R6 remains physically present; quotient is task reduction only."
        ),
        "fk": fk_payload(fk, config),
        "fk_roll_compare": fk_payload(fk_roll, config),
        "roll": roll_payload(roll),
        "notes": [
            "R6 shown translucent/dashed and labeled quotiented terminal roll.",
            "Comparison pose differs only in q6; p and d are preserved.",
        ],
    }


def build_scene_d(
    fk: ForwardKinematicsResult,
    config: ProbeConfig,
    closure: VirtualSphericalClosure,
    parent: CompoundParent,
) -> dict[str, Any]:
    return {
        "scene_id": f"reduction_{parent.pair_set}",
        "title": f"Scene D — {parent.topology} ({parent.pair_set})",
        "kind": "compound_parent",
        "disclaimer": (
            "Visual probe only. Enabled only for exact non-collinear intersections."
        ),
        "fk": fk_payload(fk, config),
        "arm_opacity": 0.25,
        "closure": closure_payload(closure),
        "parent": {
            "pair_set": parent.pair_set,
            "topology": parent.topology,
            "pairs": [list(p) for p in parent.pairs],
            "remaining_r": parent.remaining_r,
            "enabled": parent.enabled,
            "reason": parent.reason,
        },
        "notes": [
            f"Compound parent {parent.topology} from pair set {parent.pair_set}.",
            f"Remaining physical revolute: R{parent.remaining_r}.",
        ],
    }


def build_probe_bundle(
    config: ProbeConfig,
    fk: ForwardKinematicsResult,
    fk_roll: ForwardKinematicsResult,
) -> dict[str, Any]:
    """Assemble relationships, parents, candidates, and scene payloads."""
    relations = adjacent_axis_relationships(fk, config)
    parents = enumerate_compound_parents(relations)
    closure = virtual_spherical_closure(fk)
    roll = terminal_roll_display(fk)
    candidates = enumerate_candidates(fk, closure, parents)

    scenes: list[dict[str, Any]] = [
        build_scene_a(fk, config),
        build_scene_b(fk, config, closure),
        build_scene_c(fk, fk_roll, config, roll),
    ]
    for parent in parents:
        if parent.enabled:
            scenes.append(build_scene_d(fk, config, closure, parent))

    return {
        "config_name": config.name,
        "relations": [
            {
                "joint_a": r.joint_a,
                "joint_b": r.joint_b,
                "relation": r.relation,
                "distance": r.distance,
                "intersection": None if r.intersection is None else _vec(r.intersection),
            }
            for r in relations
        ],
        "parents": [
            {
                "pair_set": p.pair_set,
                "topology": p.topology,
                "pairs": [list(pair) for pair in p.pairs],
                "remaining_r": p.remaining_r,
                "enabled": p.enabled,
                "reason": p.reason,
            }
            for p in parents
        ],
        "candidates": [_candidate_payload(c) for c in candidates],
        "scenes": scenes,
        "closure": closure_payload(closure),
        "fk": fk_payload(fk, config),
    }


def _candidate_payload(c: CandidateTuple) -> dict[str, Any]:
    return {
        "candidate_id": c.candidate_id,
        "pair_set": c.pair_set,
        "topology": c.topology,
        "s_choice": c.s_choice,
        "u_first_choice": c.u_first_choice,
        "u_second_choice": c.u_second_choice,
        "remaining_r": c.remaining_r,
        "axes": [
            {
                "role": a.role,
                "source_id": a.source_id,
                "axis": _axis(a.axis),
            }
            for a in c.axes
        ],
    }
