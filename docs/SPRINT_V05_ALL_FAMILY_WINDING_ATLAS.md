# Sprint V05 — All-Family Winding Atlas

**Status:** planned after V04C  
**Purpose:** generalize the verified `UUUR` winding workflow to all six ordered one-DOF spatial four-bar families before any descriptor-to-classification rule mining.

## Research question

For the ordered families

```text
UUUR, UURU, URUU,
USRR, URSR, URRS,
```

what returned-cycle winding, angular-coverage, singularity, and unresolved-branch behavior occurs over a modest but diverse corpus of physical mechanisms and canonical virtual-tool-`U` orientations?

## Inputs

- V02B physical geometry representation only;
- V03 seven-coordinate closure and continuation kernel;
- V04 returned-cycle winding classifier;
- V04B numerical robustness checks;
- V04C canonical virtual-`U` convention and unresolved/open-branch policy.

V01/V02 mock classifications remain excluded from research evidence.

## Phase V05A — family-wide solver generalization

For each family:

1. build or perturb valid physical reference geometries;
2. verify reference closure, rank 6, and nullity 1;
3. apply the V04C canonical virtual-`U` representation;
4. continue each one-DOF branch to return, change point, invalid state, or explicit budget exhaustion;
5. compute `W = (w_alpha, w_beta)` when defined;
6. compute angular coverage and minimum singularity margin;
7. preserve solver diagnostics and unresolved reason.

The mechanism is solved once per `(geometry, phi, branch)`; `tool_a` and `tool_b` remain two classifications read from the same returned branch.

## Phase V05B — initial corpus

Start modestly:

- target **20–50 physical geometries per family**;
- include the canonical mechanism, structured perturbations, and broader valid perturbations;
- use the canonical `phi` domain from V04C;
- do not target artificial class balance.

If one family is computationally problematic, retain it with an explicit unresolved status rather than quietly dropping it.

## Phase V05C — family atlas readouts

For every family publish:

- winding pair versus `phi`;
- angular coverage versus `phi`;
- returned / crank / rocker / change-point / open / invalid counts;
- minimum singularity-margin distributions;
- representative 3D crank, rocker, and near-boundary mechanisms;
- representative unresolved/open cases;
- selected branch GIFs;
- geometry cards with the most important physical descriptors.

## Dataset contract

One atlas row should include at least:

```text
family
geometry_id
phi
virtual_u_convention
branch_status
returned
w_alpha
w_beta
class_alpha
class_beta
coverage_alpha
coverage_beta
minimum_singularity_margin
cycle_points
closure_quality
physical_descriptors
geometry_provenance
```

## Deliverables

- all-family winding runner;
- machine-readable all-family atlas;
- per-family JSON subsets;
- per-family winding / coverage / class-distribution plots;
- representative-mechanism gallery and selected GIFs;
- `sprint_05_all_family_winding_atlas.html`;
- tests covering every family through the true winding pipeline.

## Acceptance

V05 passes when:

1. all six families have true continuation-derived outcomes rather than mock classifications;
2. every family has at least a modest set of valid physical samples evaluated under the canonical V04C contract;
3. winding is reported only for returned cycles;
4. unresolved/open/change-point cases remain separate from crank/rocker;
5. the corpus reveals the basic class distribution and computational difficulty of every family;
6. enough class diversity exists in at least some families to justify V06 trend mining;
7. any V04C symmetry/canonicalization used in the corpus is rechecked on more than the original `UUUR` example.

## Non-goals

- no Grashof-like inequality claims;
- no learned classifier promoted as a rule;
- no 6R robot mapping yet;
- no forced binary answer for unresolved branches.

## Gate A

Before V06, publish a short family-viability decision:

```text
family -> suitable for trend mining / mostly uniform / numerically unresolved / needs geometry redesign
```
