"""Tests for the reproducible project HTML dashboard generator."""

from __future__ import annotations

from grashof_workspace.project_dashboard import (
    build_project_dashboard,
    render_explorer_index_html,
    render_kinematic_decomposition_index_html,
)


def test_render_explorer_index_mentions_active_ladder() -> None:
    html = render_explorer_index_html()
    assert "V05E" in html
    assert "DecompositionCertificate" in html
    assert "near-aligned" in html.casefold() or "near_aligned" in html
    assert "V06" in html
    assert "mechanism_explorer_only" in html
    assert "V05B–E audit-corrected MVP" in html or "Active V05B" in html or "audit-corrected MVP" in html
    assert (
        "CLOSED_ON_COMPONENT" in html
        or "V05 gate CLOSED" in html
        or "exact_u_pair_4r" in html
    )


def test_render_kd_hub_mentions_certificate_and_next() -> None:
    html = render_kinematic_decomposition_index_html()
    assert "V05E" in html
    assert "DecompositionCertificate" in html or "axis_aggregation" in html
    assert "near_aligned" in html or "near-aligned" in html.casefold()
    assert "V06" in html
    assert "mechanism_explorer_only" in html


def test_build_project_dashboard_writes_both(tmp_path) -> None:
    explorer_path, kd_path = build_project_dashboard(tmp_path)
    assert explorer_path.is_file()
    assert kd_path.is_file()
    assert explorer_path.name == "index.html"
    assert kd_path.name == "index.html"
    explorer_html = explorer_path.read_text(encoding="utf-8")
    kd_html = kd_path.read_text(encoding="utf-8")
    assert "V05E" in explorer_html and "V05E" in kd_html
    assert "mechanism_explorer_only" in explorer_html
    assert "V06" in kd_html
