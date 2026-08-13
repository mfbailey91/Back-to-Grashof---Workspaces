# Project Reference Index

**Status:** Active index for theory, terminology, plans, and deferred research tracks
**Project:** Characterization of Manipulator Workspaces
**Last updated:** 2026-08-07

---

## 1. Foundational Theory

### [`PROJECT_CHARTER.md`](PROJECT_CHARTER.md)

Defines the project around fixed-position virtual mechanisms, orientation coverage, and architecture-dependent kinematic decomposition. The planar 3R result is the trusted reference case, not the complete theory.

### [`MATH_NOTES.md`](MATH_NOTES.md)

Contains the current mathematical contracts used by the software:

- planar 3R exact result;
- fixed-position fibers;
- virtual closure;
- orientation and pointing images;
- regular mobility counts;
- the dimensional ladder;
- terminal-roll quotient conditions;
- decomposition proof obligations.

### [`KINEMATIC_DECOMPOSITION_FIXED_POSITION_ORIENTATION_FRAMEWORK.md`](KINEMATIC_DECOMPOSITION_FIXED_POSITION_ORIENTATION_FRAMEWORK.md)

Primary full theoretical write-up. It preserves the distinction among:

- the fixed-position fiber;
- the orientation image;
- the coverage target;
- exact virtual closure;
- architecture-dependent decomposition;
- mechanism predicates;
- coverage reconstruction.

It also explains why the planar 3R case produces a four-bar, why a spatial 4R produces an orientation curve, why a spatial 5R is naturally suited to a pointing task, why a generic spatial 6R is the minimum nonredundant full-orientation case, and why an aligned terminal roll can sometimes be factored separately.

---

## 2. Active Program

### [`DECOMPOSITION_LADDER_L3_L7_PROGRAM.md`](DECOMPOSITION_LADDER_L3_L7_PROGRAM.md)

Optional L3–L7 interface scaffold subordinate to the active V05–V09 sequence. L4↔V05, L5↔V06, L6 is V07-first then V08, L7 deferred/BLOCKED. Letter families are a candidate corpus only.

**Program readout:** [`../results/decomposition_ladder/index.html`](../results/decomposition_ladder/index.html).

### [`U_JOINT_DRIVE_CONTRACT.md`](U_JOINT_DRIVE_CONTRACT.md)

Canonical one-DOF U-drive semantics: drive branch parameter `s`; `alpha(s)`/`beta(s)` are coupled outputs.

### [`KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md`](KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md)

Active sequential program:

```text
V05  spatial 4R fixed-position fiber and one-DOF decomposition baseline
V06  spatial 5R fixed-position parent and pointing image
V07  generic spatial 6R orientation reference
V08  aligned-roll quotient and task-derived four-bar fibers
V09  validated mechanism predicates and coverage reconstruction
```

**V05B MVP readout:** [`../results/kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html`](../results/kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html).
**V05C MVP readout:** [`../results/kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html`](../results/kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html).
**V05D MVP readout:** [`../results/kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html`](../results/kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html).
**V05E MVP readout:** [`../results/kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html`](../results/kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html).
Do not confuse with explorer `results/spatial4bar_explorer/v05a/` (deferred-V10 pointing-slice prep; `mechanism_explorer_only`).
### [`ROADMAP.md`](ROADMAP.md)

Repository-level phase order, program gates, and downstream V10–V14 mapping.

### [`DECISIONS.md`](DECISIONS.md)

Architecture decisions governing source-chain truth, decomposition certificates, terminology, evidence promotion, and numerical versus analytical predicates.

---

## 3. Supporting Contracts and Diagnostics

### [`SPATIAL_POINTING_SLICE_CONTRACT.md`](SPATIAL_POINTING_SLICE_CONTRACT.md)

Supporting V06/V08 contract for constructing one-dimensional pointing level sets from the complete two-dimensional pointing parent. It is not the premise for V05 spatial 4R work.

### [`AUDIT_TOOL_AXIS_AND_PHI.md`](AUDIT_TOOL_AXIS_AND_PHI.md)

Records why arbitrary virtual-`U`/`phi` sweeps are diagnostic unless connected to a task- or architecture-derived reduction.

### [`SPRINT_03_SPATIAL_4BAR_EXPLORER.md`](SPRINT_03_SPATIAL_4BAR_EXPLORER.md)

Documents the standalone spatial-four-bar mechanism laboratory through V04C. Its geometry, continuation, winding, plotting, and HTML infrastructure remain reusable. Standalone mechanism results are not automatically manipulator-workspace evidence.

### [`WORKSHOP_2026-08-04_SPHERICAL_FIBER_HYPOTHESIS.md`](WORKSHOP_2026-08-04_SPHERICAL_FIBER_HYPOTHESIS.md)

Historical workshop record for the spherical-fiber hypothesis. Interpret it through the current fixed-position/decomposition framework and the evidence levels in the active program.

---

## 4. Deferred Downstream Program

### [`SPATIAL_4BAR_V05_V09_PROGRAM.md`](SPATIAL_4BAR_V05_V09_PROGRAM.md)

Historical spatial-four-bar-first plan. It is no longer the active V05–V09 sequence. Its content is retained and remapped:

```text
old V05 -> V10 validated-family winding atlas
old V06 -> V11 descriptor discovery
old V07 -> V12 candidate Grashof-like rules
old V08 -> V13 fast conservative evaluator
old V09 -> V14 broad workspace validation
```

The detailed historical files remain useful as deferred specifications, but their former sprint numbers are superseded:

- `SPRINT_V05_ALL_FAMILY_WINDING_ATLAS.md`;
- `SPRINT_V06_DESCRIPTOR_TREND_MINING.md`;
- `SPRINT_V07_CANDIDATE_SPATIAL_GRASHOF_RULES.md`;
- `SPRINT_V08_FAST_CRANK_EVALUATOR.md`;
- `SPRINT_V09_6R_DEXTERITY_RECONSTRUCTION.md`.

---

## 5. Evidence and Provenance Rule

The project preserves this chain:

```text
source open chain
  -> fixed-position problem
  -> exact virtual closure
  -> source fiber/parent and orientation image
  -> decomposition certificate
  -> mechanism predicate
  -> compatibility/recombination law
  -> independent coverage validation
  -> workspace classification
```

A result may omit decomposition when the source mechanism is analyzed directly. It may not skip from a standalone mechanism family to a robot-workspace claim.

---

## 6. Terminology Rule

Use the following names consistently:

- **spatial 4R serial manipulator** for an open four-revolute-joint chain;
- **spatial four-bar linkage** for a closed one-degree-of-freedom linkage family;
- **joint-kind sequence** for solver topology and **joint-role sequence** for physical/task semantics;
- **`S_v`/`U_v`** for virtual task closures and **`S_phys`/`U_phys`** for exact physical-axis aggregates;
- **fixed-position fiber** for the complete position level set;
- **fiber component** for one connected component;
- **pointing level-set fiber** for a one-dimensional child of a higher-dimensional pointing parent;
- **dexterous workspace** only for full orientation coverage;
- **pointing-complete workspace** for full `S^2` coverage when roll is excluded by task definition.

## V05 audit correction references

<!-- V05_AUDIT_CORRECTION_2026_08_08 -->

- [`V05_AUDIT_CORRECTIONS.md`](V05_AUDIT_CORRECTIONS.md) — corrected source corpus, pseudo-arclength continuation, curve classification, certificate split, and boundary suite.
- [`JACOBIAN_AND_DERIVATIVE_POLICY.md`](JACOBIAN_AND_DERIVATIVE_POLICY.md) — why derivative information is used and which derivative-free alternatives remain valid.
