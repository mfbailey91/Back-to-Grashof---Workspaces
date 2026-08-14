"""V06B: SUUR compound parent vs near control; no false complete-component claims."""

from __future__ import annotations

import json

import numpy as np

from grashof_workspace.decomposition_ladder.models import CertificateStatus
from grashof_workspace.decomposition_ladder.spatial_l5 import build_spatial_l5_scaffold_bundle
from grashof_workspace.spatial_experiments.axis_aggregation import (
    build_suur_multi_aggregation,
    detect_exact_u_pairs,
)
from grashof_workspace.spatial_experiments.compound_parent import (
    ClosedCompoundParentProblem,
    evaluate_v06b_architecture,
)
from grashof_workspace.spatial_experiments.jacobians import matrix_rank_report
from grashof_workspace.spatial_experiments.v06_corpus import (
    audit_fixed_position_seed_5r,
    build_exact_two_u_5r,
    build_generic_5r,
    build_near_two_u_5r,
)
from grashof_workspace.spatial_experiments.v06b import build_v06b_readout


def test_exact_two_u_seed_and_pairs() -> None:
    entry = build_exact_two_u_5r()
    audit = audit_fixed_position_seed_5r(entry)
    assert audit.rank_jp == 3
    assert audit.nullity_jp == 2
    pairs = detect_exact_u_pairs(entry.model)
    exact = [p for p in pairs if p.exact_u_candidate]
    assert {p.pair_index for p in exact} == {0, 2}
    c0 = next(p.center for p in exact if p.pair_index == 0)
    c2 = next(p.center for p in exact if p.pair_index == 2)
    assert float(np.linalg.norm(np.asarray(c0) - np.asarray(c2))) > 1e-6
    agg = build_suur_multi_aggregation(entry.model, entry.regular_q)
    assert agg.axis_aggregation_status == "EXACT_GLOBAL"
    assert "U_v" not in agg.joint_role_sequence
    assert agg.family_label == "S_v-U_phys-U_phys-R"


def test_near_and_generic_reject_suur_aggregation() -> None:
    near = build_near_two_u_5r()
    generic = build_generic_5r()
    near_agg = build_suur_multi_aggregation(near.model, near.regular_q)
    gen_agg = build_suur_multi_aggregation(generic.model, generic.regular_q)
    assert near_agg.axis_aggregation_status == "REJECTED"
    assert gen_agg.axis_aggregation_status == "REJECTED"
    assert any(not p.exact_u_candidate for p in detect_exact_u_pairs(near.model) if p.pair_index == 2)


def test_closed_compound_problem_rank_and_local_certificate() -> None:
    entry = build_exact_two_u_5r()
    problem = ClosedCompoundParentProblem.from_entry(entry)
    assert problem.ambient_dimension == 8
    assert problem.constraint_dimension == 6
    assert id(problem.independent_chain) != id(entry.model.chain)
    x0 = np.zeros(8)
    residual = problem.residual(x0)
    assert float(np.linalg.norm(residual)) <= 1e-12
    report = matrix_rank_report(problem.jacobian(x0))
    assert report.rank == 6
    assert report.nullity == 2
    result = evaluate_v06b_architecture(entry, grow_atlases=True, max_charts=4)
    assert result.certificate.axis_aggregation_status == "EXACT_GLOBAL"
    assert result.certificate.closed_mechanism_status == "LOCAL_ONLY"
    assert result.certificate.status == "LOCAL_ONLY"
    assert result.certificate.closed_mechanism_status not in {"EXACT_ON_COMPONENT", "EXACT_GLOBAL"}
    assert "U_v" not in result.certificate.joint_role_sequence
    json.dumps(result.to_json_dict(), allow_nan=False)


def test_generic_does_not_instantiate_suur_closed_parent() -> None:
    result = evaluate_v06b_architecture(build_generic_5r(), grow_atlases=False)
    assert result.reduced_chart_count == 0
    assert result.comparison is None
    assert result.certificate.closed_mechanism_status == "REJECTED"


def test_l5_reconstruction_still_empty() -> None:
    bundle = build_spatial_l5_scaffold_bundle()
    assert bundle.reconstruction.accepted_fiber_ids == ()
    assert bundle.reconstruction.certificate_status is CertificateStatus.UNRESOLVED
    assert bundle.parent_compound is not None
    exact = bundle.parent_compound["exact_two_u_5r"]["certificate"]
    assert exact["closed_mechanism_status"] != "EXACT_ON_COMPONENT"


def test_v06b_readout(tmp_path) -> None:
    html = build_v06b_readout(tmp_path, max_charts=4)
    body = html.read_text(encoding="utf-8")
    assert "ADR-039" in body
    assert "UUUR" in body
    payload = json.loads((tmp_path / "data" / "v06b_compound_parent.json").read_text())
    json.dumps(payload, allow_nan=False)
    assert payload["exact_two_u_5r"]["certificate"]["axis_aggregation_status"] == "EXACT_GLOBAL"
    assert payload["near_two_u_5r"]["certificate"]["axis_aggregation_status"] == "REJECTED"
    assert payload["generic_5r"]["reduced_chart_count"] == 0
    assert (tmp_path / "figures" / "v06b_compound_parent.png").is_file()
