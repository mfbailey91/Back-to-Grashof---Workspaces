from pathlib import Path

from grashof_workspace.spatial4bar_explorer.axis_drive import (
    animate_axis_drive,
    drive_tool_axis,
    plot_axis_drive_coordinates,
)
from grashof_workspace.spatial4bar_explorer.geometry import canonical_geometry
from grashof_workspace.spatial4bar_explorer.models import OrderedFamily, ToolAxis


def test_prescribed_tool_a_and_b_coordinates_satisfy_closure() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    for tool_axis, coordinate_index in ((ToolAxis.A, 0), (ToolAxis.B, 1)):
        trace = drive_tool_axis(
            geometry,
            tool_axis,
            requested_angle=0.12,
            target_step=0.04,
        )
        assert len(trace.converged_points) >= 2
        for point in trace.converged_points:
            assert abs(point.q[coordinate_index] - point.target_angle) < 1e-10
            assert point.closure_norm < 1e-7


def test_all_families_have_explicit_a_and_b_drive_attempts() -> None:
    for family in OrderedFamily:
        geometry = canonical_geometry(family)
        trace_a = drive_tool_axis(
            geometry,
            ToolAxis.A,
            requested_angle=0.08,
            target_step=0.04,
        )
        trace_b = drive_tool_axis(
            geometry,
            ToolAxis.B,
            requested_angle=0.08,
            target_step=0.04,
        )
        assert trace_a.tool_axis == "a"
        assert trace_b.tool_axis == "b"
        assert trace_a.coordinate_name == "tool_alpha"
        assert trace_b.coordinate_name == "tool_beta"


def test_a_and_b_axis_drive_visuals_are_generated(tmp_path: Path) -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    trace_a = drive_tool_axis(
        geometry,
        ToolAxis.A,
        requested_angle=0.08,
        target_step=0.04,
    )
    trace_b = drive_tool_axis(
        geometry,
        ToolAxis.B,
        requested_angle=0.08,
        target_step=0.04,
    )
    paths = [
        plot_axis_drive_coordinates(trace_a, tmp_path / "a.png"),
        plot_axis_drive_coordinates(trace_b, tmp_path / "b.png"),
        animate_axis_drive(geometry, trace_a, tmp_path / "a.gif", fps=4, dpi=55),
        animate_axis_drive(geometry, trace_b, tmp_path / "b.gif", fps=4, dpi=55),
    ]
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)


def test_all_six_families_emit_twelve_a_b_drive_artifacts(tmp_path: Path) -> None:
    for family in OrderedFamily:
        geometry = canonical_geometry(family)
        for tool_axis in (ToolAxis.A, ToolAxis.B):
            trace = drive_tool_axis(
                geometry,
                tool_axis,
                requested_angle=0.08,
                target_step=0.04,
            )
            stem = f"{family.value.lower()}_tool_{tool_axis.value}_drive"
            plot_axis_drive_coordinates(trace, tmp_path / f"{stem}.png")
            animate_axis_drive(
                geometry,
                trace,
                tmp_path / f"{stem}.gif",
                fps=4,
                dpi=45,
            )
    assert len(list(tmp_path.glob("*_tool_*_drive.png"))) == 12
    assert len(list(tmp_path.glob("*_tool_*_drive.gif"))) == 12


def test_phi_is_labeled_diagnostic_only_in_repo_contract() -> None:
    v04b_doc = Path("docs/SPRINT_V04B_VIRTUAL_U_ROBUSTNESS.md").read_text(encoding="utf-8")
    audit = Path("docs/AUDIT_TOOL_AXIS_AND_PHI.md").read_text(encoding="utf-8")
    v04b_source = Path(
        "src/grashof_workspace/spatial4bar_explorer/v04b.py"
    ).read_text(encoding="utf-8")
    result_html = Path(
        "results/spatial4bar_explorer/v04b/sprint_04b_virtual_u_robustness.html"
    ).read_text(encoding="utf-8")
    result_json = Path(
        "results/spatial4bar_explorer/v04b/data/v04b_virtual_u_robustness.json"
    ).read_text(encoding="utf-8")
    assert "DIAGNOSTIC ONLY" in v04b_doc
    assert "diagnostic_sensitivity_only" in audit
    assert "DIAGNOSTIC ONLY" in v04b_source
    assert "DIAGNOSTIC ONLY" in result_html
    assert '"experiment_role": "diagnostic_sensitivity_only"' in result_json
