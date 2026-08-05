# ATR_EXP_035 — UR-like duplicate scan and exploratory tuples

**Status:** Complete (exploratory)
**Date:** 2026-08-05
**Related sprint:** Sprint 06 — Candidate spherical equivalence
**Related claim IDs:** C12, H1
**Random seed:** none
**Implementation commit:** dirty working tree on `35630c3`

## 1. Purpose

Duplicate-scan the UR-like primary and alternate fibers and run a fixed physical four-subset scan of `R1…R5` as an exploratory diagnostic. Do not claim exact `RRRR`.

## 2. Expected result

Duplicate scans complete; `axes_construction = exploratory_fixed_physical_subset`; `exact_rrrr_claim = false`; no `SUUR` required. Each tuple is held fixed across the branch.

## 3. Command

```bash
python scripts/validate_spherical_candidates.py
```

## 4. Results

- status: PASS
- observed: both fibers 0 duplicates
- exploratory best fixed tuple on both fibers: `R1-R2-R3-R4` with `global_max ≈ 0.15 m`
- no exact `RRRR` claim

## 5. Interpretation

- UR-like remains a parallel comparison only. A physical-subset scan is not a topology-derived spherical four-bar.
- Possible Check-in 6 Case E: architecture-limited spherical claim; do not generalize to exact UR.
