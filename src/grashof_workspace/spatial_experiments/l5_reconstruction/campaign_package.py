"""Compact R3A campaign evidence and content-addressed raw bundles."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import tarfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .artifacts import (
    rebuild_artifact_index,
    reseal_campaign_summaries,
    validate_campaign_tree,
    validate_stage_output_refs,
)
from .models import (
    CampaignBlocker,
    CampaignConfig,
    file_sha256,
    git_provenance,
    json_dumps_strict,
    load_campaign_config,
)

PACKAGE_DIAGNOSTIC = "diagnostic"
PACKAGE_FULL_CLOSEOUT = "full_closeout"

COMPACT_STAGE_FILES = (
    "manifest.json",
    "fixture.json",
    "truth.json",
    "source_control.json",
    "leaves.json",
    "campaign.json",
    "compare.json",
    "render.json",
    "index.html",
    "five_point_summary.png",
)

COMMITTED_HUB_REFUSE = (
    "refusing to replace git-tracked results {path}; pass --replace-committed after the "
    "raw tree has been hashed and bundled"
)


def _read_json(path: Path) -> dict[str, Any]:
    blob = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(blob, dict):
        raise TypeError(f"{path} is not a JSON object")
    return blob


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps_strict(dict(payload)), encoding="utf-8")


def validate_package_scope(
    campaign: Mapping[str, Any],
    config: CampaignConfig,
    *,
    full_closeout: bool,
) -> tuple[str, tuple[str, ...], bool]:
    """Return the declared run scope, refusing a mislabeled closeout package."""

    campaign_hash = str(campaign.get("config_hash", ""))
    if campaign_hash != config.config_hash:
        raise ValueError(
            f"campaign config-hash drift: expected {config.config_hash}, got {campaign_hash}"
        )
    mode = str(campaign.get("mode", ""))
    if mode not in config.modes:
        raise ValueError(f"campaign.json has unsupported mode {mode!r}")

    raw_probe_ids = campaign.get("probe_ids")
    if not isinstance(raw_probe_ids, list) or not raw_probe_ids:
        raise ValueError("campaign.json must declare a nonempty probe_ids list")
    probe_ids = tuple(str(item) for item in raw_probe_ids)
    if len(set(probe_ids)) != len(probe_ids):
        raise ValueError(f"campaign.json contains duplicate probe IDs: {probe_ids}")

    configured = tuple(probe.probe_id for probe in config.probes)
    unknown = tuple(pid for pid in probe_ids if pid not in configured)
    if unknown:
        raise ValueError(f"campaign.json contains unknown probe IDs: {unknown}")
    all_configured = probe_ids == configured

    if full_closeout:
        if mode != "full":
            raise ValueError(f"full closeout requires mode='full', got {mode!r}")
        if not all_configured:
            raise ValueError(
                "full closeout requires all configured probes in order: "
                f"{configured}, got {probe_ids}"
            )
        if not config.mode(mode).allows_full_campaign_disposition:
            raise ValueError("selected mode cannot issue a full-campaign disposition")
        blocker = campaign.get("campaign_blocker")
        valid_blockers = {item.value for item in CampaignBlocker}
        if blocker not in valid_blockers:
            raise ValueError("full closeout requires one explicit CampaignBlocker outcome")
        accepted = bool(campaign.get("accepted_reconstruction"))
        if accepted and blocker != CampaignBlocker.CONTROLLED_COVER_ACCEPTED.value:
            raise ValueError("accepted reconstruction requires CONTROLLED_COVER_ACCEPTED")
        if not accepted and blocker == CampaignBlocker.CONTROLLED_COVER_ACCEPTED.value:
            raise ValueError("CONTROLLED_COVER_ACCEPTED requires accepted_reconstruction=true")

    return mode, probe_ids, all_configured


def build_reproduction_command(
    *,
    config_path: Path,
    raw_root: Path,
    mode: str,
    probe_ids: Sequence[str],
    all_configured: bool,
) -> str:
    parts = [
        "python",
        "-m",
        "grashof_workspace.spatial_experiments.l5_reconstruction.cli",
        "--config",
        str(config_path),
        "--outdir",
        str(raw_root),
        "--stage",
        "all",
        "--mode",
        mode,
    ]
    if not all_configured:
        for probe_id in probe_ids:
            parts.extend(("--probe", probe_id))
    return "PYTHONPATH=src " + shlex.join(parts)


def _producer_git(campaign: Mapping[str, Any]) -> dict[str, Any]:
    raw = campaign.get("git")
    if not isinstance(raw, Mapping):
        return {"git_commit": None, "dirty_tree": None}
    return {str(key): value for key, value in raw.items()}


def compact_truth_split(blob: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(blob, dict):
        return None
    solves = blob.get("solves")
    out = {key: value for key, value in blob.items() if key != "solves"}
    out["solve_count"] = len(solves) if isinstance(solves, list) else 0
    out["solves_omitted"] = True
    return out


def compact_direct_truth(blob: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(blob)
    payload["discovery"] = compact_truth_split(blob.get("discovery") if isinstance(blob.get("discovery"), dict) else None)
    payload["confirmation"] = compact_truth_split(
        blob.get("confirmation") if isinstance(blob.get("confirmation"), dict) else None
    )
    return payload


def _compact_leaf(leaf: Mapping[str, Any], *, keep_samples: int = 3) -> dict[str, Any]:
    samples = list(leaf.get("samples") or []) if isinstance(leaf.get("samples"), list) else []
    compact = {key: value for key, value in leaf.items() if key != "samples"}
    compact["sample_count"] = len(samples)
    compact["samples"] = samples[:keep_samples]
    compact["samples_truncated"] = len(samples) > keep_samples
    return compact


def compact_natural_family(blob: Mapping[str, Any]) -> dict[str, Any]:
    leaves = list(blob.get("leaves") or []) if isinstance(blob.get("leaves"), list) else []
    accepted = [item for item in leaves if isinstance(item, dict) and item.get("accepted_for_reconstruction")]
    excluded = [item for item in leaves if isinstance(item, dict) and not item.get("accepted_for_reconstruction")]
    reps: list[dict[str, Any]] = []
    if accepted:
        reps.append(_compact_leaf(accepted[0]))
    if excluded:
        reps.append(_compact_leaf(excluded[0]))
    payload = {key: value for key, value in blob.items() if key != "leaves"}
    payload["leaves"] = reps
    payload["leaf_count"] = len(leaves)
    payload["raw_leaves_omitted"] = True
    return payload


def compact_source_control(blob: Mapping[str, Any]) -> dict[str, Any]:
    fibers_out: list[dict[str, Any]] = []
    for fiber in blob.get("fibers") or []:
        if not isinstance(fiber, dict):
            continue
        q_samples = fiber.get("q_samples") or []
        compact_fiber = {key: value for key, value in fiber.items() if key not in {"q_samples", "pointing_samples"}}
        compact_fiber["sample_count"] = compact_fiber.get(
            "sample_count", len(q_samples) if isinstance(q_samples, list) else 0
        )
        compact_fiber["q_samples_omitted"] = True
        fibers_out.append(compact_fiber)
    payload = {key: value for key, value in blob.items() if key not in {"fibers", "pointing_samples"}}
    payload["fibers"] = fibers_out
    payload["pointing_samples_omitted"] = True
    return payload


def write_raw_bundle(
    raw_root: Path,
    bundle_dir: Path,
    *,
    config_hash: str,
    producer_git_sha: str,
    mode: str,
    probe_ids: Sequence[str],
    all_configured: bool,
) -> tuple[Path, str, str]:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    scope = f"all{len(probe_ids)}" if all_configured else f"{len(probe_ids)}probes"
    stem = f"r3a_{mode}_{scope}_{config_hash}_{producer_git_sha}"
    archive_root = f"r3a_{mode}_raw"
    zstd = shutil.which("zstd")
    if zstd is not None:
        tar_path = bundle_dir / f"{stem}.tar"
        dest = bundle_dir / f"{stem}.tar.zst"
        with tarfile.open(tar_path, "w") as tar:
            tar.add(raw_root, arcname=archive_root)
        subprocess.check_call([zstd, "-f", "-q", "-o", str(dest), str(tar_path)])
        tar_path.unlink(missing_ok=True)
        return dest, file_sha256(dest), "zstd"
    dest = bundle_dir / f"{stem}.tar.gz"
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(raw_root, arcname=archive_root)
    return dest, file_sha256(dest), "gzip"


def git_tracked_under(path: Path) -> tuple[str, ...]:
    """Paths git tracks under ``path``. Missing git is treated as untracked."""

    resolved = path.resolve()
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=resolved if resolved.is_dir() else resolved.parent,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ()
    try:
        listed = subprocess.check_output(
            ["git", "ls-files", "--", str(resolved)],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ()
    return tuple(line.strip() for line in listed.splitlines() if line.strip())


def assert_can_replace_results(results_root: Path, *, replace_committed: bool) -> None:
    if not results_root.exists():
        return
    tracked = git_tracked_under(results_root)
    if tracked and not replace_committed:
        raise ValueError(COMMITTED_HUB_REFUSE.format(path=results_root))


def _copy_compact_tree(
    *,
    raw_root: Path,
    dest_root: Path,
    probe_ids: list[str],
) -> list[Path]:
    copied: list[Path] = []
    for name in COMPACT_STAGE_FILES:
        src = raw_root / name
        if src.is_file():
            dest = dest_root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            copied.append(dest)
    for probe_id in probe_ids:
        src_dir = raw_root / probe_id
        dest_dir = dest_root / probe_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        fixture = src_dir / "fixture.json"
        if fixture.is_file():
            shutil.copy2(fixture, dest_dir / "fixture.json")
            copied.append(dest_dir / "fixture.json")
        comparison = src_dir / "comparison.json"
        if comparison.is_file():
            shutil.copy2(comparison, dest_dir / "comparison.json")
            copied.append(dest_dir / "comparison.json")
        html = src_dir / "index.html"
        if html.is_file():
            shutil.copy2(html, dest_dir / "index.html")
            copied.append(dest_dir / "index.html")
        figures = src_dir / "figures"
        if figures.is_dir():
            dest_fig = dest_dir / "figures"
            if dest_fig.exists():
                shutil.rmtree(dest_fig)
            shutil.copytree(figures, dest_fig)
            copied.extend(path for path in dest_fig.rglob("*") if path.is_file())
        truth = src_dir / "direct_truth.json"
        if truth.is_file():
            compact = compact_direct_truth(_read_json(truth))
            _write_json(dest_dir / "direct_truth.json", compact)
            copied.append(dest_dir / "direct_truth.json")
        source = src_dir / "source_control.json"
        if source.is_file():
            compact = compact_source_control(_read_json(source))
            _write_json(dest_dir / "source_control.json", compact)
            copied.append(dest_dir / "source_control.json")
        family = src_dir / "natural_family.json"
        if family.is_file():
            compact = compact_natural_family(_read_json(family))
            _write_json(dest_dir / "natural_family.json", compact)
            copied.append(dest_dir / "natural_family.json")
    return copied


def _finalize_compact_tree(
    dest_root: Path,
    copied: list[Path],
    probe_ids: list[str],
    manifest: Mapping[str, Any],
) -> None:
    copied.extend(reseal_campaign_summaries(dest_root))
    _write_json(dest_root / "compact_manifest.json", manifest)
    copied.append(dest_root / "compact_manifest.json")
    indexed = [path for path in dest_root.rglob("*") if path.is_file()]
    rebuild_artifact_index(dest_root, indexed)
    validate_campaign_tree(
        dest_root,
        probe_ids,
        expected_config_hash=str(manifest["config_hash"]),
        expected_mode=str(manifest["campaign_mode"]),
        require_all_stages=manifest["package_kind"] == PACKAGE_FULL_CLOSEOUT,
    )
    if (dest_root / "truth.json").is_file():
        validate_stage_output_refs(dest_root, _read_json(dest_root / "truth.json"))


def package_r3a_campaign(
    *,
    raw_root: Path,
    results_root: Path,
    bundle_dir: Path,
    config_path: Path = Path("configs/l5_positive_control_v1.json"),
    replace_committed: bool = False,
    full_closeout: bool = False,
) -> dict[str, Any]:
    raw_root = Path(raw_root)
    results_root = Path(results_root)
    bundle_dir = Path(bundle_dir)
    if not raw_root.is_dir():
        raise FileNotFoundError(f"missing raw campaign {raw_root}")
    if results_root.resolve() == raw_root.resolve():
        raise ValueError(
            "compact results_root must differ from raw_root; refusing in-place overwrite"
        )

    config = load_campaign_config(config_path)
    campaign_path = raw_root / "campaign.json"
    if not campaign_path.is_file():
        raise FileNotFoundError(f"missing campaign summary {campaign_path}")
    campaign = _read_json(campaign_path)
    mode, probe_scope, all_configured = validate_package_scope(
        campaign,
        config,
        full_closeout=full_closeout,
    )
    probe_ids = list(probe_scope)
    validate_campaign_tree(
        raw_root,
        probe_scope,
        expected_config_hash=config.config_hash,
        expected_mode=mode,
        require_all_stages=full_closeout,
    )
    assert_can_replace_results(results_root, replace_committed=replace_committed)

    producer_git = _producer_git(campaign)
    producer_git_sha = str(producer_git.get("git_commit") or "unknown")
    if full_closeout:
        if producer_git_sha == "unknown":
            raise ValueError("full closeout requires producer git provenance")
        if producer_git.get("dirty_tree") is not False:
            raise ValueError("full closeout requires a clean producer git tree")
    packager_git = git_provenance()

    bundle_path, bundle_sha, codec = write_raw_bundle(
        raw_root,
        bundle_dir,
        config_hash=config.config_hash,
        producer_git_sha=producer_git_sha,
        mode=mode,
        probe_ids=probe_scope,
        all_configured=all_configured,
    )
    package_kind = PACKAGE_FULL_CLOSEOUT if full_closeout else PACKAGE_DIAGNOSTIC
    manifest = {
        "program_id": config.program_id,
        "config_hash": config.config_hash,
        "producer_config_hash": str(campaign["config_hash"]),
        "packager_config_hash": config.config_hash,
        "schema_version": config.schema_version,
        "package_kind": package_kind,
        "campaign_mode": mode,
        "probe_ids": list(probe_scope),
        "all_configured_probes_present": all_configured,
        "allows_full_campaign_disposition": config.mode(mode).allows_full_campaign_disposition,
        "full_closeout_eligible": full_closeout,
        "git": producer_git,
        "producer_git": producer_git,
        "packager_git": packager_git,
        "campaign_blocker": campaign.get("campaign_blocker"),
        "accepted_reconstruction": campaign.get("accepted_reconstruction"),
        "raw_bundle": bundle_path.name,
        "raw_bundle_sha256": bundle_sha,
        "raw_bundle_codec": codec,
        "raw_bundle_archive_root": f"r3a_{mode}_raw",
        "reproduction": build_reproduction_command(
            config_path=config_path,
            raw_root=raw_root,
            mode=mode,
            probe_ids=probe_scope,
            all_configured=all_configured,
        ),
        "notes": [
            "Compact evidence only. Raw solver banks live in the content-addressed bundle.",
            "SAMPLED_ADMISSIBLE is not a global foliation. L5 remains pointing in S^2.",
            (
                "Diagnostic packages preserve their actual mode and probe scope and cannot close "
                "the scientific campaign."
                if not full_closeout
                else (
                    "Full closeout package: mode, five-probe scope, hashes, "
                    "and producer provenance verified."
                )
            ),
            (
                "campaign_blocker None means the campaign is incomplete or the mode "
                "cannot dispose; "
                "it is not NATURAL_DECOMPOSITION_BLOCKED."
            ),
        ],
    }

    results_root.parent.mkdir(parents=True, exist_ok=True)
    staging = results_root.parent / f".{results_root.name}.compact_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    try:
        copied = _copy_compact_tree(raw_root=raw_root, dest_root=staging, probe_ids=probe_ids)
        _finalize_compact_tree(staging, copied, probe_ids, manifest)
        if results_root.exists():
            shutil.rmtree(results_root)
        staging.rename(results_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return dict(manifest)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compact R3A campaign artifacts and hash the raw bundle"
    )
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/l5_positive_control_v1.json"))
    parser.add_argument(
        "--replace-committed",
        action="store_true",
        help=(
            "Allow replacing a git-tracked compact hub after the raw tree has been "
            "hashed and bundled."
        ),
    )
    parser.add_argument(
        "--full-closeout",
        action="store_true",
        help=(
            "Require mode=full, all five probes, every stage, a clean producer tree, "
            "and one blocker outcome."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = package_r3a_campaign(
        raw_root=args.raw_root,
        results_root=args.results_root,
        bundle_dir=args.bundle_dir,
        config_path=args.config,
        replace_committed=bool(args.replace_committed),
        full_closeout=bool(args.full_closeout),
    )
    print(
        json_dumps_strict(
            {
                "package_kind": manifest["package_kind"],
                "campaign_mode": manifest["campaign_mode"],
                "probe_ids": manifest["probe_ids"],
                "raw_bundle": manifest["raw_bundle"],
                "raw_bundle_sha256": manifest["raw_bundle_sha256"],
            }
        )
    )
    return 0
