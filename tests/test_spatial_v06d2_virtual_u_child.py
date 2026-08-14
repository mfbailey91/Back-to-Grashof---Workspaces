"""V06D2: local U_v chart and one UUUR child; no reconstruction promotion."""

from __future__ import annotations

import json

import numpy as np

from grashof_workspace.decomposition_ladder.models import CertificateStatus
from grashof_workspace.decomposition_ladder.registry import PARENT_CHILD_FAMILIES
from grashof_workspace.decomposition_ladder.spatial_l5 import (
    build_spatial_l5_scaffold_bundle,
    default_l5_scaffold_payload,
)
from grashof_workspace.spatial_experiments.v06_corpus import (
    build_exact_two_u_5r,
    build_generic_5r,
    build_near_two_u_5r,
)
from grashof_workspace.spatial_experiments.v06d2 import build_v06d2_readout
from grashof_workspace.spatial_experiments.virtual_u_child import (
    CHILD_DIM,
    CONSTRAINT_DIM,
    ClosedUUURProblem,
    evaluate_v06d2_architecture,
    local_virtual_u_axes,
)


def test_local_chart_and_uuur_child() -> None:
    d = (0.2, 0.1, 0.97)
    n = (0.0, 0.0, 1.0)
    a, b, k = local_virtual_u_axes(d, n)
    assert abs(float(np.dot(a, b))) < 1e-12
    assert abs(float(np.linalg.norm(a) - 1.0)) < 1e-12
    assert abs(float(np.dot(a, k))) < 1e-12
    assert abs(float(np.dot(b, k))) < 1e-12
    exact = evaluate_v06d2_architecture(
        build_exact_two_u_5r(), max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    assert exact.chart is not None
    assert exact.chart.status == "LOCAL_CANDIDATE"
    assert exact.samples
    seed = min(exact.samples, key=lambda s: abs(s.s))
    assert seed.rank_j == 6
    assert seed.nullity_j == 1
    assert exact.certificate.joint_role_sequence == ("U_v", "U_phys", "U_phys", "R_phys")
    assert exact.certificate.joint_kind_sequence == ("U", "U", "U", "R")
    assert exact.certificate.evidence.get("initialized_accepted") is False
    assert exact.certificate.evidence.get("drive_mode") == "free_branch_s"
    assert exact.certificate.status not in {"EXACT_GLOBAL", "EXACT_ON_COMPONENT"}
    blob = json.dumps(exact.to_json_dict(), allow_nan=False)
    assert "curve_type" not in blob or exact.to_json_dict()["curve_type"] is None
    problem = ClosedUUURProblem.from_seed(
        build_exact_two_u_5r(), exact.chart, exact.samples[min(range(len(exact.samples)), key=lambda i: abs(exact.samples[i].s))].q_source
    )
    assert problem.jacobian(np.zeros(CHILD_DIM)).shape == (CONSTRAINT_DIM, CHILD_DIM)
    assert problem.drive_mode == "free_branch_s"


def test_controls_rejected_and_no_family_sweep() -> None:
    generic = evaluate_v06d2_architecture(build_generic_5r(), grow_source=False)
    near = evaluate_v06d2_architecture(build_near_two_u_5r(), grow_source=False)
    assert generic.certificate.status not in {"EXACT_GLOBAL", "EXACT_ON_COMPONENT"}
    assert near.certificate.status not in {"EXACT_GLOBAL", "EXACT_ON_COMPONENT"}
    assert generic.certificate.closed_mechanism_status == "REJECTED"
    families = {spec.child_label for spec in PARENT_CHILD_FAMILIES}
    assert families == {"UUUR", "UURU", "URUU", "USRR", "URSR", "URRS"}


def test_l5_one_uuur_no_reconstruction() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.reconstruction.certificate_status is CertificateStatus.UNRESOLVED
    uuur = [c for c in bundle.children if c.family == "UUUR"]
    others = [c for c in bundle.children if c.family != "UUUR"]
    assert len(uuur) == 1
    assert uuur[0].joint_role_sequence == ("U_v", "U_phys", "U_phys", "R_phys")
    assert uuur[0].status not in {
        CertificateStatus.EXACT_GLOBAL,
        CertificateStatus.EXACT_ON_COMPONENT,
    }
    assert all(c.status is CertificateStatus.UNRESOLVED for c in others)
    payload = default_l5_scaffold_payload()
    assert payload["summary"]["accepted_fiber_count"] == 0
    assert "not a 2d parent" in payload["note"].casefold()
    assert payload["summary"]["uuur_closed_status"] not in {
        "EXACT_GLOBAL",
        "EXACT_ON_COMPONENT",
    }


def test_v06d2_readout(tmp_path) -> None:
    html = build_v06d2_readout(
        tmp_path, max_charts=6, discovery_bank=16, confirmation_bank=16
    )
    body = html.read_text(encoding="utf-8")
    assert "ADR-041" in body
    payload = json.loads((tmp_path / "data" / "v06d2_virtual_u_child.json").read_text())
    json.dumps(payload, allow_nan=False)
    assert payload["exact_two_u_5r"]["certificate"]["joint_role_sequence"][0] == "U_v"
    assert payload["generic_5r"]["certificate"]["status"] != "EXACT_GLOBAL"
    assert (tmp_path / "figures" / "v06d2_virtual_u_child.png").is_file()
