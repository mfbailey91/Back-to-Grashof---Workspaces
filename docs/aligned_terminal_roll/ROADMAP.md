# Roadmap — Aligned Terminal-Roll Reduction

**Status notation:** `NEXT`, `PLANNED`, `BLOCKED`, `COMPLETE`, `STOPPED`

## Phase 0 — Project controls

**Status:** `COMPLETE` when this scaffold is merged.

Deliver:

- living project plan;
- geometric conventions;
- validation matrix;
- assumption and risk register;
- decision and experiment templates;
- Sprint 01 plan.

**Gate:** approve Sprint 01.

---

## Phase 1 — Terminal-roll fixture

**Status:** `COMPLETE`

Build an isolated transform fixture in which the terminal axis, task point, and tool direction are explicitly controlled.

Positive case:

```text
task point lies on R6
tool direction is parallel to R6
```

Negative controls:

```text
task point moved transversely off R6
tool direction rotated away from R6
```

**Check-in 1:** Approved 2026-08-04. `q6` preserves position and pointing only under the stated aligned-terminal conditions.

---

## Phase 2 — Generic synthetic aligned 6R

**Status:** `COMPLETE`

Implement the minimum full serial-chain kernel and verify:

- analytical versus finite-difference Jacobians;
- regular fixed-position dimension;
- terminal-roll null direction;
- full position-and-pointing rank;
- two-dimensional reduced pointing tangent space;
- singular configurations reported separately.

**Check-in 2:** Approved 2026-08-04. Stage A holds for the `GenericAligned6R` reference chain.

---

## Phase 3 — Architecture comparison

**Status:** `COMPLETE`

Compare:

1. generic aligned 6R;
2. literal compound-joint synthetic representation;
3. synthetic UR-like shoulder-elbow-wrist chain.

Evaluate local mechanism order rather than relying only on mobility count. Sprint 03 established Stage A survival on all three architectures. ATR_EXP_013–014 are non-discriminating for `SUUR` equivalence.

**Check-in 3:** Approved 2026-08-04 (`CONTINUE WITH CHANGED SCOPE`). `IntersectingPairsAligned6R` is the controlled continuation benchmark because it instantiates the workshop architecture. `SUUR` remains a proposed regrouping until explicit coordinate-map and closure tests exist.

---

## Phase 4 — Fixed-position pointing manifold

**Status:** `COMPLETE WITH VALIDATION LIMITATIONS`

Implement predictor-corrector continuation for:

```text
p(q) = p0
q6 = constant
```

Produce a local two-parameter solution neighborhood and map it to `S2`. Include discriminating architecture-specific compound-coordinate tests before reading the intersecting-pairs patch through those coordinates.

**Check-in 4:** Approved 2026-08-04 (`CONTINUE WITH CHANGED SCOPE`). Local regular neighborhoods exist on intersecting-pairs and UR-like models, but sequential branch tracking, corrected chart rank, duplicate avoidance, and refinement stability require Sprint 04B.

---

## Phase 4B — Sequential continuation and pointing-chart validation

**Status:** `COMPLETE`

Replace the seed-frozen tangent-plane projection with sequential predictor-corrector continuation using a locally recomputed and aligned tangent frame.

Validate:

- true forward/reverse continuation;
- numerical rank two of the corrected configuration chart;
- numerical rank two of the pointing chart;
- duplicate and collapse detection;
- grid and step-size refinement;
- loop and alternate-path sensitivity;
- persistence of architecture-specific intersecting pairs;
- UR-like continuation without imposed `SUUR` topology;
- complete clean-source result provenance.

**Check-in 4B:** Approved 2026-08-04 (Case A). Local sequential charts are validated on intersecting-pairs and UR-like models.

---

## Phase 4C — Implementation and method audit

**Status:** `COMPLETE`

Pre-approval amendment: document method rationale and correct ATR_EXP_024/026 claim language before Check-in 4B approval.

**Check-in 04C:** Approved 2026-08-04 (Pass). Method audit accepted; 024/026 claim corrections stand.

---

## Phase 5 — Explicit one-dimensional fibers

**Status:** `COMPLETE`

Locked scalar:

```text
h(q) = n · d(q) = c
n  = (0, 1, 0)
n' = (1, 0, 0)
```

Continue:

```text
p(q) = p0
q6 = q6*   (0.70 rad on the locked regular seeds; not q6=0)
h(q) = c
```

**Check-in 5:** Approved 2026-08-04 (`CONTINUE WITH CHANGED SCOPE`). Sprint 05 closed 2026-08-04. Primary and alternate explicit task-space fibers are regular, reversible, noncollapsed, and stable under independent-step refinement on both tested architectures.

The tested fibers are candidate slices. A canonical or architecture-derived fiber remains open.

---

## Phase 6 — Exact spherical-four-bar tests

**Status:** `NEXT` (032–035 complete, awaiting Check-in 6; 036 and McCarthy–Soh blocked)

For each candidate fiber, test in order:

1. duplicate-configuration scan;
2. branch-wide topology-derived `S−UA−UB−R5` concurrency to one fixed center `c*` (IP only);
3. fixed spherical arc dimensions on cycle `(S, UA, UB, R5)`;
4. body-fixed effective-axis invariance (simple coordinate locking is diagnostic only);
5. local tangent equivalence (deferred);
6. continued-motion equivalence (deferred);
7. McCarthy-Soh classification only after items 1–6 pass.

UR-like receives a duplicate scan plus an exploratory fixed physical four-subset diagnostic. That scan is not an exact `RRRR` claim.

Test both primary and alternate task-space fibers on the intersecting-pairs architecture and retain the UR-like architecture as a parallel comparison.

**Check-in 6:** Accept or reject each candidate spherical `RRRR` independently. Rejection of one selected slice does not establish nonexistence of all spherical fibers and does not invalidate the terminal-roll reduction.

---

## Phase 7 — Exact UR geometry

**Status:** `BLOCKED` by Phase 3

Introduce exact dimensions and frame conventions only after the synthetic UR-like architecture has been understood.

Evaluate:

- task point relative to `R6`;
- tool-direction alignment;
- axis intersection residuals;
- effects of offsets;
- joint limits;
- singular and disconnected branches.

**Check-in 7:** State the real-robot architecture conditions under which the reduction and any fiber conclusions remain valid.

---

## Phase 8 — Research synthesis

**Status:** `BLOCKED`

Produce:

- supported theorem-like conditions;
- rejected hypotheses and geometric obstructions;
- figures and experiment atlas;
- paper-ready methods and limitations;
- recommendation for 7R extension or general nonaligned case.
