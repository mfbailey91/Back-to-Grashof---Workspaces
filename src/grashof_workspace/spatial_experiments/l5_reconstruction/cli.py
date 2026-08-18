"""R3A five-point reconstruction CLI.

Stages: manifest, fixture, truth, source-control, leaves, compare, render, all.
Later stages refuse missing prerequisites or config-hash, mode, or probe-scope drift.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .models import (
    PROCESS_STAGE_NAMES,
    empty_campaign_result,
    json_dumps_strict,
    load_campaign_config,
    stage_envelope,
)

STAGES = (*PROCESS_STAGE_NAMES, "all")
PREREQUISITES: dict[str, tuple[str, ...]] = {
    "fixture": ("manifest",),
    "truth": ("manifest", "fixture"),
    "source-control": ("manifest", "fixture", "truth"),
    "leaves": ("manifest", "fixture", "truth"),
    "compare": ("manifest", "fixture", "truth", "source-control", "leaves"),
    "render": ("manifest", "fixture", "truth", "source-control", "leaves", "compare"),
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps_strict(payload), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} is not a JSON object")
    return payload


def _require_hash(blob: dict[str, Any], config_hash: str) -> None:
    stored = str(blob.get("config_hash", ""))
    if stored != config_hash:
        raise ValueError("config-hash drift: refusing to resume from mismatched manifest")


def _stage_summary_path(outdir: Path, stage: str) -> Path:
    names = {
        "manifest": "manifest.json",
        "fixture": "fixture.json",
        "truth": "truth.json",
        "source-control": "source_control.json",
        "leaves": "leaves.json",
        "compare": "campaign.json",
        "render": "render.json",
    }
    return outdir / names[stage]


def _artifact_paths(outdir: Path, stage: str, probe_ids: Sequence[str]) -> tuple[Path, ...]:
    if stage == "manifest":
        return (_stage_summary_path(outdir, stage),)
    if stage == "fixture":
        return (_stage_summary_path(outdir, stage), *(outdir / pid / "fixture.json" for pid in probe_ids))
    if stage == "truth":
        return (_stage_summary_path(outdir, stage), *(outdir / pid / "direct_truth.json" for pid in probe_ids))
    if stage == "source-control":
        return (_stage_summary_path(outdir, stage), *(outdir / pid / "source_control.json" for pid in probe_ids))
    if stage == "leaves":
        return (_stage_summary_path(outdir, stage), *(outdir / pid / "natural_family.json" for pid in probe_ids))
    if stage == "compare":
        return (_stage_summary_path(outdir, stage),)
    if stage == "render":
        return (_stage_summary_path(outdir, stage),)
    return ()


def _require_prerequisites(
    outdir: Path,
    stage: str,
    *,
    config_hash: str,
    mode: str,
    probe_ids: Sequence[str],
) -> None:
    for prior in PREREQUISITES.get(stage, ()):
        for path in _artifact_paths(outdir, prior, probe_ids):
            if not path.is_file():
                raise FileNotFoundError(f"missing prerequisite {path}")
        summary = _stage_summary_path(outdir, prior)
        blob = _read_json(summary)
        stored_hash = str(blob.get("config_hash", ""))
        if stored_hash and stored_hash != config_hash:
            raise ValueError("config-hash drift: refusing to resume from mismatched artifact")
        stored_mode = blob.get("mode")
        if stored_mode is not None and str(stored_mode) != mode:
            raise ValueError(f"mode drift: {stored_mode} vs {mode}")
        stored_probes = blob.get("probe_ids")
        if stored_probes is not None:
            allowed = {str(item) for item in stored_probes}
            missing = [pid for pid in probe_ids if pid not in allowed]
            if missing:
                raise ValueError(f"probe-scope drift: {missing} not in upstream {sorted(allowed)}")


def write_manifest(config_path: Path, outdir: Path, *, mode: str = "smoke") -> Path:
    config = load_campaign_config(config_path)
    campaign = empty_campaign_result(config)
    payload = campaign.to_json_dict()
    payload.update(stage_envelope(config, stage="manifest", mode=mode, probe_ids=tuple(p.probe_id for p in config.probes)))
    path = outdir / "manifest.json"
    _write_json(path, payload)
    return path


def _load_manifest(outdir: Path, config_hash: str) -> dict[str, Any]:
    path = outdir / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError("missing prerequisite manifest.json")
    manifest = _read_json(path)
    _require_hash(manifest, config_hash)
    return manifest


def run_stage(
    *,
    config_path: Path,
    outdir: Path,
    stage: str,
    mode: str,
    probe_id: str | None,
    resume_from: Path | None,
) -> dict[str, Any]:
    config = load_campaign_config(config_path)
    outdir.mkdir(parents=True, exist_ok=True)
    if resume_from is not None:
        prior = _read_json(resume_from)
        _require_hash(prior, config.config_hash)
        stored_mode = prior.get("mode")
        if stored_mode is not None and str(stored_mode) != mode:
            raise ValueError(f"mode drift: {stored_mode} vs {mode}")

    if stage == "manifest":
        path = write_manifest(config_path, outdir, mode=mode)
        return _read_json(path)

    _load_manifest(outdir, config.config_hash)
    probes = [config.probe(probe_id)] if probe_id else list(config.probes)
    probe_ids = tuple(p.probe_id for p in probes)
    if stage != "all":
        _require_prerequisites(outdir, stage, config_hash=config.config_hash, mode=mode, probe_ids=probe_ids)

    if stage == "fixture":
        from .positive_control import write_fixture_stage

        return write_fixture_stage(config, outdir, probes, mode=mode)
    if stage == "truth":
        from .direct_truth import write_truth_stage

        return write_truth_stage(config, outdir, probes, mode=mode)
    if stage == "source-control":
        from .source_control import write_source_control_stage

        return write_source_control_stage(config, outdir, probes, mode=mode)
    if stage == "leaves":
        from .leaf_family import write_leaves_stage

        return write_leaves_stage(config, outdir, probes, mode=mode)
    if stage == "compare":
        from .comparison import write_compare_stage

        return write_compare_stage(config, outdir, probes, mode=mode)
    if stage == "render":
        from .readout import write_render_stage

        return write_render_stage(config, outdir, probes, mode=mode, generate_gif=mode == "full")
    if stage == "all":
        write_manifest(config_path, outdir, mode=mode)
        from .comparison import write_compare_stage
        from .direct_truth import write_truth_stage
        from .leaf_family import write_leaves_stage
        from .positive_control import write_fixture_stage
        from .readout import write_render_stage
        from .source_control import write_source_control_stage

        write_fixture_stage(config, outdir, probes, mode=mode)
        write_truth_stage(config, outdir, probes, mode=mode)
        write_source_control_stage(config, outdir, probes, mode=mode)
        write_leaves_stage(config, outdir, probes, mode=mode)
        result = write_compare_stage(config, outdir, probes, mode=mode)
        write_render_stage(config, outdir, probes, mode=mode, generate_gif=False)
        return result
    raise ValueError(f"unknown stage {stage}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R3A L5 five-point natural-leaf reconstruction")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES, default="manifest")
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--probe", dest="probe_id", default=None)
    parser.add_argument("--resume-from", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_stage(
        config_path=args.config,
        outdir=args.outdir,
        stage=args.stage,
        mode=args.mode,
        probe_id=args.probe_id,
        resume_from=args.resume_from,
    )
    print(json_dumps_strict({"stage": args.stage, "program_id": payload.get("program_id")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
