# Sprint V04C — Virtual-U Equivalence and Fiber Interpretation

**Status:** insertion sprint before V05 descriptor mining
**Purpose:** determine which virtual-tool `U` choices are genuine mechanism parameters and which are removable coordinate symmetries before building a large crank atlas.

## Why V04C exists

V04 established continuation-derived winding. V04B then showed two things:

1. the canonical `UUUR` winding result is numerically stable under step-size refinement and branch-direction reversal;
2. changing only the virtual tool-`U` orientation can change which tool coordinate is a crank, or whether either coordinate is a crank.

That means V05 must not fit a geometry-to-crank rule until we understand the virtual-`U` parameterization itself.

## Research questions

### A. Is `ab` versus `ba` a removable symmetry?

V04B suggests the following correspondence on the canonical `UUUR` mechanism:

```text
BA(phi)  <->  AB(phi + 90 deg)
```

with the same branch status, crank/rocker labels, and angular coverage, while the beta winding sign reverses under the coordinate convention.

V04C evaluates this correspondence explicitly. If it holds on the tested mechanism, `axis_order` is treated as a **provisionally removable coordinate symmetry**, not as an independent atlas dimension. Generalization to a larger geometry corpus remains a later validation requirement.

### B. Is the tool-U orientation half-turn periodic?

Because a revolute axis is an unoriented line geometrically, rotating both virtual `U` axes by 180 degrees should preserve the physical axis pair. V04C checks whether

```text
AB(phi)  <->  AB(phi + 180 deg)
```

preserves status, crank/rocker classes, winding magnitude, and angular coverage.

If supported, the canonical orientation domain can be reduced provisionally to

```text
phi in [0, 180 deg).
```

### C. Are the apparent open branches only budget limited?

V04B reported open branches near `phi = 120 deg` and `phi = 300 deg` at the default continuation budget. V04C reruns those orientations with increasing budgets.

Possible outcomes:

- **budget_limited_return:** a larger budget returns to the reference assembly;
- **persistent_open:** no return at the largest tested budget;
- **change_point / invalid:** continuation terminates for a different reason.

An exhausted numerical budget is not promoted to a topology claim.

### D. Where do the crank/rocker transitions occur?

Use the coarse V04B sweep only to identify intervals where the returned-cycle state changes. Densify those intervals instead of uniformly oversampling all `phi`.

For each dense probe record:

- branch status;
- `W = (w_alpha, w_beta)`;
- crank/rocker classes;
- angular coverage;
- minimum closure-Jacobian singular value encountered on the trace.

This produces a first transition map without yet fitting a Grashof-like rule.

## Canonicalization decision

V04C may emit a **provisional** canonicalization recommendation:

- use `ab` as the stored tool-`U` order if the shifted `ab`/`ba` equivalence passes;
- reduce `phi` modulo 180 degrees if half-turn periodicity passes;
- otherwise retain the failed dimension explicitly in V05.

This recommendation applies only to the tested `UUUR` geometry until repeated across a broader corpus.

## Deliverables

- standalone runner `spatial4bar_explorer.v04c`;
- `v04c_virtual_u_equivalence.json`;
- axis-order symmetry table and plot;
- half-turn periodicity table;
- extended-budget open-branch table;
- adaptive transition-state plot;
- transition singularity-margin plot;
- `sprint_04c_virtual_u_equivalence.html`;
- targeted tests for the comparison/canonicalization logic.

## Acceptance

V04C is complete when:

1. the V04B `ab` and `ba` sweeps are compared under an explicit 90-degree shift and winding-sign convention;
2. 180-degree periodicity is explicitly evaluated;
3. the `120 deg` and `300 deg` open cases are rerun at larger budgets without interpreting budget exhaustion as proof of an open topology;
4. transition intervals are densified and report branch state, winding, coverage, and minimum singular-value margin;
5. V05 receives an explicit parameter-retention/canonicalization decision rather than silently dropping virtual-`U` dimensions.
