"""Frame triad and coordinate convention tests."""

from __future__ import annotations

import math

from grashof_workspace.visual_probe.config import default_config_path, load_config
from grashof_workspace.visual_probe.forward_kinematics import forward_kinematics
from grashof_workspace.visual_probe.scene import fk_payload
from grashof_workspace.visual_probe.transforms import triad_from_mat4, world_frame_mat4


def _unit(v: list[float]) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def test_world_frame_is_identity_at_origin() -> None:
    origin, x, y, z = triad_from_mat4(world_frame_mat4())
    assert origin == (0.0, 0.0, 0.0)
    assert x == (1.0, 0.0, 0.0)
    assert y == (0.0, 1.0, 0.0)
    assert z == (0.0, 0.0, 1.0)


def test_fk_payload_includes_world_and_local_frames() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    payload = fk_payload(fk, cfg)
    assert payload["world_frame"]["label"] == "W"
    assert payload["world_frame"]["origin_world"] == [0.0, 0.0, 0.0]
    assert len(payload["local_frames"]) == 7  # R1..R6 + tool
    for fr in payload["local_frames"]:
        assert abs(_unit(fr["local_x"]) - 1.0) < 1e-12
        assert abs(_unit(fr["local_y"]) - 1.0) < 1e-12
        assert abs(_unit(fr["local_z"]) - 1.0) < 1e-12
    # Local z of each joint aligns with revolute axis.
    for joint, fr in zip(fk.joints, payload["local_frames"][:6], strict=True):
        z = fr["local_z"]
        d = joint.axis.direction
        cross = (
            z[1] * d[2] - z[2] * d[1],
            z[2] * d[0] - z[0] * d[2],
            z[0] * d[1] - z[1] * d[0],
        )
        assert (cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2) ** 0.5 < 1e-9
