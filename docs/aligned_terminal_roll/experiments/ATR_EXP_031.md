# ATR_EXP_031 — Fiber step refinement

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 05 — Explicit one-dimensional fiber
**Related claim IDs:** C11, H3
**Random seed:** none
**Implementation commit:** TBD (regenerate after clean commit)

## 1. Purpose

Repeat forward/reverse fiber tracking at `Δσ = 0.03` (4 steps) and `Δσ = 0.015` (8 steps) over the same `σ` travel with `max_microstep=None`.

## 2. Expected result

Reverse tracking succeeds on both grids. Joint and pointing return errors decrease when the step is halved. Shared-`σ` samples agree within `1e-3`. This is independent integrator-step refinement, not shared-microstep consistency.

## 3. Command

```bash
python scripts/validate_pointing_fiber.py
```

## 4. Results

- status: PASS
- observed: IP `6.295e-06 → 7.884e-07`, shared `dq=6.426e-05`; UR-like `5.915e-07 → 7.399e-08`, shared `dq=3.310e-05`

## 5. Interpretation

- `PASS` shows the no-microstep integrator converges under refinement. Tight reverse gates in ATR_EXP_028/029 use the default internal microstep and are a different diagnostic.
