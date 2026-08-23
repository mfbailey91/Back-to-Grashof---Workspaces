"""Content-addressed artifacts, compact results, and first-failing-column closeout."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

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
    validate_full_closeout_semantics,
    validate_package_scope,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.cli import run_stage, write_manifest
from grashof_workspace.spatial_experiments.l5_reconstruction.comparison import (
    campaign_reconstruction_accepted,
    classify_probe_reconstruction,
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
    json_dumps_strict,
    load_campaign_config,
    stage_envelope,
)

CONFIG = Path("configs/l5_positive_control_v1.json")
P1_P3 = ("P1_DEEP_COMPLETE", "P3_INNER_INCOMPLETE")
CLEAN_PRODUCER_GIT = {"git_commit": "a" * 40, "dirty_tree": False}
_UNSET = object()


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


def _source_blocked_result(
    probe_id: str,
    *,
    expected_complete: bool,
) -> ThreeWayReconstructionResult:
    config = load_campaign_config(CONFIG)
    direct = _passing_metrics()
    source = _failing_metrics()
    natural = _failing_metrics()
    label, disposition, reason = classify_probe_reconstruction(
        oracle_complete=expected_complete,
        expected_complete=expected_complete,
        direct_complete=True,
        direct_vs_oracle=direct,
        source_vs_direct=source,
        natural_vs_direct=natural,
        source_vs_oracle=source,
        natural_vs_oracle=natural,
        unresolved_family_intervals=(),
        unresolved_c_intervals=(),
        config=config,
    )
    result = ThreeWayReconstructionResult(
        probe_id=probe_id,
        oracle_complete=expected_complete,
        direct_complete=True,
        source_control_metrics=source,
        natural_leaf_metrics=natural,
        point_classification=label,
        disposition=disposition,
        failure_localization=reason,
        direct_vs_oracle=direct,
        source_vs_direct=source,
        natural_vs_direct=natural,
    )
    blocker = localize_probe_blocker(
        result,
        config,
        expected_complete=expected_complete,
    )
    assert blocker is CampaignBlocker.STITCHING_CONTROL_BLOCKED
    return replace(result, campaign_blocker=blocker)


def _write_probe_files(raw: Path, probe_id: str) -> None:
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


def _reseal_campaign_git(raw: Path, git: dict[str, Any] | None) -> None:
    campaign = raw / "campaign.json"
    blob = json.loads(campaign.read_text(encoding="utf-8"))
    if git is None:
        blob.pop("git", None)
    else:
        blob["git"] = dict(git)
    text = json.dumps(blob)
    campaign.write_text(text, encoding="utf-8")
    paths = [campaign]
    compare = raw / "compare.json"
    if compare.is_file():
        compare.write_text(text, encoding="utf-8")
        paths.append(compare)
    update_artifact_index(raw, paths)


def _hashed_raw_campaign(
    raw: Path,
    *,
    probe_ids: tuple[str, ...] = ("P1_DEEP_COMPLETE",),
    mode: str = "ci",
    include_render: bool = False,
    producer_git: Any = _UNSET,
) -> None:
    write_manifest(CONFIG, raw, mode=mode)
    config = load_campaign_config(CONFIG)
    comparisons = tuple(
        _source_blocked_result(
            probe_id,
            expected_complete=config.probe(probe_id).expected_pointing_complete,
        )
        for probe_id in probe_ids
    )
    for probe_id in probe_ids:
        _write_probe_files(raw, probe_id)
    for result in comparisons:
        path = raw / result.probe_id / "comparison.json"
        path.write_text(json_dumps_strict(result.to_json_dict()), encoding="utf-8")
    stages: tuple[tuple[str, dict[str, Any]], ...] = (
        ("fixture", {}),
        ("truth", {}),
        ("source-control", {}),
        ("leaves", {}),
        (
            "compare",
            {
                "comparisons": [item.to_json_dict() for item in comparisons],
                "disposition": ReconstructionDisposition.PARTIAL.value,
                "campaign_blocker": CampaignBlocker.STITCHING_CONTROL_BLOCKED.value,
                "accepted_reconstruction": False,
            },
        ),
    )
    for stage, payload in stages:
        sealed_payload = {
            **stage_envelope(
                config,
                stage=stage,
                mode=mode,
                probe_ids=probe_ids,
            ),
            **payload,
        }
        finalize_stage(
            raw,
            sealed_payload,
            config=config,
            stage=stage,
            mode=mode,
            probe_ids=probe_ids,
        )
    campaign = raw / "campaign.json"
    if campaign.is_file():
        (raw / "compare.json").write_text(campaign.read_text(encoding="utf-8"), encoding="utf-8")
        update_artifact_index(raw, (raw / "compare.json",))
    if producer_git is not _UNSET:
        git_blob = None if producer_git is None else dict(producer_git)
        _reseal_campaign_git(raw, git_blob)
    if include_render:
        (raw / "index.html").write_text("<html></html>", encoding="utf-8")
        finalize_stage(
            raw,
            stage_envelope(config, stage="render", mode=mode, probe_ids=probe_ids),
            config=config,
            stage="render",
            mode=mode,
            probe_ids=probe_ids,
        )


def _hashed_full_campaign(
    raw: Path,
    *,
    producer_git: Any = _UNSET,
    include_render: bool = True,
) -> tuple[str, ...]:
    ids = tuple(probe.probe_id for probe in load_campaign_config(CONFIG).probes)
    _hashed_raw_campaign(
        raw,
        probe_ids=ids,
        mode="full",
        include_render=include_render,
        producer_git=producer_git,
    )
    return ids


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


def test_diagnostic_package_preserves_mode_and_probe_scope(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    results = tmp_path / "compact"
    bundles = tmp_path / "bundles"
    _hashed_raw_campaign(raw, probe_ids=P1_P3, mode="ci")
    manifest = package_r3a_campaign(
        raw_root=raw,
        results_root=results,
        bundle_dir=bundles,
        config_path=CONFIG,
    )
    assert manifest["package_kind"] == "diagnostic"
    assert manifest["campaign_mode"] == "ci"
    assert manifest["probe_ids"] == list(P1_P3)
    assert manifest["all_configured_probes_present"] is False
    assert manifest["full_closeout_eligible"] is False
    assert manifest["allows_full_campaign_disposition"] is False
    assert not str(manifest["raw_bundle"]).startswith("r3a_full_")
    assert str(manifest["raw_bundle"]).startswith("r3a_ci_2probes_")
    assert "--mode ci" in manifest["reproduction"]
    assert "--probe P1_DEEP_COMPLETE" in manifest["reproduction"]
    assert "--probe P3_INNER_INCOMPLETE" in manifest["reproduction"]


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


def test_p1_p3_ci_package_is_diagnostic(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    results = tmp_path / "compact"
    bundles = tmp_path / "bundles"
    _hashed_raw_campaign(raw, probe_ids=P1_P3, mode="ci")
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
    assert manifest["probe_ids"] == list(P1_P3)
    assert manifest["all_configured_probes_present"] is False
    assert manifest["full_closeout_eligible"] is False
    assert manifest["allows_full_campaign_disposition"] is False
    assert str(manifest["raw_bundle"]).startswith("r3a_ci_2probes_")
    assert manifest["raw_bundle_archive_root"] == "r3a_ci_raw"
    assert manifest["raw_bundle_codec"] in {"zstd", "gzip"}
    assert manifest["producer_config_hash"] == manifest["packager_config_hash"]
    assert manifest["packager_config_hash"] == load_campaign_config(CONFIG).config_hash
    assert "--mode ci" in manifest["reproduction"]
    assert "--probe P1_DEEP_COMPLETE" in manifest["reproduction"]
    assert "--probe P3_INNER_INCOMPLETE" in manifest["reproduction"]
    assert manifest["git"] == manifest["producer_git"]
    assert "packager_git" in manifest


def test_full_closeout_refuses_smoke_subset(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _hashed_raw_campaign(raw, mode="smoke")
    with pytest.raises(ValueError, match="mode='full'"):
        package_r3a_campaign(
            raw_root=raw,
            results_root=tmp_path / "compact",
            bundle_dir=tmp_path / "bundles",
            config_path=CONFIG,
            full_closeout=True,
        )


def test_full_closeout_refuses_missing_producer_git(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _hashed_full_campaign(raw, producer_git=None)
    with pytest.raises(ValueError, match="producer git provenance"):
        package_r3a_campaign(
            raw_root=raw,
            results_root=tmp_path / "compact",
            bundle_dir=tmp_path / "bundles",
            config_path=CONFIG,
            full_closeout=True,
        )


def test_full_closeout_refuses_dirty_producer_tree(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _hashed_full_campaign(raw, producer_git={"git_commit": "a" * 40, "dirty_tree": True})
    with pytest.raises(ValueError, match="clean producer git tree"):
        package_r3a_campaign(
            raw_root=raw,
            results_root=tmp_path / "compact",
            bundle_dir=tmp_path / "bundles",
            config_path=CONFIG,
            full_closeout=True,
        )


def test_strict_campaign_tree_requires_per_probe_artifacts(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    ids = _hashed_full_campaign(raw)
    config = load_campaign_config(CONFIG)
    (raw / ids[0] / "direct_truth.json").unlink()
    with pytest.raises(FileNotFoundError, match="direct_truth"):
        validate_campaign_tree(
            raw,
            ids,
            expected_config_hash=config.config_hash,
            expected_mode="full",
            require_all_stages=True,
        )


def test_synthetic_full_closeout_package_names_all_five_probes(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    results = tmp_path / "compact"
    bundles = tmp_path / "bundles"
    ids = _hashed_full_campaign(raw, producer_git=CLEAN_PRODUCER_GIT)
    manifest = package_r3a_campaign(
        raw_root=raw,
        results_root=results,
        bundle_dir=bundles,
        config_path=CONFIG,
        full_closeout=True,
    )
    bundle = bundles / str(manifest["raw_bundle"])
    assert bundle.is_file()
    assert file_sha256(bundle) == manifest["raw_bundle_sha256"]
    assert manifest["package_kind"] == "full_closeout"
    assert manifest["campaign_mode"] == "full"
    assert manifest["probe_ids"] == list(ids)
    assert manifest["all_configured_probes_present"] is True
    assert manifest["full_closeout_eligible"] is True
    assert manifest["allows_full_campaign_disposition"] is True
    assert manifest["semantic_revalidation"] is True
    assert (
        manifest["recomputed_campaign_blocker"]
        == CampaignBlocker.STITCHING_CONTROL_BLOCKED.value
    )
    assert str(manifest["raw_bundle"]).startswith("r3a_full_all5_")
    assert manifest["raw_bundle_archive_root"] == "r3a_full_raw"
    assert manifest["producer_git"]["git_commit"] == CLEAN_PRODUCER_GIT["git_commit"]
    assert manifest["producer_git"]["dirty_tree"] is False
    assert manifest["git"] == manifest["producer_git"]
    assert "packager_git" in manifest
    assert "--mode full" in manifest["reproduction"]
    assert "--probe" not in manifest["reproduction"]


def test_full_closeout_semantics_recomputes_probe_and_global_blockers(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw"
    ids = _hashed_full_campaign(raw, producer_git=CLEAN_PRODUCER_GIT)
    config = load_campaign_config(CONFIG)
    campaign = json.loads((raw / "campaign.json").read_text(encoding="utf-8"))
    blocker = validate_full_closeout_semantics(
        raw,
        campaign,
        config,
        ids,
        mode="full",
    )
    assert blocker is CampaignBlocker.STITCHING_CONTROL_BLOCKED


def test_full_closeout_semantics_refuses_wrong_global_blocker(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    ids = _hashed_full_campaign(raw, producer_git=CLEAN_PRODUCER_GIT)
    config = load_campaign_config(CONFIG)
    campaign = json.loads((raw / "campaign.json").read_text(encoding="utf-8"))
    campaign["campaign_blocker"] = CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED.value
    (raw / "compare.json").write_text(json_dumps_strict(campaign), encoding="utf-8")
    with pytest.raises(ValueError, match="campaign_blocker does not recompute"):
        validate_full_closeout_semantics(
            raw,
            campaign,
            config,
            ids,
            mode="full",
        )


def test_full_closeout_semantics_refuses_per_probe_drift(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    ids = _hashed_full_campaign(raw, producer_git=CLEAN_PRODUCER_GIT)
    config = load_campaign_config(CONFIG)
    campaign = json.loads((raw / "campaign.json").read_text(encoding="utf-8"))
    path = raw / ids[0] / "comparison.json"
    per_probe = json.loads(path.read_text(encoding="utf-8"))
    per_probe["campaign_blocker"] = CampaignBlocker.NATURAL_DECOMPOSITION_BLOCKED.value
    path.write_text(json.dumps(per_probe), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match the embedded campaign record"):
        validate_full_closeout_semantics(
            raw,
            campaign,
            config,
            ids,
            mode="full",
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
