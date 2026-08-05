# ATR_EXP_004 — Combined alignment violation

**Status:** Complete
**Date:** 2026-08-04
**Repository commit:** 0d27bb139c1a
**Related sprint:** Sprint 01 — Spatial Foundations
**Related claim IDs:** C3 (negation), C4 (negation)
**Random seed:** none

## 1. Purpose

Verify that simultaneous off-axis point and misaligned pointing cause both position and pointing to change under `q6`.

## 2. Model

- model name: `TerminalRollFixture` combined N3
- task point: transverse offset `0.02 m`
- pointing direction: tilt `0.2 rad`
- configuration: sweep `q6 ∈ [0, 2π]`

## 3. Parameters

| Parameter | Value | Units / interpretation |
|---|---:|---|
| transverse_offset | 0.02 | m |
| tilt | 0.2 | rad |

## 4. Numerical settings

Same motion floors as ATR_EXP_002.

## 5. Expected result

Position and pointing both change.

## 6. Command

```bash
python scripts/validate_terminal_roll_fixture.py
```

## 7. Results

### Metrics

- position_changes: True
- pointing_changes: True

### Figures

`results/aligned_terminal_roll/ATR_EXP_004/figures/residuals_vs_q6.png`

## 8. Sensitivity

Combined violation does not mask either individual failure mode.

## 9. Interpretation

- `PASS`

## 10. Follow-up

- next experiment: ATR_EXP_005
