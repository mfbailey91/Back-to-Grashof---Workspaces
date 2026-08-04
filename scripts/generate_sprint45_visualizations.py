"""Generate Sprint 4–5 visualizations and dashboards (reproducible)."""

from __future__ import annotations

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


def generate_sprint5(out: Path = OUT5) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    summary = run_architecture_experiments(
        resolution="coarse",
        seed=0,
        n_ik_starts=3,
        n_a_positions=3,
        orientation_count=32,
    )
    paths = [
        write_records_json(summary.records, out / "experiment_records.json"),
        write_json(summary.to_dict(), out / "experiment_summary.json"),
    ]
    for fn, name, kwargs in (
        (plot_confusion_heatmap, "confusion_heatmap.png", {"summary": summary}),
        (plot_residual_vs_error, "residual_vs_error.png", {"summary": summary}),
        (plot_offset_sweeps, "offset_sweeps.png", {"summary": summary}),
        (plot_agreement_map, "agreement_map.png", {}),
    ):
        p = fn(output=out / name, **kwargs)
        assert p is not None
        paths.append(p)
    return paths


def main() -> None:
    p4 = generate_sprint4()
    p5 = generate_sprint5()
    from sixr_grashof.dashboard import generate_dashboards

    dash = generate_dashboards(results_root=ROOT / "results")
    print(f"Sprint 4: {len(p4)} artifacts under {OUT4}")
    print(f"Sprint 5: {len(p5)} artifacts under {OUT5}")
    for p in p4 + p5:
        print(f"  {p.relative_to(ROOT)}")
    print("Dashboards:")
    for key, path in dash.items():
        print(f"  {key}: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
