# Sprint 06 — Candidate spherical equivalence

**Sprint status:** Ready for review — planning only; no spherical code yet
**Milestone target:** M6 — Spherical equivalence decision
**Check-in:** Check-in 6
**Authorized by:** Check-in 5 (`CONTINUE WITH CHANGED SCOPE`), 2026-08-04
**Primary architectures:** `IntersectingPairsAligned6R` (controlled primary), `URLikeAligned6R` (parallel comparison)
**Candidate fibers:** primary `n = (0, 1, 0)` and alternate `n' = (1, 0, 0)`
**Timebox:** Exact spherical-`RRRR` prerequisites on the accepted local fibers
**HTML diagnostic:** Developer-only if added; not an acceptance criterion

## 1. Sprint objective

Test whether either named Sprint 05 task-space fiber is an exact spherical four-bar on the continued local branch, without treating either slice as canonical or architecture-derived.

```text
For each (architecture, n_star) in the Check-in 5 matrix:
    continue F_c = { q in P_{p0,q6*} : n_star · d(q) = c }
    test spherical-RRRR prerequisites in order
```

## 2. Candidate matrix

| Architecture | Primary `n=(0,1,0)` | Alternate `n'=(1,0,0)` |
|---|---|---|
| `IntersectingPairsAligned6R` | Required | Required |
| `URLikeAligned6R` | Required parallel comparison | Required parallel comparison |

Seeds remain `INTERSECTING_PAIRS_REGULAR_Q` / `URLIKE_REGULAR_Q` with `q6* = 0.70`. Do not introduce a new fiber constraint in this sprint.

## 3. Ordered tests

For each candidate, in order:

1. **Duplicate-configuration scan** over the accepted fiber segment (Sprint 05 closeout item).
2. **Branch-wide candidate-axis concurrency** (four-axis residual, not a single-pose drawing).
3. **Fixed spherical arc dimensions** along the continued branch.
4. **Inactive-coordinate locking**, where applicable and marked unverified if the theorem does not apply.
5. **Local tangent equivalence** to a spherical `RRRR` model, if one is well-posed.
6. **Continued-motion equivalence** on the same branch.
7. **McCarthy–Soh classification only after items 1–6 pass.**

Stop a candidate at the first failed prerequisite. Record the failure as “this slice is not an exact spherical `RRRR`,” not as “no spherical fiber exists.”

## 4. Hypotheses under test

### H1 — No hidden repeats

Distinct accepted `σ` stations are not the same configuration up to wrap.

### H2 — Concurrent candidate axes

A named four-axis set remains concurrent along the branch within a documented residual.

### H3 — Fixed arcs

Spherical link angles are invariant along the branch, not only at the seed.

### H4 — Mechanism equivalence

If concurrency and arcs hold, local tangent and continued motion match the spherical model.

### H5 — Classifier last

McCarthy–Soh is applied only to a candidate that already passed H2–H4.

## 5. Nonclaims

Sprint 06 does not establish:

- a canonical or architecture-derived fiber;
- that failure of `n` or `n'` rules out other spherical fibers;
- exact UR / URDF applicability;
- global pointing coverage or dexterity;
- that local fiber existence (Check-in 5) is spherical.

A one-dimensional fiber is not a spherical `RRRR` merely because four axes can be drawn at one pose.

## 6. Research lane

### 6.1 Precise claim (C12)

For a named candidate slice, either the branch-wide spherical-`RRRR` prerequisites hold, or the candidate is rejected / labeled approximate / left unresolved.

### 6.2 Failure interpretations

| Observation | Interpretation |
|---|---|
| Duplicate `q` at distinct `σ` | branch tracking or parameterization issue; do not test spherical invariants yet |
| Concurrency residual grows along the branch | instantaneous quadrilateral only |
| Arcs drift | not a fixed spherical linkage |
| Tangent or continued motion mismatch | geometric resemblance without mechanism equivalence |
| McCarthy–Soh applied before 1–6 | out of order; discard the classification |

## 7. Software layout (proposed; not created in this planning step)

```text
src/grashof_workspace/spatial_experiments/
    fiber_duplicates.py          # pairwise wrap-distance duplicate scan
    spherical_invariants.py      # concurrency and arc residuals on a fiber
    spherical_equivalence.py     # tangent / continued-motion comparison

scripts/
    validate_spherical_candidates.py

tests/
    test_spatial_fiber_duplicates.py
    test_spatial_spherical_invariants.py

docs/aligned_terminal_roll/checkins/
    CHECKIN_06_SPHERICAL_EQUIVALENCE.md   # draft after experiments
```

Keep `suur_map` out of the general spherical-test API. IP pair diagnostics remain IP-only.

Sprint 05 closeout renamed `local_rank_one` to `local_pointing_tangent_nonzero`. Duplicate scan remains the first Sprint 06 metric.

## 8. Proposed experiments

| ID | Experiment | Required result |
|---|---|---|
| `ATR_EXP_032` | Duplicate scan on all four candidate fibers | no wrap-equivalent repeats at distinct `σ`, or labeled unresolved |
| `ATR_EXP_033` | IP primary concurrency and arcs | pass, fail, or approximate — not undecided without a residual report |
| `ATR_EXP_034` | IP alternate concurrency and arcs | same |
| `ATR_EXP_035` | UR-like primary and alternate concurrency/arcs | parallel comparison; no SUUR required |
| `ATR_EXP_036` | Tangent and continued-motion equivalence for any candidate that passed 033–035 | pass only if both local and continued tests hold |

Do not run McCarthy–Soh experiments unless at least one candidate passes 032–036.

Do not run these experiments until this sprint note is accepted and implementation begins.

## 9. Provisional thresholds

Start from Sprint 05 fiber gates for continuation quality. Spherical residuals must be named before coding (metres for concurrency, radians for arcs). Decision artifacts from a clean committed revision only.

## 10. Check-in 6 questions

1. Did every candidate receive a duplicate scan?
2. Which candidates remain concurrent along the branch?
3. Which candidates keep fixed spherical arcs?
4. Does any surviving candidate match spherical motion, not just seed geometry?
5. Is McCarthy–Soh authorized, or still blocked?
6. Does a failed candidate imply only that slice failed?

## 11. Check-in 6 decision matrix

| Case | Meaning | Next |
|---|---|---|
| A | At least one candidate passes 1–6 | Authorize McCarthy–Soh on that candidate only |
| B | Concurrency/arcs fail; resemblance only | Record approximate spherical geometry; no classifier |
| C | All tested slices fail exact `RRRR` | Reject those slices; terminal-roll and fiber existence stand; other slices remain possible |
| D | Duplicate or tracking failure | Unresolved candidate; no spherical claim |
| E | UR-like diverges from IP | Architecture-limited spherical claim; do not generalize to exact UR |

## 12. Explicitly deferred

- exact UR geometry and URDF identity;
- global dexterity;
- declaring `n` or `n'` canonical;
- McCarthy–Soh before spherical prerequisites;
- HTML readout as a gate.

## 13. Acceptance of this planning note

This note is accepted for implementation when the decision owner agrees that:

1. both fibers and both architectures are in scope;
2. tests run in the Check-in 5 order;
3. McCarthy–Soh stays out until 1–6 pass;
4. one failed slice is not a global nonexistence proof.

Implementation must not start from this file until that review is explicit.
