# Check-in 4B — Pointing-chart validation

**Date:** 2026-08-04
**Milestone:** M4B — Validated local two-dimensional pointing chart
**Sprint(s):** Sprint 04B — Sequential continuation and pointing-chart validation
**Repository commit:** `e179ead` (implementation); artifacts regenerated from that clean revision
**Decision owner:** Michael Bailey
**Decision status:** Draft — awaiting human review

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
| ATR_EXP_021 | Sequential forward/reverse | PASS |
| ATR_EXP_022 | IP transported chart | PASS |
| ATR_EXP_023 | UR-like transported chart | PASS |
| ATR_EXP_024 | Grid/step refinement | PASS |
| ATR_EXP_025 | Rectangular-loop refinement | PASS |
| ATR_EXP_026 | Alternate-path and duplicates | PASS |

All manifests record `repository_commit=e179ead` and `working_tree_dirty=false`.

## 4. Interpretation

**SUPPORTED locally, pending human gate.**

Both synthetic architectures admit a sequential local chart that is regular, reversible from the true forward endpoint, rank-two in both configuration and pointing differentials, free of duplicates, and stable under grid/step refinement. Intersecting-pair distances remain zero on the IP patch. UR-like continuation uses the same API without `SUUR` or pair diagnostics.

Residual rectangular-loop and alternate-path discrepancies are small and consistent with curvature / holonomy on a finite patch. Exact closure and path independence are not claimed.

Recommended check-in case: **A — both architectures pass.**

## 5. Decision

**Pending human review.**

If approved as Case A: authorize Sprint 05 with `IntersectingPairsAligned6R` as the controlled primary fiber benchmark and `URLikeAligned6R` as the practical parallel architecture.

Still blocked: spherical `RRRR`, McCarthy–Soh, exact UR/URDF, and global dexterity.

## 6. Next sprint recommendation

After human approval of Case A or B, open Sprint 05 for one scalar constraint `h(q)=c`.
