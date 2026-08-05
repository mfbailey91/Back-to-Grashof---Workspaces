# ATR_EXP_022 — Intersecting-pairs transported chart

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H1, H2, H3, H6
**Random seed:** none
**Implementation commit:** `e179ead`

## 1. Purpose

Build a row-wise sequential `(s,t)` chart on `IntersectingPairsAligned6R` with Procrustes-aligned `N_red` at each accepted sample.

## 2. Expected result

100% regular approved patch; `rank(Q)=rank(D)=2` at every interior node; no duplicates or failed samples; pair intersections persist.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

- status: PASS
- observed: `regular=81/81`, `rejected=0`, `interior=49`, `rankQ2=49`, `rankD2=49`, `duplicates=0`, `max_ua=max_ub=0`

## 5. Interpretation

- `PASS` validates a local transported chart on the workshop intersecting-pairs parent.
- Pair persistence is architecture-specific and is not imposed on UR-like chains.
- This does not authorize a fiber.
