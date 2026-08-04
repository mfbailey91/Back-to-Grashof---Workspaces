#!/usr/bin/env python3
"""Inspect a flat URDF and select a precise base-to-tip kinematic subchain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ACTUATED = {"revolute", "continuous", "prismatic"}


def norm_type(value: str) -> str:
    return "revolute" if value == "continuous" else value


def vector(element: ET.Element | None, attribute: str, default: str) -> list[float]:
    text = default if element is None else element.attrib.get(attribute, default)
    values = [float(item) for item in text.split()]
    if len(values) != 3:
        raise ValueError(f"Expected three values for {attribute}: {text!r}")
    return values


def parse(path: Path) -> tuple[str | None, set[str], list[dict[str, object]]]:
    text = path.read_text(encoding="utf-8")
    if "<xacro:" in text or "xmlns:xacro" in text:
        raise ValueError("Xacro detected; expand it before using the flat-URDF inspector")
    root = ET.fromstring(text)
    if root.tag != "robot":
        raise ValueError(f"Expected <robot>, found <{root.tag}>")
    links = {item.attrib["name"] for item in root.findall("link")}
    joints = []
    for item in root.findall("joint"):
        parent = item.find("parent")
        child = item.find("child")
        if parent is None or child is None:
            raise ValueError(f"Joint {item.attrib.get('name')} lacks parent or child")
        origin = item.find("origin")
        axis = item.find("axis")
        joint_type = item.attrib.get("type", "")
        joints.append({
            "name": item.attrib.get("name", "<unnamed>"),
            "type": joint_type,
            "normalized_type": norm_type(joint_type),
            "parent": parent.attrib["link"],
            "child": child.attrib["link"],
            "origin_xyz": vector(origin, "xyz", "0 0 0"),
            "origin_rpy": vector(origin, "rpy", "0 0 0"),
            "axis": vector(axis, "xyz", "1 0 0"),
            "actuated": joint_type in ACTUATED,
        })
    return root.attrib.get("name"), links, joints


def find_path(joints: list[dict[str, object]], base: str, tip: str) -> list[dict[str, object]]:
    outgoing: dict[str, list[dict[str, object]]] = {}
    for joint in joints:
        outgoing.setdefault(str(joint["parent"]), []).append(joint)

    stack: list[tuple[str, list[dict[str, object]], set[str]]] = [(base, [], {base})]
    matches: list[list[dict[str, object]]] = []
    while stack:
        link, path, visited = stack.pop()
        if link == tip:
            matches.append(path)
            continue
        for joint in outgoing.get(link, []):
            child = str(joint["child"])
            if child not in visited:
                stack.append((child, [*path, joint], {*visited, child}))
    if not matches:
        raise ValueError(f"No path from {base!r} to {tip!r}")
    if len(matches) > 1:
        raise ValueError(f"Multiple paths from {base!r} to {tip!r}")
    return matches[0]


def longest_actuated_path(links: set[str], joints: list[dict[str, object]]) -> tuple[str, str, list[dict[str, object]]]:
    children = {str(joint["child"]) for joint in joints}
    roots = sorted(links - children)
    if not roots:
        raise ValueError("No root link found")
    outgoing: dict[str, list[dict[str, object]]] = {}
    for joint in joints:
        outgoing.setdefault(str(joint["parent"]), []).append(joint)

    candidates: list[tuple[str, str, list[dict[str, object]]]] = []
    for root in roots:
        stack = [(root, [], {root})]
        while stack:
            link, path, visited = stack.pop()
            next_joints = outgoing.get(link, [])
            if not next_joints:
                candidates.append((root, link, path))
            for joint in next_joints:
                child = str(joint["child"])
                if child not in visited:
                    stack.append((child, [*path, joint], {*visited, child}))
    return max(candidates, key=lambda item: (sum(bool(j["actuated"]) for j in item[2]), len(item[2])))


def inspect(path: Path, base: str | None, tip: str | None) -> dict[str, object]:
    robot_name, links, joints = parse(path)
    if (base is None) != (tip is None):
        raise ValueError("Provide both --base-link and --tip-link")
    if base is not None and tip is not None:
        chain = find_path(joints, base, tip)
        selected_base, selected_tip = base, tip
    else:
        selected_base, selected_tip, chain = longest_actuated_path(links, joints)
    actuated = [joint for joint in chain if joint["actuated"]]
    return {
        "path": str(path),
        "robot_name": robot_name,
        "base_link": selected_base,
        "tip_link": selected_tip,
        "actuated_dof": len(actuated),
        "actuated_signature": [joint["normalized_type"] for joint in actuated],
        "chain": chain,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urdf", type=Path)
    parser.add_argument("--base-link")
    parser.add_argument("--tip-link")
    parser.add_argument("--expect-dof", type=int)
    parser.add_argument("--expect-signature")
    args = parser.parse_args()
    try:
        result = inspect(args.urdf, args.base_link, args.tip_link)
    except (OSError, ET.ParseError, ValueError) as error:
        print(f"URDF inspection failed: {error}", file=sys.stderr)
        return 2

    failures = []
    if args.expect_dof is not None and result["actuated_dof"] != args.expect_dof:
        failures.append(f"expected DOF {args.expect_dof}, found {result['actuated_dof']}")
    if args.expect_signature:
        expected = [norm_type(item.strip()) for item in args.expect_signature.split(",") if item.strip()]
        if result["actuated_signature"] != expected:
            failures.append(f"expected signature {expected}, found {result['actuated_signature']}")
    print(json.dumps(result, indent=2, sort_keys=True))
    for failure in failures:
        print(f"validation failure: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
