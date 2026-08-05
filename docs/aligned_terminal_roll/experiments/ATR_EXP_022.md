# ATR_EXP_022 — Intersecting-pairs transported chart

**Status:** Ready
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H1, H2, H3, H6
**Random seed:** none

## 1. Purpose

Build a row-wise sequential `(s,t)` chart on `IntersectingPairsAligned6R` with Procrustes-aligned `N_red` at each accepted sample.

## 2. Expected result

100% regular approved patch; `rank(Q)=rank(D)=2` at every interior node; no duplicates or failed samples; pair intersections persist. Pair distances are architecture-specific diagnostics, not part of the general continuation API.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

Recorded after the clean implementation commit.

## 5. Interpretation

A pass validates a local transported chart on the workshop intersecting-pairs parent. It does not authorize a fiber.
