"""CLI for the aligned terminal-roll visual probe.

Produces static outputs under ``outputs/aligned_terminal_visual_probe/``.
This is not production or certification code.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from . import DISCLAIMER
from .config import default_config_path, load_config
from .export import (
    write_contact_sheet,
    write_index_browser,
    write_json,
    write_manifest,
    write_scene_html,
    write_steps_gallery,
)
from .forward_kinematics import forward_kinematics
from .model import Manifest, SceneRecord
from .plotting import write_scene_plot
from .scene import build_probe_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aligned terminal-roll visual mechanism probe. "
            "Explanatory / diagnostic only — not spherical-four-bar certification."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to architecture JSON (default: configs/aligned_terminal_6r_visual_probe.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/aligned_terminal_visual_probe"),
        help="Output directory for manifest, scenes, and data",
    )
    parser.add_argument(
        "--shell-only",
        action="store_true",
        help="V00 mode: write manifest with no scenes (package shell)",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Skip matplotlib PNG step plots",
    )
    return parser


def _scene_output_path(output_dir: Path, scene: dict[str, Any]) -> Path:
    sid = str(scene["scene_id"])
    kind = str(scene.get("kind", ""))
    group = str(scene.get("group", ""))
    if kind == "compound_parent" or group == "E_reductions":
        return output_dir / "scenes" / "reductions" / f"{sid}.html"
    if group in {"D_relationships", "F_candidates"} or sid.startswith(("04", "06")):
        return output_dir / "scenes" / "steps" / f"{sid}.html"
    return output_dir / "scenes" / f"{sid}.html"


def _scene_href(scene: dict[str, Any], path: Path, scenes_root: Path) -> str:
    rel = path.relative_to(scenes_root).as_posix()
    return rel


def generate(output_dir: Path, config_path: Path, *, shell_only: bool = False, skip_plots: bool = False) -> Manifest:
    """Generate probe outputs and return the manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data").mkdir(parents=True, exist_ok=True)
    (output_dir / "scenes" / "reductions").mkdir(parents=True, exist_ok=True)
    (output_dir / "scenes" / "steps").mkdir(parents=True, exist_ok=True)
    (output_dir / "contact_sheets").mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(parents=True, exist_ok=True)

    config = load_config(config_path)
    scenes: list[SceneRecord] = []
    data_files: list[str] = []

    if shell_only:
        manifest = Manifest(
            project="aligned_terminal_roll_visual_probe",
            disclaimer=DISCLAIMER,
            config_name=config.name,
            output_dir=str(output_dir),
            scenes=tuple(scenes),
            data_files=tuple(data_files),
        )
        write_manifest(output_dir / "manifest.json", manifest)
        return manifest

    fk = forward_kinematics(config)
    q_roll = (
        fk.q[0],
        fk.q[1],
        fk.q[2],
        fk.q[3],
        fk.q[4],
        float(config.roll_compare_q6),
    )
    fk_roll = forward_kinematics(config, q_roll)
    bundle = build_probe_bundle(config, fk, fk_roll)

    rel_path = output_dir / "data" / "axis_relationships.json"
    write_json(rel_path, bundle["relations"])
    data_files.append(str(rel_path))

    parents_path = output_dir / "data" / "compound_parents.json"
    write_json(parents_path, bundle["parents"])
    data_files.append(str(parents_path))

    cand_path = output_dir / "data" / "candidates.json"
    write_json(cand_path, bundle["candidates"])
    data_files.append(str(cand_path))

    frames_path = output_dir / "data" / "frames.json"
    write_json(
        frames_path,
        {
            "convention": (
                "World frame W is fixed at the origin. Each local frame is "
                "right-handed with local z along the revolute / pointing axis. "
                "origin_world is the frame origin in global XYZ metres; "
                "local_x/y/z are unit directions expressed in world coordinates."
            ),
            "world_frame": bundle["fk"]["world_frame"],
            "local_frames": bundle["fk"]["local_frames"],
            "q": bundle["fk"]["q"],
        },
    )
    data_files.append(str(frames_path))

    scenes_root = output_dir / "scenes"
    gallery_scenes: list[dict[str, Any]] = []
    for scene in bundle["scenes"]:
        path = _scene_output_path(output_dir, scene)
        href = _scene_href(scene, path, scenes_root)
        scene_with_href = {**scene, "_href": href}
        # Fix gallery links for pages under scenes/steps or reductions
        if path.parent.name == "steps":
            scene_with_href["_href"] = f"steps/{path.name}"
        elif path.parent.name == "reductions":
            scene_with_href["_href"] = f"reductions/{path.name}"
        else:
            scene_with_href["_href"] = path.name
        gallery_scenes.append(scene_with_href)
        scenes.append(
            write_scene_html(
                path,
                scene,
                gallery_href=("../gallery.html" if path.parent.name in {"steps", "reductions"} else "gallery.html"),
            )
        )
        if not skip_plots:
            plot_path = output_dir / "plots" / f"{scene['scene_id']}.png"
            write_scene_plot(plot_path, scene)
            data_files.append(str(plot_path))

    # Gallery embeds PNG thumbnails as data URIs for reliable local preview.
    gallery_path = scenes_root / "gallery.html"
    write_steps_gallery(
        gallery_path,
        gallery_scenes,
        plot_dir=None if skip_plots else (output_dir / "plots"),
        plot_rel_dir="plots",
    )
    scenes.append(
        SceneRecord(
            scene_id="gallery",
            title="Step storyboard gallery",
            path=str(gallery_path),
            kind="gallery",
            notes=("Ordered step plots with PNG thumbnails",),
        )
    )

    contact = output_dir / "contact_sheets" / "candidates.html"
    write_contact_sheet(contact, bundle["candidates"], bundle["fk"])
    data_files.append(str(contact))

    index = output_dir / "index.html"
    write_index_browser(index, bundle)
    scenes.append(
        SceneRecord(
            scene_id="index",
            title="Interactive candidate browser",
            path=str(index),
            kind="browser",
            notes=("Static no-server dashboard",),
        )
    )

    audit = {
        "disclaimer": DISCLAIMER,
        "historical_failures": [
            {
                "id": "atr_topology_candidate_1",
                "status": "unmappable_without_prior_axis_provenance",
                "note": (
                    "Prior rejected spherical-four-bar reading cannot be rematerialized "
                    "as a visual-probe candidate without preserved axis provenance from "
                    "the fiber experiments."
                ),
            },
            {
                "id": "atr_topology_candidate_2",
                "status": "unmappable_without_prior_axis_provenance",
                "note": (
                    "Second rejected topology-derived candidate likewise lacks a stable "
                    "mapping into the coordinate-dependent RRRR enumeration."
                ),
            },
        ],
        "concurrency_false_positive_fixture": {
            "description": (
                "Single-pose visual near-concurrency of four drawn axes can look "
                "convincing while branch-wide concurrency fails. Visual passage at one "
                "pose is insufficient for spherical-four-bar claims."
            ),
            "candidate_ids_for_manual_review": [
                c["candidate_id"] for c in bundle["candidates"][:3]
            ],
        },
        "concurrency_pass_at_one_pose_fixture": {
            "description": (
                "Deliberately constructed display where selected axes appear concurrent "
                "at the default pose only — still not a certification."
            ),
            "pose_q": list(fk.q),
        },
        "shortlist_for_later_validation": [
            {
                "candidate_id": c["candidate_id"],
                "topology": c["topology"],
                "pair_set": c["pair_set"],
                "reason": "enabled compound parent with preserved provenance",
            }
            for c in bundle["candidates"]
            if c["s_choice"] == "Sz"
        ],
        "claims_forbidden": [
            "No candidate is a spherical four-bar based on this project alone.",
            "Visual concurrency is preliminary screening only.",
        ],
        "step_scene_count": len(bundle["scenes"]),
    }
    audit_path = output_dir / "data" / "visual_audit.json"
    write_json(audit_path, audit)
    data_files.append(str(audit_path))

    # Keep classic Scene A/B/C filenames as copies/aliases for plan compatibility
    alias_map = {
        "01_physical_manipulator.html": "01e_physical_assembled.html",
        "02_virtual_spherical_closure.html": "02c_virtual_closure_assembled.html",
        "03_terminal_roll_quotient.html": "03d_terminal_roll_quotient.html",
    }
    for alias, source in alias_map.items():
        src = output_dir / "scenes" / source
        dst = output_dir / "scenes" / alias
        if src.is_file():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    manifest = Manifest(
        project="aligned_terminal_roll_visual_probe",
        disclaimer=DISCLAIMER,
        config_name=config.name,
        output_dir=str(output_dir),
        scenes=tuple(scenes),
        data_files=tuple(data_files),
    )
    write_manifest(output_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    args = build_parser().parse_args()
    config_path = args.config or default_config_path()
    if not config_path.is_file():
        raise SystemExit(f"missing config: {config_path}")
    manifest = generate(
        args.output_dir,
        config_path,
        shell_only=args.shell_only,
        skip_plots=args.skip_plots,
    )
    print(DISCLAIMER)
    print(f"wrote manifest: {args.output_dir / 'manifest.json'}")
    print(f"scenes: {len(manifest.scenes)}")
    print(f"data files: {len(manifest.data_files)}")
    print(f"step gallery: {args.output_dir / 'scenes' / 'gallery.html'}")


if __name__ == "__main__":
    main()
