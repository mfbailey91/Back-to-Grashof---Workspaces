"""UURU certificate statuses and absence of h_c."""

from __future__ import annotations

import json

from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    json_dumps_strict,
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
    continue_uuru_leaf,
    issue_leaf_certificate,
    leaf_spec_for,
    problem_from_source_seed,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_certificate_has_no_h_c_and_is_component_scoped() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q = analytic_seed_configuration(config.geometry, probe)
    chart = charts_from_config(config.charts)[0]
    built = problem_from_source_seed(arm, chart, q, probe.p_star, leaf_id="cert_leaf")
    assert built is not None
    problem, x0 = built
    samples, status, returned = continue_uuru_leaf(problem, x0, max_steps=4)
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
    payload = cert.to_json_dict()
    text = json_dumps_strict(payload)
    assert "h_c" not in payload
    assert '"h_c"' not in text
    assert payload["closed_mechanism_status"] in {
        "EXACT_ON_COMPONENT",
        "LOCAL_ONLY",
        "REJECTED",
        "UNRESOLVED",
    }
    json.loads(text)
