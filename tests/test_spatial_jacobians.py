"""Unit tests for serial-chain Jacobians and rank helpers."""

from __future__ import annotations

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.aligned_6r import REGULAR_Q, GenericAligned6R
from grashof_workspace.spatial_experiments.jacobians import (
    central_difference_jacobians,
    kernel_alignment_to_unit,
    matrix_rank_report,
    nullspace,
    pointing_jacobian,
    position_jacobian,
    reduced_pointing_basis,
)


def test_rank_full_and_deficient_boundary() -> None:
    full = np.eye(3)
    report = matrix_rank_report(full)
    assert report.rank == 3
    assert report.nullity == 0
    deficient = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])
    rep2 = matrix_rank_report(deficient)
    assert rep2.rank == 2
    assert rep2.nullity == 1


def test_nullspace_drops_to_known_kernel() -> None:
    A = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])
    ker = nullspace(A)
    assert ker.shape == (3, 1)
    assert abs(float(ker[2, 0])) == pytest.approx(1.0)


def test_reduced_pointing_basis_drops_e6() -> None:
    # Fake J_p whose kernel is span{e4, e5, e6}.
    J_p = np.zeros((3, 6))
    J_p[0, 0] = 1.0
    J_p[1, 1] = 1.0
    J_p[2, 2] = 1.0
    nred = reduced_pointing_basis(J_p)
    assert nred.shape == (6, 2)
    assert float(np.linalg.norm(nred[5, :])) == pytest.approx(0.0, abs=1e-12)


def test_aligned_e6_columns_vanish_equality() -> None:
    chain = GenericAligned6R.aligned().chain
    jp = position_jacobian(chain, REGULAR_Q)
    jd = pointing_jacobian(chain, REGULAR_Q)
    assert float(np.linalg.norm(jp[:, -1])) == pytest.approx(0.0, abs=1e-12)
    assert float(np.linalg.norm(jd[:, -1])) == pytest.approx(0.0, abs=1e-12)


def test_misaligned_pointing_makes_jd_e6_exterior() -> None:
    chain = GenericAligned6R.misaligned_pointing().chain
    jd = pointing_jacobian(chain, REGULAR_Q)
    assert float(np.linalg.norm(jd[:, -1])) > 1e-6


def test_fd_matches_analytical_interior() -> None:
    chain = GenericAligned6R.aligned().chain
    jp = position_jacobian(chain, REGULAR_Q)
    jd = pointing_jacobian(chain, REGULAR_Q)
    jp_fd, jd_fd = central_difference_jacobians(chain, REGULAR_Q, 1e-6)
    assert float(np.linalg.norm(jp_fd - jp)) < 1e-7
    assert float(np.linalg.norm(jd_fd - jd)) < 1e-7


def test_kernel_alignment_parallel_and_orthogonal() -> None:
    e = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    assert kernel_alignment_to_unit(e, e) == pytest.approx(0.0)
    ortho = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert kernel_alignment_to_unit(ortho, e) == pytest.approx(1.0)
