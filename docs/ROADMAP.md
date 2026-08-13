# Roadmap

## Program thesis

The project proceeds from the exact fixed-position source mechanism to lower-dimensional mechanism predicates:

```text
open chain
  -> fixed-position fiber/parent
  -> exact virtual closure
  -> orientation/pointing image
  -> certified decomposition
  -> mechanism predicate
  -> compatibility/reconstruction
  -> independent workspace validation
```

Grashof-like rule discovery is downstream of the decomposition gate.

---

## Phase 0 — Research kernel and project guardrails

- establish coordinate, link-order, and task conventions;
- create typed immutable data models;
- separate analytical definitions from sampled validation;
- preserve equality, degeneracy, component, and unresolved states;
- produce reproducible figures and machine-readable evidence.

## Phase 1 — Planar 3R trusted reference

- construct the equivalent planar four-bar after fixing position;
- distinguish assemblability, Grashof class, inversion, and exact terminal-link rotatability;
- recover the analytical dexterous workspace;
- validate the analytical boundary independently;
- preserve the planar result as the reference example explaining why a mechanism predicate can characterize orientation coverage.

## Parallel planar extensions

These remain valuable but do not block the active spatial ladder:

- finite joint limits and broken rotational symmetry;
- graded planar orientation-capability fields;
- singularity and branch-connectivity descriptors;
- task-based planar capability decomposition.

## Completed spatial mechanism laboratory — V00 to V04C

The standalone spatial-four-bar explorer established reusable infrastructure for:

- compound-joint geometry;
- closure and continuation;
- returned-cycle detection;
- winding and angular coverage;
- tool-coordinate sensitivity diagnostics;
- 3D figures, GIFs, JSON, and offline HTML reports.

Its standalone results remain `mechanism_explorer_only` until connected to a certified source-chain decomposition.

---

## Active Phase — Kinematic decomposition ladder, V05 to V09

### V05 — Spatial 4R fixed-position fiber

- construct the exact \(4R+S_v\), \(M=1\) source mechanism;
- continue complete regular components where possible;
- map the orientation curve in \(SO(3)\);
- detect exact physical \(RR\rightarrow U\) axis aggregations;
- certify or reject one-degree-of-freedom spatial-four-bar reductions.

### V06 — Spatial 5R fixed-position parent

- construct the exact \(5R+S_v\), \(M=2\) parent;
- represent its two-dimensional orientation image and pointing projection;
- test exact `S_v U U R` / `S_v S R R` parent reductions where architecture permits;
- distinguish the full parent from task-derived one-dimensional pointing level sets;
- audit factorization rather than assume two independent one-DOF mechanisms.

### V07 — Generic spatial 6R orientation reference

- construct the exact \(6R+S_v\), \(M=3\) source mechanism;
- build a decomposition-free numerical reference in \(SO(3)\);
- preserve components, multiplicity, singularity, chart coverage, and uncertainty;
- freeze the reference before decomposition comparison.

### V08 — Aligned terminal-roll quotient

- verify the geometric and range conditions for factoring \(R_6\);
- certify the \(6R\rightarrow5R\) pointing quotient and reconstruction;
- compare pointing-plus-roll against direct \(SO(3)\) truth;
- construct task-derived one-dimensional pointing fibers;
- certify any resulting `UUUR`/`USRR` family reductions.

### V09 — Mechanism-predicate reconstruction

- use only certified decompositions;
- apply winding, coverage, rotatability, branch, or other defined predicates;
- state compatibility/recombination laws explicitly;
- compare reconstructed capability against V05/V06/V07/V08 source-chain truth;
- issue a go/no-go decision for broad atlas and Grashof-like rule discovery.

See `docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md` for the detailed active plan.

---

## Active program gates

### Gate K1 — V05 source-fiber gate

Do not infer a manipulator result from a standalone spatial four-bar unless a source-to-reduced decomposition certificate passes.

### Gate K2 — V06 parent gate

Do not describe a collection of one-dimensional traces as the complete two-dimensional pointing parent. Preserve parent charts, components, and slice provenance.

### Gate K3 — V07 independent-reference gate

Freeze a decomposition-free numerical orientation reference before testing reconstruction.

### Gate K4 — V08 quotient gate

Do not remove terminal roll from the problem unless position invariance, pointing invariance, orbit/reconstruction correspondence, component correspondence, and range conditions are verified.

### Gate K5 — V09 reconstruction gate

Do not begin broad family rule discovery until the mechanism predicate and recombination law reproduce independent source-chain capability within documented tolerances.

---

## Deferred downstream program — V10 to V14

The former V05–V09 spatial-four-bar-first program is retained after the decomposition gate:

### V10 — Validated-family winding atlas

- sample only mechanisms carrying certified manipulator/task provenance;
- preserve exact solver fallback and unresolved states.

### V11 — Descriptor discovery

- mine invariant geometry descriptors on the certified corpus;
- preserve discovery/holdout separation and counterexamples.

### V12 — Candidate Grashof-like rules

- formulate family-specific, falsifiable, low-complexity hypotheses;
- test fresh, held-out, and near-boundary cases;
- pursue analytical derivation only where evidence supports it.

### V13 — Conservative fast evaluator

- use analytical rules where justified and adaptive numerical atlases elsewhere;
- refuse out-of-domain cases and retain exact continuation fallback.

### V14 — Broad architecture/workspace validation

- evaluate additional synthetic and later real robot architectures;
- compare speed, error, unresolved rate, component failures, and computational benefit;
- only then promote the method as a general or architecture-qualified workspace characterization framework.

See `docs/SPATIAL_4BAR_V05_V09_PROGRAM.md` for the retained historical plan and its remapping.

---

## Optional scaffold — L3–L7 interface contracts

<!-- DECOMPOSITION_LADDER_L3_L7_2026_08_12 -->

`docs/DECOMPOSITION_LADDER_L3_L7_PROGRAM.md` and `src/grashof_workspace/decomposition_ladder/` provide optional shared interfaces. They do **not** replace the Active Phase V05–V09 above.

```text
L3  planar calibration retrofit (trusted exact map)
L4  maps to V05 (closed-mechanism gate currently HOLD / UNRESOLVED)
L5  maps to V06 (claims blocked until V05 lifts)
L6  V07-first independent SO(3) truth, then optional nested / V08 work
L7  deferred / BLOCKED until the V05 closed-mechanism gate lifts
```
