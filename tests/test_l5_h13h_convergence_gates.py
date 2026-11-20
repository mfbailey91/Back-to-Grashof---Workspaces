"""H13H-4 run-level gate evaluation uses stored records, not the arm."""

from __future__ import annotations

from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    MetricState,
    PointingSetMetrics,
    ScalarMetric,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics import (
    evaluate_source_run_level_gates,
)

REPO = Path(__file__).resolve().parents[1]
H13G = REPO / "configs" / "l5_positive_control_h13g_source_pilot_v1.json"


def _metrics(*, miss: float = 0.0, fp: float = 0.0, haus: float = 0.0, ref: float = 0.0) -> dict:
    fine = PointingSetMetrics(
        strict_covered_count=10,
        strict_uncovered_count=5,
        reconstructed_hit_count=8,
        missed_covered=ScalarMetric(MetricState.VALUE, miss, None),
        false_positive=ScalarMetric(MetricState.VALUE, fp, None),
        hausdorff=ScalarMetric(MetricState.VALUE, haus, None),
        boundary_disagreement_fraction=0.0,
        unresolved_fraction=0.0,
        max_cell_diameter_rad=0.2,
        refinement=ScalarMetric(MetricState.VALUE, ref, None),
        coarse_metrics=None,
    )
    coarse = PointingSetMetrics(
        strict_covered_count=10,
        strict_uncovered_count=5,
        reconstructed_hit_count=8,
        missed_covered=ScalarMetric(MetricState.VALUE, miss, None),
        false_positive=ScalarMetric(MetricState.VALUE, fp, None),
        hausdorff=ScalarMetric(MetricState.VALUE, haus, None),
        boundary_disagreement_fraction=0.0,
        unresolved_fraction=0.0,
        max_cell_diameter_rad=0.4,
        refinement=ScalarMetric(MetricState.VALUE, ref, None),
        coarse_metrics=None,
    )
    fine = PointingSetMetrics(
        strict_covered_count=fine.strict_covered_count,
        strict_uncovered_count=fine.strict_uncovered_count,
        reconstructed_hit_count=fine.reconstructed_hit_count,
        missed_covered=fine.missed_covered,
        false_positive=fine.false_positive,
        hausdorff=fine.hausdorff,
        boundary_disagreement_fraction=fine.boundary_disagreement_fraction,
        unresolved_fraction=fine.unresolved_fraction,
        max_cell_diameter_rad=fine.max_cell_diameter_rad,
        refinement=fine.refinement,
        coarse_metrics=coarse,
    )
    return fine.to_json_dict()


def test_run_level_gates_fail_on_required_budget_bin() -> None:
    config = load_campaign_config(H13G)
    columns = {
        "direct_vs_oracle": _metrics(),
        "source_vs_direct": _metrics(),
        "source_vs_oracle": _metrics(),
    }
    report = {"probe_id": "P1_DEEP_COMPLETE", "direct_complete": True, "columns": columns}
    source = {
        "c_records": [
            {
                "c": 0.0,
                "required": True,
                "parameter_interval_status": "BUDGET_EXHAUSTED",
                "budget_exhausted_count": 2,
                "rasterization_incomplete_count": 0,
                "candidate_budget_exhausted": False,
                "trace_budget_exhausted": False,
                "unexplained_projected_seed_count": 0,
            }
        ],
        "fibers": [],
    }
    gate = evaluate_source_run_level_gates(config=config, probe_report=report, source_blob=source)
    assert gate["passed"] is False
    assert gate["implicates_continuation_effort"] is True
    assert len(gate["interval_blockers"]) == 1


def test_run_level_gates_pass_on_covered_bin() -> None:
    config = load_campaign_config(H13G)
    columns = {
        "direct_vs_oracle": _metrics(),
        "source_vs_direct": _metrics(),
        "source_vs_oracle": _metrics(),
    }
    report = {"probe_id": "P1_DEEP_COMPLETE", "direct_complete": True, "columns": columns}
    source = {
        "c_records": [
            {
                "c": 0.0,
                "required": True,
                "parameter_interval_status": "RETURNED_SET_FOUND",
                "budget_exhausted_count": 0,
                "rasterization_incomplete_count": 0,
                "candidate_budget_exhausted": False,
                "trace_budget_exhausted": False,
                "unexplained_projected_seed_count": 0,
            }
        ],
        "fibers": [
            {
                "fiber_id": "P1_DEEP_COMPLETE_c0_t0",
                "c": 0.0,
                "rasterization_complete": True,
                "termination_status": "RETURNED_TO_SEED",
            }
        ],
    }
    gate = evaluate_source_run_level_gates(config=config, probe_report=report, source_blob=source)
    assert gate["passed"] is True
    assert gate["implicates_continuation_effort"] is False
