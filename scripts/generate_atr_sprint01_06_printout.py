#!/usr/bin/env python3
"""Generate a combined printable readout for ATR Sprints 01–06.

Reproducible command::

    python scripts/generate_atr_sprint01_06_printout.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.sprint01_06_printout import write_sprint01_06_printout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=ROOT / "results" / "aligned_terminal_roll",
    )
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    results_root = args.results_root.resolve()
    out_dir = (args.out_dir or (results_root / "sprint01_06_printout")).resolve()
    payload = write_sprint01_06_printout(results_root, out_dir)
    print(f"Wrote {out_dir / 'index.html'}")
    print(f"Experiments: {payload['pass_count']}/{payload['experiment_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
