# Spatial 4-Bar Explorer — Historical V05 to V09 Program Plan

> **Status: deferred and remapped.** This file no longer defines the active V05–V09 sequence. The active plan is [`KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md`](KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md). The work below is retained as the downstream V10–V14 program after the decomposition-validation gate.

| Historical label | Active downstream label |
|---|---|
| V05 all-family winding atlas | V10 validated-family winding atlas |
| V06 descriptor trend mining | V11 descriptor discovery |
| V07 candidate spatial Grashof-like rules | V12 candidate-rule testing |
| V08 fast crank evaluator | V13 conservative fast evaluator |
| V09 broad 6R reconstruction | V14 broad architecture/workspace validation |

Do not implement the historical labels as active V05–V09 work. Standalone spatial-four-bar results remain `mechanism_explorer_only` until connected to a certified source-chain decomposition.

---

**Historical status:** planned continuation after V04C
**Historical purpose:** carry the spatial-four-bar work from verified winding behavior through family-wide atlases, interpretable rule discovery, fast evaluation, and finally a direct test against aligned-terminal 6R dexterous-workspace truth.

## Historical program thesis

The retained downstream sequence is:

```text
V10  Do all certified spatial four-bar families admit useful winding/crank atlases?
  -> V11  Which physical descriptors correlate with those classifications?
  -> V12  Can those correlations become family-specific Grashof-like rules?
  -> V13  Can crank capability be evaluated quickly and conservatively?
  -> V14  Does certified virtual-mechanism capability predict broad robot orientation/dexterity truth?
```

V10 begins only after V09 of the active kinematic-decomposition program establishes at least one accepted source-to-mechanism mapping, exact predicate definition, recombination law, and independent source-chain validation.

## Prerequisites

Before V10 research evidence is generated:

- complete the active V05–V09 kinematic-decomposition program;
- retain the full fixed-position parent before introducing one-dimensional slices;
- define every one-dimensional child through an explicit task or architecture constraint;
- require a passing decomposition certificate;
- verify parent-child tangent, task-map, component, and branch equivalence;
- keep arbitrary V04B/V04C `phi` sweeps labeled diagnostic unless proved to parameterize legitimate task-derived fibers;
- retain budget-limited, singular, open, and unresolved outcomes separately.

## Cross-sprint data contract

Each downstream atlas observation should preserve:

```text
source_chain_id
fixed_position_problem_id
source_component_id
coverage_target
decomposition_certificate_id
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

Never discard source geometry or decomposition provenance after reducing a mechanism to descriptors.

## Evidence levels

Keep these levels explicit:

1. source-chain numerical result;
2. exact virtual-closure result;
3. decomposition-certificate result;
4. numerical mechanism result;
5. empirical trend;
6. candidate rule;
7. analytical result;
8. robot-workspace result.

Do not promote one level to another by wording alone.

## Downstream gates

### Gate A — after V10: family viability
Proceed to descriptor mining only when certified family corpora show reproducible, interpretable outcomes and the unresolved fraction is understood.

### Gate B — after V12: analytical-rule viability
If compact family-specific rules survive held-out and near-boundary validation, pursue analytical derivation. Otherwise route the family to the V13 numerical-atlas path.

### Gate C — V14: broad robotics relevance
Do not claim broad workspace characterization until certified mechanism predictions agree with independent source-chain orientation truth across the declared architecture domain.

## Required outputs across V10–V14

- JSON / machine-readable outputs;
- PNG plots and representative 3D mechanism views;
- GIFs where motion interpretation matters;
- offline HTML sprint readouts;
- explicit successes, failures, and counterexamples;
- tests separating numerical validity, decomposition validity, and research interpretation.

## Historical detailed sprint files

The following files are retained as specifications but their headings are superseded by the mapping above:

- `SPRINT_V05_ALL_FAMILY_WINDING_ATLAS.md` -> V10;
- `SPRINT_V06_DESCRIPTOR_TREND_MINING.md` -> V11;
- `SPRINT_V07_CANDIDATE_SPATIAL_GRASHOF_RULES.md` -> V12;
- `SPRINT_V08_FAST_CRANK_EVALUATOR.md` -> V13;
- `SPRINT_V09_6R_DEXTERITY_RECONSTRUCTION.md` -> V14.
