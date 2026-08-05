# Check-in 4 — Pointing manifold (local patch)

**Date:** 2026-08-04
**Milestone:** M4 — Two-dimensional pointing surface established
**Sprint(s):** Sprint 04 — Pointing manifold
**Decision owner:** Michael Bailey
**Decision status:** Draft — awaiting human confirmation

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
| ATR_EXP_018 | SUUR coordinate map + closure | PASS |
| ATR_EXP_019 | IP continuation patch | PASS |
| ATR_EXP_020 | UR-like continuation patch | PASS |

## 4. Interpretation

Select one:

- `SUPPORTED`

Local C10 patches exist on both synthetic architectures. Discriminating SUUR tests pass on intersecting pairs and fail to be defined on the generic skew chain, while the deprecated `N_red` embedding test still passes there. Regular IP samples may be read in SUUR coordinates locally. This is not a global manifold classification and not a fiber.

## 5. Decision

Select one (human gate):

- `CONTINUE`
- `CONTINUE WITH CHANGED SCOPE`
- `REPEAT EXPERIMENT`
- `PIVOT`
- `STOP THIS BRANCH`

Recommended if approved: Sprint 05 explicit one-dimensional fiber `h(q)=c`. Still blocked: spherical `RRRR`, McCarthy–Soh, exact UR.

## 6. Next sprint recommendation

If Check-in 4 is approved, define one independent scalar constraint on the reduced pointing parent and continue the resulting one-dimensional branch. Do not apply McCarthy–Soh until exact `RRRR` tests pass.
