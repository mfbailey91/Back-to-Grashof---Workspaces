"""Architecture A/B/C geometry acceptance tests."""

from __future__ import annotations

import pytest

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)

ZERO = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_architecture_a_exact_planar_and_spherical() -> None:
    arch = ArchitectureA()
    report = arch.geometry_report(ZERO)
    assert report.regional_exact_candidate is True
    assert report.spherical_status == "exact"
    assert report.wrist_concurrency.residual_rho == pytest.approx(0.0, abs=1e-12)
    assert report.z2_z3_parallel is True
    assert report.z1_z2_distance == pytest.approx(0.0, abs=1e-12)


def test_architecture_b_exact_only_at_zero_offset() -> None:
    exact = ArchitectureB(ArchitectureParams(epsilon_w=0.0)).geometry_report(ZERO)
    assert exact.spherical_status == "exact"
    assert exact.z2_z3_z4_parallel is True

    residuals = []
    for ew in (0.0, 0.025, 0.05, 0.10, 0.20):
        r = ArchitectureB(ArchitectureParams(epsilon_w=ew)).geometry_report(ZERO)
        residuals.append(r.wrist_concurrency.residual_rho)
        if ew == 0.0:
            assert r.spherical_status == "exact"
        else:
            assert r.spherical_status in {"approximate", "invalid"}
    # Residuals grow with epsilon_w.
    assert residuals == sorted(residuals)
    assert residuals[-1] > residuals[0]


def test_architecture_c_spherical_exact_for_all_shoulder_offsets() -> None:
    distances = []
    for es in (0.0, 0.025, 0.05, 0.10, 0.20):
        r = ArchitectureC(ArchitectureParams(epsilon_s=es)).geometry_report(ZERO)
        assert r.spherical_status == "exact"
        assert r.wrist_concurrency.residual_rho == pytest.approx(0.0, abs=1e-9)
        distances.append(r.z1_z2_distance)
        assert r.z1_z2_distance == pytest.approx(es, abs=1e-12)
    assert distances == sorted(distances)


def test_fk_tool_moves_with_base_joint() -> None:
    arch = ArchitectureA()
    t0 = arch.forward(ZERO).tool_position
    t1 = arch.forward((0.3, 0.0, 0.0, 0.0, 0.0, 0.0)).tool_position
    assert t0 != t1
