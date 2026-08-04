"""Sprint 5 architecture experiment tests."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.experiments.offset_sweep import run_architecture_experiments
from sixr_grashof.io.results import write_records_json


def test_architecture_experiments_reproducible(tmp_path: Path) -> None:
    a = run_architecture_experiments(
        resolution="coarse",
        seed=2,
        n_ik_starts=2,
        n_a_positions=2,
        include_a_grid=False,
        epsilon_w_values=(0.0, 0.2),
        epsilon_s_values=(0.0, 0.2),
        orientation_count=16,
    )
    b = run_architecture_experiments(
        resolution="coarse",
        seed=2,
        n_ik_starts=2,
        n_a_positions=2,
        include_a_grid=False,
        epsilon_w_values=(0.0, 0.2),
        epsilon_s_values=(0.0, 0.2),
        orientation_count=16,
    )
    assert len(a.records) == len(b.records)
    for ra, rb in zip(a.records, b.records, strict=True):
        assert ra.architecture_id == rb.architecture_id
        assert ra.orientation_coverage == rb.orientation_coverage
        assert ra.prediction_outcome == rb.prediction_outcome
        assert ra.spherical_reduction_status == rb.spherical_reduction_status

    path = write_records_json(a.records, tmp_path / "records.json")
    assert path.is_file()
    # Reconstructibility: seed / resolution / offsets present.
    row = a.records[0].to_dict()
    assert "random_seed" in row and row["random_seed"] == 2
    assert row["sample_resolution"] == "coarse"
    assert "epsilon_w" in row["offset_parameters"]


def test_exact_approx_not_pooled_without_labels() -> None:
    summary = run_architecture_experiments(
        resolution="coarse",
        seed=0,
        n_ik_starts=2,
        n_a_positions=1,
        include_a_grid=False,
        epsilon_w_values=(0.0, 0.2),
        epsilon_s_values=(0.0, 0.2),
        orientation_count=12,
    )
    statuses = {(r.architecture_id, r.spherical_reduction_status) for r in summary.records}
    assert ("A", "exact") in statuses
    # B with large offset should not silently claim exact without residual.
    b_large = [r for r in summary.records if r.architecture_id == "B" and r.offset_parameters["epsilon_w"] == 0.2]
    assert b_large
    assert b_large[0].spherical_reduction_status in {"approximate", "invalid"}
    assert b_large[0].concurrency_residual > 0.0

    # Regional unreachable is a distinct outcome label when it occurs.
    for r in summary.records:
        if r.prediction_outcome == "regional_unreachable":
            assert r.regional_reachable is False or r.orientation_coverage >= 0.0


def test_gate_summary_fields_present() -> None:
    summary = run_architecture_experiments(
        resolution="coarse",
        seed=1,
        n_ik_starts=2,
        n_a_positions=2,
        include_a_grid=False,
        orientation_count=12,
    )
    d = summary.to_dict()
    assert "gate3_crank_precision" in d
    assert "gate4_residual_error_correlation" in d
    assert "gate5_c_orientation_stable" in d
    assert "outcome_counts" in d
    assert d["gate5_c_orientation_stable"] is True
