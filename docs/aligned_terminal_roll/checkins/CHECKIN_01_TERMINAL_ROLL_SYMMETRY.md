# Check-in 1 — Terminal-roll symmetry (fixture)

**Date:** 2026-08-04
**Milestone:** M1 — Terminal-roll symmetry established
**Sprint(s):** Sprint 01 — Spatial Foundations
**Repository commit:** 7b59b64
**Decision owner:** Michael Bailey
**Decision status:** Approved 2026-08-04

## 1. Claim under review

For an isolated revolute axis `R6 = (r6, w6)`, task point `p`, and unit pointing `d`, the geometric conditions

```text
distance(p, R6) = 0
d parallel w6
```

imply

```text
dp/dq6 = 0
dd/dq6 = 0
```

while full tool orientation changes by roll about `d`. This check-in does **not** claim dimensionality of a complete 6R fixed-position mechanism.

## 2. What was implemented

- Research: provisional aligned-terminal definition exercised; analytical `dp/dq6`, `dd/dq6` derived and implemented; full orientation vs pointing distinguished via relative rotation about `d`.
- Software: isolated package `grashof_workspace.spatial_experiments` (`axis_geometry`, `rotations`, `terminal_roll_fixture`, `diagnostics`) and runner `scripts/validate_terminal_roll_fixture.py`.
- Validation: ATR_EXP_001–005 with positive and negative controls, multi-`h` FD refinement, full `q6` sweep.
- Documentation: experiment records, this check-in draft, risk-register updates.

## 3. Experiments reviewed

| Experiment | Purpose | Result |
|---|---|---|
| ATR_EXP_001 | aligned positive control | PASS |
| ATR_EXP_002 | off-axis task point | PASS |
| ATR_EXP_003 | misaligned pointing | PASS |
| ATR_EXP_004 | combined violation | PASS |
| ATR_EXP_005 | FD refinement | PASS |

## 4. Acceptance-criteria results

| Criterion | Required | Observed | Status |
|---|---|---|---|
| Isolated under `spatial_experiments` | no planar / 6R coupling | package separate; no sixr import | PASS |
| Planar tests unchanged | trusted suite green | fourbar/planar3r/validation + spatial: 76 passed | PASS |
| Positive/negative qualitative behavior | Sprint matrix | all five PASS | PASS |
| Analytical vs FD | convergence | O(h²) then mild round-off | PASS |
| Orientation roll without Euler subtraction | relative R + probe atan2 | max roll err ~1e-15 rad | PASS |
| Explicit tolerances/units | documented | metres / radians in manifests | PASS |
| Experiment manifests/summaries | `results/aligned_terminal_roll/<id>/` | written | PASS |
| No 6R / spherical / continuation code | deferred | not introduced | PASS |

## 5. Evidence

### Metrics

- ATR_EXP_001: max `|Δp| = 0` m, max `|Δd| = 0`, max roll error `1.3e-15` rad
- ATR_EXP_002: max `|Δp| = 0.04` m with pointing invariant
- ATR_EXP_003: pointing changes with position invariant
- ATR_EXP_005: FD errors drop from `~1e-6` at `h=1e-2` to `~1e-12` near `h=1e-5`

### Figures

`results/aligned_terminal_roll/ATR_EXP_00N/figures/residuals_vs_q6.png`

HTML readout: `results/aligned_terminal_roll/sprint01_readout/index.html` (regenerate with `python scripts/generate_atr_sprint01_readout.py`).

### Sensitivity and refinement

Central-difference refinement shows expected quadratic convergence until floating-point noise dominates.

## 6. Unexpected observations

None material. Roll extraction for a full `2π` sweep required a probe-vector `atan2` about `d` rather than naive `[0, π]` axis-angle unwrapping; this is a measurement detail, not a change to the geometric claim.

## 7. Limitations

- known model exclusions: single revolute only; no serial chain;
- numerical limitations: FD round-off at `h ≲ 1e-6`;
- local-versus-global: fixture identity is global in `q6` for this model, but does not speak to 6R manifolds;
- unresolved: whether conventions remain adequate once a full chain is introduced.

## 8. Interpretation

Select one:

- `SUPPORTED`

Rationale: positive and independently violated negative controls behave as predicted; analytical derivatives match finite differences.

## 9. Decision

Select one:

- `CONTINUE`

Authorized next stage: Sprint 02 generic synthetic aligned 6R kernel (Jacobian ranks and terminal-roll null direction). **Approved.**

Blocked work: compound-joint models, UR-like architectures, fibers, spherical `RRRR`, McCarthy-Soh.

## 10. Project updates

- Project plan: Terminal fixture → Complete; Sprint 01 → Complete; Check-in 1 → Approved
- Roadmap: Phase 1 complete; Phase 2 authorized
- Conventions: frozen after Check-in 1 approval; later changes require a decision record
- Validation plan: C1–C5 exercised at fixture level
- Risk register: A01/A02 verified on fixture; R01/R03/R04/R09/R11 mitigated for Sprint 01
- Decision records: none new (ADR_001 still governs later UR deferral)

## 11. Next sprint recommendation

Build a generic synthetic aligned-terminal 6R chain and verify local rank / nullity claims (`rank(J_p)=3`, `rank(J_pd)=5`, kernel aligned to `e6`, `rank(J_d N_red)=2`) without introducing spherical four-bar constructions.
