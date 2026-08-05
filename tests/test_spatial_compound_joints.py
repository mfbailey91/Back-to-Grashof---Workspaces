"""Tests for compound-joint grouping, principal angles, and local N_red steps."""

from __future__ import annotations

import math

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    IntersectingPairsAligned6R,
)
from grashof_workspace.spatial_experiments.compound_joints import (
    COMPOUND_GROUPS,
    POINTING_AGREE_TOL,
    POSITION_RESIDUAL_TOL_M,
    PRINCIPAL_ANGLE_TOL_RAD,
    compare_reduced_tangents,
    compound_reduced_basis,
    embed_compound_tangent,
    local_nred_steps,
    principal_angles,
)
from grashof_workspace.spatial_experiments.jacobians import (
    position_jacobian,
    reduced_pointing_basis,
)


def test_compound_groups_literal() -> None:
    assert COMPOUND_GROUPS["UA"] == (0, 1)
    assert COMPOUND_GROUPS["UB"] == (2, 3)
    assert COMPOUND_GROUPS["RC"] == (4,)
    assert COMPOUND_GROUPS["roll"] == (5,)


def test_embed_compound_tangent_strips_roll() -> None:
    v = embed_compound_tangent((0.1, -0.2, 0.3, 0.4, -0.5, 9.0))
    assert v.shape == (6,)
    assert v[5] == 0.0
    assert tuple(v[:5]) == pytest.approx((0.1, -0.2, 0.3, 0.4, -0.5))


def test_principal_angles_identical_interior() -> None:
    a = np.eye(4)[:, :2]
    angles = principal_angles(a, a @ np.array([[0.0, -1.0], [1.0, 0.0]]))
    assert angles == pytest.approx(np.zeros(2), abs=1e-12)


def test_principal_angles_orthogonal_exterior() -> None:
    a = np.eye(4)[:, :2]
    b = np.eye(4)[:, 2:]
    angles = principal_angles(a, b)
    assert angles == pytest.approx(np.full(2, math.pi / 2.0), abs=1e-12)


def test_principal_angles_mixed_boundary() -> None:
    a = np.eye(4)[:, :2]
    b = np.column_stack([np.eye(4)[:, 0], np.eye(4)[:, 2]])
    angles = np.sort(principal_angles(a, b))
    assert angles[0] == pytest.approx(0.0, abs=1e-12)
    assert angles[1] == pytest.approx(math.pi / 2.0, abs=1e-12)


def test_intersecting_pairs_compound_matches_nred() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    report = compare_reduced_tangents(chain, INTERSECTING_PAIRS_REGULAR_Q)
    assert report.within_tolerance
    assert report.max_angle_rad <= PRINCIPAL_ANGLE_TOL_RAD
    n_phys = reduced_pointing_basis(position_jacobian(chain, INTERSECTING_PAIRS_REGULAR_Q))
    n_comp = compound_reduced_basis(chain, INTERSECTING_PAIRS_REGULAR_Q)
    assert n_phys.shape[1] == 2
    assert n_comp.shape[1] == 2


def test_local_nred_steps_physical_vs_compound() -> None:
    chain = IntersectingPairsAligned6R.aligned().chain
    seed = reduced_pointing_basis(position_jacobian(chain, INTERSECTING_PAIRS_REGULAR_Q))[:, 0]
    physical = local_nred_steps(
        chain,
        INTERSECTING_PAIRS_REGULAR_Q,
        compound=False,
        seed_direction=seed,
    )
    compound = local_nred_steps(
        chain,
        INTERSECTING_PAIRS_REGULAR_Q,
        compound=True,
        seed_direction=seed,
    )
    assert len(physical) == 3
    assert len(compound) == 3
    for p_rec, c_rec in zip(physical, compound, strict=True):
        assert float(p_rec["p_residual_m"]) <= POSITION_RESIDUAL_TOL_M
        assert float(c_rec["p_residual_m"]) <= POSITION_RESIDUAL_TOL_M
        d_p = np.asarray(p_rec["d"], dtype=float)
        d_c = np.asarray(c_rec["d"], dtype=float)
        assert float(np.linalg.norm(d_p - d_c)) <= POINTING_AGREE_TOL
