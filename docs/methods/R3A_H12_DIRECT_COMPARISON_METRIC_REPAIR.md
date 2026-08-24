# R3A-H12 — Direct-Comparison Metric Repair and Closeout Revalidation

**Status:** RECORDED — H12 frozen full-mode closeout is `STITCHING_CONTROL_BLOCKED`
**Project:** Back to Grashof — Mechanism-Based Workspace Characterization
**Rung:** L5 spatial 5R
**Starting point:** PR #19 / head `5ffe8ef5c7c4e8bb42c67396d5c8cc1368910ebc`
**Parent controls:** H7 metric applicability, H10 artifact authority, H11 package authority
**Goal:** Repair the direct comparison so the first failing scientific column is determined by kinematic evidence rather than sphere-grid representation.

---

## 1. Why H12 is required

The H11E full package is valid as an artifact package:

```text
mode = full
all five probes
clean producer provenance
content-addressed raw bundle
complete stage tree
accepted_reconstruction = false
```

Its scientific `DIRECT_REFERENCE_BLOCKED` label is withdrawn.

At P1, P2, and P4 the direct reference reconstructs every fine-grid direction with
zero fine Hausdorff distance. The coarse comparison nevertheless compares the same
fine-grid direction cloud against non-nested coarse-grid barycenters. The resulting
normalized barycenter offset is reported as refinement instability.

At P3 and P5, found `AMBIGUOUS_BOUNDARY` cells are excluded from strict recall and
false-positive denominators but included in the reconstructed Hausdorff set. A
boundary solve can therefore fail a strict metric even though the strict feasible and
infeasible cells agree.

H12 repairs those semantics without changing:

```text
positive-control geometry
oracle formulas
IK budgets
source h=c control
natural UURU construction
acceptance tolerances
```

---

## 2. Locked invariants

- Raw direction samples determine cell occupancy.
- Recall, false positives, and Hausdorff use the same strict domain.
- `AMBIGUOUS_BOUNDARY` is excluded from strict Hausdorff.
- Fine and coarse Hausdorff sets are represented by barycenters from their own grid.
- The underlying raw sample bank is unchanged between refinement levels.
- `ci` and `smoke` remain unable to issue full-campaign disposition.
- Source and natural columns remain uninterpreted until the corrected direct column passes.
- The old H11E package remains historical evidence; it is not silently rewritten.
- `accepted_reconstruction` remains false until a corrected full rerun passes all gates.

---

# H12A — Grid-local strict set representation

## 3. Strict grid sets

For one grid, labels, and hit mask, construct:

```text
reference strict set =
    barycenters of STRICT_COVERED cells

reconstructed strict set =
    barycenters of hit cells whose label is not AMBIGUOUS_BOUNDARY
```

This preserves strict false positives in the reconstructed Hausdorff set while
excluding intentionally ambiguous cells.

Raw directions are used only to paint the hit mask.

## 4. Two-resolution refinement

For each comparison column:

```text
fine:
  paint raw directions on fine grid
  form fine strict barycenter sets
  compute fine metrics

coarse:
  paint the same raw directions on coarse grid
  form coarse strict barycenter sets
  compute coarse metrics
```

Then compute the existing normalized refinement delta.

A complete sphere reconstructed on both grids must produce:

```text
fine Hausdorff = 0
coarse Hausdorff = 0
refinement delta = 0
```

The regression must use actual level-0/level-1 or level-2/level-3 sphere grids, not
identical arrays with only the scalar cell diameter changed.

## 5. H12A acceptance

- complete-sphere refinement is zero on two non-nested grids;
- a found ambiguous-boundary cell does not enter strict Hausdorff;
- a hit in `STRICT_UNCOVERED` still produces a strict false positive and Hausdorff penalty;
- empty reconstruction remains a failed Hausdorff value;
- the existing denominator-aware states remain unchanged.

---

# H12B — Direct-column strict sampling

## 6. Fine direct mask

The fine direct mask remains the confirmation-cell solve status:

```text
FOUND -> hit
NOT_FOUND_AT_DECLARED_BUDGET -> no hit
UNRESOLVED -> no accepted disposition
```

The strict grid helper removes ambiguous cells from the Hausdorff representation.

## 7. Coarse direct painting

Only fine direct directions satisfying:

```text
direct_status == FOUND
and strict_reference_eligible == true
```

are repainted onto the coarse grid.

This prevents a fine boundary solve from painting a coarse strict cell.

## 8. H12B acceptance

- P1/P2/P4-style complete-sphere synthetic direct truth passes refinement;
- P3/P5-style found boundary cells cannot fail strict Hausdorff;
- strict infeasible hits remain failures;
- unresolved strict cells continue to block direct completeness.

---

# H12C — Reseed disposition vocabulary

## 9. Returned sampled-set evidence

The implemented re-seed evidence establishes:

```text
returned symmetric branch-set match
at the declared continuation budget
```

It does not independently establish:

```text
circuit identity
assembly-mode identity
topological component identity
```

Add:

```python
ReseedScope.RETURNED_SET
ReseedDisposition.RETURNED_SET_PASS
```

Production re-seeding emits `RETURNED_SET_PASS`.

Reserve:

```text
COMPONENT_PASS
```

for a future independent component/circuit signature.

The finite declared-resolution family gate may explicitly accept either
`RETURNED_SET_PASS` or a future `COMPONENT_PASS`, but those claims remain distinct in
JSON and prose.

## 10. H12C acceptance

- production returned-set evidence never emits `COMPONENT_PASS`;
- existing local/open behavior remains `LOCAL_PASS`;
- component identity compatibility fields remain null;
- family admission documents that returned-set evidence is sufficient only for the
  finite declared-resolution reconstruction claim.

---

# H12D — Package-side semantic recomputation

## 11. Full-closeout semantic authority

After hash and scope validation, `--full-closeout` must:

1. load all five per-probe `comparison.json` records;
2. require exact equality with the comparison records embedded in `campaign.json`;
3. require `compare.json == campaign.json`;
4. reconstruct typed metrics from JSON;
5. reread unresolved source-c and natural-lambda intervals;
6. recompute each point classification, disposition, failure localization, and blocker;
7. recompute campaign acceptance and global first blocker;
8. refuse any stored/recomputed mismatch.

The compact manifest records:

```text
semantic_revalidation = true
recomputed_campaign_blocker = <enum>
```

A self-consistently rehashed but semantically mislabeled tree must not package.

## 12. H12D acceptance

- a synthetic source-blocked full campaign recomputes to `STITCHING_CONTROL_BLOCKED`;
- a wrong global blocker is refused;
- per-probe/embedded comparison drift is refused;
- accepted reconstruction and campaign disposition must recompute;
- diagnostics remain packageable without full scientific disposition.

---

# H12E — Closeout withdrawal and rerun

## 13. Before the rerun

Do not edit the existing compact JSON in place. Preserve it as historical H11E evidence
until the corrected producer tree is green.

Update the live status and ADR to state:

```text
H11 package authority retained
H11E DIRECT_REFERENCE_BLOCKED withdrawn
no authoritative scientific blocker currently recorded
H12 metric repair active
```

## 14. Verification

```bash
pytest tests/test_l5_refinement.py        tests/test_l5_three_way_metrics.py        tests/test_l5_artifact_authority.py        tests/test_l5_leaf_admissibility.py        tests/test_l5_leaf_reseed.py

ruff check .
mypy src
python scripts/check_markdown_links.py
pytest
```

Then run the reduced P1/P3 diagnostic package smoke.

## 15. Corrected full rerun

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli   --config configs/l5_positive_control_v1.json   --outdir outputs/r3a_full_raw_h12   --stage all   --mode full

python scripts/package_r3a_campaign.py   --raw-root outputs/r3a_full_raw_h12   --results-root results/l5_reconstruction/r3a   --bundle-dir outputs/r3a_campaign_bundles   --replace-committed   --full-closeout
```

Record only the recomputed result:

```text
DIRECT_REFERENCE_BLOCKED
STITCHING_CONTROL_BLOCKED
NATURAL_DECOMPOSITION_BLOCKED
CONTROLLED_COVER_ACCEPTED
```

No expectation about which column will fail is part of H12.

**Recorded H12 outcome:** producer `9505a87`, `--mode full`, five probes, `package_kind=full_closeout`, `semantic_revalidation=true`, `campaign_blocker=STITCHING_CONTROL_BLOCKED`, `accepted_reconstruction=false`. Direct-vs-oracle Hausdorff and refinement are zero on all five probes (`direct_complete=true`). Source `h=c` reconstruction fails with unresolved `c` intervals. The natural column is not interpreted. L5 remains `parent_incomplete`.

---

## 16. File plan

```text
src/.../l5_reconstruction/comparison.py
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/leaf_family.py
src/.../l5_reconstruction/campaign_package.py

tests/test_l5_refinement.py
tests/test_l5_artifact_authority.py
tests/test_l5_leaf_admissibility.py
tests/test_l5_leaf_reseed.py
tests/test_project_dashboard.py

docs/CURRENT_STATUS.md
docs/ROADMAP.md
docs/README.md
docs/reference/DECISIONS.md
docs/methods/R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md
docs/methods/R3A_H12_DIRECT_COMPARISON_METRIC_REPAIR.md
```

## 17. Stop conditions

Stop and localize rather than retune if:

```text
corrected direct strict metrics still fail
semantic package recomputation disagrees with stored output
the same raw directions do not reproduce their fine hit mask
a strict boundary exclusion changes strict recall/false-positive counts
```

Do not tune source or natural continuation while the corrected direct column is
blocked.
