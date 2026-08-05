# ATR_EXP_013 — Compound-joint principal angles

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 03 — Architecture comparison
**Related claim IDs:** C9 (local)
**Random seed:** none

## 1. Purpose

Compare physical `N_red` with the embedded compound-joint reduced basis on `IntersectingPairsAligned6R`.

## 2. Model

- model name: `IntersectingPairsAligned6R`
- grouping: `UA=(R1,R2)`, `UB=(R3,R4)`, `RC=R5`, roll `R6` held fixed
- configuration: `INTERSECTING_PAIRS_REGULAR_Q`
- comparison: principal angles, not raw basis columns

## 3. Expected result

Maximum principal angle at or below `1e-8` rad.

## 4. Command

```bash
python scripts/validate_architecture_comparison.py
```

## 5. Results

- status: PASS
- observed: principal angles `(0, 0)` rad
- artifacts: `results/aligned_terminal_roll/ATR_EXP_013/`

## 6. Interpretation

- `PASS` supports local C9 on this architecture only.
- This is not a global continuation-equivalence claim.
