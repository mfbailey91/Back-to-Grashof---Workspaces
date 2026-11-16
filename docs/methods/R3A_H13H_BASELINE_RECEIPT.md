# R3A-H13H-0 baseline receipt

**Status:** BASELINE RECORDED. Source policy validated: false. `accepted_reconstruction`: false. The H12 hub remains the recorded closeout.

**Authority:** This file is the H13H-0 identity and invariant receipt. [R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the scientific status ledger. Machine-readable copy: [h13h0_baseline_receipt.json](../../results/l5_reconstruction/h13h/h13h0_baseline_receipt.json).

Regenerate from the gitignored historical pilot with:

```bash
PYTHONPATH=src python scripts/write_h13h0_baseline_receipt.py
```

## 1. Baseline identity

| Field | Value |
|---|---|
| Inspection branch | `r3a-h13h-source-convergence` |
| Inspection HEAD | `90feebf430d77a099cecb3868f9854c9dd618073` |
| H13G implementation | `81f1e2059040b74e503d166f4e6588922ddafb8c` |
| H13G parent | `b42823699ab6332d6f81e9a522394d533e592c6a` |
| `origin/main` | `201b10f7779c671b9da2a8d88e4da83ab8b9cc9e` |
| `origin/main` parents | `3750a55946d72af843647d8c4d199a293234fddf b42823699ab6332d6f81e9a522394d533e592c6a` |
| `origin/main` subject | Merge pull request #22 from mfbailey91/R3A_H13_locked_invariants |
| `origin/R3A_H13_locked_invariants` | `81f1e2059040b74e503d166f4e6588922ddafb8c` |
| H13G contained in HEAD | true |
| H13G contained in `origin/main` | false |
| Inspection Python | 3.14.0 |
| Inspection packages | numpy 2.5.1, scipy 1.18.0, matplotlib 3.11.1, pillow 12.3.0 |
| Inspected at | 2026-11-15T20:33:51-08:00 |

`origin/main` is merge commit `201b10f7779c671b9da2a8d88e4da83ab8b9cc9e` (PR #22). Its second parent is the H13G parent `b42823699ab6332d6f81e9a522394d533e592c6a`. The H13G implementation commit is a later child of that parent on `origin/R3A_H13_locked_invariants`. `source_control_h13g.py` is present at the H13G commit and absent at its parent.

Tracked worktree dirty at inspection: false. Untracked path count: 25. Those untracked paths stay outside this receipt.

## 2. Historical pilot

Classification: `historical_dirty_producer`.

The raw tree `outputs/r3a_h13g_source_pilot` and compact tree `outputs/r3a_h13g_source_pilot_compact` are present. Their artifact indexes match the files on disk. The campaign config hash matches the committed H13G config. Mode is `full`. The compare-stage probe scope is P1/P4/P5. The manifest stage still lists all five configured probes. Package kind is `diagnostic`, `allows_full_campaign_disposition` is false, and `semantic_revalidation` is false.

Producer commit: `b42823699ab6332d6f81e9a522394d533e592c6a` with `dirty_tree=true`. That commit is the parent of H13G. The exact dirty diff is unavailable, so this tree is the historical pilot. A fresh reproduction on a clean H13G checkout was not run.

| Quantity | Value |
|---|---|
| Raw tree bytes | 191797676 |
| Compact tree bytes | 14967507 |
| Raw bundle | `r3a_full_3probes_e4b25df91753f9861f643db3558d20790b5e69184affd3fad0034fd9428ea9c4_b42823699ab6332d6f81e9a522394d533e592c6a.tar.zst` |
| Raw bundle sha256 | `89e85a61e51ce46e491cb0947e237c6d78dca0b586333ca82b77f66f5733c0aa` |
| Raw bundle bytes | 29549195 |
| Raw filesystem mtime span | 2026-08-27T10:05:23-07:00 to 2026-08-27T16:44:07-07:00 |
| Compact filesystem mtime span | 2026-08-27T10:05:23-07:00 to 2026-08-27T17:05:34-07:00 |
| Solver wall time | unavailable |
| Historical dependency versions | unavailable |
| Campaign blocker | `STITCHING_CONTROL_BLOCKED` |
| Recomputed campaign blocker | null |

Filesystem timestamps are archive clock observations. They are not a measured solver runtime.

The historical `--stage all` tree contains natural-family artifacts. This receipt leaves them uninterpreted.

Declared full-mode settings matched by every serialized probe policy: continuation steps 48, initial step 0.08, `c` count minimum 17, `c` spacing fraction 0.75, curve fraction 0.5, raster depth 8, candidate budget 1024, trace budget 16, trace-cover 0.35, dedup 0.35, endpoint tolerance 0.1, endpoint tangent dot 0.85.

## 3. Protected evidence

| Config | Schema | Config hash | File sha256 | Full mode may dispose |
| --- | --- | --- | --- | --- |
| h12 | r3a_l5_positive_control_v1 | 8a656dec0227232b83a51bb891f541f4ec160a7b93cf2add944d3b5caf6fdffa | f4f583325e425ad0faf0d5f243558f689288e35c609d24b75272b6d42e358137 | true |
| h13e | r3a_l5_positive_control_h13_source_pilot_v1 | db4e4409a12b82b7cfbed504144b327ebc74bf1df1a09ce602ce24ffc5f07496 | 86e952a0968ded585907c1462fa7520578cc55e5970ec32a264d26e8bcdc6c09 | false |
| h13f | r3a_l5_positive_control_h13_source_v1 | ff9f4bd1be03e05d85dbad6d086ba513d7f766edb0f06a1a877c2cfb4aa847f9 | 1563c0872f19b97eb1f8f8d97acf48b6a81187c62a1b9e7fae029409f6f132a4 | true |
| h13g | r3a_l5_positive_control_h13g_source_pilot_v1 | e4b25df91753f9861f643db3558d20790b5e69184affd3fad0034fd9428ea9c4 | 13234cc165d5c02ad1db824b6523ac46a5f402c48a6cd8354a3b91d715f8617e | false |

H12 hub `results/l5_reconstruction/r3a/compact_manifest.json` file sha256 `1f75c2483b8feeeafac6c7daedf50d01b71a07293917d18fc1b8727eb53d09ff`. Raw bundle digest `d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec`. Package `full_closeout`, blocker `STITCHING_CONTROL_BLOCKED`, accepted reconstruction false, semantic revalidation true, producer `9505a877a489469186afb5fb3a8dfc89bb6a75ad`.

## 4. Per-probe source baseline

Direct and source columns below are the stored run-level metrics. Hausdorff cell diameters are the stored angular Hausdorff divided by the stored cell diameter. Refinement is the existing within-run coarse/fine metric. The declared refinement limit is 0.02.

| Probe | Direct complete | Oracle complete | Direct miss | Direct Hausdorff | Direct refinement | Source miss | Source Hausdorff diameters | Source false positive | Source refinement | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1_DEEP_COMPLETE | true | true | 0 | 0 | 0 | 0.00703125 | 0.522938536534 | NOT_APPLICABLE | 0.522938536534 | STITCHING_CONTROL_BLOCKED |
| P4_OUTER_COMPLETE | true | true | 0 | 0 | 0 | 0.0078125 | 0.522938536534 | NOT_APPLICABLE | 0.522938536534 | STITCHING_CONTROL_BLOCKED |
| P5_OUTER_INCOMPLETE | true | false | 0 | 0 | 0 | 0.00855513307985 | 0.522938536534 | 0 | 0.522938536534 | STITCHING_CONTROL_BLOCKED |

`oracle_complete` is the stored comparison flag. P5 remains the outer-incomplete probe. On these three probes the stored `source_vs_oracle` metric view equals `source_vs_direct`.

| Probe | Required bins | Required status counts | Unexplained representatives | Explained representatives | Candidate-cap bins | Trace-cap bins | Seed-cap bins |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1_DEEP_COMPLETE | 25 | {'BUDGET_EXHAUSTED': 8, 'MIXED_UNRESOLVED': 4, 'RETURNED_SET_FOUND': 13} | 0 | 3536 | 0 | 0 | 0 |
| P4_OUTER_COMPLETE | 25 | {'BUDGET_EXHAUSTED': 5, 'MIXED_UNRESOLVED': 3, 'RETURNED_SET_FOUND': 17} | 0 | 3312 | 0 | 0 | 0 |
| P5_OUTER_INCOMPLETE | 19 | {'BUDGET_EXHAUSTED': 6, 'RETURNED_SET_FOUND': 13} | 0 | 2867 | 0 | 0 | 0 |

| Probe | Fibers | Termination counts | Incomplete raster fibers | Raster budget exhausted | Raster failure count | Required bins with incomplete raster | Effective c count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1_DEEP_COMPLETE | 216 | {'BUDGET_EXHAUSTED': 64, 'CORRECTOR_FAILURE': 16, 'RETURNED_TO_SEED': 136} | 2 | 0 | 2 | 1 | 27 |
| P4_OUTER_COMPLETE | 216 | {'BUDGET_EXHAUSTED': 36, 'CORRECTOR_FAILURE': 16, 'RETURNED_TO_SEED': 164} | 4 | 4 | 3 | 2 | 27 |
| P5_OUTER_INCOMPLETE | 160 | {'BUDGET_EXHAUSTED': 34, 'CORRECTOR_FAILURE': 8, 'RETURNED_TO_SEED': 118} | 4 | 4 | 1 | 1 | 21 |

Required-bin cap flags above count discovery and trace allocation caps. Fiber `BUDGET_EXHAUSTED` counts are continuation termination, recorded separately in the termination column. Non-required bins retain status `CRITICAL_OR_BOUNDARY`. Serialized fibers contain accepted samples, ray termination, and raster counts. Per-step branch history and corrected raster configurations are absent. Compact `source_control.json` files are smaller than the raw files. Compact comparison files match the raw comparison bytes.

## 5. Unavailable historical detail

- exact dirty working-tree diff at the producer commit
- solver wall-clock runtime
- historical Python and dependency versions
- per-step BranchTrace history
- corrected raster segment configurations

## 6. Exit

Baseline identity, protected hashes, and the hash-checked historical pilot are recorded. The clean-SHA reproduction remains unrun because the historical raw tree was available and its producer diff is the missing detail, not the tree itself. Source-policy validation remains future H13H work.
