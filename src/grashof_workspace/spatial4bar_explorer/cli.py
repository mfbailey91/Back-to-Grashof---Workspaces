from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import classify_mock_branch
from .descriptors import generate_geometry_samples
from .families import FAMILY_AXIS_CASES, ORDERED_FAMILIES
from .plots import (
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

    write_index_html(
        outdir,
        sprint_pages=[
            "sprint_00_overview.html",
            "sprint_01_parameter_inventory.html",
            "sprint_02_mock_branch_results.html",
        ],
        image_files=[
            str(family_plot.relative_to(outdir)),
            *schematic_files,
            *histogram_paths,
            str(classification_plot.relative_to(outdir)),
            str(winding_pair_plot.relative_to(outdir)),
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
