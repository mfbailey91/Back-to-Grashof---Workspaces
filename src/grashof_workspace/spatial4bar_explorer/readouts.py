from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .descriptors import grouped_descriptor_inventory
from .families import FAMILY_AXIS_CASES, FAMILY_NOTES, FAMILY_PARENT_MAP, ORDERED_FAMILIES
from .models import BranchResult, GeometrySample, dataclass_to_jsonable


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
    image_html = "\n".join(f'<img src="{img}" alt="{img}" style="max-width: 480px; margin: 8px;">' for img in histogram_files)
    sample_rows = []
    for sample in samples[:8]:
        desc_map = sample.descriptor_map()
        sample_rows.append(
            f"<tr><td>{sample.sample_id}</td><td>{sample.family.value}</td><td>{sample.seed}</td>"
            f"<td>{desc_map['center_distance_12']:.3f}</td><td>{desc_map['center_distance_23']:.3f}</td>"
            f"<td>{desc_map['twist_23_deg']:.1f}</td><td>{desc_map['tetra_volume']:.3f}</td></tr>"
        )
    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Sprint 01</title></head>
<body>
<h1>Sprint 01 — parameter inventory and first sampled geometries</h1>
<p>Focus: list a broad parameter inventory, generate initial synthetic geometry instances, and graph several descriptor distributions.</p>
{''.join(sections)}
<h2>Descriptor histograms</h2>
{image_html}
<h2>Representative samples</h2>
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Sample</th><th>Family</th><th>Seed</th><th>L12</th><th>L23</th><th>twist23</th><th>tetra volume</th></tr>
{''.join(sample_rows)}
</table>
</body></html>
"""
    (outdir / "sprint_01_parameter_inventory.html").write_text(html, encoding="utf-8")


def write_sprint02_html(outdir: Path, results: list[BranchResult], classification_plot: str) -> None:
    rows = []
    for result in results[:20]:
        rows.append(
            f"<tr><td>{result.sample_id}</td><td>{result.case.family.value}</td><td>{result.case.tool_axis.value}</td>"
            f"<td>{result.w_alpha}</td><td>{result.w_beta}</td><td>{result.class_alpha.value}</td><td>{result.class_beta.value}</td>"
            f"<td>{', '.join(result.notes)}</td></tr>"
        )
    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Sprint 02</title></head>
<body>
<h1>Sprint 02 — mock branch classification and winding scaffold</h1>
<p>Focus: stand up the branch-result data model and generate first readouts that will later be filled by closure continuation and true winding calculations.</p>
<img src=\"{classification_plot}\" alt=\"classification counts\" style=\"max-width: 900px;\">
<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
<tr><th>Sample</th><th>Family</th><th>Tool axis</th><th>w_alpha</th><th>w_beta</th><th>class_alpha</th><th>class_beta</th><th>notes</th></tr>
{''.join(rows)}
</table>
</body></html>
"""
    (outdir / "sprint_02_mock_branch_results.html").write_text(html, encoding="utf-8")
