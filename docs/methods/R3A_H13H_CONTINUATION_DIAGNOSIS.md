# R3A-H13H-2 continuation diagnosis

**Status:** DIAGNOSIS RECORDED. Source policy validated: false. `accepted_reconstruction`: false. The default continuation solver is unchanged.

**Authority:** This file is the H13H-2 continuation diagnosis. [R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the scientific status ledger. Machine-readable copy: [h13h2_continuation_diagnosis.json](../../results/l5_reconstruction/h13h/h13h2_continuation_diagnosis.json).

Regenerate from the gitignored historical pilot with:

```bash
PYTHONPATH=src python scripts/write_h13h2_continuation_diagnosis.py
```

## 1. Scope

Inspection HEAD `91395bd7e160d811cd5c7964b67c8cbef17ab93c` on `r3a-h13h-source-convergence`. Config hash `e4b25df91753f9861f643db3558d20790b5e69184affd3fad0034fd9428ea9c4`. Mode `full` uses 48 continuation steps per ray when no override is supplied.

The historical pilot remains a dirty-producer record. `stored_fiber_agreement` false means this clean replay disagrees with that record. Disagreement is not a solver defect.

Raster-only failures are outside this diagnosis. Full per-step traces stay in gitignored `outputs/r3a_h13h2_continuation/`.

## 2. Selected continuation cases

Underlying counts: `{'passing_regular': 410, 'budget_exhausted': 163, 'mixed_bin': 56, 'raster_failing': 10, 'singular_or_corrector': 40}`.

### passing_regular

- Fiber `P1_DEEP_COMPLETE_c1_t0` at c `-0.992709`, stored termination `RETURNED_TO_SEED`, stored interval `RETURNED_SET_FOUND`.
- Baseline agreement with the stored fiber: `True`.
- Demonstrated cause: `NO_CONTINUATION_FAILURE`. The trace closed without a hidden singular or corrector ray.
- Possible causes: `[]`.
- Closure route: `seed_return`. Ray terminations: `{'positive': 'RETURNED_TO_SEED'}`.
- Accepted steps `36`, arclength `1.77401`, step range `0.015` to `0.08`.
- Reached step cap: `False`. Endpoint meeting implicated: `False`.
- Step-count comparisons: `0`. Step-cap comparison: `not_implicated`. Unequal ray budgets: `not_implicated`.
- Seed inferred from the first serialized sample: `False`. First serialized sample equals a recorded seed: `True`.
- Rejection counts: `{'tangent_rotation': 56, 'corrector_failed': 18}`.
- Stored interval evidence: `{'required': True, 'rasterization_incomplete_count': 0, 'blocking_projection_failure_count': 0, 'diagnostic_projection_failure_count': 28, 'budget_exhausted_count': 0, 'corrector_failure_count': 0, 'closure_kind_counts': {'RETURNED_TO_SEED': 8}}`.
- Interval reading: The stored interval is a returned set. Rasterization is complete.

### budget_exhausted

- Fiber `P1_DEEP_COMPLETE_c2_t1` at c `-0.970942`, stored termination `RETURNED_TO_SEED`, stored interval `MIXED_UNRESOLVED`.
- Baseline agreement with the stored fiber: `True`.
- Demonstrated cause: `CLOSED_TRACE_BIN_BLOCKED_BY_OTHER_STAGE`. The trace is closed, and the stored c interval is blocked by another stage.
- Possible causes: `[]`.
- Closure route: `seed_return`. Ray terminations: `{'positive': 'BUDGET_EXHAUSTED', 'negative': 'RETURNED_TO_SEED'}`.
- Accepted steps `71`, arclength `6.44449`, step range `0.03` to `0.18`.
- Reached step cap: `False`. Endpoint meeting implicated: `False`.
- Step-count comparisons: `0`. Step-cap comparison: `not_implicated`. Unequal ray budgets: `not_implicated`.
- Seed inferred from the first serialized sample: `False`. First serialized sample equals a recorded seed: `False`.
- Rejection counts: `{'tangent_rotation': 88, 'corrector_failed': 22}`.
- Stored interval evidence: `{'required': True, 'rasterization_incomplete_count': 2, 'blocking_projection_failure_count': 0, 'diagnostic_projection_failure_count': 8, 'budget_exhausted_count': 0, 'corrector_failure_count': 0, 'closure_kind_counts': {'RETURNED_TO_SEED': 8}}`.
- Interval reading: Every stored closure in this bin returned to its seed. 2 fibers have incomplete rasterization, which leaves the interval mixed.

### mixed_bin

- Fiber `P1_DEEP_COMPLETE_c2_t0` at c `-0.970942`, stored termination `RETURNED_TO_SEED`, stored interval `MIXED_UNRESOLVED`.
- Baseline agreement with the stored fiber: `True`.
- Demonstrated cause: `CLOSED_TRACE_BIN_BLOCKED_BY_OTHER_STAGE`. The trace is closed, and the stored c interval is blocked by another stage.
- Possible causes: `[]`.
- Closure route: `seed_return`. Ray terminations: `{'positive': 'RETURNED_TO_SEED'}`.
- Accepted steps `23`, arclength `1.80868`, step range `0.03` to `0.12`.
- Reached step cap: `False`. Endpoint meeting implicated: `False`.
- Step-count comparisons: `0`. Step-cap comparison: `not_implicated`. Unequal ray budgets: `not_implicated`.
- Seed inferred from the first serialized sample: `False`. First serialized sample equals a recorded seed: `True`.
- Rejection counts: `{'tangent_rotation': 24}`.
- Stored interval evidence: `{'required': True, 'rasterization_incomplete_count': 2, 'blocking_projection_failure_count': 0, 'diagnostic_projection_failure_count': 8, 'budget_exhausted_count': 0, 'corrector_failure_count': 0, 'closure_kind_counts': {'RETURNED_TO_SEED': 8}}`.
- Interval reading: Every stored closure in this bin returned to its seed. 2 fibers have incomplete rasterization, which leaves the interval mixed.

### singular_or_corrector

- Fiber `P1_DEEP_COMPLETE_c0_t0` at c `-1`, stored termination `CORRECTOR_FAILURE`, stored interval `CRITICAL_OR_BOUNDARY`.
- Baseline agreement with the stored fiber: `True`.
- Demonstrated cause: `REPEATED_CORRECTOR_REJECTION`. Continuation ended in corrector rejection or minimum-step collapse.
- Possible causes: `[]`.
- Closure route: `None`. Ray terminations: `{'positive': 'CORRECTOR_FAILURE', 'negative': 'CORRECTOR_FAILURE'}`.
- Accepted steps `0`, arclength `0`, step range `null` to `null`.
- Reached step cap: `False`. Endpoint meeting implicated: `False`.
- Step-count comparisons: `0`. Step-cap comparison: `not_implicated`. Unequal ray budgets: `not_implicated`.
- Seed inferred from the first serialized sample: `False`. First serialized sample equals a recorded seed: `True`.
- Rejection counts: `{'corrector_failed': 28}`.
- Stored interval evidence: `{'required': False, 'rasterization_incomplete_count': 0, 'blocking_projection_failure_count': 8, 'diagnostic_projection_failure_count': 200, 'budget_exhausted_count': 0, 'corrector_failure_count': 8, 'closure_kind_counts': {'CORRECTOR_FAILURE': 8}}`.
- Interval reading: This bin is not required. Its stored closures are corrector failures on a boundary interval, with blocking projection failures.

## 3. Repair decision

`solver_defect_demonstrated` is `False`. `production_solver_changed` is `False`. The shared natural continuation budget is unchanged.

No selected replay demonstrated a continuation defect. No selected fiber had demonstrated cause REGULAR_BUDGET_EXHAUSTED, so the 96-step and 192-step comparisons were not run. Regular budget exhaustion remains a later numerical-schedule question.

- `continuation_max_steps_per_ray`: not added.
- `h13h_source_convergence_v1`: not registered.
- Unknown nonempty policy tokens: dispatch unchanged. An absent policy version still selects the H12 path.

A regular budget on a later numerical schedule remains an H13H-4 question. It is not converted into closure here.
