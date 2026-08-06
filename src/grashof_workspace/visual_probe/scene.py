"""Scene payload builders for static HTML export.

Scenes are broken into ordered step plots so each mechanical idea
(link chain, axes, task, closure, roll, pair classification, reduction,
candidate) gets its own dedicated view.
"""

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

_DISCLAIMER = (
    "Visual probe only. Not production code and not a spherical-four-bar certificate."
)


def _vec(v: tuple[float, float, float]) -> list[float]:
    return [float(v[0]), float(v[1]), float(v[2])]


def _axis(axis: Any) -> dict[str, Any]:
    return {"point": _vec(axis.point), "direction": _vec(axis.direction)}


def _frame_payload(label: str, mat: Any, *, kind: str) -> dict[str, Any]:
    """Serialize a frame with global origin and local unit axes."""
    from .transforms import triad_from_mat4

    origin, x, y, z = triad_from_mat4(mat)
    return {
        "label": label,
        "kind": kind,
        "origin_world": _vec(origin),
        "local_x": _vec(x),
        "local_y": _vec(y),
        "local_z": _vec(z),
        "convention": "right-handed; local z along revolute / pointing axis",
    }


def fk_payload(fk: ForwardKinematicsResult, config: ProbeConfig) -> dict[str, Any]:
    from .transforms import world_frame_mat4

    world = _frame_payload("W", world_frame_mat4(length=1.0), kind="world")
    joint_frames = [
        _frame_payload(j.label, j.frame, kind="joint") for j in fk.joints
    ]
    tool = _frame_payload("tool", fk.tool_transform, kind="tool")
    return {
        "q": list(fk.q),
        "tool_point": _vec(fk.tool_point),
        "pointing": _vec(fk.pointing),
        "axis_length": config.axis_length,
        "frame_length": config.frame_length,
        "world_frame": world,
        "local_frames": joint_frames + [tool],
        "joints": [
            {
                "index": j.index,
                "label": j.label,
                "origin": _vec(j.origin),
                "axis": _axis(j.axis),
                "local_frame": _frame_payload(j.label, j.frame, kind="joint"),
            }
            for j in fk.joints
        ],
        "links": [{"start": _vec(a), "end": _vec(b)} for a, b in fk.link_endpoints],
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


def _base_scene(
    *,
    scene_id: str,
    title: str,
    kind: str,
    step: int,
    group: str,
    notes: list[str],
    fk: ForwardKinematicsResult,
    config: ProbeConfig,
    disclaimer: str = _DISCLAIMER,
    fk_data: dict[str, Any] | None = None,
    **opts: Any,
) -> dict[str, Any]:
    scene: dict[str, Any] = {
        "scene_id": scene_id,
        "title": title,
        "kind": kind,
        "step": step,
        "group": group,
        "disclaimer": disclaimer,
        "fk": fk_data if fk_data is not None else fk_payload(fk, config),
        "notes": notes,
        "camera": {"orthographic": True},
    }
    scene.update(opts)
    return scene


def build_step_scenes(
    config: ProbeConfig,
    fk: ForwardKinematicsResult,
    fk_roll: ForwardKinematicsResult,
    *,
    relations: tuple[Any, ...],
    parents: tuple[CompoundParent, ...],
    closure: VirtualSphericalClosure,
    roll: TerminalRollDisplay,
    candidates: tuple[CandidateTuple, ...],
) -> list[dict[str, Any]]:
    """Return ordered step scenes for the visual probe storyboard."""
    scenes: list[dict[str, Any]] = []
    step = 0

    def add(**kwargs: Any) -> None:
        nonlocal step
        step += 1
        scenes.append(_base_scene(step=step, fk=fk, config=config, **kwargs))

    # --- Group A: physical chain ---
    add(
        scene_id="01a_links_only",
        title="Step 01a — Link centerlines",
        kind="step_links",
        group="A_physical",
        notes=["Only successive joint-origin links. No axes yet."],
        show_links=True,
        show_joint_centers=False,
        show_axes=False,
        show_task=False,
        arm_opacity=1.0,
    )
    add(
        scene_id="01b_joint_centers",
        title="Step 01b — Joint centers J1–J6",
        kind="step_centers",
        group="A_physical",
        notes=["Joint origins only, with light link ghost for context."],
        show_links=True,
        show_joint_centers=True,
        show_axes=False,
        show_task=False,
        arm_opacity=0.35,
    )
    add(
        scene_id="01b2_world_xyz",
        title="Step 01b2 — Global world frame W (X,Y,Z)",
        kind="step_world_frame",
        group="A_physical",
        notes=[
            "Fixed world frame W at the origin.",
            "RGB triad: X red, Y green, Z blue.",
            "All joint origins are reported in these global coordinates.",
        ],
        show_links=True,
        show_joint_centers=True,
        show_axes=False,
        show_task=False,
        show_world_frame=True,
        show_local_frames=False,
        show_coordinate_table=True,
        arm_opacity=0.25,
    )
    add(
        scene_id="01b3_local_frames",
        title="Step 01b3 — Local frames per joint + tool",
        kind="step_local_frames",
        group="A_physical",
        notes=[
            "Each joint has a right-handed local triad; local z along the revolute axis.",
            "Tool frame local z aligns with pointing d.",
            "World frame W remains visible for reference.",
        ],
        show_links=True,
        show_joint_centers=True,
        show_axes=False,
        show_task=False,
        show_world_frame=True,
        show_local_frames=True,
        show_coordinate_table=True,
        arm_opacity=0.2,
    )
    add(
        scene_id="01c_revolute_axes",
        title="Step 01c — Infinite revolute axes",
        kind="step_axes",
        group="A_physical",
        notes=["Extended R1–R6 axes. Joint centers labeled."],
        show_links=True,
        show_joint_centers=True,
        show_axes=True,
        show_task=False,
        show_world_frame=True,
        arm_opacity=0.45,
        label_all_axes=True,
    )
    add(
        scene_id="01d_task_point_and_pointing",
        title="Step 01d — Task point p and pointing d",
        kind="step_task",
        group="A_physical",
        notes=["Task point on R6; pointing parallel to R6."],
        show_links=True,
        show_joint_centers=True,
        show_axes=False,
        show_task=True,
        show_world_frame=True,
        selected_joint_indices=[6],
        dim_unselected_axes=True,
        show_unselected_axes=False,
        arm_opacity=0.35,
    )
    add(
        scene_id="01e_physical_assembled",
        title="Step 01e — Physical manipulator assembled",
        kind="physical",
        group="A_physical",
        notes=[
            "Full Scene A: links, centers, axes, task point, pointing.",
            "World XYZ plus local frames at every joint and the tool.",
        ],
        show_links=True,
        show_joint_centers=True,
        show_axes=True,
        show_task=True,
        show_world_frame=True,
        show_local_frames=True,
        show_coordinate_table=True,
        label_all_axes=True,
        arm_opacity=1.0,
    )

    # --- Group B: virtual closure ---
    add(
        scene_id="02a_task_point_focus",
        title="Step 02a — Task point focus",
        kind="step_task_focus",
        group="B_closure",
        notes=["Arm ghosted; emphasize the fixed task point p."],
        show_links=True,
        show_joint_centers=True,
        show_axes=False,
        show_task=True,
        arm_opacity=0.2,
    )
    add(
        scene_id="02b_virtual_spherical_axes",
        title="Step 02b — Virtual spherical axes Sx, Sy, Sz",
        kind="step_sv_axes",
        group="B_closure",
        notes=[
            "S_v coordinate decomposition at p (display convention only).",
            "Physical arm remains translucent.",
        ],
        show_links=True,
        show_joint_centers=False,
        show_axes=False,
        show_task=True,
        arm_opacity=0.2,
        closure=closure_payload(closure),
        show_closure_center=True,
        show_closure_axes=True,
    )
    add(
        scene_id="02c_virtual_closure_assembled",
        title="Step 02c — Virtual spherical closure assembled",
        kind="virtual_closure",
        group="B_closure",
        notes=["Scene B assembled: physical arm + virtual spherical closure."],
        show_links=True,
        show_joint_centers=True,
        show_axes=True,
        show_task=True,
        arm_opacity=0.35,
        closure=closure_payload(closure),
        show_closure_center=True,
        show_closure_axes=True,
    )

    # --- Group C: terminal roll ---
    add(
        scene_id="03a_r6_aligned_with_d",
        title="Step 03a — R6 aligned with pointing d",
        kind="step_r6_align",
        group="C_roll",
        notes=["R6 contains p and is parallel to d."],
        show_links=True,
        show_joint_centers=True,
        show_axes=True,
        show_task=True,
        selected_joint_indices=[6],
        dim_unselected_axes=True,
        arm_opacity=0.35,
    )
    add(
        scene_id="03b_roll_pose_reference",
        title="Step 03b — Reference pose (q6)",
        kind="step_roll_a",
        group="C_roll",
        notes=[f"Reference configuration q6 = {fk.q[5]:.3f}."],
        show_links=True,
        show_joint_centers=True,
        show_axes=False,
        show_task=True,
        arm_opacity=1.0,
        closure=closure_payload(closure),
        show_closure_axes=True,
        show_closure_center=True,
    )
    add(
        scene_id="03c_roll_pose_compare",
        title="Step 03c — Roll-compare pose (Δq6)",
        kind="step_roll_b",
        group="C_roll",
        notes=[
            f"Compare pose q6 = {fk_roll.q[5]:.3f}; p and d preserved.",
            "Ghosted reference arm shown underneath.",
        ],
        show_links=True,
        show_joint_centers=True,
        show_axes=False,
        show_task=True,
        arm_opacity=1.0,
        fk_data=fk_payload(fk_roll, config),
        fk_ghost=fk_payload(fk, config),
        ghost_opacity=0.25,
        closure=closure_payload(virtual_spherical_closure(fk_roll)),
        show_closure_axes=True,
        show_closure_center=True,
    )
    add(
        scene_id="03d_terminal_roll_quotient",
        title="Step 03d — Quotiented terminal roll",
        kind="terminal_roll",
        group="C_roll",
        notes=[
            "R6 remains physically present; dashed style marks task-roll quotient.",
            "Do not read this as deleting the terminal joint.",
        ],
        disclaimer=(
            "Visual probe only. R6 remains physically present; quotient is task reduction only."
        ),
        show_links=True,
        show_joint_centers=True,
        show_axes=True,
        show_task=True,
        arm_opacity=0.4,
        roll=roll_payload(roll),
        show_roll=True,
        selected_joint_indices=[6],
        dim_unselected_axes=True,
    )

    # --- Group D: adjacent axis relationships ---
    relation_payloads = [
        {
            "joint_a": r.joint_a,
            "joint_b": r.joint_b,
            "relation": r.relation,
            "distance": r.distance,
            "intersection": None if r.intersection is None else _vec(r.intersection),
        }
        for r in relations
    ]
    for rel in relations:
        ja, jb = rel.joint_a, rel.joint_b
        add(
            scene_id=f"04_pair_R{ja}_R{jb}",
            title=f"Step 04 — Adjacent pair R{ja}–R{jb}: {rel.relation}",
            kind="step_axis_pair",
            group="D_relationships",
            notes=[
                f"Classification: {rel.relation}",
                f"Line-line distance = {rel.distance:.3e}",
                "Only intersecting non-collinear pairs may form a U.",
            ],
            show_links=True,
            show_joint_centers=True,
            show_axes=True,
            show_task=False,
            arm_opacity=0.2,
            selected_joint_indices=[ja, jb],
            dim_unselected_axes=True,
            show_unselected_axes=True,
            relations=[relation_payloads[ja - 1]],
            show_intersections=True,
            highlight_pair=[ja, jb],
        )
    add(
        scene_id="04f_adjacent_summary",
        title="Step 04f — Adjacent-axis relationship summary",
        kind="step_axis_summary",
        group="D_relationships",
        notes=["All adjacent R1–R6 relationships in one view."],
        show_links=True,
        show_joint_centers=True,
        show_axes=True,
        show_task=False,
        arm_opacity=0.25,
        label_all_axes=True,
        relations=relation_payloads,
        show_intersections=True,
    )

    # --- Group E: compound parents ---
    for parent in parents:
        pair_indices = sorted({i for pair in parent.pairs for i in pair})
        add(
            scene_id=f"05a_{parent.pair_set}_pairs",
            title=f"Step 05a — Pair set {parent.pair_set} ({'enabled' if parent.enabled else 'disabled'})",
            kind="step_pair_set",
            group="E_reductions",
            notes=[
                f"Requested pairs: {list(parent.pairs)}",
                f"Status: {parent.reason}",
                "Collinear / skew / parallel-distinct pairs never form U.",
            ],
            show_links=True,
            show_joint_centers=True,
            show_axes=True,
            show_task=False,
            arm_opacity=0.2,
            selected_joint_indices=pair_indices,
            dim_unselected_axes=True,
            parent={
                "pair_set": parent.pair_set,
                "topology": parent.topology,
                "pairs": [list(p) for p in parent.pairs],
                "remaining_r": parent.remaining_r,
                "enabled": parent.enabled,
                "reason": parent.reason,
            },
            show_intersections=True,
            relations=[
                rp
                for rp in relation_payloads
                if (rp["joint_a"], rp["joint_b"]) in parent.pairs
            ],
        )
        if parent.enabled:
            add(
                scene_id=f"05b_{parent.pair_set}_{parent.topology}",
                title=f"Step 05b — Compound parent {parent.topology}",
                kind="compound_parent",
                group="E_reductions",
                notes=[
                    f"Topology {parent.topology} from {parent.pair_set}.",
                    f"Remaining physical revolute: R{parent.remaining_r}.",
                    "Virtual spherical closure shown for context.",
                ],
                show_links=True,
                show_joint_centers=True,
                show_axes=True,
                show_task=True,
                arm_opacity=0.22,
                selected_joint_indices=pair_indices + [parent.remaining_r],
                dim_unselected_axes=True,
                closure=closure_payload(closure),
                show_closure_center=True,
                show_closure_axes=True,
                parent={
                    "pair_set": parent.pair_set,
                    "topology": parent.topology,
                    "pairs": [list(p) for p in parent.pairs],
                    "remaining_r": parent.remaining_r,
                    "enabled": parent.enabled,
                    "reason": parent.reason,
                },
                show_intersections=True,
                relations=[
                    rp
                    for rp in relation_payloads
                    if (rp["joint_a"], rp["joint_b"]) in parent.pairs
                ],
            )

    # --- Group F: candidate samples ---
    samples: list[CandidateTuple] = []
    for parent in parents:
        if not parent.enabled:
            continue
        chosen = next(
            (
                c
                for c in candidates
                if c.pair_set == parent.pair_set and c.s_choice == "Sz"
            ),
            None,
        )
        if chosen is not None:
            samples.append(chosen)
    for sample in samples:
        add(
            scene_id=f"06_{sample.pair_set}_sample",
            title=f"Step 06 — Sample candidate ({sample.topology}, Sz)",
            kind="step_candidate",
            group="F_candidates",
            notes=[
                "candidate RRRR axis tuple — not certified",
                sample.candidate_id,
                "Coordinate-dependent selection; provenance preserved.",
            ],
            show_links=True,
            show_joint_centers=False,
            show_axes=False,
            show_task=True,
            arm_opacity=0.15,
            candidate=_candidate_payload(sample),
            closure=closure_payload(closure),
            show_closure_center=True,
            show_closure_axes=False,
        )

    return scenes


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
    scenes = build_step_scenes(
        config,
        fk,
        fk_roll,
        relations=relations,
        parents=parents,
        closure=closure,
        roll=roll,
        candidates=candidates,
    )

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
