"""Configuration loader tests for the visual probe."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from grashof_workspace.visual_probe import DISCLAIMER
from grashof_workspace.visual_probe.config import config_from_dict, default_config_path, load_config

ROOT = Path(__file__).resolve().parents[2]
PROBE_SRC = ROOT / "src" / "grashof_workspace" / "visual_probe"


def test_default_config_loads() -> None:
    cfg = load_config(default_config_path())
    assert cfg.name == "aligned_terminal_6r_visual_probe"
    assert len(cfg.joints) == 6
    assert DISCLAIMER


def test_rejects_malformed_axis_direction() -> None:
    raw = {
        "name": "bad",
        "joints": [
            {"index": i + 1, "home_point": [0, 0, float(i)], "home_direction": [0, 0, 1]}
            for i in range(6)
        ],
        "default_q": [0, 0, 0, 0, 0, 0],
        "tool_offset_along_r6": 0.1,
    }
    raw["joints"][0]["home_direction"] = [0, 0, 0]
    with pytest.raises(ValueError, match="nonzero"):
        config_from_dict(raw)


def test_rejects_wrong_joint_count() -> None:
    with pytest.raises(ValueError, match="length 6"):
        config_from_dict(
            {
                "name": "bad",
                "joints": [{"index": 1, "home_point": [0, 0, 0], "home_direction": [0, 0, 1]}],
                "default_q": [0, 0, 0, 0, 0, 0],
            }
        )


def test_probe_modules_do_not_import_planar_or_spatial_research() -> None:
    forbidden = {
        "grashof_workspace.planar3r",
        "grashof_workspace.fourbar",
        "grashof_workspace.atlas",
        "grashof_workspace.plotting",
        "grashof_workspace.spatial_experiments",
        "sixr_grashof",
    }
    for path in PROBE_SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    full = alias.name
                    assert full not in forbidden
                    assert not any(full == f or full.startswith(f + ".") for f in forbidden)
            elif isinstance(node, ast.ImportFrom) and node.module:
                full = node.module
                assert full not in forbidden
                assert not any(full == f or full.startswith(f + ".") for f in forbidden)
