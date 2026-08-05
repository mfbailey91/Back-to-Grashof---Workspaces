# ATR_EXP_002 — Off-axis task-point negative control

**Status:** Complete
**Date:** 2026-08-04
**Repository commit:** 0d27bb139c1a
**Related sprint:** Sprint 01 — Spatial Foundations
**Related claim IDs:** C3 (negation), C4
**Random seed:** none

## 1. Purpose

Verify that a transverse offset of the task point causes `q6` to move `p` while axis-aligned pointing remains invariant.

## 2. Model

- model name: `TerminalRollFixture` off-axis N1
- axis definitions: same as ATR_EXP_001
- task point: aligned point plus transverse offset `0.02 m`
- pointing direction: parallel to `w6`
- configuration: sweep `q6 ∈ [0, 2π]`
- units: metres, radians

## 3. Parameters

| Parameter | Value | Units / interpretation |
|---|---:|---|
| transverse_offset | 0.02 | m |

## 4. Numerical settings

| Setting | Value |
|---|---:|
| position motion floor | 1e-6 m |
| pointing motion floor | 1e-6 |

## 5. Expected result

Position changes; pointing invariant.

## 6. Command

```bash
python scripts/validate_terminal_roll_fixture.py
```

## 7. Results

### Metrics

- position_changes: True
- pointing_changes: False
- max position residual: `4.000e-02` m (diameter of circular orbit)

### Figures

`results/aligned_terminal_roll/ATR_EXP_002/figures/residuals_vs_q6.png`

## 8. Sensitivity

Orbit radius equals the commanded transverse offset, confirming the metric is not loose.

## 9. Interpretation

- `PASS`

## 10. Follow-up

- next experiment: ATR_EXP_003
