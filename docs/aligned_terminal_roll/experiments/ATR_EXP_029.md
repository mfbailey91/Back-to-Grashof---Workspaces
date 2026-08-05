# ATR_EXP_029 — UR-like sequential fiber

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 05 — Explicit one-dimensional fiber
**Related claim IDs:** C11, H2, H3, H4, H6
**Random seed:** none
**Implementation commit:** `9eaf0ff`

## 1. Purpose

Repeat the primary fiber continuation on `URLikeAligned6R` with the same general API and without `SUUR` or pair-distance gates.

## 2. Expected result

Same C11 gates as ATR_EXP_028. Pair/`SUUR` fields are not required.

## 3. Command

```bash
python scripts/validate_pointing_fiber.py
```

## 4. Results

- status: PASS
- observed: 9 accepted samples, 0 failed; reverse `eq=2.741e-09`, `ed=1.888e-09`, from endpoint; image `dmax=1.641e-01`, local pointing tangent nonzero

## 5. Interpretation

- `PASS` shows the fiber API is architecture-general. It does not authorize exact UR/URDF conclusions.
