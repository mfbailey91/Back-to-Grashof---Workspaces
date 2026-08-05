# ATR_EXP_018 — SUUR coordinate map and closure

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04 — Pointing manifold
**Related claim IDs:** C9
**Random seed:** 23

## 1. Purpose

Exercise the explicit map `φ(θ; q6*)=(θ, q6*)`, defined only when both intersecting pairs persist, and check closure residuals.

## 2. Expected result

`φ` is defined on `IntersectingPairsAligned6R`; pair, FK, and inverse residuals stay below tolerance.

## 3. Command

```bash
python scripts/validate_pointing_manifold.py
```

## 4. Results

- status: PASS
- observed: `defined=True`, `closed=True`, position residual `0`

## 5. Interpretation

- `PASS` authorizes reading regular IP continuation samples through SUUR coordinates locally.
- This is not global continued equivalence of an independent SUUR mechanism model.
