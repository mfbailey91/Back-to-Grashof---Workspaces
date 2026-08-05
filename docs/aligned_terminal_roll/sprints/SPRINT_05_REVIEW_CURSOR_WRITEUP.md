# Sprint 05 Review — Explicit Pointing Fibers

**Status:** Closed 2026-08-04  
**Decision:** `CONTINUE WITH CHANGED SCOPE`  
**Check-in:** `CHECKIN_05_FIBER_LEGITIMACY.md`  
**Next stage:** Sprint 06 — Candidate spherical-equivalence testing

## 1. Review summary

Sprint 05 successfully produced regular, reproducible one-dimensional pointing fibers on both:

- `IntersectingPairsAligned6R`
- `URLikeAligned6R`

The supported result is local and specific to the tested seeds and scalar task directions.

## 2. Supported claim

For the scalar task map

```text
h(q) = n^T d(q)
```

with the primary direction

```text
n = (0, 1, 0)
```

the reduced constraint system has:

```text
rank = 4
nullity = 1
```

in the five active coordinates after terminal roll is fixed.

This establishes one local tangent direction and therefore a one-dimensional constrained branch at regular samples.

The same construction also succeeds for the alternate direction

```text
n' = (1, 0, 0)
```

on both tested architectures.

The supported claim is therefore:

> Explicit regular local pointing level-set fibers exist for both tested architectures and both tested scalar task directions.

## 3. What passed

### Primary fiber

For both architectures:

- the scalar constraint is independent of the position constraints;
- terminal roll does not change the scalar task;
- continuation produces a regular one-dimensional branch;
- all accepted samples preserve position and the scalar constraint;
- reverse continuation begins at the forward endpoint;
- the branch returns within the configured error gates;
- the pointing image changes meaningfully and does not collapse.

### Alternate fiber

The alternate world-axis direction also produces regular reversible fibers.

This demonstrates that the fiber construction is not dependent on one selected world direction.

It also demonstrates that the selected fiber is not unique.

### Coordinate-frozen control

The primary task-space fiber differs from the tested `q2`-frozen path.

This establishes only that the task-space fiber is distinct from that named coordinate slice.

It does not establish that the task-space fiber is canonical or architecture-derived.

### Step refinement

With continuation microstepping disabled, halving the fiber step reduces the reverse error by approximately the expected amount and preserves agreement at shared stations.

This provides credible numerical refinement evidence.

## 4. Interpretation limits

Sprint 05 does not establish:

- a unique fiber;
- a canonical fiber;
- an architecture-selected fiber;
- a spherical four-bar;
- global branch structure;
- global pointing coverage;
- exact UR applicability;
- McCarthy–Soh classification.

The primary and alternate fibers are explicit candidate slices of the two-dimensional pointing parent.

They are not yet privileged by the robot architecture.

## 5. Terminology correction

The project should retain the term **fiber**, with the precise meaning:

> The pointing level-set fiber `h^-1(c)` of a selected scalar task map on the fixed-position, fixed-terminal-roll parent.

For Sprint 05, the selected fibers are:

```text
h(q) = n^T d(q) = c
```

with:

```text
n  = (0, 1, 0)
n' = (1, 0, 0)
```

These should be described as:

- explicit task-space fibers;
- pointing level-set fibers;
- candidate fibers.

Avoid calling either fiber:

- canonical;
- natural;
- architecture-derived;
- the robot's unique fiber.

## 6. Project corrections

### Assumption A09

Replace:

```text
A nonarbitrary scalar fiber constraint exists.
```

with:

```text
Explicit regular task-space fiber constraints exist locally for the tested
primary and alternate slices. A canonical or architecture-derived fiber
remains open.
```

### Risk R06

Record:

```text
The tested task-space fibers are regular and distinct from the named q2-frozen
control. Canonical fiber selection remains unresolved.
```

### Pointing diagnostic language

Sprint 05 closeout renamed the local pointing derivative field from `local_rank_one` to `local_pointing_tangent_nonzero`.

Because the derivative is a nonzero `3 x 1` vector, that is the meaningful language. The rename does not change numerical gates or invalidate the result.

### Duplicate detection

Add an explicit duplicate-configuration scan before spherical testing:

```text
For sigma_i != sigma_j:

    ||wrap(q_i - q_j)|| > duplicate_tolerance
```

The stored Sprint 05 branches appear distinct, but the duplicate check should become a formal Sprint 06 metric.

## 7. Check-in decision

**Interpretation:** `SUPPORTED LOCALLY`

**Decision:** `CONTINUE WITH CHANGED SCOPE`

Authorize Sprint 06 to test the accepted primary and alternate fibers as candidate spherical mechanisms.

## 8. Sprint 06 test matrix

Test the following four cases:

| Architecture | Primary fiber `n=(0,1,0)` | Alternate fiber `n'=(1,0,0)` |
|---|---:|---:|
| `IntersectingPairsAligned6R` | Required | Required |
| `URLikeAligned6R` | Parallel comparison | Parallel comparison |

For each candidate fiber, test in order:

1. duplicate-configuration scan;
2. branch-wide candidate-axis concurrency;
3. fixed spherical arc dimensions;
4. inactive-coordinate locking, where applicable;
5. local tangent equivalence;
6. continued-motion equivalence.

Only after all six prerequisites pass may the candidate be treated as an exact spherical `RRRR`.

McCarthy–Soh classification remains blocked until then.

## 9. Failure interpretation for Sprint 06

If one candidate fails, the valid conclusion is:

> This selected task-space fiber is not an exact spherical `RRRR`.

The invalid conclusion is:

> No spherical fiber exists for this robot architecture.

Because Sprint 05 established multiple valid fibers, failure of one selected slice cannot rule out all possible spherical fibers.

## 10. Closeout

Sprint 05 is closed.

Administrative closeout completed:

- Check-in 5 approved (`CONTINUE WITH CHANGED SCOPE`);
- A09 and R06 constrained;
- Phase 5 marked complete;
- Phase 6 opened under the candidate-fiber framing;
- exact UR and McCarthy–Soh remain blocked;
- pointing diagnostic renamed to `local_pointing_tangent_nonzero`;
- duplicate-configuration scan deferred to Sprint 06 as a formal metric.

The next research question is no longer whether local fibers exist.

It is:

> Does any tested candidate pointing fiber admit an exact spherical four-bar representation?
