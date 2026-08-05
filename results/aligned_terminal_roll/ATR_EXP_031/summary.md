# ATR_EXP_031

**Status:** PASS
**Commit:** 9eaf0fff6c4216085e7c176de0c7198d156d5b69
**Working tree dirty:** False
**Source:** grashof_workspace.spatial_experiments.fiber_experiments:sprint05-v1

## Expected

With max_microstep=None over the same σ travel, reverse tracking succeeds and both joint and pointing return errors decrease when Δσ is halved; shared-σ samples stay within 1e-3. Tight 1e-6/5e-8 reverse gates apply to microstepped runs (028/029), not this independent-step refinement diagnostic

## Observed

IntersectingPairsAligned6R: coarse_eq=6.295e-06 -> fine_eq=7.884e-07, shared_dq=6.426e-05; URLikeAligned6R: coarse_eq=5.915e-07 -> fine_eq=7.399e-08, shared_dq=3.310e-05
