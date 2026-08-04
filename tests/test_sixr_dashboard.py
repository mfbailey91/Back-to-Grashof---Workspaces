"""Tests for Sprint 0–6 static HTML dashboards."""

from __future__ import annotations

import json
from pathlib import Path

from sixr_grashof.dashboard import (
    generate_dashboards,
    write_sprint0_dashboard,
    write_sprint1_dashboard,
    write_sprint2_dashboard,
    write_sprint3_dashboard,
    write_sprint4_dashboard,
    write_sprint5_dashboard,
    write_sprint6_dashboard,
)


def test_dashboards_write_from_existing_figures(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1] / "results"
    fig0 = root / "sprint00_classification"
    fig1 = root / "sprint01_geometry"
    fig2 = root / "sprint02_reduction"
    fig3 = root / "sprint03_prediction"
    fig4 = root / "sprint04_orientation"
    fig5 = root / "sprint05_experiments"
    assert fig0.is_dir() and fig1.is_dir()
    assert fig2.is_dir() and fig3.is_dir()
    assert fig4.is_dir() and fig5.is_dir()
    assert (fig5 / "experiment_summary.json").is_file()

    out = tmp_path / "results"
    paths = generate_dashboards(
        results_root=out,
        figures0=fig0,
        figures1=fig1,
        figures2=fig2,
        figures3=fig3,
        figures4=fig4,
        figures5=fig5,
    )
    assert paths["sprint0"].is_file()
    assert paths["sprint1"].is_file()
    assert paths["sprint2"].is_file()
    assert paths["sprint3"].is_file()
    assert paths["sprint4"].is_file()
    assert paths["sprint5"].is_file()
    assert paths["sprint6"].is_file()
    assert paths["overview"].is_file()

    html4 = paths["sprint4"].read_text(encoding="utf-8")
    assert "Sprint 4" in html4
    assert "orientation_sample_cloud.png" in html4
    assert "solver_failed" in html4 or "Gate 2" in html4

    html5 = paths["sprint5"].read_text(encoding="utf-8")
    assert "Sprint 5" in html5
    assert "confusion_heatmap.png" in html5
    assert "dexterity" in html5.lower() or "hypothesis" in html5.lower()

    html6 = paths["sprint6"].read_text(encoding="utf-8")
    assert "Sprint 6" in html6
    assert 'id="dashboard-data"' in html6
    assert 'id="state-picker"' in html6
    assert 'id="eps-w-slider"' in html6
    assert 'id="eps-s-slider"' in html6
    assert "prediction_outcome" in html6
    assert "concurrency_residual" in html6

    payload = json.loads((out / "sprint06_dashboard" / "dashboard.json").read_text(encoding="utf-8"))
    assert payload["sprint"] == 6
    assert len(payload["records"]) >= 1
    assert "record_id" in payload["records"][0]
    assert "arm_figure" in payload["records"][0]
    assert (out / "sprint06_dashboard" / "figures" / "residual_vs_error.png").is_file()
    assert (out / "sprint06_dashboard" / "figures" / "orientation_sample_cloud.png").is_file()

    js = (out / "sprint06_dashboard" / "assets" / "dashboard.js").read_text(encoding="utf-8")
    assert "renderSprint6" in js
    assert "eps-w-slider" in js

    overview = paths["overview"].read_text(encoding="utf-8")
    assert "sprint04_dashboard" in overview
    assert "sprint05_dashboard" in overview
    assert "sprint06_dashboard" in overview


def test_individual_writers(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1] / "results"
    i0 = write_sprint0_dashboard(tmp_path / "s0", figures_src=root / "sprint00_classification")
    i1 = write_sprint1_dashboard(tmp_path / "s1", figures_src=root / "sprint01_geometry")
    i2 = write_sprint2_dashboard(tmp_path / "s2", figures_src=root / "sprint02_reduction")
    i3 = write_sprint3_dashboard(tmp_path / "s3", figures_src=root / "sprint03_prediction")
    i4 = write_sprint4_dashboard(tmp_path / "s4", figures_src=root / "sprint04_orientation")
    i5 = write_sprint5_dashboard(tmp_path / "s5", figures_src=root / "sprint05_experiments")
    i6 = write_sprint6_dashboard(
        tmp_path / "s6",
        experiments_src=root / "sprint05_experiments",
        geometry_src=root / "sprint01_geometry",
        reduction_src=root / "sprint02_reduction",
        orientation_src=root / "sprint04_orientation",
    )
    assert all(p.is_file() for p in (i0, i1, i2, i3, i4, i5, i6))
