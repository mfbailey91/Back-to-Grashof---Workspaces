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

from .registry import PARENT_CHILD_FAMILIES, RUNG_SPECS, program_payload
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
<li><strong>L4 / V05:</strong> proximal <code>exact_u_pair_4r</code> closed-mechanism is
<code>EXACT_ON_COMPONENT</code>; multi-component / other architectures remain unresolved.</li>
<li><strong>L5 / V06:</strong> complete 2D 5R parent + task-derived fiber family
(architecture-scoped after the proximal exact-U gate).</li>
<li><strong>L6:</strong> V07-first freeze a decomposition-free SO(3) reference, then
optional nested slices / V08 quotient against that truth.</li>
<li><strong>L7:</strong> deferred / BLOCKED pending multi-component and nested-slice
certificate work beyond the proximal exact-U gate.</li>
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
