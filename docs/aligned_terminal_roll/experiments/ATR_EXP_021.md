# ATR_EXP_021 — Sequential forward/reverse rays

**Status:** Ready
**Date:** 2026-08-04
**Related sprint:** Sprint 04B — Sequential continuation and pointing-chart validation
**Related claim IDs:** C10, H4
**Random seed:** none

## 1. Purpose

Continue sequentially along each chart axis on both architectures, then reverse from the accepted endpoint with the transported tangent frame.

## 2. Expected result

Return within `1e-6` rad joint wrap-norm and `1e-8` pointing residual. The reverse run must start at the forward endpoint.

## 3. Command

```bash
python scripts/validate_pointing_chart.py
```

## 4. Results

Recorded after the clean implementation commit.

## 5. Interpretation

A pass supports reversible sequential branch tracking locally. It is not a global connectedness claim.
