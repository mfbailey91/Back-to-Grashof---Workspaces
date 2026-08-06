"""Scene export and CLI manifest tests."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.visual_probe.cli import generate
from grashof_workspace.visual_probe.config import default_config_path


def test_shell_only_manifest_has_no_scenes(tmp_path: Path) -> None:
    out = tmp_path / "shell"
    manifest = generate(out, default_config_path(), shell_only=True)
    assert manifest.scenes == ()
    payload = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert payload["scenes"] == []
    assert "VISUAL PROBE ONLY" in payload["disclaimer"]


def test_full_generate_writes_required_artifacts(tmp_path: Path) -> None:
    out = tmp_path / "full"
    manifest = generate(out, default_config_path(), shell_only=False)
    assert (out / "manifest.json").is_file()
    assert (out / "scenes" / "01e_physical_assembled.html").is_file()
    assert (out / "scenes" / "01_physical_manipulator.html").is_file()
    assert (out / "scenes" / "02c_virtual_closure_assembled.html").is_file()
    assert (out / "scenes" / "02_virtual_spherical_closure.html").is_file()
    assert (out / "scenes" / "03d_terminal_roll_quotient.html").is_file()
    assert (out / "scenes" / "03_terminal_roll_quotient.html").is_file()
    assert (out / "scenes" / "01a_links_only.html").is_file()
    assert (out / "scenes" / "01b2_world_xyz.html").is_file()
    assert (out / "scenes" / "01b3_local_frames.html").is_file()
    assert (out / "data" / "frames.json").is_file()
    assert (out / "scenes" / "steps" / "04_pair_R1_R2.html").is_file()
    assert (out / "scenes" / "gallery.html").is_file()
    assert (out / "plots" / "01a_links_only.png").is_file()
    assert (out / "data" / "axis_relationships.json").is_file()
    assert (out / "data" / "compound_parents.json").is_file()
    assert (out / "data" / "candidates.json").is_file()
    assert (out / "contact_sheets" / "candidates.html").is_file()
    assert (out / "index.html").is_file()
    assert (out / "data" / "visual_audit.json").is_file()

    parents = json.loads((out / "data" / "compound_parents.json").read_text(encoding="utf-8"))
    assert sum(1 for p in parents if p["enabled"]) == 3
    for p in parents:
        if p["enabled"]:
            assert (
                out / "scenes" / "reductions" / f"05b_{p['pair_set']}_{p['topology']}.html"
            ).is_file()

    candidates = json.loads((out / "data" / "candidates.json").read_text(encoding="utf-8"))
    assert len(candidates) == 36
    assert any(s.scene_id == "index" for s in manifest.scenes)
    assert any(s.scene_id == "gallery" for s in manifest.scenes)
    # Broken-out step scenes should substantially exceed the original A/B/C set.
    step_html = list((out / "scenes").rglob("*.html"))
    assert len(step_html) >= 20

    index_html = (out / "index.html").read_text(encoding="utf-8")
    assert "PROBE_BUNDLE" in index_html
    assert "Orthographic" in index_html

    gallery = (out / "scenes" / "gallery.html").read_text(encoding="utf-8")
    assert "Step 01a" in gallery or "01a_links_only" in gallery
    assert "A_physical" in gallery
    assert "data:image/png;base64," in gallery


def test_skip_plots_still_writes_html(tmp_path: Path) -> None:
    out = tmp_path / "noplots"
    generate(out, default_config_path(), shell_only=False, skip_plots=True)
    assert (out / "scenes" / "gallery.html").is_file()
    assert not (out / "plots" / "01a_links_only.png").is_file()
