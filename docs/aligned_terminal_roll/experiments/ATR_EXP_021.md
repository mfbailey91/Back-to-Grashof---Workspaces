# ATR_EXP_021 — Sequential forward/reverse rays

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H4
**Random seed:** none
**Implementation commit:** `e179ead`

## 1. Purpose

Continue sequentially along each chart axis on both architectures, then reverse from the accepted endpoint with the transported tangent frame.

## 2. Expected result

Return within `1e-6` rad joint wrap-norm and `1e-8` pointing residual. The reverse run must start at the forward endpoint.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

- status: PASS
- observed: IP `s` `ε_q=1.010e-08` `ε_d=6.882e-09`; IP `t` `ε_q=1.967e-08` `ε_d=5.933e-09`; UR-like `s` `ε_q=1.678e-10` `ε_d=1.199e-10`; UR-like `t` `ε_q=1.402e-09` `ε_d=9.454e-10`; all reverse runs started from the forward endpoint

## 5. Interpretation

- `PASS` supports reversible sequential branch tracking on the local patch.
- This is not a global connectedness claim.
