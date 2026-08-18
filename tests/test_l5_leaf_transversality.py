"""Transversality uses child tangents; every neighbor pair is audited."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from grashof_workspace.spatial_experiments.implicit_manifold import orthonormal_tangent_basis
from grashof_workspace.spatial_experiments.jacobians import position_jacobian
from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    LeafWorkRecord,
    audit_all_neighbors,
    audit_neighbor_transversality,
    circular_neighbor_pairs,
    recompute_family_acceptance,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    ACCEPTED_CHILD_STATUSES,
    ChartOverlapAudit,
    FamilyAdmissibilityStatus,
    TransversalityAudit,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    child_tangent,
    continue_uuru_leaf,
    issue_leaf_certificate,
    leaf_spec_for,
    problem_from_source_seed,
)

CONFIG = "configs/l5_positive_control_v1.json"


def _wrap(q: tuple[float, ...], delta: np.ndarray) -> tuple[float, ...]:
    arr = np.asarray(q, dtype=float) + np.asarray(delta, dtype=float)
    return tuple(float(np.arctan2(np.sin(v), np.cos(v))) for v in arr)


def _work_from_q(arm, chart, probe, q, leaf_id: str, *, max_steps: int = 6) -> LeafWorkRecord | None:
    built = problem_from_source_seed(arm, chart, q, probe.p_star, leaf_id=leaf_id)
    if built is None:
        return None
    problem, x0 = built
    samples, status, returned = continue_uuru_leaf(problem, x0, max_steps=max_steps, step_size=0.08)
    if len(samples) < 1:
        return None
    spec = leaf_spec_for(probe.probe_id, chart, problem.lambda_fixed, probe.p_star, problem.problem_id)
    cert = issue_leaf_certificate(
        spec,
        samples,
        branch_status=status,
        returned=returned,
        position_tol=1e-6,
        orientation_tol=1e-5,
        pointing_tol=1e-5,
        lift_tol=1e-8,
        lambda_tol=1e-5,
        closure_tol=1e-6,
    )
    return LeafWorkRecord(
        certificate=cert,
        problem=problem,
        seed_x=tuple(float(v) for v in x0),
        seed_q=tuple(float(v) for v in problem.physical_q(x0)),
        chart=chart,
        lambda_fixed=float(problem.lambda_fixed),
    )


def _p1_fixture():
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    chart = charts_from_config(config.charts)[0]
    q0 = analytic_seed_configuration(config.geometry, probe)
    return config, arm, chart, probe, q0


def _two_neighbor_works() -> tuple[LeafWorkRecord, LeafWorkRecord]:
    _config, arm, chart, probe, q0 = _p1_fixture()
    w0 = _work_from_q(arm, chart, probe, q0, "leaf_a", max_steps=6)
    assert w0 is not None
    for delta in (0.12, 0.2, 0.28, 0.36, -0.18, 0.45):
        q1 = _wrap(q0, np.array([delta, 0.0, 0.0, 0.0, 0.0]))
        w1 = _work_from_q(arm, chart, probe, q1, "leaf_b", max_steps=6)
        if w1 is None:
            continue
        gap = abs(float(np.arctan2(np.sin(w1.lambda_fixed - w0.lambda_fixed), np.cos(w1.lambda_fixed - w0.lambda_fixed))))
        if gap >= 0.05:
            return w0, w1
    raise AssertionError("could not construct a second distinct-lambda neighbor")


def test_transversality_uses_child_tangent() -> None:
    config, arm, *_rest = _p1_fixture()
    work_a, work_b = _two_neighbor_works()
    audit = audit_neighbor_transversality(
        arm,
        work_a,
        work_b,
        sigma_min=config.tolerances.minimum_transversality_sigma,
    )
    notes = " ".join(audit.notes).lower()
    assert "child jacobian" in notes
    assert "proxy" not in notes
    sa = work_a.certificate.samples[0]
    t_child = child_tangent(work_a.problem, np.asarray(sa.x, dtype=float))
    jp = position_jacobian(arm.chain, sa.q_source)
    parent_plane = orthonormal_tangent_basis(jp, expected_nullity=2)
    proxy = np.asarray(parent_plane[:, 0], dtype=float)
    proxy_align = abs(float(np.dot(t_child, proxy / np.linalg.norm(proxy))))
    assert audit.sigma_min is not None
    # Child tangent is a source-Q vector from J_child, not an arbitrary parent-null column.
    assert abs(float(np.linalg.norm(t_child)) - 1.0) <= 1e-12
    if proxy_align > 1.0 - 1e-6:
        assert audit.notes and "child jacobian" in notes
    else:
        assert not np.allclose(t_child, proxy)


def test_rank_two_pair_passes_configured_sigma() -> None:
    config, arm, *_rest = _p1_fixture()
    work_a, work_b = _two_neighbor_works()
    audit = audit_neighbor_transversality(
        arm,
        work_a,
        work_b,
        sigma_min=config.tolerances.minimum_transversality_sigma,
    )
    assert work_a.lambda_fixed != work_b.lambda_fixed
    assert audit.status == "PASS"
    assert audit.rank_span == 2
    assert audit.sigma_min is not None
    assert audit.sigma_min >= config.tolerances.minimum_transversality_sigma


def test_colinear_neighbor_leaves_fail_sigma_gate() -> None:
    config, arm, *_rest = _p1_fixture()
    work_a, _work_b = _two_neighbor_works()
    sample = work_a.certificate.samples[0]
    t_s = child_tangent(work_a.problem, np.asarray(sample.x, dtype=float))
    q_col = _wrap(sample.q_source, 0.04 * t_s)
    x_col = tuple(float(v) for v in np.concatenate([np.asarray(sample.x[:2]), np.asarray(q_col)]))
    col_sample = replace(sample, q_source=q_col, x=x_col)
    work_single = LeafWorkRecord(
        certificate=replace(work_a.certificate, samples=(sample,)),
        problem=work_a.problem,
        seed_x=work_a.seed_x,
        seed_q=sample.q_source,
        chart=work_a.chart,
        lambda_fixed=work_a.lambda_fixed,
    )
    spec_b = replace(
        work_a.certificate.spec,
        leaf_id="colinear_b",
        lambda_fixed=float(work_a.lambda_fixed + 0.25),
    )
    cert_b = replace(
        work_a.certificate,
        spec=spec_b,
        samples=(col_sample,),
    )
    work_col = LeafWorkRecord(
        certificate=cert_b,
        problem=work_a.problem,
        seed_x=x_col,
        seed_q=q_col,
        chart=work_a.chart,
        lambda_fixed=float(spec_b.lambda_fixed),
    )
    audit = audit_neighbor_transversality(
        arm,
        work_single,
        work_col,
        sigma_min=config.tolerances.minimum_transversality_sigma,
    )
    assert audit.status == "FAIL"
    assert audit.sigma_min is not None
    assert audit.sigma_min < config.tolerances.minimum_transversality_sigma


def test_all_neighbor_pairs_audited() -> None:
    config, arm, *_rest = _p1_fixture()
    work_a, work_b = _two_neighbor_works()
    spec_c = replace(
        work_a.certificate.spec,
        leaf_id="leaf_c",
        lambda_fixed=float(work_a.lambda_fixed + 1.1),
    )
    work_c = LeafWorkRecord(
        certificate=replace(work_a.certificate, spec=spec_c),
        problem=work_a.problem,
        seed_x=work_a.seed_x,
        seed_q=work_a.seed_q,
        chart=work_a.chart,
        lambda_fixed=float(spec_c.lambda_fixed),
    )
    works = (work_a, work_b, work_c)
    ordered = tuple(
        sorted(
            works,
            key=lambda item: float(np.arctan2(np.sin(item.lambda_fixed), np.cos(item.lambda_fixed))),
        )
    )
    expected = circular_neighbor_pairs(tuple(item.certificate.spec.leaf_id for item in ordered))
    assert len(expected) == 3
    audits = audit_all_neighbors(
        arm,
        works,
        sigma_min=config.tolerances.minimum_transversality_sigma,
    )
    assert len(audits) == 3
    got = {frozenset((item.leaf_id_a, item.leaf_id_b)) for item in audits}
    want = {frozenset(pair) for pair in expected}
    assert got == want
    assert not any(item.leaf_id_a is None or item.leaf_id_b is None for item in audits)


def test_one_bad_neighbor_prevents_family_pass() -> None:
    _config, _arm, *_rest = _p1_fixture()
    work_a, work_b = _two_neighbor_works()
    spec_c = replace(work_a.certificate.spec, leaf_id="leaf_c")
    cert_c = replace(work_a.certificate, spec=spec_c)
    pass_ab = TransversalityAudit(
        status="PASS",
        sigma_min=0.4,
        rank_span=2,
        notes=("synthetic pass",),
        leaf_id_a=work_a.certificate.spec.leaf_id,
        leaf_id_b=work_b.certificate.spec.leaf_id,
        lambda_a=work_a.lambda_fixed,
        lambda_b=work_b.lambda_fixed,
    )
    fail_bc = TransversalityAudit(
        status="FAIL",
        sigma_min=1e-12,
        rank_span=1,
        notes=("synthetic fail",),
        leaf_id_a=work_b.certificate.spec.leaf_id,
        leaf_id_b="leaf_c",
        lambda_a=work_b.lambda_fixed,
        lambda_b=work_a.lambda_fixed + 1.0,
    )
    overlap = ChartOverlapAudit(status="UNRESOLVED")
    updated = recompute_family_acceptance(
        (work_a.certificate, work_b.certificate, cert_c),
        (pass_ab, fail_bc),
        overlap,
    )
    assert all(leaf.family_admissibility_status is FamilyAdmissibilityStatus.FAIL for leaf in updated)
    assert all(leaf.accepted_for_reconstruction is False for leaf in updated)


def test_returned_leaf_not_accepted_before_family_audits() -> None:
    _config, arm, chart, probe, q0 = _p1_fixture()
    work = _work_from_q(arm, chart, probe, q0, "pre_audit", max_steps=4)
    assert work is not None
    cert = work.certificate
    assert cert.family_admissibility_status is FamilyAdmissibilityStatus.UNRESOLVED
    assert cert.accepted_for_reconstruction is False
    assert cert.leaf_component_status not in ACCEPTED_CHILD_STATUSES or cert.accepted_for_reconstruction is False
