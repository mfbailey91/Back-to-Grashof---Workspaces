# Project Reference Index

**Status:** REFERENCE evidence / provenance index (not the entry page)
**Project:** Characterization of Manipulator Workspaces
**Last updated:** 2026-08-17
**Start here instead:** [`../README.md`](../README.md) → thesis → current status → ladder → roadmap

---

## 1. Foundational Theory

### [`../PROJECT_THESIS.md`](../PROJECT_THESIS.md)

Canonical scientific thesis and claim boundaries (replaces the archived charter).

### [`../CURRENT_STATUS.md`](../CURRENT_STATUS.md)

Sole live status ledger for L3–L7.

### [`../theory/MATH_NOTES.md`](../theory/MATH_NOTES.md)

Contains the current mathematical contracts used by the software:

- planar 3R exact result;
- fixed-position fibers;
- virtual closure;
- orientation and pointing images;
- regular mobility counts;
- the dimensional ladder;
- terminal-roll quotient conditions;
- decomposition proof obligations.

### [`../theory/FIXED_POSITION_KINEMATIC_DECOMPOSITION.md`](../theory/FIXED_POSITION_KINEMATIC_DECOMPOSITION.md)

Primary full theoretical write-up. It preserves the distinction among:

- the fixed-position fiber;
- the orientation image;
- the coverage target;
- exact virtual closure;
- architecture-dependent decomposition;
- mechanism predicates;
- coverage reconstruction.

It also explains why the planar 3R case produces a four-bar, why a spatial 4R produces an orientation curve, why a spatial 5R is naturally suited to a pointing task, why a generic spatial 6R is the minimum nonredundant full-orientation case, and why an aligned terminal roll can sometimes be factored separately.

### [`../theory/MECHANISM_BEHAVIOR_AND_STITCHING.md`](../theory/MECHANISM_BEHAVIOR_AND_STITCHING.md)

Behavior certificates and coverage-stitching gates beyond Grashof shorthand.

---

## 2. Active Program

### Project printout (so far)

**Root index:** [`../../results/index.html`](../../results/index.html) — project status hubs and evidence readouts.

### [`../theory/DECOMPOSITION_LADDER.md`](../theory/DECOMPOSITION_LADDER.md)

**CANONICAL** L3–L7 active architecture. Live implementation status is in [`../CURRENT_STATUS.md`](../CURRENT_STATUS.md); future gates in [`../ROADMAP.md`](../ROADMAP.md). Letter families remain a candidate corpus only until certified.

**Program readout:** [`../../results/decomposition_ladder/index.html`](../../results/decomposition_ladder/index.html).

### [`../methods/U_JOINT_DRIVE_CONTRACT.md`](../methods/U_JOINT_DRIVE_CONTRACT.md)

Canonical one-DOF U-drive semantics: drive branch parameter `s`; `alpha(s)`/`beta(s)` are coupled outputs.

### [`../methods/NATURAL_LEAF_FAMILY_CONTRACT.md`](../methods/NATURAL_LEAF_FAMILY_CONTRACT.md)

Source-derived natural mechanism leaves versus task-sliced `h=c` controls (ADR-049).

### [`../methods/R3A_L5_FIVE_POINT_EXECUTION.md`](../methods/R3A_L5_FIVE_POINT_EXECUTION.md)

Five-point L5 positive-control execution program. Hub: [`../../results/l5_reconstruction/r3a/index.html`](../../results/l5_reconstruction/r3a/index.html).

### [`../methods/R3A_HARDENING_EXECUTION.md`](../methods/R3A_HARDENING_EXECUTION.md)

R3A-H0–H6 evidence-hardening contract: evaluative family audits, independent direct reference, and stage artifact authority (ADR-050). Guide: [`CURSOR_GUIDE_R3A_HARDENING.md`](../methods/CURSOR_GUIDE_R3A_HARDENING.md).

### [`../methods/R3A_H7_H10_FOLLOWUP_EXECUTION.md`](../methods/R3A_H7_H10_FOLLOWUP_EXECUTION.md)

R3A-H7–H10 follow-up: metric applicability, two-resolution refinement, leaf-scoped admission, chart responsibility, and compact artifact closeout (ADR-051 draft). Guide: [`CURSOR_GUIDE_R3A_H7_H10_FOLLOWUP.md`](../methods/CURSOR_GUIDE_R3A_H7_H10_FOLLOWUP.md).

### [`../methods/R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md`](../methods/R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md)

R3A-H11 acceptance-authority hardening: diagnostic vs full-closeout packages, overlap-band chart transitions, returned-set claim narrowing, and the strict gate before a frozen full rerun.

### Archived V05–V09 planning lineage

Historical sequential sprint labels (V05–V09) are preserved under [`../archive/programs/`](../archive/programs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md) and [`../archive/sprints/`](../archive/sprints/SPRINT_01.md). They are not the active roadmap.

```text
L4 / historical V05  spatial 4R fixed-position fiber and one-DOF baseline
L5 / historical V06  spatial 5R fixed-position parent and pointing image
L6 / historical V07–V08  generic 6R orientation reference then roll quotient
L5–L6 / historical V09  validated mechanism predicates and coverage reconstruction
```

**V05B MVP readout:** [`../../results/kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html`](../../results/kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html).
**V05C MVP readout:** [`../../results/kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html`](../../results/kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html).
**V05D MVP readout:** [`../../results/kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html`](../../results/kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html).
**V05E MVP readout:** [`../../results/kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html`](../../results/kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html).
**V06A0 software-validation readout:** [`../../results/kinematic_decomposition/v06a0/sprint_v06a0_implicit_manifold.html`](../../results/kinematic_decomposition/v06a0/sprint_v06a0_implicit_manifold.html) (unit-sphere manifold engine; not a 5R parent).
**V06A1 local-patch readout:** [`../../results/kinematic_decomposition/v06a1/sprint_v06a1_local_parent_patch.html`](../../results/kinematic_decomposition/v06a1/sprint_v06a1_local_parent_patch.html) (`LOCAL_PATCH`; not a complete parent).
**V06A2 parent-atlas readout:** [`../../results/kinematic_decomposition/v06a2/sprint_v06a2_parent_atlas.html`](../../results/kinematic_decomposition/v06a2/sprint_v06a2_parent_atlas.html) (stitched multi-chart atlas; not a closed component).
**V06C source-image readout:** [`../../results/kinematic_decomposition/v06c/sprint_v06c_source_images.html`](../../results/kinematic_decomposition/v06c/sprint_v06c_source_images.html) (orientation surface + pointing image; not S² completeness).
**V06B compound-parent readout:** [`../../results/kinematic_decomposition/v06b/sprint_v06b_compound_parent.html`](../../results/kinematic_decomposition/v06b/sprint_v06b_compound_parent.html) (SUUR LOCAL_ONLY; near control REJECTED).
**V06D1 level-set readout:** [`../../results/kinematic_decomposition/v06d1/sprint_v06d1_level_sets.html`](../../results/kinematic_decomposition/v06d1/sprint_v06d1_level_sets.html) (task-derived source fibers; not reconstruction).
**V06D2 virtual-U readout:** [`../../results/kinematic_decomposition/v06d2/sprint_v06d2_virtual_u_child.html`](../../results/kinematic_decomposition/v06d2/sprint_v06d2_virtual_u_child.html) (one UUUR child; not reconstruction).
**V06E reconstruction readout:** [`../../results/kinematic_decomposition/v06e/sprint_v06e_reconstruction.html`](../../results/kinematic_decomposition/v06e/sprint_v06e_reconstruction.html) (source-fiber paint vs V06C grid; no accepted children; V06 not passed).
**V06 H0–H2 hardening contract:** [`../archive/audits/V06_HARDENING_PATCH.md`](../archive/audits/V06_HARDENING_PATCH.md) and **ADR-043** in [`DECISIONS.md`](DECISIONS.md) (conjunctive local child equivalence; unevaluable empty `COVERED` miss metric).
**V06H3 continuation engine:** [`../../src/grashof_workspace/spatial_experiments/branch_continuation.py`](../../src/grashof_workspace/spatial_experiments/branch_continuation.py) and **ADR-044** (shared 1D pseudo-arclength).
**V06H4 D1/D2 migration:** **ADR-045** (level-set and UUUR traces use the H3 corrector; equations unchanged).
**V06H5 atlas stitch:** **ADR-046** (overlap components, clustered unattached growth, stitched mesh, fiber dedup).
**V06H6 closeout:** **ADR-047** (UUUR rejected; campaign factorization unresolved; V07A held).
**ADR-048:** mechanism behavior and coverage stitching as the general framework.
Do not confuse with explorer `results/spatial4bar_explorer/v05a/` (deferred atlas work; `mechanism_explorer_only`).
### [`../ROADMAP.md`](../ROADMAP.md)

Future dependency gates only (R0–R7).

### [`DECISIONS.md`](DECISIONS.md)

Architecture decisions governing source-chain truth, decomposition certificates, terminology, evidence promotion, and numerical versus analytical predicates.

---

## 3. Supporting Contracts and Diagnostics

### [`../methods/SPATIAL_POINTING_SLICE_CONTRACT.md`](../methods/SPATIAL_POINTING_SLICE_CONTRACT.md)

Supporting L5/L6 contract for constructing one-dimensional pointing level sets from the complete two-dimensional pointing parent. It is not the premise for L4 spatial 4R work.

### [`../archive/audits/AUDIT_TOOL_AXIS_AND_PHI.md`](../archive/audits/AUDIT_TOOL_AXIS_AND_PHI.md)

Records why arbitrary virtual-`U`/`phi` sweeps are diagnostic unless connected to a task- or architecture-derived reduction.

### [`../archive/sprints/SPRINT_03_SPATIAL_4BAR_EXPLORER.md`](../archive/sprints/SPRINT_03_SPATIAL_4BAR_EXPLORER.md)

Documents the standalone spatial-four-bar mechanism laboratory through V04C. Its geometry, continuation, winding, plotting, and HTML infrastructure remain reusable. Standalone mechanism results are not automatically manipulator-workspace evidence.

### [`../archive/workshops/WORKSHOP_2026-08-04_SPHERICAL_FIBER_HYPOTHESIS.md`](../archive/workshops/WORKSHOP_2026-08-04_SPHERICAL_FIBER_HYPOTHESIS.md)

Historical workshop record for the spherical-fiber hypothesis. Interpret it through the current fixed-position/decomposition framework.

---

## 4. Deferred Downstream Program

### [`../archive/programs/SPATIAL_4BAR_V05_V09_PROGRAM.md`](../archive/programs/SPATIAL_4BAR_V05_V09_PROGRAM.md)

Historical spatial-four-bar-first plan. Retained as deferred atlas/rule work after reconstruction (roadmap R7). Remapped:

```text
old V05 -> V10 validated-family winding atlas
old V06 -> V11 descriptor discovery
old V07 -> V12 candidate Grashof-like rules
old V08 -> V13 fast conservative evaluator
old V09 -> V14 broad workspace validation
```

Historical sprint files live under [`../archive/sprints/`](../archive/sprints/SPRINT_01.md).

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

- [`../archive/audits/V05_AUDIT_CORRECTIONS.md`](../archive/audits/V05_AUDIT_CORRECTIONS.md) — corrected source corpus, pseudo-arclength continuation, curve classification, certificate split, and boundary suite.
- [`../methods/JACOBIAN_AND_DERIVATIVE_POLICY.md`](../methods/JACOBIAN_AND_DERIVATIVE_POLICY.md) — why derivative information is used and which derivative-free alternatives remain valid.
