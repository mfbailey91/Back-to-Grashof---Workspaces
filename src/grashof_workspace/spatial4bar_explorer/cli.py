from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import classify_mock_branch
from .closure import audit_reference_geometry
from .continuation import continue_branch
from .continuation_plots import (
    animate_branch,
    plot_branch_snapshots,
    plot_closure_residual,
    plot_continuation_coordinates,
    plot_reference_mobility_audit,
    plot_singularity_margin,
    plot_tool_coordinate_phase,
)
from .continuation_readouts import write_sprint03_html
from .descriptors import generate_geometry_samples
from .families import FAMILY_AXIS_CASES, ORDERED_FAMILIES
from .geometry_descriptors import generate_physical_geometry_samples
from .geometry_plots import plot_physical_geometry_3d
from .geometry_readouts import write_sprint02b_html
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
        family_samples = [sample for sample in all_samples if sample.family is case.family][
            : min(sample_count, 4)
        ]
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

    # Sprint V03: one general seven-coordinate closure kernel. Each physical
    # mechanism is solved once; tool_alpha and tool_beta are read from the same
    # continued branch rather than treated as two separate mechanism solves.
    canonical_by_family = {
        sample.family: sample.geometry
        for sample in physical_samples
        if sample.sample_id.endswith("_000")
    }
    audits = [audit_reference_geometry(canonical_by_family[family]) for family in ORDERED_FAMILIES]
    audit_json = data_dir / "v03_reference_closure_audits.json"
    write_json(audit_json, audits)
    mobility_plot = figures_dir / "v03_reference_mobility_audit.png"
    plot_reference_mobility_audit(audits, mobility_plot)

    traces = [
        continue_branch(canonical_by_family[family], steps=60, step_size=0.04)
        for family in ORDERED_FAMILIES
    ]
    trace_json = data_dir / "v03_continuation_traces.json"
    write_json(trace_json, traces)
    detailed_trace = next(trace for trace in traces if trace.family == "UUUR")
    detailed_geometry = canonical_by_family[next(f for f in ORDERED_FAMILIES if f.value == "UUUR")]
    coordinate_plot = figures_dir / "v03_uuur_coordinates.png"
    residual_plot = figures_dir / "v03_uuur_closure_residual.png"
    singularity_plot = figures_dir / "v03_uuur_singularity_margin.png"
    phase_plot = figures_dir / "v03_uuur_tool_phase.png"
    plot_continuation_coordinates(detailed_trace, coordinate_plot)
    plot_closure_residual(detailed_trace, residual_plot)
    plot_singularity_margin(detailed_trace, singularity_plot)
    plot_tool_coordinate_phase(detailed_trace, phase_plot)
    snapshot_dir = figures_dir / "v03_uuur_snapshots"
    snapshot_files = plot_branch_snapshots(detailed_geometry, detailed_trace, snapshot_dir, count=5)
    snapshot_relpaths = [str(path.relative_to(outdir)) for path in snapshot_files]
    animation_relpaths: list[tuple[str, str]] = []
    for family, trace in zip(ORDERED_FAMILIES, traces, strict=True):
        animation_plot = figures_dir / f"v03_{family.value.lower()}_branch.gif"
        animate_branch(canonical_by_family[family], trace, animation_plot)
        animation_relpaths.append((family.value, str(animation_plot.relative_to(outdir))))
    write_sprint03_html(
        outdir,
        audits=audits,
        traces=traces,
        detailed_family="UUUR",
        mobility_plot=str(mobility_plot.relative_to(outdir)),
        coordinate_plot=str(coordinate_plot.relative_to(outdir)),
        residual_plot=str(residual_plot.relative_to(outdir)),
        singularity_plot=str(singularity_plot.relative_to(outdir)),
        phase_plot=str(phase_plot.relative_to(outdir)),
        animation_paths=animation_relpaths,
        snapshot_paths=snapshot_relpaths,
        audit_json=str(audit_json.relative_to(outdir)),
        trace_json=str(trace_json.relative_to(outdir)),
    )

    write_index_html(
        outdir,
        sprint_pages=[
            "sprint_00_overview.html",
            "sprint_01_parameter_inventory.html",
            "sprint_02_mock_branch_results.html",
            "sprint_02b_physical_geometry.html",
            "sprint_03_closure_and_continuation.html",
        ],
        image_files=[
            str(family_plot.relative_to(outdir)),
            *schematic_files,
            *histogram_paths,
            str(classification_plot.relative_to(outdir)),
            str(winding_pair_plot.relative_to(outdir)),
            *image_by_sample.values(),
            str(mobility_plot.relative_to(outdir)),
            str(coordinate_plot.relative_to(outdir)),
            str(residual_plot.relative_to(outdir)),
            str(singularity_plot.relative_to(outdir)),
            str(phase_plot.relative_to(outdir)),
            *[path for _, path in animation_relpaths],
            *snapshot_relpaths,
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
