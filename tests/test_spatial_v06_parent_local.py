"""V06A1: one local generic_5r parent chart is LOCAL_PATCH, not a complete parent."""

from __future__ import annotations

import json

import numpy as np

from grashof_workspace.decomposition_ladder.models import CertificateStatus, ProcessStatus
from grashof_workspace.decomposition_ladder.spatial_l5 import build_spatial_l5_scaffold_bundle
from grashof_workspace.spatial_experiments.fixed_position import POSITION_RESIDUAL_TOL_M
from grashof_workspace.spatial_experiments.implicit_manifold import orthonormal_tangent_basis
from grashof_workspace.spatial_experiments.jacobians import position_jacobian
from grashof_workspace.spatial_experiments.parent_local import (
    ParentRepresentationStatus,
    build_generic_5r_local_patch,
)
from grashof_workspace.spatial_experiments.v06_corpus import build_generic_5r
from grashof_workspace.spatial_experiments.v06a1 import build_v06a1_readout


def test_local_patch_samples_meet_fixed_position_tolerance() -> None:
    result = build_generic_5r_local_patch()
    assert result.representation_status is ParentRepresentationStatus.LOCAL_PATCH
    assert result.chart is not None
    accepted = [v for v in result.vertices if v.accepted]
    assert len(accepted) >= 7
    for vertex in accepted:
        assert vertex.p_residual_m is not None
        assert vertex.p_residual_m <= POSITION_RESIDUAL_TOL_M
        assert vertex.np_shape == (5, 2)
        jp = position_jacobian(build_generic_5r().model.chain, vertex.q)
        n_v = orthonormal_tangent_basis(jp, expected_nullity=2)
        assert n_v.shape == (5, 2)
        assert np.allclose(jp @ n_v, 0.0, atol=1e-9)
        assert vertex.rank_jp == 3
        assert vertex.nullity_jp == 2
        assert vertex.rank_jd_np in (1, 2)
        assert len(vertex.jd_np_singular_values) >= 1


def test_local_patch_is_one_chart_without_fibers_or_children() -> None:
    result = build_generic_5r_local_patch()
    assert result.chart is not None
    assert result.representation_status is ParentRepresentationStatus.LOCAL_PATCH
    assert result.component_ids == ()
    assert result.fiber_ids == ()
    assert result.joint_limits == "not_modeled"
    payload = result.to_json_dict()
    assert payload["certificate_status"] is None
    assert "EXACT" not in result.representation_status.value
    assert "CLOSED_COMPONENT" not in result.representation_status.value
    json.dumps(payload, allow_nan=False)


def test_l5_bundle_keeps_unresolved_fibers_and_children() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.parent.component_ids == ()
    assert bundle.parent.process_status is ProcessStatus.SCAFFOLD
    notes = " ".join(bundle.parent.notes)
    assert "LOCAL_PATCH" in notes
    assert "UNRESOLVED" in notes
    assert bundle.fiber_placeholder.sample_count == 0
    assert bundle.fiber_placeholder.component_id == "UNRESOLVED_PARENT_COMPONENT"
    assert bundle.reconstruction.accepted_fiber_ids == ()
    for child, cert in zip(bundle.children, bundle.certificates, strict=True):
        assert child.status is CertificateStatus.UNRESOLVED
        assert cert.closed_mechanism_status is CertificateStatus.UNRESOLVED
    assert bundle.parent_local is not None
    assert bundle.parent_local["representation_status"] == "LOCAL_PATCH"
    assert bundle.parent_local["fiber_ids"] == []


def test_v06a1_readout(tmp_path) -> None:
    html = build_v06a1_readout(tmp_path)
    body = html.read_text(encoding="utf-8")
    assert "LOCAL_PATCH" in body
    assert "DecompositionCertificate" in body
    payload = json.loads((tmp_path / "data" / "v06a1_generic_5r_local_patch.json").read_text())
    assert payload["representation_status"] == "LOCAL_PATCH"
    assert payload["fiber_ids"] == []
    assert (tmp_path / "figures" / "v06a1_generic_5r_local_patch.png").is_file()
