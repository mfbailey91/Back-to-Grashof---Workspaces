"""Tests for planar workspace exemplar visualization."""

from __future__ import annotations

from math import pi

from grashof_workspace.fourbar import FourBar
from grashof_workspace.fourbar_poses import (
    angle_span,
    pose_at_input_angle,
    sample_admissible_input_angles,
    sample_poses,
)
from grashof_workspace.planar3r import Planar3R
from grashof_workspace.workspace_exemplars import (
    build_exemplar_case,
    render_workspace_exemplars,
    select_workspace_exemplars,
)


def test_select_workspace_exemplars_inside_outside_boundary() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    exemplars = select_workspace_exemplars(arm, include_boundary=True)
    by_name = {item.name: item for item in exemplars}
    assert set(by_name) == {"inside", "outside", "boundary"}
    assert by_name["inside"].classification == "dexterous"
    assert by_name["outside"].classification == "reachable_nondexterous"
    assert by_name["boundary"].classification == "boundary"
    assert arm.is_dexterous_radius(by_name["inside"].radial_value or 0.0)
    assert not arm.is_dexterous_radius(by_name["outside"].radial_value or 0.0)
    assert arm.is_reachable_radius(by_name["outside"].radial_value or 0.0)


def test_select_without_boundary() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    exemplars = select_workspace_exemplars(arm, include_boundary=False)
    assert [item.name for item in exemplars] == ["inside", "outside"]


def test_pose_sampler_full_revolution_and_rocker() -> None:
    crank = FourBar(ground=1.5, input=1.0, coupler=2.0, output=2.0)
    assert crank.input_can_fully_rotate()
    angles = sample_admissible_input_angles(crank, 48)
    assert angle_span(angles) > 2.0 * pi - 0.5
    assert pose_at_input_angle(crank, 0.0) is not None
    assert len(sample_poses(crank, 24)) >= 20

    rocker = FourBar(ground=4.0, input=1.0, coupler=2.0, output=2.0)
    assert rocker.is_assemblable()
    assert not rocker.input_can_fully_rotate()
    rocker_angles = sample_admissible_input_angles(rocker, 36)
    assert rocker_angles
    assert angle_span(rocker_angles) < pi


def test_non_assemblable_has_no_poses() -> None:
    bad = FourBar(ground=6.0, input=1.0, coupler=2.0, output=2.0)
    assert not bad.is_assemblable()
    assert sample_admissible_input_angles(bad, 12) == ()
    assert sample_poses(bad, 12) == ()


def test_build_exemplar_preserves_classification_predicates() -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    inside = select_workspace_exemplars(arm, include_boundary=False)[0]
    case = build_exemplar_case(arm, inside, samples=24)
    assert case.state.dexterous == arm.is_dexterous_radius(inside.radial_value or 0.0)
    assert case.orientation_coverage_type == "full"
    assert case.poses
    outside = select_workspace_exemplars(arm, include_boundary=False)[1]
    outside_case = build_exemplar_case(arm, outside, samples=24)
    assert outside_case.orientation_coverage_type == "partial"
    assert angle_span(outside_case.orientation_samples) < angle_span(
        case.orientation_samples
    )


def test_render_workspace_exemplars_writes_artifacts(tmp_path) -> None:
    arm = Planar3R(2.0, 2.0, 1.0)
    paths = render_workspace_exemplars(
        arm,
        tmp_path,
        include_boundary=True,
        samples=16,
        animate=True,
    )
    for name in ("inside", "outside", "boundary"):
        assert paths[f"{name}_static"].is_file()
        assert paths[f"{name}_animation"].is_file()
    assert paths["comparison"].is_file()
    assert paths["json"].is_file()
    text = paths["json"].read_text(encoding="utf-8")
    assert "workspace_exemplars" in text
    assert "dexterous" in text
