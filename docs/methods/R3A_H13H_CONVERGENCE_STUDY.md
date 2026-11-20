# R3A-H13H-4 P1/P4/P5 convergence study

**Status:** STUDY RECORDED. No candidate. Blocker `REQUIRED_INTERVALS_UNRESOLVED`. Source policy validated: false. `accepted_reconstruction`: false.

**Authority:** This file is the H13H-4 convergence receipt. [R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the scientific status ledger. Machine-readable copy: [h13h4_convergence_study.json](../../results/l5_reconstruction/h13h/h13h4_convergence_study.json).

Regenerate with:

```bash
PYTHONPATH=src python scripts/write_h13h4_convergence_study.py
```

## 1. Scope

Inspection HEAD `62991f3816d0475a1c572dbb461c631a23e86a51` on `r3a-h13h-source-convergence`. Probes `['P1_DEEP_COMPLETE', 'P4_OUTER_COMPLETE', 'P5_OUTER_INCOMPLETE']`.

Executed profiles: `['baseline', 'steps96', 'steps192']`.
Skipped axes: `[{'axis': 'step_resolution', 'reason': 'H13H-2 did not implicate return sampling or endpoint meeting'}, {'axis': 'raster_depth', 'reason': 'H13H-3 classified depth exhaustion as an untraced closing gap'}]`.

## 2. Run-level gates

### baseline

- Config `configs/l5_positive_control_h13g_source_pilot_v1.json` hash `e4b25df91753f9861f643db3558d20790b5e69184affd3fad0034fd9428ea9c4`. Passed: `False`.
- Declared numerical fields: `{'continuation_steps': 48}`.
- `P1_DEEP_COMPLETE` passed `False`; interval blockers `12`; required raster failures `2`; cap flags `0`.
- `P4_OUTER_COMPLETE` passed `False`; interval blockers `8`; required raster failures `4`; cap flags `0`.
- `P5_OUTER_INCOMPLETE` passed `False`; interval blockers `6`; required raster failures `7`; cap flags `0`.

### steps96

- Config `configs/l5_positive_control_h13h4_steps96_v1.json` hash `a98a32de74887762e3e16316d5700d83b22fa2b4046ea5d372c692f34fb304fa`. Passed: `False`.
- Declared numerical fields: `{'continuation_max_steps_per_ray': 96}`.
- `P1_DEEP_COMPLETE` passed `False`; interval blockers `3`; required raster failures `0`; cap flags `0`.
- `P4_OUTER_COMPLETE` passed `False`; interval blockers `2`; required raster failures `0`; cap flags `0`.
- `P5_OUTER_INCOMPLETE` passed `False`; interval blockers `3`; required raster failures `7`; cap flags `0`.

### steps192

- Config `configs/l5_positive_control_h13h4_steps192_v1.json` hash `52f972b1e3f1f8cc6b356fc7541bfd29ba806c566c134d2aa41ea306b09fab9c`. Passed: `False`.
- Declared numerical fields: `{'continuation_max_steps_per_ray': 192}`.
- `P1_DEEP_COMPLETE` passed `False`; interval blockers `3`; required raster failures `0`; cap flags `0`.
- `P4_OUTER_COMPLETE` passed `False`; interval blockers `1`; required raster failures `0`; cap flags `0`.
- `P5_OUTER_INCOMPLETE` passed `False`; interval blockers `3`; required raster failures `7`; cap flags `0`.

## 3. Cross-run comparisons

No eligible Section 3.3 pair was formed.


## 4. Decision

`candidate_policy`: `None`.
`blocker`: `{'status': 'REQUIRED_INTERVALS_UNRESOLVED', 'after_profile': 'steps192', 'detail': 'Continuation effort through 192 steps left required bins unresolved. Remaining blockers mix projection-backed MIXED_UNRESOLVED bins with P5 budget exhaustion and incomplete rasterization.', 'remaining': [{'probe_id': 'P1_DEEP_COMPLETE', 'statuses': ['MIXED_UNRESOLVED'], 'raster_failures': 0}, {'probe_id': 'P4_OUTER_COMPLETE', 'statuses': ['MIXED_UNRESOLVED'], 'raster_failures': 0}, {'probe_id': 'P5_OUTER_INCOMPLETE', 'statuses': ['BUDGET_EXHAUSTED', 'MIXED_UNRESOLVED'], 'raster_failures': 7}]}`.

Natural continuation budgets and the committed H13G pilot config are unchanged.
