"""Sprint 2 reduction engine tests."""

from __future__ import annotations

import math

import pytest

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.classification import classify_spherical
from sixr_grashof.reductions import (
    reduce_architecture_a,
    reduce_architecture_b,
    reduce_architecture_c,
)

ZERO = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_architecture_a_home_spherical_repeatable() -> None:
    arch = ArchitectureA()
    r1 = reduce_architecture_a(arch, ZERO)
    r2 = reduce_architecture_a(arch, ZERO)
    assert r1.spherical.linkage is not None
    assert r2.spherical.linkage is not None
    assert r1.spherical.linkage == r2.spherical.linkage
    assert r1.spherical.status == "exact"
    assert r1.regional.wrist_reachable is True
    link = r1.spherical.linkage
    assert link.alpha == pytest.approx(math.pi / 2, abs=1e-9)
    assert link.eta == pytest.approx(math.pi / 2, abs=1e-9)
    assert link.beta == pytest.approx(math.pi / 2, abs=1e-9)
    assert link.gamma == pytest.approx(math.pi, abs=1e-9)
    result = classify_spherical(link)
    assert result.linkage_type == 11


def test_architecture_a_same_state_identical_regional() -> None:
    arch = ArchitectureA()
    q = (0.2, -0.3, 0.4, 0.1, -0.2, 0.05)
    a = reduce_architecture_a(arch, q)
    b = reduce_architecture_a(arch, q)
    assert a.regional.rho_w == pytest.approx(b.regional.rho_w)
    assert a.regional.ground == pytest.approx(b.regional.ground)
    assert a.spherical.linkage == b.spherical.linkage


def test_architecture_b_large_offset_withholds_or_labels() -> None:
    arch = ArchitectureB(ArchitectureParams(epsilon_w=0.20))
    result = reduce_architecture_b(arch, ZERO)
    assert result.spherical.concurrency.residual_rho > 0.0
    if result.spherical.status == "invalid":
        assert result.spherical.linkage is None
    else:
        assert result.spherical.status == "approximate"
        assert result.spherical.concurrency.residual_rho > 1e-9


def test_architecture_b_zero_offset_exact() -> None:
    arch = ArchitectureB(ArchitectureParams(epsilon_w=0.0))
    result = reduce_architecture_b(arch, ZERO)
    assert result.spherical.status == "exact"
    assert result.spherical.linkage is not None


def test_architecture_c_spherical_exact_for_offsets() -> None:
    for es in (0.0, 0.05, 0.20):
        arch = ArchitectureC(ArchitectureParams(epsilon_s=es))
        result = reduce_architecture_c(arch, ZERO)
        assert result.spherical.status == "exact"
        assert result.spherical.linkage is not None
        assert result.spherical.concurrency.residual_rho == pytest.approx(0.0, abs=1e-9)
