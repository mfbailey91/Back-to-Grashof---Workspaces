# ATR_EXP_024 — Grid and step-size refinement

**Status:** Ready
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H5
**Random seed:** none

## 1. Purpose

Compare baseline `9×9` / `0.03`, fine `17×17` / `0.015`, and compact `9×9` / `0.015` sequential charts on both architectures.

## 2. Expected result

Shared-node `q`/`d` agree within `1e-4` rad / `1e-6` pointing. Rank classifications remain two under all three grids.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

Recorded after the clean implementation commit.

## 5. Interpretation

A pass supports local chart stability under refinement, not path-independent finite coordinates.
