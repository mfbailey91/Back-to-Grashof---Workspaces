# ATR_EXP_033 — IP primary S−UA−UB−R5 invariants

**Status:** Complete
**Date:** 2026-08-05
**Related sprint:** Sprint 06 — Candidate spherical equivalence
**Related claim IDs:** C12, H2, H3, H4
**Random seed:** none
**Implementation commit:** dirty working tree on `35630c3`

## 1. Purpose

Test topology-derived `S−UA−UB−R5` global-center concurrency, fixed-center drift, cycle-arc invariance, and body-fixed effective-axis legitimacy on the intersecting-pairs primary fiber `n=(0,1,0)`.

## 2. Expected result

A named residual report: `exact`, `approximate`, `fail`, or `unresolved`. Simple coordinate locking is diagnostic only. Body-fixed axis invariance is the legitimacy gate.

## 3. Command

```bash
python scripts/validate_spherical_candidates.py
```

## 4. Results

- status: PASS (complete residual report)
- candidate verdict: `fail`
- construction: `s_ua_ub_r5`
- observed: `c*_rms=2.477e-01 m`, `c*_max=3.338e-01 m`, `drift=9.175e-02 m`, `arc=7.714e-01 rad`, `body_fixed=5.109e-01 rad`, `simple_lock=False`, `locking=fail`
- simple-lock ranges (rad): `q1=0.0863`, `q2=0.0428`, `q3=0.0948`, `q4=0.1951`, `q5=0.0198`

## 5. Interpretation

- This primary slice is not an exact spherical `RRRR` under the named topology-derived axes.
- The candidate fails global concurrency, fixed-center drift, arcs, and body-fixed legitimacy. Simple locking also fails, as expected.
- Terminal-roll reduction and local fiber existence stand.
- Do not apply McCarthy–Soh. Do not infer that no spherical fiber exists.
