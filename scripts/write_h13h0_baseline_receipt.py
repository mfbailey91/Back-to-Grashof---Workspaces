#!/usr/bin/env python3
"""Write the H13H-0 baseline identity and invariant receipt.

Reads the existing gitignored H13G pilot. Does not rerun continuation, alter
solver behavior, or replace the H12 hub. A dirty historical producer stays
labeled as that historical pilot.
"""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    config_sha256,
    file_sha256,
    load_campaign_config,
)

H13G_IMPLEMENTATION_SHA = "81f1e2059040b74e503d166f4e6588922ddafb8c"
LOCKED_H12_BUNDLE_SHA256 = (
    "d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec"
)
PROBE_ORDER = (
    "P1_DEEP_COMPLETE",
    "P4_OUTER_COMPLETE",
    "P5_OUTER_INCOMPLETE",
)
CONFIGURED_PROBES = (
    "P1_DEEP_COMPLETE",
    "P2_INNER_COMPLETE",
    "P3_INNER_INCOMPLETE",
    "P4_OUTER_COMPLETE",
    "P5_OUTER_INCOMPLETE",
)
RAW_RELATIVE = Path("outputs/r3a_h13g_source_pilot")
COMPACT_RELATIVE = Path("outputs/r3a_h13g_source_pilot_compact")
BUNDLE_DIR_RELATIVE = Path("outputs/r3a_campaign_bundles")
RECEIPT_JSON_RELATIVE = Path("results/l5_reconstruction/h13h/h13h0_baseline_receipt.json")
RECEIPT_MD_RELATIVE = Path("docs/methods/R3A_H13H_BASELINE_RECEIPT.md")
PROTECTED_CONFIGS = (
    ("h12", Path("configs/l5_positive_control_v1.json")),
    ("h13e", Path("configs/l5_positive_control_h13_source_pilot_v1.json")),
    ("h13f", Path("configs/l5_positive_control_h13_source_v1.json")),
    ("h13g", Path("configs/l5_positive_control_h13g_source_pilot_v1.json")),
)
HUB_RELATIVE = Path("results/l5_reconstruction/r3a/compact_manifest.json")
METRIC_KEYS = (
    "missed_covered_fraction",
    "missed_covered_fraction_state",
    "false_positive_fraction",
    "false_positive_fraction_state",
    "hausdorff_rad",
    "hausdorff_rad_state",
    "max_cell_diameter_rad",
    "refinement_delta",
    "refinement_delta_state",
    "strict_covered_count",
    "strict_uncovered_count",
    "reconstructed_hit_count",
)
INSPECTION_PACKAGES = ("numpy", "scipy", "matplotlib", "pillow")


class ReceiptError(RuntimeError):
    """The located pilot or protected evidence failed a baseline check."""


def _git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def _git_text(args: list[str]) -> str:
    return _git(args).stdout.strip()


def _blob_exists(rev: str, path: str) -> bool:
    return _git(["cat-file", "-e", f"{rev}:{path}"], check=False).returncode == 0


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReceiptError(f"{path} is not a JSON object")
    return payload


def _dir_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _mtime_span(path: Path) -> dict[str, str]:
    stamps = [item.stat().st_mtime for item in path.rglob("*") if item.is_file()]
    if not stamps:
        raise ReceiptError(f"{path} has no files")

    def _iso(stamp: float) -> str:
        return datetime.fromtimestamp(stamp).astimezone().isoformat(timespec="seconds")

    return {"earliest": _iso(min(stamps)), "latest": _iso(max(stamps))}


def _index_mismatches(root: Path) -> list[str]:
    index = _read_json(root / "artifact_index.json")
    files = index.get("files")
    if not isinstance(files, dict):
        raise ReceiptError(f"{root / 'artifact_index.json'} files field is not an object")
    mismatches: list[str] = []
    for relative, expected in sorted(files.items()):
        path = root / relative
        if not path.is_file():
            mismatches.append(f"missing:{relative}")
            continue
        actual = file_sha256(path)
        if actual != expected:
            mismatches.append(f"hash:{relative}")
    return mismatches


def _config_record(relative: Path) -> dict[str, Any]:
    path = ROOT / relative
    raw = json.loads(path.read_text(encoding="utf-8"))
    loaded = load_campaign_config(path)
    canonical = config_sha256(raw)
    if loaded.config_hash != canonical:
        raise ReceiptError(f"{relative} loader hash differs from canonical JSON hash")
    return {
        "path": relative.as_posix(),
        "file_sha256": file_sha256(path),
        "config_hash": canonical,
        "schema_version": loaded.schema_version,
        "full_allows_campaign_disposition": loaded.mode("full").allows_full_campaign_disposition,
    }


def collect_protected(repo: Path | None = None) -> dict[str, Any]:
    """Protected config and H12 hub identities. Independent of the H13G pilot tree."""

    del repo
    configs = {name: _config_record(relative) for name, relative in PROTECTED_CONFIGS}
    hub_path = ROOT / HUB_RELATIVE
    hub = _read_json(hub_path)
    if hub.get("raw_bundle_sha256") != LOCKED_H12_BUNDLE_SHA256:
        raise ReceiptError("H12 hub raw-bundle digest differs from the locked value")
    if hub.get("package_kind") != "full_closeout":
        raise ReceiptError("H12 hub package_kind is no longer full_closeout")
    if hub.get("campaign_blocker") != "STITCHING_CONTROL_BLOCKED":
        raise ReceiptError("H12 hub blocker changed")
    if hub.get("accepted_reconstruction") is not False:
        raise ReceiptError("H12 hub accepted_reconstruction changed")
    return {
        "configs": configs,
        "h12_hub": {
            "path": HUB_RELATIVE.as_posix(),
            "file_sha256": file_sha256(hub_path),
            "raw_bundle_sha256": hub["raw_bundle_sha256"],
            "config_hash": hub.get("config_hash"),
            "package_kind": hub.get("package_kind"),
            "campaign_mode": hub.get("campaign_mode"),
            "campaign_blocker": hub.get("campaign_blocker"),
            "accepted_reconstruction": hub.get("accepted_reconstruction"),
            "semantic_revalidation": hub.get("semantic_revalidation"),
            "producer_git_commit": (hub.get("producer_git") or {}).get("git_commit"),
            "probe_ids": hub.get("probe_ids"),
        },
    }


def _cell_diameters(hausdorff: object, diameter: object) -> float | None:
    if not isinstance(hausdorff, (int, float)) or not isinstance(diameter, (int, float)):
        return None
    if isinstance(hausdorff, bool) or isinstance(diameter, bool) or diameter == 0:
        return None
    return float(hausdorff) / float(diameter)


def _metric_view(blob: Mapping[str, Any]) -> dict[str, Any]:
    view = {key: blob.get(key) for key in METRIC_KEYS}
    view["hausdorff_in_cell_diameters"] = _cell_diameters(
        blob.get("hausdorff_rad"),
        blob.get("max_cell_diameter_rad"),
    )
    for grid in ("fine", "coarse"):
        grid_blob = blob.get(grid)
        if not isinstance(grid_blob, Mapping):
            view[grid] = None
            continue
        grid_view = {key: grid_blob.get(key) for key in METRIC_KEYS}
        grid_view["hausdorff_in_cell_diameters"] = _cell_diameters(
            grid_blob.get("hausdorff_rad"),
            grid_blob.get("max_cell_diameter_rad"),
        )
        view[grid] = grid_view
    return view


def _count_flags(records: list[Mapping[str, Any]], key: str) -> int:
    return sum(1 for item in records if item.get(key) is True)


def _probe_summary(raw_root: Path, compact_root: Path, probe_id: str) -> dict[str, Any]:
    source = _read_json(raw_root / probe_id / "source_control.json")
    comparison = _read_json(raw_root / probe_id / "comparison.json")
    records = [item for item in source.get("c_records") or [] if isinstance(item, Mapping)]
    required = [item for item in records if item.get("required") is True]
    boundary = [item for item in records if item.get("required") is not True]
    fibers = [item for item in source.get("fibers") or [] if isinstance(item, Mapping)]
    terminations: Counter[str] = Counter()
    for item in records:
        counts = item.get("closure_kind_counts")
        if isinstance(counts, Mapping):
            for kind, count in counts.items():
                terminations[str(kind)] += int(count)
    sample = fibers[0].get("rasterized_pointing_samples") if fibers else None
    sample_kind = "absent"
    if isinstance(sample, list) and sample and isinstance(sample[0], list):
        sample_kind = "direction_vectors"
    elif isinstance(sample, list):
        sample_kind = type(sample[0]).__name__ if sample else "empty"
    columns = {
        name: _metric_view(comparison[name])
        for name in ("direct_vs_oracle", "source_vs_direct", "source_vs_oracle")
        if isinstance(comparison.get(name), Mapping)
    }
    return {
        "probe_id": probe_id,
        "policy_version": (source.get("policy") or {}).get("policy_version"),
        "serialized_policy": source.get("policy"),
        "requested_c_value_count": source.get("requested_c_value_count"),
        "effective_c_value_count": source.get("effective_c_value_count"),
        "certificate_status": source.get("certificate_status"),
        "raw_pointing_sample_count": source.get("raw_pointing_sample_count"),
        "rasterized_pointing_sample_count": source.get("rasterized_pointing_sample_count"),
        "hit_cell_count": source.get("hit_cell_count"),
        "unresolved_c_intervals": source.get("unresolved_c_intervals"),
        "required_bin_count": len(required),
        "nonrequired_bin_count": len(boundary),
        "required_bin_status_counts": dict(
            sorted(Counter(str(item.get("parameter_interval_status")) for item in required).items())
        ),
        "nonrequired_bin_status_counts": dict(
            sorted(Counter(str(item.get("parameter_interval_status")) for item in boundary).items())
        ),
        "explained_projected_seed_count": sum(
            int(item.get("explained_projected_seed_count") or 0) for item in required
        ),
        "unexplained_projected_seed_count": sum(
            int(item.get("unexplained_projected_seed_count") or 0) for item in required
        ),
        "required_bins_candidate_budget_exhausted": _count_flags(required, "candidate_budget_exhausted"),
        "required_bins_trace_budget_exhausted": _count_flags(required, "trace_budget_exhausted"),
        "required_bins_seed_budget_exhausted": _count_flags(required, "seed_budget_exhausted"),
        "required_bins_with_incomplete_raster": sum(
            1 for item in required if int(item.get("rasterization_incomplete_count") or 0) > 0
        ),
        "required_rasterization_incomplete_count": sum(
            int(item.get("rasterization_incomplete_count") or 0) for item in required
        ),
        "fiber_count": len(fibers),
        "fiber_termination_counts": dict(
            sorted(Counter(str(item.get("termination_status")) for item in fibers).items())
        ),
        "positive_ray_termination_counts": dict(
            sorted(Counter(str(item.get("positive_ray_termination")) for item in fibers).items())
        ),
        "negative_ray_termination_counts": dict(
            sorted(Counter(str(item.get("negative_ray_termination")) for item in fibers).items())
        ),
        "fibers_rasterization_complete": sum(1 for item in fibers if item.get("rasterization_complete") is True),
        "fibers_rasterization_incomplete": sum(
            1 for item in fibers if item.get("rasterization_complete") is False
        ),
        "fibers_rasterization_budget_exhausted": sum(
            1 for item in fibers if item.get("rasterization_budget_exhausted") is True
        ),
        "rasterization_failure_count": sum(int(item.get("rasterization_failure_count") or 0) for item in fibers),
        "closure_kind_counts": dict(sorted(terminations.items())),
        "serialized_fiber_fields": sorted(fibers[0].keys()) if fibers else [],
        "rasterized_sample_kind": sample_kind,
        "per_step_branch_trace_serialized": False,
        "direct_complete": comparison.get("direct_complete"),
        "oracle_complete": comparison.get("oracle_complete"),
        "disposition": comparison.get("disposition"),
        "campaign_blocker": comparison.get("campaign_blocker"),
        "failure_localization": comparison.get("failure_localization"),
        "columns": columns,
        "source_control_file_sha256": file_sha256(raw_root / probe_id / "source_control.json"),
        "comparison_file_sha256": file_sha256(raw_root / probe_id / "comparison.json"),
        "compact_source_control_byte_identical": file_sha256(raw_root / probe_id / "source_control.json")
        == file_sha256(compact_root / probe_id / "source_control.json"),
        "compact_comparison_byte_identical": file_sha256(raw_root / probe_id / "comparison.json")
        == file_sha256(compact_root / probe_id / "comparison.json"),
    }


def _full_mode_settings(config_path: Path) -> dict[str, Any]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    source = raw["source_control"]
    full = raw["campaign_modes"]["full"]
    resolved = {
        "policy_version": source["policy_version"],
        "c_domain_policy": source["c_domain_policy"],
        "c_slice_max_angular_spacing_cell_fraction": source["c_slice_max_angular_spacing_cell_fraction"],
        "continuation_step_size": source["continuation_step_size"],
        "continuation_steps": full["continuation_steps"],
        "curve_segment_fraction": source["curve_segment_fraction"],
        "kinematic_refinement_max_depth": source["kinematic_refinement_max_depth"]["full"],
        "max_seed_candidates_per_c": source["max_seed_candidates_per_c"]["full"],
        "max_source_traces_per_c": source["max_source_traces_per_c"]["full"],
        "dedup_q_tol_rad": source["dedup_q_tol_rad"],
        "trace_cover_q_tol_rad": source["trace_cover_q_tol_rad"],
        "endpoint_state_tol_rad": source["endpoint_state_tol_rad"],
        "endpoint_tangent_abs_dot_min": source["endpoint_tangent_abs_dot_min"],
        "source_c_value_count": full["source_c_value_count"],
        "confirmation_icosphere_level": full["confirmation_icosphere_level"],
        "discovery_icosphere_level": full["discovery_icosphere_level"],
        "allows_full_campaign_disposition": full["allows_full_campaign_disposition"],
        "max_refinement_metric_delta": raw["set_acceptance"]["max_refinement_metric_delta"],
        "max_hausdorff_in_confirmation_cell_diameters": raw["set_acceptance"][
            "max_hausdorff_in_confirmation_cell_diameters"
        ],
        "max_missed_strict_covered_fraction": raw["set_acceptance"]["max_missed_strict_covered_fraction"],
        "max_strict_false_positive_fraction": raw["set_acceptance"]["max_strict_false_positive_fraction"],
    }
    return resolved


def collect_historical_pilot(repo: Path | None = None) -> dict[str, Any]:
    """Validate and summarize the on-disk H13G pilot. Requires the gitignored outputs."""

    del repo
    raw_root = ROOT / RAW_RELATIVE
    compact_root = ROOT / COMPACT_RELATIVE
    if not raw_root.is_dir() or not compact_root.is_dir():
        raise ReceiptError("historical H13G raw pilot or compact package is absent")
    campaign = _read_json(raw_root / "campaign.json")
    manifest = _read_json(raw_root / "manifest.json")
    compact = _read_json(compact_root / "compact_manifest.json")
    h13g_config = ROOT / PROTECTED_CONFIGS[-1][1]
    config_hash = config_sha256(json.loads(h13g_config.read_text(encoding="utf-8")))
    producer = campaign.get("git") if isinstance(campaign.get("git"), dict) else {}
    bundle_name = str(compact.get("raw_bundle") or "")
    bundle_path = ROOT / BUNDLE_DIR_RELATIVE / bundle_name
    problems: list[str] = []
    if campaign.get("config_hash") != config_hash:
        problems.append("campaign config_hash differs from the committed H13G config")
    if compact.get("config_hash") != config_hash:
        problems.append("compact config_hash differs from the committed H13G config")
    if campaign.get("mode") != "full" or compact.get("campaign_mode") != "full":
        problems.append("pilot mode is not full")
    if campaign.get("schema_version") != "r3a_l5_positive_control_h13g_source_pilot_v1":
        problems.append("campaign schema_version differs")
    if campaign.get("probe_ids") != list(PROBE_ORDER):
        problems.append("campaign probe scope is not P1/P4/P5")
    if manifest.get("probe_ids") != list(CONFIGURED_PROBES):
        problems.append("manifest probe list is not the configured five-probe order")
    if compact.get("probe_ids") != list(PROBE_ORDER):
        problems.append("compact probe scope is not P1/P4/P5")
    if compact.get("package_kind") != "diagnostic":
        problems.append("compact package_kind is not diagnostic")
    if compact.get("allows_full_campaign_disposition") is not False:
        problems.append("compact package allows a full campaign disposition")
    if compact.get("accepted_reconstruction") is not False or campaign.get("accepted_reconstruction") is not False:
        problems.append("pilot records accepted_reconstruction")
    if campaign.get("campaign_blocker") != "STITCHING_CONTROL_BLOCKED":
        problems.append("campaign blocker is not STITCHING_CONTROL_BLOCKED")
    if producer.get("git_commit") != "b42823699ab6332d6f81e9a522394d533e592c6a":
        problems.append("producer commit differs from the recorded historical value")
    if producer.get("dirty_tree") is not True:
        problems.append("producer dirty_tree flag is not true")
    raw_mismatches = _index_mismatches(raw_root)
    compact_mismatches = _index_mismatches(compact_root)
    if raw_mismatches:
        problems.append("raw artifact index mismatches: " + ",".join(raw_mismatches[:8]))
    if compact_mismatches:
        problems.append("compact artifact index mismatches: " + ",".join(compact_mismatches[:8]))
    if not bundle_path.is_file():
        problems.append("recorded raw bundle file is absent")
        bundle_sha = None
    else:
        bundle_sha = file_sha256(bundle_path)
        if bundle_sha != compact.get("raw_bundle_sha256"):
            problems.append("raw bundle bytes differ from compact_manifest raw_bundle_sha256")
    if problems:
        raise ReceiptError("; ".join(problems))

    settings = _full_mode_settings(h13g_config)
    probes = [_probe_summary(raw_root, compact_root, probe_id) for probe_id in PROBE_ORDER]
    policies = [probe["serialized_policy"] for probe in probes]
    if any(policy != policies[0] for policy in policies):
        raise ReceiptError("probe serialized source policies differ")
    for key in (
        "policy_version",
        "c_slice_max_angular_spacing_cell_fraction",
        "continuation_step_size",
        "curve_segment_fraction",
        "kinematic_refinement_max_depth",
        "max_seed_candidates_per_c",
        "max_source_traces_per_c",
        "dedup_q_tol_rad",
        "trace_cover_q_tol_rad",
        "endpoint_state_tol_rad",
        "endpoint_tangent_abs_dot_min",
    ):
        if policies[0].get(key) != settings[key]:
            raise ReceiptError(f"serialized policy {key} differs from the committed full-mode config")
    return {
        "classification": "historical_dirty_producer",
        "fresh_reproduction": False,
        "clean_h13g_checkout": False,
        "raw_root": RAW_RELATIVE.as_posix(),
        "compact_root": COMPACT_RELATIVE.as_posix(),
        "raw_bytes": _dir_bytes(raw_root),
        "compact_bytes": _dir_bytes(compact_root),
        "raw_filesystem_mtime_span": _mtime_span(raw_root),
        "compact_filesystem_mtime_span": _mtime_span(compact_root),
        "solver_wall_time_s": None,
        "solver_wall_time_status": "unavailable",
        "historical_dependency_versions": "unavailable",
        "campaign_config_hash": campaign["config_hash"],
        "campaign_mode": campaign["mode"],
        "campaign_schema_version": campaign["schema_version"],
        "campaign_probe_ids": campaign["probe_ids"],
        "manifest_probe_ids": manifest["probe_ids"],
        "manifest_stage": manifest.get("stage"),
        "campaign_blocker": campaign["campaign_blocker"],
        "accepted_reconstruction": False,
        "producer_git_commit": producer["git_commit"],
        "producer_dirty_tree": True,
        "producer_is_parent_of_h13g": True,
        "dirty_diff": "unavailable",
        "package_kind": compact["package_kind"],
        "allows_full_campaign_disposition": False,
        "full_closeout_eligible": compact.get("full_closeout_eligible"),
        "semantic_revalidation": compact.get("semantic_revalidation"),
        "recomputed_campaign_blocker": compact.get("recomputed_campaign_blocker"),
        "compact_manifest_sha256": file_sha256(compact_root / "compact_manifest.json"),
        "raw_bundle": bundle_name,
        "raw_bundle_sha256": bundle_sha,
        "raw_bundle_bytes": bundle_path.stat().st_size,
        "raw_artifact_index_entries": len(_read_json(raw_root / "artifact_index.json")["files"]),
        "compact_artifact_index_entries": len(_read_json(compact_root / "artifact_index.json")["files"]),
        "artifact_indexes_match_files": True,
        "declared_full_mode_settings": settings,
        "natural_family_artifacts_present": all(
            (raw_root / probe_id / "natural_family.json").is_file() for probe_id in PROBE_ORDER
        ),
        "natural_family_interpreted": False,
        "probes": probes,
        "missing_historical_detail": [
            "exact dirty working-tree diff at the producer commit",
            "solver wall-clock runtime",
            "historical Python and dependency versions",
            "per-step BranchTrace history",
            "corrected raster segment configurations",
        ],
    }


def collect_inspection() -> dict[str, Any]:
    tracked = _git_text(["status", "--porcelain", "--untracked-files=no"])
    untracked = _git(["status", "--porcelain", "--untracked-files=normal"], check=True).stdout
    untracked_count = sum(1 for line in untracked.splitlines() if line.startswith("??"))
    versions: dict[str, str] = {}
    for dist in INSPECTION_PACKAGES:
        try:
            versions[dist] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            versions[dist] = "unavailable"
    remote_main = _git_text(["rev-parse", "origin/main"])
    remote_feature = _git_text(["rev-parse", "origin/R3A_H13_locked_invariants"])
    h13g_parent = _git_text(["rev-parse", f"{H13G_IMPLEMENTATION_SHA}^"])
    main_parents = _git_text(["log", "-1", "--format=%P", remote_main]).split()
    h13g_in_main = _git(
        ["merge-base", "--is-ancestor", H13G_IMPLEMENTATION_SHA, remote_main],
        check=False,
    ).returncode == 0
    h13g_in_head = _git(
        ["merge-base", "--is-ancestor", H13G_IMPLEMENTATION_SHA, "HEAD"],
        check=False,
    ).returncode == 0
    if not h13g_in_head:
        raise ReceiptError("HEAD does not contain the H13G implementation commit")
    source_path = "src/grashof_workspace/spatial_experiments/l5_reconstruction/source_control_h13g.py"
    return {
        "branch": _git_text(["rev-parse", "--abbrev-ref", "HEAD"]),
        "head_sha": _git_text(["rev-parse", "HEAD"]),
        "h13g_implementation_sha": H13G_IMPLEMENTATION_SHA,
        "h13g_parent_sha": h13g_parent,
        "h13g_is_ancestor_of_head": True,
        "tracked_worktree_dirty": bool(tracked),
        "untracked_path_count": untracked_count,
        "python": sys.version.split()[0],
        "inspection_dependency_versions": versions,
        "origin_main_sha": remote_main,
        "origin_main_parents": main_parents,
        "origin_main_subject": _git_text(["log", "-1", "--format=%s", remote_main]),
        "origin_feature_sha": remote_feature,
        "h13g_is_ancestor_of_origin_main": h13g_in_main,
        "h13g_commit_contains_source_control_h13g": _blob_exists(H13G_IMPLEMENTATION_SHA, source_path),
        "h13g_parent_contains_source_control_h13g": _blob_exists(h13g_parent, source_path),
        "inspected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def build_receipt() -> dict[str, Any]:
    inspection = collect_inspection()
    protected = collect_protected()
    pilot = collect_historical_pilot()
    if inspection["h13g_is_ancestor_of_origin_main"]:
        raise ReceiptError("ancestry check found H13G inside origin/main; receipt assumptions changed")
    if inspection["h13g_parent_sha"] != pilot["producer_git_commit"]:
        raise ReceiptError("pilot producer is not the parent of the H13G commit")
    if not inspection["h13g_commit_contains_source_control_h13g"]:
        raise ReceiptError("H13G commit is missing source_control_h13g.py")
    if inspection["h13g_parent_contains_source_control_h13g"]:
        raise ReceiptError("parent commit already contains source_control_h13g.py")
    return {
        "schema_version": "r3a_h13h0_baseline_receipt_v1",
        "sprint": "R3A-H13H",
        "work_package": "H13H-0",
        "source_policy_validated": False,
        "accepted_reconstruction": False,
        "h12_hub_replaced": False,
        "inspection": inspection,
        "protected": protected,
        "historical_pilot": pilot,
    }


def _fmt(value: object) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def _md_table(headers: list[str], rows: list[list[object]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(_fmt(cell) for cell in row) + " |" for row in rows]
    return "\n".join([head, rule, *body])


def render_markdown(receipt: Mapping[str, Any]) -> str:
    inspection = receipt["inspection"]
    protected = receipt["protected"]
    pilot = receipt["historical_pilot"]
    hub = protected["h12_hub"]
    config_rows = [
        [
            name,
            item["schema_version"],
            item["config_hash"],
            item["file_sha256"],
            item["full_allows_campaign_disposition"],
        ]
        for name, item in protected["configs"].items()
    ]
    probe_rows = []
    status_rows = []
    raster_rows = []
    for probe in pilot["probes"]:
        source = probe["columns"]["source_vs_direct"]
        direct = probe["columns"]["direct_vs_oracle"]
        probe_rows.append(
            [
                probe["probe_id"],
                probe["direct_complete"],
                probe["oracle_complete"],
                direct["missed_covered_fraction"],
                direct["hausdorff_rad"],
                direct["refinement_delta"],
                source["missed_covered_fraction"],
                source["hausdorff_in_cell_diameters"],
                source["false_positive_fraction_state"]
                if source["false_positive_fraction"] is None
                else source["false_positive_fraction"],
                source["refinement_delta"],
                probe["campaign_blocker"],
            ]
        )
        status_rows.append(
            [
                probe["probe_id"],
                probe["required_bin_count"],
                probe["required_bin_status_counts"],
                probe["unexplained_projected_seed_count"],
                probe["explained_projected_seed_count"],
                probe["required_bins_candidate_budget_exhausted"],
                probe["required_bins_trace_budget_exhausted"],
                probe["required_bins_seed_budget_exhausted"],
            ]
        )
        raster_rows.append(
            [
                probe["probe_id"],
                probe["fiber_count"],
                probe["fiber_termination_counts"],
                probe["fibers_rasterization_incomplete"],
                probe["fibers_rasterization_budget_exhausted"],
                probe["rasterization_failure_count"],
                probe["required_bins_with_incomplete_raster"],
                probe["effective_c_value_count"],
            ]
        )
    missing = "\n".join(f"- {item}" for item in pilot["missing_historical_detail"])
    settings = pilot["declared_full_mode_settings"]
    source_columns_match = all(
        probe["columns"]["source_vs_direct"] == probe["columns"]["source_vs_oracle"]
        for probe in pilot["probes"]
    )
    compact_comparisons_match = all(
        probe["compact_comparison_byte_identical"] for probe in pilot["probes"]
    )
    recomputed = pilot["recomputed_campaign_blocker"]
    recomputed_text = "null" if recomputed is None else _fmt(recomputed)
    if source_columns_match:
        source_column_sentence = (
            "On these three probes the stored `source_vs_oracle` metric view equals "
            "`source_vs_direct`."
        )
    else:
        source_column_sentence = (
            "On these three probes the stored `source_vs_oracle` metric view differs from "
            "`source_vs_direct`. Both views are in the JSON receipt."
        )
    compact_sentence = (
        "Compact comparison files match the raw comparison bytes."
        if compact_comparisons_match
        else "At least one compact comparison file differs from the raw comparison bytes."
    )
    return f"""# R3A-H13H-0 baseline receipt

**Status:** BASELINE RECORDED. Source policy validated: false. `accepted_reconstruction`: false. The H12 hub remains the recorded closeout.

**Authority:** This file is the H13H-0 identity and invariant receipt. [R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the scientific status ledger. Machine-readable copy: [h13h0_baseline_receipt.json](../../results/l5_reconstruction/h13h/h13h0_baseline_receipt.json).

Regenerate from the gitignored historical pilot with:

```bash
PYTHONPATH=src python scripts/write_h13h0_baseline_receipt.py
```

## 1. Baseline identity

| Field | Value |
|---|---|
| Inspection branch | `{inspection["branch"]}` |
| Inspection HEAD | `{inspection["head_sha"]}` |
| H13G implementation | `{inspection["h13g_implementation_sha"]}` |
| H13G parent | `{inspection["h13g_parent_sha"]}` |
| `origin/main` | `{inspection["origin_main_sha"]}` |
| `origin/main` parents | `{" ".join(inspection["origin_main_parents"])}` |
| `origin/main` subject | {inspection["origin_main_subject"]} |
| `origin/R3A_H13_locked_invariants` | `{inspection["origin_feature_sha"]}` |
| H13G contained in HEAD | {str(inspection["h13g_is_ancestor_of_head"]).lower()} |
| H13G contained in `origin/main` | {str(inspection["h13g_is_ancestor_of_origin_main"]).lower()} |
| Inspection Python | {inspection["python"]} |
| Inspection packages | {", ".join(f"{name} {version}" for name, version in inspection["inspection_dependency_versions"].items())} |
| Inspected at | {inspection["inspected_at"]} |

`origin/main` is merge commit `201b10f7779c671b9da2a8d88e4da83ab8b9cc9e` (PR #22). Its second parent is the H13G parent `{inspection["h13g_parent_sha"]}`. The H13G implementation commit is a later child of that parent on `origin/R3A_H13_locked_invariants`. `source_control_h13g.py` is present at the H13G commit and absent at its parent.

Tracked worktree dirty at inspection: {str(inspection["tracked_worktree_dirty"]).lower()}. Untracked path count: {inspection["untracked_path_count"]}. Those untracked paths stay outside this receipt.

## 2. Historical pilot

Classification: `historical_dirty_producer`.

The raw tree `{pilot["raw_root"]}` and compact tree `{pilot["compact_root"]}` are present. Their artifact indexes match the files on disk. The campaign config hash matches the committed H13G config. Mode is `full`. The compare-stage probe scope is P1/P4/P5. The manifest stage still lists all five configured probes. Package kind is `diagnostic`, `allows_full_campaign_disposition` is false, and `semantic_revalidation` is {str(pilot["semantic_revalidation"]).lower()}.

Producer commit: `{pilot["producer_git_commit"]}` with `dirty_tree=true`. That commit is the parent of H13G. The exact dirty diff is unavailable, so this tree is the historical pilot. A fresh reproduction on a clean H13G checkout was not run.

| Quantity | Value |
|---|---|
| Raw tree bytes | {pilot["raw_bytes"]} |
| Compact tree bytes | {pilot["compact_bytes"]} |
| Raw bundle | `{pilot["raw_bundle"]}` |
| Raw bundle sha256 | `{pilot["raw_bundle_sha256"]}` |
| Raw bundle bytes | {pilot["raw_bundle_bytes"]} |
| Raw filesystem mtime span | {pilot["raw_filesystem_mtime_span"]["earliest"]} to {pilot["raw_filesystem_mtime_span"]["latest"]} |
| Compact filesystem mtime span | {pilot["compact_filesystem_mtime_span"]["earliest"]} to {pilot["compact_filesystem_mtime_span"]["latest"]} |
| Solver wall time | unavailable |
| Historical dependency versions | unavailable |
| Campaign blocker | `{pilot["campaign_blocker"]}` |
| Recomputed campaign blocker | {recomputed_text} |

Filesystem timestamps are archive clock observations. They are not a measured solver runtime.

The historical `--stage all` tree contains natural-family artifacts. This receipt leaves them uninterpreted.

Declared full-mode settings matched by every serialized probe policy: continuation steps {settings["continuation_steps"]}, initial step {settings["continuation_step_size"]}, `c` count minimum {settings["source_c_value_count"]}, `c` spacing fraction {settings["c_slice_max_angular_spacing_cell_fraction"]}, curve fraction {settings["curve_segment_fraction"]}, raster depth {settings["kinematic_refinement_max_depth"]}, candidate budget {settings["max_seed_candidates_per_c"]}, trace budget {settings["max_source_traces_per_c"]}, trace-cover {settings["trace_cover_q_tol_rad"]}, dedup {settings["dedup_q_tol_rad"]}, endpoint tolerance {settings["endpoint_state_tol_rad"]}, endpoint tangent dot {settings["endpoint_tangent_abs_dot_min"]}.

## 3. Protected evidence

{_md_table(["Config", "Schema", "Config hash", "File sha256", "Full mode may dispose"], config_rows)}

H12 hub `{hub["path"]}` file sha256 `{hub["file_sha256"]}`. Raw bundle digest `{hub["raw_bundle_sha256"]}`. Package `{hub["package_kind"]}`, blocker `{hub["campaign_blocker"]}`, accepted reconstruction {str(hub["accepted_reconstruction"]).lower()}, semantic revalidation {str(hub["semantic_revalidation"]).lower()}, producer `{hub["producer_git_commit"]}`.

## 4. Per-probe source baseline

Direct and source columns below are the stored run-level metrics. Hausdorff cell diameters are the stored angular Hausdorff divided by the stored cell diameter. Refinement is the existing within-run coarse/fine metric. The declared refinement limit is {settings["max_refinement_metric_delta"]}.

{_md_table(["Probe", "Direct complete", "Oracle complete", "Direct miss", "Direct Hausdorff", "Direct refinement", "Source miss", "Source Hausdorff diameters", "Source false positive", "Source refinement", "Blocker"], probe_rows)}

`oracle_complete` is the stored comparison flag. P5 remains the outer-incomplete probe. {source_column_sentence}

{_md_table(["Probe", "Required bins", "Required status counts", "Unexplained representatives", "Explained representatives", "Candidate-cap bins", "Trace-cap bins", "Seed-cap bins"], status_rows)}

{_md_table(["Probe", "Fibers", "Termination counts", "Incomplete raster fibers", "Raster budget exhausted", "Raster failure count", "Required bins with incomplete raster", "Effective c count"], raster_rows)}

Required-bin cap flags above count discovery and trace allocation caps. Fiber `BUDGET_EXHAUSTED` counts are continuation termination, recorded separately in the termination column. Non-required bins retain status `CRITICAL_OR_BOUNDARY`. Serialized fibers contain accepted samples, ray termination, and raster counts. Per-step branch history and corrected raster configurations are absent. Compact `source_control.json` files are smaller than the raw files. {compact_sentence}

## 5. Unavailable historical detail

{missing}

## 6. Exit

Baseline identity, protected hashes, and the hash-checked historical pilot are recorded. The clean-SHA reproduction remains unrun because the historical raw tree was available and its producer diff is the missing detail, not the tree itself. Source-policy validation remains future H13H work.
"""


def main() -> None:
    receipt = build_receipt()
    json_path = ROOT / RECEIPT_JSON_RELATIVE
    md_path = ROOT / RECEIPT_MD_RELATIVE
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(receipt), encoding="utf-8")
    print(f"wrote {json_path.relative_to(ROOT)}")
    print(f"wrote {md_path.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except ReceiptError as exc:
        print(f"H13H-0 receipt failed: {exc}", file=sys.stderr)
        sys.exit(1)
