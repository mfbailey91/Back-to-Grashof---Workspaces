# Check-in 5 — Explicit one-dimensional fiber

**Date:** 2026-08-04
**Milestone:** M5 — Fiber legitimacy established
**Sprint(s):** Sprint 05 — Explicit one-dimensional fiber
**Repository commit:** `9eaf0ff` (implementation); artifacts regenerated from that clean revision
**Decision owner:** Michael Bailey
**Decision status:** Ready for review — not approved

## 1. Claim under review

At the locked regular aligned-terminal seeds, one independent task-space scalar

```text
h(q) = n · d(q) = c
n = (0, 1, 0)
c = h(q0)
```

together with `p = p0` and frozen `q6 = q6*` (`0.70` rad), defines a reproducible local 1D configuration branch whose pointing image is a curve on `IntersectingPairsAligned6R` (primary) and `URLikeAligned6R` (parallel).

An alternate slice `n' = (1, 0, 0)` remains a regular reversible fiber. A `q2`-freeze control is distinct. The general fiber API does not impose `SUUR`.

This check-in does **not** claim spherical `RRRR`, four-axis concurrency, fixed spherical arcs, McCarthy–Soh, exact UR/URDF, or global pointing coverage.

## 2. What was implemented

- `docs/MATH_NOTES.md` §10 — fiber equations
- `fiber_constraints.py`, `fiber_continuation.py`, `fiber_diagnostics.py`, `fiber_experiments.py`
- `scripts/validate_pointing_fiber.py`
- tests: `test_spatial_fiber_constraints.py`, `test_spatial_fiber_continuation.py`
- ATR_EXP_027–031 specs and results
- method rationale / references updated for local C11

## 3. Experiments reviewed

| ID | Result | Role |
|---|---|---|
| ATR_EXP_027 | PASS | H1 independence, `dh/dq6=0`, both architectures |
| ATR_EXP_028 | PASS | IP sequential fiber, reverse from endpoint, pointing curve |
| ATR_EXP_029 | PASS | UR-like same API; no SUUR/pair gates |
| ATR_EXP_030 | PASS | Alternate `n'` fiber survives; `q2` freeze distinct |
| ATR_EXP_031 | PASS | `max_microstep=None` reverse error decreases; shared-`σ` within `1e-3` |

Recorded thresholds: position `1e-10` m; `|h-c|` `1e-12`; reverse joint `1e-6` rad; fiber reverse pointing `5e-8` (04B chart used `1e-8`; IP/`n'` accumulates `1.43e-8`). EXP 031 does not apply the tight reverse pointing gate to no-microstep runs.

## 4. Interpretation

Numerical outcomes are consistent with sprint-note **Case A** (both architectures pass the stated C11 gates), with these limitations:

- local benchmark segment only (`±4 × 0.03` around the seed);
- R06 is tested for this named `(n, n')` pair and one joint-freeze control, not for every scalar;
- A09 remains `OPEN (Sprint 05 under test)` until this check-in decides;
- a 1D pointing fiber is not a spherical four-bar.

**Check-in case (numerical, pending human decision): A — both architectures pass.**

## 5. Decision

**READY FOR REVIEW — not approved.**

Questions:

1. Is `h` independent of `p=p0` and of terminal roll?
2. Is the constrained set locally one-dimensional and regular?
3. Is the branch reversible and noncollapsed?
4. Is the pointing image a curve?
5. Does the fiber survive an alternate task-space `h` (not a joint freeze)?
6. Does UR-like pass without imposed `SUUR`?
7. Is the evidence enough to open spherical-four-bar tests, or only to retain a non-spherical fiber?

| Case | Meaning | Next |
|---|---|---|
| A | Both architectures pass all gates | Authorize Phase 6 spherical tests on the accepted fiber definition |
| B | IP passes; UR-like fails | Spherical search only on IP; open a UR-like fiber investigation |
| C | UR-like passes; IP fails | Do not start the compound-topology spherical program |
| D | Rank/nullity or artifact control fails | No Phase 6; revise `h` or stop the fiber claim |
| E | Reverse/duplicates fail | Branch tracking unresolved; no Phase 6 |

Still blocked until approval: spherical `RRRR`, McCarthy–Soh, exact UR/URDF, global dexterity.

## 6. Next sprint recommendation

If Case A is approved, authorize Sprint 06 spherical-four-bar tests on this fiber definition, in the roadmap order, without treating the fiber itself as already spherical.
