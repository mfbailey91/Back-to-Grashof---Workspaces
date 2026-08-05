# ATR_EXP_005 — Finite-difference derivative refinement

**Status:** Complete
**Date:** 2026-08-04
**Repository commit:** 0d27bb139c1a
**Related sprint:** Sprint 01 — Spatial Foundations
**Related claim IDs:** C3, C4 (analytical/numerical agreement)
**Random seed:** none

## 1. Purpose

Verify that analytical `dp/dq6` and `dd/dq6` agree with central finite differences across multiple step sizes, with visible convergence on a usable `h` range.

## 2. Model

- model name: combined-violation fixture (nonzero derivatives)
- configuration: probe at `q6 = 0.3 rad`
- FD steps: `1e-2, 1e-3, 1e-4, 1e-5, 1e-6` rad

## 3. Parameters

| Parameter | Value | Units / interpretation |
|---|---:|---|
| probe q6 | 0.3 | rad |
| FD scheme | central | `[f(q+h)-f(q-h)]/(2h)` |

## 4. Numerical settings

| Setting | Value |
|---|---:|
| finite-difference steps | 1e-2 … 1e-6 rad |

## 5. Expected result

Derivative error decreases as `h` decreases until round-off; analytical and numerical derivatives agree.

## 6. Command

```bash
python scripts/validate_terminal_roll_fixture.py
```

## 7. Results

### Metrics

| h [rad] | dp_error | dd_error |
|---:|---:|---:|
| 1e-2 | 3.333e-07 | 3.311e-06 |
| 1e-3 | 3.333e-09 | 3.311e-08 |
| 1e-4 | 3.336e-11 | 3.312e-10 |
| 1e-5 | 4.699e-13 | 3.471e-12 |
| 1e-6 | 5.174e-12 | 3.713e-12 |

### Figures

`results/aligned_terminal_roll/ATR_EXP_005/figures/residuals_vs_q6.png`
plus `fd_refinement.csv`

## 8. Sensitivity

Error scales approximately as `O(h^2)` through `h = 1e-5`; the smallest step shows mild round-off inflation, as expected.

## 9. Interpretation

- `PASS`

## 10. Follow-up

- risk-register updates: R03 mitigated for Sprint 01 fixture
- next: Check-in 1
