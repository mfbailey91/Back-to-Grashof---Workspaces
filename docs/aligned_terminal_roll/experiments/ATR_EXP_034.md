# ATR_EXP_034 — IP alternate S−UA−UB−R5 invariants

**Status:** Complete
**Date:** 2026-08-05
**Related sprint:** Sprint 06 — Candidate spherical equivalence
**Related claim IDs:** C12, H2, H3, H4
**Random seed:** none
**Implementation commit:** dirty working tree on `35630c3`

## 1. Purpose

Repeat the topology-derived global-center, arc, and body-fixed tests on the intersecting-pairs alternate fiber `n'=(1,0,0)`.

## 2. Expected result

A named residual report: `exact`, `approximate`, `fail`, or `unresolved`.

## 3. Command

```bash
python scripts/validate_spherical_candidates.py
```

## 4. Results

- status: PASS (complete residual report)
- candidate verdict: `fail`
- construction: `s_ua_ub_r5`
- observed: `c*_rms=1.597e-01 m`, `c*_max=3.105e-01 m`, `drift=7.589e-02 m`, `arc=8.617e-01 rad`, `body_fixed=5.859e-01 rad`, `simple_lock=False`, `locking=fail`

## 5. Interpretation

- This alternate slice is not an exact spherical `RRRR` under the named topology-derived axes.
- Failure of `n'` does not rule out other untested slices.
- Do not apply McCarthy–Soh.
