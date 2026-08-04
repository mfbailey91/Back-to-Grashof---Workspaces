"""Visualization generation reproducibility tests."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.classification import SphericalFourBar
from sixr_grashof.visualization import (
    plot_architecture_a_worked_closure,
    plot_architecture_panel,
    plot_residual_sweeps,
    plot_sign_type_table,
    plot_spherical_fourbar,
    plot_type_fixture_gallery,
)


def test_sprint0_plots_write(tmp_path: Path) -> None:
    assert plot_architecture_a_worked_closure(output=tmp_path / "a.png") is not None
    assert plot_type_fixture_gallery(output=tmp_path / "gallery.png") is not None
    assert plot_sign_type_table(output=tmp_path / "table.png") is not None
    p = plot_spherical_fourbar(
        SphericalFourBar(1.0, 0.5, 1.2, 0.8),
        output=tmp_path / "type2.png",
    )
    assert p is not None
    assert p.is_file() and p.stat().st_size > 1000


def test_sprint1_comparison_plots_write(tmp_path: Path) -> None:
    assert plot_architecture_panel(output=tmp_path / "panel.png") is not None
    assert plot_residual_sweeps(output=tmp_path / "sweeps.png") is not None
    assert (tmp_path / "panel.png").stat().st_size > 1000
    assert (tmp_path / "sweeps.png").stat().st_size > 1000
