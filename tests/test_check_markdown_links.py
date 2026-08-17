"""Tests for scripts/check_markdown_links.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check_markdown_links.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_markdown_links", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_local_target_strips_anchor_and_ignores_http() -> None:
    mod = _load_module()
    assert mod._local_target("theory/DECOMPOSITION_LADDER.md#sec") == "theory/DECOMPOSITION_LADDER.md"
    assert mod._local_target("https://example.com/a.md") is None
    assert mod._local_target("mailto:a@b.c") is None
    assert mod._local_target("#anchor-only") is None


def test_resolve_directory_to_readme(tmp_path: Path) -> None:
    mod = _load_module()
    docs = tmp_path / "docs"
    archive = docs / "archive"
    archive.mkdir(parents=True)
    (archive / "README.md").write_text("# archive\n", encoding="utf-8")
    source = docs / "README.md"
    source.write_text("[a](archive/)\n", encoding="utf-8")
    resolved = mod.resolve_local(source, "archive/", tmp_path)
    assert resolved == (archive / "README.md").resolve()


def test_check_file_reports_missing_and_accepts_image(tmp_path: Path) -> None:
    mod = _load_module()
    root = tmp_path
    docs = root / "docs"
    docs.mkdir()
    assets = docs / "assets"
    assets.mkdir()
    img = assets / "example.png"
    img.write_bytes(b"x")
    md = docs / "page.md"
    md.write_text(
        "[ok](assets/example.png)\n[missing](nope.md)\n![also](assets/example.png)\n",
        encoding="utf-8",
    )
    errors = mod.check_file(md, root)
    assert len(errors) == 1
    assert "nope.md" in errors[0]


def test_cli_on_repo_root() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
