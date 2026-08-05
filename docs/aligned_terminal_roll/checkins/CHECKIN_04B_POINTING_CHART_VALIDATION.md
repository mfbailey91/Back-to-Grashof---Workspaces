# Check-in 4B — Pointing-chart validation

**Date:** 2026-08-04
**Milestone:** M4B — Validated local two-dimensional pointing chart
**Sprint(s):** Sprint 04B — Sequential continuation and pointing-chart validation
**Repository commit:** pending clean implementation commit
**Decision owner:** Michael Bailey
**Decision status:** Draft — awaiting human review after artifact regeneration

## 1. Claim under review

Sequential predictor-corrector continuation of

```text
p(q) = p0
q6 = constant
```

with a Procrustes-aligned reduced tangent frame at each accepted sample produces a reversible, rank-two, noncollapsed local chart of the fixed-position pointing manifold on `IntersectingPairsAligned6R` and `URLikeAligned6R`.

This check-in does **not** claim fibers, spherical `RRRR`, McCarthy–Soh, exact UR, or global pointing coverage.

## 2. What was implemented

- Software: sequential continuation in `continuation.py`, `continuation_paths.py`, `chart_diagnostics.py`, `chart_experiments.py`
- Validation: ATR_EXP_021–026
- Runner: `scripts/validate_pointing_chart.py`
- HTML readout remains a developer diagnostic only

## 3. Experiments reviewed

| Experiment | Purpose | Result |
|---|---|---|
| ATR_EXP_021 | Sequential forward/reverse | pending regeneration |
| ATR_EXP_022 | IP transported chart | pending regeneration |
| ATR_EXP_023 | UR-like transported chart | pending regeneration |
| ATR_EXP_024 | Grid/step refinement | pending regeneration |
| ATR_EXP_025 | Rectangular-loop refinement | pending regeneration |
| ATR_EXP_026 | Alternate-path and duplicates | pending regeneration |

## 4. Interpretation

Draft. Fill after decision-bearing artifacts are regenerated from a clean commit.

## 5. Decision

**Pending human review.**

Check-in 4B cases:

- A — both architectures pass → authorize Sprint 05 with IP primary and UR-like parallel
- B — IP only → fiber work on IP only
- C — UR-like only → do not start the compound-topology fiber program
- D — rank loss under refinement → no Sprint 05
- E — reverse or duplicates fail → branch tracking unresolved

## 6. Next sprint recommendation

If Case A or B is selected after review, open Sprint 05 for one scalar constraint `h(q)=c`. Still blocked: spherical `RRRR`, McCarthy–Soh, exact UR/URDF, global dexterity.
