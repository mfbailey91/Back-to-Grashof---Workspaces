"""Reproducible HTML/JSON/PNG/GIF readout for the L3-L7 ladder scaffold."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from PIL import Image

from .planar_l3 import default_l3_calibration_payload
from .registry import PARENT_CHILD_FAMILIES, RUNG_SPECS, program_payload
from .spatial_l4 import default_l4_equivalence_payload
from .spatial_l5 import default_l5_scaffold_payload
from .spatial_l6 import default_l6_scaffold_payload
from .u_drive import (
    conceptual_branch_samples,
    free_branch_contract,
    simple_drive_explanation,
    summarize_branch,
    task_derived_fiber_contract,
    u_rotation_matrix,
)


@dataclass(frozen=True, slots=True)
class ReadoutPaths:
    """Generated decomposition-ladder artifacts."""

    html: Path
    json: Path
    coordinate_plot: Path
    animation: Path | None


def _plot_u_coordinates(outpath: Path) -> None:
    samples = conceptual_branch_samples()
    s = np.asarray([sample.s for sample in samples], dtype=float)
    alpha = np.asarray([sample.alpha for sample in samples], dtype=float)
    beta = np.asarray([sample.beta for sample in samples], dtype=float)

    figure, axis = plt.subplots(figsize=(8.2, 4.6))
    axis.plot(s, alpha, label="alpha(s): circulates")
    axis.plot(s, beta, label="beta(s): rocks")
    axis.set_xlabel("branch parameter s")
    axis.set_ylabel("U coordinate [rad]")
    axis.set_title("Conceptual U-joint readout: drive s, observe alpha(s) and beta(s)")
    axis.legend()
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(outpath, dpi=160)
    plt.close(figure)


def _animate_u_drive(outpath: Path) -> None:
    samples = conceptual_branch_samples(sample_count=49)
    pointing_path = np.asarray([sample.pointing for sample in samples], dtype=float)
    figure = plt.figure(figsize=(6.0, 5.3))
    axis = figure.add_subplot(111, projection="3d")

    def _draw(frame_index: int) -> None:
        axis.cla()
        sample = samples[frame_index]
        rotation_x = u_rotation_matrix(sample.alpha, 0.0)
        second_axis = rotation_x @ np.array((0.0, 1.0, 0.0), dtype=float)
        pointing = np.asarray(sample.pointing, dtype=float)

        axis.plot(
            pointing_path[:, 0],
            pointing_path[:, 1],
            pointing_path[:, 2],
            linewidth=1.0,
            alpha=0.35,
            label="pointing path",
        )
        axis.quiver(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, length=0.9, normalize=True)
        axis.quiver(
            0.0,
            0.0,
            0.0,
            float(second_axis[0]),
            float(second_axis[1]),
            float(second_axis[2]),
            length=0.9,
            normalize=True,
        )
        axis.quiver(
            0.0,
            0.0,
            0.0,
            float(pointing[0]),
            float(pointing[1]),
            float(pointing[2]),
            length=1.0,
            normalize=True,
        )
        axis.scatter([pointing[0]], [pointing[1]], [pointing[2]], s=35)
        axis.set_xlim(-1.1, 1.1)
        axis.set_ylim(-1.1, 1.1)
        axis.set_zlim(-1.1, 1.1)
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        axis.set_zlabel("z")
        axis.set_title(
            "Conceptual U joint | param=s (not independently driven alpha/beta)\n"
            f"s={sample.s:.2f}, alpha(s)={sample.alpha:+.2f}, beta(s)={sample.beta:+.2f}"
        )
        axis.legend(loc="upper left", fontsize="small")

    animation = FuncAnimation(figure, _draw, frames=len(samples), interval=90)
    animation.save(outpath, writer=PillowWriter(fps=8))
    plt.close(figure)

    # Keep the committed explanatory artifact compact and offline-friendly.
    with Image.open(outpath) as image:
        frames: list[Image.Image] = []
        frame_count = int(getattr(image, "n_frames", 1))
        for frame_index in range(frame_count):
            image.seek(frame_index)
            frames.append(
                image.convert("RGB").quantize(
                    colors=96,
                    method=Image.Quantize.MEDIANCUT,
                )
            )
    if frames:
        frames[0].save(
            outpath,
            save_all=True,
            append_images=frames[1:],
            duration=125,
            loop=0,
            optimize=True,
            disposal=2,
        )


def _html_table_rows() -> str:
    rows: list[str] = []
    for spec in RUNG_SPECS:
        rows.append(
            "<tr>"
            f"<td><code>{spec.rung.value}</code></td>"
            f"<td>{spec.source_chain}</td>"
            f"<td>{spec.fixed_position_mobility}</td>"
            f"<td>{spec.target_label}</td>"
            f"<td>{spec.task_slice_count}</td>"
            f"<td>{spec.redundancy_slice_count}</td>"
            f"<td>{'direct' if spec.direct_leaf else 'fiber family'}</td>"
            "</tr>"
        )
    return "".join(rows)


def _family_rows() -> str:
    rows: list[str] = []
    for family in PARENT_CHILD_FAMILIES:
        rows.append(
            "<tr>"
            f"<td><code>{family.parent_label}</code></td>"
            f"<td>{family.parent_mobility}</td>"
            f"<td><code>{family.child_label}</code></td>"
            f"<td>{family.child_mobility}</td>"
            f"<td>{family.source_pattern}</td>"
            "</tr>"
        )
    return "".join(rows)


def _l3_calibration_rows(payload: dict[str, Any]) -> str:
    calibration = payload.get("l3_calibration")
    if not isinstance(calibration, dict):
        return ""
    summaries = calibration.get("summaries")
    if not isinstance(summaries, list):
        return ""
    rows: list[str] = []
    for entry in summaries:
        if not isinstance(entry, dict):
            continue
        rows.append(
            "<tr>"
            f"<td><code>{entry.get('rho')}</code></td>"
            f"<td><code>{entry.get('assemblable')}</code></td>"
            f"<td><code>{entry.get('designated_input_can_fully_rotate')}</code></td>"
            f"<td><code>{entry.get('dexterous')}</code></td>"
            f"<td><code>{entry.get('decomposition_status')}</code></td>"
            f"<td><code>{entry.get('predicate_reconstruction_match')}</code></td>"
            "</tr>"
        )
    return "".join(rows)


def _l4_equivalence_rows(payload: dict[str, Any]) -> str:
    section = payload.get("l4_equivalence")
    if not isinstance(section, dict):
        return ""
    summaries = section.get("summaries")
    if not isinstance(summaries, list):
        return ""
    rows: list[str] = []
    for entry in summaries:
        if not isinstance(entry, dict):
            continue
        rows.append(
            "<tr>"
            f"<td><code>{entry.get('architecture_id')}</code></td>"
            f"<td><code>{entry.get('axis_aggregation_status')}</code></td>"
            f"<td><code>{entry.get('closed_mechanism_status')}</code></td>"
            f"<td><code>{entry.get('orientation_curve_type')}</code></td>"
            f"<td><code>{entry.get('reconstruction_status')}</code></td>"
            f"<td><code>{entry.get('independent_reduced_solve_present')}</code></td>"
            "</tr>"
        )
    return "".join(rows)


def _l5_scaffold_rows(payload: dict[str, Any]) -> str:
    section = payload.get("l5_scaffold")
    if not isinstance(section, dict):
        return ""
    summary = section.get("summary")
    if not isinstance(summary, dict):
        return ""
    families = summary.get("candidate_families")
    family_list = (
        ", ".join(f"<code>{name}</code>" for name in families)
        if isinstance(families, list)
        else ""
    )
    return (
        "<tr>"
        f"<td><code>{summary.get('architecture_id')}</code></td>"
        f"<td><code>{summary.get('seed_rank_jp')}</code></td>"
        f"<td><code>{summary.get('seed_nullity_jp')}</code></td>"
        f"<td><code>{summary.get('seed_status')}</code></td>"
        f"<td>{family_list}</td>"
        f"<td><code>{summary.get('reconstruction_status')}</code></td>"
        f"<td><code>{summary.get('process_status')}</code></td>"
        "</tr>"
    )


def _l6_scaffold_rows(payload: dict[str, Any]) -> str:
    section = payload.get("l6_scaffold")
    if not isinstance(section, dict):
        return ""
    summary = section.get("summary")
    if not isinstance(summary, dict):
        return ""
    return (
        "<tr>"
        f"<td><code>{summary.get('architecture_id')}</code></td>"
        f"<td><code>{summary.get('seed_rank_jp')}</code></td>"
        f"<td><code>{summary.get('seed_nullity_jp')}</code></td>"
        f"<td><code>{summary.get('seed_status')}</code></td>"
        f"<td><code>{summary.get('target_space')}</code></td>"
        f"<td><code>{summary.get('child_count')}</code></td>"
        f"<td><code>{summary.get('reconstruction_status')}</code></td>"
        f"<td><code>{summary.get('process_status')}</code></td>"
        "</tr>"
    )


def render_ladder_html(
    *,
    payload: dict[str, Any],
    coordinate_plot_name: str,
    animation_name: str | None,
) -> str:
    """Return the standalone decomposition-ladder readout."""

    summary = payload["conceptual_u_branch"]
    animation_block = (
        f'<p><img src="{animation_name}" alt="conceptual U drive animation" '
        'style="max-width: 760px;"></p>'
        if animation_name is not None
        else "<p><em>Animation generation disabled for this run.</em></p>"
    )
    l3_rows = _l3_calibration_rows(payload)
    l3_section = (
        """
<h2>L3 planar calibration (trusted exact map)</h2>
<p>
Radius-level retrofit of the analytical planar 3R→4R result into shared ladder records.
<code>EXACT_GLOBAL</code> certifies the map at each radius; dexterity/rotatability remain
separate predicates. Process status stays <code>SCAFFOLD</code>. Active science remains
V05–V09.
</p>
<table>
<tr>
<th>rho</th><th>assemblable</th><th>rotatable</th><th>dexterous</th>
<th>map certificate</th><th>predicate match</th>
</tr>
"""
        + l3_rows
        + "</table>"
        if l3_rows
        else ""
    )
    l4_rows = _l4_equivalence_rows(payload)
    l4_section = (
        """
<h2>L4 spatial 4R equivalence (wraps V05)</h2>
<p>
Shared ladder records for the existing V05 independent closed-mechanism evidence.
Proximal <code>exact_u_pair_4r</code> is <code>LOCAL_ONLY</code> on the budget-limited
traced arc; generic architectures do not promote a child. Process stays
<code>SCAFFOLD</code>. Scientific source:
<a href="../kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html">V05D readout</a>.
</p>
<table>
<tr>
<th>architecture</th><th>axis aggregation</th><th>closed mechanism</th>
<th>orientation curve</th><th>reconstruction</th><th>independent reduce</th>
</tr>
"""
        + l4_rows
        + "</table>"
        if l4_rows
        else ""
    )
    l5_rows = _l5_scaffold_rows(payload)
    l5_section = (
        """
<h2>L5 spatial 5R scaffold (V06-mapped)</h2>
<p>
Architecture-scoped scaffold after the proximal exact-U gate: synthetic 5R seed audit
(<code>rank Jp=3</code>, <code>nullity=2</code>) plus a V06A1 <code>LOCAL_PATCH</code>
hexagonal chart. This is <strong>not</strong> a complete 2D parent component and
<strong>not</strong> pointing-image reconstruction. All family certificates stay
<code>UNRESOLVED</code>. V06A2 atlas remains next. Process status is <code>SCAFFOLD</code>.
</p>
<table>
<tr>
<th>architecture</th><th>seed rank Jp</th><th>seed nullity</th><th>seed status</th>
<th>candidate families</th><th>reconstruction</th><th>process</th>
</tr>
"""
        + l5_rows
        + "</table>"
        if l5_rows
        else ""
    )
    l6_rows = _l6_scaffold_rows(payload)
    l6_section = (
        """
<h2>L6 spatial 6R scaffold (V07-mapped)</h2>
<p>
Architecture-scoped scaffold after the proximal exact-U gate: synthetic non-aligned 6R
seed audit (<code>rank Jp=3</code>, <code>nullity=3</code>). This is
<strong>not</strong> a frozen SO(3) reference, <strong>not</strong> nested-slice
reconstruction, and <strong>not</strong> V08 terminal-roll quotient work. Children remain
empty until V07A. Process status is <code>SCAFFOLD</code>; reconstruction stays
<code>UNRESOLVED</code>.
</p>
<table>
<tr>
<th>architecture</th><th>seed rank Jp</th><th>seed nullity</th><th>seed status</th>
<th>target</th><th>children</th><th>reconstruction</th><th>process</th>
</tr>
"""
        + l6_rows
        + "</table>"
        if l6_rows
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Kinematic Decomposition Ladder L3–L7</title>
<style>
  body {{
    font-family: Georgia, "Times New Roman", serif;
    max-width: 980px;
    margin: 2rem auto;
    padding: 0 1.25rem 3rem;
    line-height: 1.48;
    color: #1a1a1a;
  }}
  h1, h2, h3 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.8rem 0 1.2rem; }}
  th, td {{
    border: 1px solid #bbb;
    padding: 0.45rem 0.55rem;
    text-align: left;
    vertical-align: top;
  }}
  th {{ background: #f3f3f3; }}
  code, pre {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.9em;
  }}
  pre {{ background: #f6f6f6; border: 1px solid #ddd; padding: 0.8rem 1rem; overflow-x: auto; }}
  .note {{
    background: #faf7f0;
    border-left: 3px solid #c4a35a;
    padding: 0.7rem 0.9rem;
    margin: 1rem 0;
  }}
</style>
</head>
<body>
<h1>Kinematic Decomposition Ladder — L3 through L7 (optional scaffold)</h1>
<p>
<strong>Active scientific sequence:</strong> <code>docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</code>.
This readout is an optional interface scaffold subordinate to that program. It does not demote
the V05 scoped closed-mechanism gate or promote L5–L7 claims beyond accepted scope.
</p>
<p>
The common implementation contract is: construct the exact fixed-position source parent,
introduce only enough task/redundancy level sets to obtain a one-dimensional source fiber,
compress that fiber into a known closed mechanism only where equivalence is certified, solve
the leaf, and reconstruct the parent task image from accepted fibers.
</p>

<pre>source open chain
  → fix Cartesian position
  → source parent of dimension m
  → impose m−1 justified scalar level sets
  → one-dimensional source fiber
  → candidate one-DOF closed-mechanism child
  → independent parent/child equivalence certificate
  → leaf continuation + winding/coverage
  → parent orientation/pointing reconstruction</pre>

<h2>Ladder</h2>
<table>
<tr>
<th>Rung</th><th>Source</th><th>Fixed-position mobility</th><th>Target</th>
<th>Task slices</th><th>Redundancy slices</th><th>Leaf construction</th>
</tr>
{_html_table_rows()}
</table>

{l3_section}

{l4_section}

{l5_section}

{l6_section}

<h2>Candidate L5 parent → child letter corpus</h2>
<p>
For L5, replacing the virtual spherical closure <code>S_v</code> by a task-derived
<code>U_v</code> on one regular pointing level set removes one degree of freedom.
Letter labels below are a <em>candidate test corpus</em> only: kinds and roles are recorded,
but axis aggregation and closed-mechanism statuses remain <code>UNRESOLVED</code> until
issued. Mobility/letter matching is not an equivalence certificate.
</p>
<table>
<tr><th>Parent</th><th>M</th><th>Child</th><th>M</th><th>Architecture origin</th></tr>
{_family_rows()}
</table>

<h2>How the U joint is “driven”</h2>
<div class="note"><strong>Simple statement.</strong> {simple_drive_explanation()}</div>
<p>
The canonical child solver drives pseudo-arclength <code>s</code>. Loop closure returns
<code>alpha(s)</code>, <code>beta(s)</code>, and every other joint coordinate. A prescribed-alpha
experiment adds <code>alpha=alpha_command</code> as one equation and solves the remaining
coordinates; it fails as a local chart when <code>dalpha/ds=0</code>.
</p>
<p>
In the conceptual branch below, alpha winds once while beta rocks. They are still coordinates
of one mechanism branch—not two independent mechanism DOFs.
</p>
<p><img src="{coordinate_plot_name}" alt="U coordinate graph" style="max-width: 760px;"></p>
{animation_block}
<table>
<tr><th>Conceptual result</th><th>Value</th></tr>
<tr><td>alpha winding</td><td>{summary['alpha_winding']}</td></tr>
<tr><td>beta winding</td><td>{summary['beta_winding']}</td></tr>
<tr><td>interpretation</td><td>{summary['interpretation']}</td></tr>
</table>

<h2>Scaffold mapping to active V05–V09</h2>
<ol>
<li><strong>L3:</strong> planar calibration adapter (trusted exact map).</li>
<li><strong>L4 / V05:</strong> proximal <code>exact_u_pair_4r</code> independent match is
<code>LOCAL_ONLY</code> on a traced arc; complete component correspondence remains unresolved.</li>
<li><strong>L5 / V06:</strong> V06A1 <code>LOCAL_PATCH</code> plus candidate letter families
(<code>UNRESOLVED</code> certificates); complete 2D parent atlas + reconstruction remain V06A2+.
Direct V06A parent construction may proceed without an L4 component certificate.</li>
<li><strong>L6 / V07:</strong> scaffold interface with nullity-3 seed audit for generic 6R;
frozen SO(3) reference and nested / V08 work remain V07A+.</li>
<li><strong>L7:</strong> deferred / BLOCKED pending complete-component and nested-slice
certificate work.</li>
</ol>

<h2>Evidence guardrails</h2>
<ul>
<li>A level-set fiber can be valid even when no known four-bar compression exists.</li>
<li>A matching DOF count or joint-letter string is not an equivalence certificate.</li>
<li>Preserve <code>axis_aggregation_status</code> vs <code>closed_mechanism_status</code> (ADR-021).</li>
<li><code>tool_alpha</code> and <code>tool_beta</code> are readouts from the same leaf solve.</li>
<li>Promote <code>source_chain_evidence</code> only with a real accepted closed-mechanism certificate.</li>
<li>Descriptor discovery remains downstream of successful reconstruction.</li>
</ul>
</body>
</html>
"""


def build_ladder_readout(
    outdir: Path,
    *,
    include_animation: bool = True,
) -> ReadoutPaths:
    """Write the L3-L7 program readout and conceptual U-drive visualization."""

    output = Path(outdir)
    output.mkdir(parents=True, exist_ok=True)
    figure_dir = output / "figures"
    data_dir = output / "data"
    figure_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    samples = conceptual_branch_samples()
    summary = summarize_branch(samples)
    payload = program_payload()
    payload["canonical_drive_contract"] = free_branch_contract().to_dict()
    payload["source_fiber_drive_contract"] = task_derived_fiber_contract().to_dict()
    payload["conceptual_u_branch"] = asdict(summary)
    payload["conceptual_only"] = True
    payload["l3_calibration"] = default_l3_calibration_payload()
    payload["l4_equivalence"] = default_l4_equivalence_payload()
    payload["l5_scaffold"] = default_l5_scaffold_payload()
    payload["l6_scaffold"] = default_l6_scaffold_payload()

    json_path = data_dir / "decomposition_ladder_program.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    coordinate_plot = figure_dir / "u_drive_coordinates.svg"
    _plot_u_coordinates(coordinate_plot)

    animation_path: Path | None = None
    if include_animation:
        animation_path = figure_dir / "u_drive_free_branch.gif"
        _animate_u_drive(animation_path)

    html = render_ladder_html(
        payload=payload,
        coordinate_plot_name=str(coordinate_plot.relative_to(output)),
        animation_name=(
            None if animation_path is None else str(animation_path.relative_to(output))
        ),
    )
    html_path = output / "index.html"
    html_path.write_text(html, encoding="utf-8")
    return ReadoutPaths(
        html=html_path,
        json=json_path,
        coordinate_plot=coordinate_plot,
        animation=animation_path,
    )
