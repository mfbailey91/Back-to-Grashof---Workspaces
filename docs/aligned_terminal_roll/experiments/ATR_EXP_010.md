# ATR_EXP_010 — Seeded survey and named near-singular sample

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 02
**Related claim IDs:** C6, C7, C8
**Random seed:** 17

## 1. Purpose

Check that regular samples support the reduction identities and that a poorer-conditioned sample is labeled separately rather than treated as a generic failure.

## 2. Expected result

Regular subset satisfies C6–C8. Named sample is singular or near-singular.

## 3. Results

- survey: 48/48 regular under the published rank threshold
- no exact `rank(J_p)<3` sample in the survey
- named near-singular: `σ_min/σ_max = 1.43e-2` versus median regular `2.24e-1`

## 4. Interpretation

- `PASS`

Exact position singularities of this generic skew 6R were not hit by uniform sampling; the named sample is reported as near-singular.
