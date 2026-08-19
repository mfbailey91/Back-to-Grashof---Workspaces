"""Content-addressed stage authority for R3A campaign artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .models import (
    ArtifactHashDrift,
    CampaignConfig,
    StageArtifactRef,
    file_sha256,
    git_provenance,
    json_dumps_strict,
)

INDEX_NAME = "artifact_index.json"

STAGE_SUMMARY_NAMES: dict[str, str] = {
    "manifest": "manifest.json",
    "fixture": "fixture.json",
    "truth": "truth.json",
    "source-control": "source_control.json",
    "leaves": "leaves.json",
    "compare": "campaign.json",
    "render": "render.json",
}

PREREQUISITES: dict[str, tuple[str, ...]] = {
    "fixture": ("manifest",),
    "truth": ("manifest", "fixture"),
    "source-control": ("manifest", "fixture", "truth"),
    "leaves": ("manifest", "fixture", "truth"),
    "compare": ("manifest", "fixture", "truth", "source-control", "leaves"),
    "render": ("manifest", "fixture", "truth", "source-control", "leaves", "compare"),
}


def stage_summary_path(outdir: Path, stage: str) -> Path:
    return outdir / STAGE_SUMMARY_NAMES[stage]


def artifact_paths(outdir: Path, stage: str, probe_ids: Sequence[str]) -> tuple[Path, ...]:
    if stage == "manifest":
        return (stage_summary_path(outdir, stage),)
    if stage == "fixture":
        return (stage_summary_path(outdir, stage), *(outdir / pid / "fixture.json" for pid in probe_ids))
    if stage == "truth":
        return (stage_summary_path(outdir, stage), *(outdir / pid / "direct_truth.json" for pid in probe_ids))
    if stage == "source-control":
        return (stage_summary_path(outdir, stage), *(outdir / pid / "source_control.json" for pid in probe_ids))
    if stage == "leaves":
        return (stage_summary_path(outdir, stage), *(outdir / pid / "natural_family.json" for pid in probe_ids))
    if stage == "compare":
        return (
            stage_summary_path(outdir, stage),
            outdir / "compare.json",
            *(outdir / pid / "comparison.json" for pid in probe_ids),
        )
    if stage == "render":
        return (stage_summary_path(outdir, stage), outdir / "index.html")
    return ()


def relative_artifact_path(path: Path, outdir: Path) -> str:
    resolved = path.resolve()
    root = outdir.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return path.name


def make_artifact_ref(
    path: Path,
    *,
    outdir: Path,
    stage: str,
    config: CampaignConfig,
    mode: str,
    probe_ids: Sequence[str],
) -> StageArtifactRef:
    return StageArtifactRef(
        stage=stage,
        path=relative_artifact_path(path, outdir),
        sha256=file_sha256(path),
        config_hash=config.config_hash,
        mode=mode,
        probe_ids=tuple(probe_ids),
        schema_version=config.schema_version,
    )


def load_artifact_index(outdir: Path) -> dict[str, str]:
    path = outdir / INDEX_NAME
    if not path.is_file():
        return {}
    blob = json.loads(path.read_text(encoding="utf-8"))
    files = blob.get("files", blob)
    if not isinstance(files, dict):
        raise TypeError(f"{path} is not an artifact index")
    return {str(key): str(value) for key, value in files.items()}


def write_artifact_index(outdir: Path, files: Mapping[str, str]) -> None:
    payload = {"files": dict(sorted(files.items()))}
    (outdir / INDEX_NAME).write_text(json_dumps_strict(payload), encoding="utf-8")


def update_artifact_index(outdir: Path, paths: Sequence[Path]) -> dict[str, str]:
    index = load_artifact_index(outdir)
    for path in paths:
        if path.is_file():
            index[relative_artifact_path(path, outdir)] = file_sha256(path)
    write_artifact_index(outdir, index)
    return index


def rebuild_artifact_index(outdir: Path, paths: Sequence[Path]) -> dict[str, str]:
    """Replace the index with hashes of ``paths``. Does not record the index file itself."""

    index: dict[str, str] = {}
    for path in paths:
        if not path.is_file() or path.name == INDEX_NAME:
            continue
        index[relative_artifact_path(path, outdir)] = file_sha256(path)
    write_artifact_index(outdir, index)
    return index


def validate_artifact_hashes(
    outdir: Path,
    paths: Sequence[Path],
    *,
    recorded: Mapping[str, str] | None = None,
) -> None:
    if recorded is None and not (outdir / INDEX_NAME).is_file():
        raise ArtifactHashDrift(f"missing {INDEX_NAME}; refusing unhashed campaign {outdir}")
    index = dict(recorded) if recorded is not None else load_artifact_index(outdir)
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"missing prerequisite {path}")
        rel = relative_artifact_path(path, outdir)
        actual = file_sha256(path)
        expected = index.get(rel)
        if expected is None:
            raise ArtifactHashDrift(f"missing recorded hash for {rel}")
        if actual != expected:
            raise ArtifactHashDrift(f"hash drift for {rel}: recorded {expected} actual {actual}")


def validate_campaign_tree(outdir: Path, probe_ids: Sequence[str]) -> None:
    """Refuse a campaign tree whose stage hashes are missing or drifted."""

    if not (outdir / INDEX_NAME).is_file():
        raise ArtifactHashDrift(f"missing {INDEX_NAME}; refusing unhashed campaign {outdir}")
    for stage in STAGE_SUMMARY_NAMES:
        summary = stage_summary_path(outdir, stage)
        if not summary.is_file():
            continue
        blob = json.loads(summary.read_text(encoding="utf-8"))
        if not isinstance(blob, dict):
            raise TypeError(f"{summary} is not a JSON object")
        validate_stage_output_refs(outdir, blob)
        present = tuple(path for path in artifact_paths(outdir, stage, probe_ids) if path.is_file())
        validate_artifact_hashes(outdir, present)


def validate_stage_output_refs(outdir: Path, blob: Mapping[str, Any]) -> None:
    refs = blob.get("outputs")
    if not isinstance(refs, list):
        return
    for item in refs:
        if not isinstance(item, dict):
            continue
        rel = str(item.get("path", ""))
        expected = str(item.get("sha256", ""))
        if not rel or not expected:
            continue
        path = outdir / rel
        if not path.is_file():
            raise FileNotFoundError(f"missing hashed artifact {path}")
        actual = file_sha256(path)
        if actual != expected:
            raise ArtifactHashDrift(f"hash drift for {rel}: recorded {expected} actual {actual}")


def finalize_stage(
    outdir: Path,
    payload: dict[str, Any],
    *,
    config: CampaignConfig,
    stage: str,
    mode: str,
    probe_ids: Sequence[str],
    extra_outputs: Sequence[Path] = (),
) -> dict[str, Any]:
    """Write the stage summary with hashed inputs/outputs and update the index."""

    probe_tuple = tuple(probe_ids)
    input_files: list[Path] = []
    input_refs: list[dict[str, Any]] = []
    for prior in PREREQUISITES.get(stage, ()):
        for path in artifact_paths(outdir, prior, probe_tuple):
            if not path.is_file():
                continue
            input_files.append(path)
            input_refs.append(
                make_artifact_ref(
                    path,
                    outdir=outdir,
                    stage=prior,
                    config=config,
                    mode=mode,
                    probe_ids=probe_tuple,
                ).to_json_dict()
            )
    summary_path = stage_summary_path(outdir, stage)
    output_paths = [
        path
        for path in (*artifact_paths(outdir, stage, probe_tuple), *extra_outputs)
        if path != summary_path and path.is_file()
    ]
    output_refs = [
        make_artifact_ref(
            path,
            outdir=outdir,
            stage=stage,
            config=config,
            mode=mode,
            probe_ids=probe_tuple,
        ).to_json_dict()
        for path in output_paths
    ]
    sealed = {
        **payload,
        "schema_version": config.schema_version,
        "git": git_provenance(),
        "inputs": input_refs,
        "outputs": output_refs,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json_dumps_strict(sealed), encoding="utf-8")
    update_artifact_index(outdir, (*input_files, *output_paths, summary_path))
    return sealed


def reseal_stage_blob(outdir: Path, blob: dict[str, Any]) -> dict[str, Any]:
    """Rewrite input/output SHA-256s to match files currently on disk."""

    for key in ("inputs", "outputs"):
        refs = blob.get(key)
        if not isinstance(refs, list):
            continue
        for item in refs:
            if not isinstance(item, dict):
                continue
            rel = str(item.get("path", ""))
            if not rel:
                continue
            path = outdir / rel
            if path.is_file():
                item["sha256"] = file_sha256(path)
    return blob


def reseal_campaign_summaries(outdir: Path) -> tuple[Path, ...]:
    """Recompute stage-summary hashes after compacting probe artifacts.

    Summaries are rewritten in pipeline order so later ``inputs`` see the new
    summary SHA-256s.
    """

    names = (
        "manifest.json",
        "fixture.json",
        "truth.json",
        "source_control.json",
        "leaves.json",
        "campaign.json",
        "compare.json",
        "render.json",
    )
    written: list[Path] = []
    for name in names:
        path = outdir / name
        if not path.is_file():
            continue
        blob = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(blob, dict):
            continue
        reseal_stage_blob(outdir, blob)
        path.write_text(json_dumps_strict(blob), encoding="utf-8")
        written.append(path)
    return tuple(written)
