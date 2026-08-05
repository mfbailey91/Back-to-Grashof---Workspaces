# Check-in 2 — Two-dimensional reduction (generic 6R)

**Date:** 2026-08-04
**Milestone:** M2 — Two-dimensional reduction established
**Sprint(s):** Sprint 02 — Generic aligned 6R
**Decision owner:** Michael Bailey
**Decision status:** Draft — awaiting human confirmation

## 1. Claim under review

At regular configurations of a generic synthetic aligned-terminal 6R chain,

```text
rank(J_p) = 3
dim ker(J_p) = 3
J_p e6 = 0
J_d e6 = 0
rank(J_pd) = 5
dim ker(J_pd) = 1 ∥ e6
rank(J_d N_red) = 2
```

This is a local differential claim. It is not a continuation or architecture-equivalence claim.

## 2. What was implemented

- Software: `serial_chain.py`, `jacobians.py`, `aligned_6r.py`, `reduction_experiments.py`
- Validation: ATR_EXP_006–010
- Readout: `results/aligned_terminal_roll/sprint02_readout/index.html`

## 3. Experiments reviewed

| Experiment | Purpose | Result |
|---|---|---|
| ATR_EXP_006 | regular rank suite | PASS |
| ATR_EXP_007 | Jacobian FD refinement | PASS |
| ATR_EXP_008 | full-chain terminal roll | PASS |
| ATR_EXP_009 | alignment negative controls | PASS |
| ATR_EXP_010 | seeded survey + near-singular label | PASS |

## 4. Interpretation

Select one:

- `SUPPORTED`

For the `GenericAligned6R` skew reference chain, the named regular configuration and all 48 seeded configurations satisfy the expected local fixed-position and position-and-pointing ranks. Terminal roll is the sole task-kernel direction, and the quotient fixed-position tangent space has rank-two pointing motion. This establishes the numerical Stage A reference result but does not yet establish architecture independence or global continuation.

## 5. Decision

Select one (human gate):

- `CONTINUE`
- `CONTINUE WITH CHANGED SCOPE`
- `REPEAT EXPERIMENT`
- `PIVOT`
- `STOP THIS BRANCH`

Recommended if approved: architecture comparison (generic vs compound-joint vs UR-like). Still blocked: continuation fibers and spherical `RRRR`.

## 6. Next sprint recommendation

If Check-in 2 is approved, implement controlled synthetic compound-joint / UR-like models and compare tangent spaces. Do not start spherical four-bar classification.
