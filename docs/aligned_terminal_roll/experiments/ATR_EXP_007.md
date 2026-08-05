# ATR_EXP_007 — Jacobian finite-difference refinement

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 02
**Related claim IDs:** C6, C7

## 1. Purpose

Compare analytical `J_p` and `J_d` to central finite differences over multiple `h`.

## 2. Expected result

Error decreases as `O(h^2)` until round-off.

## 3. Command

```bash
python scripts/validate_aligned_6r_reduction.py
```

## 4. Results

PASS. Errors drop from `~1e-5` at `h=1e-2` to `~1e-11` at `h=1e-5`, with mild round-off at `h=1e-6`.

## 5. Interpretation

- `PASS`
