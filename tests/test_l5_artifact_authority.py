"""Content-addressed artifacts, compact results, and first-failing-column closeout."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grashof_workspace.spatial_experiments.l5_reconstruction.artifacts import (
    finalize_stage,
    update_artifact_index,
    validate_artifact_hashes,
    validate_campaign_tree,
    validate_stage_output_refs,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.campaign_package import (
    assert_can_replace_results,
    compact_direct_truth,
    compact_natural_family,
    compact_source_control,
    package_r3a_campaign,
    validate_package_scope,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.cli import run_stage, write_manifest
from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import (
    campaign_reconstruction_accepted,
    first_campaign_blocker,
    localize_campaign_blocker,
    localize_probe_blocker,
    pointing_set_metrics,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    ArtifactHashDrift,
    CampaignBlocker,
    CellClass,
    CompletenessLabel,
    ReconstructionDisposition,
    ThreeWayReconstructionResult,
    file_sha256,
    load_campaign_config,
    stage_envelope,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def _blocker_result(
    probe_id: str,
    blocker: CampaignBlocker,
    *,
    expected_complete: bool = True,
) -> ThreeWayReconstructionResult:
    accepted = blocker is CampaignBlocker.CONTROLLED_COVER_ACCEPTED
    return ThreeWayReconstructionResult(
        probe_id=probe_id,
        oracle_complete=expected_complete,
        direct_complete=expected_complete,
        source_control_metrics=None,
        natural_leaf_metrics=None,
        point_classification=(
            CompletenessLabel.COMPLETE if expected_complete else CompletenessLabel.PARTIAL
        ),
        disposition=(
            ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION
            if accepted
            else ReconstructionDisposition.PARTIAL
        ),
        failure_localization=blocker.value,
        campaign_blocker=blocker,
    )


def _passing_metrics():
    return pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (True, True, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        covered_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        refinement_delta=0.0,
    )


def _failing_metrics():
    return pointing_set_metrics(
        (CellClass.STRICT_COVERED, CellClass.STRICT_COVERED, CellClass.STRICT_UNCOVERED),
        (False, True, False),
        max_cell_diameter_rad=0.4,
        reconstructed_dirs=((0.0, 1.0, 0.0),),
        covered_dirs=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        refinement_delta=0.0,
    )


def _metric_result(
    *,
    direct,
    source,
    natural,
    expected_complete: bool = True,
    classification: CompletenessLabel | None = None,
) -> ThreeWayReconstructionResult:
    label = classification
    if label is None:
        label = CompletenessLabel.COMPLETE if expected_complete else CompletenessLabel.PARTIAL
    return ThreeWayReconstructionResult(
        probe_id="P1_DEEP_COMPLETE",
        oracle_complete=expected_complete,
        direct_complete=True,
        source_control_metrics=source,
        natural_leaf_metrics=natural,
        point_classification=label,
        disposition=ReconstructionDisposition.PARTIAL,
        failure_localization="test",
        direct_vs_oracle=direct,
        source_vs_direct=source,
        natural_vs_direct=natural,
    )


def _hashed_raw_campaign(raw: Path, *, probe_id: str = "P1_DEEP_COMPLETE") -> None:
    write_manifest(CONFIG, raw, mode="ci")
    config = load_campaign_config(CONFIG)
    probe = raw / probe_id
    probe.mkdir(parents=True, exist_ok=True)
    (probe / "fixture.json").write_text(json.dumps({"probe_id": probe_id, "rank_jp": 5}), encoding="utf-8")
    (probe / "direct_truth.json").write_text(
        json.dumps({"discovery": {"solves": [{"clusters": [1]}]}, "confirmation": {"solves": []}}),
        encoding="utf-8",
    )
    (probe / "source_control.json").write_text(
        json.dumps(
            {
                "fibers": [{"q_samples": [[0.0]], "fiber_id": "f", "component_id": "c0"}],
                "pointing_samples": [[1.0, 0.0, 0.0]],
                "c_records": [{"parameter_interval_status": "RETURNED_COMPONENT_FOUND"}],
            }
        ),
        encoding="utf-8",
    )
    (probe / "natural_family.json").write_text(
        json.dumps({"leaves": [{"accepted_for_reconstruction": False, "samples": [{"q_source": [0.0]}]}]}),
        encoding="utf-8",
    )
    (probe / "comparison.json").write_text(json.dumps({"probe_id": probe_id}), encoding="utf-8")
    probe_ids = (probe_id,)
    for stage, payload in (
        ("fixture", {}),
        ("truth", {}),
        ("source-control", {}),
        ("leaves", {}),
        (
            "compare",
            {
                "campaign_blocker": "STITCHING_CONTROL_BLOCKED",
                "accepted_reconstruction": False,
            },
        ),
    ):
        sealed_payload = {
            **stage_envelope(
                config,
                stage=stage,
                mode="ci",
                probe_ids=probe_ids,
            ),
            **payload,
        }
        finalize_stage(
            raw,
            sealed_payload,
            config=config,
            stage=stage,
            mode="ci",
            probe_ids=probe_ids,
        )
    campaign = raw / "campaign.json"
    if campaign.is_file():
        (raw / "compare.json").write_text(campaign.read_text(encoding="utf-8"), encoding="utf-8")
        update_artifact_index(raw, (raw / "compare.json",))


def test_artifact_hash_drift_is_refused(tmp_path: Path) -> None:
    write_manifest(CONFIG, tmp_path, mode="ci")
    run_stage(
        config_path=CONFIG,
        outdir=tmp_path,
        stage="fixture",
        mode="ci",
        probe_id=None,
        resume_from=None,
        probe_ids=["P1_DEEP_COMPLETE"],
    )
    target = tmp_path / "P1_DEEP_COMPLETE" / "fixture.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["rank_jp"] = 0
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactHashDrift):
        run_stage(
            config_path=CONFIG,
            outdir=tmp_path,
            stage="truth",
            mode="ci",
            probe_id=None,
            resume_from=None,
            probe_ids=["P1_DEEP_COMPLETE"],
        )


def test_fixture_summary_hash_drift_is_refused(tmp_path: Path) -> None:
    write_manifest(CONFIG, tmp_path, mode="ci")
    run_stage(
        config_path=CONFIG,
        outdir=tmp_path,
        stage="fixture",
        mode="ci",
        probe_id=None,
        resume_from=None,
        probe_ids=["P1_DEEP_COMPLETE"],
    )
    summary = tmp_path / "fixture.json"
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["tampered"] = True
    summary.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactHashDrift):
        run_stage(
            config_path=CONFIG,
            outdir=tmp_path,
            stage="truth",
            mode="ci",
            probe_id=None,
            resume_from=None,
            probe_ids=["P1_DEEP_COMPLETE"],
        )


def test_missing_artifact_index_hash_is_refused(tmp_path: Path) -> None:
    write_manifest(CONFIG, tmp_path, mode="ci")
    (tmp_path / "artifact_index.json").unlink()
    with pytest.raises(ArtifactHashDrift, match="missing artifact_index"):
        run_stage(
            config_path=CONFIG,
            outdir=tmp_path,
            stage="fixture",
            mode="ci",
            probe_id=None,
            resume_from=None,
            probe_ids=["P1_DEEP_COMPLETE"],
        )


def test_unindexed_path_hash_is_refused(tmp_path: Path) -> None:
    write_manifest(CONFIG, tmp_path, mode="ci")
    stray = tmp_path / "stray.json"
    stray.write_text("{}", encoding="utf-8")
    with pytest.raises(ArtifactHashDrift, match="missing recorded hash"):
        validate_artifact_hashes(tmp_path, (stray,))


def test_compact_results_exclude_raw_solver_banks() -> None:
    truth = {
        "probe_id": "P1",
        "discovery": {
            "solves": [
                {
                    "clusters": [{"members": [[0.0, 0.0]], "seed_sources": ["sobol"]}],
                    "n_starts": 8,
                }
            ],
            "found_count": 1,
        },
        "confirmation": {"solves": [{"clusters": [{"members": [[1.0]]}]}], "found_count": 1},
        "confirmation_cells": [{"cell_id": 0}],
    }
    compact_truth = compact_direct_truth(truth)
    assert "solves" not in compact_truth["discovery"]
    assert "clusters" not in json.dumps(compact_truth)
    assert compact_truth["discovery"]["solves_omitted"] is True
    family = {
        "leaves": [
            {"accepted_for_reconstruction": True, "samples": [{"q_source": [0.0]} for _ in range(20)]},
            {"accepted_for_reconstruction": False, "samples": [{"q_source": [1.0]}]},
        ],
        "lambda_intervals": [{"interval_status": "SAMPLED_LOCAL"}],
    }
    compact_family = compact_natural_family(family)
    assert compact_family["leaf_count"] == 2
    assert compact_family["raw_leaves_omitted"] is True
    assert len(compact_family["leaves"][0]["samples"]) <= 3
    source = {
        "fibers": [{"fiber_id": "f0", "q_samples": [[0.0, 0.0, 0.0, 0.0, 0.0]], "c": 0.1, "returned": True}],
        "pointing_samples": [[0.0, 0.0, 1.0]],
        "c_records": [{"parameter_interval_status": "RETURNED_COMPONENT_FOUND"}],
    }
    compact_source = compact_source_control(source)
    assert "q_samples" not in compact_source["fibers"][0]
    assert compact_source["fibers"][0]["fiber_id"] == "f0"
    assert "pointing_samples" not in compact_source
    assert compact_source["pointing_samples_omitted"] is True
    assert compact_source["c_records"][0]["parameter_interval_status"] == "RETURNED_COMPONENT_FOUND"


def test_raw_bundle_hash_matches_manifest(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    results = tmp_path / "compact"
    bundles = tmp_path / "bundles"
    _hashed_raw_campaign(raw)
    manifest = package_r3a_campaign(
        raw_root=raw,
        results_root=results,
        bundle_dir=bundles,
        config_path=CONFIG,
    )
    bundle = bundles / str(manifest["raw_bundle"])
    assert bundle.is_file()
    assert file_sha256(bundle) == manifest["raw_bundle_sha256"]
    assert manifest["package_kind"] == "diagnostic"
    assert manifest["campaign_mode"] == "ci"
    assert manifest["probe_ids"] == ["P1_DEEP_COMPLETE"]
    assert manifest["all_configured_probes_present"] is False
    assert manifest["full_closeout_eligible"] is False
    assert str(manifest["raw_bundle"]).startswith("r3a_ci_1probes_")
    assert manifest["raw_bundle_archive_root"] == "r3a_ci_raw"
    assert "--mode ci" in manifest["reproduction"]
    assert "--probe P1_DEEP_COMPLETE" in manifest["reproduction"]
    assert manifest["git"] == manifest["producer_git"]
    assert "packager_git" in manifest
    compact_truth = json.loads(
        (results / "P1_DEEP_COMPLETE" / "direct_truth.json").read_text(encoding="utf-8")
    )
    assert "solves" not in compact_truth["discovery"]
    truth_summary = json.loads((results / "truth.json").read_text(encoding="utf-8"))
    validate_stage_output_refs(results, truth_summary)
    compact_path = "P1_DEEP_COMPLETE/direct_truth.json"
    recorded = {
        item["path"]: item["sha256"]
        for item in truth_summary["outputs"]
        if isinstance(item, dict)
    }
    assert recorded[compact_path] == file_sha256(results / compact_path)


def test_packager_refuses_raw_hash_drift(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _hashed_raw_campaign(raw)
    target = raw / "P1_DEEP_COMPLETE" / "direct_truth.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["tampered"] = True
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ArtifactHashDrift):
        package_r3a_campaign(
            raw_root=raw,
            results_root=tmp_path / "compact",
            bundle_dir=tmp_path / "bundles",
            config_path=CONFIG,
        )


def test_full_closeout_refuses_ci_subset(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _hashed_raw_campaign(raw)
    with pytest.raises(ValueError, match="mode='full'"):
        package_r3a_campaign(
            raw_root=raw,
            results_root=tmp_path / "compact",
            bundle_dir=tmp_path / "bundles",
            config_path=CONFIG,
            full_closeout=True,
        )


def test_campaign_config_hash_mismatch_is_refused_before_packaging(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _hashed_raw_campaign(raw)
    campaign_path = raw / "campaign.json"
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    campaign["config_hash"] = "mismatched-config"
    campaign_path.write_text(json.dumps(campaign), encoding="utf-8")
    with pytest.raises(ValueError, match="campaign config-hash drift"):
        package_r3a_campaign(
            raw_root=raw,
            results_root=tmp_path / "compact",
            bundle_dir=tmp_path / "bundles",
            config_path=CONFIG,
        )


def test_full_scope_requires_all_five_probes_and_one_blocker() -> None:
    config = load_campaign_config(CONFIG)
    probe_ids = [probe.probe_id for probe in config.probes]
    campaign = {
        "config_hash": config.config_hash,
        "mode": "full",
        "probe_ids": probe_ids,
        "campaign_blocker": CampaignBlocker.STITCHING_CONTROL_BLOCKED.value,
        "accepted_reconstruction": False,
    }
    mode, declared, all_configured = validate_package_scope(
        campaign,
        config,
        full_closeout=True,
    )
    assert mode == "full"
    assert declared == tuple(probe_ids)
    assert all_configured is True

    campaign["probe_ids"] = probe_ids[:-1]
    with pytest.raises(ValueError, match="all configured probes"):
        validate_package_scope(campaign, config, full_closeout=True)


def test_strict_campaign_tree_requires_every_stage(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _hashed_raw_campaign(raw)
    config = load_campaign_config(CONFIG)
    with pytest.raises(FileNotFoundError, match="render.json"):
        validate_campaign_tree(
            raw,
            ("P1_DEEP_COMPLETE",),
            expected_config_hash=config.config_hash,
            expected_mode="ci",
            require_all_stages=True,
        )


def test_packager_refuses_git_tracked_results_without_flag() -> None:
    committed = Path("results/l5_reconstruction/r3a")
    if not committed.is_dir():
        pytest.skip("committed R3A hub is not present")
    with pytest.raises(ValueError, match="git-tracked"):
        assert_can_replace_results(committed, replace_committed=False)
    assert_can_replace_results(committed, replace_committed=True)


def test_global_blocker_localizes_direct_first() -> None:
    blockers = (
        CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED,
        CampaignBlocker.STITCHING_CONTROL_BLOCKED,
        CampaignBlocker.DIRECT_REFERENCE_BLOCKED,
    )
    assert (
        first_campaign_blocker(blockers, campaign_accepted=False)
        is CampaignBlocker.DIRECT_REFERENCE_BLOCKED
    )


def test_global_blocker_localizes_source_before_natural() -> None:
    blockers = (
        CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED,
        CampaignBlocker.STITCHING_CONTROL_BLOCKED,
        CampaignBlocker.CONTROLLED_COVER_ACCEPTED,
    )
    assert (
        first_campaign_blocker(blockers, campaign_accepted=False)
        is CampaignBlocker.STITCHING_CONTROL_BLOCKED
    )


def test_global_blocker_localizes_natural_after_source_pass() -> None:
    blockers = (
        CampaignBlocker.CONTROLLED_COVER_ACCEPTED,
        CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED,
    )
    assert (
        first_campaign_blocker(blockers, campaign_accepted=False)
        is CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED
    )


def test_global_blocker_does_not_invent_natural_when_columns_pass() -> None:
    blockers = (CampaignBlocker.CONTROLLED_COVER_ACCEPTED, CampaignBlocker.CONTROLLED_COVER_ACCEPTED)
    assert first_campaign_blocker(blockers, campaign_accepted=False) is None


def test_localize_probe_blocker_direct_before_source() -> None:
    config = load_campaign_config(CONFIG)
    fail = _failing_metrics()
    ok = _passing_metrics()
    result = _metric_result(direct=fail, source=ok, natural=ok)
    assert localize_probe_blocker(result, config) is CampaignBlocker.DIRECT_REFERENCE_BLOCKED


def test_localize_probe_blocker_source_before_natural() -> None:
    config = load_campaign_config(CONFIG)
    ok = _passing_metrics()
    fail = _failing_metrics()
    result = _metric_result(direct=ok, source=fail, natural=fail)
    assert localize_probe_blocker(result, config) is CampaignBlocker.STITCHING_CONTROL_BLOCKED
    unresolved = _metric_result(direct=ok, source=ok, natural=fail)
    assert (
        localize_probe_blocker(unresolved, config, unresolved_c=True)
        is CampaignBlocker.STITCHING_CONTROL_BLOCKED
    )


def test_localize_probe_blocker_natural_after_source_pass() -> None:
    config = load_campaign_config(CONFIG)
    ok = _passing_metrics()
    fail = _failing_metrics()
    result = _metric_result(direct=ok, source=ok, natural=fail)
    assert localize_probe_blocker(result, config) is CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED
    unresolved = _metric_result(direct=ok, source=ok, natural=ok)
    assert (
        localize_probe_blocker(unresolved, config, unresolved_family=True)
        is CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED
    )


def test_localize_probe_blocker_classification_mismatch_is_natural() -> None:
    config = load_campaign_config(CONFIG)
    ok = _passing_metrics()
    result = _metric_result(
        direct=ok,
        source=ok,
        natural=ok,
        expected_complete=True,
        classification=CompletenessLabel.PARTIAL,
    )
    assert (
        localize_probe_blocker(result, config, expected_complete=True)
        is CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED
    )
    matched = _metric_result(direct=ok, source=ok, natural=ok, expected_complete=True)
    assert (
        localize_probe_blocker(matched, config, expected_complete=True)
        is CampaignBlocker.CONTROLLED_COVER_ACCEPTED
    )


def test_full_acceptance_requires_all_five_probes() -> None:
    config = load_campaign_config(CONFIG)
    full = config.mode("full")
    four = tuple(
        _blocker_result(
            probe.probe_id,
            CampaignBlocker.CONTROLLED_COVER_ACCEPTED,
            expected_complete=probe.expected_pointing_complete,
        )
        for probe in config.probes[:4]
    )
    assert campaign_reconstruction_accepted(four, config.probes, full) is False
    blocker = localize_campaign_blocker(four, config.probes, full, config)
    assert blocker is not CampaignBlocker.CONTROLLED_COVER_ACCEPTED
    assert blocker is not CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED
    assert blocker is None
    five = tuple(
        _blocker_result(
            probe.probe_id,
            CampaignBlocker.CONTROLLED_COVER_ACCEPTED,
            expected_complete=probe.expected_pointing_complete,
        )
        for probe in config.probes
    )
    assert campaign_reconstruction_accepted(five, config.probes, full) is True
    assert (
        localize_campaign_blocker(five, config.probes, full, config)
        is CampaignBlocker.CONTROLLED_COVER_ACCEPTED
    )
    ci_blocker = localize_campaign_blocker(five, config.probes, config.mode("ci"), config)
    assert ci_blocker is not CampaignBlocker.CONTROLLED_COVER_ACCEPTED
    assert ci_blocker is not CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED
    assert ci_blocker is None
