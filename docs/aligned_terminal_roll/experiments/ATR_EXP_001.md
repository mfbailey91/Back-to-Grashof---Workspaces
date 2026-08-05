# ATR_EXP_001 — Aligned terminal-roll positive control

**Status:** Complete
**Date:** 2026-08-04
**Repository commit:** 0d27bb139c1a
**Related sprint:** Sprint 01 — Spatial Foundations
**Related claim IDs:** C1, C2, C3, C4, C5
**Random seed:** none (deterministic fixture)

## 1. Purpose

Verify that when the task point lies on `R6` and the pointing direction is parallel to `R6`, joint `q6` preserves position and pointing while changing full tool orientation by roll about `d`.

## 2. Model

- model name: `TerminalRollFixture` aligned positive control
- axis definitions: `r6 = (0.1, -0.2, 0.3) m`, `w6 = (0, 0, 1)`
- task point: on-axis with axial offset `0.05 m`
- pointing direction: exactly `w6`
- configuration: sweep `q6 ∈ [0, 2π]`
- units: metres, radians
- expected regular or singular status: regular by construction (single revolute)

## 3. Parameters

| Parameter | Value | Units / interpretation |
|---|---:|---|
| axial_offset | 0.05 | m |
| sweep samples | 361 | inclusive full revolution |

## 4. Numerical settings

| Setting | Value |
|---|---:|
| absolute position tolerance | 1e-12 m |
| absolute pointing tolerance | 1e-12 |
| roll absolute tolerance | 1e-10 rad |

## 5. Expected result

Position invariant; pointing invariant; recovered roll angle matches commanded `Δq6`.

## 6. Command

```bash
python scripts/validate_terminal_roll_fixture.py
```

Artifacts: `results/aligned_terminal_roll/ATR_EXP_001/`

## 7. Results

### Metrics

- max position residual: `0` m
- max pointing residual: `0`
- max roll angle error: `1.332e-15` rad

### Residuals

See `metrics.csv` and `figures/residuals_vs_q6.png`.

### Singular values

Not applicable (fixture has no multi-joint Jacobian).

### Figures

`results/aligned_terminal_roll/ATR_EXP_001/figures/residuals_vs_q6.png`

## 8. Sensitivity

Residuals remain at machine precision across the full sweep; no step-size dependence for the kinematic identity.

## 9. Interpretation

Select one:

- `PASS`

Positive control matches the aligned-terminal hypothesis on the isolated fixture.

## 10. Follow-up

- project-plan implication: Level-0 positive control established
- risk-register updates: A01, A02, R01, R04 supported for this fixture
- next experiment: ATR_EXP_002
