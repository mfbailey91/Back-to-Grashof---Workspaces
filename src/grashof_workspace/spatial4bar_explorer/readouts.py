from __future__ import annotations

import json
from pathlib import Path

from .analysis import summarize_class_counts, summarize_winding_pairs
from .descriptors import grouped_descriptor_inventory
from .families import FAMILY_AXIS_CASES, FAMILY_NOTES, FAMILY_PARENT_MAP, ORDERED_FAMILIES
from .models import BranchClass, BranchResult, GeometrySample, dataclass_to_jsonable

BRANCH_RESULT_SCHEMA_FIELDS: tuple[tuple[str, str], ...] = (
    ("sample_id", "Geometry sample identifier"),
    ("case", "ExplorerCase with family and tool-axis choice"),
    ("branch_id", "Branch label within a sample/case"),
    ("branch_closed", "Whether the continued branch returned to its seed"),
    ("singularity_count", "Counted singularity encounters on the branch"),
    ("w_alpha", "Integer winding of tool coordinate alpha (None if undefined)"),
    ("w_beta", "Integer winding of tool coordinate beta (None if undefined)"),
    ("class_alpha", "Crank/rocker/... label for alpha"),
    ("class_beta", "Crank/rocker/... label for beta"),
    ("tool_range_alpha", "Observed tool alpha range in radians (None if undefined)"),
    ("tool_range_beta", "Observed tool beta range in radians (None if undefined)"),
    ("notes", "Human-readable flags; includes mock_placeholder for Sprint V02"),
)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(dataclass_to_jsonable(payload), indent=2), encoding="utf-8")


def write_index_html(outdir: Path, *, sprint_pages: list[str], image_files: list[str]) -> None:
    links = "\n".join(f'<li><a href="{page}">{page}</a></li>' for page in sprint_pages)
    images = "\n".join(f'<li><a href="{image}">{image}</a></li>' for image in image_files)
    html = f"""<!doctype html>
<html lang=\"en\">
<head><meta charset=\"utf-8\"><title>4-Bar Explorer</title></head>
<body>
<h1>Spatial 4-Bar Explorer</h1>
<p>Scaffold readouts for the aligned-terminal 6R one-DOF spatial 4-bar exploration track.</p>
<h2>Sprint pages</h2>
<ul>{links}</ul>
<h2>Generated figures</h2>
<ul>{images}</ul>
</body></html>
"""
    (outdir / "index.html").write_text(html, encoding="utf-8")


def write_sprint00_html(outdir: Path, family_plot: str, schematics: list[str]) -> None:
    family_rows = []
    for family in ORDERED_FAMILIES:
        family_rows.append(
            f"<tr><td>{family.value}</td><td>{FAMILY_PARENT_MAP[family]}</td><td>{FAMILY_NOTES[family]}</td></tr>"
        )
    case_rows = []
    for case in FAMILY_AXIS_CASES:
        case_rows.append(
            f"<tr><td>{case.family.value}</td><td>{case.tool_axis.value}</td><td>{case.slug}</td></tr>"
        )
    schematics_html = "\n".join(f'<li><a href="{name}">{name}</a></li>' for name in schematics)
    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Sprint 00</title></head>
<body>
<h1>Sprint 00 — family inventory and explorer shell</h1>
<p>Focus: enumerate the six ordered one-DOF families and the twelve virtual-tool-axis test cases.</p>
<img src=\"{family_plot}\" alt=\"family case counts\" style=\"max-width: 900px;\">
<h2>Ordered family inventory</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Family</th><th>Origin</th><th>Note</th></tr>
{''.join(family_rows)}
</table>
<h2>Tool-axis case inventory (12 total)</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Family</th><th>Tool axis</th><th>Case slug</th></tr>
{''.join(case_rows)}
</table>
<h2>Family schematics</h2>
<ul>{schematics_html}</ul>
</body></html>
"""
    (outdir / "sprint_00_overview.html").write_text(html, encoding="utf-8")


def write_sprint01_html(outdir: Path, samples: list[GeometrySample], histogram_files: list[str]) -> None:
    grouped = grouped_descriptor_inventory()
    sections: list[str] = []
    for group_name, items in grouped.items():
        li = "".join(f"<li><code>{name}</code> — {description}</li>" for name, description in items)
        sections.append(f"<h3>{group_name}</h3><ul>{li}</ul>")
    family_counts: dict[str, int] = {}
    for sample in samples:
        key = sample.family.value
        family_counts[key] = family_counts.get(key, 0) + 1
    family_count_html = "".join(f"<li>{family}: {count}</li>" for family, count in sorted(family_counts.items()))
    image_html = "\n".join(f'<img src="{img}" alt="{img}" style="max-width: 480px; margin: 8px;">' for img in histogram_files)
    sample_rows = []
    for sample in samples[:12]:
        desc_map = sample.descriptor_map()
        sample_rows.append(
            f"<tr><td>{sample.sample_id}</td><td>{sample.family.value}</td><td>{sample.seed}</td>"
            f"<td>{desc_map['center_distance_12']:.3f}</td><td>{desc_map['center_distance_23']:.3f}</td>"
            f"<td>{desc_map['twist_23_deg']:.1f}</td><td>{desc_map['tetra_volume']:.3f}</td></tr>"
        )
    representative_by_metric: list[tuple[str, GeometrySample]] = []
    if samples:
        representative_by_metric = [
            ("min center_distance_12", min(samples, key=lambda s: float(s.descriptor_map()["center_distance_12"]))),
            ("max center_distance_12", max(samples, key=lambda s: float(s.descriptor_map()["center_distance_12"]))),
            ("min twist_23_deg", min(samples, key=lambda s: float(s.descriptor_map()["twist_23_deg"]))),
            ("max twist_23_deg", max(samples, key=lambda s: float(s.descriptor_map()["twist_23_deg"]))),
            ("min tetra_volume", min(samples, key=lambda s: float(s.descriptor_map()["tetra_volume"]))),
            ("max tetra_volume", max(samples, key=lambda s: float(s.descriptor_map()["tetra_volume"]))),
        ]
    representative_rows = []
    for label, sample in representative_by_metric:
        desc_map = sample.descriptor_map()
        representative_rows.append(
            f"<tr><td>{label}</td><td>{sample.sample_id}</td><td>{sample.family.value}</td>"
            f"<td>{desc_map['center_distance_12']:.3f}</td><td>{desc_map['twist_23_deg']:.1f}</td>"
            f"<td>{desc_map['tetra_volume']:.3f}</td></tr>"
        )
    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Sprint 01</title></head>
<body>
<h1>Sprint 01 — parameter inventory and first sampled geometries</h1>
<p>Focus: list a broad parameter inventory, generate initial synthetic geometry instances, and graph several descriptor distributions.</p>
<h2>Synthetic corpus summary</h2>
<p>Total samples: {len(samples)}</p>
<ul>{family_count_html}</ul>
<h2>Descriptor inventory</h2>
{''.join(sections)}
<h2>Descriptor histograms</h2>
{image_html}
<h2>Representative samples</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Sample</th><th>Family</th><th>Seed</th><th>L12</th><th>L23</th><th>twist23</th><th>tetra volume</th></tr>
{''.join(sample_rows)}
</table>
<h2>Representative edge cases by descriptor</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Criterion</th><th>Sample</th><th>Family</th><th>L12</th><th>twist23</th><th>tetra volume</th></tr>
{''.join(representative_rows)}
</table>
</body></html>
"""
    (outdir / "sprint_01_parameter_inventory.html").write_text(html, encoding="utf-8")


def write_sprint02_html(
    outdir: Path,
    results: list[BranchResult],
    classification_plot: str,
    winding_pair_plot: str | None = None,
) -> None:
    class_counts = summarize_class_counts(results)
    winding_counts = summarize_winding_pairs(results)
    schema_rows = "".join(
        f"<tr><td><code>{name}</code></td><td>{description}</td></tr>"
        for name, description in BRANCH_RESULT_SCHEMA_FIELDS
    )
    label_rows = "".join(
        f"<tr><td><code>{label.value}</code></td><td>{class_counts.get(label.value, 0)}</td></tr>"
        for label in BranchClass
    )
    winding_rows = "".join(
        f"<tr><td><code>{pair}</code></td><td>{count}</td></tr>" for pair, count in winding_counts.items()
    )
    winding_img = (
        f'<img src="{winding_pair_plot}" alt="winding pair counts" style="max-width: 900px;">'
        if winding_pair_plot
        else ""
    )

    def _fmt_range(value: float | None) -> str:
        return "—" if value is None else f"{value:.3f}"

    def _fmt_winding(value: int | None) -> str:
        return "—" if value is None else str(value)

    rows = []
    for result in results[:24]:
        rows.append(
            f"<tr><td>{result.sample_id}</td><td>{result.case.family.value}</td><td>{result.case.tool_axis.value}</td>"
            f"<td>{result.branch_id}</td><td>{result.branch_closed}</td>"
            f"<td>{_fmt_winding(result.w_alpha)}</td><td>{_fmt_winding(result.w_beta)}</td>"
            f"<td>{result.class_alpha.value}</td><td>{result.class_beta.value}</td>"
            f"<td>{_fmt_range(result.tool_range_alpha)}</td><td>{_fmt_range(result.tool_range_beta)}</td>"
            f"<td>{', '.join(result.notes)}</td></tr>"
        )

    representative_rows: list[str] = []
    seen_classes: set[str] = set()
    for result in results:
        for cls in (result.class_alpha, result.class_beta):
            if cls.value in seen_classes:
                continue
            seen_classes.add(cls.value)
            representative_rows.append(
                f"<tr><td>{cls.value}</td><td>{result.sample_id}</td><td>{result.case.slug}</td>"
                f"<td>{result.branch_id}</td><td>{_fmt_winding(result.w_alpha)}</td>"
                f"<td>{_fmt_winding(result.w_beta)}</td></tr>"
            )

    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Sprint 02</title></head>
<body>
<h1>Sprint 02 — mock branch classification and winding scaffold</h1>
<p><strong>MOCK / PLACEHOLDER:</strong> windings and classifications below are heuristic stand-ins.
True loop-closure continuation arrives in Sprint V03; true winding arrives in Sprint V04.</p>
<p>Focus: stand up the branch-result data model and generate first readouts that will later be filled by closure continuation and true winding calculations.</p>
<h2>BranchResult schema</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Field</th><th>Meaning</th></tr>
{schema_rows}
</table>
<h2>Classification label inventory</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Label</th><th>Count (alpha+beta)</th></tr>
{label_rows}
</table>
<h2>Mock winding-pair summary</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Pair (w_alpha, w_beta)</th><th>Count</th></tr>
{winding_rows}
</table>
<img src=\"{classification_plot}\" alt=\"classification counts\" style=\"max-width: 900px;\">
{winding_img}
<h2>Representative class examples</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Class</th><th>Sample</th><th>Case</th><th>Branch</th><th>w_alpha</th><th>w_beta</th></tr>
{''.join(representative_rows)}
</table>
<h2>Mock branch results</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Sample</th><th>Family</th><th>Tool axis</th><th>Branch</th><th>Closed</th><th>w_alpha</th><th>w_beta</th><th>class_alpha</th><th>class_beta</th><th>range_alpha</th><th>range_beta</th><th>notes</th></tr>
{''.join(rows)}
</table>
</body></html>
"""
    (outdir / "sprint_02_mock_branch_results.html").write_text(html, encoding="utf-8")
