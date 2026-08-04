"""Tests for Sprint 0–3 static HTML dashboards."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.dashboard import (
    generate_dashboards,
    write_sprint0_dashboard,
    write_sprint1_dashboard,
    write_sprint2_dashboard,
    write_sprint3_dashboard,
)


def test_dashboards_write_from_existing_figures(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1] / "results"
    fig0 = root / "sprint00_classification"
    fig1 = root / "sprint01_geometry"
    fig2 = root / "sprint02_reduction"
    fig3 = root / "sprint03_prediction"
    assert fig0.is_dir() and fig1.is_dir()
    assert fig2.is_dir() and fig3.is_dir()

    out = tmp_path / "results"
    paths = generate_dashboards(
        results_root=out,
        figures0=fig0,
        figures1=fig1,
        figures2=fig2,
        figures3=fig3,
    )
    assert paths["sprint0"].is_file()
    assert paths["sprint1"].is_file()
    assert paths["sprint2"].is_file()
    assert paths["sprint3"].is_file()
    assert paths["overview"].is_file()

    html0 = paths["sprint0"].read_text(encoding="utf-8")
    assert "Sprint 0" in html0
    assert "dashboard-data" in html0
    assert "arch_a_worked_spherical_closure.png" in html0
    assert (paths["sprint0"].parent / "assets" / "dashboard.css").is_file()
    assert (paths["sprint0"].parent / "figures" / "mccarthy_soh_T_gallery.png").is_file()
    assert (paths["sprint0"].parent / "dashboard.json").is_file()

    html1 = paths["sprint1"].read_text(encoding="utf-8")
    assert "Sprint 1" in html1
    assert "architecture_panel.png" in html1
    assert (paths["sprint1"].parent / "figures" / "residual_sweeps.png").is_file()

    html2 = paths["sprint2"].read_text(encoding="utf-8")
    assert "Sprint 2" in html2
    assert "regional_planar_reduction.png" in html2
    assert "reductions" in html2
    assert (paths["sprint2"].parent / "figures" / "exact_A_vs_offset_B.png").is_file()

    html3 = paths["sprint3"].read_text(encoding="utf-8")
    assert "Sprint 3" in html3
    assert "hand-link-toggle" in html3
    assert "product" in html3.lower() and ("dexterity" in html3.lower() or "hypothesis" in html3.lower())
    assert (paths["sprint3"].parent / "figures" / "linkage_type_map.png").is_file()

    overview = paths["overview"].read_text(encoding="utf-8")
    assert "sprint02_dashboard" in overview
    assert "sprint03_dashboard" in overview

    # Product ≠ dexterity must remain visible in Sprint 0 copy.
    assert "not dexterity" in html0.lower() or "≠" in html0 or "not dexterity" in html0


def test_individual_writers(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1] / "results"
    i0 = write_sprint0_dashboard(tmp_path / "s0", figures_src=root / "sprint00_classification")
    i1 = write_sprint1_dashboard(tmp_path / "s1", figures_src=root / "sprint01_geometry")
    i2 = write_sprint2_dashboard(tmp_path / "s2", figures_src=root / "sprint02_reduction")
    i3 = write_sprint3_dashboard(tmp_path / "s3", figures_src=root / "sprint03_prediction")
    assert i0.is_file() and i1.is_file() and i2.is_file() and i3.is_file()
