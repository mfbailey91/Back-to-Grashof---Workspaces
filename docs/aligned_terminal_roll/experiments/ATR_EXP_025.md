# ATR_EXP_025 — Rectangular-loop refinement

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H4, H5
**Random seed:** none
**Implementation commit:** `e179ead`

## 1. Purpose

Continue the commutator `+s +t -s -t` at two step sizes with the same step count, so the refined loop is smaller.

## 2. Expected result

Closure error decreases when the step is halved. Exact closure is not required.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

- status: PASS
- observed: IP `3.301e-04 → 4.067e-05`; UR-like `3.792e-05 → 4.779e-06`

## 5. Interpretation

- `PASS` shows loop error scales down with step size / loop area.
- Residual closure is geometric holonomy on a curved manifold, not a failed return to a flat chart.
