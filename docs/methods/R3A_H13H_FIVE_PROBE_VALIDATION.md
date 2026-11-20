# R3A-H13H-5 five-probe validation

**Status:** BLOCKED VALIDATION. No frozen policy. P2/P3 were not evaluated. Source policy validated: false. `accepted_reconstruction`: false.

**Authority:** This file is the H13H-5 five-probe validation receipt. [R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the scientific status ledger. Machine-readable copy: [h13h5_five_probe_validation.json](../../results/l5_reconstruction/h13h/h13h5_five_probe_validation.json).

Regenerate with:

```bash
PYTHONPATH=src python scripts/write_h13h5_five_probe_validation.py
```

## 1. Prerequisite

Inspection HEAD `5f2c822b27955f41aac46d55f8cffce9aa0e2e3d` on `r3a-h13h-source-convergence`. H13H-4 receipt `results/l5_reconstruction/h13h/h13h4_convergence_study.json` (sha256 `ea8f8e0c1feccb0b8f01a7bda1870ce10b6b039d78db8414918bfc23caf0f35e`) reports `candidate_policy: null`.

Executed H13H-4 profiles: `['baseline', 'steps96', 'steps192']`.

## 2. Validation decision

`frozen_policy` is `null`. `p2_p3_evaluated` is `false`. `held_out_validation_claimed` is `false`.

Blocker `REQUIRED_INTERVALS_UNRESOLVED` after `steps192`. Continuation effort through 192 steps left required bins unresolved. Remaining blockers mix projection-backed MIXED_UNRESOLVED bins with P5 budget exhaustion and incomplete rasterization.

Remaining diagnostic-probe statuses: `[{'probe_id': 'P1_DEEP_COMPLETE', 'raster_failures': 0, 'statuses': ['MIXED_UNRESOLVED']}, {'probe_id': 'P4_OUTER_COMPLETE', 'raster_failures': 0, 'statuses': ['MIXED_UNRESOLVED']}, {'probe_id': 'P5_OUTER_INCOMPLETE', 'raster_failures': 7, 'statuses': ['BUDGET_EXHAUSTED', 'MIXED_UNRESOLVED']}]`.

Configured probe order remains `['P1_DEEP_COMPLETE', 'P2_INNER_COMPLETE', 'P3_INNER_INCOMPLETE', 'P4_OUTER_COMPLETE', 'P5_OUTER_INCOMPLETE']`. Unevaluated probes: `['P2_INNER_COMPLETE', 'P3_INNER_INCOMPLETE']`.

## 3. Next action

Reopen source diagnosis on projection-backed MIXED_UNRESOLVED bins and the remaining P5 budget/raster failures before any freeze.

Natural continuation budgets and the committed H13G pilot config are unchanged.
