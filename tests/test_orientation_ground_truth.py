"""Sprint 4 sampling / IK / fixed-position / Gate-2 tests."""

from __future__ import annotations

import math

import numpy as np
import pytest

from sixr_grashof.architectures import ArchitectureA
from sixr_grashof.experiments.convergence import run_convergence_study
from sixr_grashof.experiments.fixed_position import run_fixed_position_experiment
from sixr_grashof.kinematics.ik import (
    regional_reachable_wrist,
    solve_ik,
    wrist_center_from_pose,
)
from sixr_grashof.sampling.orientations import (
    geodesic_angle,
    rotation_from_mat4,
    sample_orientations,
)
from sixr_grashof.sampling.workspace import architecture_a_workspace_samples


def test_orientation_sampling_reproducible() -> None:
    a = sample_orientations("coarse", seed=7, count=64)
    b = sample_orientations("coarse", seed=7, count=64)
    assert len(a) == 64
    assert all(np.allclose(Ra, Rb) for Ra, Rb in zip(a, b, strict=True))
    c = sample_orientations("coarse", seed=8, count=64)
    assert not all(np.allclose(Ra, Rc) for Ra, Rc in zip(a, c, strict=True))


def test_ik_recovers_fk_pose() -> None:
    arch = ArchitectureA()
    q = (0.1, 0.2, -0.15, 0.3, 0.4, -0.2)
    fk = arch.forward(q)
    R = rotation_from_mat4(fk.tool_transform)
    sol = solve_ik(arch, fk.tool_position, R, seed=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), n_starts=8)
    assert sol.status == "solved"
    assert sol.configuration is not None
    assert sol.position_error < 1e-4
    assert sol.orientation_error < 1e-3


def test_unreachable_vs_solver_failed() -> None:
    arch = ArchitectureA()
    target_p = (10.0, 0.0, 0.0)
    R = np.eye(3)
    cw = wrist_center_from_pose(target_p, R, arch.params.Lt)
    assert not regional_reachable_wrist(cw, L2=arch.params.L2, L3=arch.params.L3)
    sol = solve_ik(arch, target_p, R, n_starts=3)
    assert sol.status == "unreachable"

    sample = architecture_a_workspace_samples()[0]
    fk = arch.forward(sample.joint_seed)
    R_tgt = rotation_from_mat4(fk.tool_transform)
    Rx = np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, -1.0]])
    R_hard = R_tgt @ Rx
    sol2 = solve_ik(
        arch,
        fk.tool_position,
        R_hard,
        seed=(3.0, 3.0, 3.0, 3.0, 3.0, 3.0),
        n_starts=1,
        rng_seed=99,
        pos_tol=1e-12,
        ori_tol=1e-12,
        geometric_precheck=True,
    )
    cw2 = wrist_center_from_pose(fk.tool_position, R_hard, arch.params.Lt)
    if regional_reachable_wrist(cw2, L2=arch.params.L2, L3=arch.params.L3):
        assert sol2.status in {"solved", "solver_failed"}
        if sol2.status == "solver_failed":
            assert sol2.notes != "wrist center outside regional annulus"


def test_fixed_position_repeatable() -> None:
    arch = ArchitectureA()
    sample = architecture_a_workspace_samples()[0]
    a = run_fixed_position_experiment(
        arch, sample, resolution="coarse", seed=1, n_ik_starts=3, orientation_count=24
    )
    b = run_fixed_position_experiment(
        arch, sample, resolution="coarse", seed=1, n_ik_starts=3, orientation_count=24
    )
    assert a.record.orientation_coverage == b.record.orientation_coverage
    assert a.record.orientation_component_count == b.record.orientation_component_count
    assert a.feasible_indices == b.feasible_indices
    assert a.record.solved_count + a.record.unreachable_count + a.record.solver_failed_count == 24


def test_architecture_a_spherical_wrist_sanity() -> None:
    """Among geometrically eligible orientations, Arch A should usually solve."""
    arch = ArchitectureA()
    sample = architecture_a_workspace_samples()[0]
    result = run_fixed_position_experiment(
        arch, sample, resolution="coarse", seed=0, n_ik_starts=6, orientation_count=64
    )
    assert result.record.unreachable_count >= 1  # fixed-p wrist-sphere constraint
    assert result.eligible_solve_rate >= 0.55
    assert result.record.solved_count >= 8

    # Fixed wrist center: roll samples about the seed approach axis should solve.
    fk = arch.forward(sample.joint_seed)
    R0 = rotation_from_mat4(fk.tool_transform)
    solved = 0
    for k in range(12):
        ang = 2 * math.pi * k / 12
        c, s = math.cos(ang), math.sin(ang)
        Rz = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        R = R0 @ Rz
        sol = solve_ik(arch, sample.position, R, seed=sample.joint_seed, n_starts=10)
        if sol.status == "solved":
            solved += 1
    assert solved >= 6


def test_gate2_convergence_smoke() -> None:
    report = run_convergence_study(
        seed=0,
        resolutions=("coarse", "medium"),
        n_ik_starts=3,
        orientation_counts={"coarse": 24, "medium": 48},
        coverage_tol=0.35,
    )
    assert len(report.metrics) == 2
    assert report.metrics[0].sample_count == 24
    assert report.metrics[1].sample_count == 48
    d = report.to_dict()
    assert "gate2_pass" in d
    assert math.isfinite(report.coverage_delta_coarse_medium)


def test_geodesic_identity() -> None:
    R = np.eye(3)
    assert geodesic_angle(R, R) == pytest.approx(0.0)
