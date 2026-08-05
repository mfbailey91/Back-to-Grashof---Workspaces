# Check-in 3 — Architecture comparison (local Stage B)

**Date:** 2026-08-04
**Milestone:** M3 — Architecture comparison
**Sprint(s):** Sprint 03 — Architecture comparison
**Decision owner:** Michael Bailey
**Decision status:** Draft — awaiting human confirmation

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
| ATR_EXP_013 | principal angles vs compound embedding | PASS |
| ATR_EXP_014 | local `N_red` steps | PASS |
| ATR_EXP_015 | three-architecture comparison | PASS |

## 4. Interpretation

Select one:

- `SUPPORTED`

Stage A survives on `GenericAligned6R`, `IntersectingPairsAligned6R`, and `URLikeAligned6R` at the named regular configurations. Local compound-joint embedding of the intersecting-pair chain matches physical `N_red` within the stated principal-angle tolerance, and short corrected steps keep `p` near `p0` with agreeing pointing increments. This establishes local C9 on the intersecting-pair architecture and architecture survival of Stage A. It does not establish global continued equivalence.

## 5. Decision

Select one (human gate):

- `CONTINUE`
- `CONTINUE WITH CHANGED SCOPE`
- `REPEAT EXPERIMENT`
- `PIVOT`
- `STOP THIS BRANCH`

Recommended if approved: Sprint 04 local pointing-manifold continuation with parent `IntersectingPairsAligned6R` (workshop SUUR path). Retain `URLikeAligned6R` as a parallel check. **Not auto-selected.**

Blocked work: fibers, spherical `RRRR`, McCarthy-Soh, exact UR / URDF / `sixr_grashof`.

## 6. Next sprint recommendation

If Check-in 3 is approved, implement predictor-corrector continuation of

```text
p(q) = p0
q6 held / quotiented
```

on `IntersectingPairsAligned6R`. Do not start spherical four-bar classification.
