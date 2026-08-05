# ATR_EXP_012 — UR-like Stage A

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 03 — Architecture comparison
**Related claim IDs:** C6, C7, C8, A08
**Random seed:** none

## 1. Purpose

Verify Stage A identities on synthetic `URLikeAligned6R`, including exact `R2∥R3` and spherical-wrist concurrency.

## 2. Model

- model name: `URLikeAligned6R`
- configuration: `URLIKE_REGULAR_Q = (0.35, -0.42, 0.55, 0.28, -0.33, 0.70)`
- geometry: `R2∥R3`, `R4∩R5∩R6`, TCP on `R6` beyond the wrist, `d0∥w6`
- not an exact UR / URDF model
- units: metres, radians

## 3. Expected result

C6–C8 hold; elbow parallelism residual `0`; wrist pairwise distances `0`.

## 4. Command

```bash
python scripts/validate_architecture_comparison.py
```

## 5. Results

- status: PASS
- observed: `regular=True, rank_jp=3, rank_jpd=5, rank_jd_nred=2, elbow_par=0, wrist all 0`
- artifacts: `results/aligned_terminal_roll/ATR_EXP_012/`

## 6. Interpretation

- `PASS`
