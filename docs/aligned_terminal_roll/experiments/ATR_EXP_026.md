# ATR_EXP_026 — Alternate-path and duplicate analysis

**Status:** Ready
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H5
**Random seed:** none

## 1. Purpose

Compare `s`-then-`t` versus `t`-then-`s` arrivals at a selected interior target, and scan the sequential chart for duplicate configurations.

## 2. Expected result

No duplicate wrapped-`q` samples. Path discrepancy shrinks under step refinement or is already at the geometric noncommutativity floor (relative change `≤ 5%` and absolute discrepancy `≤ 5e-4` rad).

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

Recorded after the clean implementation commit.

## 5. Interpretation

A pass supports local injectivity of the sampled chart. Exact path independence over a finite curved patch is not claimed.
