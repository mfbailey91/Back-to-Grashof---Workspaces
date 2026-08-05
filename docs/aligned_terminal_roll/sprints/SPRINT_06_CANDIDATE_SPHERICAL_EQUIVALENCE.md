# Sprint 06 — Candidate spherical equivalence

**Sprint status:** ATR_EXP_032–035 reimplemented under Check-in 5 review corrections; 036 deferred  
**Milestone target:** M6 — Spherical equivalence decision  
**Check-in:** Check-in 6  
**Authorized by:** Check-in 5 (`CONTINUE WITH CHANGED SCOPE`), approved 2026-08-04  
**Primary architectures:** `IntersectingPairsAligned6R` (controlled primary), `URLikeAligned6R` (parallel / exploratory)  
**Candidate fibers:** primary `n = (0, 1, 0)` and alternate `n' = (1, 0, 0)`  
**Timebox:** Duplicate scan plus topology-derived global-center / arc / axis-legitimacy tests; motion equivalence deferred  
**HTML diagnostic:** Developer-only if added; not an acceptance criterion

## 1. Sprint objective

Test whether either named Sprint 05 task-space fiber is an exact spherical four-bar on the continued local branch, without treating either slice as canonical or architecture-derived.

```text
For each (architecture, n_star) in the Check-in 5 matrix:
    continue F_c = { q in P_{p0,q6*} : n_star · d(q) = c }
    test spherical-RRRR prerequisites in order
```

This batch implements tests 1–4 on the named constructions. Tests 5–7 and McCarthy–Soh remain deferred.

## 2. Candidate matrix

| Architecture | Primary `n=(0,1,0)` | Alternate `n'=(1,0,0)` |
|---|---|---|
| `IntersectingPairsAligned6R` | Required topology-derived `S−UA−UB−R5` | Required, same construction |
| `URLikeAligned6R` | Duplicate scan + exploratory fixed-tuple diagnostic | Same; no exact `RRRR` claim |

Seeds remain `INTERSECTING_PAIRS_REGULAR_Q` / `URLIKE_REGULAR_Q` with `q6* = 0.70`. Do not introduce a new fiber constraint in this sprint.

## 3. Ordered tests

For each candidate, in order:

1. **Duplicate-configuration scan** over the accepted fiber segment.
2. **Concurrency** — one branch-global spherical center `c*`, not per-pose near-concurrency.
3. **Fixed spherical arc dimensions** along the continued branch.
4. **Axis legitimacy** — body-fixed effective-axis invariance (Sprint 06 gate). Simple coordinate locking is reported as a diagnostic only.
5. **Local tangent equivalence** to a spherical `RRRR` model — deferred (`ATR_EXP_036`).
6. **Continued-motion equivalence** — deferred with item 5.
7. **McCarthy–Soh classification** — blocked until items 1–6 pass.

Stop a candidate at the first failed prerequisite. Record the failure as “this slice is not an exact spherical `RRRR`,” not as “no spherical fiber exists.”

## 4. Named four-axis set

The predicted four-bar is not four original robot axes and is not an arbitrary per-sample `C(5,4)` scan.

For `IntersectingPairsAligned6R` the architecture is

```text
UA = (R1, R2)    UB = (R3, R4)    RC = R5
```

The reduced cyclic parent is

```text
S − UA − UB − R5
```

At each fiber configuration, with unit fiber tangent `t = (t1,…,t5, 0)` and live `current_axes(q)`:

```text
Ω_A = t1 ω1 + t2 ω2     through the current UA center
Ω_B = t3 ω3 + t4 ω4     through the current UB center
Ω_R = ω5                on the physical R5 line
Ω_S = Σ_{i=1}^{5} t_i ω_i through the fixed task point p0
```

Every effective angular velocity must be nonzero (`‖Ω‖ > 1e-8`), normalized, and sign-aligned continuously along the branch. The candidate cyclic order is

```text
S_eff → UA_eff → UB_eff → R5
```

This construction is **unverified as a theorem**. It is the named C12 hypothesis for this sprint. Equations live in `docs/MATH_NOTES.md` §11.

### 4.1 Global fixed-center concurrency

It is insufficient for the four lines to have a small best-fit intersection independently at every sample if that center drifts.

```text
c* = argmin_c  Σ_{j,k} ‖(I − a_jk a_jk^T)(c − r_jk)‖²
```

Report:

- global RMS line-to-center residual;
- maximum line-to-center residual;
- per-sample fitted-center drift from `c*`;
- residual versus fiber parameter `σ`.

A spherical mechanism requires a fixed center.

### 4.2 UR-like exploratory diagnostic

The UR-like model has parallel `R2,R3` and a spherical wrist `R4,R5,R6`. Because `q6` is gauge-fixed, “the three wrist axes plus one more” is not a justified active spherical-four-bar construction.

For Sprint 06:

- run the duplicate scan on both UR-like fibers;
- allow a fixed physical four-subset scan of `R1…R5` as an **exploratory diagnostic**;
- hold each tested tuple fixed across the branch;
- do not choose a different best tuple at each sample;
- do not use the physical-subset scan to claim exact `RRRR`.

`ATR_EXP_035` is exploratory unless a topology-derived four-axis construction is later supplied.

### 4.3 Locking versus body-fixed axis invariance

The primary intersecting-pairs fiber does not lock any of `q1,…,q5`. Approximate committed-segment ranges:

```text
q1: 0.0863 rad
q2: 0.0428 rad
q3: 0.0948 rad
q4: 0.1951 rad
q5: 0.0198 rad
```

Neither universal pair collapses to a physical revolute merely because one of its original coordinates remains constant.

Two policies:

- **Simple locking (diagnostic only):** require one coordinate in each `U` pair to remain constant within `1e-6` rad. Under this policy the primary IP fiber already fails.
- **Body-fixed effective-axis invariance (Sprint 06 gate):** both coordinates may move, but each effective revolute axis remains fixed in its two adjacent body frames:
  - `S` in ground and the body after `R5`;
  - `UA` in ground and the body after `R2`;
  - `UB` in the bodies after `R2` and `R4`;
  - `R5` in the bodies after `R4` and `R5`.

Frozen `q6` is the terminal-roll quotient, not spherical locking.

## 5. Hypotheses under test

### H1 — No hidden repeats

Distinct accepted `σ` stations are not the same configuration up to wrap.

### H2 — Concurrent candidate axes at one fixed center

The topology-derived set remains concurrent at a single `c*` along the branch within a documented residual, and per-sample centers do not drift from `c*`.

### H3 — Fixed arcs

Spherical link angles of cycle `(S, UA, UB, R5)` are invariant along the branch, not only at the seed.

### H4 — Axis legitimacy

Effective axes remain body-fixed in adjacent frames. Simple coordinate locking is reported but is not the exactness gate.

### H5 — Mechanism equivalence

Deferred. If concurrency, fixed center, arcs, and axis legitimacy hold exactly, local tangent and continued motion must still be designed before coding.

### H6 — Classifier last

McCarthy–Soh is applied only to a candidate that already passed H2–H5 and later motion equivalence.

## 6. Nonclaims

Sprint 06 does not establish:

- a canonical or architecture-derived fiber;
- that failure of `n` or `n'` rules out other spherical fibers;
- exact UR / URDF applicability;
- global pointing coverage or dexterity;
- that local fiber existence (Check-in 5) is spherical;
- McCarthy–Soh labels from 032–035 alone;
- an exact UR-like `RRRR` from a physical-subset scan.

A one-dimensional fiber is not a spherical `RRRR` merely because four axes can be drawn at one pose.

## 7. Research lane

### 7.1 Precise claim (C12, partial this batch)

For a named candidate slice, either the branch-wide topology-derived concurrency, fixed-center, arc, and axis-legitimacy prerequisites hold, or the candidate is rejected / labeled approximate / left unresolved. Motion equivalence remains open.

### 7.2 Failure interpretations

| Observation | Interpretation |
|---|---|
| Duplicate `q` at distinct `σ` | branch tracking or parameterization issue; do not test spherical invariants yet |
| Construction not well-posed | unresolved or N/A; not a physical-axis search |
| Global `c*` residual large, or sample centers drift | not a fixed spherical center |
| Arcs drift | not a fixed spherical linkage |
| Simple lock fails while body-fixed passes | compound `U` still moving as an effective revolute; report both |
| Body-fixed axis fails | effective axis is not a physical revolute in adjacent bodies |
| Exact 032–035 without 036 | geometric resemblance only; do not apply McCarthy–Soh |
| McCarthy–Soh applied before 1–6 | out of order; discard the classification |
| Best UR-like tuple looks concurrent | exploratory diagnostic only; no exact `RRRR` claim |

## 8. Software layout

```text
src/grashof_workspace/spatial_experiments/
    fiber_duplicates.py          # pairwise wrap-distance duplicate scan
    spherical_invariants.py      # S−UA−UB−R5 axes, global c*, arcs, body-fixed drift

scripts/
    validate_spherical_candidates.py

tests/
    test_spatial_fiber_duplicates.py
    test_spatial_spherical_invariants.py
    test_spatial_spherical_experiments.py
```

Keep `suur_map` out of the general spherical-test API. IP pair-center geometry remains IP-only. Do not add `spherical_equivalence.py` or `mccarthy_soh.py` in this batch.

## 9. Experiments

| ID | Experiment | Required result |
|---|---|---|
| `ATR_EXP_032` | Duplicate scan on all four candidate fibers | no wrap-equivalent repeats at distinct `σ`, or labeled unresolved |
| `ATR_EXP_033` | IP primary topology-derived axes, global concurrency, drift, arcs, body-fixed legitimacy | `exact` / `approximate` / `fail` / `unresolved` with residual report |
| `ATR_EXP_034` | IP alternate using the same construction | same |
| `ATR_EXP_035` | UR-like duplicate scan plus exploratory fixed-tuple diagnostics | duplicates reported; no exact `RRRR` claim |
| Mini-check-in | Review 032–035 | before any 036 design |
| `ATR_EXP_036` | Tangent and continued-motion equivalence | implement only if an IP candidate passes concurrency, fixed-center, arc, and axis-legitimacy gates |

Do not run McCarthy–Soh experiments unless at least one candidate later passes 032–036.

## 10. Numerical policy

These cutoffs are provisional exact-synthetic thresholds, not theorems. Always report raw residuals. Continuation quality reuses Sprint 05 fiber gates.

```text
duplicate joint distance:       1e-6 rad
minimum effective-axis norm:    1e-8
global concurrency residual:    1e-8 m
fixed-center drift:             1e-8 m
spherical arc drift:            1e-6 rad
body-fixed axis drift:          1e-6 rad
coordinate-lock range:          1e-6 rad  (diagnostic policy only)
pair-center persistence:        1e-12 m
```

Approximate reporting bands (not exactness gates): concurrency / drift `≤ 1e-6 m`, arcs / body-fixed `≤ 1e-4 rad`.

Arc cycle is `(S, UA, UB, R5)` with `acos` in `(0, π]` and seed-continuous `±w`. Do not assign McCarthy–Soh roles.

Decision artifacts from a committed revision; working-tree dirty is recorded in the manifest.

## 11. Check-in 6 questions

1. Did every candidate receive a duplicate scan?
2. Which IP candidates remain concurrent at one fixed `c*`?
3. Which IP candidates keep fixed spherical arcs and body-fixed effective axes?
4. Was UR-like kept exploratory rather than given an invented exact four-bar?
5. Is McCarthy–Soh still blocked?
6. Does a failed candidate imply only that slice failed?

## 12. Check-in 6 decision matrix

| Case | Meaning | Next |
|---|---|---|
| A | At least one candidate later passes 1–6 including 036 | Authorize McCarthy–Soh on that candidate only |
| B | Concurrency/arcs/axis legitimacy fail or approximate; resemblance only | Record approximate spherical geometry; no classifier |
| C | All tested IP slices fail exact `RRRR` | Reject those slices; terminal-roll and fiber existence stand; other slices remain possible |
| D | Duplicate or tracking failure | Unresolved candidate; no spherical claim |
| E | UR-like remains exploratory / diverges from IP | Architecture-limited claim; do not generalize to exact UR |

## 13. Explicitly deferred

- `ATR_EXP_036` spherical-model tangent and continued-motion equivalence until an IP candidate passes 032–035;
- exact UR geometry and URDF identity;
- global dexterity;
- declaring `n` or `n'` canonical;
- McCarthy–Soh before spherical prerequisites;
- HTML readout as a gate;
- A10/A11 status updates until Check-in 6.

## 14. Acceptance of this planning note

Accepted for 032–035 implementation after the Sprint 06 review corrections:

1. Check-in 5 is formally approved (`CONTINUE WITH CHANGED SCOPE`);
2. both fibers and both architectures are in scope;
3. tests run in the ordered gate;
4. IP axes are the named set `S−UA−UB−R5`, not physical four-subsets;
5. concurrency is a single branch-global `c*`;
6. UR-like spherical testing is exploratory only;
7. simple locking is diagnostic; body-fixed effective-axis invariance is the legitimacy gate;
8. thresholds and equations are recorded before coding;
9. McCarthy–Soh stays out until 1–6 pass;
10. one failed slice is not a global nonexistence proof.

## 15. Implementation outcome (2026-08-05, corrected construction)

| ID | Report status | Candidate verdict |
|---|---|---|
| `ATR_EXP_032` | PASS | no duplicates on all four fibers |
| `ATR_EXP_033` | PASS | IP primary `fail` (`c*_rms≈0.248 m`, `c*_max≈0.334 m`, drift `≈0.092 m`, arc `≈0.771 rad`, body-fixed `≈0.511 rad`; simple lock false) |
| `ATR_EXP_034` | PASS | IP alternate `fail` (`c*_rms≈0.160 m`, `c*_max≈0.310 m`, drift `≈0.076 m`, arc `≈0.862 rad`, body-fixed `≈0.586 rad`; simple lock false) |
| `ATR_EXP_035` | PASS | UR-like duplicates clean; exploratory best fixed tuple `R1-R2-R3-R4` (`max≈0.15 m`); no exact `RRRR` claim |
| `ATR_EXP_036` | Deferred | no exact IP candidate |

Command: `python scripts/validate_spherical_candidates.py`.

McCarthy–Soh remains blocked. Check-in 6 can treat this as Case B/C for the tested IP slices and Case E for UR-like exploratory diagnostics, without invalidating Check-in 5 fiber existence.
