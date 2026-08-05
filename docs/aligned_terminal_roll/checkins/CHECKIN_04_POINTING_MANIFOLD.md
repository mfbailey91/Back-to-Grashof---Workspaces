# Check-in 4 — Pointing manifold (local patch)

**Date:** 2026-08-04
**Milestone:** M4 — Two-dimensional pointing surface established
**Sprint(s):** Sprint 04 — Pointing manifold
**Decision owner:** Michael Bailey
**Decision status:** Approved — `CONTINUE WITH CHANGED SCOPE`

## 1. Claim under review

Predictor-corrector continuation of

```text
p(q) = p0
q6 = constant
```

produces a local two-dimensional regular subset with `rank(J_d N_red)=2` away from explicitly labeled singular samples, first on `IntersectingPairsAligned6R` and then on `URLikeAligned6R` via the same interface.

The SUUR map `φ(θ; q6*)=(θ, q6*)` is defined exactly when intersecting-axis pairs persist. The Sprint 03 compound-tangent comparison is non-discriminating.

This check-in does **not** claim fibers, spherical `RRRR`, McCarthy–Soh, or exact UR.

## 2. What was implemented

- Software: `suur_coordinates.py`, `continuation.py`, `manifold_experiments.py`, `sprint04_readout.py`
- Validation: ATR_EXP_016–020
- Readout: `results/aligned_terminal_roll/sprint04_readout/index.html`

## 3. Experiments reviewed

| Experiment | Purpose | Result |
|---|---|---|
| ATR_EXP_016 | IP pair persistence | PASS |
| ATR_EXP_017 | Generic negative control | PASS |
| ATR_EXP_018 | IP compound-coordinate definedness and round-trip consistency | PASS |
| ATR_EXP_019 | IP continuation patch | PASS |
| ATR_EXP_020 | UR-like continuation patch | PASS |

## 4. Interpretation

**SUPPORTED WITH VALIDATION LIMITATIONS**

Sprint 04 establishes regular local fixed-position solution neighborhoods on both `IntersectingPairsAligned6R` and `URLikeAligned6R`. Across the sampled (9×9) patches, all corrected configurations satisfy the position constraint, the expected Stage A ranks, and rank-two reduced pointing motion.

For `IntersectingPairsAligned6R`, both designated consecutive axis pairs remain intersecting over the tested configurations, allowing the physical coordinates to be locally grouped as \(U_A=(R_1,R_2)\), \(U_B=(R_3,R_4)\), and \(R_C=R_5\). This topology is used because it is present in that architecture; it is not imposed on `URLikeAligned6R` or on generic chains.

The generic skew negative control confirms that the earlier principal-angle comparison was non-discriminating. The new pair-definedness test rejects that architecture as a two-universal-joint grouping.

The current grid is a local tangent-plane projection onto \(p(q)=p_0\), rather than a fully validated sequential continuation atlas. The implementation has not yet demonstrated chart injectivity, rank-two corrected chart coordinates, branch reversibility, or path independence. The current reverse-return metric is non-discriminating because each predictor is generated from \(q_0\) and the final requested sample is \(s=0\).

ATR_EXP_018 verifies coordinate-map definedness and round-trip consistency. It does not independently validate the forward kinematics of a separate closed `SUUR` mechanism.

This check-in does not establish a fiber, spherical `RRRR`, McCarthy–Soh classification, global pointing coverage, or exact UR applicability.

## 5. Decision

**CONTINUE WITH CHANGED SCOPE**

Authorize a short Sprint 04B validation-hardening package before explicit fiber construction.

Sprint 04B must:

1. implement sequential predictor-corrector continuation with basis alignment at each corrected sample;
2. perform genuine forward/reverse and closed-loop return tests;
3. verify that the corrected \((s,t)\mapsto q\) chart has numerical rank two;
4. test patch and step-size refinement;
5. retain the architecture-specific topology rule rather than imposing `SUUR`;
6. rename ATR_EXP_018 as a coordinate-definedness and round-trip test;
7. regenerate decision-bearing artifacts from a clean committed implementation revision;
8. preserve complete \(q\) and \(d\) sample data in machine-readable results.

After Sprint 04B passes, authorize Sprint 05 to define one independent scalar task-space constraint \(h(q)=c\) and continue the resulting one-dimensional fiber.

Still blocked: spherical `RRRR`, McCarthy–Soh classification, exact UR/URDF integration, and global dexterity claims.

## 6. Next sprint recommendation

Execute `SPRINT_04B_SEQUENTIAL_CONTINUATION_AND_POINTING_CHART_VALIDATION.md`.

After Check-in 4B validates a connected, reversible, rank-two, noncollapsed local chart, define one independent scalar constraint on the reduced pointing parent in Sprint 05.
