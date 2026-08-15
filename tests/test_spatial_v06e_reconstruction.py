"""V06E: source-fiber reconstruction is partial; accepted children stay empty."""

from __future__ import annotations

import json

from grashof_workspace.decomposition_ladder.models import CertificateStatus
from grashof_workspace.decomposition_ladder.spatial_l5 import (
    build_spatial_l5_scaffold_bundle,
    default_l5_scaffold_payload,
)
from grashof_workspace.spatial_experiments.parent_atlas import build_generic_5r_parent_atlas
from grashof_workspace.spatial_experiments.parent_level_sets import build_parent_level_sets
from grashof_workspace.spatial_experiments.parent_reconstruction import (
    FACTORIZATION_ALLOWED,
    build_parent_reconstruction,
)
from grashof_workspace.spatial_experiments.parent_task_images import (
    DEFAULT_ICOSPHERE_LEVEL,
    CoverageLabel,
    build_source_task_images,
)
from grashof_workspace.spatial_experiments.v06_corpus import build_generic_5r
from grashof_workspace.spatial_experiments.v06e import build_v06e_readout


def test_source_fiber_paint_is_partial_and_child_empty() -> None:
    entry = build_generic_5r()
    atlas = build_generic_5r_parent_atlas(
        entry, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    images = build_source_task_images(atlas, entry.model)
    level_sets = build_parent_level_sets(atlas, entry.model)
    result = build_parent_reconstruction(atlas, entry.model, images, level_sets)
    assert result.icosphere_level == DEFAULT_ICOSPHERE_LEVEL
    assert result.icosphere_level == images.pointing.sphere_grid.subdivision_level
    assert result.metrics.fiber_hit_cells >= 1
    assert result.metrics.direct_covered == 0
    assert result.metrics.coverage_comparison_evaluable is False
    assert result.metrics.missed_covered_fraction is None
    assert result.complete_foliation is False
    assert result.coverage_label != CoverageLabel.COVERED_AT_DECLARED_RESOLUTION.value
    assert result.metrics.accepted_child_count == 0
    assert result.metrics.child_hit_cells == 0
    assert result.factorization_status == "unresolved"
    assert result.reconstruction_coverage == "UNRESOLVED"
    assert result.factorization_status in FACTORIZATION_ALLOWED
    assert result.factorization_status != "exact product"
    assert "fiber bundle" not in result.factorization_status
    assert result.v06_program_passed is False
    assert result.v06_gate["source_fiber_cell_paint_generated"] is True
    assert result.v06_gate["source_fiber_reconstruction_compared"] is False
    blob = json.dumps(result.to_json_dict(), allow_nan=False)
    assert "curve_type" not in blob
    assert result.to_json_dict()["certificate_status"] is None
    assert result.to_json_dict()["metrics"]["missed_cell_fraction"] is None


def test_l5_reconstruction_cert_unresolved() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.reconstruction.certificate_status is CertificateStatus.UNRESOLVED
    assert bundle.parent_reconstruction["factorization_status"] == "unresolved"
    assert bundle.parent_reconstruction["reconstruction_coverage"] == "UNRESOLVED"
    payload = default_l5_scaffold_payload()
    assert payload["summary"]["accepted_fiber_count"] == 0
    assert "not a 2d parent" in payload["note"].casefold()
    assert payload["summary"]["v06_program_passed"] is False


def test_v06e_readout(tmp_path) -> None:
    html = build_v06e_readout(
        tmp_path, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    body = html.read_text(encoding="utf-8")
    assert "unevaluable" in body.casefold()
    assert "ADR-043" in body or "ADR-042" in body
    payload = json.loads((tmp_path / "data" / "v06e_reconstruction.json").read_text())
    json.dumps(payload, allow_nan=False)
    rec = payload["reconstruction"]
    assert rec["complete_foliation"] is False
    assert rec["metrics"]["accepted_child_count"] == 0
    assert rec["metrics"]["missed_cell_fraction"] is None
    assert rec["factorization_status"] == "unresolved"
    assert rec["reconstruction_coverage"] == "UNRESOLVED"
    assert (tmp_path / "figures" / "v06e_reconstruction_comparison.png").is_file()
