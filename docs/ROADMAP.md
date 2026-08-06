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

## Phase 5 — Spatial 4-bar explorer (new active track)

- start from the aligned-terminal 6R position-and-pointing reduction;
- enumerate the six ordered one-DOF spatial four-bar families;
- decompose the tool `U` into two perpendicular revolute coordinates;
- publish visualizations, graphs, JSON exports, and HTML readouts per sprint;
- sample broad geometry families and record descriptor atlases;
- compute winding-based crank and rocker classifications numerically first.

## Phase 6 — Spatial Grashof-like discovery and later analytical closure

- identify which geometry descriptors correlate with crank classifications;
- extract representative and counterexample mechanisms for visual inspection;
- propose family-specific candidate crank inequalities or thresholds;
- validate or refute those rules near observed class boundaries;
- only then attempt analytical derivation.

## Phase 7 — Spatial 6R dexterity reconstruction

- lift one-DOF family results back to the two-DOF pointing parents;
- map fiber-level crank fields over the pointing-space slice parameter;
- integrate terminal-roll capability;
- address joint limits, branch connectivity, and singularity structure.
