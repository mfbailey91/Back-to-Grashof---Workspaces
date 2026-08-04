#!/usr/bin/env python3
"""Fetch selected robot-description repositories and record provenance."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "robot_corpus" / "manifest.json"
SOURCE_ROOT = ROOT / "third_party" / "robot_corpus"
PROVENANCE_ROOT = ROOT / "data" / "robot_corpus" / "provenance"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def run(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def selected_models(manifest: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    models = list(manifest["models"])
    if args.models:
        wanted = set(args.models)
        known = {model["id"] for model in models}
        unknown = sorted(wanted - known)
        if unknown:
            raise ValueError("Unknown model IDs: " + ", ".join(unknown))
        return [model for model in models if model["id"] in wanted]
    if args.group and args.group != "all":
        return [model for model in models if model["group"] == args.group]
    return [model for model in models if model.get("source_id") is not None]


def resolve_entrypoint(source_dir: Path, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if (source_dir / candidate).is_file():
            return candidate
    return None


def clone_source(source: dict[str, Any], *, refresh: bool, dry_run: bool) -> tuple[Path, str | None]:
    source_dir = SOURCE_ROOT / str(source["id"])
    command = ["git", "clone", "--depth", "1"]
    if source.get("branch"):
        command.extend(["--branch", str(source["branch"])])
    command.extend([str(source["repository"]), str(source_dir)])

    print(f"\n[{source['id']}] {source['repository']}")
    print("  " + " ".join(command))
    if dry_run:
        return source_dir, None

    if source_dir.exists():
        if refresh:
            shutil.rmtree(source_dir)
        else:
            commit = run(["git", "rev-parse", "HEAD"], cwd=source_dir)
            print(f"  existing snapshot: {commit}")
            return source_dir, commit

    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    run(command)
    commit = run(["git", "rev-parse", "HEAD"], cwd=source_dir)
    print(f"  resolved commit: {commit}")
    return source_dir, commit


def write_provenance(
    source: dict[str, Any],
    source_dir: Path,
    commit: str,
    models: list[dict[str, Any]],
) -> None:
    PROVENANCE_ROOT.mkdir(parents=True, exist_ok=True)
    model_records = []
    for model in models:
        selected = resolve_entrypoint(source_dir, list(model.get("entrypoint_candidates", [])))
        model_records.append(
            {
                "model_id": model["id"],
                "group": model["group"],
                "selected_entrypoint": selected,
                "entrypoint_candidates": model.get("entrypoint_candidates", []),
                "expected_dof": model["expected_dof"],
                "expected_signature": model["expected_signature"],
                "chain": model.get("chain"),
                "entrypoint_status": "resolved" if selected else "unresolved",
            }
        )
        status = selected or "UNRESOLVED"
        print(f"  {model['id']}: {status}")

    record = {
        "source_id": source["id"],
        "repository": source["repository"],
        "requested_branch": source.get("branch"),
        "resolved_commit": commit,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "license_spdx": source["license_spdx"],
        "license_status": source["license_status"],
        "models": model_records,
    }
    path = PROVENANCE_ROOT / f"{source['id']}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"  provenance: {path.relative_to(ROOT)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=["all", "primary_6r", "redundant_7r_control", "planar_3r_external"], default="all")
    parser.add_argument("--models", nargs="+")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--list-sources", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = load_manifest()

    if args.list_sources:
        for source in manifest["sources"]:
            branch = source.get("branch") or "default"
            print(f"{source['id']:36} {branch:14} {source['repository']}")
        return 0

    if args.list_models:
        for model in manifest["models"]:
            source = model.get("source_id") or "project"
            print(f"{model['id']:32} {model['group']:24} DOF={model['expected_dof']} {source}")
        return 0

    try:
        models = selected_models(manifest, args)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    source_by_id = {source["id"]: source for source in manifest["sources"]}
    models_by_source: dict[str, list[dict[str, Any]]] = {}
    for model in models:
        source_id = model.get("source_id")
        if source_id is not None:
            models_by_source.setdefault(source_id, []).append(model)

    for source_id, source_models in models_by_source.items():
        source = source_by_id[source_id]
        try:
            source_dir, commit = clone_source(source, refresh=args.refresh, dry_run=args.dry_run)
            if not args.dry_run and commit is not None:
                write_provenance(source, source_dir, commit, source_models)
        except (OSError, subprocess.CalledProcessError) as error:
            print(f"Fetch failed for {source_id}: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
