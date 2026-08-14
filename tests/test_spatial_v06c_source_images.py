"""V06C: source orientation/pointing images are not V05 curves or S^2 coverage."""

from __future__ import annotations

import inspect
import json

from grashof_workspace.decomposition_ladder.models import CertificateStatus, ProcessStatus
from grashof_workspace.decomposition_ladder.spatial_l5 import build_spatial_l5_scaffold_bundle
from grashof_workspace.spatial_experiments.fixed_position import POSITION_RESIDUAL_TOL_M
from grashof_workspace.spatial_experiments.parent_atlas import build_generic_5r_parent_atlas
from grashof_workspace.spatial_experiments.parent_task_images import (
    CoverageLabel,
    build_source_task_images,
)
from grashof_workspace.spatial_experiments.v06_corpus import build_generic_5r
from grashof_workspace.spatial_experiments.v06c import build_v06c_readout


def test_builder_takes_atlas_and_model_only() -> None:
    params = inspect.signature(build_source_task_images).parameters
    assert "atlas" in params
    assert "model" in params
    assert "child" not in params
    assert "aggregation" not in params


def test_source_images_are_partial_and_not_v05_curves() -> None:
    entry = build_generic_5r()
    atlas = build_generic_5r_parent_atlas(
        entry, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    bundle = build_source_task_images(atlas, entry.model)
    payload = bundle.to_json_dict()
    text = json.dumps(payload, allow_nan=False)
    assert "curve_type" not in payload["orientation"]
    assert "PURE_TERMINAL_ROLL" not in text
    assert payload["certificate_status"] is None
    assert bundle.pointing.coverage_label is not CoverageLabel.COVERED_AT_DECLARED_RESOLUTION
    uncovered = sum(1 for c in bundle.pointing.sphere_grid.cells if c.kind.value == "UNCOVERED")
    assert uncovered > 0
    assert bundle.orientation.vertices
    for vertex in bundle.orientation.vertices:
        d = next(
            v.pointing
            for v in atlas.vertices
            if v.accepted and v.q == vertex.q
        )
        nrm = sum(x * x for x in d) ** 0.5
        assert abs(nrm - 1.0) < 1e-9
        assert vertex.rank_jp == 3
        assert vertex.rank_jd_np in (1, 2)
    accepted = [v for v in atlas.vertices if v.accepted]
    assert all(
        v.p_residual_m is not None and v.p_residual_m <= POSITION_RESIDUAL_TOL_M for v in accepted
    )


def test_l5_keeps_reconstruction_unresolved() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.parent.process_status is ProcessStatus.SCAFFOLD
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.reconstruction.certificate_status is CertificateStatus.UNRESOLVED
    assert bundle.parent_images is not None
    assert bundle.parent_images["coverage_label"] != "COVERED_AT_DECLARED_RESOLUTION"
    assert bundle.parent_images["certificate_status"] is None


def test_v06c_readout(tmp_path) -> None:
    html = build_v06c_readout(
        tmp_path, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    body = html.read_text(encoding="utf-8")
    assert "ADR-038" in body
    assert "DecompositionCertificate" in body
    payload = json.loads((tmp_path / "data" / "v06c_generic_5r_source_images.json").read_text())
    assert payload["atlas"]["fiber_ids"] == []
    assert payload["images"]["certificate_status"] is None
    assert payload["images"]["pointing"]["coverage_label"] != "COVERED_AT_DECLARED_RESOLUTION"
    assert "curve_type" not in payload["images"]["orientation"]
    json.dumps(payload, allow_nan=False)
    assert (tmp_path / "figures" / "v06c_generic_5r_source_images.png").is_file()
