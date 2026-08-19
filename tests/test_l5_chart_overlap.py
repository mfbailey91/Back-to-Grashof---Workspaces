"""Chart overlap is source-Q correspondence, not directed-distance asymmetry."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import audit_chart_overlap
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    analytic_seed_configuration,
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    continue_uuru_leaf,
    problem_from_source_seed,
)

CONFIG = "configs/l5_positive_control_v1.json"


def _continued_source_curve():
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    q = analytic_seed_configuration(config.geometry, probe)
    charts = charts_from_config(config.charts)
    built = problem_from_source_seed(arm, charts[0], q, probe.p_star, leaf_id="overlap_a")
    assert built is not None
    problem, x0 = built
    samples, _status, _returned = continue_uuru_leaf(problem, x0, max_steps=6, step_size=0.08)
    assert samples
    return config, arm, charts, samples


def test_empty_overlap_is_unresolved() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    charts = charts_from_config(config.charts)
    audit = audit_chart_overlap(
        arm,
        charts[0],
        charts[1],
        (),
        ((0.0, 0.0, 0.0, 0.0, 0.0),),
        (),
        ((0.0, 0.0, 1.0),),
        lambda_a=0.0,
        lambda_b=0.1,
        q_tol=config.tolerances.leaf_duplicate_distance_rad,
        rotation_tol=config.tolerances.orientation_geodesic_rad,
        pointing_tol=config.tolerances.pointing_geodesic_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
    )
    assert audit.status == "UNRESOLVED"
    assert audit.status != "COMPATIBLE"


def test_same_source_curve_in_two_charts_is_compatible() -> None:
    config, arm, charts, samples = _continued_source_curve()
    qs = tuple(item.q_source for item in samples)
    pointings = tuple(item.pointing for item in samples)
    q0 = qs[0]
    r0 = arm.chain.evaluate(q0).R
    lam_a = charts[0].decompose(r0).lam
    lam_b = charts[1].decompose(r0).lam
    audit = audit_chart_overlap(
        arm,
        charts[0],
        charts[1],
        qs,
        qs,
        pointings,
        pointings,
        lambda_a=lam_a,
        lambda_b=lam_b,
        q_tol=config.tolerances.leaf_duplicate_distance_rad,
        rotation_tol=config.tolerances.orientation_geodesic_rad,
        pointing_tol=config.tolerances.pointing_geodesic_rad,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
    )
    assert audit.status == "COMPATIBLE"
    assert audit.source_q_correspondence is True
    assert audit.recovered_rotation_correspondence is True
    assert audit.chart_coordinate_transform is True
    assert audit.family_parameter_correspondence is True
    assert audit.component_identity is True
    assert audit.pointing_set_correspondence is True
    notes = " ".join(audit.notes).lower()
    assert "d_ab" not in notes
    assert "asymmetry" not in notes


def test_pointing_overlap_with_disjoint_q_is_not_compatible() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    charts = charts_from_config(config.charts)
    pointing = ((0.0, 0.0, 1.0), (0.0, 0.1, np.sqrt(1.0 - 0.1**2)))
    q_a = ((0.0, 0.0, 0.0, 0.0, 0.0), (0.05, 0.0, 0.0, 0.0, 0.0))
    q_b = ((1.4, 0.3, -0.2, 0.1, 0.4), (1.5, 0.3, -0.2, 0.1, 0.4))
    audit = audit_chart_overlap(
        arm,
        charts[0],
        charts[1],
        q_a,
        q_b,
        pointing,
        pointing,
        lambda_a=0.1,
        lambda_b=-0.4,
        q_tol=config.tolerances.leaf_duplicate_distance_rad,
        rotation_tol=config.tolerances.orientation_geodesic_rad,
        pointing_tol=0.2,
        lambda_tol=config.tolerances.family_coordinate_error_rad,
    )
    assert audit.status != "COMPATIBLE"
    assert audit.source_q_correspondence is False
    assert audit.status in {"UNRESOLVED", "INCOMPATIBLE"}
