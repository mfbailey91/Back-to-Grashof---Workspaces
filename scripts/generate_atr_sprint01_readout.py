#!/usr/bin/env python3
"""Generate the Sprint 01 Spatial Foundations HTML readout.

Reproducible command::

    python scripts/validate_terminal_roll_fixture.py
    python scripts/generate_atr_sprint01_readout.py

Writes::

    results/aligned_terminal_roll/sprint01_readout/index.html
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.readout import write_readout_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=ROOT / "results" / "aligned_terminal_roll",
        help="Directory containing ATR_EXP_00N artifact folders",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: <results-root>/sprint01_readout)",
    )
    args = parser.parse_args(argv)

    results_root = args.results_root.resolve()
    out_dir = (args.out_dir or (results_root / "sprint01_readout")).resolve()
    payload = write_readout_artifacts(results_root, out_dir)
    print(f"Wrote {out_dir / 'index.html'}")
    print(f"Experiments: {payload['pass_count']}/{payload['experiment_count']} PASS")
    return 0 if payload["pass_count"] == payload["experiment_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
