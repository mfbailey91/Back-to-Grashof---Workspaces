#!/usr/bin/env python3
"""Validate the isolated terminal-roll fixture (Sprint 01).

Reproducible command::

    python scripts/validate_terminal_roll_fixture.py

Writes decision-bearing artifacts under::

    results/aligned_terminal_roll/ATR_EXP_00N/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.diagnostics import run_all_controls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Repository root for results/ and git commit stamping",
    )
    args = parser.parse_args(argv)

    results = run_all_controls(args.repo_root.resolve())
    print("Terminal-roll fixture validation")
    print("================================")
    failed = 0
    for r in results:
        print(f"{r.experiment_id}: {r.status}")
        print(f"  expected: {r.expected}")
        print(f"  observed: {r.observed}")
        if r.status != "PASS":
            failed += 1
    out = args.repo_root.resolve() / "results" / "aligned_terminal_roll"
    print(f"Artifacts: {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
