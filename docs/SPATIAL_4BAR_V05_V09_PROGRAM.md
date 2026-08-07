# Spatial 4-Bar Explorer — V05 to V09 Program Plan

**Status:** planned continuation after V04C  
**Purpose:** carry the spatial-four-bar work from verified winding behavior through family-wide atlases, interpretable rule discovery, fast evaluation, and finally a direct test against aligned-terminal 6R dexterous-workspace truth.

## Program thesis

The remaining work is deliberately staged:

```text
V05  Do all six spatial four-bar families admit useful winding/crank atlases?
  -> V06  Which physical descriptors correlate with those classifications?
  -> V07  Can those correlations become family-specific Grashof-like rules?
  -> V08  Can crank capability be evaluated quickly and conservatively?
  -> V09  Does virtual crank capability actually predict 6R orientation/dexterity?
```

V05 first reconnects the standalone four-bar laboratory to the task-derived `S_v -> U_v` fiber construction. V05–V08 then solve the **spatial four-bar classification problem on validated pointing fibers**. V09 tests whether solving that problem is useful for the **robot-workspace problem**.

## Prerequisite

V04C closes useful numerical / coordinate diagnostics, but it is **not sufficient by itself** to define the physical pointing-fiber contract. Before V05 research evidence is generated, implement [`SPATIAL_POINTING_SLICE_CONTRACT.md`](SPATIAL_POINTING_SLICE_CONTRACT.md):

- retain the two-DOF `S_v` pointing parent;
- define the one-DOF fiber through an explicit scalar pointing constraint;
- derive `U_v` / `R_a` / `R_b` from that task-derived slice;
- verify constrained-parent versus `U_v` child tangent / pointing / branch equivalence;
- keep V04B/V04C arbitrary `phi` sweeps labeled as diagnostic unless they are proved to parameterize legitimate pointing fibers;
- retain the policy for budget-limited open branches and the distinction between winding, angular coverage, and unresolved classification.

Any `ab` / `ba` or half-turn canonicalization accepted in V04C is a provisional solver-coordinate simplification, not a proof of physical fiber equivalence.

## Cross-sprint data contract

From V05 onward, one evaluated observation should preserve:

```text
family
geometry_id
full physical geometry / provenance
invariant physical descriptors
pointing-slice id / explicit constraint definition
slice parameter and task provenance
fiber-equivalence status / residuals
virtual-U axes and solver convention / canonicalization metadata
branch_id
branch_status
returned
w_alpha
w_beta
coverage_alpha
coverage_beta
minimum singularity margin
cycle length / solver diagnostics
classification confidence / unresolved reason
```

Never discard the full mechanism geometry after reducing it to descriptors. New descriptors must be derivable later without rerunning the kinematics whenever possible.

## Evidence levels

Keep these levels explicit in every sprint readout:

1. **numerical mechanism result** — directly produced by closure/continuation;
2. **empirical trend** — association observed in the sampled corpus;
3. **candidate rule** — explicit predictive hypothesis tested on held-out data;
4. **analytical result** — derived from mechanism equations;
5. **robot-workspace result** — validated against independent manipulator orientation truth.

Do not promote one level to the next by wording alone.

## Program gates

### Gate A — after V05: family viability
Proceed to descriptor mining only when the six-family corpus shows reproducible, interpretable outcome classes and the unresolved fraction is understood.

A family that is nearly always one class is a valid result; do not force artificial class balance.

### Gate B — after V07: analytical-rule viability
If compact family-specific rules survive held-out and near-boundary validation, pursue analytical derivation. If not, route to the V08 numerical-atlas path without treating that as project failure.

### Gate C — V09: robotics relevance
The decisive question is whether virtual-mechanism predictions agree with independently computed orientation capability of a 6R manipulator. Failure here means the spatial-four-bar work may still be interesting mechanism research, but it is not yet a dexterous-workspace characterization method.

## Required outputs across V05–V09

Every sprint should retain the explorer convention:

- JSON / machine-readable outputs;
- PNG plots and representative 3D mechanism views;
- GIFs where motion interpretation matters;
- offline HTML sprint readouts;
- explicit representative successes, failures, and counterexamples;
- tests that separate numerical validity from research interpretation.

## Planned sprint files

- `SPRINT_V05_ALL_FAMILY_WINDING_ATLAS.md`
- `SPRINT_V06_DESCRIPTOR_TREND_MINING.md`
- `SPRINT_V07_CANDIDATE_SPATIAL_GRASHOF_RULES.md`
- `SPRINT_V08_FAST_CRANK_EVALUATOR.md`
- `SPRINT_V09_6R_DEXTERITY_RECONSTRUCTION.md`
