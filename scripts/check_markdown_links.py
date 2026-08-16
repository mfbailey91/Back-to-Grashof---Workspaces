#!/usr/bin/env python3
"""Check local Markdown links among tracked ``*.md`` files.

Ignores external http(s)/mailto links. Strips anchors and query strings.
Directory targets resolve to README.md. Exits nonzero if any target is missing.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def tracked_markdown_files(repo_root: Path) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [repo_root / line for line in proc.stdout.splitlines() if line.strip()]


def _local_target(raw: str) -> str | None:
    target = raw.strip()
    if not target or target.startswith("#"):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    # split title "path" or path 'title'
    if target[:1] in {'"', "'"}:
        return None
    for sep in (" '", ' "'):
        if sep in target:
            target = target.split(sep, 1)[0].strip()
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https", "mailto", "ftp"}:
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    # Ignore trivial non-path tokens (e.g. accidental math markdown).
    if "/" not in path and "." not in path and len(path) <= 2:
        return None
    return path


def resolve_local(source: Path, target: str, repo_root: Path) -> Path:
    candidate = (source.parent / target).resolve()
    if candidate.is_dir():
        readme = candidate / "README.md"
        return readme
    return candidate


FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def check_file(path: Path, repo_root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = FENCE_RE.sub("", text)
    errors: list[str] = []
    for match in list(LINK_RE.finditer(text)) + list(IMAGE_RE.finditer(text)):
        raw = match.group(2)
        local = _local_target(raw)
        if local is None:
            continue
        resolved = resolve_local(path, local, repo_root)
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError:
            # allow targets outside repo only if they exist; still report missing
            pass
        if not resolved.exists():
            rel = path.relative_to(repo_root)
            errors.append(f"{rel}: missing {raw!r} -> {resolved}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    errors: list[str] = []
    for path in tracked_markdown_files(repo_root):
        if not path.is_file():
            continue
        errors.extend(check_file(path, repo_root))
    if errors:
        print(f"Found {len(errors)} broken Markdown link(s):", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("All local Markdown links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
