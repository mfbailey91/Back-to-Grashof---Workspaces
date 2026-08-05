# Check-in 3 — Architecture comparison (local Stage B)

**Date:** 2026-08-04
**Milestone:** M3 — Architecture comparison
**Sprint(s):** Sprint 03 — Architecture comparison
**Repository commit:** 6f43611
**Decision owner:** Michael Bailey
**Decision status:** Approved 2026-08-04

## 1. Claim under review

At named regular configurations of three synthetic aligned-terminal 6R architectures,

```text
rank(J_p) = 3
rank(J_pd) = 5
ker(J_pd) ∥ e6
rank(J_d N_red) = 2
```

and, locally on `IntersectingPairsAligned6R` only, the literal grouping

```text
UA = (R1, R2)   UB = (R3, R4)   RC = R5   roll = R6
```

matches physical `N_red` by principal angles and short `N_red` steps.

This check-in does **not** claim global continued equivalence, a 2D pointing manifold, fibers, spherical `RRRR`, or exact UR.

## 2. What was implemented

- Software: `architectures.py`, `compound_joints.py`, `architecture_experiments.py`, `sprint03_readout.py`
- Validation: ATR_EXP_011–015
- Readout: `results/aligned_terminal_roll/sprint03_readout/index.html`

## 3. Experiments reviewed

| Experiment | Purpose | Result |
|---|---|---|
| ATR_EXP_011 | intersecting-pairs Stage A | PASS |
| ATR_EXP_012 | UR-like Stage A | PASS |
| ATR_EXP_013 | principal angles vs compound embedding | PASS (non-discriminating; see §4) |
| ATR_EXP_014 | local `N_red` steps | PASS (non-discriminating; see §4) |
| ATR_EXP_015 | three-architecture comparison | PASS |

## 4. Interpretation

**PARTIALLY SUPPORTED**

Stage A survives at the named regular configurations of `GenericAligned6R`, `IntersectingPairsAligned6R`, and `URLikeAligned6R`. The two new architectures satisfy the expected position, position-and-pointing, terminal-roll-kernel, and reduced-pointing ranks.

The exact axis intersections and parallelisms of the synthetic architectures are also verified by construction.

ATR_EXP_013 and ATR_EXP_014 do not independently establish local compound-joint equivalence. The current compound basis is the fixed-roll portion of the same physical position-Jacobian null space used to construct `N_red`; consequently, zero principal angles and identical short trajectories are expected from the terminal-roll quotient itself and do not depend on the `UA` and `UB` intersection structure.

The `SUUR` grouping therefore remains a proposed exact kinematic regrouping that must be stated or implemented explicitly. Global continued equivalence and the two-dimensional pointing manifold remain untested.

## 5. Decision

**CONTINUE WITH CHANGED SCOPE**

Authorize Sprint 04 pointing-manifold work on `IntersectingPairsAligned6R`, with `URLikeAligned6R` retained as a parallel architecture check.

Before interpreting continuation through the `SUUR` model, Sprint 04 must:

1. replace the non-discriminating compound-tangent tests with an explicit coordinate-map and closure-equivalence test;
2. verify persistence of both intersecting-axis pairs away from the home configuration;
3. add a nonintersecting negative control demonstrating that the previous basis comparison did not test compound geometry;
4. regenerate experiment artifacts with a reproducible committed source identifier.

`IntersectingPairsAligned6R` is selected as the controlled continuation benchmark because it directly instantiates the workshop architecture, not because ATR_EXP_013–014 empirically selected it over the UR-like model.

Blocked work remains: fibers, spherical `RRRR`, McCarthy–Soh classification, and exact UR/URDF integration.

## 6. Next sprint recommendation

Implement predictor-corrector continuation of

```text
p(q) = p0,    q6 = constant
```

first on `IntersectingPairsAligned6R` and then through the same continuation interface on `URLikeAligned6R`.

The Sprint 04 exit gate is a stable two-dimensional fixed-position manifold with rank-two pointing motion away from explicitly identified singular sets.
