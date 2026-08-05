# ATR_EXP_011 — Intersecting-pairs Stage A

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 03 — Architecture comparison
**Related claim IDs:** C6, C7, C8
**Random seed:** none

## 1. Purpose

Verify Stage A rank/nullity identities and exact pair intersections on `IntersectingPairsAligned6R`.

## 2. Model

- model name: `IntersectingPairsAligned6R`
- configuration: `INTERSECTING_PAIRS_REGULAR_Q = (0.35, -0.42, 0.55, 0.28, -0.33, 0.70)`
- geometry: exact `R1∩R2`, exact `R3∩R4`, leftover `R5`, aligned `R6`
- units: metres, radians

## 3. Expected result

`rank(J_p)=3`, `rank(J_pd)=5` with kernel aligned to `e6`, `rank(J_d N_red)=2`, pair intersection distances `0`.

## 4. Command

```bash
python scripts/validate_architecture_comparison.py
```

## 5. Results

- status: PASS
- observed: `regular=True, rank_jp=3, rank_jpd=5, rank_jd_nred=2, d_ua=0, d_ub=0`
- artifacts: `results/aligned_terminal_roll/ATR_EXP_011/`

## 6. Interpretation

- `PASS`
