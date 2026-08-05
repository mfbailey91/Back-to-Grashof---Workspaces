# ATR_EXP_023 — UR-like transported chart

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H1, H2, H3, H6, A08
**Random seed:** none
**Implementation commit:** `e179ead`

## 1. Purpose

Run the same sequential chart interface on `URLikeAligned6R` without imposing `SUUR` or pair diagnostics.

## 2. Expected result

Same C10 chart gates as ATR_EXP_022. No `suur_map` or pair-distance fields required.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

- status: PASS
- observed: `regular=81/81`, `rejected=0`, `interior=49`, `rankQ2=49`, `rankD2=49`, `duplicates=0`

## 5. Interpretation

- `PASS` is synthetic UR-like chart evidence only, not exact UR.
- Pair/`SUUR` fields are recorded as `not_applicable`.
