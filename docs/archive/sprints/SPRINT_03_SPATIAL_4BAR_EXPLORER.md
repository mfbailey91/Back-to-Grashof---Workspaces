> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# Sprint Plan — Spatial 4-Bar Explorer

> **Current role:** mechanism laboratory through V04C. Geometry, closure,
> continuation, winding, visualization, and HTML infrastructure remain active.
> Any V05+ sections in this historical file are superseded by
> `KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md`; standalone mechanism results
> remain `mechanism_explorer_only` until a source-chain decomposition passes.

**Status:** approved pivot from spherical-candidate enumeration toward direct spatial four-bar family exploration  
**Purpose:** start a visual/numerical explorer for the one-DOF spatial four-bar families induced by aligned-terminal 6R pointing fibers.

## Intent

We are shifting the spatial effort away from forcing every pointing fiber into a spherical `RRRR` candidate. Instead, we will:

1. start from the aligned-terminal 6R reduced parent;
2. enumerate the ordered one-DOF spatial four-bar families;
3. decompose the virtual tool `U` into two perpendicular revolute coordinates;
4. build visual and HTML readouts per sprint;
5. compute numerical crank/rocker behavior first;
6. infer candidate Grashof-like trends from descriptor atlases.

## Mobility hierarchy

The exact two-DOF reduced parent is:

```text
S + 5R, M = 2
```

The compound-joint two-DOF parent families are:

```text
SUUR
SSRR
```

After introducing one tool-slice constraint, the ordered one-DOF families are:

```text
UUUR, UURU, URUU,
USRR, URSR, URRS.
```

Each family is evaluated with two tool-axis choices from:

```text
U_t(alpha, beta) = R_a(alpha) R_b(beta)
```

so the first explorer contains **12 family–axis cases**.

These are **12 rotatability/classification questions, not 12 unrelated physical
mechanisms or 12 required closure solves**.  A physical UXXX branch carries both
`alpha(s)` and `beta(s)`; A and B remain separate designated-axis questions and
must both remain visible in the readouts.

## Required outputs

Every sprint should publish:

- PNG figures;
- JSON data exports;
- one or more HTML readouts;
- selected representative cases extracted for visual inspection.

The HTML readouts should highlight both broad statistics and handpicked geometries.

## Sprint V00 — explorer shell and family inventory

### Goal
Stand up the visual explorer shell and enumerate the six ordered one-DOF families.

### Deliverables
- package scaffold under `src/grashof_workspace/spatial4bar_explorer/`;
- family catalog and tool-axis case catalog;
- family schematic plots;
- `index.html` and `sprint_00_overview.html`.

### Acceptance
- six families listed correctly;
- twelve tool-axis cases listed correctly;
- generated HTML readout loads without a server.

## Sprint V01 — parameter inventory and sampled geometries

### Goal
List the broadest sensible geometry descriptor inventory first, then generate a synthetic geometry corpus.

### Deliverables
- parameter inventory grouped into distances, angles, offsets, axis-center descriptors, shape descriptors, and flags;
- synthetic geometry sampler;
- histogram plots for initial descriptors;
- representative case table in HTML;
- JSON export of sampled geometries.

### Acceptance
- descriptor inventory is explicit and reviewable;
- at least three descriptor graphs are produced;
- representative cases are visible in HTML.

## Sprint V02 — branch-result and winding scaffold

### Goal
Stand up the data model for branch closure, tool coordinate range, and winding classification, even before the true closure solver is implemented.

### Deliverables
- branch-result data model;
- classification labels (`crank`, `rocker`, `change_point`, `no_assembly`, etc.);
- first classification graphs and HTML tables;
- mock or placeholder branch outputs with clear labeling.

### Acceptance
- result schema matches the intended later closure/continuation output;
- figures and HTML pages can be regenerated from code.

## Sprint V02B — physical geometry hardening

### Why this sprint exists
V01 and V02 passed their software-scaffold acceptance criteria, but the V01 sample corpus is not yet a mechanism corpus. It samples descriptor-like scalar values directly rather than constructing joint centers, joint frames, compound-joint axes, and rigid links first. V02B hardens the geometry layer before any continuation solver is allowed to consume it.

The research-data direction becomes:

```text
physical four-bar reference assembly
    -> derive descriptors
    -> solve closure / continue branch
    -> compute W
```

not:

```text
random descriptor vector
    -> infer mechanism
```

### Goal
Create physically structured reference geometries for all six ordered families and derive every atlas descriptor from those objects. Publish 3D mechanism readouts so geometry can be inspected before V03.

### Deliverables
- explicit `R`, `U`, and `S` joint geometry objects;
- four joint centers and a complete orthonormal frame at each joint;
- exact compound-joint internal axis structure (`U`: two perpendicular intersecting axes; `S`: three concurrent orthogonal axes);
- four-link loop adjacency with an explicit ground link and tool `U`;
- one canonical reference assembly for each ordered family;
- topology-preserving perturbations of canonical geometries;
- descriptors derived from the physical geometry, including the fourth loop-center distance `L41` and the two center diagonals;
- deterministic sampling independent of Python's randomized `hash()`;
- 3D PNG mechanism views showing links, joint centers, and all motion axes;
- `physical_geometry_samples.json`;
- `sprint_02b_physical_geometry.html`;
- tests for topology, U/S internal orthogonality, deterministic perturbation, descriptor consistency, and JSON serialization.

### Data status
The V01/V02 random descriptor corpus remains **scaffold/test data only**. It must not be used as crank evidence or included in the future surrogate atlas. V02B physical samples become the accepted geometry input for V03 and later research experiments.

### Acceptance
- all six canonical geometries pass structural validation;
- family letters exactly match the four joint kinds in every canonical mechanism;
- tool joint is always `U` with two perpendicular axes;
- every `U` and `S` preserves its exact internal axis constraints after perturbation;
- normalized center distances and shape descriptors can be recomputed directly from stored geometry;
- at least one canonical and one perturbed 3D mechanism are rendered per family;
- the V02B HTML readout explicitly states `PHYSICAL GEOMETRY / NO CLOSURE SOLVE YET`;
- V03 is blocked from using the legacy V01 descriptor-only corpus.

## Sprint V03 — closure and continuation proof

### Goal
Establish that the V02B physical mechanisms possess the expected regular one-dimensional closure manifolds before any crank interpretation. Use one general seven-coordinate closure kernel for all six ordered families.

### V03A — reference closure and mobility audit
Expand compound joints only as solver coordinates:

```text
R -> 1 revolute coordinate
U -> 2 ordered intersecting revolute coordinates
S -> 3 ordered concurrent revolute coordinates
```

Every ordered family therefore contains seven scalar rotational coordinates and six spatial closure constraints. At each canonical V02B reference assembly:

- verify `||r(0)||` is numerically zero;
- compute the `6 x 7` closure Jacobian;
- require rank 6 and nullity 1 at a regular reference state;
- record all singular values and the smallest nonzero singular value.

### V03B — first detailed branch proof on `UUUR`
Use the closure-Jacobian null vector as the predictor direction and a pseudo-arclength corrector to remain on the six-constraint closure manifold. Publish:

- all seven scalar coordinates versus continuation arclength;
- closure-residual norm;
- smallest nonzero closure-Jacobian singular value;
- the local `tool_alpha` versus `tool_beta` path;
- five 3D mechanism snapshots using a fixed camera/scale.

This sprint follows a branch segment only. It does not yet require full-cycle return or compute winding.

### V03C — generalize the same kernel to all six families
Run the same solver on:

```text
UUUR, UURU, URUU,
USRR, URSR, URRS.
```

Each physical mechanism is solved once. The two tool-U coordinates are read from that single branch; the 12 eventual tool-axis crank questions are not 12 separate closure solves.

### Deliverables
- general transform/product-of-exponentials closure residual;
- seven-coordinate expansion metadata with semantic coordinate names;
- finite-difference `6 x 7` closure Jacobian and SVD mobility audit;
- pseudo-arclength predictor/corrector continuation;
- `v03_reference_closure_audits.json`;
- `v03_continuation_traces.json`;
- V03 mobility, coordinate, residual, singularity-margin, and tool-U phase plots;
- fixed-view 3D `UUUR` branch snapshots;
- `sprint_03_closure_and_continuation.html`.

### Acceptance
- all six canonical V02B reference geometries close at the stored zero state;
- all six regular reference Jacobians have rank 6 / nullity 1;
- `UUUR` continuation produces a well-conditioned branch segment with closure residual near numerical precision;
- the same continuation kernel produces a nontrivial converged segment for all six families;
- V03 readouts explicitly state that no crank/winding/dexterity classification is made yet;
- S-joint x/y/z variables are labeled solver-chart coordinates and are excluded from invariant Grashof-descriptor claims.

## Sprint V04 — true winding and crank atlas

### Goal
Compute actual winding numbers for the two tool coordinates from continued one-DOF closure branches and generate the first UUUR crank atlas.

See [`docs/SPRINT_V04_WINDING_AND_CRANK_ATLAS.md`](SPRINT_V04_WINDING_AND_CRANK_ATLAS.md) for the full research definition.

### Conventions
- **Angle unwrap:** continuous nearest-`2π` accumulation of each scalar coordinate along the continuation trace.
- **Branch return:** after leaving a neighborhood of `q_0`, re-enter a wrapped tolerance ball of the reference assembly with small closure residual.
- **Winding:** `w_i = round(Δθ̃_i / 2π)` for `i ∈ {tool_alpha, tool_beta}` on a returned cycle.
- **Classification (link-specific, not planar Grashof):** `crank` if `|w_i| ≥ 1`, `rocker` if returned and `w_i = 0`, `open_branch` if no return within budget.

### Deliverables
- angle unwrapping;
- branch return detection (`continue_until_return`);
- winding calculation `W = (w_alpha, w_beta)`;
- branch-classification plots;
- representative crank and rocker cases rendered as plots and HTML cards;
- `sprint_04_winding_and_crank.html`.

### Acceptance
- winding is computed from continued branches, not inferred heuristically;
- at least one crank and one rocker example are visualized;
- UUUR-first; other families remain V03 diagnostics until winding is verified on UUUR.

## Sprint V04B — virtual-U robustness and orientation sweep

### Goal
Verify that V04 crank/rocker labels are stable under continuation step size, tangent direction, controlled virtual tool-`U` orientation, and tool-axis serial order (`ab` vs `ba`) before descriptor mining.

See [`docs/SPRINT_V04B_VIRTUAL_U_ROBUSTNESS.md`](SPRINT_V04B_VIRTUAL_U_ROBUSTNESS.md).

### Guardrail for V05
V04B `phi` is a **diagnostic sensitivity experiment only**.  Rotating an
arbitrarily chosen standalone virtual-U frame and observing different answers
shows that the U axes cannot be chosen arbitrarily.  It does not establish
`phi` as a dexterity-atlas parameter.

Before V05 uses UXXX results as dexterity evidence, the `S_v -> U_v` reduction
must derive the A/B axes from an explicit pointing slice/fiber.  Standalone
`phi` sweeps remain mechanism-laboratory diagnostics. See
[`SPATIAL_POINTING_SLICE_CONTRACT.md`](../../methods/SPATIAL_POINTING_SLICE_CONTRACT.md) and
[`AUDIT_TOOL_AXIS_AND_PHI.md`](../audits/AUDIT_TOOL_AXIS_AND_PHI.md).

### Deliverables
- standalone runner `spatial4bar_explorer.v04b`;
- step-size / direction-reversal / orientation-sweep JSON and plots;
- `sprint_04b_virtual_u_robustness.html`.

## Sprint V04C — virtual-U equivalence and fiber interpretation

### Goal
Determine whether tool-`U` axis order is a removable coordinate symmetry, resolve budget-limited open cases, and densify only the observed orientation-transition intervals before V05 descriptor mining.

See [`docs/SPRINT_V04C_VIRTUAL_U_EQUIVALENCE.md`](SPRINT_V04C_VIRTUAL_U_EQUIVALENCE.md).

### Guardrail for V05
Any removal of `axis_order` or reduction of the `phi` domain is provisional until V04C supports the symmetry on the tested geometry and later corpus validation repeats it.

### Deliverables
- standalone runner `spatial4bar_explorer.v04c`;
- shifted `ab`/`ba` equivalence check;
- 180-degree periodicity check;
- extended-budget resolution of the V04B open cases;
- adaptive transition-state and singularity-margin plots;
- `sprint_04c_virtual_u_equivalence.html`.

## Sprint V05 — all-family winding atlas

### Goal
Generalize true returned-cycle winding, coverage, and branch-status evaluation from `UUUR` to all six ordered spatial four-bar families before attempting descriptor mining.

See [`docs/SPRINT_V05_ALL_FAMILY_WINDING_ATLAS.md`](SPRINT_V05_ALL_FAMILY_WINDING_ATLAS.md).

### Deliverables
- true winding results for `UUUR`, `UURU`, `URUU`, `USRR`, `URSR`, and `URRS`;
- modest physical geometry corpus per family;
- canonical virtual-`U` sweep according to V04C;
- family-specific winding / coverage / class-distribution plots;
- representative crank, rocker, boundary, and unresolved mechanism gallery;
- `sprint_05_all_family_winding_atlas.html`.

### Gate A
Do not begin cross-family descriptor mining until the true outcome distribution and unresolved fraction are characterized for all six families.

## Sprint V06 — descriptor trend mining

### Goal
Identify interpretable invariant physical descriptors and retained virtual parameters that organize crank / rocker / boundary behavior within each viable family.

See [`docs/SPRINT_V06_DESCRIPTOR_TREND_MINING.md`](SPRINT_V06_DESCRIPTOR_TREND_MINING.md).

### Deliverables
- frozen discovery / holdout split;
- univariate and bivariate classification plots;
- dimensionless ratio and trigonometric descriptor analysis;
- shallow interpretable baseline models;
- counterexample and interesting-geometry gallery;
- `sprint_06_descriptor_trend_mining.html`.

## Sprint V07 — candidate spatial Grashof-like rules

### Goal
Convert the strongest V06 empirical structures into explicit, family-specific, falsifiable crank hypotheses and test them on held-out, fresh, and near-boundary mechanisms.

See [`docs/SPRINT_V07_CANDIDATE_SPATIAL_GRASHOF_RULES.md`](SPRINT_V07_CANDIDATE_SPATIAL_GRASHOF_RULES.md).

### Deliverables
- candidate-rule registry by family;
- held-out metrics and counterexample gallery;
- near-boundary campaigns and singularity comparisons;
- analytical follow-up notes for the strongest candidates;
- `sprint_07_candidate_spatial_grashof_rules.html`.

### Gate B
Choose rule-backed or numerical-atlas evaluation paths family by family. A messy analytical boundary is allowed to route to V08 rather than block the project.

## Sprint V08 — fast crank evaluator

### Goal
Create a conservative fast evaluator using direct rules where justified and a sparse adaptive numerical atlas elsewhere, with exact continuation as fallback.

See [`docs/SPRINT_V08_FAST_CRANK_EVALUATOR.md`](SPRINT_V08_FAST_CRANK_EVALUATOR.md).

### Deliverables
- common crank-evaluator query/result API;
- rule-backed and atlas-backed family adapters;
- uncertainty / OOD handling and exact fallback;
- held-out speed / agreement benchmark;
- `sprint_08_fast_crank_evaluator.html`.

## Sprint V09 — 6R dexterity reconstruction and validation

### Goal
Return to a synthetic aligned-terminal 6R manipulator and test whether extracted virtual spatial-four-bar crank / coverage fields predict independent numerical orientation capability and dexterous-workspace structure.

See [`docs/SPRINT_V09_6R_DEXTERITY_RECONSTRUCTION.md`](SPRINT_V09_6R_DEXTERITY_RECONSTRUCTION.md).

### Deliverables
- deterministic robot-to-virtual-four-bar extraction;
- fiber winding / coverage fields at Cartesian points;
- independent numerical orientation-capability reference;
- pointwise prediction-vs-reference validation;
- dexterous / non-dexterous / unresolved workspace reconstruction;
- runtime comparison and failure gallery;
- `sprint_09_6r_dexterity_reconstruction.html`.

### Gate C
Do not claim a dexterous-workspace characterization method unless the virtual-mechanism predictions agree with independent manipulator orientation truth under explicitly stated assumptions.

## Guardrails

- keep this effort separate from the trusted planar kernel;
- prefer synthetic exact geometries before any URDF or industrial robot import;
- make visual inspection a first-class output, not a side effect;
- always preserve the distinction between: full geometry parameters, derived descriptors, empirical trends, candidate rules, analytical derivations, and robot-workspace validation;
- unresolved / OOD cases must remain explicit rather than being forced into binary classifications.
