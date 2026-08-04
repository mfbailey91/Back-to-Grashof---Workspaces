from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "robot_corpus" / "manifest.json"


def data() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_group_counts_and_unique_ids() -> None:
    manifest = data()
    models = manifest["models"]
    ids = [model["id"] for model in models]
    assert len(ids) == len(set(ids))
    for group, metadata in manifest["groups"].items():
        count = sum(model["group"] == group for model in models)
        assert count == metadata["expected_count"], (group, count)


def test_primary_and_control_signatures() -> None:
    models = data()["models"]
    for model in models:
        assert len(model["expected_signature"]) == model["expected_dof"]
        if model["group"] == "primary_6r":
            assert model["expected_signature"] == ["revolute"] * 6
        if model["group"] == "redundant_7r_control":
            assert model["expected_signature"] == ["revolute"] * 7


def test_universal_robot_family_is_complete() -> None:
    models = data()["models"]
    selected = {model["id"] for model in models if model["source_id"] == "universal_robots_ros2_description"}
    assert selected == {"ur3e", "ur5e", "ur8long", "ur10e", "ur15", "ur20", "ur30"}


def test_fetch_is_explicitly_arm_only() -> None:
    fetch = next(model for model in data()["models"] if model["id"] == "fetch_arm")
    assert fetch["selection_policy"] == "arm_only_subchain"
    assert fetch["chain"] == {"base_link": "torso_lift_link", "tip_link": "wrist_roll_link"}
    assert len(fetch["included_joints"]) == 7
    assert "torso_lift" in fetch["excluded_subsystems"]


def test_project_planar_urdfs_are_current_and_rrr() -> None:
    generator = ROOT / "scripts" / "generate_planar3r_urdfs.py"
    completed = subprocess.run([sys.executable, str(generator), "--check"], cwd=ROOT, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr

    for path in sorted((ROOT / "fixtures" / "planar3r").glob("*.urdf")):
        root = ET.parse(path).getroot()
        joints = [joint for joint in root.findall("joint") if joint.attrib["type"] != "fixed"]
        assert [joint.attrib["type"] for joint in joints] == ["continuous"] * 3
        assert [joint.find("axis").attrib["xyz"] for joint in joints] == ["0 0 1"] * 3


def test_inspector_selects_project_planar_chain() -> None:
    inspector = ROOT / "scripts" / "inspect_urdf.py"
    urdf = ROOT / "fixtures" / "planar3r" / "symmetric_disk.urdf"
    completed = subprocess.run(
        [sys.executable, str(inspector), str(urdf), "--base-link", "base_link", "--tip-link", "tool0", "--expect-dof", "3", "--expect-signature", "revolute,revolute,revolute"],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["actuated_dof"] == 3
