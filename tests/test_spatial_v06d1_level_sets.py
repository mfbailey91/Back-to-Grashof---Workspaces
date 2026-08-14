"""V06D1: task-derived source level sets are not U_v or reconstruction."""

from __future__ import annotations

import json

from grashof_workspace.decomposition_ladder.models import CertificateStatus
from grashof_workspace.decomposition_ladder.spatial_l5 import (
    build_spatial_l5_scaffold_bundle,
    default_l5_scaffold_payload,
)
from grashof_workspace.spatial_experiments.parent_atlas import build_generic_5r_parent_atlas
from grashof_workspace.spatial_experiments.parent_level_sets import (
    EPS_H,
    build_parent_level_sets,
    levelset_jacobian,
    levelset_residual,
)
from grashof_workspace.spatial_experiments.v06_corpus import build_generic_5r
from grashof_workspace.spatial_experiments.v06d1 import build_v06d1_readout


def test_level_sets_regular_slices_and_continuation() -> None:
    entry = build_generic_5r()
    atlas = build_generic_5r_parent_atlas(
        entry, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    result = build_parent_level_sets(atlas, entry.model)
    assert any(v.regular for v in result.vertices)
    assert result.eps_h == EPS_H
    assert len(result.slice_values) == 3
    regular_h = [v.h for v in result.vertices if v.regular]
    lo, hi = min(regular_h), max(regular_h)
    for c in result.slice_values:
        assert lo < c < hi
    assert result.complete_foliation is False
    assert any(sl.contours for sl in result.slices)
    assert result.fibers
    fiber = next(f for f in result.fibers if f.samples)
    seed = min(fiber.samples, key=lambda s: abs(s.sigma))
    res = levelset_residual(entry.model, seed.q, atlas.p_star, result.n, fiber.c)
    assert float(sum(float(x) ** 2 for x in res)) ** 0.5 < 1e-8
    jac = levelset_jacobian(entry.model, seed.q, result.n)
    assert jac.shape == (4, 5)
    assert seed.rank_jfc == 4
    assert seed.nullity_jfc == 1
    assert fiber.provenance == "task-derived"
    json.dumps(result.to_json_dict(), allow_nan=False)
    assert "curve_type" not in json.dumps(result.to_json_dict())
    assert "UUUR" not in json.dumps(result.to_json_dict())
    for fiber in result.fibers:
        assert fiber.provenance == "task-derived"
        dumped = fiber.to_json_dict()
        assert "joint_role_sequence" not in dumped
        assert "U_v" not in fiber.fiber_id


def test_l5_reconstruction_stays_empty() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.reconstruction.certificate_status is CertificateStatus.UNRESOLVED
    assert bundle.fiber_placeholder.source_provenance == "task-derived"
    assert bundle.fiber_placeholder.sample_count > 0
    assert "U_v" not in bundle.fiber_placeholder.fiber_id
    for child in bundle.children:
        if child.family != "UUUR":
            assert child.status is CertificateStatus.UNRESOLVED
        else:
            assert child.status not in {
                CertificateStatus.EXACT_GLOBAL,
                CertificateStatus.EXACT_ON_COMPONENT,
            }
    payload = default_l5_scaffold_payload()
    assert payload["summary"]["accepted_fiber_count"] == 0
    assert "not a 2d parent" in payload["note"].casefold()
    assert payload["summary"]["complete_foliation"] is False


def test_v06d1_readout(tmp_path) -> None:
    html = build_v06d1_readout(
        tmp_path, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    body = html.read_text(encoding="utf-8")
    assert "ADR-040" in body
    assert "U_v" in body
    payload = json.loads((tmp_path / "data" / "v06d1_generic_5r_level_sets.json").read_text())
    json.dumps(payload, allow_nan=False)
    assert payload["atlas"]["certificate_status"] is None
    assert payload["level_sets"]["complete_foliation"] is False
    assert payload["level_sets"]["fibers"]
    assert payload["level_sets"]["fibers"][0]["provenance"] == "task-derived"
    assert "curve_type" not in json.dumps(payload)
    assert (tmp_path / "figures" / "v06d1_generic_5r_level_sets.png").is_file()
