> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# Sprint V06 — Descriptor Trend Mining

> **Superseded sprint number:** retained as deferred **V11 descriptor
> discovery**. Active V06 constructs the complete spatial 5R fixed-position
> parent and pointing image before one-dimensional factor analysis.

**Historical status:** planned after V05 Gate A
**Purpose:** identify interpretable physical geometry quantities associated with the winding/crank outcomes in the all-family atlas.

## Research question

Within each viable spatial four-bar family, which coordinate-invariant or explicitly parameterized geometry descriptors organize the observed crank/rocker/change-point boundaries?

## Inputs

- accepted V05 all-family atlas;
- full physical mechanism geometry for every observation;
- V04C canonical virtual-`U` parameters, including `phi` if it remains physically relevant.

## Descriptor policy

Separate descriptors into:

1. **physical/invariant descriptors** — geometry quantities independent of arbitrary solver charts;
2. **explicit virtual-mechanism parameters** — e.g. retained `phi`;
3. **solver diagnostics** — never use these as causal geometry features without separate justification.

S-joint x/y/z solver-chart coordinates are not invariant descriptors.

## Phase V06A — interpretable transforms

Evaluate, family by family:

- normalized adjacent and diagonal center distances;
- primary-axis twist angles where physically meaningful;
- shortest axis-axis distances;
- signed axial offsets;
- axis-to-opposite-center distances;
- normalized tetrahedral volume / coplanarity / chirality;
- symmetry and special-geometry flags;
- canonical `phi`;
- dimensionless ratios and sums/differences;
- simple trigonometric transforms such as `sin(alpha)` / `cos(alpha)`.

Retain the raw geometry so new descriptors can be added later.

## Phase V06B — visualization first

Produce:

- univariate class plots;
- bivariate crank/rocker scatter maps;
- class-conditioned histograms;
- `phi` interaction plots;
- singularity-margin overlays near apparent boundaries;
- gallery links from suspicious points back to their 3D mechanisms.

Counterexamples should be visible, not averaged away.

## Phase V06C — lightweight interpretable models

Use discovery tools only:

- shallow decision trees;
- sparse logistic regression;
- simple threshold searches;
- rule lists;
- optionally low-complexity GAMs.

Create a frozen discovery/holdout split before model selection. Do not use neural networks or symbolic regression as the first-line method.

## Deliverables

- descriptor matrix with provenance;
- discovery / holdout split manifest;
- per-family uni- and bivariate plots;
- dimensionless-ratio report;
- shallow interpretable baseline models;
- interesting-geometry / counterexample gallery;
- `sprint_06_descriptor_trend_mining.html`.

## Acceptance

V06 passes when:

1. all tested features are labeled physical, virtual, or solver-derived;
2. the discovery and holdout sets are fixed before candidate-rule selection;
3. each viable family has interpretable descriptor plots;
4. at least some families show repeatable structure **or** the sprint explicitly concludes that the present descriptor basis is insufficient;
5. counterexamples to the strongest simple trends are identified and visualized;
6. no empirical trend is called a Grashof rule yet.

## Output to V07

For each viable family nominate only a small number of candidate descriptor combinations worth turning into explicit hypotheses.
