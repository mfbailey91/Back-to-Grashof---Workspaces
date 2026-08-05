"""Runner-level guards for Sprint 06 spherical experiments."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.spherical_experiments import (
    evaluate_duplicate_scan,
    evaluate_ip_alternate_invariants,
    evaluate_ip_primary_invariants,
    evaluate_urlike_parallel,
)


def test_urlike_parallel_does_not_require_suur(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("suur_map must stay out of ATR_EXP_035")

    monkeypatch.setattr(
        "grashof_workspace.spatial_experiments.suur_coordinates.suur_map",
        _boom,
    )
    result = evaluate_urlike_parallel()
    assert result["experiment_id"] == "ATR_EXP_035"
    assert result["metrics"]["suur_required"] is False
    assert result["metrics"]["axes_construction"] == "exploratory_fixed_physical_subset"
    assert result["metrics"]["exact_rrrr_claim"] is False


def test_duplicate_and_ip_evaluators_do_not_call_suur(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("suur_map must stay out of ATR_EXP_032–034")

    monkeypatch.setattr(
        "grashof_workspace.spatial_experiments.suur_coordinates.suur_map",
        _boom,
    )
    assert evaluate_duplicate_scan()["experiment_id"] == "ATR_EXP_032"
    assert evaluate_ip_primary_invariants()["experiment_id"] == "ATR_EXP_033"
    assert evaluate_ip_alternate_invariants()["experiment_id"] == "ATR_EXP_034"
