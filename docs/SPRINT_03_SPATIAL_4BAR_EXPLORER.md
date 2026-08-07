# Sprint Plan — Spatial 4-Bar Explorer

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
Compute actual winding numbers for the two tool coordinates and generate the first crank atlas.

### Deliverables
- angle unwrapping;
- branch return detection;
- winding calculation `W = (w_alpha, w_beta)`;
- branch-classification plots;
- representative crank and rocker cases rendered as plots and HTML cards.

### Acceptance
- winding is computed from continued branches, not inferred heuristically;
- at least one crank and one rocker example are visualized.

## Sprint V05 — descriptor trend mining

### Goal
Correlate crank classifications with the descriptor atlas.

### Deliverables
- univariate and bivariate classification plots;
- dimensionless ratio analysis;
- first candidate trend statements;
- extracted "interesting geometries" gallery.

### Acceptance
- at least a few descriptors show visible structure;
- HTML readout explains the emerging patterns.

## Sprint V06 — candidate Grashof-like rules

### Goal
Use the numerical atlas to nominate family-specific Grashof-like candidate rules.

### Deliverables
- simple interpretable classifiers;
- candidate inequality or threshold hypotheses;
- fail/pass counterexamples gallery;
- readout separating robust patterns from weak or misleading ones.

### Acceptance
- candidate rules are explicit and tied to observed evidence;
- no analytical claim is made without clearly marking it as a hypothesis.

## Guardrails

- keep this effort separate from the trusted planar kernel;
- prefer synthetic exact geometries before any URDF or industrial robot import;
- make visual inspection a first-class output, not a side effect;
- always preserve the distinction between: full geometry parameters, derived descriptors, and final candidate rules.
