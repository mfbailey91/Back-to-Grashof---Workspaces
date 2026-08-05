"""Unit tests for serial revolute PoE kinematics."""

from __future__ import annotations

import math

import pytest

from grashof_workspace.spatial_experiments.axis_geometry import AxisLine
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain


def _one_joint_chain() -> SerialRevoluteChain:
    axis = AxisLine((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    R0 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    return SerialRevoluteChain(home_axes=(axis,), p0=(1.0, 0.0, 0.0), d0=(0.0, 0.0, 1.0), R0=R0)


def test_evaluate_identity_at_zero() -> None:
    chain = _one_joint_chain()
    state = chain.evaluate((0.0,))
    assert state.p == pytest.approx((1.0, 0.0, 0.0))
    assert state.d == pytest.approx((0.0, 0.0, 1.0))


def test_single_joint_ninety_degree_interior() -> None:
    chain = _one_joint_chain()
    state = chain.evaluate((math.pi / 2,))
    assert state.p[0] == pytest.approx(0.0, abs=1e-12)
    assert state.p[1] == pytest.approx(1.0, abs=1e-12)
    assert state.d == pytest.approx((0.0, 0.0, 1.0))


def test_rejects_wrong_q_dimension() -> None:
    chain = _one_joint_chain()
    with pytest.raises(ValueError, match="expected 1 joint"):
        chain.evaluate((0.1, 0.2))


def test_rejects_empty_chain() -> None:
    R0 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="at least one"):
        SerialRevoluteChain(home_axes=(), p0=(0.0, 0.0, 0.0), d0=(0.0, 0.0, 1.0), R0=R0)
