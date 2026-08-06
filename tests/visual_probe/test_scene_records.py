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
    assert (out / "scenes" / "01_physical_manipulator.html").is_file()
    assert (out / "scenes" / "02_virtual_spherical_closure.html").is_file()
    assert (out / "scenes" / "03_terminal_roll_quotient.html").is_file()
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
            assert (out / "scenes" / "reductions" / f"reduction_{p['pair_set']}.html").is_file()

    candidates = json.loads((out / "data" / "candidates.json").read_text(encoding="utf-8"))
    assert len(candidates) == 36
    assert any(s.scene_id == "index" for s in manifest.scenes)

    index_html = (out / "index.html").read_text(encoding="utf-8")
    assert "PROBE_BUNDLE" in index_html
    assert "Orthographic" in index_html
