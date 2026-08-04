"""CLI for synthetic 6R geometry reports and plots."""

from __future__ import annotations

import argparse
from pathlib import Path

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.visualization import format_geometry_report, plot_robot_axes


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Synthetic 6R axis geometry reports, visualizations, and dashboards."
    )
    p.add_argument(
        "--dashboard",
        action="store_true",
        help="Generate Sprint 0–3 static HTML dashboards under results/",
    )
    p.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Results root for --dashboard (default: results/)",
    )
    p.add_argument("--architecture", choices=["A", "B", "C"], default=None)
    p.add_argument("--L2", type=float, default=1.0)
    p.add_argument("--L3", type=float, default=0.8)
    p.add_argument("--Lt", type=float, default=0.25)
    p.add_argument("--epsilon-w", type=float, default=0.0)
    p.add_argument("--epsilon-s", type=float, default=0.0)
    p.add_argument("--output", type=Path, default=None, help="PNG path for 3D plot")
    p.add_argument("--report", type=Path, default=None, help="Write text geometry report")
    return p


def _make_arch(args: argparse.Namespace):  # type: ignore[no-untyped-def]
    params = ArchitectureParams(
        L2=args.L2,
        L3=args.L3,
        Lt=args.Lt,
        epsilon_w=args.epsilon_w,
        epsilon_s=args.epsilon_s,
    )
    if args.architecture == "A":
        return ArchitectureA(ArchitectureParams(L2=params.L2, L3=params.L3, Lt=params.Lt))
    if args.architecture == "B":
        return ArchitectureB(
            ArchitectureParams(L2=params.L2, L3=params.L3, Lt=params.Lt, epsilon_w=params.epsilon_w)
        )
    return ArchitectureC(
        ArchitectureParams(L2=params.L2, L3=params.L3, Lt=params.Lt, epsilon_s=params.epsilon_s)
    )


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.dashboard:
        from sixr_grashof.dashboard import generate_dashboards

        paths = generate_dashboards(results_root=args.results_dir)
        for key, path in paths.items():
            print(f"{key}: {path}")
        return
    if args.architecture is None:
        raise SystemExit("Provide --architecture A|B|C, or use --dashboard")
    arch = _make_arch(args)
    q = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    fk = arch.forward(q)
    report = arch.geometry_report(q)
    text = format_geometry_report(report)
    print(text)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    if args.output is not None:
        plot_robot_axes(fk, report, output=args.output)


if __name__ == "__main__":
    main()
