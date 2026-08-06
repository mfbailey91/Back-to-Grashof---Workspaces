"""Terminal alignment and roll-preservation tests."""

from __future__ import annotations

from grashof_workspace.visual_probe.axis_geometry import parallelism_residual, point_axis_distance
from grashof_workspace.visual_probe.config import default_config_path, load_config
from grashof_workspace.visual_probe.forward_kinematics import forward_kinematics
from grashof_workspace.visual_probe.virtual_closure import (
    roll_preserves_task,
    virtual_spherical_closure,
)


def test_task_point_on_r6_and_pointing_parallel() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    assert point_axis_distance(fk.tool_point, fk.joints[5].axis) < 1e-9
    assert parallelism_residual(fk.pointing, fk.joints[5].axis.direction) < 1e-9


def test_spherical_center_equals_task_point() -> None:
    cfg = load_config(default_config_path())
    fk = forward_kinematics(cfg)
    closure = virtual_spherical_closure(fk)
    assert closure.center == fk.tool_point


def test_q6_change_preserves_p_and_d() -> None:
    cfg = load_config(default_config_path())
    fk_a = forward_kinematics(cfg)
    q_b = (*fk_a.q[:5], cfg.roll_compare_q6)
    fk_b = forward_kinematics(cfg, q_b)
    assert roll_preserves_task(fk_a, fk_b)
    # Full tool frame changes (Sx/Sy rotate about Sz).
    ca = virtual_spherical_closure(fk_a)
    cb = virtual_spherical_closure(fk_b)
    assert ca.sx.direction != cb.sx.direction or ca.sy.direction != cb.sy.direction
