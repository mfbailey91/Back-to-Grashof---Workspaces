from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import classify_mock_branch
from .axis_drive import (
    animate_axis_drive,
    drive_tool_axis,
    plot_axis_drive_coordinates,
)
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
from .geometry import PhysicalGeometrySample
from .geometry_descriptors import generate_physical_geometry_samples
from .geometry_plots import plot_physical_geometry_3d
from .geometry_readouts import write_sprint02b_html
from .models import OrderedFamily, ToolAxis
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
from .winding import classify_physical_sample, select_crank_and_rocker_examples
from .winding_plots import (
    plot_classification_cards,
    plot_unwrapped_tool_angles,
    plot_winding_summary,
)
from .winding_readouts import write_sprint04_html


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
    physical_samples: list[PhysicalGeometrySample] = []
    image_by_sample: dict[str, str] = {}
    physical_count = max(2, sample_count)
    for family in ORDERED_FAMILIES:
        physical_family_samples = generate_physical_geometry_samples(
            family, count=physical_count, seed=202
        )
        physical_samples.extend(physical_family_samples)
        for physical_sample in physical_family_samples[:2]:
            path = figures_dir / f"physical_{physical_sample.sample_id}.png"
            plot_physical_geometry_3d(physical_sample.geometry, path)
            image_by_sample[physical_sample.sample_id] = str(path.relative_to(outdir))
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

    axis_drive_cards: list[tuple[str, str, str, str, str, str, str, bool, bool]] = []
    axis_drive_traces: list[object] = []
    for family in ORDERED_FAMILIES:
        geometry = canonical_by_family[family]
        trace_a = drive_tool_axis(geometry, ToolAxis.A)
        trace_b = drive_tool_axis(geometry, ToolAxis.B)
        axis_drive_traces.extend((trace_a, trace_b))
        a_gif = figures_dir / f"v03_{family.value.lower()}_tool_a_drive.gif"
        b_gif = figures_dir / f"v03_{family.value.lower()}_tool_b_drive.gif"
        a_plot = figures_dir / f"v03_{family.value.lower()}_tool_a_drive.png"
        b_plot = figures_dir / f"v03_{family.value.lower()}_tool_b_drive.png"
        animate_axis_drive(geometry, trace_a, a_gif)
        animate_axis_drive(geometry, trace_b, b_gif)
        plot_axis_drive_coordinates(trace_a, a_plot)
        plot_axis_drive_coordinates(trace_b, b_plot)
        axis_drive_cards.append(
            (
                family.value,
                str(a_gif.relative_to(outdir)),
                str(b_gif.relative_to(outdir)),
                str(a_plot.relative_to(outdir)),
                str(b_plot.relative_to(outdir)),
                trace_a.status,
                trace_b.status,
                trace_a.full_input_turn,
                trace_b.full_input_turn,
            )
        )
    axis_drive_json = data_dir / "v03_tool_axis_drive_traces.json"
    write_json(axis_drive_json, axis_drive_traces)
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
        axis_drive_cards=axis_drive_cards,
        axis_drive_json=str(axis_drive_json.relative_to(outdir)),
    )

    # Sprint V04: UUUR-first true winding from returned continued cycles.
    uuur_samples = [
        sample for sample in physical_samples if sample.family is OrderedFamily.UUUR
    ]
    # Prefer a slightly denser UUUR corpus so crank and rocker examples coexist.
    if len(uuur_samples) < 6:
        uuur_samples = generate_physical_geometry_samples(
            OrderedFamily.UUUR, count=max(6, physical_count), seed=202
        )
    v04_classifications = [
        classify_physical_sample(sample, step_size=0.05, max_steps=1200)
        for sample in uuur_samples
    ]
    cycle_json = data_dir / "v04_uuur_cycle_traces.json"
    results_json = data_dir / "v04_uuur_winding_results.json"
    write_json(cycle_json, [item.cycle for item in v04_classifications])
    write_json(results_json, v04_classifications)
    winding_summary_plot = figures_dir / "v04_uuur_winding_summary.png"
    classification_plot_v04 = figures_dir / "v04_uuur_classification_counts.png"
    plot_winding_summary(v04_classifications, winding_summary_plot)
    plot_classification_cards(v04_classifications, classification_plot_v04)
    crank_example, rocker_example = select_crank_and_rocker_examples(v04_classifications)
    crank_angle_plot = figures_dir / "v04_uuur_crank_unwrapped.png"
    rocker_angle_plot = figures_dir / "v04_uuur_rocker_unwrapped.png"
    crank_rel: str | None = None
    rocker_rel: str | None = None
    if crank_example is not None:
        plot_unwrapped_tool_angles(crank_example, crank_angle_plot)
        crank_rel = str(crank_angle_plot.relative_to(outdir))
    if rocker_example is not None:
        plot_unwrapped_tool_angles(rocker_example, rocker_angle_plot)
        rocker_rel = str(rocker_angle_plot.relative_to(outdir))
    write_sprint04_html(
        outdir,
        classifications=v04_classifications,
        crank_example=crank_example,
        rocker_example=rocker_example,
        winding_summary_plot=str(winding_summary_plot.relative_to(outdir)),
        classification_plot=str(classification_plot_v04.relative_to(outdir)),
        crank_angle_plot=crank_rel,
        rocker_angle_plot=rocker_rel,
        results_json=str(results_json.relative_to(outdir)),
        traces_json=str(cycle_json.relative_to(outdir)),
    )

    write_index_html(
        outdir,
        sprint_pages=[
            "sprint_00_overview.html",
            "sprint_01_parameter_inventory.html",
            "sprint_02_mock_branch_results.html",
            "sprint_02b_physical_geometry.html",
            "sprint_03_closure_and_continuation.html",
            "sprint_04_winding_and_crank.html",
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
            *[card[1] for card in axis_drive_cards],
            *[card[2] for card in axis_drive_cards],
            *[card[3] for card in axis_drive_cards],
            *[card[4] for card in axis_drive_cards],
            str(winding_summary_plot.relative_to(outdir)),
            str(classification_plot_v04.relative_to(outdir)),
            *([crank_rel] if crank_rel else []),
            *([rocker_rel] if rocker_rel else []),
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
