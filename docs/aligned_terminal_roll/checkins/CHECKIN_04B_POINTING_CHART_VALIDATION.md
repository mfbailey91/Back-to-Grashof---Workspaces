# Check-in 4B — Pointing-chart validation

**Date:** 2026-08-04
**Milestone:** M4B — Validated local two-dimensional pointing chart
**Sprint(s):** Sprint 04B — Sequential continuation and pointing-chart validation
**Repository commit:** `e179ead` (original 04B implementation); documentation amended and artifacts regenerated at `82622cf` (Sprint 04C)
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
| ATR_EXP_024 | Macro-grid consistency (shared microstep) | PASS |
| ATR_EXP_025 | Rectangular-loop refinement | PASS |
| ATR_EXP_026 | Alternate-path and duplicates | PASS |

Sprint 04C regenerated manifests record `repository_commit=82622cf`, `working_tree_dirty=false`, and `source_identifier=…:sprint04c-v1`. Numerical PASS/FAIL outcomes are unchanged from the 04B runs.

## 4. Interpretation

**SUPPORTED locally, pending human gate.**

Both synthetic architectures admit a sequential local chart that is regular, reversible from the true forward endpoint, rank-two in both configuration and pointing differentials, and free of duplicates. Intersecting-pair distances remain zero on the IP patch. UR-like continuation uses the same API without `SUUR` or pair diagnostics.

ATR_EXP_024 shows deterministic macro-grid consistency: baseline and fine shared nodes agree because both use the same internal `0.005` microstep. That is not independent numerical refinement. ATR_EXP_025 remains the primary step-refinement evidence.

Alternate-path discrepancies are small and stable. They are compatible with finite-path noncommutativity of the transported chart and do not independently establish geometric holonomy. Exact closure and path independence are not claimed.

Recommended check-in case: **A — both architectures pass.**

## 5. Decision

**Pending human review.**

If approved as Case A: authorize Sprint 05 with `IntersectingPairsAligned6R` as the controlled primary fiber benchmark and `URLikeAligned6R` as the practical parallel architecture.

Still blocked: spherical `RRRR`, McCarthy–Soh, exact UR/URDF, and global dexterity.

## 6. Next sprint recommendation

After human approval of Case A or B **and** Check-in 04C, open Sprint 05 for one scalar constraint `h(q)=c`.
