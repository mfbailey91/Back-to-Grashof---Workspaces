"""Reproducible project HTML dashboard generator.

Writes:

- ``results/index.html`` — project-so-far printout (V05–V09 + L3–L7 crosswalk)
- ``results/spatial4bar_explorer/index.html`` — cumulative explorer + active ladder
- ``results/kinematic_decomposition/index.html`` — active-program hub (V05B–E)

Reproducible command::

    PYTHONPATH=src python -m grashof_workspace.project_dashboard \\
      --results-root results
"""

from __future__ import annotations

import argparse
from pathlib import Path

STATUS_DATE = "2026-08-13"

# Proximal exact_u_pair_4r closed-mechanism is LOCAL_ONLY on a traced arc (ADR-034);
# axis aggregation remains EXACT_GLOBAL; EXACT_ON_COMPONENT is reserved.

_SHARED_CSS = """
  body { font-family: Georgia, "Times New Roman", serif; max-width: 920px; margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.45; color: #1a1a1a; }
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
  .note { background: #faf7f0; border-left: 3px solid #c4a35a; padding: 0.6rem 0.85rem; margin: 1rem 0; }
  @media print {
    body { max-width: none; margin: 0; }
    a { color: inherit; text-decoration: none; }
    a::after { content: " (" attr(href) ")"; font-size: 0.8em; color: #555; }
    ul.toc { columns: 1; }
  }
"""


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
  Explorer sprints <strong>V00–V05A</strong> remain a <code>mechanism_explorer_only</code> laboratory
  (deferred V10 prep). The <strong>active</strong> source-chain program is kinematic decomposition
  <strong>V05B–E (audit-corrected MVP)</strong> with proximal <code>exact_u_pair_4r</code>
  closed-mechanism <strong>LOCAL_ONLY</strong> on a budget-limited traced arc; multi-component and other architectures
  remain unresolved. Direct V06A parent construction may proceed without inheriting an L4 component certificate.
  Hub: <a href="../kinematic_decomposition/index.html">../kinematic_decomposition/index.html</a>.
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
<a href="../../docs/PROJECT_REFERENCE_INDEX.md">PROJECT_REFERENCE_INDEX.md</a>
· <a href="../../docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md">KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</a>
· <a href="../../docs/ROADMAP.md">ROADMAP.md</a>
· explorer notes: <a href="../../docs/SPRINT_03_SPATIAL_4BAR_EXPLORER.md">SPRINT_03_SPATIAL_4BAR_EXPLORER.md</a>
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
      (<a href="../../docs/SPATIAL_POINTING_SLICE_CONTRACT.md">SPATIAL_POINTING_SLICE_CONTRACT.md</a>);
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
· corrections: <a href="../../docs/V05_AUDIT_CORRECTIONS.md">V05_AUDIT_CORRECTIONS.md</a>
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
<a href="../../docs/PROJECT_REFERENCE_INDEX.md">PROJECT_REFERENCE_INDEX.md</a>
· <a href="../../docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md">KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</a>
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
<title>Kinematic Decomposition — active V05B–E hub</title>
<style>
{_SHARED_CSS}
</style>
</head>
<body>

<h1>Kinematic Decomposition</h1>
<p class="meta">
  <strong>Active source-chain program hub (V05B–E)</strong><br>
  Artifact root: <code>results/kinematic_decomposition/</code> · Status date: {status_date}<br>
  <a href="../index.html">Project index (so far)</a> ·
  <a href="../decomposition_ladder/index.html">L3–L7 ladder readout</a>
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
<a href="../../docs/PROJECT_REFERENCE_INDEX.md">PROJECT_REFERENCE_INDEX.md</a>
· <a href="../../docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md">KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</a>
· <a href="../../docs/V05_AUDIT_CORRECTIONS.md">V05_AUDIT_CORRECTIONS.md</a>
· <a href="../../docs/JACOBIAN_AND_DERIVATIVE_POLICY.md">JACOBIAN_AND_DERIVATIVE_POLICY.md</a>
· <a href="../../docs/DECISIONS.md">DECISIONS.md</a>
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
    <td class="status pass">PARENT ATLAS (not closed)</td>
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
    <td class="status pass">ONE UUUR CHILD (not reconstruction)</td>
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
<p><strong>V07</strong> — V06E compared source fibers to the frozen V06C grid
(ADR-042 / ADR-043). Coverage comparison is unevaluable when interior
<code>COVERED</code> cells are empty; factorization is
<code>unresolved</code>; V06 is not passed. V07A remains next.
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
    """Return the root project-so-far printout joining V05-V09 and L3-L7 status."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Back to Grashof — project index printout (so far)</title>
<style>
{_SHARED_CSS}
</style>
</head>
<body>

<h1>Back to Grashof — project index printout (so far)</h1>
<p class="meta">
  <strong>Active scientific sequence:</strong>
  <code>docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md</code><br>
  Optional L3–L7 ladder scaffold is subordinate to that program.
  Status date: {status_date}
</p>

<div class="note">
  This page joins the three evidence hubs. It does not replace them and does not
  fabricate V06–V09 science artifacts. Proximal <code>exact_u_pair_4r</code>
  closed-mechanism is <code>LOCAL_ONLY</code> on a traced arc (ADR-034); multi-component
  <code>EXACT_GLOBAL</code> and other architectures remain unresolved.
</div>

<h2>Contents</h2>
<ul class="toc">
  <li><a href="#v05v09">Active V05–V09 status</a></li>
  <li><a href="#l3l7">Optional L3–L7 scaffold</a></li>
  <li><a href="#crosswalk">L↔V crosswalk</a></li>
  <li><a href="#hubs">Evidence hubs</a></li>
  <li><a href="#reproduce">Reproduce</a></li>
</ul>

<h2 id="v05v09">Active V05–V09 status</h2>
<table>
  <tr>
    <th>Sprint</th><th>Source</th><th>Target</th><th>Status</th><th>Primary artifacts</th>
  </tr>
  <tr>
    <td><strong>V05</strong></td>
    <td>spatial 4R + S_v</td>
    <td>orientation curve / 1D fiber</td>
    <td><code>LOCAL_ONLY</code> (proximal <code>exact_u_pair_4r</code> traced-arc match); other architectures unresolved</td>
    <td>
      <a href="kinematic_decomposition/index.html">KD hub</a> ·
      <a href="kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html">V05B</a> ·
      <a href="kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html">V05C</a> ·
      <a href="kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html">V05D</a> ·
      <a href="kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html">V05E</a>
    </td>
  </tr>
  <tr>
    <td><strong>V06</strong></td>
    <td>spatial 5R + S_v</td>
    <td>S² pointing parent</td>
    <td>V06E reconstruction closeout (partial source fibers; no accepted children; V06 not passed); V07A next</td>
    <td>
      <a href="kinematic_decomposition/v06a0/sprint_v06a0_implicit_manifold.html">V06A0</a> ·
      <a href="kinematic_decomposition/v06a1/sprint_v06a1_local_parent_patch.html">V06A1</a> ·
      <a href="kinematic_decomposition/v06a2/sprint_v06a2_parent_atlas.html">V06A2</a> ·
      <a href="kinematic_decomposition/v06c/sprint_v06c_source_images.html">V06C</a> ·
      <a href="kinematic_decomposition/v06b/sprint_v06b_compound_parent.html">V06B</a> ·
      <a href="kinematic_decomposition/v06d1/sprint_v06d1_level_sets.html">V06D1</a> ·
      <a href="kinematic_decomposition/v06d2/sprint_v06d2_virtual_u_child.html">V06D2</a> ·
      <a href="kinematic_decomposition/v06e/sprint_v06e_reconstruction.html">V06E</a> ·
      <a href="decomposition_ladder/index.html">L5 scaffold</a>
    </td>
  </tr>
  <tr>
    <td><strong>V07</strong></td>
    <td>spatial 6R + S_v</td>
    <td>SO(3) orientation reference</td>
    <td>Not started — Gate K3 freeze absent; L6 scaffold only</td>
    <td><a href="decomposition_ladder/index.html">L6 scaffold</a> (seed audit, not frozen SO(3))</td>
  </tr>
  <tr>
    <td><strong>V08</strong></td>
    <td>aligned 6R quotient</td>
    <td>pointing + roll vs V07 truth</td>
    <td>Blocked on V07 reference (Gate K4)</td>
    <td>—</td>
  </tr>
  <tr>
    <td><strong>V09</strong></td>
    <td>reconstruction</td>
    <td>coverage from accepted children</td>
    <td>Blocked on prior gates (Gate K5)</td>
    <td>—</td>
  </tr>
</table>

<h2 id="l3l7">Optional L3–L7 scaffold</h2>
<p>
Process labels (<code>SCAFFOLD</code>, <code>BLOCKED</code>) are separate from certificate
statuses (<code>EXACT_GLOBAL</code>, <code>EXACT_ON_COMPONENT</code>, <code>LOCAL_ONLY</code>, <code>UNRESOLVED</code>).
</p>
<table>
  <tr>
    <th>Rung</th><th>Maps to</th><th>Process</th><th>Certificate / evidence</th><th>Notes</th>
  </tr>
  <tr>
    <td><strong>L3</strong></td>
    <td>planar calibration</td>
    <td><code>SCAFFOLD</code></td>
    <td>Map <code>EXACT_GLOBAL</code> at each radius</td>
    <td>Trusted analytical planar 3R→4R retrofit</td>
  </tr>
  <tr>
    <td><strong>L4</strong></td>
    <td>V05</td>
    <td><code>SCAFFOLD</code></td>
    <td><code>LOCAL_ONLY</code> traced-arc match for proximal exact_u_pair_4r</td>
    <td>Wraps audited V05D closed-mechanism evidence</td>
  </tr>
  <tr>
    <td><strong>L5</strong></td>
    <td>V06</td>
    <td><code>SCAFFOLD</code></td>
    <td>All certs <code>UNRESOLVED</code>; nullity-2 seed audit</td>
    <td>Not a 2D parent; not pointing reconstruction (ADR-032)</td>
  </tr>
  <tr>
    <td><strong>L6</strong></td>
    <td>V07-first</td>
    <td><code>SCAFFOLD</code></td>
    <td>All certs <code>UNRESOLVED</code>; nullity-3 seed audit</td>
    <td>Not a frozen SO(3) reference; not V08 (ADR-033)</td>
  </tr>
  <tr>
    <td><strong>L7</strong></td>
    <td>deferred</td>
    <td><code>BLOCKED</code></td>
    <td><code>UNRESOLVED</code></td>
    <td>Outside active V05–V09 until multi-component certificates exist</td>
  </tr>
</table>
<p>
Full ladder readout:
<a href="decomposition_ladder/index.html">results/decomposition_ladder/index.html</a>
</p>

<h2 id="crosswalk">L↔V crosswalk</h2>
<table>
  <tr><th>Ladder rung</th><th>Active sprint</th><th>Relationship</th></tr>
  <tr><td>L3</td><td>—</td><td>Planar calibration interface (trusted exact map)</td></tr>
  <tr><td>L4</td><td>V05</td><td>Wraps V05 closed-mechanism evidence into shared records</td></tr>
  <tr><td>L5</td><td>V06</td><td>Scaffold interface; V06E closeout (not passed), reconstruction unresolved</td></tr>
  <tr><td>L6</td><td>V07 then V08</td><td>Scaffold interface; V07A SO(3) freeze remains next science</td></tr>
  <tr><td>L7</td><td>deferred</td><td>Blocked pending nested-slice / multi-component work</td></tr>
</table>

<h2 id="hubs">Evidence hubs</h2>
<ul>
  <li><a href="spatial4bar_explorer/index.html">Explorer printout</a> — V00–V05A laboratory + cumulative history</li>
  <li><a href="kinematic_decomposition/index.html">Kinematic decomposition hub</a> — active V05B–E source-chain evidence</li>
  <li><a href="decomposition_ladder/index.html">Decomposition ladder readout</a> — L3–L7 scaffold interfaces</li>
</ul>
<p>
Key docs:
<a href="../docs/ROADMAP.md">ROADMAP.md</a> ·
<a href="../docs/DECISIONS.md">DECISIONS.md</a> (ADR-028–042) ·
<a href="../docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md">V05–V09 program</a> ·
<a href="../docs/DECOMPOSITION_LADDER_L3_L7_PROGRAM.md">L3–L7 program</a> ·
<a href="../docs/PROJECT_REFERENCE_INDEX.md">PROJECT_REFERENCE_INDEX.md</a>
</p>

<h2 id="reproduce">Reproduce</h2>
<pre>PYTHONPATH=src python -m grashof_workspace.project_dashboard --results-root results
PYTHONPATH=src python -m grashof_workspace.decomposition_ladder --outdir results/decomposition_ladder --no-animation</pre>
<p>
The ladder readout is generated separately; regenerate both commands after scaffold or
V05 evidence changes.
</p>

<p class="meta" style="margin-top:2rem;">
  Regenerate this page with
  <code>python -m grashof_workspace.project_dashboard --results-root results</code>.
</p>

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
