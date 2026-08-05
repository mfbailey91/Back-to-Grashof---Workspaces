# ATR_EXP_020 — UR-like continuation patch

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04 — Pointing manifold
**Related claim IDs:** C10, A08
**Random seed:** none

## 1. Purpose

Run the same continuation interface on `URLikeAligned6R`.

## 2. Expected result

Local 2D regular subset with rank-two pointing away from labeled singular samples. No SUUR map is required.

## 3. Command

```bash
python scripts/validate_pointing_manifold.py
```

## 4. Results

- status: PASS
- observed: `regular=81/81`, `max_p=9.845e-15`, `reverse_err=0`

## 5. Interpretation

- `PASS` is a synthetic UR-like C10 check only, not exact UR.
