# ATR_EXP_025 — Rectangular-loop refinement

**Status:** Ready
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H4, H5
**Random seed:** none

## 1. Purpose

Continue the commutator `+s +t -s -t` at two step sizes with the same step count, so the refined loop is smaller.

## 2. Expected result

Closure error decreases when the step is halved. Exact closure is not required; the loop is an integration / frame-transport diagnostic on a curved manifold.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

Recorded after the clean implementation commit.

## 5. Interpretation

A pass shows loop error scales down with step size. Residual closure is geometric holonomy, not a failed return to a flat chart.
