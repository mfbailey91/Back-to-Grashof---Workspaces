"""Forward-kinematics tests for the visual probe."""

from __future__ import annotations

import math

from grashof_workspace.visual_probe.config import default_config_path, load_config
from grashof_workspace.visual_probe.forward_kinematics import forward_kinematics
from grashof_workspace.visual_probe.transforms import (
    as_axis_line,
    identity4,
    matmul,
    screw_rotation,
    transform_point,
)


def test_axis_directions_are_unit_length() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    for joint in fk.joints:
        d = joint.axis.direction
        n = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        assert abs(n - 1.0) < 1e-12


def test_fk_matches_independent_partial_product_snapshot() -> None:
    cfg = load_config(default_config_path())
    q = cfg.default_q
    fk = forward_kinematics(cfg, q)

    partial = identity4()
    for i, spec in enumerate(cfg.joints):
        origin = transform_point(partial, spec.home_point)
        assert abs(origin[0] - fk.joints[i].origin[0]) < 1e-12
        assert abs(origin[1] - fk.joints[i].origin[1]) < 1e-12
        assert abs(origin[2] - fk.joints[i].origin[2]) < 1e-12
        home = as_axis_line(spec.home_point, spec.home_direction)
        partial = matmul(partial, screw_rotation(home, q[i]))


def test_link_endpoints_join_without_gaps() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    # Links between joints connect successive origins.
    for i, (a, b) in enumerate(fk.link_endpoints[:-1]):
        assert a == fk.joints[i].origin
        assert b == fk.joints[i + 1].origin
    assert fk.link_endpoints[-1][0] == fk.joints[5].origin
    assert fk.link_endpoints[-1][1] == fk.tool_point


def test_changing_one_joint_rotates_only_downstream() -> None:
    cfg = load_config(default_config_path())
    q0 = cfg.default_q
    fk0 = forward_kinematics(cfg, q0)
    q1 = (q0[0] + 0.4, q0[1], q0[2], q0[3], q0[4], q0[5])
    fk1 = forward_kinematics(cfg, q1)
    # Joint 1 origin is fixed in base; joint 2+ move.
    assert fk0.joints[0].origin == fk1.joints[0].origin
    moved = False
    for j0, j1 in zip(fk0.joints[1:], fk1.joints[1:]):
        if j0.origin != j1.origin:
            moved = True
            break
    assert moved
