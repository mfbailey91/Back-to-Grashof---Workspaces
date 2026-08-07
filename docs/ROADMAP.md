# Roadmap

## Phase 0 — Research kernel and project guardrails

- establish conventions and equations;
- create typed data models;
- add analytical and sampled tests;
- produce one reproducible figure.

## Phase 1 — Planar 3R workspace atlas

- sweep representative link-length ratios;
- classify empty, disk, annular, disconnected, and change-point cases;
- compare four-bar classification against exact terminal-link rotatability;
- generate a figure set and machine-readable result table;
- document all equality and degeneracy cases.

## Phase 2 — Joint limits and broken symmetry

- add finite limits for \(q_1,q_2,q_3\);
- distinguish global base-rotation symmetry from limited angular sectors;
- compute exact results where possible and certified numerical bounds otherwise;
- compare against the unrestricted Grashof baseline.

## Phase 3 — Planar capability fields

- replace binary full-orientation membership with orientation coverage;
- define geometry-only capability measures;
- identify singularity and branch-connectivity descriptors;
- decompose simple planar tasks into required position-orientation sets;
- compare against workspace-decomposition approaches in the literature.

## Phase 4 — Automated structural reduction

- parse a simple kinematic description;
- detect one-parameter task-space symmetries;
- detect residual planar chains;
- construct candidate equivalent loops;
- report which reductions are proven, plausible, or invalid.

## Phase 5 — Spatial 4-bar explorer and family-wide winding atlas

- start from the aligned-terminal 6R position-and-pointing reduction;
- enumerate the six ordered one-DOF spatial four-bar families;
- decompose the tool `U` into two perpendicular revolute coordinates;
- validate physical geometry, closure, continuation, winding, and virtual-`U` conventions;
- complete V04C virtual-`U` canonicalization;
- **V05:** build a true returned-cycle winding / coverage atlas for all six ordered families;
- publish visualizations, graphs, JSON exports, GIFs, and HTML readouts per sprint.

## Phase 6 — Spatial descriptor discovery and candidate Grashof-like rules

- **V06:** identify which invariant physical descriptors and retained virtual parameters correlate with crank classifications;
- preserve discovery / holdout separation and explicit counterexample galleries;
- **V07:** nominate family-specific, dimensionless candidate crank inequalities or low-complexity rules;
- validate rules on held-out, fresh, and near-boundary geometries;
- only then escalate the strongest candidates toward analytical derivation.

## Phase 7 — Fast crank evaluation

- **V08:** provide a common fast-evaluator interface across families;
- use direct candidate rules where justified and a sparse adaptive numerical atlas elsewhere;
- retain exact continuation as a fallback for low-confidence / OOD queries;
- benchmark speed, held-out agreement, boundary behavior, and rejection rate.

## Phase 8 — Spatial 6R dexterity reconstruction and validation

- **V09:** return to a synthetic aligned-terminal 6R manipulator;
- deterministically extract virtual spatial four-bars at Cartesian points;
- map fiber-level winding / coverage fields over the retained pointing-slice parameter;
- compare predictions against an independent numerical orientation-capability reference;
- reconstruct dexterous / non-dexterous / unresolved workspace regions;
- measure both classification error and computational benefit.

## Spatial-track program gates

- **Gate A after V05:** verify that all six families have interpretable true winding outcomes before descriptor mining.
- **Gate B after V07:** choose analytical-rule or numerical-atlas evaluation paths family by family.
- **Gate C in V09:** require independent robot-orientation validation before claiming dexterous-workspace characterization.

See `docs/SPATIAL_4BAR_V05_V09_PROGRAM.md` for the detailed continuation plan.
