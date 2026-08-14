"""V06A2: generic_5r parent atlas is not a complete parent or certificate."""

from __future__ import annotations

import json

from grashof_workspace.decomposition_ladder.models import CertificateStatus, ProcessStatus
from grashof_workspace.decomposition_ladder.spatial_l5 import build_spatial_l5_scaffold_bundle
from grashof_workspace.spatial_experiments.fixed_position import POSITION_RESIDUAL_TOL_M
from grashof_workspace.spatial_experiments.parent_atlas import (
    ParentRepresentationStatus,
    build_generic_5r_parent_atlas,
)
from grashof_workspace.spatial_experiments.v06a2 import build_v06a2_readout

_OPEN_STATUSES = {
    ParentRepresentationStatus.ATLAS_OPEN_FRONTIER,
    ParentRepresentationStatus.BUDGET_LIMITED,
    ParentRepresentationStatus.SINGULAR_BOUNDARY,
    ParentRepresentationStatus.MULTICOMPONENT_UNRESOLVED,
    ParentRepresentationStatus.LOCAL_PATCH,
}


def test_parent_atlas_grows_charts_without_claiming_closure() -> None:
    result = build_generic_5r_parent_atlas(max_charts=6, discovery_bank=16, confirmation_bank=16)
    assert result.representation_status in _OPEN_STATUSES
    assert result.representation_status is not ParentRepresentationStatus.CLOSED_COMPONENT_AT_DECLARED_RESOLUTION
    assert len(result.charts) >= 2
    assert result.fiber_ids == ()
    accepted = [v for v in result.vertices if v.accepted]
    assert accepted
    for vertex in accepted:
        assert vertex.p_residual_m is not None
        assert vertex.p_residual_m <= POSITION_RESIDUAL_TOL_M
        assert vertex.np_shape == (5, 2)
        assert vertex.rank_jp == 3
        assert vertex.nullity_jp == 2
    payload = result.to_json_dict()
    assert payload["certificate_status"] is None
    json.dumps(payload, allow_nan=False)
    assert result.discovery.bank_size == 16
    assert result.joint_limits == "not_modeled"


def test_l5_bundle_exposes_atlas_without_fibers() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.parent.process_status is ProcessStatus.SCAFFOLD
    notes = " ".join(bundle.parent.notes)
    assert "ADR-037" in notes
    assert "UNRESOLVED" in notes
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.fiber_placeholder.source_provenance in {"task-derived", "scaffold_only"}
    assert bundle.parent_atlas is not None
    for child, cert in zip(bundle.children, bundle.certificates, strict=True):
        assert not cert.accepted_for_reconstruction
        if child.family != "UUUR":
            assert child.status is CertificateStatus.UNRESOLVED
            assert cert.closed_mechanism_status is CertificateStatus.UNRESOLVED
    assert bundle.parent_atlas is not None
    assert bundle.parent_atlas["fiber_ids"] == []
    assert bundle.parent_atlas["representation_status"] != "CLOSED_COMPONENT_AT_DECLARED_RESOLUTION"


def test_v06a2_readout(tmp_path) -> None:
    html = build_v06a2_readout(tmp_path, max_charts=6, discovery_bank=16, confirmation_bank=16)
    body = html.read_text(encoding="utf-8")
    assert "ADR-037" in body
    assert "DecompositionCertificate" in body
    payload = json.loads((tmp_path / "data" / "v06a2_generic_5r_parent_atlas.json").read_text())
    assert payload["fiber_ids"] == []
    assert payload["certificate_status"] is None
    assert payload["representation_status"] != "CLOSED_COMPONENT_AT_DECLARED_RESOLUTION"
    assert (tmp_path / "figures" / "v06a2_generic_5r_parent_atlas.png").is_file()
