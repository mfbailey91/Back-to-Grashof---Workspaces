from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import classify_mock_branch
from .continuation import ContinuationConfig, continue_physical_uuur_sample
from .descriptors import generate_geometry_samples
from .families import FAMILY_AXIS_CASES, ORDERED_FAMILIES
from .geometry_descriptors import generate_physical_geometry_samples
from .geometry_plots import plot_physical_geometry_3d
from .geometry_readouts import write_sprint02b_html
from .models import ExplorerCase, OrderedFamily, ToolAxis
from .plots import (
    plot_branch_trajectory,
    plot_case_schematic,
    plot_classification_counts,
    plot_descriptor_histogram,
    plot_family_case_counts,
    plot_winding_pair_counts,
)
from .readouts import (
    write_index_html,
    write_json,
    write_sprint00_html,
    write_sprint01_html,
    write_sprint02_html,
    write_sprint03_html,
)


def build_readouts(outdir: Path, sample_count: int) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    figures_dir = outdir / "figures"
    data_dir = outdir / "data"
    figures_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    family_plot = figures_dir / "family_case_counts.png"
    plot_family_case_counts(family_plot)
    schematic_files: list[str] = []
    for family in ORDERED_FAMILIES:
        path = figures_dir / f"schematic_{family.value.lower()}.png"
        plot_case_schematic(family.value, path)
        schematic_files.append(str(path.relative_to(outdir)))
    write_sprint00_html(outdir, str(family_plot.relative_to(outdir)), schematic_files)

    all_samples = []
    for family in ORDERED_FAMILIES:
        all_samples.extend(generate_geometry_samples(family, count=sample_count, seed=101))
    write_json(data_dir / "geometry_samples.json", all_samples)
    histogram_paths = []
    for descriptor_name in ("center_distance_12", "twist_23_deg", "tetra_volume"):
        path = figures_dir / f"hist_{descriptor_name}.png"
        plot_descriptor_histogram(all_samples, descriptor_name, path)
        histogram_paths.append(str(path.relative_to(outdir)))
    write_sprint01_html(outdir, all_samples, histogram_paths)

    results = []
    for case in FAMILY_AXIS_CASES:
        family_samples = [sample for sample in all_samples if sample.family is case.family][: min(sample_count, 4)]
        for sample in family_samples:
            results.append(classify_mock_branch(sample, case))
    write_json(data_dir / "mock_branch_results.json", results)
    classification_plot = figures_dir / "classification_counts.png"
    winding_pair_plot = figures_dir / "winding_pair_counts.png"
    plot_classification_counts(results, classification_plot)
    plot_winding_pair_counts(results, winding_pair_plot)
    write_sprint02_html(
        outdir,
        results,
        str(classification_plot.relative_to(outdir)),
        winding_pair_plot=str(winding_pair_plot.relative_to(outdir)),
    )

    # Sprint V02B: physical geometry objects replace the V01 random-descriptor
    # corpus as the input source for all future kinematic experiments.
    physical_samples = []
    image_by_sample: dict[str, str] = {}
    physical_count = max(2, sample_count)
    for family in ORDERED_FAMILIES:
        family_samples = generate_physical_geometry_samples(family, count=physical_count, seed=202)
        physical_samples.extend(family_samples)
        for sample in family_samples[:2]:
            path = figures_dir / f"physical_{sample.sample_id}.png"
            plot_physical_geometry_3d(sample.geometry, path)
            image_by_sample[sample.sample_id] = str(path.relative_to(outdir))
    physical_json = data_dir / "physical_geometry_samples.json"
    write_json(physical_json, physical_samples)
    write_sprint02b_html(
        outdir,
        physical_samples,
        image_by_sample=image_by_sample,
        json_path=str(physical_json.relative_to(outdir)),
    )

    # Sprint V03: SE(3) closure + continuation on V02B physical UUUR samples only.
    uuur_samples = [sample for sample in physical_samples if sample.family is OrderedFamily.UUUR][:2]
    closure_results = []
    trajectories = []
    for sample in uuur_samples:
        for tool_axis in (ToolAxis.A, ToolAxis.B):
            case = ExplorerCase(family=OrderedFamily.UUUR, tool_axis=tool_axis)
            trajectory, result = continue_physical_uuur_sample(
                sample,
                case,
                config=ContinuationConfig(step=0.08, max_steps=120),
            )
            trajectories.append(trajectory)
            closure_results.append(result)
    trajectory_json = data_dir / "branch_trajectories.json"
    write_json(trajectory_json, trajectories)
    write_json(data_dir / "uuur_closure_branch_results.json", closure_results)
    trajectory_plot = figures_dir / "uuur_branch_trajectory.png"
    plot_branch_trajectory(trajectories[0], trajectory_plot)
    write_sprint03_html(
        outdir,
        results=closure_results,
        trajectories=trajectories,
        trajectory_plot=str(trajectory_plot.relative_to(outdir)),
        trajectory_json=str(trajectory_json.relative_to(outdir)),
    )

    write_index_html(
        outdir,
        sprint_pages=[
            "sprint_00_overview.html",
            "sprint_01_parameter_inventory.html",
            "sprint_02_mock_branch_results.html",
            "sprint_02b_physical_geometry.html",
            "sprint_03_closure.html",
        ],
        image_files=[
            str(family_plot.relative_to(outdir)),
            *schematic_files,
            *histogram_paths,
            str(classification_plot.relative_to(outdir)),
            str(winding_pair_plot.relative_to(outdir)),
            *image_by_sample.values(),
            str(trajectory_plot.relative_to(outdir)),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build spatial 4-bar explorer readouts.")
    parser.add_argument("--outdir", type=Path, default=Path("outputs/spatial4bar_explorer"))
    parser.add_argument("--sample-count", type=int, default=6)
    args = parser.parse_args()
    build_readouts(args.outdir, sample_count=args.sample_count)


if __name__ == "__main__":
    main()
