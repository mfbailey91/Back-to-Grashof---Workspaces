# Sprint V05 — All-Family Winding Atlas

> **Superseded sprint number:** retained as the deferred **V10 validated-family
> winding atlas**. Active V05 is the spatial 4R fixed-position source-fiber
> sprint in `KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md`.

**Historical status:** planned after V04C; explorer V05A MVP (SUUR→UUUR) recorded below
**Purpose:** generalize the verified winding workflow to all six ordered families **only after** each one-DOF `UXXX` mechanism is derived as a validated pointing fiber of its two-DOF virtual-`S_v` parent.

## Research question

For the ordered families

```text
UUUR, UURU, URUU,
USRR, URSR, URRS,
```

what returned-cycle winding, angular-coverage, singularity, and unresolved-branch behavior occurs over a modest corpus of **task-derived pointing fibers**, and which ordered `UXXX` topologies arise from those validated fibers?

## Inputs

- V02B physical geometry representation only;
- V03 seven-coordinate closure and continuation kernel;
- V04 returned-cycle winding classifier;
- V04B numerical robustness checks;
- V04C solver-coordinate diagnostics and unresolved/open-branch policy;
- [`SPATIAL_POINTING_SLICE_CONTRACT.md`](SPATIAL_POINTING_SLICE_CONTRACT.md).

V01/V02 mock classifications remain excluded from research evidence.

## Phase V05A — parent-first pointing-fiber construction

Do not begin V05 evidence generation from an arbitrary standalone `UXXX`. Begin from the two-DOF pointing parent with a virtual spherical closure.

For each candidate parent / slice:

1. construct the regular two-DOF `S_v` pointing parent (`SUUR` / `SSRR` representation where applicable);
2. define an explicit scalar pointing constraint `h(d)=c`;
3. continue or otherwise verify that the constrained parent is a regular one-DOF fiber;
4. derive the virtual universal-joint axes `R_a`, `R_b` associated with that slice;
5. construct the corresponding ordered `UXXX` child mechanism;
6. verify tangent, pointing-curve, and branch equivalence between the constrained `S_v` parent and the `U_v` child;
7. record `slice_provenance`, the constraint definition, and equivalence residuals.

Only a child with `fiber_equivalence_status = PASS` is admitted to the dexterity-derived V05 atlas. Existing V02B/V03/V04 standalone `UXXX` mechanisms remain valuable regression / mechanism-explorer fixtures.

### Historical explorer V05A status (2026-08-07)

Under the old spatial-four-bar-first numbering this was “V05A”; after the kinematic-decomposition restructure it is preparatory / deferred-**V10** explorer evidence, not the active source-chain V05.

- Restored minimal ATR fiber kernel under `src/grashof_workspace/spatial_experiments/` from `spherical_framework`.
- Bridge: `spatial4bar_explorer/pointing_slice.py` + runner `spatial4bar_explorer/v05a.py`.
- Worked MVP: intersecting-pairs **SUUR → UUUR** with explicit `h(d)=n·d=c`, virtual-`U` chart `(R_a,R_b,d)`, and fiber-equivalence **PASS**.
- Readout: [`results/spatial4bar_explorer/v05a/sprint_05a_pointing_slice_fibers.html`](../results/spatial4bar_explorer/v05a/sprint_05a_pointing_slice_fibers.html).
- Deferred: SSRR-line parents; family winding atlas (now V10); promoting diagnostic `phi` to a fiber parameter.
- Note: compound UA/UB frames are orthonormalized seed charts; exact free-SUUR identity beyond the seed remains **unverified**. PASS uses `S_v→U_v` pointing-lift tangent agreement; V03 child nullspace match is diagnostic-only.
- Standalone / explorer rows remain `mechanism_explorer_only` until certified against the active V05–V09 source-chain program.

## Phase V05B — family-wide winding generalization

For each validated child family:

1. verify reference closure, rank 6, and nullity 1;
2. continue each one-DOF branch to return, change point, invalid state, or explicit budget exhaustion;
3. compute `W = (w_alpha, w_beta)` when defined;
4. compute angular coverage and minimum singularity margin;
5. preserve solver diagnostics and unresolved reason.

The mechanism is solved once per validated `(parent, slice, child_geometry, branch)`; `tool_a` and `tool_b` remain two classifications read from the same returned branch.

## Phase V05C — initial corpus

Start modestly:

- target **20–50 physical geometries per family**;
- include the canonical mechanism, structured perturbations, and broader valid perturbations;
- sample explicit pointing constraints / slice definitions, not arbitrary `phi`, unless a proven mapping identifies `phi` with a legitimate fiber parameter;
- do not target artificial class balance.

If one family is computationally problematic, retain it with an explicit unresolved status rather than quietly dropping it.

## Phase V05D — family atlas readouts

For every family publish:

- winding pair versus the **task-derived slice parameter** (use `phi` only if V05A proves that correspondence);
- angular coverage versus the task-derived slice parameter;
- returned / crank / rocker / change-point / open / invalid counts;
- minimum singularity-margin distributions;
- representative 3D crank, rocker, and near-boundary mechanisms;
- representative unresolved/open cases;
- selected branch GIFs that satisfy the task-derived animation contract in [`SPATIAL_POINTING_SLICE_CONTRACT.md`](SPATIAL_POINTING_SLICE_CONTRACT.md): tool point and virtual `S_v` center; pointing direction `d`; derived `R_a` / `R_b` axes; pointing-slice definition / curve; `alpha(s)` and `beta(s)` readouts; and an explicit statement that continuation arclength `s` (not `tool_a`) is the branch parameter unless an input is prescribed;
- geometry cards with the most important physical descriptors.

## Dataset contract

One atlas row should include at least:

```text
family
geometry_id
slice_id
slice_definition
slice_parameter
slice_provenance
fiber_equivalence_status
fiber_equivalence_residuals
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
2. every research-evidence child four-bar is traceable to an explicit `S_v` parent and pointing-slice constraint and passes the fiber-equivalence contract;
3. winding is reported only for returned cycles;
4. unresolved/open/change-point cases remain separate from crank/rocker;
5. the corpus reveals the basic class distribution and computational difficulty of every family;
6. enough class diversity exists in at least some families to justify V06 trend mining;
7. arbitrary V04B/V04C `phi` variants are not pooled into the dexterity-derived corpus unless V05A proves that `phi` parameterizes legitimate pointing fibers;
8. any V04C coordinate symmetry/canonicalization used for storage is rechecked on more than the original `UUUR` example.

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
