#!/usr/bin/env python3
"""Validate Sprint 06 candidate spherical experiments (ATR_EXP_032–035).

Reproducible command::

    python scripts/validate_spherical_candidates.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.spherical_experiments import (
    run_all_spherical_experiments,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    results = run_all_spherical_experiments(args.repo_root.resolve())
    print("Spherical-candidate validation")
    print("==============================")
    failed = 0
    for result in results:
        print(f"{result['experiment_id']}: {result['status']}")
        print(f"  expected: {result['expected']}")
        print(f"  observed: {result['observed']}")
        if result["status"] != "PASS":
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
