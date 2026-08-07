from __future__ import annotations

from pathlib import Path

from .winding import WindingClassification


def write_sprint04_html(
    outdir: Path,
    *,
    classifications: list[WindingClassification],
    crank_example: WindingClassification | None,
    rocker_example: WindingClassification | None,
    winding_summary_plot: str,
    classification_plot: str,
    crank_angle_plot: str | None,
    rocker_angle_plot: str | None,
    results_json: str,
    traces_json: str,
) -> None:
    rows = "".join(
        (
            f"<tr><td>{item.sample_id}</td><td>{item.cycle.status}</td>"
            f"<td>{item.cycle.direction}</td><td>{len(item.cycle.points)}</td>"
            f"<td>{item.w_alpha if item.w_alpha is not None else '—'}</td>"
            f"<td>{item.w_beta if item.w_beta is not None else '—'}</td>"
            f"<td>{item.class_alpha.value}</td><td>{item.class_beta.value}</td>"
            f"<td>{'yes' if item.cycle.returned else 'no'}</td></tr>"
        )
        for item in classifications
    )

    def _card(title: str, item: WindingClassification | None, plot: str | None) -> str:
        if item is None:
            return (
                f"<h3>{title}</h3>"
                "<p><strong>REVIEW:</strong> no example found under the default cycle budget.</p>"
            )
        plot_html = f'<img src="{plot}" alt="{title}" style="max-width: 820px;">' if plot else ""
        return f"""
<h3>{title}: {item.sample_id}</h3>
<p>
W=({item.w_alpha}, {item.w_beta});
classes=({item.class_alpha.value}, {item.class_beta.value});
returned={item.cycle.returned}; direction={item.cycle.direction}; points={len(item.cycle.points)}.
</p>
{plot_html}
"""

    html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Sprint V04 — winding and crank atlas</title></head>
<body>
<h1>Sprint V04 — true winding and crank atlas (UUUR-first)</h1>
<p>
<strong>STATUS:</strong> windings below are computed from continued one-DOF closure cycles.
They are <em>not</em> V02 mock heuristics and are <em>not</em> conventional planar Grashof labels.
</p>
<p>
Each UUUR physical sample is solved once with the V03 seven-coordinate kernel.
<code>tool_alpha</code> and <code>tool_beta</code> windings are read from that single returned cycle.
</p>
<h2>Winding summary</h2>
<img src="{winding_summary_plot}" alt="winding summary" style="max-width: 980px;">
<img src="{classification_plot}" alt="classification counts" style="max-width: 900px;">
<table border="1" cellpadding="6" cellspacing="0">
<tr>
<th>Sample</th><th>Cycle status</th><th>Direction</th><th>Points</th>
<th>w_alpha</th><th>w_beta</th><th>class_alpha</th><th>class_beta</th><th>Returned</th>
</tr>
{rows}
</table>
<p><a href="{results_json}">Winding-result JSON</a> · <a href="{traces_json}">Cycle-trace JSON</a></p>
<h2>Representative examples</h2>
{_card("Crank example", crank_example, crank_angle_plot)}
{_card("Rocker example", rocker_example, rocker_angle_plot)}
<h2>Interpretation guardrails</h2>
<ul>
<li><code>crank</code> means <code>|w_i| ≥ 1</code> on a returned cycle for that tool coordinate.</li>
<li><code>rocker</code> means the cycle returned and <code>w_i = 0</code>.</li>
<li>Conventional planar double-crank / crank-rocker / double-rocker labels are not used here.</li>
<li>Other ordered families remain V03 diagnostics until UUUR winding is verified.</li>
<li>Descriptor-trend mining belongs to V05.</li>
</ul>
</body>
</html>
"""
    (outdir / "sprint_04_winding_and_crank.html").write_text(html, encoding="utf-8")
