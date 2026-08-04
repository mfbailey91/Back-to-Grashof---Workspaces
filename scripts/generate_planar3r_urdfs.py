#!/usr/bin/env python3
"""Generate project-authored planar 3R URDF fixtures from link-ratio cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data" / "robot_corpus" / "planar3r_instances.json"
OUTPUT = ROOT / "fixtures" / "planar3r"


def fmt(value: float) -> str:
    return f"{value:.12g}"


def make_urdf(instance: dict[str, object]) -> str:
    name = str(instance["id"])
    lengths = [float(instance[key]) for key in ("l1", "l2", "l3")]
    max_length = max(lengths)
    width = max(0.04, 0.06 * max_length)
    height = width

    link_xml = []
    for index, length in enumerate(lengths, start=1):
        link_xml.append(f"""  <link name="link_{index}">\n    <visual>\n      <origin xyz="{fmt(length / 2)} 0 0" rpy="0 0 0"/>\n      <geometry><box size="{fmt(length)} {fmt(width)} {fmt(height)}"/></geometry>\n    </visual>\n    <collision>\n      <origin xyz="{fmt(length / 2)} 0 0" rpy="0 0 0"/>\n      <geometry><box size="{fmt(length)} {fmt(width)} {fmt(height)}"/></geometry>\n    </collision>\n  </link>""")

    return f"""<?xml version="1.0"?>
<!-- Project-authored planar 3R fixture: {instance['name']} -->
<robot name="project_planar3r_{name}">
  <link name="base_link"/>
{link_xml[0]}
{link_xml[1]}
{link_xml[2]}
  <link name="tool0"/>

  <joint name="joint_1" type="continuous">
    <parent link="base_link"/><child link="link_1"/>
    <origin xyz="0 0 0" rpy="0 0 0"/><axis xyz="0 0 1"/>
  </joint>
  <joint name="joint_2" type="continuous">
    <parent link="link_1"/><child link="link_2"/>
    <origin xyz="{fmt(lengths[0])} 0 0" rpy="0 0 0"/><axis xyz="0 0 1"/>
  </joint>
  <joint name="joint_3" type="continuous">
    <parent link="link_2"/><child link="link_3"/>
    <origin xyz="{fmt(lengths[1])} 0 0" rpy="0 0 0"/><axis xyz="0 0 1"/>
  </joint>
  <joint name="tool_fixed" type="fixed">
    <parent link="link_3"/><child link="tool0"/>
    <origin xyz="{fmt(lengths[2])} 0 0" rpy="0 0 0"/>
  </joint>
</robot>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    instances = json.loads(CONFIG.read_text(encoding="utf-8"))["instances"]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    mismatches = []
    for instance in instances:
        path = OUTPUT / f"{instance['id']}.urdf"
        expected = make_urdf(instance)
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(expected, encoding="utf-8")
            print(path.relative_to(ROOT))
    if mismatches:
        print("Generated planar URDFs are stale: " + ", ".join(mismatches), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
