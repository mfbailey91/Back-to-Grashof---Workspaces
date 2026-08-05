# ATR_EXP_028 — Intersecting-pairs sequential fiber

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 05 — Explicit one-dimensional fiber
**Related claim IDs:** C11, H2, H3, H4
**Random seed:** none
**Implementation commit:** `9eaf0ff`

## 1. Purpose

Continue the primary fiber `h = n · d = c` on `IntersectingPairsAligned6R` with sequential predictor-corrector steps, then reverse from the accepted endpoint.

## 2. Expected result

Zero failed samples on the ±4×0.03 benchmark; reverse within `1e-6` rad / `5e-8` pointing; pointing image noncollapsed with a nonzero local `∂d/∂σ`.

## 3. Command

```bash
python scripts/validate_pointing_fiber.py
```

## 4. Results

- status: PASS
- observed: 9 accepted samples, 0 failed; reverse `eq=2.922e-08`, `ed=7.525e-09`, from endpoint; image `dmax=6.150e-02`, local pointing tangent nonzero

## 5. Interpretation

- `PASS` is a local C11 fiber on IP. It is not a spherical `RRRR` claim.
