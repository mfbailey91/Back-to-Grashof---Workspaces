# ADR 002 — Compound-tangent tests were non-discriminating

**Status:** Accepted
**Date:** 2026-08-04
**Related check-in:** Check-in 3 (`CONTINUE WITH CHANGED SCOPE`)

## Context

Sprint 03 compared physical `N_red` with an embedded compound basis formed from `ker(J_p[:, :5])`. Principal angles were zero and short `N_red` steps agreed. That result was initially treated as local C9 evidence for `UA=(R1,R2)`, `UB=(R3,R4)`.

Those tests do not depend on pair-intersection geometry. After the terminal-roll quotient, the fixed-`q6` null space of `J_p` is the same object as `N_red` by construction.

## Decision

- Do not interpret ATR_EXP_013–014 as independent compound-joint equivalence.
- Treat `SUUR` as a proposed exact kinematic regrouping until an explicit coordinate map and closure-equivalence test exist.
- Select `IntersectingPairsAligned6R` as the Sprint 04 continuation benchmark because it instantiates the workshop architecture, not because the non-discriminating tangent tests ranked it above UR-like.
- Before reading continuation through `SUUR`, require: explicit coordinate-map/closure tests; away-from-home pair persistence; a nonintersecting negative control; committed source identifiers on artifacts.

## Consequences

Sprint 04 may continue the physical 6R on `p(q)=p0`, `q6` constant, without claiming an established `SUUR` reduced mechanism. A07 remains open until the discriminating tests pass or fail.
