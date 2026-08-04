"""Command-line interface."""

from __future__ import annotations

import argparse

from .atlas import generate_atlas
from .planar3r import Planar3R
from .plotting import plot_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plot analytical reachable and dexterous workspaces for a planar 3R arm, "
            "or generate a link-ratio atlas."
        )
    )
    parser.add_argument(
        "--atlas",
        action="store_true",
        help="Generate CSV atlas and experiment-matrix figures",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/atlas",
        help="Directory for atlas CSV and figures (with --atlas)",
    )
    parser.add_argument("--l1", type=float, help="Proximal link length")
    parser.add_argument("--l2", type=float, help="Middle link length")
    parser.add_argument("--l3", type=float, help="Terminal link length")
    parser.add_argument("--output", default="workspace.png")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.atlas:
        csv_path = generate_atlas(args.output_dir)
        print(f"wrote atlas: {csv_path}")
        return

    missing = [name for name in ("l1", "l2", "l3") if getattr(args, name) is None]
    if missing:
        raise SystemExit(
            f"missing required link lengths for single-figure mode: {', '.join(missing)}"
        )

    robot = Planar3R(args.l1, args.l2, args.l3)
    output = plot_workspace(robot, args.output)

    print(f"reachable radial interval: {robot.reachable_radial_interval()}")
    print(f"dexterous radial intervals: {robot.dexterous_radial_intervals()}")
    print(f"dexterous topology: {robot.dexterous_topology()}")
    print(f"wrote: {output}")


if __name__ == "__main__":
    main()
