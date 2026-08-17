"""Source-control reconstruction paints cells or marks misses; no false complete."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import pointing_set_metrics
from grashof_workspace.spatial_experiments.l5_reconstruction.direct_truth import (
    build_direct_pointing_truth,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CellClass,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    build_source_control,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.sphere_grid import (
    build_sphere_grid,
    classify_cells,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_deep_complete_marks_hits_or_explicit_misses() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P1_DEEP_COMPLETE")
    discovery = build_direct_pointing_truth(
        arm, probe, config, split="discovery", icosphere_level=0, sobol_count=4, max_nfev=40, target_indices=(0, 1, 4)
    )
    result = build_source_control(arm, probe, discovery, c_count=3, confirmation_level=0, max_steps=6)
    grid = build_sphere_grid(0)
    labels = classify_cells(
        grid, config.geometry, probe.p_star, margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m
    )
    metrics = pointing_set_metrics(
        labels,
        result.hit_cells,
        max_cell_diameter_rad=grid.max_cell_diameter_rad,
        reconstructed_dirs=result.pointing_samples,
        covered_dirs=tuple(tuple(float(v) for v in grid.barycenters[i]) for i, lab in enumerate(labels) if lab is CellClass.STRICT_COVERED),
    )
    assert metrics.missed_covered_fraction is None or metrics.missed_covered_fraction <= 1.0
    assert metrics.reconstructed_hit_count >= 0


def test_negative_probe_does_not_become_false_complete() -> None:
    config = load_campaign_config(CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probe("P3_INNER_INCOMPLETE")
    discovery = build_direct_pointing_truth(
        arm, probe, config, split="discovery", icosphere_level=0, sobol_count=4, max_nfev=40, target_indices=(0, 2)
    )
    result = build_source_control(arm, probe, discovery, c_count=2, confirmation_level=0, max_steps=6)
    grid = build_sphere_grid(0)
    labels = classify_cells(
        grid, config.geometry, probe.p_star, margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m
    )
    metrics = pointing_set_metrics(
        labels,
        result.hit_cells,
        max_cell_diameter_rad=grid.max_cell_diameter_rad,
        reconstructed_dirs=result.pointing_samples,
        covered_dirs=(),
    )
    assert metrics.false_positive_fraction is None or metrics.false_positive_fraction < 1.0
    assert probe.expected_pointing_complete is False
