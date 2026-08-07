# Sprint V07 — Candidate Spatial Grashof-Like Rules

**Status:** planned after V06  
**Purpose:** convert the strongest V06 empirical structures into explicit, family-specific, falsifiable crank hypotheses and determine whether any deserve analytical follow-up.

## Research question

Can the numerical crank boundary for a spatial four-bar family be represented by a compact, mechanically interpretable condition

```text
g_F(x) > 0  -> candidate crank region
```

with useful held-out predictive power and understandable boundary behavior?

## Candidate-rule requirements

Prefer rules that are:

- dimensionless;
- invariant to global translation / rotation / scale where appropriate;
- explicit about retained virtual parameters such as `phi`;
- low complexity;
- mechanically interpretable;
- testable on fresh mechanisms.

Examples of form are allowed, but coefficients and structure must come from evidence rather than being assumed:

```text
g = c1*Lhat1 + c2*Lhat2 + c3*cos(alpha12) + c4*ahat13 - c5
```

Nonlinear but simple rules are acceptable.

## Phase V07A — nominate candidate rules

For each viable family:

1. choose a small set of V06-supported forms;
2. fit / calibrate only on the discovery set;
3. lock each candidate before holdout evaluation;
4. record the exact rule and domain of intended validity.

## Phase V07B — counterexample-first validation

Test on:

- V06 holdout data;
- fresh random valid geometries;
- targeted samples near the predicted boundary;
- symmetry / inversion checks;
- planar or spherical limiting cases when meaningful;
- perturbations around known crank and rocker mechanisms.

Publish false-crank and false-rocker examples as prominently as successes.

## Phase V07C — boundary mechanics

Near promising rule boundaries, compare:

- predicted rule margin `g_F(x)`;
- minimum closure-Jacobian singular value;
- branch return status;
- winding and angular coverage;
- visible mechanism behavior.

The goal is to determine whether the empirical boundary corresponds to a mechanically meaningful change point or another transition.

## Phase V07D — analytical escalation

Only for rules that survive validation:

- inspect closure equations and discriminants;
- identify whether the numerical boundary can be derived from closure / singularity conditions;
- document analytical progress separately from empirical accuracy.

## Deliverables

- explicit candidate-rule registry by family;
- held-out metrics and confusion tables;
- near-boundary campaign;
- counterexample gallery;
- candidate-margin versus singularity plots;
- analytical derivation notes for the strongest candidates;
- `sprint_07_candidate_spatial_grashof_rules.html`.

## Acceptance

A condition may be called a **candidate Grashof-like rule** only when:

1. its exact expression and domain are documented;
2. it is evaluated on held-out / fresh geometries;
3. near-boundary behavior is explicitly tested;
4. invariance assumptions are checked;
5. counterexamples are preserved;
6. analytical status is clearly labeled as empirical hypothesis, partial derivation, or proof.

## Gate B

At sprint closeout choose one of two routes, family by family:

```text
strong compact rule -> direct evaluator + analytical follow-up
messy / weak rule    -> V08 numerical atlas / surrogate evaluator
```

Both routes are acceptable outcomes.
