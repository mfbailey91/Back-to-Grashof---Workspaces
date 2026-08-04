from math import isclose

import pytest

from grashof_workspace.planar3r import (
    FULL_COVERAGE,
    Planar3R,
    dexterous_topology,
)


def test_equal_first_links_produce_single_dexterous_disk() -> None:
    robot = Planar3R(2.0, 2.0, 1.0)
    assert robot.reachable_radial_interval() == (0.0, 5.0)
    assert robot.dexterous_radial_intervals() == ((0.0, 3.0),)
    assert robot.dexterous_topology() == "disk"


def test_unequal_first_links_can_produce_inner_dexterous_island() -> None:
    robot = Planar3R(3.0, 1.0, 2.5)
    assert robot.dexterous_radial_intervals() == ((0.0, 0.5),)
    assert robot.dexterous_topology() == "disk"
    assert robot.is_dexterous_radius(0.25)
    assert not robot.is_dexterous_radius(1.0)


def test_two_disconnected_dexterous_components_are_possible() -> None:
    robot = Planar3R(3.0, 2.0, 1.5)
    assert robot.dexterous_radial_intervals() == ((0.0, 0.5), (2.5, 3.5))
    assert robot.dexterous_topology() == "disk_and_annulus"


def test_no_dexterous_workspace_when_terminal_link_is_too_long() -> None:
    robot = Planar3R(1.0, 1.0, 3.0)
    assert robot.dexterous_radial_intervals() == ()
    assert robot.dexterous_topology() == "empty"


def test_boundary_case_preserves_degenerate_outer_circle() -> None:
    robot = Planar3R(3.0, 2.0, 2.0)
    assert robot.dexterous_radial_intervals() == ((0.0, 1.0), (3.0, 3.0))
    assert robot.dexterous_topology() == "degenerate"
    assert robot.is_dexterous_radius(3.0)
    assert not robot.is_dexterous_radius(2.0)


def test_annular_dexterous_component() -> None:
    # Outer branch only: rho in [l3 + |l1-l2|, l1+l2-l3]
    robot = Planar3R(3.0, 2.0, 0.5)
    intervals = robot.dexterous_radial_intervals()
    assert intervals == ((1.5, 4.5),)
    assert dexterous_topology(intervals) == "annulus"


def test_analytical_result_matches_orientation_sampling() -> None:
    robot = Planar3R(2.0, 2.0, 1.0)

    inside = robot.sampled_orientation_coverage(2.5, 0.0)
    outside = robot.sampled_orientation_coverage(3.5, 0.0)
    boundary = robot.sampled_orientation_coverage(3.0, 0.0)

    assert isclose(inside, FULL_COVERAGE)
    assert outside < FULL_COVERAGE
    assert isclose(boundary, FULL_COVERAGE)
    assert robot.is_dexterous_radius(3.0)
    assert not robot.is_dexterous_radius(3.5)


def test_fourbar_reduction_matches_workspace_predicate() -> None:
    robot = Planar3R(2.5, 1.5, 1.0)
    for rho in (0.0, 0.5, 1.0, 2.0, 3.0):
        assert (
            robot.is_dexterous_radius(rho)
            == robot.fourbar_at_radius(rho).input_can_fully_rotate()
        )


@pytest.mark.parametrize("lambda2", [0.5, 1.0, 1.5, 2.0])
@pytest.mark.parametrize("lambda3", [0.25, 0.5, 1.0, 1.5, 2.5])
def test_link_ratio_grid_sweep_matches_orientation_sampling(
    lambda2: float, lambda3: float
) -> None:
    robot = Planar3R(1.0, lambda2, lambda3)
    reachable_inner, reachable_outer = robot.reachable_radial_interval()
    probe_radii = {
        reachable_inner,
        reachable_outer,
        0.5 * (reachable_inner + reachable_outer),
    }
    for inner, outer in robot.dexterous_radial_intervals():
        probe_radii.add(inner)
        probe_radii.add(outer)
        probe_radii.add(0.5 * (inner + outer))
        if outer > inner:
            probe_radii.add(inner + 0.25 * (outer - inner))
            probe_radii.add(outer - 0.25 * (outer - inner))

    for rho in sorted(probe_radii):
        if rho < 0.0:
            continue
        analytical = robot.is_dexterous_radius(rho)
        coverage = robot.sampled_orientation_coverage(rho, 0.0, samples=360)
        sampled_full = isclose(coverage, FULL_COVERAGE)
        assert analytical == sampled_full, (
            f"mismatch at l2/l1={lambda2}, l3/l1={lambda3}, rho={rho}: "
            f"analytical={analytical}, coverage={coverage}"
        )
