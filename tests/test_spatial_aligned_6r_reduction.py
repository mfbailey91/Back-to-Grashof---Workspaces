"""Tests for generic aligned 6R Stage A reduction experiments."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.aligned_6r import GenericAligned6R
from grashof_workspace.spatial_experiments.reduction_experiments import (
    evaluate_fd_refinement,
    evaluate_full_chain_roll,
    evaluate_negative_alignment,
    evaluate_regular_reduction,
    evaluate_survey_and_singular,
)


def test_home_alignment_exact() -> None:
    dist, par = GenericAligned6R.aligned().home_alignment_residuals()
    assert dist == 0.0 or dist < 1e-15
    assert par == 0.0 or par < 1e-15


def test_regular_reduction_pass() -> None:
    result = evaluate_regular_reduction()
    assert result["status"] == "PASS"
    assert result["snapshot"]["regular"] is True


def test_fd_refinement_pass() -> None:
    result = evaluate_fd_refinement()
    assert result["status"] == "PASS"


def test_full_chain_roll_pass() -> None:
    result = evaluate_full_chain_roll()
    assert result["status"] == "PASS"


def test_negative_alignment_pass() -> None:
    result = evaluate_negative_alignment()
    assert result["status"] == "PASS"


def test_survey_and_named_singular() -> None:
    result = evaluate_survey_and_singular()
    assert result["status"] == "PASS"
    assert result["named_label"] in {"singular", "near-singular"}
    assert result["survey_regular_count"] > 0
