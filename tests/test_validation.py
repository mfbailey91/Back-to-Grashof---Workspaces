"""Boundary probes, seeded property tests, and sampling extrema checks."""

from __future__ import annotations

import random
from math import isclose

import pytest

from grashof_workspace.planar3r import FULL_COVERAGE, Planar3R

PROPERTY_SEED = 20260803


def test_orientation_sampling_includes_phi_extrema() -> None:
    robot = Planar3R(2.0, 2.0, 1.0)
    # Odd sample counts would miss pi on a uniform grid without the forced extrema.
    coverage = robot.sampled_orientation_coverage(2.0, 0.0, samples=5)
    assert isclose(coverage, FULL_COVERAGE)


def test_boundary_probes_inside_on_outside() -> None:
    robot = Planar3R(3.0, 2.0, 1.5)
    epsilon = 1e-8 * max(robot.l1, robot.l2, robot.l3)
    boundaries = []
    for inner, outer in robot.dexterous_radial_intervals():
        boundaries.extend([inner, outer])
    for rho_b in boundaries:
        for rho in (rho_b - epsilon, rho_b, rho_b + epsilon):
            if rho < 0.0:
                continue
            analytical = robot.is_dexterous_radius(rho)
            coverage = robot.sampled_orientation_coverage(rho, 0.0, samples=360)
            sampled_full = isclose(coverage, FULL_COVERAGE)
            assert analytical == sampled_full, (
                f"boundary probe failed for l=({robot.l1},{robot.l2},{robot.l3}) "
                f"at rho={rho} (boundary={rho_b}): analytical={analytical}, "
                f"coverage={coverage}"
            )


def test_scale_invariance_of_dexterity() -> None:
    base = Planar3R(2.0, 1.5, 1.0)
    scaled = Planar3R(4.0, 3.0, 2.0)
    for rho in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5):
        assert base.is_dexterous_radius(rho) == scaled.is_dexterous_radius(2.0 * rho)
        assert (
            base.mechanism_state(rho).inversion_type
            == scaled.mechanism_state(2.0 * rho).inversion_type
        )


def test_seeded_randomized_dexterity_matches_sampling() -> None:
    rng = random.Random(PROPERTY_SEED)
    failures: list[str] = []
    for _ in range(250):
        l1 = rng.uniform(0.5, 3.0)
        l2 = rng.uniform(0.5, 3.0)
        l3 = rng.uniform(0.25, 3.0)
        robot = Planar3R(l1, l2, l3)
        reachable_inner, reachable_outer = robot.reachable_radial_interval()
        span = max(reachable_outer - reachable_inner, 1e-9)
        for _probe in range(20):
            rho = reachable_inner + rng.random() * span * 1.1
            if rho < 0.0:
                continue
            analytical = robot.is_dexterous_radius(rho)
            coverage = robot.sampled_orientation_coverage(rho, 0.0, samples=180)
            sampled_full = isclose(coverage, FULL_COVERAGE)
            if analytical != sampled_full:
                failures.append(
                    f"seed={PROPERTY_SEED} l=({l1:.6g},{l2:.6g},{l3:.6g}) "
                    f"rho={rho:.6g} analytical={analytical} coverage={coverage}"
                )
                break
        if len(failures) >= 5:
            break
    assert not failures, "\n".join(failures)


@pytest.mark.stress
def test_stress_randomized_dexterity_matches_sampling() -> None:
    rng = random.Random(PROPERTY_SEED + 1)
    for _ in range(1000):
        robot = Planar3R(rng.uniform(0.5, 4.0), rng.uniform(0.5, 4.0), rng.uniform(0.2, 4.0))
        inner, outer = robot.reachable_radial_interval()
        for _probe in range(40):
            rho = max(0.0, inner + rng.random() * max(outer - inner, 1e-9) * 1.2)
            analytical = robot.is_dexterous_radius(rho)
            coverage = robot.sampled_orientation_coverage(rho, 0.0, samples=240)
            assert analytical == isclose(coverage, FULL_COVERAGE), (
                f"stress fail seed={PROPERTY_SEED + 1} "
                f"l=({robot.l1},{robot.l2},{robot.l3}) rho={rho} "
                f"analytical={analytical} coverage={coverage}"
            )
