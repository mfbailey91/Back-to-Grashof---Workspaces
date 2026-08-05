# ATR_EXP_026 — Alternate-path and duplicate analysis

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04B / 04C amendment
**Related claim IDs:** C10, H5
**Random seed:** none

## 1. Purpose

Compare `s`-then-`t` versus `t`-then-`s` arrivals at a selected interior target, and scan the sequential chart for duplicate configurations.

## 2. Expected result

No duplicate wrapped-`q` samples. Alternate-path discrepancy is small and `discrepancy_stable_or_decreased` under the tested step pair.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

Recorded after the Sprint 04C clean implementation commit.

## 5. Interpretation

No duplicate solutions were detected. Alternate-path discrepancies remain small and stable under the tested refinement. The results are compatible with finite-path noncommutativity of the transported chart, but do not independently establish geometric holonomy.
