"""JSON configuration loader and validation for the visual probe."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import JointSpec, ProbeConfig, Vec3
from .transforms import normalize


def _as_vec3(value: Any, *, field_name: str) -> Vec3:
    if not isinstance(value, list | tuple) or len(value) != 3:
        raise ValueError(f"{field_name} must be a length-3 array")
    try:
        vec = (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must contain numeric components") from exc
    return vec


def _as_unit_vec3(value: Any, *, field_name: str) -> Vec3:
    vec = _as_vec3(value, field_name=field_name)
    try:
        return normalize(vec, name=field_name)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a nonzero direction") from exc


def config_from_dict(data: dict[str, Any]) -> ProbeConfig:
    """Validate and build a ``ProbeConfig`` from a mapping."""
    if not isinstance(data, dict):
        raise TypeError("configuration root must be an object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a nonempty string")

    description = data.get("description", "")
    if not isinstance(description, str):
        raise TypeError("description must be a string")

    joints_raw = data.get("joints")
    if not isinstance(joints_raw, list) or len(joints_raw) != 6:
        raise ValueError("joints must be an array of length 6")

    joints: list[JointSpec] = []
    for i, item in enumerate(joints_raw):
        if not isinstance(item, dict):
            raise TypeError(f"joints[{i}] must be an object")
        index = int(item.get("index", i + 1))
        if index != i + 1:
            raise ValueError(f"joints[{i}].index must equal {i + 1}")
        label = item.get("label", f"R{index}")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"joints[{i}].label must be a nonempty string")
        point = _as_vec3(item.get("home_point"), field_name=f"joints[{i}].home_point")
        direction = _as_unit_vec3(
            item.get("home_direction"),
            field_name=f"joints[{i}].home_direction",
        )
        joints.append(
            JointSpec(index=index, home_point=point, home_direction=direction, label=label)
        )

    q_raw = data.get("default_q")
    if not isinstance(q_raw, list | tuple) or len(q_raw) != 6:
        raise ValueError("default_q must be a length-6 array")
    try:
        default_q = tuple(float(v) for v in q_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("default_q must contain numeric components") from exc
    if len(default_q) != 6:
        raise ValueError("default_q must be a length-6 array")

    tool_offset = float(data.get("tool_offset_along_r6", 0.08))
    roll_compare = float(data.get("roll_compare_q6", default_q[5] + 1.2))
    axis_length = float(data.get("axis_length", 0.35))
    frame_length = float(data.get("frame_length", 0.08))
    incidence_tol = float(data.get("incidence_tol", 1e-9))
    parallel_tol = float(data.get("parallel_tol", 1e-9))
    ambiguous_tol = float(data.get("ambiguous_tol", 1e-6))

    if axis_length <= 0.0 or frame_length <= 0.0:
        raise ValueError("axis_length and frame_length must be positive")
    if incidence_tol <= 0.0 or parallel_tol <= 0.0 or ambiguous_tol <= 0.0:
        raise ValueError("tolerances must be positive")

    return ProbeConfig(
        name=name.strip(),
        description=description,
        joints=tuple(joints),
        default_q=(
            default_q[0],
            default_q[1],
            default_q[2],
            default_q[3],
            default_q[4],
            default_q[5],
        ),
        tool_offset_along_r6=tool_offset,
        roll_compare_q6=roll_compare,
        axis_length=axis_length,
        frame_length=frame_length,
        incidence_tol=incidence_tol,
        parallel_tol=parallel_tol,
        ambiguous_tol=ambiguous_tol,
    )


def load_config(path: Path | str) -> ProbeConfig:
    """Load and validate a probe configuration JSON file."""
    cfg_path = Path(path)
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("configuration root must be an object")
    return config_from_dict(raw)


def default_config_path() -> Path:
    """Return the repository default architecture config path."""
    return Path(__file__).resolve().parents[3] / "configs" / "aligned_terminal_6r_visual_probe.json"
