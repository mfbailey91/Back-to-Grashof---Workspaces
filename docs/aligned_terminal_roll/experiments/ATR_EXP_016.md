# ATR_EXP_016 — Intersecting-pair persistence

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 04 — Pointing manifold
**Related claim IDs:** C9 (discriminating), A07
**Random seed:** 23

## 1. Purpose

Verify that `R1∩R2` and `R3∩R4` persist away from home on `IntersectingPairsAligned6R`.

## 2. Expected result

Both pair distances remain `0` at the named regular configuration and 24 seeded configurations.

## 3. Command

```bash
python scripts/validate_pointing_manifold.py
```

## 4. Results

- status: PASS
- observed: named and seeded max pair distances `0`
- source: `grashof_workspace.spatial_experiments.manifold_experiments:sprint04-v1`

## 5. Interpretation

- `PASS` supports pair persistence as a serial identity of the intersecting-pair architecture.
