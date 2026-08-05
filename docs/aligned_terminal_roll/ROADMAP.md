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

**Status:** `NEXT`

Implement the minimum full serial-chain kernel and verify:

- analytical versus finite-difference Jacobians;
- regular fixed-position dimension;
- terminal-roll null direction;
- full position-and-pointing rank;
- two-dimensional reduced pointing tangent space;
- singular configurations reported separately.

**Check-in 2:** Is the reduction a property of the full chain rather than only the terminal fixture?

---

## Phase 3 — Architecture comparison

**Status:** `PLANNED`

Compare:

1. generic aligned 6R;
2. literal compound-joint synthetic representation;
3. synthetic UR-like shoulder-elbow-wrist chain.

Evaluate mechanism order rather than relying only on mobility count.

**Check-in 3:** Which reduced topology accurately represents the physical chain under continued motion?

---

## Phase 4 — Fixed-position pointing manifold

**Status:** `BLOCKED` by Phase 2 and Phase 3

Implement predictor-corrector continuation for:

```text
p(q) = p0
q6 = 0
```

Produce a local two-parameter manifold and map it to `S2`.

**Check-in 4:** Does the parent remain two-dimensional and provide independent pointing motions away from singular sets?

---

## Phase 5 — Explicit one-dimensional fibers

**Status:** `BLOCKED` by Phase 4

Define one independent scalar constraint such as:

```text
n^T d(q) = c
```

Continue:

```text
p(q) = p0
q6 = 0
h(q) = c
```

**Check-in 5:** Is the fiber regular, nondegenerate, reproducible, and geometrically meaningful?

---

## Phase 6 — Exact spherical-four-bar tests

**Status:** `BLOCKED` by Phase 5

For each candidate fiber, test in order:

1. four-axis global concurrency;
2. fixed spherical arc dimensions;
3. inactive-coordinate locking;
4. local tangent equivalence;
5. global continued-motion equivalence;
6. McCarthy-Soh classification.

**Check-in 6:** Accept or reject the spherical `RRRR` hypothesis independently of the terminal-roll reduction.

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
