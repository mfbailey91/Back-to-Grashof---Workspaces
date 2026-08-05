# ATR_EXP_018 — IP compound-coordinate definedness and round-trip consistency

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04 — Pointing manifold
**Related claim IDs:** C9
**Random seed:** 23

## 1. Purpose

Verify that the intersecting-pair compound coordinate map `φ(θ; q6*)=(θ, q6*)` is defined when both pairs persist, and that it round-trips with serial coordinates.

## 2. Expected result

`φ` is defined on `IntersectingPairsAligned6R`; pair distances and inverse residuals stay below tolerance.

## 3. Command

```bash
python scripts/validate_pointing_manifold.py
```

## 4. Results

- status: PASS
- observed: `defined=True`, round-trip residuals `0`

## 5. Interpretation

- `PASS` is coordinate-map definedness and round-trip consistency only.
- This does **not** independently validate the forward kinematics of a separate closed `SUUR` mechanism.
