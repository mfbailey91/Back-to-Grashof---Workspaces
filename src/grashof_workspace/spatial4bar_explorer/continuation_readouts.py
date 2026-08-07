from __future__ import annotations

from pathlib import Path

from .closure import ClosureAudit
from .continuation import ContinuationTrace


def write_sprint03_html(
    outdir: Path,
    *,
    audits: list[ClosureAudit],
    traces: list[ContinuationTrace],
    detailed_family: str,
    mobility_plot: str,
    coordinate_plot: str,
    residual_plot: str,
    singularity_plot: str,
    phase_plot: str,
    animation_paths: list[tuple[str, str]],
    snapshot_paths: list[str],
    audit_json: str,
    trace_json: str,
) -> None:
    audit_rows = "".join(
        f"<tr><td>{audit.family}</td><td>{audit.coordinate_count}</td>"
        f"<td>{audit.closure_norm:.3e}</td><td>{audit.jacobian_rank}</td>"
        f"<td>{audit.jacobian_nullity}</td><td>{audit.smallest_nonzero_singular_value:.3e}</td>"
        f"<td>{audit.status}</td></tr>"
        for audit in audits
    )
    trace_rows = "".join(
        f"<tr><td>{trace.family}</td><td>{len(trace.points)}</td>"
        f"<td>{trace.points[-1].arclength:.3f}</td><td>{trace.converged_fraction:.3f}</td>"
        f"<td>{max(point.closure_norm for point in trace.points):.3e}</td>"
        f"<td>{min(point.smallest_singular_value for point in trace.points):.3e}</td></tr>"
        for trace in traces
    )
    snapshots = "".join(
        f'<img src="{path}" alt="{detailed_family} continued mechanism snapshot" style="max-width: 430px; margin: 6px;">'
        for path in snapshot_paths
    )
    detailed_animation = next(
        (path for family, path in animation_paths if family == detailed_family),
        animation_paths[0][1] if animation_paths else "",
    )
    family_animations = "".join(
        f'<figure style="display:inline-block; margin: 8px; vertical-align: top;">'
        f'<img src="{path}" alt="{family} driven branch animation" style="max-width: 420px;">'
        f"<figcaption>{family}</figcaption></figure>"
        for family, path in animation_paths
    )
    html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Sprint V03 — closure and continuation</title></head>
<body>
<h1>Sprint V03 — closure and continuation</h1>
<p><strong>STATUS:</strong> local one-dimensional closure branches only. No crank, winding, or dexterity classification is made in V03.</p>
<p>
V03 uses only V02B physical geometry. Every R/U/S family is expanded internally into seven ordered revolute solver coordinates.
The same six-constraint closure kernel is used for all six ordered families.
</p>
<h2>V03A — reference closure and mobility audit</h2>
<p>Expected regular result: 7 scalar coordinates, closure Jacobian rank 6, nullity 1.</p>
<img src="{mobility_plot}" alt="V03A mobility audit" style="max-width: 900px;">
<table border="1" cellpadding="6" cellspacing="0">
<tr><th>Family</th><th>Coordinates</th><th>||r(0)||</th><th>Rank</th><th>Nullity</th><th>sigma_min+</th><th>Status</th></tr>
{audit_rows}
</table>
<p><a href="{audit_json}">Closure-audit JSON</a></p>
<h2>V03B — detailed {detailed_family} branch proof</h2>
<p>
Pseudo-arclength predictor/corrector continuation follows the local null direction of the closure Jacobian.
The plots below are diagnostics of a real closure branch segment; they are not yet a full-cycle continuation.
</p>
<img src="{coordinate_plot}" alt="seven joint coordinate traces" style="max-width: 900px;">
<img src="{residual_plot}" alt="closure residual" style="max-width: 760px;">
<img src="{singularity_plot}" alt="singularity margin" style="max-width: 760px;">
<img src="{phase_plot}" alt="tool U coordinate path" style="max-width: 620px;">
<h3>Driven branch animation</h3>
<p>
The GIF advances along continuation arclength on the local one-DOF closure manifold.
This is local branch motion only; it is not a crank, winding, or full-cycle proof.
</p>
<img src="{detailed_animation}" alt="{detailed_family} driven branch animation" style="max-width: 640px;">
<h3>3D branch snapshots</h3>
{snapshots}
<h2>V03C — same kernel across all six families</h2>
<table border="1" cellpadding="6" cellspacing="0">
<tr><th>Family</th><th>Points</th><th>Final arclength</th><th>Converged fraction</th><th>Max closure residual</th><th>Min sigma_min+</th></tr>
{trace_rows}
</table>
<p><a href="{trace_json}">Continuation-trace JSON</a></p>
<h3>Driven branch animations (all families)</h3>
<p>
Each GIF uses the same seven-coordinate closure/continuation kernel on that family's V02B reference geometry.
Motion is along local continuation arclength only; not a crank or winding classification.
</p>
{family_animations}
<h2>Interpretation guardrails</h2>
<ul>
<li>V03 establishes local closure motion, not a crank condition.</li>
<li><code>tool_alpha</code> and <code>tool_beta</code> are both recorded from one mechanism solve; the mechanism is not solved twice.</li>
<li>S-joint x/y/z coordinates are solver-chart coordinates only. They must not be promoted to invariant Grashof descriptors.</li>
<li>Closed-loop winding and branch return belong to V04.</li>
</ul>
</body>
</html>
"""
    (outdir / "sprint_03_closure_and_continuation.html").write_text(html, encoding="utf-8")
