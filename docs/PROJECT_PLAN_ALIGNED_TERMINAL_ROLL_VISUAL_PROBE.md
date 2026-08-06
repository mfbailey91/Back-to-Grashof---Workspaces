# Project Plan — Aligned Terminal-Roll Visual Mechanism Probe

**Status:** Proposed experimental track  
**Project type:** Small visualization-first software test project  
**Production status:** Isolated from the trusted planar workspace kernel  
**Primary question:** Can the reduced aligned-terminal mechanism be understood and screened more reliably by assembling and visualizing its physical and virtual kinematic elements before constructing manifolds or fibers?

## 1. Project intent

Build a compact, reproducible visual probe around one deliberately constructed six-degree-of-freedom revolute manipulator.

The probe shall:

1. compute forward kinematics for one reasonable nonsingular joint configuration;
2. plot links, joint origins, joint coordinate frames, and infinite joint axes;
3. add a virtual spherical closure centered at the tool task point;
4. show the aligned terminal-roll symmetry and quotient visually;
5. enumerate exact adjacent intersecting-axis groupings among `R1` through `R5`;
6. display all resulting four-joint compound-parent topologies on top of a transparent manipulator;
7. expand each compound parent into coordinate-dependent candidate `RRRR` axis tuples;
8. draw those axes in space for visual concurrency inspection;
9. export a static, no-server browser for review.

The first release is explanatory and diagnostic. It is not a spherical-four-bar certification tool.

## 2. Research ordering

The visual probe reverses the previous explanatory sequence.

Previous sequence:

```text
fixed-position set
-> reduced manifold
-> one-dimensional fiber
-> candidate spherical four-bar
```

Probe sequence:

```text
physical 6R chain
-> physical axes and links
-> virtual spherical closure
-> terminal-roll quotient
-> exact intersecting-axis groupings
-> compound-parent topology
-> candidate four-axis tuple
-> visual screening
```

Mathematical continuation and spherical-linkage validation remain downstream.

## 3. Scope

### In scope

- one synthetic aligned-terminal 6R architecture;
- homogeneous-transform forward kinematics;
- world-frame joint origins and axis directions;
- simple link geometry;
- virtual spherical-joint glyph at the task point;
- visual terminal-roll quotient;
- exact line-line relationship classification;
- enumeration of disjoint adjacent intersecting-axis pairs;
- compound-parent representations such as `SRUU`, `SURU`, and `SUUR`;
- coordinate decomposition of `S` and `U` joints for finite visual candidate enumeration;
- interactive three-dimensional inspection;
- static HTML output and contact sheets;
- deterministic tests of FK and enumeration semantics.

### Out of scope

- URDF parsing;
- named industrial manipulators;
- inverse kinematics;
- workspace sweeps;
- numerical continuation;
- configuration manifolds;
- fiber construction;
- mobility proof beyond descriptive bookkeeping;
- global spherical-axis concurrency validation;
- spherical arc invariance;
- inactive-coordinate locking;
- parent/four-bar motion equivalence;
- McCarthy–Soh `T1`-`T4` classification;
- joint limits, collision, dynamics, torque, or stiffness;
- production integration with the planar workspace API.

## 4. Geometry conventions

### 4.1 Revolute axis

Each revolute axis is represented in world coordinates by:

```text
AxisLine(point, direction)
```

where `direction` is normalized and axis sign is treated as visually meaningful only for frame display, not geometric incidence.

### 4.2 Axis relationship labels

Every adjacent axis pair shall be classified as one of:

- `collinear`;
- `intersecting`;
- `parallel_distinct`;
- `skew`;
- `numerically_ambiguous`.

Only `intersecting` pairs may form an exact universal-joint representation.

### 4.3 Compound-joint terminology

- `R_i + R_(i+1) -> U_i,i+1` only for exact noncollinear intersection.
- Collinear axes may be displayed as a redundant or collapsed revolute pair, but never as `U`.
- Skew or merely near-intersecting axes must remain separate physical revolutes.

### 4.4 Virtual spherical joint

The virtual spherical closure is centered at the fixed task point `p`.

For display, it is represented by three tool-frame-aligned coordinate axes:

```text
S_v = {Sx, Sy, Sz}
```

This is a chosen coordinate decomposition, not a claim that the spherical joint intrinsically contains only three available axes.

### 4.5 Candidate `RRRR` language

The output shall use:

> candidate `RRRR` axis tuple

until later work proves:

- one-dimensional motion;
- global concurrency;
- fixed spherical dimensions;
- inactive-coordinate locking;
- motion equivalence.

## 5. Synthetic architecture requirements

The synthetic arm should be built as a topology playground rather than a representative commercial robot.

Required properties:

1. six revolute joints;
2. the task point lies on the `R6` axis;
3. the selected tool direction is parallel to `R6`;
4. the default pose is asymmetric and visually readable;
5. the architecture deliberately supports several adjacent intersecting-axis relations among `R1` through `R5`;
6. all intended intersections are exact by construction;
7. no zero-length link is hidden inside an opaque transform convention;
8. link offsets are sufficient to make shoulder, elbow, wrist, and task centers visually distinguishable.

The architecture configuration must be stored as data, not embedded only in rendering code.

## 6. Expected topology enumeration

For five remaining physical revolutes after quotienting terminal roll, the complete combinatorial set of two disjoint adjacent pairs is:

```text
P12_P34 -> paired U12 and U34; remaining R5
P12_P45 -> paired U12 and U45; remaining R3
P23_P45 -> paired U23 and U45; remaining R1
```

For traversal from the virtual spherical joint toward ground, the displayed parent labels are:

```text
P12_P34 -> SRUU
P12_P45 -> SURU
P23_P45 -> SUUR
```

These three records are combinatorial possibilities. A record is enabled only when both requested adjacent pairs are exact intersections in the synthetic architecture.

## 7. Candidate enumeration

For one enabled compound parent:

- select one display axis from `S_v`: 3 choices;
- select one coordinate axis from the first `U`: 2 choices;
- select one coordinate axis from the second `U`: 2 choices;
- include the remaining physical `R`: 1 choice.

Therefore:

```text
3 * 2 * 2 = 12
```

candidate axis tuples are shown per enabled parent.

With all three compound parents enabled, the visual browser contains:

```text
3 * 12 = 36
```

candidate tuples.

This count is explicitly coordinate-convention-dependent and is not an exhaustive enumeration of the continuum of axes admitted by `S_v`.

## 8. Proposed package layout

```text
src/grashof_workspace/visual_probe/
    __init__.py
    model.py
    transforms.py
    forward_kinematics.py
    axis_geometry.py
    virtual_closure.py
    reductions.py
    candidates.py
    scene.py
    export.py
    cli.py

configs/
    aligned_terminal_6r_visual_probe.json

tests/visual_probe/
    test_forward_kinematics.py
    test_axis_relationships.py
    test_terminal_alignment.py
    test_reduction_enumeration.py
    test_candidate_enumeration.py
    test_scene_records.py

outputs/aligned_terminal_visual_probe/
    index.html
    data/
    scenes/
    contact_sheets/
```

The package must not import from or mutate the planar analytical kernel except for ordinary project utilities that are geometry-neutral.

## 9. Output scenes

### Scene A — Physical manipulator

Show:

- link centerlines or simple cylindrical links;
- joint centers `J1` through `J6`;
- finite frame triads;
- extended revolute axes;
- base frame;
- tool frame;
- task point `p`;
- selected pointing direction `d`.

### Scene B — Virtual spherical closure

Show the physical arm at reduced opacity and add:

- spherical-joint center at `p`;
- tool-aligned `Sx`, `Sy`, `Sz` axes;
- virtual ground closure;
- labels distinguishing physical and virtual geometry.

### Scene C — Terminal-roll quotient

Keep `R6` visible, but show it as:

- translucent or dashed;
- aligned with `d`;
- accompanied by a roll arrow;
- labeled `quotiented terminal roll`.

### Scene D — Compound-parent reductions

Generate one scene per enabled pair set:

- transparent physical manipulator;
- emphasized selected joint pairs;
- universal-joint glyphs at exact intersections;
- remaining revolute axis;
- virtual spherical closure;
- topology and pair-set labels.

### Scene E — Candidate axis browser

Provide selectors for:

- parent pair set;
- spherical coordinate axis;
- first universal-joint coordinate axis;
- second universal-joint coordinate axis;
- physical-arm visibility;
- unselected-axis visibility;
- joint-center visibility;
- perspective or orthographic camera.

### Scene F — Contact sheet

Export one fixed-camera thumbnail for each candidate tuple with direct labels.

## 10. Sprint plan

## Sprint V00 — Project shell and guardrails

### Goal

Create the isolated visual-probe package, configuration schema, CLI shell, and documentation without implementing robot geometry.

### Work packages

- add the package and test directories;
- define immutable typed records for joints, transforms, axes, links, and scenes;
- add a JSON configuration loader;
- add `grashof-visual-probe` CLI entry point;
- define output-directory conventions;
- add a visible disclaimer that this is not production or certification code.

### Acceptance criteria

- package imports cleanly;
- configuration validation rejects malformed axes and transforms;
- CLI produces a manifest with no scenes yet;
- planar tests remain unchanged and passing;
- no spatial algorithm is imported into the planar modules.

### Exit artifact

`outputs/aligned_terminal_visual_probe/manifest.json`

## Sprint V01 — Synthetic 6R forward kinematics

### Goal

Build one deterministic synthetic aligned-terminal 6R manipulator and render its physical pose.

### Work packages

- implement homogeneous transforms;
- implement forward kinematics;
- emit every joint origin and world-frame axis;
- emit link endpoints and tool transform;
- define one readable default joint configuration;
- render Scene A.

### Acceptance criteria

- FK matches independently calculated transform snapshots;
- every axis direction is unit length;
- link endpoints join without gaps under the chosen representation;
- changing one joint rotates only downstream geometry;
- output is visually asymmetric and readable.

### Exit artifact

`scenes/01_physical_manipulator.html`

## Sprint V02 — Virtual closure and aligned-roll display

### Goal

Place the virtual spherical closure at the tool task point and make the terminal-roll symmetry visually explicit.

### Work packages

- define task point and pointing-axis conventions;
- add tool-aligned spherical coordinate axes;
- add virtual ground closure graphics;
- show `R6` and `d` coincidence;
- add roll-only comparison poses differing in `q6`;
- render Scenes B and C.

### Acceptance criteria

- the spherical-joint center equals the FK task point;
- `R6` contains the task point;
- `R6` is parallel to the selected pointing direction;
- two displayed `q6` values preserve `p` and `d` while changing the full tool frame;
- quotient graphics never imply physical deletion of `R6`.

### Exit artifacts

- `scenes/02_virtual_spherical_closure.html`
- `scenes/03_terminal_roll_quotient.html`

## Sprint V03 — Axis relationships and compound-parent enumeration

### Goal

Classify adjacent physical axis relationships and enumerate every valid disjoint adjacent-pair reduction.

### Work packages

- implement robust line-line relationship classification;
- calculate exact intersection points where applicable;
- enumerate `P12_P34`, `P12_P45`, and `P23_P45`;
- reject pair sets containing skew, parallel-distinct, or collinear pairs;
- produce a machine-readable reduction report;
- render Scene D for every enabled reduction.

### Acceptance criteria

- intersecting, collinear, parallel-distinct, and skew fixtures classify correctly;
- no `U` is created from collinear axes;
- no geometry is snapped or modified during reduction;
- pair-set and topology labels are deterministic;
- at least two compound-parent scenes are enabled by the synthetic architecture; the preferred fixture enables all three.

### Exit artifacts

- `data/axis_relationships.json`
- `data/compound_parents.json`
- `scenes/reductions/*.html`

## Sprint V04 — Candidate `RRRR` axis-tuple enumeration

### Goal

Expand every enabled compound parent into its coordinate-dependent four-axis selections.

### Work packages

- define ordered coordinate axes for `S_v` and each `U`;
- enumerate 12 candidates per enabled parent;
- assign stable candidate identifiers;
- preserve references to source physical or virtual axes;
- generate candidate metadata and fixed-camera previews.

### Acceptance criteria

- each enabled parent produces exactly 12 unique identifiers;
- three enabled parents produce exactly 36 records;
- each candidate contains one `S`, two `U` coordinate axes, and one physical remaining `R`;
- source-axis provenance is never lost;
- documentation states that enumeration is not exhaustive over the spherical-axis continuum.

### Exit artifacts

- `data/candidates.json`
- `contact_sheets/candidates.html`

## Sprint V05 — Interactive visual candidate browser

### Goal

Create a static, no-server dashboard for inspecting compound parents and candidate axis tuples in three dimensions.

### Work packages

- implement parent and coordinate selectors;
- add transparent-arm and axis visibility toggles;
- add perspective and orthographic camera presets;
- add direct labels and a legend;
- display candidate provenance and topology metadata;
- add next/previous candidate navigation;
- add permalink-compatible query parameters if possible without a framework.

### Acceptance criteria

- all candidates are reachable from the interface;
- the scene remains legible at laptop width;
- selected axes are visually distinguishable from unselected axes without relying only on color;
- the browser works from local static files;
- no remote assets, server, or build system is required.

### Exit artifact

`outputs/aligned_terminal_visual_probe/index.html`

## Sprint V06 — Visual audit, regression fixtures, and closeout

### Goal

Turn the probe into a reproducible review instrument and record what the visuals actually reveal.

### Work packages

- recreate the first two previously rejected candidate interpretations when their axis provenance can be mapped;
- add one obvious concurrency-failure fixture;
- add one deliberately constructed concurrency-pass-at-one-pose fixture;
- add captions explaining why single-pose visual passage is insufficient;
- freeze camera presets and screenshot/contact-sheet outputs;
- write a closeout report separating visual findings from mathematical claims.

### Acceptance criteria

- the two historical failures are identifiable or explicitly documented as unmappable;
- visual false positives are demonstrated;
- the report lists which candidates deserve later numerical testing;
- no candidate is called a spherical four-bar based on this project alone;
- all unit tests and static generation commands pass from a clean checkout.

### Exit artifacts

- `docs/REPORT_ALIGNED_TERMINAL_ROLL_VISUAL_PROBE.md`
- frozen dashboard and contact sheet
- candidate shortlist for a later validation project

## 11. Definition of done

The project is complete when a reviewer can use the static output to explain:

1. how the synthetic 6R arm is assembled;
2. where every physical joint axis lies;
3. where the virtual spherical closure is placed;
4. why `R6` is displayed as terminal roll;
5. which adjacent revolute pairs form exact universal joints;
6. which compound-parent topologies follow from those pairings;
7. how each candidate four-axis tuple is selected;
8. why visual concurrency is only a preliminary screening observation.

## 12. Stop conditions

Pause and revise the fixture if:

- the architecture requires hidden axis snapping;
- intended intersections are pose-dependent accidents rather than architectural properties;
- the terminal axis does not contain the task point;
- the terminal axis is not aligned with the selected pointing direction;
- topology labels depend on inconsistent traversal conventions;
- the browser obscures source-axis provenance;
- the visual project begins accumulating continuation or certification mathematics.

## 13. Follow-on project boundary

A later validation project may add:

- least-squares common-center residuals;
- branch-wide concurrency;
- spherical arc invariance;
- inactive-coordinate locking;
- fiber definition and continuation;
- parent/four-bar tangent and motion equivalence;
- McCarthy–Soh classification.

Those tasks are intentionally excluded here so the first question remains mechanical and visual:

> What mechanism are we actually assembling from the manipulator, task closure, and axis reductions?

