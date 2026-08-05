# Sprint 05 — Explicit one-dimensional fiber

**Sprint status:** Complete — Check-in 5 approved `CONTINUE WITH CHANGED SCOPE`  
**Milestone target:** M5 — Fiber legitimacy established  
**Check-in:** Check-in 5  
**Authorized by:** Check-in 4B (Case A) and Check-in 04C (Pass), 2026-08-04  
**Primary architectures:** `IntersectingPairsAligned6R` (controlled primary), `URLikeAligned6R` (parallel)  
**Timebox:** One independent scalar fiber of the validated pointing parent  
**HTML diagnostic:** Developer-only if added; not an acceptance criterion

## 1. Sprint objective

Impose one independent scalar constraint on the Sprint 04B/04C local two-dimensional pointing chart and continue the resulting one-dimensional fiber.

Stage C (workshop): a 1DOF pointing fiber is an additional slice of the reduced pointing parent, not a restatement of terminal-roll quotienting.

```text
F_c = { q in P_{p0,q6*} : h(q) = c }
```

with

```text
p(q) = p0
q6 = q6*
h(q) = c
```

## 2. Primary candidate constraint

Workshop / roadmap candidate, now locked:

```text
h(q) = n · d(q) = c
n  = (0, 1, 0)     world +Y
n' = (1, 0, 0)     world +X   (ATR_EXP_030 alternate)
```

`c = h(q0)` and `c' = h'(q0)` at `INTERSECTING_PAIRS_REGULAR_Q` / `URLIKE_REGULAR_Q`. Both directions were checked at those seeds: stacked `(p,h)` Jacobian on `q1…q5` has rank 4 / nullity 1, and `dh/dq6 = 0`.

Requirements on the choice:

- `n` is a named fixed world-frame unit direction, recorded in the experiment manifest;
- `c` is taken at the existing regular seed so `h(q0)=c` exactly (up to documented roundoff);
- `h` is independent of the position constraint and of terminal roll (`dh/dq6 = 0` analytically when `d ∥ w6`);
- `n` is not parallel to `d(q0)` in a way that makes the level set locally empty or the differential vanish.

Joint freeze `q2 = q2*` is a negative control only, not a candidate primary `h`.

## 3. Hypotheses under test

### H1 — Independent scalar

At the regular seed, the stacked constraint Jacobian for `(p, h)` with `q6` frozen has rank 4 and nullity 1.

### H2 — Regular one-dimensional branch

Sequential continuation along the reduced null direction produces a connected regular fiber through `q0`.

### H3 — Reversibility

Forward then reverse along the fiber returns within configured joint and pointing tolerances, starting the reverse run from the accepted endpoint.

### H4 — Nondegenerate pointing image

The map from fiber parameter to `d(q)` is a genuine curve (numerical rank 1), not a collapsed point.

### H5 — Not a coordinate artifact

The same qualitative 1D fiber exists under at least one alternate task-space `h` (or an equivalent reparameterization). Freezing a single joint `qi=const` or a chart coordinate `s=const` is not accepted as the primary `h`.

### H6 — Architecture-specific topology remains optional

The general fiber API does not call `suur_map`. Intersecting-pairs pair distances may be reported separately on IP only.

## 4. Nonclaims

Sprint 05 does not establish:

- a spherical four-bar;
- four-axis global concurrency;
- fixed spherical arc dimensions;
- McCarthy–Soh `T1`–`T4`;
- an eight-fiber `Uv` enumeration;
- exact UR / URDF applicability;
- global pointing coverage or dexterity.

A one-dimensional fiber is not a spherical `RRRR` merely because four axes can be drawn at one pose.

## 5. Research lane

### 5.1 Precise claim (C11 / A09)

At a regular aligned-terminal seed, one independent task-space scalar on pointing, together with `p=p0` and frozen `q6`, defines a reproducible local 1D configuration branch whose pointing image is a curve.

### 5.2 Failure interpretations

| Observation | Interpretation |
|---|---|
| Rank of `(Jp; ∇h)` on `q1…q5` is not 4 | `h` is redundant, singular, or parallel to the position constraint |
| Nullity ≠ 1 | wrong constraint count or singular seed |
| Reverse fails | branch tracking unresolved; do not claim a fiber |
| Pointing image collapses | `h` locked pointing; fiber is not useful for orientation capability |
| Fiber disappears under alternate `h` | coordinate artifact (R06) |
| UR-like path requires `SUUR` | topology is being imposed |

## 6. Algorithm sketch (implementation later)

Reuse sequential predictor-corrector machinery from Sprint 04B:

1. At accepted `q_k`, form the reduced tangent to `{p=p0, h=c, q6=q6*}`.
2. Align the 1D tangent to the previous step (sign consistency).
3. Predict `q_pred = q_k + t_k Δσ`, freeze `q6`, correct `(p,h)=(p0,c)` on `q1…q5`.
4. Halve the step on failure; record rejected steps.
5. Continue both `±σ` from the seed; store full `q` and `d`.

Do not reuse only the 2D chart `N_red` without imposing `∇h`.

## 7. Software layout (proposed; not created in this planning step)

```text
src/grashof_workspace/spatial_experiments/
    fiber_constraints.py      # h(q), gradients, independence tests
    fiber_continuation.py     # 1D sequential PC (or extend continuation.py carefully)

scripts/
    validate_pointing_fiber.py

tests/
    test_spatial_fiber_constraints.py
    test_spatial_fiber_continuation.py

docs/aligned_terminal_roll/checkins/
    CHECKIN_05_FIBER_LEGITIMACY.md   # approved CONTINUE WITH CHANGED SCOPE
```

Keep `include_pairs` / `suur_map` out of the general fiber API.

## 8. Proposed experiments

| ID | Experiment | Required result |
|---|---|---|
| `ATR_EXP_027` | Independence of `h=n·d` at the IP seed | rank 4 / nullity 1; `dh/dq6=0` |
| `ATR_EXP_028` | IP sequential fiber | regular reversible branch; pointing curve rank 1 |
| `ATR_EXP_029` | UR-like sequential fiber, same API | same C11 gates; no SUUR/pair fields required |
| `ATR_EXP_030` | Alternate task-space `h` artifact control | fiber survives; joint-freeze control is distinct |
| `ATR_EXP_031` | Step refinement on the fiber | shared-node stability and/or loop/reverse improvement with true integrator steps |

These experiments have been run via `python scripts/validate_pointing_fiber.py` (ATR_EXP_027–031 PASS).

## 9. Provisional thresholds

Start from Sprint 04B/04C gates unless a recorded reason revises them:

- position residual `≤ 1e-10 m`
- `|h(q)-c|` at or below a documented pointing-scalar tolerance
- reverse joint wrap-norm `≤ 1e-6 rad`
- reverse pointing `≤ 1e-8`
- max corrector iterations 20; max step reductions 3
- 0 failed samples on the approved benchmark segment

Record actual thresholds in manifests. Decision artifacts from a clean committed revision only.

## 10. Check-in 5 questions

1. Is `h` independent of `p=p0` and of terminal roll?
2. Is the constrained set locally one-dimensional and regular?
3. Is the branch reversible and noncollapsed?
4. Is the pointing image a curve?
5. Does the fiber survive an alternate task-space `h` (not a joint freeze)?
6. Does UR-like pass without imposed `SUUR`?
7. Is the evidence enough to open spherical-four-bar tests, or only to retain a non-spherical fiber?

## 11. Check-in 5 decision matrix

| Case | Meaning | Next |
|---|---|---|
| A | Both architectures pass all gates | Authorize Phase 6 spherical tests on the accepted fiber definition |
| B | IP passes; UR-like fails | Spherical search only on IP; open a UR-like fiber investigation |
| C | UR-like passes; IP fails | Do not start the compound-topology spherical program |
| D | Rank/nullity or artifact control fails | No Phase 6; revise `h` or stop the fiber claim |
| E | Reverse/duplicates fail | Branch tracking unresolved; no Phase 6 |

## 12. Explicitly deferred

- spherical-axis concurrency;
- fixed spherical arc dimensions;
- inactive-coordinate locking as a spherical test;
- McCarthy–Soh classification;
- exact UR geometry;
- global dexterity claims;
- HTML readout as a gate.

## 13. Acceptance of this planning note

This note is accepted for implementation when the decision owner agrees that:

1. `h(q)=n·d(q)` is the primary candidate;
2. the alternate-`h` artifact control is required;
3. IP is primary and UR-like is parallel;
4. spherical work remains out of Sprint 05.

Accepted for implementation 2026-08-04. Check-in 5 approved 2026-08-04 (`CONTINUE WITH CHANGED SCOPE`): primary and alternate fibers are candidate slices, not canonical fibers. Sprint 06 spherical-equivalence planning is authorized.
