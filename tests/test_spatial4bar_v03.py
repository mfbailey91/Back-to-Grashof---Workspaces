from pathlib import Path

from grashof_workspace.spatial4bar_explorer.closure import audit_reference_geometry, scalar_axes
from grashof_workspace.spatial4bar_explorer.continuation import continue_branch
from grashof_workspace.spatial4bar_explorer.continuation_plots import (
    animate_branch,
    plot_branch_snapshots,
    plot_closure_residual,
    plot_continuation_coordinates,
    plot_reference_mobility_audit,
    plot_singularity_margin,
    plot_tool_coordinate_phase,
)
from grashof_workspace.spatial4bar_explorer.continuation_readouts import write_sprint03_html
from grashof_workspace.spatial4bar_explorer.geometry import canonical_geometry
from grashof_workspace.spatial4bar_explorer.models import OrderedFamily


def test_v03_all_families_expand_to_seven_coordinates() -> None:
    for family in OrderedFamily:
        axes = scalar_axes(canonical_geometry(family))
        assert len(axes) == 7
        assert axes[0].name == "tool_alpha"
        assert axes[1].name == "tool_beta"


def test_v03_reference_closure_rank_and_nullity() -> None:
    for family in OrderedFamily:
        audit = audit_reference_geometry(canonical_geometry(family))
        assert audit.status == "PASS"
        assert audit.closure_norm < 1e-9
        assert audit.coordinate_count == 7
        assert audit.jacobian_rank == 6
        assert audit.jacobian_nullity == 1
        assert audit.smallest_nonzero_singular_value > 1e-4


def test_v03_uuur_continuation_is_nontrivial_and_closed_numerically() -> None:
    trace = continue_branch(canonical_geometry(OrderedFamily.UUUR), steps=18, step_size=0.03)
    assert len(trace.points) == 19
    assert trace.converged_fraction == 1.0
    assert max(point.closure_norm for point in trace.points) < 1e-8
    assert max(abs(value) for value in trace.points[-1].q) > 0.1
    assert min(point.smallest_singular_value for point in trace.points) > 1e-4


def test_v03_one_kernel_continues_all_six_families() -> None:
    for family in OrderedFamily:
        trace = continue_branch(canonical_geometry(family), steps=8, step_size=0.025)
        assert len(trace.points) == 9
        assert trace.converged_fraction == 1.0
        assert max(point.closure_norm for point in trace.points) < 1e-7


def test_v03_visuals_and_html_are_generated(tmp_path: Path) -> None:
    audits = [audit_reference_geometry(canonical_geometry(family)) for family in OrderedFamily]
    traces = [continue_branch(canonical_geometry(family), steps=5, step_size=0.02) for family in OrderedFamily]
    detailed = next(trace for trace in traces if trace.family == "UUUR")
    geometry = canonical_geometry(OrderedFamily.UUUR)

    mobility = tmp_path / "mobility.png"
    coordinates = tmp_path / "coordinates.png"
    residual = tmp_path / "residual.png"
    singularity = tmp_path / "singularity.png"
    phase = tmp_path / "phase.png"
    plot_reference_mobility_audit(audits, mobility)
    plot_continuation_coordinates(detailed, coordinates)
    plot_closure_residual(detailed, residual)
    plot_singularity_margin(detailed, singularity)
    plot_tool_coordinate_phase(detailed, phase)
    snapshots = plot_branch_snapshots(geometry, detailed, tmp_path / "snapshots", count=3)
    animation_paths: list[tuple[str, str]] = []
    for family, trace in zip(OrderedFamily, traces, strict=True):
        path = animate_branch(
            canonical_geometry(family),
            trace,
            tmp_path / f"{family.value.lower()}_branch.gif",
            stride=1,
            fps=8,
            dpi=70,
        )
        assert path.exists()
        assert path.stat().st_size > 0
        animation_paths.append((family.value, path.name))
    for path in (mobility, coordinates, residual, singularity, phase, *snapshots):
        assert path.exists()
        assert path.stat().st_size > 0

    write_sprint03_html(
        tmp_path,
        audits=audits,
        traces=traces,
        detailed_family="UUUR",
        mobility_plot=mobility.name,
        coordinate_plot=coordinates.name,
        residual_plot=residual.name,
        singularity_plot=singularity.name,
        phase_plot=phase.name,
        animation_paths=animation_paths,
        snapshot_paths=[str(path.relative_to(tmp_path)) for path in snapshots],
        audit_json="data/audit.json",
        trace_json="data/traces.json",
        axis_drive_cards=[],
        axis_drive_json="data/axis_drive.json",
    )
    html = (tmp_path / "sprint_03_closure_and_continuation.html").read_text(encoding="utf-8")
    assert "V03A" in html
    assert "V03B" in html
    assert "V03C" in html
    assert "No crank, winding, or dexterity classification" in html
    assert "S-joint x/y/z" in html
    assert "Canonical local branch animation" in html
    assert "Canonical local branch animations (all families)" in html
    assert "Prescribed tool-A and tool-B drive diagnostics" in html
    assert "not driven by" in html
    assert "validated dexterity-derived pointing fiber" in html
    assert "local branch motion only" in html
    assert "tool_a" in html
    assert "tool_b" in html
    for family, path_name in animation_paths:
        assert path_name in html
        assert family in html


def test_branch_frame_title_reports_tool_a_and_tool_b() -> None:
    from grashof_workspace.spatial4bar_explorer.continuation_plots import _branch_frame_title

    title = _branch_frame_title(
        "UUUR",
        0.4,
        (0.12, -0.34, 0.0, 0.0, 0.0, 0.0, 0.0),
        ("tool_alpha", "tool_beta", "j2_u1", "j2_u2", "j3_u1", "j3_u2", "j4_r1"),
    )
    assert "canonical local branch" in title
    assert "param=s (not driven)" in title
    assert "tool_a=+0.12 rad" in title
    assert "tool_b=-0.34 rad" in title
