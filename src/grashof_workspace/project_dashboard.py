"""Reproducible project HTML dashboard generator.

Writes:

- ``results/index.html`` — L3–L7 capabilities, R3A five-point hub, status readout
- ``results/spatial4bar_explorer/index.html`` — explorer laboratory lineage
- ``results/kinematic_decomposition/index.html`` — historical V05B–E / V06 lineage hub

Active scientific authority is the L3–L7 ladder plus the R3A five-point program.
Historical V05–V09 labels are lineage, not the current roadmap.

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.project_dashboard \\
      --results-root results
"""

from __future__ import annotations

import argparse
from pathlib import Path

STATUS_DATE = "2026-08-20"

# Proximal exact_u_pair_4r closed-mechanism is LOCAL_ONLY on a traced arc (ADR-034);
# axis aggregation remains EXACT_GLOBAL; EXACT_ON_COMPONENT is reserved.

_SHARED_CSS = """
  body { font-family: Georgia, "Times New Roman", serif; max-width: 960px; margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.45; color: #1a1a1a; }
  h1, h2, h3 { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; line-height: 1.2; }
  h1 { font-size: 1.75rem; margin-bottom: 0.35rem; }
  h2 { margin-top: 2rem; border-bottom: 1px solid #ccc; padding-bottom: 0.25rem; }
  h3 { margin-top: 1.25rem; }
  .meta { color: #444; margin-bottom: 1.5rem; }
  table { border-collapse: collapse; width: 100%; margin: 0.75rem 0 1rem; font-size: 0.95rem; }
  th, td { border: 1px solid #bbb; padding: 0.4rem 0.55rem; text-align: left; vertical-align: top; }
  th { background: #f3f3f3; }
  code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.88em; }
  pre { background: #f6f6f6; padding: 0.75rem 1rem; overflow-x: auto; border: 1px solid #ddd; }
  ul.toc { columns: 2; column-gap: 2rem; }
  .status { font-weight: bold; }
  .pass { color: #0a5; }
  .hold { color: #a50; }
  .reject { color: #a10; }
  .deferred { color: #555; }
  .note { background: #faf7f0; border-left: 3px solid #c4a35a; padding: 0.6rem 0.85rem; margin: 1rem 0; }
  .cap-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin: 1rem 0; }
  .cap { border: 1px solid #ccc; padding: 0.65rem 0.8rem; background: #fcfcfc; }
  .cap h3 { margin: 0 0 0.35rem; font-size: 1rem; }
  .cap p { margin: 0.25rem 0; font-size: 0.92rem; }
  .anim-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
  .anim-grid figure { margin: 0; border: 1px solid #ccc; padding: 0.5rem; background: #fcfcfc; }
  .anim-grid img { width: 100%; height: auto; display: block; background: #fff; }
  .anim-grid figcaption { margin-top: 0.4rem; font-size: 0.88rem; color: #333; }
  @media (max-width: 720px) {
    .cap-grid, .anim-grid { grid-template-columns: 1fr; }
    ul.toc { columns: 1; }
  }
  @media print {
    body { max-width: none; margin: 0; }
    a { color: inherit; text-decoration: none; }
    a::after { content: " (" attr(href) ")"; font-size: 0.8em; color: #555; }
    ul.toc { columns: 1; }
  }
"""

# Canonical V04 copies of the V03 local-branch GIFs (six ordered one-DOF families).
_EXPLORER_BRANCH_ANIMATIONS: tuple[tuple[str, str], ...] = (
    ("UUUR", "spatial4bar_explorer/v04/figures/v03_uuur_branch.gif"),
    ("UURU", "spatial4bar_explorer/v04/figures/v03_uuru_branch.gif"),
    ("URUU", "spatial4bar_explorer/v04/figures/v03_uruu_branch.gif"),
    ("USRR", "spatial4bar_explorer/v04/figures/v03_usrr_branch.gif"),
    ("URSR", "spatial4bar_explorer/v04/figures/v03_ursr_branch.gif"),
    ("URRS", "spatial4bar_explorer/v04/figures/v03_urrs_branch.gif"),
)

_SOURCE_4R_ANIMATIONS: tuple[tuple[str, str], ...] = (
    (
        "exact_u_pair_4r fiber (V05B)",
        "kinematic_decomposition/v05b/figures/v05b_exact_u_pair_4r_fiber.gif",
    ),
    (
        "exact_u_pair_4r source/reduced overlay (V05D)",
        "kinematic_decomposition/v05d/figures/v05d_exact_u_pair_4r_overlay.gif",
    ),
)


def _animation_figures(items: tuple[tuple[str, str], ...]) -> str:
    """Return HTML figures for committed GIF paths relative to ``results/``."""
    return "".join(
        f'<figure><img src="{path}" alt="{label} animation">'
        f"<figcaption><code>{label}</code></figcaption></figure>"
        for label, path in items
    )


def render_explorer_index_html(*, status_date: str = STATUS_DATE) -> str:
    """Return the cumulative project dashboard HTML for the explorer tree."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Spatial 4-Bar Explorer — project printout through V05 audit correction</title>
<style>
{_SHARED_CSS}
</style>
</head>
<body>

<h1>Spatial 4-Bar Explorer</h1>
<p class="meta">
  <strong>Project printout through V05 audit correction</strong> · explorer V00–V05A + kinematic-decomposition ladder<br>
  Artifact roots: <code>results/spatial4bar_explorer/</code> ·
  <code>results/kinematic_decomposition/</code> · Status date: {status_date}<br>
  <a href="../index.html">Project index (so far)</a> ·
  <a href="../decomposition_ladder/index.html">L3–L7 ladder readout</a>
</p>

<div class="note">
  Explorer sprints <strong>V00–V05A</strong> remain a <code>mechanism_explorer_only</code> laboratory.
  The <strong>active</strong> scientific program is the L3–L7 fixed-position ladder
  (<a href="../../docs/CURRENT_STATUS.md">CURRENT_STATUS.md</a>) with R3A five-point natural-leaf
  reconstruction under L5. Historical V05B–E / V06 readouts stay as lineage; proximal
  <code>exact_u_pair_4r</code> closed-mechanism remains <strong>LOCAL_ONLY</strong> on a traced arc.
  Hub: <a href="../kinematic_decomposition/index.html">../kinematic_decomposition/index.html</a>
  · R3A: <a href="../l5_reconstruction/r3a/index.html">../l5_reconstruction/r3a/index.html</a>.
</div>

<h2>Contents</h2>
<ul class="toc">
  <li><a href="#thesis">Program thesis</a></li>
  <li><a href="#families">Families and tool axes</a></li>
  <li><a href="#pipeline">Evidence pipeline</a></li>
  <li><a href="#sprints">Sprint-by-sprint printout</a></li>
  <li><a href="#findings">Findings locked so far</a></li>
  <li><a href="#contract">V04C provisional contract</a></li>
  <li><a href="#v05a">Explorer V05A</a></li>
  <li><a href="#active">V05B–E audit-corrected MVP</a></li>
  <li><a href="#next">Next: V06</a></li>
  <li><a href="#links">Full sprint link index</a></li>
</ul>

<h2 id="thesis">Program thesis</h2>
<p>
We left spherical-candidate enumeration and explore the <strong>one-DOF spatial four-bar families</strong>
induced by an aligned-terminal 6R pointing fiber. Each family is solved as a physical mechanism;
the virtual tool joint <code>U</code> is decomposed into two perpendicular revolute coordinates
<code>(α, β)</code>. Crank/rocker labels are <em>link-specific windings</em> on returned cycles —
not conventional planar Grashof class names.
</p>
<pre>Aligned-terminal 6R pointing fiber
  → compound parents SUUR / SSRR (M = 2)
  → tool-slice → ordered one-DOF families
  → physical geometry → closure/continuation → winding W = (w_α, w_β)
  → (later, certified only) descriptor trends → candidate rules → 6R dexterity test</pre>
<p>
The active scientific ladder is now source-chain first:
</p>
<pre>spatial 4R + S_v (off-axis tool)
  → fixed-position fiber (V05B)
  → classified orientation-curve truth (V05C)
  → exact RR→U aggregation EXACT_GLOBAL + closed-mechanism LOCAL_ONLY for exact_u_pair_4r (V05D)
  → near-aligned rejection + false-U diagnostic (V05E)
  → V06 architecture-scoped after proximal exact-U gate</pre>
<p>
Docs:
<a href="../../docs/reference/PROJECT_REFERENCE_INDEX.md">PROJECT_REFERENCE_INDEX.md</a>
· <a href="../../docs/archive/programs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md">KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</a>
· <a href="../../docs/ROADMAP.md">ROADMAP.md</a>
· explorer notes: <a href="../../docs/archive/sprints/SPRINT_03_SPATIAL_4BAR_EXPLORER.md">SPRINT_03_SPATIAL_4BAR_EXPLORER.md</a>
</p>

<h2 id="families">Families and tool axes</h2>
<p>Exact two-DOF reduced parent: <code>S + 5R</code>, mobility <code>M = 2</code>.</p>
<table>
  <tr><th>Ordered one-DOF family</th><th>Parent origin</th></tr>
  <tr><td>UUUR, UURU, URUU</td><td>SUUR line</td></tr>
  <tr><td>USRR, URSR, URRS</td><td>SSRR line</td></tr>
</table>
<pre>U_t(α, β) = R_a(α) R_b(β)</pre>
<p>
Twelve family–axis <em>questions</em> exist, but each physical mechanism is solved
<strong>once</strong>; <code>tool_a</code> and <code>tool_b</code> are two classifications read from the same returned branch.
These explorer windings must not be reused as <code>U_phys</code> / source-chain roles.
</p>

<h2 id="pipeline">Evidence pipeline (what counts)</h2>
<ol>
  <li><strong>Scaffold only (not research evidence):</strong> V01/V02 random descriptor samples and mock branch labels.</li>
  <li><strong>Physical geometry:</strong> V02B reference assemblies and topology-preserving perturbations.</li>
  <li><strong>Numerical mechanism result (explorer):</strong> V03 closure / continuation; V04 returned-cycle windings.</li>
  <li><strong>Provisional convention:</strong> V04C virtual-<code>U</code> canonicalization (storage/diagnostics only).</li>
  <li><strong>Explorer pointing fiber:</strong> V05A SUUR→UUUR MVP — provenance <code>mechanism_explorer_only</code>.</li>
  <li><strong>Source-chain certificates:</strong> active V05B–E under <code>results/kinematic_decomposition/</code>
      (fiber, orientation curve, <code>DecompositionCertificate</code>, near-aligned rejection).</li>
  <li><strong>Not yet:</strong> V06 5R parent; certified all-family atlas (V10+); workspace coverage theorems.</li>
</ol>

<h2 id="sprints">Sprint-by-sprint printout (V00–V04C)</h2>

<h3>V00 — explorer shell and family inventory</h3>
<p class="status pass">DONE</p>
<p>
Stood up the package scaffold, ordered-family catalog, twelve tool-axis case slugs, and schematic plots.
</p>
<p>
Canonical readout folder: <a href="v00/index.html">v00/</a>
· <a href="v00/sprint_00_overview.html">sprint_00_overview.html</a>
</p>

<h3>V01 — parameter inventory and sampled geometries</h3>
<p class="status pass">DONE (scaffold corpus)</p>
<p>
Published a broad descriptor inventory (distances, twists, offsets, shape, flags) and synthetic samples with histograms.
<strong>Research guardrail:</strong> this corpus samples descriptor-like scalars; it is not a mechanism corpus and must not feed crank evidence.
</p>
<p>
Canonical readout: <a href="v01/index.html">v01/</a>
· <a href="v01/sprint_01_parameter_inventory.html">sprint_01_parameter_inventory.html</a>
</p>

<h3>V02 — branch-result and winding scaffold</h3>
<p class="status pass">DONE (schema + mocks)</p>
<p>
Froze the branch-result schema (<code>w_alpha</code>/<code>w_beta</code>, class labels, ranges, notes) and produced clearly labeled
<strong>mock</strong> classifications so HTML/JSON pipelines existed before the solver.
</p>
<p>
Canonical readout: <a href="v02/index.html">v02/</a>
· <a href="v02/sprint_02_mock_branch_results.html">sprint_02_mock_branch_results.html</a>
</p>

<h3>V02B — physical geometry hardening</h3>
<p class="status pass">DONE — research geometry input begins here</p>
<p>
Replaced descriptor-first sampling with physical four-bar assemblies: joint centers/frames, exact
<code>U</code>/<code>S</code> internal axis structure, ground + tool <code>U</code>, canonical references for all six families,
topology-preserving perturbations, and descriptors derived from geometry (including <code>L41</code> and diagonals).
Readouts state <strong>PHYSICAL GEOMETRY / NO CLOSURE SOLVE YET</strong>.
</p>
<p>
Canonical readout: <a href="v02b/index.html">v02b/</a>
· <a href="v02b/sprint_02b_physical_geometry.html">sprint_02b_physical_geometry.html</a>
</p>

<h3>V03 — closure and continuation proof</h3>
<p class="status pass">DONE — local 1-DOF manifold, no crank claim</p>
<p>
One shared seven-coordinate PoE closure kernel for all six families (R→1, U→2, S→3). At every
canonical V02B reference: <code>||r(0)|| ≈ 0</code>, Jacobian rank 6 / nullity 1. Pseudo-arclength
continuation produces well-conditioned branch segments and canonical local-branch GIFs for all six families
(with highlighted <code>tool_a</code>/<code>tool_b</code> chart readouts; frame titles state <code>param=s (not driven)</code>).
Prescribed tool-A and tool-B drive diagnostics (12 GIFs + 12 coordinate plots) restore the explicit A/B rotatability questions without replacing returned-cycle winding.
These are mechanism-explorer demos, not a validated <code>S_v → U_v</code> pointing-fiber proof.
<strong>No winding or crank classification in V03.</strong>
</p>
<table>
  <tr><th>Family</th><th>Rank / nullity</th><th>Reference audit</th></tr>
  <tr><td>UUUR, UURU, URUU, USRR, URSR, URRS</td><td>6 / 1</td><td>all PASS</td></tr>
</table>
<p>
Canonical readout: <a href="v03/index.html">v03/</a>
· <a href="v03/sprint_03_closure_and_continuation.html">sprint_03_closure_and_continuation.html</a>
<br>
Also mirrored in the cumulative tree: <a href="v04/sprint_03_closure_and_continuation.html">v04/sprint_03_…</a>
</p>

<h3>V04 — true winding and crank atlas (UUUR-first)</h3>
<p class="status pass">DONE — first true crank/rocker labels</p>
<p>
Returned-cycle continuation + angle unwrap → integer windings
<code>W = (w_α, w_β)</code>. Classification (link-specific):
</p>
<ul>
  <li><code>crank</code> if returned and <code>|w_i| ≥ 1</code></li>
  <li><code>rocker</code> if returned and <code>w_i = 0</code></li>
  <li><code>open_branch</code> if no return within budget</li>
</ul>
<p>
On the initial UUUR physical sample set, both crank and rocker examples appear
(e.g. <code>uuur_physical_000</code>: <code>W = (−1, 0)</code> crank/rocker;
<code>uuur_physical_003</code>: <code>W = (0, 0)</code> rocker/rocker).
Other families remain V03 diagnostics until a certified all-family atlas (deferred V10).
</p>
<p>
Canonical readout: <a href="v04/index.html">v04/</a>
· <a href="v04/sprint_04_winding_and_crank.html">sprint_04_winding_and_crank.html</a>
</p>

<h3>V04B — virtual-U robustness and orientation sweep</h3>
<p class="status pass">DONE — labels are step/direction-stable; orientation matters</p>
<p>
Step-size and direction-reversal checks preserve crank/rocker (with
<code>W_minus = −W_plus</code>). Controlled tool-<code>U</code> orientation <code>φ</code> and axis order
<code>ab</code>/<code>ba</code> <strong>change</strong> class labels and coverage. Budget-limited opens appeared near
<code>φ = 120°</code> and <code>300°</code> under the default step budget.
</p>
<p>
Canonical readout: <a href="v04b/sprint_04b_virtual_u_robustness.html">v04b/sprint_04b_virtual_u_robustness.html</a>
</p>

<h3>V04C — virtual-U equivalence and fiber interpretation</h3>
<p class="status pass">DONE — provisional canonicalization</p>
<p>
On the tested canonical UUUR geometry:
</p>
<ul>
  <li><code>BA(φ) ∼ AB(φ + 90°)</code> with β-winding sign reversal — symmetry holds across the coarse grid.</li>
  <li><code>AB(φ) ∼ AB(φ + 180°)</code> in status, classes, <code>|W|</code>, and coverage — half-turn periodicity holds.</li>
  <li>Extended budgets resolved the V04B open cases at <code>φ = 120°</code>/<code>300°</code> to returned
      rocker/rocker (budget exhaustion ≠ topology).</li>
  <li>Dense transition probes mapped class changes in intervals
      <code>[0,30]</code>, <code>[30,60]</code>, <code>[60,90]</code>, <code>[120,150]</code> (degrees).</li>
</ul>
<p>
Canonical readout: <a href="v04c/sprint_04c_virtual_u_equivalence.html">v04c/sprint_04c_virtual_u_equivalence.html</a>
</p>

<h2 id="findings">Findings locked so far</h2>
<table>
  <tr><th>Claim</th><th>Level</th><th>Sprint</th></tr>
  <tr>
    <td>Six ordered families are the correct explorer catalog; twelve axis questions share one solve per mechanism.</td>
    <td>setup</td>
    <td>V00</td>
  </tr>
  <tr>
    <td>V01/V02 mock/descriptor corpora are not crank evidence.</td>
    <td>guardrail</td>
    <td>V01–V02B</td>
  </tr>
  <tr>
    <td>All six canonical physical references close with rank-6 / nullity-1 Jacobians; shared continuation kernel works on all six.</td>
    <td>numerical mechanism</td>
    <td>V03</td>
  </tr>
  <tr>
    <td>Returned-cycle windings yield nontrivial UUUR crank and rocker examples.</td>
    <td>numerical mechanism</td>
    <td>V04</td>
  </tr>
  <tr>
    <td>Winding labels are stable to step size and continuation direction; not invariant to tool-U φ or ab/ba order.</td>
    <td>numerical mechanism</td>
    <td>V04B</td>
  </tr>
  <tr>
    <td>Axis order is a removable coordinate symmetry (shift + sign); φ domain reduces modulo 180° — provisional, UUUR-tested.</td>
    <td>provisional convention</td>
    <td>V04C</td>
  </tr>
  <tr>
    <td>One SUUR→UUUR parent pointing slice and local virtual-U chart are valid; parent–child mechanism equivalence remains unresolved (split status).</td>
    <td>numerical mechanism / mechanism_explorer_only</td>
    <td>V05A</td>
  </tr>
  <tr>
    <td>Off-axis spatial 4R fixed-position fibers continue with rank 3 / nullity 1 and nontrivial pointing; singular parallel exterior rejects; terminal-roll retained as named control.</td>
    <td>source-chain</td>
    <td>V05B</td>
  </tr>
  <tr>
    <td>Orientation/pointing curve exports are classified (e.g. NONTRIVIAL_POINTING_CURVE vs PURE_TERMINAL_ROLL); not SO(3)/S² coverage.</td>
    <td>source-chain</td>
    <td>V05C</td>
  </tr>
  <tr>
    <td>Exact proximal RR→U axis aggregation is EXACT_GLOBAL as regrouping; closed-mechanism equivalence is LOCAL_ONLY for proximal exact_u_pair_4r on a budget-limited traced arc.</td>
    <td>source-chain certificate / LOCAL_ONLY</td>
    <td>V05D</td>
  </tr>
  <tr>
    <td>Near-aligned RR pair rejects exact aggregation; forced exact-U surrogate shows nonzero task error (diagnostic only).</td>
    <td>source-chain rejection</td>
    <td>V05E</td>
  </tr>
</table>

<h2 id="contract">V04C provisional experiment contract</h2>
<ul>
  <li><strong>Axis order:</strong> canonicalize to <code>ab</code> (solver-coordinate storage).</li>
  <li><strong>Orientation domain:</strong> reduce <code>φ</code> modulo 180° for diagnostic representation.</li>
  <li><strong>Open branches:</strong> keep unresolved / budget-limited cases explicit; do not promote budget exhaustion to a topology claim.</li>
  <li><strong>Scope:</strong> decisions apply to the tested canonical UUUR geometry and only to storage / diagnostics — not a proof of physical <code>S_v → U_v</code> fiber equivalence.</li>
  <li><strong>Explorer pointing fibers:</strong> use the task-derived pointing-slice contract
      (<a href="../../docs/methods/SPATIAL_POINTING_SLICE_CONTRACT.md">SPATIAL_POINTING_SLICE_CONTRACT.md</a>);
      arbitrary <code>φ</code> sweeps remain diagnostic-only until mapped to legitimate pointing fibers.</li>
</ul>

<h2 id="v05a">Explorer V05A — parent-first pointing fiber (historical / deferred V10 prep)</h2>
<p class="status pass">SPLIT — parent slice / U_v chart PASS; child equivalence UNRESOLVED (mechanism_explorer_only)</p>
<p>
Restored the aligned-terminal fiber kernel and constructed one task-derived
<code>UUUR</code> child from an intersecting-pairs <code>SUUR</code> parent with explicit
<code>h(d)=n·d=c</code>. This is <strong>not</strong> active-program V05B.
Parent–child mechanism equivalence is not claimed from the undifferentiated legacy PASS.
</p>
<p>
Canonical readout:
<a href="v05a/sprint_05a_pointing_slice_fibers.html">v05a/sprint_05a_pointing_slice_fibers.html</a>
· JSON: <a href="v05a/data/v05a_pointing_slice_fibers.json">v05a/data/v05a_pointing_slice_fibers.json</a>
</p>

<h2 id="active">Active kinematic decomposition — V05B–E</h2>
<p class="status pass">AUDIT-CORRECTED MVP — V05 independent match LOCAL_ONLY (exact_u_pair_4r traced arc)</p>
<p>
Hub: <a href="../kinematic_decomposition/index.html">../kinematic_decomposition/index.html</a>
· corrections: <a href="../../docs/archive/audits/V05_AUDIT_CORRECTIONS.md">V05_AUDIT_CORRECTIONS.md</a>
</p>
<pre>V05A corpus (off-axis + terminal-roll control) → V05B fixed-position fiber (audit-corrected MVP)
V05C orientation-curve classification (audit-corrected MVP)
V05D exact-axis EXACT_GLOBAL / closed-mechanism LOCAL_ONLY (exact_u_pair_4r traced arc)
V05E near-aligned rejection (audit-corrected MVP)
V05 overall LOCAL_ONLY · other architectures UNRESOLVED · V06A parent construction not blocked by L4
V10+ deferred atlas</pre>
<ul>
  <li>V05B:
    <a href="../kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html">sprint_v05b_fixed_position_fiber.html</a>
  </li>
  <li>V05C:
    <a href="../kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html">sprint_v05c_orientation_curve.html</a>
    (classified orientation-curve truth, not coverage)
  </li>
  <li>V05D:
    <a href="../kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html">sprint_v05d_axis_aggregation.html</a>
    (<code>DecompositionCertificate</code>: axis aggregation vs closed-mechanism statuses)
  </li>
  <li>V05E:
    <a href="../kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html">sprint_v05e_near_aligned_rejection.html</a>
    (near-aligned <code>REJECTED</code> + false-U task-error diagnostic)
  </li>
</ul>
<p>
Program docs:
<a href="../../docs/reference/PROJECT_REFERENCE_INDEX.md">PROJECT_REFERENCE_INDEX.md</a>
· <a href="../../docs/archive/programs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md">KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</a>
</p>

<h2 id="next">Next: V06 — spatial 5R fixed-position parent</h2>
<p>
Software scaffold work for a spatial 5R fixed-position parent may proceed.
<strong>V06 scientific claims</strong> may be architecture-scoped for pathways that inherit
the accepted proximal exact-U closed-mechanism certificate; multi-component and
non-proximal embeddings remain unverified. Do not promote explorer four-bar atlases
to manipulator evidence without certificates.
</p>

<h2 id="links">Full sprint link index</h2>
<table>
  <tr><th>Sprint</th><th>Primary HTML</th><th>Folder / notes</th></tr>
  <tr>
    <td>V00</td>
    <td><a href="v00/sprint_00_overview.html">sprint_00_overview.html</a></td>
    <td><a href="v00/index.html">v00/</a></td>
  </tr>
  <tr>
    <td>V01</td>
    <td><a href="v01/sprint_01_parameter_inventory.html">sprint_01_parameter_inventory.html</a></td>
    <td><a href="v01/index.html">v01/</a> · scaffold samples only</td>
  </tr>
  <tr>
    <td>V02</td>
    <td><a href="v02/sprint_02_mock_branch_results.html">sprint_02_mock_branch_results.html</a></td>
    <td><a href="v02/index.html">v02/</a> · mocks only</td>
  </tr>
  <tr>
    <td>V02B</td>
    <td><a href="v02b/sprint_02b_physical_geometry.html">sprint_02b_physical_geometry.html</a></td>
    <td><a href="v02b/index.html">v02b/</a> · physical geometry</td>
  </tr>
  <tr>
    <td>V03</td>
    <td><a href="v03/sprint_03_closure_and_continuation.html">sprint_03_closure_and_continuation.html</a></td>
    <td><a href="v03/index.html">v03/</a> · also in <a href="v04/sprint_03_closure_and_continuation.html">v04/</a></td>
  </tr>
  <tr>
    <td>V04</td>
    <td><a href="v04/sprint_04_winding_and_crank.html">sprint_04_winding_and_crank.html</a></td>
    <td><a href="v04/index.html">v04/</a> · UUUR-first true W</td>
  </tr>
  <tr>
    <td>V04B</td>
    <td><a href="v04b/sprint_04b_virtual_u_robustness.html">sprint_04b_virtual_u_robustness.html</a></td>
    <td><a href="v04b/">v04b/</a></td>
  </tr>
  <tr>
    <td>V04C</td>
    <td><a href="v04c/sprint_04c_virtual_u_equivalence.html">sprint_04c_virtual_u_equivalence.html</a></td>
    <td><a href="v04c/">v04c/</a> · provisional ab / φ mod 180°</td>
  </tr>
  <tr>
    <td>Explorer V05A</td>
    <td><a href="v05a/sprint_05a_pointing_slice_fibers.html">sprint_05a_pointing_slice_fibers.html</a></td>
    <td><a href="v05a/">v05a/</a> · mechanism_explorer_only</td>
  </tr>
  <tr>
    <td>Active V05B</td>
    <td><a href="../kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html">sprint_v05b_fixed_position_fiber.html</a></td>
    <td><a href="../kinematic_decomposition/v05b/">v05b/</a> · 4R + S_v fiber</td>
  </tr>
  <tr>
    <td>Active V05C</td>
    <td><a href="../kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html">sprint_v05c_orientation_curve.html</a></td>
    <td><a href="../kinematic_decomposition/v05c/">v05c/</a> · orientation-curve truth</td>
  </tr>
  <tr>
    <td>Active V05D</td>
    <td><a href="../kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html">sprint_v05d_axis_aggregation.html</a></td>
    <td><a href="../kinematic_decomposition/v05d/">v05d/</a> · DecompositionCertificate</td>
  </tr>
  <tr>
    <td>Active V05E</td>
    <td><a href="../kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html">sprint_v05e_near_aligned_rejection.html</a></td>
    <td><a href="../kinematic_decomposition/v05e/">v05e/</a> · near-aligned rejection</td>
  </tr>
</table>

<p class="meta" style="margin-top:2rem;">
  Cumulative explorer tree with early sprint pages:
  <a href="v04/index.html">v04/index.html</a>.
  Prefer versioned folders above when citing a sprint’s authoritative readout.
  Regenerate this page with
  <code>python -m grashof_workspace.project_dashboard --results-root results</code>.
</p>

</body>
</html>
"""


def render_kinematic_decomposition_index_html(*, status_date: str = STATUS_DATE) -> str:
    """Return the active kinematic-decomposition hub HTML."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Kinematic Decomposition — V05B–E / V06 lineage hub</title>
<style>
{_SHARED_CSS}
</style>
</head>
<body>

<h1>Kinematic Decomposition</h1>
<p class="meta">
  <strong>Historical V05B–E / V06 lineage hub</strong> · active L5 work is R3A<br>
  Artifact root: <code>results/kinematic_decomposition/</code> · Status date: {status_date}<br>
  <a href="../index.html">Project index (so far)</a> ·
  <a href="../decomposition_ladder/index.html">L3–L7 ladder readout</a> ·
  <a href="../l5_reconstruction/r3a/index.html">R3A five-point hub</a>
</p>

<div class="note">
  This track builds independent source-chain truth before mechanism reconstruction.
  Exports are <strong>not</strong> coverage certificates for <code>SO(3)</code> or <code>S²</code>.
  Explorer <code>spatial4bar_explorer/v05a</code> remains <code>mechanism_explorer_only</code>
  and is <strong>not</strong> this ladder.
  <strong>V05 scientific gate: LOCAL_ONLY</strong> for proximal
  <code>exact_u_pair_4r</code> on a budget-limited independent traced arc.
  Exact axis aggregation remains <code>EXACT_GLOBAL</code> and is still not
  closed-mechanism equivalence; complete component correspondence,
  multi-component <code>EXACT_GLOBAL</code>, and other architectures remain unresolved.
</div>

<h2>Thesis</h2>
<pre>OpenChainModel (spatial 4R, off-axis tool)
  → FixedPositionProblem + S_v
  → FixedPositionFiberResult (V05B)
  → classified OrientationImageResult / PointingImageResult (V05C)
  → DecompositionCertificate: axis_aggregation vs closed_mechanism (V05D)
  → near-aligned REJECTED + false_u_surrogate diagnostic (V05E)
  → V06 architecture-scoped after proximal exact-U gate</pre>
<p>
Docs:
<a href="../../docs/reference/PROJECT_REFERENCE_INDEX.md">PROJECT_REFERENCE_INDEX.md</a>
· <a href="../../docs/archive/programs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md">KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</a>
· <a href="../../docs/archive/audits/V05_AUDIT_CORRECTIONS.md">V05_AUDIT_CORRECTIONS.md</a>
· <a href="../../docs/methods/JACOBIAN_AND_DERIVATIVE_POLICY.md">JACOBIAN_AND_DERIVATIVE_POLICY.md</a>
· <a href="../../docs/reference/DECISIONS.md">DECISIONS.md</a>
</p>

<h2>V05A corpus</h2>
<p>Synthetic spatial-4R members used by the active ladder:</p>
<table>
  <tr><th>Architecture</th><th>Role</th></tr>
  <tr><td><code>generic_4r</code></td><td>Off-axis active source; no intentional consecutive intersecting pairs</td></tr>
  <tr><td><code>terminal_roll_control_4r</code></td><td>On-axis aligned terminal-roll control (PURE_TERMINAL_ROLL)</td></tr>
  <tr><td><code>exact_u_pair_4r</code></td><td>Off-axis exact proximal RR→U_phys geometry</td></tr>
  <tr><td><code>near_aligned_u_pair_4r</code></td><td>Off-axis near-miss pair; must reject as exact U</td></tr>
  <tr><td><code>singular_4r_parallel</code></td><td>Rank-deficient exterior for fixed-position regularity</td></tr>
</table>

<h2>Sprint readouts</h2>
<table>
  <tr><th>Sprint</th><th>Status</th><th>Primary HTML</th><th>JSON</th></tr>
  <tr>
    <td>V05B</td>
    <td class="status pass">AUDIT-CORRECTED MVP</td>
    <td><a href="v05b/sprint_v05b_fixed_position_fiber.html">sprint_v05b_fixed_position_fiber.html</a></td>
    <td><a href="v05b/data/v05b_fixed_position_fibers.json">v05b_fixed_position_fibers.json</a></td>
  </tr>
  <tr>
    <td>V05C</td>
    <td class="status pass">AUDIT-CORRECTED MVP</td>
    <td><a href="v05c/sprint_v05c_orientation_curve.html">sprint_v05c_orientation_curve.html</a></td>
    <td><a href="v05c/data/v05c_orientation_curves.json">v05c_orientation_curves.json</a></td>
  </tr>
  <tr>
    <td>V05D</td>
    <td class="status pass">AUDIT-CORRECTED MVP</td>
    <td><a href="v05d/sprint_v05d_axis_aggregation.html">sprint_v05d_axis_aggregation.html</a></td>
    <td><a href="v05d/data/v05d_axis_aggregation.json">v05d_axis_aggregation.json</a></td>
  </tr>
  <tr>
    <td>V05E</td>
    <td class="status pass">AUDIT-CORRECTED MVP</td>
    <td><a href="v05e/sprint_v05e_near_aligned_rejection.html">sprint_v05e_near_aligned_rejection.html</a></td>
    <td><a href="v05e/data/v05e_near_aligned_rejection.json">v05e_near_aligned_rejection.json</a></td>
  </tr>
  <tr>
    <td>V06A0</td>
    <td class="status pass">SOFTWARE VALIDATION</td>
    <td><a href="v06a0/sprint_v06a0_implicit_manifold.html">sprint_v06a0_implicit_manifold.html</a></td>
    <td><a href="v06a0/data/v06a0_implicit_manifold.json">v06a0_implicit_manifold.json</a></td>
  </tr>
  <tr>
    <td>V06A1</td>
    <td class="status pass">LOCAL_PATCH</td>
    <td><a href="v06a1/sprint_v06a1_local_parent_patch.html">sprint_v06a1_local_parent_patch.html</a></td>
    <td><a href="v06a1/data/v06a1_generic_5r_local_patch.json">v06a1_generic_5r_local_patch.json</a></td>
  </tr>
  <tr>
    <td>V06A2</td>
    <td class="status pass">STITCHED ATLAS (budget-limited; not closed)</td>
    <td><a href="v06a2/sprint_v06a2_parent_atlas.html">sprint_v06a2_parent_atlas.html</a></td>
    <td><a href="v06a2/data/v06a2_generic_5r_parent_atlas.json">v06a2_generic_5r_parent_atlas.json</a></td>
  </tr>
  <tr>
    <td>V06C</td>
    <td class="status pass">SOURCE IMAGES (partial)</td>
    <td><a href="v06c/sprint_v06c_source_images.html">sprint_v06c_source_images.html</a></td>
    <td><a href="v06c/data/v06c_generic_5r_source_images.json">v06c_generic_5r_source_images.json</a></td>
  </tr>
  <tr>
    <td>V06B</td>
    <td class="status pass">SUUR LOCAL_ONLY / near REJECTED</td>
    <td><a href="v06b/sprint_v06b_compound_parent.html">sprint_v06b_compound_parent.html</a></td>
    <td><a href="v06b/data/v06b_compound_parent.json">v06b_compound_parent.json</a></td>
  </tr>
  <tr>
    <td>V06D1</td>
    <td class="status pass">SOURCE LEVEL SETS (not reconstruction)</td>
    <td><a href="v06d1/sprint_v06d1_level_sets.html">sprint_v06d1_level_sets.html</a></td>
    <td><a href="v06d1/data/v06d1_generic_5r_level_sets.json">v06d1_generic_5r_level_sets.json</a></td>
  </tr>
  <tr>
    <td>V06D2</td>
    <td class="status pass">ONE UUUR CHILD REJECTED (not reconstruction)</td>
    <td><a href="v06d2/sprint_v06d2_virtual_u_child.html">sprint_v06d2_virtual_u_child.html</a></td>
    <td><a href="v06d2/data/v06d2_virtual_u_child.json">v06d2_virtual_u_child.json</a></td>
  </tr>
  <tr>
    <td>V06E</td>
    <td class="status pass">RECON CLOSEOUT (V06 not passed)</td>
    <td><a href="v06e/sprint_v06e_reconstruction.html">sprint_v06e_reconstruction.html</a></td>
    <td><a href="v06e/data/v06e_reconstruction.json">v06e_reconstruction.json</a></td>
  </tr>
</table>

<h2>Reproduce</h2>
<pre>PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05b --outdir results/kinematic_decomposition/v05b
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05c --outdir results/kinematic_decomposition/v05c
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05d --outdir results/kinematic_decomposition/v05d
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v05e --outdir results/kinematic_decomposition/v05e
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a0 --outdir results/kinematic_decomposition/v06a0
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a1 --outdir results/kinematic_decomposition/v06a1
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06a2 --outdir results/kinematic_decomposition/v06a2
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06c --outdir results/kinematic_decomposition/v06c
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06b --outdir results/kinematic_decomposition/v06b
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06d1 --outdir results/kinematic_decomposition/v06d1
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06d2 --outdir results/kinematic_decomposition/v06d2
PYTHONPATH=src python -m grashof_workspace.spatial_experiments.v06e --outdir results/kinematic_decomposition/v06e
PYTHONPATH=src python -m grashof_workspace.project_dashboard --results-root results</pre>

<h2>Next</h2>
<p><strong>V07A held</strong> (ADR-047). V06H6 closeout:
current fixed-axis UUUR construction rejected; broader 5R factorization
unresolved; V07A held pending parent/continuation completion. Empty interior
<code>COVERED</code> makes the miss metric unevaluable (ADR-043); a nonempty
COVERED set does not pass V06. Atlas stitch (ADR-046) is not a closed parent.
L5 reconstruction stays unresolved.

<p class="meta" style="margin-top:2rem;">
  Project index (so far):
  <a href="../index.html">../index.html</a> ·
  Explorer dashboard:
  <a href="../spatial4bar_explorer/index.html">../spatial4bar_explorer/index.html</a>
</p>

</body>
</html>
"""


def render_project_index_html(*, status_date: str = STATUS_DATE) -> str:
    """Return the root capabilities / status readout (project so far)."""
    explorer_animations = _animation_figures(_EXPLORER_BRANCH_ANIMATIONS)
    source_animations = _animation_figures(_SOURCE_4R_ANIMATIONS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Back to Grashof — capabilities and status so far</title>
<style>
{_SHARED_CSS}
</style>
</head>
<body>

<h1>Back to Grashof — capabilities and status so far</h1>
<p class="meta">
  Mechanism-based characterization of manipulator orientation after fixing tool position.<br>
  <strong>Active architecture:</strong> L3–L7 fixed-position decomposition ladder
  (<code>docs/theory/DECOMPOSITION_LADDER.md</code>) ·
  <strong>Status ledger:</strong> <code>docs/CURRENT_STATUS.md</code> ·
  Status date: {status_date}
</p>

<div class="note">
  This page summarizes <em>what the software and evidence chain can do today</em>,
  and what they explicitly do <em>not</em> claim. It links to reproducible sprint
  readouts; it does not invent accepted children, complete parents, or V07 readiness.
</div>

<h2>Contents</h2>
<ul class="toc">
  <li><a href="#question">Project question</a></li>
  <li><a href="#animations">Constituent four-bar animations</a></li>
  <li><a href="#ledger">Rung ledger</a></li>
  <li><a href="#capabilities">Capabilities by rung</a></li>
  <li><a href="#negatives">Locked negatives</a></li>
  <li><a href="#artifacts">Evidence artifacts</a></li>
  <li><a href="#hubs">Hubs and docs</a></li>
  <li><a href="#next">What comes next</a></li>
  <li><a href="#reproduce">Reproduce</a></li>
</ul>

<h2 id="question">Project question</h2>
<p>
Fix the tool position, form the exact virtual closed source mechanism, then ask
whether architecture- or task-derived lower-dimensional mechanism families can
certify behavior whose task images reconstruct the parent orientation or pointing
image under an explicit stitching contract.
</p>
<pre>open chain
  → fixed-position fiber / parent
  → exact virtual closure
  → orientation or pointing image
  → certified decomposition (when valid)
  → mechanism behavior certificate
  → coverage / compatibility stitching
  → independent validation</pre>
<p>
Classical Grashof classification is one planar four-bar behavior descriptor.
The program does <strong>not</strong> assume a universal spatial Grashof inequality.
</p>

<h2 id="animations">Constituent four-bar animations</h2>
<div class="note">
  These GIFs show <strong>one-DOF spatial four-bar closures moving along local
  continuation arclength</strong>. The six ordered families below are the explorer
  laboratory constituents (<code>mechanism_explorer_only</code>): they are
  <em>not</em> accepted source-derived children and are not workspace certificates.
  Source-chain L4 motion (proximal <code>exact_u_pair_4r</code>) is shown separately
  and remains <code>LOCAL_ONLY</code> on a traced arc.
</div>

<h3>Explorer lab — six ordered one-DOF families</h3>
<p>
Canonical V04 copies of the V03 branch animations. Parameter is continuation
arclength <code>s</code> (not a prescribed crank input). Highlighted axes are the
virtual tool chart coordinates <code>tool_a</code> / <code>tool_b</code>.
Full sprint readout:
<a href="spatial4bar_explorer/v04/sprint_03_closure_and_continuation.html">V03/V04 closure continuation</a>.
</p>
<div class="anim-grid">
{explorer_animations}
</div>

<h3>Source-chain L4 — proximal exact-U spatial 4R</h3>
<p>
Fixed-position fiber continuation and independent source/reduced overlay for the
proximal <code>exact_u_pair_4r</code> architecture (V05B / V05D). Closed-mechanism
claim remains <code>LOCAL_ONLY</code>.
</p>
<div class="anim-grid">
{source_animations}
</div>

<h2 id="ledger">Rung ledger</h2>
<table>
  <tr>
    <th>Rung</th><th>Label</th><th>Strongest supported statement</th><th>Missing gate</th>
  </tr>
  <tr>
    <td><strong>L3</strong> planar 3R</td>
    <td><code class="status pass">trusted_exact_reference</code></td>
    <td>Exact fixed-position four-bar reduction and designated-link rotatability recover planar dexterity</td>
    <td>None for reference role</td>
  </tr>
  <tr>
    <td><strong>L4</strong> spatial 4R</td>
    <td><code class="status hold">local_only</code></td>
    <td>One-DOF source / orientation-curve machinery exists; proximal exact-U traced-arc match is <code>LOCAL_ONLY</code></td>
    <td>Global component-complete certificate</td>
  </tr>
  <tr>
    <td><strong>L5</strong> spatial 5R</td>
    <td><code class="status hold">parent_incomplete</code></td>
    <td>Hardened source-parent infrastructure; R3A five-point kernels and H0–H11 evidence law; frozen full-mode closeout <code>DIRECT_REFERENCE_BLOCKED</code>; reconstruction not accepted; fixed-axis UUUR still rejected as an h=c equivalence</td>
    <td>Direct-vs-oracle declared-resolution set gate; accepted source-derived child reconstruction</td>
  </tr>
  <tr>
    <td><strong>L6</strong> spatial 6R</td>
    <td><code class="status deferred">scaffold_only</code></td>
    <td>Dimensional / task contracts and ladder stubs exist</td>
    <td>Independent <code>SO(3)</code> reference; V07A held</td>
  </tr>
  <tr>
    <td><strong>L7</strong> spatial 7R</td>
    <td><code class="status deferred">deferred</code> / <code>BLOCKED</code></td>
    <td>Redundancy / gauge framing only</td>
    <td>L6 completion</td>
  </tr>
</table>

<h2 id="capabilities">Capabilities by rung</h2>
<div class="cap-grid">
  <div class="cap">
    <h3>L3 — planar reference <span class="pass">trusted</span></h3>
    <p>Analytical reachable / dexterous workspace for planar 3R.</p>
    <p>Exact four-bar assemblability, inversion, designated-link rotatability (Grashof kept separate).</p>
    <p>CLI: <code>grashof-workspace</code> · atlas / experiment figures.</p>
  </div>
  <div class="cap">
    <h3>L4 — spatial 4R source <span class="hold">local</span></h3>
    <p>Fixed-position fiber continuation and orientation-curve machinery (V05B–C).</p>
    <p>Axis aggregation with certificate split; near-aligned rejection (V05D–E).</p>
    <p>Proximal <code>exact_u_pair_4r</code>: aggregation <code>EXACT_GLOBAL</code>, closed-mechanism <code>LOCAL_ONLY</code> on a traced arc.</p>
  </div>
  <div class="cap">
    <h3>L5 — spatial 5R parent <span class="hold">incomplete</span></h3>
    <p>Implicit-manifold engine validation (V06A0); local parent patch (V06A1); multi-chart atlas (V06A2).</p>
    <p>Orientation + pointing images (V06C); task-derived <code>h=c</code> fibers (V06D1); compound SUUR audit (V06B).</p>
    <p>Shared 1D pseudo-arclength continuation; atlas stitch / component provenance; reconstruction cell paint (V06E).</p>
    <p>R3A five-point hub: <a href="l5_reconstruction/r3a/index.html">l5_reconstruction/r3a/index.html</a> — implemented kernels (oracle, direct IK, h=c control, UURU leaves). Frozen full-mode closeout is <code>DIRECT_REFERENCE_BLOCKED</code>. Reconstruction is not accepted.</p>
    <p><strong>Not yet:</strong> general 5R factorization, complete parent, S² completeness theorem. Fixed-axis UUUR remains rejected as an h=c fiber equivalence.</p>
  </div>
  <div class="cap">
    <h3>Explorer lab <span class="deferred">mechanism_explorer_only</span></h3>
    <p>Standalone spatial four-bar geometry, closure, winding, and HTML laboratory (V00–V05A).</p>
    <p>Reusable infrastructure — <strong>not</strong> manipulator-workspace evidence without source provenance and reconstruction.</p>
  </div>
  <div class="cap">
    <h3>Ladder interfaces <span class="deferred">scaffold where incomplete</span></h3>
    <p>Shared L3–L7 records: parent → fiber → child → certificate → reconstruction payloads.</p>
    <p>Readout: <a href="decomposition_ladder/index.html">decomposition_ladder/index.html</a>.</p>
  </div>
  <div class="cap">
    <h3>L6 / L7 <span class="deferred">held / deferred</span></h3>
    <p>Contracts and stubs only. No frozen decomposition-free <code>SO(3)</code> reference.</p>
    <p>V07A not authorized (ADR-047 / ADR-048).</p>
  </div>
</div>

<h2 id="r3a">R3A five-point pointing reconstruction</h2>
<p>
Implemented L5 execution program, not an accepted reconstruction. Pointing coverage in <code>S^2</code>, not dexterity.
Natural children fix one virtual-spherical chart coordinate (<code>SURU → UURU</code>)
and continue frozen geometry. They are not required to remain on <code>h=c</code>.
R3A-H0–H6 gates exist; <code>ci</code>/<code>smoke</code> cannot issue full-campaign disposition.
R3B and L6 remain held.
</p>
<ul>
  <li>Hub: <a href="l5_reconstruction/r3a/index.html">l5_reconstruction/r3a/index.html</a> (full-mode <code>DIRECT_REFERENCE_BLOCKED</code>; reconstruction not accepted)</li>
  <li>Contract: <a href="../docs/methods/NATURAL_LEAF_FAMILY_CONTRACT.md">NATURAL_LEAF_FAMILY_CONTRACT.md</a></li>
  <li>Execution: <a href="../docs/methods/R3A_L5_FIVE_POINT_EXECUTION.md">R3A_L5_FIVE_POINT_EXECUTION.md</a></li>
</ul>

<h2 id="negatives">Locked negatives</h2>
<ul>
  <li>Fixed-axis <code>UUUR</code> child: <code class="reject">REJECTED</code> (not accepted).</li>
  <li>No L5 child with <code>EXACT_GLOBAL</code> / <code>EXACT_ON_COMPONENT</code>.</li>
  <li>Campaign factorization remains <code>unresolved</code> (empty accepted children ≠ <code>no valid recombination</code>).</li>
  <li>Atlas remains <code>BUDGET_LIMITED</code>; stitch topology unresolved / not conforming.</li>
  <li>Explorer outputs are not workspace certificates.</li>
  <li>Descriptor discovery / broad Grashof-like atlas rules stay blocked until reconstruction succeeds.</li>
</ul>
<pre>current fixed-axis UUUR construction rejected;
broader 5R factorization unresolved;
V07A held pending parent/continuation completion.</pre>

<h2 id="artifacts">Evidence artifacts (what exists on disk)</h2>
<table>
  <tr><th>Capability slice</th><th>Status</th><th>Primary readout</th></tr>
  <tr>
    <td>V05B fixed-position fiber</td>
    <td>MVP</td>
    <td><a href="kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html">v05b</a></td>
  </tr>
  <tr>
    <td>V05C orientation curve</td>
    <td>MVP</td>
    <td><a href="kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html">v05c</a></td>
  </tr>
  <tr>
    <td>V05D axis aggregation</td>
    <td>MVP (<code>LOCAL_ONLY</code> closed-mech on proximal exact-U)</td>
    <td><a href="kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html">v05d</a></td>
  </tr>
  <tr>
    <td>V05E near-aligned rejection</td>
    <td>MVP</td>
    <td><a href="kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html">v05e</a></td>
  </tr>
  <tr>
    <td>R3A L5 five-point natural leaves</td>
    <td>implemented kernels; full-mode closeout <code>DIRECT_REFERENCE_BLOCKED</code>; reconstruction not accepted</td>
    <td><a href="l5_reconstruction/r3a/index.html">r3a</a></td>
  </tr>
  <tr>
    <td>V06A0 manifold engine</td>
    <td>software validation only</td>
    <td><a href="kinematic_decomposition/v06a0/sprint_v06a0_implicit_manifold.html">v06a0</a></td>
  </tr>
  <tr>
    <td>V06A1 local parent patch</td>
    <td><code>LOCAL_PATCH</code></td>
    <td><a href="kinematic_decomposition/v06a1/sprint_v06a1_local_parent_patch.html">v06a1</a></td>
  </tr>
  <tr>
    <td>V06A2 parent atlas</td>
    <td><code>BUDGET_LIMITED</code></td>
    <td><a href="kinematic_decomposition/v06a2/sprint_v06a2_parent_atlas.html">v06a2</a></td>
  </tr>
  <tr>
    <td>V06C source images</td>
    <td>partial coverage; not S² complete</td>
    <td><a href="kinematic_decomposition/v06c/sprint_v06c_source_images.html">v06c</a></td>
  </tr>
  <tr>
    <td>V06B compound SUUR</td>
    <td>LOCAL_ONLY / controls REJECTED</td>
    <td><a href="kinematic_decomposition/v06b/sprint_v06b_compound_parent.html">v06b</a></td>
  </tr>
  <tr>
    <td>V06D1 level-set fibers</td>
    <td>task-derived; not reconstruction</td>
    <td><a href="kinematic_decomposition/v06d1/sprint_v06d1_level_sets.html">v06d1</a></td>
  </tr>
  <tr>
    <td>V06D2 virtual-U / UUUR</td>
    <td><code class="reject">REJECTED</code></td>
    <td><a href="kinematic_decomposition/v06d2/sprint_v06d2_virtual_u_child.html">v06d2</a></td>
  </tr>
  <tr>
    <td>V06E reconstruction paint</td>
    <td>partial / no accepted children; factorization unresolved</td>
    <td><a href="kinematic_decomposition/v06e/sprint_v06e_reconstruction.html">v06e</a></td>
  </tr>
</table>

<h2 id="hubs">Hubs and documentation</h2>
<ul>
  <li><a href="kinematic_decomposition/index.html">Kinematic decomposition hub</a></li>
  <li><a href="decomposition_ladder/index.html">L3–L7 ladder readout</a></li>
  <li><a href="spatial4bar_explorer/index.html">Spatial four-bar explorer lab</a> (<code>mechanism_explorer_only</code>)</li>
  <li>Docs: <a href="../docs/README.md">docs/README.md</a> ·
    <a href="../docs/CURRENT_STATUS.md">CURRENT_STATUS.md</a> ·
    <a href="../docs/ROADMAP.md">ROADMAP.md</a> ·
    <a href="../docs/reference/DECISIONS.md">DECISIONS.md</a></li>
</ul>

<h2 id="next">What comes next</h2>
<p>
Forward gates live only in <code>docs/ROADMAP.md</code> (R1 behavior certificate → R2 L4 reference →
R3 L5 stitching MVP → R4–R5 L6 → R6 L7 → R7 atlases/rules after reconstruction).
</p>
<p>
Strongest next scientific candidate after the documentation reset:
one controlled source parent → one legitimate parameterized child family →
verified lifts → behavior records → stitching → independent parent comparison.
</p>

<h2 id="reproduce">Reproduce this page</h2>
<pre>PYTHONPATH=src python -m grashof_workspace.project_dashboard --results-root results
PYTHONPATH=src python -m grashof_workspace.decomposition_ladder --outdir results/decomposition_ladder --no-animation</pre>
<p class="meta">Generated by <code>grashof_workspace.project_dashboard</code>. Status date {status_date}.</p>

</body>
</html>
"""



def build_project_dashboard(
    results_root: Path,
    *,
    status_date: str = STATUS_DATE,
) -> tuple[Path, Path, Path]:
    """Write root, explorer, and kinematic-decomposition dashboard HTML files."""
    results_root = Path(results_root)
    explorer_dir = results_root / "spatial4bar_explorer"
    kd_dir = results_root / "kinematic_decomposition"
    explorer_dir.mkdir(parents=True, exist_ok=True)
    kd_dir.mkdir(parents=True, exist_ok=True)

    root_path = results_root / "index.html"
    explorer_path = explorer_dir / "index.html"
    kd_path = kd_dir / "index.html"
    root_path.write_text(render_project_index_html(status_date=status_date), encoding="utf-8")
    explorer_path.write_text(render_explorer_index_html(status_date=status_date), encoding="utf-8")
    kd_path.write_text(
        render_kinematic_decomposition_index_html(status_date=status_date),
        encoding="utf-8",
    )
    return root_path, explorer_path, kd_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate project HTML dashboards")
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("results"),
        help="Repository results/ directory (default: results)",
    )
    parser.add_argument("--status-date", default=STATUS_DATE)
    args = parser.parse_args(argv)
    root_path, explorer_path, kd_path = build_project_dashboard(
        args.results_root,
        status_date=args.status_date,
    )
    print(f"Wrote {root_path}")
    print(f"Wrote {explorer_path}")
    print(f"Wrote {kd_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
