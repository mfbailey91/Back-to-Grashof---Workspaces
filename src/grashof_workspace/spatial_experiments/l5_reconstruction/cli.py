"""R3A five-point reconstruction CLI.

Stages: manifest, fixture, truth, source-control, leaves, compare, render, all.
Later stages refuse missing prerequisites or config-hash drift.
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
)

STAGES = (*PROCESS_STAGE_NAMES, "all")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps_strict(payload), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} is not a JSON object")
    return payload


def _require_hash(manifest: dict[str, Any], config_hash: str) -> None:
    stored = str(manifest.get("config_hash", ""))
    if stored != config_hash:
        raise ValueError("config-hash drift: refusing to resume from mismatched manifest")


def write_manifest(config_path: Path, outdir: Path) -> Path:
    config = load_campaign_config(config_path)
    campaign = empty_campaign_result(config)
    payload = campaign.to_json_dict()
    payload["stage"] = "manifest"
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

    if stage == "manifest":
        path = write_manifest(config_path, outdir)
        return _read_json(path)

    _load_manifest(outdir, config.config_hash)
    probes = [config.probe(probe_id)] if probe_id else list(config.probes)

    if stage == "fixture":
        from .positive_control import write_fixture_stage

        return write_fixture_stage(config, outdir, probes)
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
        write_manifest(config_path, outdir)
        from .comparison import write_compare_stage
        from .direct_truth import write_truth_stage
        from .leaf_family import write_leaves_stage
        from .positive_control import write_fixture_stage
        from .readout import write_render_stage
        from .source_control import write_source_control_stage

        write_fixture_stage(config, outdir, probes)
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
