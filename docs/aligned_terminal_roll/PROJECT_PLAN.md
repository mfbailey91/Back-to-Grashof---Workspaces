# Project Plan — Aligned Terminal-Roll Reduction

**Project owner:** Michael Bailey
**Status:** Sprint 04C pre-approval audit / Check-in 4B and 04C drafts pending review
**Last updated:** 2026-08-04
**Planning horizon:** Reduction proof through exact-robot generalization
**Change policy:** Update at formal check-ins; record material reversals in `decisions/`

## 1. Project objective

Determine whether the aligned terminal revolute of a spatial serial manipulator can be rigorously quotiented from the fixed-position position-and-pointing problem, and determine whether restricted architectures admit exact one-dimensional spherical four-bar fibers that provide useful analytical orientation-capability classifications.

## 2. Primary research hypothesis

For an `nR` manipulator whose terminal revolute axis contains the task point and is aligned with the selected tool pointing direction, the terminal joint generates pure roll and is a symmetry of the position-and-pointing task.

At regular fixed-position configurations:

```text
M_position = n - 3
M_pointing = n - 4
```

For an aligned-terminal 6R manipulator, the reduced fixed-position pointing mechanism is therefore expected to be two-dimensional.

Any spherical-four-bar construction is a later, narrower hypothesis requiring an additional one-dimensional fiber constraint.

## 3. Product of the project

The project will produce:

1. a reusable spatial kinematic experiment kernel isolated from the trusted planar package;
2. deterministic positive and negative controls for terminal-roll symmetry;
3. a numerical and geometric characterization of the reduced fixed-position pointing manifold;
4. a controlled comparison among generic, literal compound-joint, UR-like, and exact UR geometries;
5. explicit one-dimensional fiber constructions, if they exist;
6. exact spherical-four-bar equivalence tests, if warranted;
7. a documented conclusion identifying supported claims, limitations, and obstructions.

## 4. Scope

### In scope

- rigid spatial revolute-joint kinematics;
- explicit axis-line geometry;
- task point and tool pointing direction;
- analytical and finite-difference Jacobians;
- fixed-position constraint manifolds;
- quotienting terminal roll;
- synthetic and UR-like 6R architectures;
- numerical continuation;
- exact spherical concurrency and fixed-arc tests;
- McCarthy-Soh classification only after exact `RRRR` validation;
- deterministic reports, tests, and check-in artifacts.

### Out of scope until later approval

- dynamics, torque, stiffness, or compliance;
- collision and link thickness;
- calibration uncertainty;
- controller design;
- motion planning;
- arbitrary URDF ingestion;
- broad robot-corpus comparisons;
- claims of global dexterity from local rank alone;
- general nonaligned terminal geometry;
- production changes to the planar analytical kernel.

## 5. Model ladder

| Level | Model | Purpose | Advancement condition |
|---|---|---|---|
| 0 | Terminal-roll fixture | Isolate pure-roll geometry | Positive control and two negative controls behave correctly |
| 1 | Generic synthetic aligned 6R | Establish full-chain differential reduction | Regular samples satisfy expected ranks and null directions |
| 2A | Literal compound-joint synthetic model | Test the proposed reduced topology | Tangent spaces and continued motion match the physical chain |
| 2B | Synthetic UR-like 6R | Test practical architecture ordering | Reduction survives recognizable shoulder-elbow-wrist geometry |
| 3 | Fixed-position pointing manifold | Establish a two-dimensional parent | Continuation produces a stable 2D patch with rank-two pointing map |
| 4 | Explicit one-dimensional fiber | Produce a legitimate constrained branch | Constraint is independent and branch is regular and reproducible |
| 5 | Candidate spherical `RRRR` | Test exact mechanism equivalence | Global concurrency, fixed arcs, locking, and motion equivalence pass |
| 6 | Exact UR geometry | Generalization test | Supported conclusions survive exact dimensions and frames |

## 6. Milestones and formal check-ins

### M0 — Project controls established

Deliver the project plan, roadmap, conventions, validation matrix, risk register, decision record, templates, and Sprint 01.

**Decision:** authorize Sprint 01.

### M1 — Terminal-roll symmetry established

Review the isolated terminal fixture and negative controls.

**Decision options:**

- continue to a full synthetic 6R chain;
- revise task-point or pointing-direction conventions;
- reject the aligned-terminal formulation.

### M2 — Two-dimensional reduction established

Review regular and singular samples of the generic synthetic 6R chain.

Required evidence includes:

```text
rank(J_p) = 3
dim ker(J_p) = 3
J_p e_6 = 0
J_d e_6 = 0
rank([J_p; J_d]) = 5
dim ker([J_p; J_d]) = 1
rank(J_d N_red) = 2
```

Here `N_red` spans the two-dimensional fixed-position tangent space after removing the terminal-roll direction.

**Decision:** authorize architecture-specific models or reformulate the reduction.

### M3 — Architecture representation selected

Compare the generic chain, literal compound-joint representation, and UR-like chain.

**Decision:** select the parent topology and exact architecture used for continuation.

### M4 — Two-dimensional pointing surface established

Review continuation quality, branch behavior, singular sets, and coverage of the local pointing patch.

**Decision:** authorize explicit fiber construction.

### M5 — Fiber legitimacy established

Review the scalar constraint, rank/nullity, branch closure, and coordinate independence.

**Decision:** authorize spherical-four-bar search.

### M6 — Spherical equivalence decision

Review global concurrency, fixed arcs, inactive-coordinate locking, and motion equivalence.

**Decision options:**

- proceed to McCarthy-Soh classification;
- retain only the dimensional reduction;
- retain fiber construction but reject spherical equivalence;
- identify the geometric obstruction and close the branch.

### M7 — Exact UR generalization

Review exact robot dimensions, frames, joint limits, and deviations from the synthetic model.

**Decision:** state the final architecture class and supported analytical claim.

## 7. Workstream structure

Every sprint contains four lanes:

| Lane | Responsibility |
|---|---|
| Research | Precise claim, derivation, and failure interpretation |
| Software | Minimal implementation needed for the current claim |
| Validation | Independent tests, controls, tolerances, and reproducibility |
| Documentation | Updated conventions, experiment record, check-in packet, and decisions |

No sprint is complete if one lane is absent.

## 8. Definition of Done

### Software Definition of Done

- implementation is isolated from trusted planar APIs;
- tests pass from a clean environment;
- analytical quantities have an independent numerical oracle where feasible;
- deterministic experiment command and seed are documented;
- outputs include machine-readable metrics;
- tolerances and units are explicit;
- linting and type checks pass;
- documentation is updated.

### Research Definition of Done

- the claim is stated with its geometric conditions;
- positive and negative controls exist;
- regular and singular cases are distinguished;
- numerical results are stable under refinement;
- local evidence is not presented as global evidence;
- failure interpretations are documented;
- the check-in records `supported`, `partially supported`, `inconclusive`, or `rejected`;
- the next stage is explicitly authorized or blocked.

## 9. Reporting standard

Each experiment writes:

```text
results/aligned_terminal_roll/<experiment_id>/
    manifest.json
    metrics.csv
    summary.md
    figures/
```

The manifest records:

- repository commit;
- experiment ID;
- model and parameters;
- initial configuration;
- units;
- solver and tolerance settings;
- random seed;
- software version;
- completion status.

Large generated outputs may remain untracked, but the manifest and summary for every decision-bearing experiment must be committed.

## 10. Current state

| Item | State |
|---|---|
| Workshop hypothesis | Drafted |
| PM scaffold | Ready |
| Geometric conventions | Frozen after Check-in 1 |
| Validation matrix | Provisional |
| Sprint 01 | Complete |
| Check-in 1 | Approved (`CONTINUE`) |
| Terminal fixture | Complete (ATR_EXP_001–005 PASS) |
| Sprint 02 | Complete (ATR_EXP_006–010 PASS) |
| Check-in 2 | Approved (`CONTINUE`) |
| Generic 6R kernel | Complete |
| Sprint 03 | Complete (ATR_EXP_011–015 PASS; C9 local claim withdrawn) |
| Check-in 3 | Approved (`CONTINUE WITH CHANGED SCOPE`) |
| UR-like model | Stage A verified; parallel continuation check |
| Compound / `SUUR` regrouping | Local coordinate-map defined on intersecting pairs; generic negative control passes |
| Sprint 04 | Implementation complete (ATR_EXP_016–020 PASS with validation limitations) |
| Check-in 4 | Approved (`CONTINUE WITH CHANGED SCOPE`) |
| Sprint 04B | Implementation complete (ATR_EXP_021–026 PASS; descriptions under 04C correction) |
| Sprint 04C | Pre-approval method audit before Check-in 4B |
| Check-in 4B | Draft pending human review |
| Check-in 04C | Draft pending human review |
| Fiber construction | Blocked by Check-in 4B and 04C |
| Spherical Grashof work | Blocked by M6 |

## 11. Immediate project decision

Complete Sprint 04C, then hold human review of Check-in 4B and Check-in 04C before selecting a one-dimensional fiber.

Do not start fiber, spherical-four-bar, McCarthy–Soh, or exact-UR work until both check-ins are approved.
