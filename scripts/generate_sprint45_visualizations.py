"""Generate Sprint 4–5 visualizations and dashboards (reproducible)."""

from __future__ import annotations

import argparse
from pathlib import Path

from sixr_grashof.experiments.offset_sweep import run_architecture_experiments
from sixr_grashof.io.results import write_json, write_records_json
from sixr_grashof.visualization import (
    plot_agreement_map,
    plot_confusion_heatmap,
    plot_connectivity_components,
    plot_gate2_coverage_convergence,
    plot_offset_sweeps,
    plot_orientation_sample_cloud,
    plot_residual_vs_error,
    plot_solver_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
OUT4 = ROOT / "results" / "sprint04_orientation"
OUT5 = ROOT / "results" / "sprint05_experiments"

# Published densification: full ε sweeps; coarse 512 orientations (plan default).
# Use --fast for orientation_count=128 during local iteration.
DEFAULT_ORIENTATION_COUNT = 512
FAST_COARSE_COUNT = 128
EPS = (0.0, 0.025, 0.05, 0.10, 0.20)


def generate_sprint4(out: Path = OUT4) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for fn, name in (
        (plot_orientation_sample_cloud, "orientation_sample_cloud.png"),
        (plot_connectivity_components, "connectivity_components.png"),
        (plot_gate2_coverage_convergence, "gate2_coverage_convergence.png"),
        (plot_solver_diagnostics, "solver_diagnostics.png"),
    ):
        p = fn(output=out / name)
        assert p is not None
        paths.append(p)
    return paths


def generate_sprint5(
    out: Path = OUT5,
    *,
    orientation_count: int = DEFAULT_ORIENTATION_COUNT,
) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    summary = run_architecture_experiments(
        resolution="coarse",
        seed=0,
        n_ik_starts=2,
        n_a_positions=5,
        include_a_grid=True,
        grid_radial=3,
        grid_elbow=3,
        epsilon_w_values=EPS,
        epsilon_s_values=EPS,
        orientation_count=orientation_count,
    )
    paths = [
        write_records_json(summary.records, out / "experiment_records.json"),
        write_json(summary.to_dict(), out / "experiment_summary.json"),
    ]
    for fn, name, kwargs in (
        (plot_confusion_heatmap, "confusion_heatmap.png", {"summary": summary}),
        (plot_residual_vs_error, "residual_vs_error.png", {"summary": summary}),
        (plot_offset_sweeps, "offset_sweeps.png", {"summary": summary}),
        (
            plot_agreement_map,
            "agreement_map.png",
            {
                "records": [
                    r for r in summary.records if r.architecture_id == "A"
                ]
            },
        ),
    ):
        p = fn(output=out / name, **kwargs)
        assert p is not None
        paths.append(p)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fast",
        action="store_true",
        help=f"Use orientation_count={FAST_COARSE_COUNT} (faster local iteration)",
    )
    parser.add_argument(
        "--full-coarse",
        action="store_true",
        help=f"Alias for published default orientation_count={DEFAULT_ORIENTATION_COUNT}",
    )
    parser.add_argument("--skip-sprint4", action="store_true")
    args = parser.parse_args()
    n_ori = FAST_COARSE_COUNT if args.fast else DEFAULT_ORIENTATION_COUNT

    paths: list[Path] = []
    if not args.skip_sprint4:
        paths.extend(generate_sprint4())
    paths.extend(generate_sprint5(orientation_count=n_ori))

    from sixr_grashof.dashboard import generate_dashboards

    dash = generate_dashboards(results_root=ROOT / "results")
    print(f"Artifacts ({len(paths)}) with orientation_count={n_ori}")
    for p in paths:
        print(f"  {p.relative_to(ROOT)}")
    print("Dashboards:")
    for key, path in dash.items():
        print(f"  {key}: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
