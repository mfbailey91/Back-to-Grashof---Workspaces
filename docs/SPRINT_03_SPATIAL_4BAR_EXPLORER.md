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

## Sprint V03 — closure solver for one-DOF families

### Goal
Replace mock branch outputs with actual loop-closure solving and continuation.

### Deliverables
- family-specific closure equations or a general transform-based closure formulation;
- local solver for valid seed assemblies;
- continuation driver for connected one-DOF branches;
- singularity detection hooks.

### Acceptance
- at least one family runs end-to-end with a closed or well-characterized branch;
- branch trajectories are exportable.

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
