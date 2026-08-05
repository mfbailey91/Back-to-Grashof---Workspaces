# ATR_EXP_003 — Misaligned pointing-direction negative control

**Status:** Complete
**Date:** 2026-08-04
**Repository commit:** 0d27bb139c1a
**Related sprint:** Sprint 01 — Spatial Foundations
**Related claim IDs:** C3, C4 (negation)
**Random seed:** none

## 1. Purpose

Verify that tilting `d` away from `R6` while keeping `p` on-axis makes pointing vary under `q6` while position remains fixed.

## 2. Model

- model name: `TerminalRollFixture` misaligned N2
- task point: on-axis (aligned construction)
- pointing direction: tilted by `0.2 rad` from `w6`
- configuration: sweep `q6 ∈ [0, 2π]`

## 3. Parameters

| Parameter | Value | Units / interpretation |
|---|---:|---|
| tilt | 0.2 | rad from axis |

## 4. Numerical settings

Same motion floors as ATR_EXP_002.

## 5. Expected result

Position invariant; pointing changes.

## 6. Command

```bash
python scripts/validate_terminal_roll_fixture.py
```

## 7. Results

### Metrics

- position_changes: False
- pointing_changes: True
- max pointing residual: `3.973e-01`

### Figures

`results/aligned_terminal_roll/ATR_EXP_003/figures/residuals_vs_q6.png`

## 8. Sensitivity

Pointing residual amplitude is consistent with the commanded tilt (order `sin(tilt)` geometry).

## 9. Interpretation

- `PASS`

## 10. Follow-up

- next experiment: ATR_EXP_004
