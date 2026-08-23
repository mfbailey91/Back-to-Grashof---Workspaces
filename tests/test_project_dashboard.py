"""Tests for the reproducible project HTML dashboard generator."""

from __future__ import annotations

from grashof_workspace.project_dashboard import (
    STATUS_DATE,
    build_project_dashboard,
    render_explorer_index_html,
    render_kinematic_decomposition_index_html,
    render_project_index_html,
)


def test_render_project_index_covers_capabilities_and_l3_l7() -> None:
    html = render_project_index_html()
    assert STATUS_DATE == "2026-08-23"
    assert "STITCHING_CONTROL_BLOCKED" in html
    assert "capabilities and status" in html.casefold() or "L3–L7" in html
    assert "R3A" in html
    assert "l5_reconstruction/r3a/index.html" in html
    assert "L3–L7" in html or "L3" in html
    assert "trusted_exact_reference" in html
    assert "parent_incomplete" in html
    assert "LOCAL_ONLY" in html
    assert "scaffold_only" in html or "SCAFFOLD" in html
    assert "BLOCKED" in html
    assert "L5" in html and "L6" in html and "L7" in html
    assert "REJECTED" in html
    assert "decomposition_ladder/index.html" in html
    assert "kinematic_decomposition/index.html" in html
    assert "spatial4bar_explorer/index.html" in html
    assert "SO(3)" in html
    assert "V06A" in html or "V07A" in html
    assert "CURRENT_STATUS.md" in html
    assert 'id="animations"' in html
    assert "v03_uuur_branch.gif" in html
    assert "v03_urrs_branch.gif" in html
    assert "v05b_exact_u_pair_4r_fiber.gif" in html
    assert "v05d_exact_u_pair_4r_overlay.gif" in html
    assert "mechanism_explorer_only" in html
    assert "reconstruction not accepted" in html.casefold()
    assert "implemented kernels" in html.casefold()
    assert "R3B" in html
    assert "held" in html.casefold()


def test_render_explorer_index_mentions_active_ladder() -> None:
    html = render_explorer_index_html()
    assert "V05E" in html
    assert "DecompositionCertificate" in html
    assert "near-aligned" in html.casefold() or "near_aligned" in html
    assert "V06" in html
    assert "mechanism_explorer_only" in html
    assert "LOCAL_ONLY" in html
    assert "R3A" in html or "L3–L7" in html
    assert "../index.html" in html
    assert "decomposition_ladder/index.html" in html


def test_render_kd_hub_mentions_certificate_and_next() -> None:
    html = render_kinematic_decomposition_index_html()
    assert "V05E" in html
    assert "DecompositionCertificate" in html or "axis_aggregation" in html
    assert "near_aligned" in html or "near-aligned" in html.casefold()
    assert "V06" in html
    assert "ADR-047" in html
    assert "V07A held" in html
    assert "mechanism_explorer_only" in html
    assert "LOCAL_ONLY" in html
    assert "../index.html" in html
    assert "decomposition_ladder/index.html" in html


def test_build_project_dashboard_writes_all_three(tmp_path) -> None:
    root_path, explorer_path, kd_path = build_project_dashboard(tmp_path)
    assert root_path.is_file()
    assert explorer_path.is_file()
    assert kd_path.is_file()
    assert root_path.name == "index.html"
    assert root_path.parent == tmp_path
    assert explorer_path.name == "index.html"
    assert kd_path.name == "index.html"
    root_html = root_path.read_text(encoding="utf-8")
    explorer_html = explorer_path.read_text(encoding="utf-8")
    kd_html = kd_path.read_text(encoding="utf-8")
    assert "V05E" in explorer_html and "V05E" in kd_html
    assert "mechanism_explorer_only" in explorer_html
    assert "V06" in kd_html
    assert "L3" in root_html and "L7" in root_html
    assert "LOCAL_ONLY" in root_html
