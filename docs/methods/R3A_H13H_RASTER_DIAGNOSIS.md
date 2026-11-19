# R3A-H13H-3 raster diagnosis

**Status:** DIAGNOSIS RECORDED. Source policy validated: false. `accepted_reconstruction`: false. Raster midpoints now stay on the wrapped chord section. Continuation is unchanged.

**Authority:** This file is the H13H-3 raster diagnosis. [R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the scientific status ledger. Machine-readable copy: [h13h3_raster_diagnosis.json](../../results/l5_reconstruction/h13h/h13h3_raster_diagnosis.json).

Regenerate from the gitignored historical pilot with:

```bash
PYTHONPATH=src python scripts/write_h13h3_raster_diagnosis.py
```

## 1. Scope

Inspection HEAD `6a96d52ea4697af232a0a06aae0dd7fb0c1b3903` on `r3a-h13h-source-convergence`. Config hash `e4b25df91753f9861f643db3558d20790b5e69184affd3fad0034fd9428ea9c4`.

The historical pilot remains a dirty-producer record. Agreement compares termination, accepted step counts, and the raster completion flag. A false agreement means this repaired replay disagrees with that record. Disagreement is not a solver defect by itself.

## 2. Selected raster cases

Underlying counts: `{'passing_regular': 410, 'budget_exhausted': 163, 'mixed_bin': 56, 'raster_failing': 10, 'singular_or_corrector': 40}`.

### closing_control

- Fiber `P1_DEEP_COMPLETE_c1_t0` at c `-0.992708874098054`. Stored termination `RETURNED_TO_SEED`, rays `RETURNED_TO_SEED` / `None`.
- Stored raster complete: `True`. Replay raster complete: `True`. Stored fiber agreement: `True`.
- Demonstrated cause: `NO_RASTER_FAILURE`. The raster meets the declared gap, correction, depth, and residual checks.
- Closing outcomes: `{'within_declared_gap': 1}`. Replay correction failures: `0`. Replay depth exhausted: `False`. Nonlocal corrections: `0`. Interval blocked: `False`.
- Residuals position `1.5770682649803802e-11`, scalar `6.706291078018012e-11`. Max interior excursion `0.0008432192151755918` over `37` short segments.

### raster_failing

- Fiber `P1_DEEP_COMPLETE_c2_t3` at c `-0.970941817426052`. Stored termination `RETURNED_TO_SEED`, rays `BUDGET_EXHAUSTED` / `RETURNED_TO_SEED`.
- Stored raster complete: `False`. Replay raster complete: `False`. Stored fiber agreement: `True`.
- Demonstrated cause: `UNTRACED_CLOSING_GAP`. The closing chord joins an open ray to the seed. The local section correction does not cross that untraced gap.
- Closing outcomes: `{'failed_correction': 1}`. Replay correction failures: `1`. Replay depth exhausted: `False`. Nonlocal corrections: `0`. Interval blocked: `True`.
- Residuals position `3.3222743980604046e-11`, scalar `8.619049918223709e-11`. Max interior excursion `0.000287304348867784` over `96` short segments.

### depth_exhausted_closing

- Fiber `P4_OUTER_COMPLETE_c5_t4` at c `-0.8229838658936564`. Stored termination `RETURNED_TO_SEED`, rays `BUDGET_EXHAUSTED` / `RETURNED_TO_SEED`.
- Stored raster complete: `False`. Replay raster complete: `False`. Stored fiber agreement: `True`.
- Demonstrated cause: `UNTRACED_CLOSING_GAP`. The closing chord joins an open ray to the seed. The local section correction does not cross that untraced gap.
- Closing outcomes: `{'failed_correction': 1}`. Replay correction failures: `1`. Replay depth exhausted: `False`. Nonlocal corrections: `0`. Interval blocked: `True`.
- Residuals position `1.5606156487479942e-11`, scalar `6.94152513247559e-11`. Max interior excursion `2.9786621617872155e-05` over `258` short segments.

### open_ray_completed

- Fiber `P4_OUTER_COMPLETE_c8_t4` at c `-0.5680647467311557`. Stored termination `RETURNED_TO_SEED`, rays `BUDGET_EXHAUSTED` / `RETURNED_TO_SEED`.
- Stored raster complete: `True`. Replay raster complete: `True`. Stored fiber agreement: `True`.
- Demonstrated cause: `NO_RASTER_FAILURE`. The raster meets the declared gap, correction, depth, and residual checks.
- Closing outcomes: `{'corrected': 31, 'within_declared_gap': 32}`. Replay correction failures: `0`. Replay depth exhausted: `False`. Nonlocal corrections: `0`. Interval blocked: `False`.
- Residuals position `7.46956421536348e-11`, scalar `9.593270622332284e-11`. Max interior excursion `7.902596823330943e-06` over `248` short segments.

## 3. Repair decision

The selected depth-exhausted closing chord accepted a midpoint correction farther than the chord. Raster midpoints now solve the level set on the wrapped chord section and are rejected outside that chord. Position and scalar residuals block completion.

- Midpoint correction: `chord_section_with_chord_length_trust_radius`.
- Residual gate: `position_and_scalar_residuals_block_completion`.
- Continuation step budget: `not_added`.
- `h13h_source_convergence_v1`: `not_registered`.
- Raster depth increased: `False`.

`replay_still_shows_nonlocal_sample` is `False`. `accepted_reconstruction` remains false.
