# ATR_EXP_019 — Intersecting-pairs continuation patch

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04 — Pointing manifold
**Related claim IDs:** C10
**Random seed:** none

## 1. Purpose

Build a local predictor-corrector patch of `p(q)=p0`, `q6` constant, on `IntersectingPairsAligned6R`.

## 2. Expected result

A regular subset remains near `p0` with `rank(J_d N_red)=2`. Singular samples are labeled. `φ` is defined on the regular subset. Reverse-run returns near the start.

## 3. Command

```bash
python scripts/validate_pointing_manifold.py
```

## 4. Results

- status: PASS
- observed: `regular=81/81`, `max_p=6.991e-15`, `reverse_err=0`, `phi_regular=True`

## 5. Interpretation

- `PASS` is a local C10 patch, not a fiber and not a spherical `RRRR`.
