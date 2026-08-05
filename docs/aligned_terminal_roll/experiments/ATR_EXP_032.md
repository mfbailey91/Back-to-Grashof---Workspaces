# ATR_EXP_032 — Duplicate scan on all four candidate fibers

**Status:** Complete
**Date:** 2026-08-05
**Related sprint:** Sprint 06 — Candidate spherical equivalence
**Related claim IDs:** C12, H1
**Random seed:** none
**Implementation commit:** dirty working tree on `35630c3`

## 1. Purpose

Scan every accepted station of the four Check-in 5 candidate fibers for wrap-equivalent repeated configurations at distinct `σ`.

## 2. Expected result

No wrap-equivalent repeats at distinct `σ`, or a labeled unresolved / Case D result.

## 3. Command

```bash
python scripts/validate_spherical_candidates.py
```

## 4. Results

- status: PASS
- observed: all four candidates, 9 stations each, 0 duplicates; min nearest-neighbor wrap distance about `0.03` rad

## 5. Interpretation

- `PASS` clears H1 on the local continued segments. It does not establish spherical `RRRR` geometry.
