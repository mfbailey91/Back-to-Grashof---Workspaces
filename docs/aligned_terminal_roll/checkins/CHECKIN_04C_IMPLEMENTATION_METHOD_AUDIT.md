# Check-in 04C — Implementation and method audit

**Date:** 2026-08-04
**Milestone:** Pre-approval amendment to M4B
**Sprint(s):** Sprint 04C — Bounded implementation and method audit
**Repository commit:** `82622cf` (implementation); artifacts regenerated from that clean revision
**Decision owner:** Michael Bailey
**Decision status:** Approved 2026-08-04 — Pass

## 1. Claim under review

The Sprint 04B sequential-chart implementation is documented, its methods are valid for the local C10 claims actually tested, and the ATR_EXP_024 / ATR_EXP_026 descriptions no longer overclaim refinement or holonomy.

This check-in does **not** claim fibers, spherical `RRRR`, McCarthy–Soh, exact UR, or global pointing coverage.

## 2. What was implemented

- Relocated sprint note: `docs/aligned_terminal_roll/sprints/SPRINT_04C_IMPLEMENTATION_METHOD_AUDIT.md`
- `IMPLEMENTATION_RATIONALE.md`, `METHOD_REFERENCES.md`
- ATR_EXP_024/026 claim and field corrections (`discrepancy_stable_or_decreased`; macro-grid consistency metrics)
- Updated Check-in 4B interpretation; no auto-approval

## 3. Audit findings

| Item | Finding |
|---|---|
| Sequential PC and Procrustes transport | Appropriate local continuation methods; reverse starts at the forward endpoint |
| Chart ranks `Q` and `D` | Independent central-difference diagnostics of numerical dimension two |
| ATR_EXP_024 | Exact shared-node agreement is shared-microstep consistency, not independent refinement |
| ATR_EXP_025 | Remains the primary step-refinement evidence (`max_microstep=None`) |
| ATR_EXP_026 | No duplicates; discrepancy small and stable; not a holonomy proof |
| SUUR / pairs | Remain IP-only diagnostics; general continuation API does not impose them |
| Developer-only paths | Sprint 04 HTML readout, seed-frozen patch, compound-tangent probes — labeled |

Accepted Sprint 04B numerical PASS/FAIL outcomes are unchanged. Only interpretation and stored field names changed.

## 4. Interpretation

**SUPPORTED as a documentation and claim-correction amendment.**

The local sequential chart evidence in Check-in 4B can be reviewed honestly: reversible rank-two noncollapsed patches on both architectures, with refinement understood through ATR_EXP_025 and with 024/026 language matched to the actual tests.

## 5. Decision

**APPROVED — Pass**

The method audit is accepted. ATR_EXP_024/026 interpretations stand. Sprint 05 is authorized together with Check-in 4B Case A, using `IntersectingPairsAligned6R` as the primary fiber benchmark and `URLikeAligned6R` as the parallel architecture.

Still blocked: spherical `RRRR`, McCarthy–Soh, exact UR/URDF, and global dexterity.

## 6. Next sprint recommendation

Review `SPRINT_05_EXPLICIT_ONE_DIMENSIONAL_FIBER.md`, then implement one independent scalar constraint.
