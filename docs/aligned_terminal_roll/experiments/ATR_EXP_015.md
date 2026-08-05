# ATR_EXP_015 — Three-architecture comparison

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 03 — Architecture comparison
**Related claim IDs:** C6, C7, C8, C9 (local), A07, A08
**Random seed:** none

## 1. Purpose

Summarize Stage A survival across the three synthetic architectures and record the local C9 result plus a continuation-parent recommendation.

## 2. Models

- `GenericAligned6R` (Stage A baseline; no re-derivation)
- `IntersectingPairsAligned6R` (literal compound-joint parent)
- `URLikeAligned6R` (practical ordering check)

## 3. Expected result

Stage A survives all three. Local C9 is reported for intersecting pairs. Continuation parent is recorded as `IntersectingPairsAligned6R` but not auto-selected.

## 4. Command

```bash
python scripts/validate_architecture_comparison.py
```

## 5. Results

- status: PASS
- observed: Stage A on all three; local C9 true; recommended parent `IntersectingPairsAligned6R`; `auto_selected=false`
- artifacts: `results/aligned_terminal_roll/ATR_EXP_015/`

## 6. Interpretation

- `PASS` authorizes a Check-in 3 draft only.
- Human gate required before Sprint 04 continuation.
