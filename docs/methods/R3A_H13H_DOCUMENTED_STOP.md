# R3A-H13H-6 documented stop

**Status:** DOCUMENTED STOP. No frozen policy. No frozen config. H13I not authorized. Source policy validated: false. `accepted_reconstruction`: false.

**Authority:** This file is the H13H-6 documented-stop receipt. [R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) is the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) is the scientific status ledger. Decision: [ADR-063](../reference/DECISIONS.md#adr-063--h13h-closes-as-a-documented-source-control-stop). Machine-readable copy: [h13h6_documented_stop.json](../../results/l5_reconstruction/h13h/h13h6_documented_stop.json).

Regenerate with:

```bash
PYTHONPATH=src python scripts/write_h13h6_documented_stop.py
```

## 1. Closeout identity

Inspection HEAD `e6ed53efa1d387a1a1cf89b5dcf17856b0decc7c` on `r3a-h13h-source-convergence`. `closeout_kind` is `documented_stop`. `frozen_config_created` is `False`.

Blocker `REQUIRED_INTERVALS_UNRESOLVED` after `steps192`. Continuation effort through 192 steps left required bins unresolved. Remaining blockers mix projection-backed MIXED_UNRESOLVED bins with P5 budget exhaustion and incomplete rasterization.

Remaining diagnostic-probe statuses: `[{'probe_id': 'P1_DEEP_COMPLETE', 'raster_failures': 0, 'statuses': ['MIXED_UNRESOLVED']}, {'probe_id': 'P4_OUTER_COMPLETE', 'raster_failures': 0, 'statuses': ['MIXED_UNRESOLVED']}, {'probe_id': 'P5_OUTER_INCOMPLETE', 'raster_failures': 7, 'statuses': ['BUDGET_EXHAUSTED', 'MIXED_UNRESOLVED']}]`.

## 2. Evidence chain

- `H13H-0`: `results/l5_reconstruction/h13h/h13h0_baseline_receipt.json` (sha256 `dc80d37ccc35a70d19b444adf095ed76521c0ae68ba1b23d828d21c22aa26cbb`)
- `H13H-2`: `results/l5_reconstruction/h13h/h13h2_continuation_diagnosis.json` (sha256 `ef52985bd14dc787e89e41d6a2282f3d892c803d9c3f24dd777079a5f51756c2`)
- `H13H-3`: `results/l5_reconstruction/h13h/h13h3_raster_diagnosis.json` (sha256 `0f560b3cd3387cda87f3e49705ea96bf2fd013443d653d9a98f5ba81fd045d60`)
- `H13H-4`: `results/l5_reconstruction/h13h/h13h4_convergence_study.json` (sha256 `ea8f8e0c1feccb0b8f01a7bda1870ce10b6b039d78db8414918bfc23caf0f35e`)
- `H13H-5`: `results/l5_reconstruction/h13h/h13h5_five_probe_validation.json` (sha256 `5f2491ec255aa7e7e73a1fd2188be60b1641369a949bf6c63c4ec0402f618dad`)

## 3. Protected H12 identity

H12 hub `results/l5_reconstruction/r3a/compact_manifest.json` file sha256 `1f75c2483b8feeeafac6c7daedf50d01b71a07293917d18fc1b8727eb53d09ff`; raw bundle sha256 `d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec`; campaign blocker `STITCHING_CONTROL_BLOCKED`; `accepted_reconstruction` `False`.

Protected configs and hub hashes are copied from the H13H-0 baseline receipt. This package does not mutate the hub.

## 4. Attempted settings

- `baseline` axis `baseline` declared `{'continuation_steps': 48}` passed=`False`
- `steps96` axis `continuation_effort` declared `{'continuation_max_steps_per_ray': 96}` passed=`False`
- `steps192` axis `continuation_effort` declared `{'continuation_max_steps_per_ray': 192}` passed=`False`

Skipped axes:

- `step_resolution`: H13H-2 did not implicate return sampling or endpoint meeting
- `raster_depth`: H13H-3 classified depth exhaustion as an untraced closing gap

## 5. Failure classification

No three-probe candidate. P2/P3 were not evaluated. Projection-backed MIXED_UNRESOLVED bins remain on P1/P4; P5 retains budget exhaustion, MIXED_UNRESOLVED, and raster failures.

## 6. Repairs landed

- `H13H-2`: No demonstrated continuation solver defect; production solver unchanged.
- `H13H-3`: Chord-section midpoint correction for raster midpoints; open-ray closing gaps remain unresolved.
- `Gate-B`: Unknown source-policy tokens reject; continuation_max_steps_per_ray is an explicit opt-in.

## 7. H13I handoff

`authorized` is `False`. Blocker: H13H source-policy validation unmet.

Prerequisites:

- Resolve projection-backed MIXED_UNRESOLVED bins on diagnostic probes.
- Clear remaining P5 BUDGET_EXHAUSTED and raster-failure obligations.
- Obtain one candidate policy that passes P1/P4/P5 and five-probe validation.

Remaining limitations:

- No frozen H13H numerical policy exists.
- P2 and P3 were not evaluated under a candidate policy.
- The H12 hub remains the authoritative full closeout.
- Natural UURU interpretation and all-column H13I packaging are not authorized.

## 8. Next action

Reopen source diagnosis on projection-backed MIXED_UNRESOLVED bins and the remaining P5 budget/raster failures before any freeze.

Natural continuation budgets and the committed H13G pilot config are unchanged.
