from __future__ import annotations

from pathlib import Path

from .geometry import PhysicalGeometrySample
from .geometry_descriptors import physical_descriptor_inventory_by_group
from .models import OrderedFamily


def write_sprint02b_html(
    outdir: Path,
    samples: list[PhysicalGeometrySample],
    *,
    image_by_sample: dict[str, str],
    json_path: str,
) -> None:
    grouped = physical_descriptor_inventory_by_group()
    inventory_sections: list[str] = []
    for group, items in grouped.items():
        rows = "".join(
            f"<tr><td><code>{name}</code></td><td>{description}</td></tr>"
            for name, description in items
        )
        inventory_sections.append(
            f"<h3>{group}</h3><table border=\"1\" cellpadding=\"5\" cellspacing=\"0\">"
            f"<tr><th>Descriptor</th><th>Derived meaning</th></tr>{rows}</table>"
        )

    family_counts = {family.value: 0 for family in OrderedFamily}
    for sample in samples:
        family_counts[sample.family.value] += 1
    family_summary = "".join(
        f"<li><strong>{family}</strong>: {count} reference geometries</li>"
        for family, count in family_counts.items()
    )

    # Show one canonical (index 000) and one perturbed sample for every family.
    cards: list[str] = []
    by_family: dict[OrderedFamily, list[PhysicalGeometrySample]] = {}
    for sample in samples:
        by_family.setdefault(sample.family, []).append(sample)
    for family in OrderedFamily:
        family_samples = by_family.get(family, [])
        if not family_samples:
            continue
        chosen = [family_samples[0]]
        if len(family_samples) > 1:
            chosen.append(family_samples[1])
        for sample in chosen:
            descriptors = sample.descriptor_map()
            geometry = sample.geometry
            errors = geometry.validation_errors()
            image = image_by_sample.get(sample.sample_id, "")
            image_html = (
                f'<img src="{image}" alt="3D reference geometry {sample.sample_id}" style="max-width: 620px;">'
                if image
                else "<p>No image generated.</p>"
            )
            joint_rows = "".join(
                f"<tr><td>{joint.name}</td><td>{joint.kind.value}</td>"
                f"<td>{len(joint.motion_axes)}</td><td>{joint.center}</td></tr>"
                for joint in geometry.joints
            )
            cards.append(
                f"""
<section style="margin-bottom: 2rem;">
<h3>{sample.sample_id}</h3>
<p><strong>Family:</strong> {sample.family.value} &nbsp; <strong>Seed:</strong> {sample.seed} &nbsp;
<strong>Provenance:</strong> <code>{sample.provenance}</code></p>
<p><strong>Reference validation:</strong> {'PASS' if not errors else 'FAIL: ' + '; '.join(errors)}</p>
{image_html}
<table border="1" cellpadding="5" cellspacing="0">
<tr><th>Joint</th><th>Kind</th><th>Motion axes</th><th>Center</th></tr>
{joint_rows}
</table>
<p>
L12={float(descriptors['center_distance_12']):.3f},
L23={float(descriptors['center_distance_23']):.3f},
L34={float(descriptors['center_distance_34']):.3f},
L41={float(descriptors['center_distance_41']):.3f},
twist23={float(descriptors['twist_23_deg']):.1f} deg,
V={float(descriptors['tetra_volume']):.4f},
chirality={descriptors['chirality']}.
</p>
</section>
"""
            )

    html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Sprint V02B — physical geometry hardening</title></head>
<body>
<h1>Sprint V02B — physical geometry hardening</h1>
<p><strong>PHYSICAL GEOMETRY / NO CLOSURE SOLVE YET.</strong></p>
<p>
This sprint replaces the V01 random descriptor-vector corpus as the geometry source for all future kinematic experiments.
Each record below contains four actual joint centers, an orthonormal frame at every joint, the exact internal axis structure
for R/U/S joints, four rigid link adjacencies, and descriptors derived from that geometry.
</p>
<p>
The V01/V02 corpus remains useful only as readout/scaffold test data. It must not be used as crank evidence.
Sprint V03 will consume the V02B physical geometry objects when loop closure and continuation are implemented.
</p>
<h2>Corpus summary</h2>
<ul>{family_summary}</ul>
<p><a href="{json_path}">Physical geometry JSON export</a></p>
<h2>Geometry descriptor inventory</h2>
{''.join(inventory_sections)}
<h2>Representative 3D mechanisms</h2>
{''.join(cards)}
</body>
</html>
"""
    (outdir / "sprint_02b_physical_geometry.html").write_text(html, encoding="utf-8")
