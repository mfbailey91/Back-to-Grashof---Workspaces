# ATR_EXP_017 — Nonintersecting negative control

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04 — Pointing manifold
**Related claim IDs:** C9, ADR 002
**Random seed:** none

## 1. Purpose

Show that the Sprint 03 compound-tangent comparison does not test UA/UB geometry.

## 2. Expected result

On `GenericAligned6R`, pair distances are positive, `φ` is undefined, and the old principal-angle test remains ~0.

## 3. Command

```bash
python scripts/validate_pointing_manifold.py
```

## 4. Results

- status: PASS
- observed: `dist_ua=1.535e-02`, `dist_ub=1.386e-01`, `phi_defined=False`, old max angle `0`

## 5. Interpretation

- `PASS` demonstrates that ATR_EXP_013 was non-discriminating.
