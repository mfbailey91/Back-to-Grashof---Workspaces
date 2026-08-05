# ATR_EXP_014 — Local N_red step probes

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 03 — Architecture comparison
**Related claim IDs:** C9 (local)
**Random seed:** none

## 1. Purpose

Probe local continued motion along unit `N_red` for the physical 6R and the embedded compound model.

## 2. Model

- model name: `IntersectingPairsAligned6R`
- steps: 3 explicit Euler steps of `dt = 1e-3` rad
- corrector: Newton on `p(q)=p0` only, `q6` frozen
- not a predictor-corrector manifold solver

## 3. Expected result

Position residual stays near `p0`; pointing increments of physical and compound models agree within `1e-8`.

## 4. Command

```bash
python scripts/validate_architecture_comparison.py
```

## 5. Results

- status: PASS
- observed: `max_p_residual_m=1.57e-16`, `max_pointing_diff=0`
- artifacts: `results/aligned_terminal_roll/ATR_EXP_014/`

## 6. Interpretation

- `PASS` numerically, but Check-in 3 rules the test **non-discriminating**.
- Identical short trajectories are expected once both models step in the same fixed-roll null space.
- Do not treat this as independent local C9 / `SUUR` evidence.
