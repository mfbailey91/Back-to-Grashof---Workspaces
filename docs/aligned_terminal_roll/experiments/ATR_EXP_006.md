# ATR_EXP_006 — Regular configuration rank suite

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 02 — Generic aligned 6R
**Related claim IDs:** C6, C7, C8
**Random seed:** none

## 1. Purpose

Verify Stage A rank/nullity identities at a named regular configuration of `GenericAligned6R`.

## 2. Model

- model name: `GenericAligned6R`
- configuration: `REGULAR_Q = (0.35, -0.42, 0.55, 0.28, -0.33, 0.70)`
- units: metres, radians

## 3. Expected result

`rank(J_p)=3`, `dim ker(J_p)=3`, `rank(J_pd)=5`, `dim ker(J_pd)=1` aligned to `e6`, `rank(J_d N_red)=2`.

## 4. Command

```bash
python scripts/validate_aligned_6r_reduction.py
```

## 5. Results

- status: PASS
- observed: `rank_jp=3, null_jp=3, rank_jpd=5, null_jpd=1, align=0, rank_jd_nred=2`

## 6. Interpretation

- `PASS`
