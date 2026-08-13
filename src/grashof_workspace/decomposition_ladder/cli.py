"""CLI for the L3-L7 decomposition-ladder program readout."""

from __future__ import annotations

import argparse
from pathlib import Path

from .readout import build_ladder_readout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/decomposition_ladder"),
        help="output directory for HTML, JSON, PNG, and GIF artifacts",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="skip the conceptual U-joint GIF",
    )
    args = parser.parse_args(argv)
    paths = build_ladder_readout(args.outdir, include_animation=not args.no_animation)
    print(f"Wrote {paths.html}")
    print(f"Wrote {paths.json}")
    print(f"Wrote {paths.coordinate_plot}")
    if paths.animation is not None:
        print(f"Wrote {paths.animation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
