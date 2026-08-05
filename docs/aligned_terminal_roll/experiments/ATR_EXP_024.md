# ATR_EXP_024 — Grid and step-size consistency

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04B / 04C amendment
**Related claim IDs:** C10, H5
**Random seed:** none

## 1. Purpose

Compare baseline `9×9` / `0.03`, fine `17×17` / `0.015`, and compact `9×9` / `0.015` sequential charts on both architectures.

## 2. Expected result

Shared-node `q`/`d` agree within configured tolerances. Rank classifications remain two. Agreement is interpreted as deterministic macro-grid consistency under a shared internal microstep, not independent numerical refinement.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

Recorded after the Sprint 04C clean implementation commit.

## 5. Interpretation

Baseline and fine grids agree exactly at shared coordinates because both resolve to the same internal `0.005` continuation microstep sequence. This establishes deterministic consistency between the two macro-grid descriptions, but it is not an independent numerical-refinement result.

Retain ATR_EXP_025 as the primary step-refinement evidence.
