# Cursor Guide — R3A-H7–H10 Full-Mode Acceptance Follow-Up

**Authority:** `docs/methods/R3A_H7_H10_FOLLOWUP_EXECUTION.md`  
**Starting point:** `R3A_Stiching_Stitch_Tests` after the full-mode H6 regeneration  
**Recommended branch:** `r3a-h7-h10-acceptance-followup`

---

## 1. Branch preparation

The reviewed branch is ahead of and behind `main`. Start by preserving the full-mode artifact commit, then rebase or merge current `main` before implementation.

```bash
git switch R3A_Stiching_Stitch_Tests
git status --short
git fetch origin

git switch -c r3a-h7-h10-acceptance-followup
# Choose the repository's normal policy:
git rebase origin/main
# or:
# git merge origin/main
```

Freeze the current full-run summary before deleting or compacting raw artifacts:

```bash
cp results/l5_reconstruction/r3a/campaign.json /tmp/r3a_h6_campaign.json
sha256sum /tmp/r3a_h6_campaign.json
```

Run baseline checks:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" --config-settings editable_mode=strict
pytest
ruff check .
mypy src
python scripts/check_markdown_links.py
```

Do not begin by tuning continuation budgets. Correct the evidence law first.

---

# H7 — Metric applicability and refinement

## 2. `models.py`

Add:

```python
class MetricState(str, Enum):
    VALUE = "VALUE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNEVALUABLE = "UNEVALUABLE"

@dataclass(frozen=True, slots=True)
class ScalarMetric:
    state: MetricState
    value: float | None
    reason: str
```

Either replace scalar fields in `PointingSetMetrics` or add state companions:

```text
missed_covered_fraction_state
false_positive_fraction_state
hausdorff_rad_state
refinement_delta_state
```

Backward compatibility is less important than unambiguous semantics, but the readout loader should handle pre-H7 JSON as legacy/unevaluable.

## 3. `comparison.py` denominator helpers

Implement:

```python
def fraction_metric(num: int, den: int, *, zero_denominator_reason: str) -> ScalarMetric:
    if den == 0:
        return ScalarMetric(MetricState.NOT_APPLICABLE, None, zero_denominator_reason)
    return ScalarMetric(MetricState.VALUE, num / den, "computed")
```

Then:

```python
def metric_within_limit(metric: ScalarMetric, limit: float) -> bool:
    if metric.state is MetricState.NOT_APPLICABLE:
        return True
    if metric.state is not MetricState.VALUE or metric.value is None:
        return False
    return metric.value <= limit
```

Do not use one generic `None` path.

## 4. Hausdorff semantics

Implement explicit empty-set cases:

```python
if reference_dirs and not reconstructed_dirs:
    hausdorff = ScalarMetric(VALUE, inf, "empty reconstruction")
elif not reference_dirs and not reconstructed_dirs:
    hausdorff = ScalarMetric(NOT_APPLICABLE, None, "both sets empty")
elif not reference_dirs and reconstructed_dirs:
    hausdorff = ScalarMetric(VALUE, inf, "reconstruction over empty reference")
else:
    hausdorff = ScalarMetric(VALUE, computed, "computed")
```

JSON-safe serialization may encode `inf` as a failed state with `value=None`; do not silently turn it into an unevaluable metric. A dedicated `FAILED_VALUE` state is also acceptable.

## 5. Two-resolution metrics

Add a reusable function:

```python
def evaluate_set_on_grid(
    *,
    grid: SphereGrid,
    reference_labels: tuple[CellClass, ...],
    reconstructed_dirs: tuple[Vec3, ...],
    reference_dirs: tuple[Vec3, ...],
) -> PointingSetMetrics:
    ...
```

Add:

```python
def compute_refinement_delta(
    coarse: PointingSetMetrics,
    fine: PointingSetMetrics,
) -> ScalarMetric:
    ...
```

Recommended inputs:

```text
coarse grid = level confirmation_level - 1
fine grid   = level confirmation_level
same reconstructed direction samples on both
same direct/oracle logic rebuilt on both
```

Do not compare unrelated discovery and confirmation seed banks as though they differ only in grid resolution.

## 6. `write_compare_stage()`

Build a coarse and fine metric bundle for every column. Store:

```json
{
  "fine": {...},
  "coarse": {...},
  "refinement": {...}
}
```

If retaining the existing top-level metric fields, make them aliases of `fine` and add the refinement state.

## 7. H7 tests

Add/strengthen:

```text
test_complete_reference_no_uncovered_cells_can_pass_fp_gate
test_partial_reference_still_requires_recall_and_precision
test_missing_refinement_is_unevaluable
test_full_metric_path_computes_refinement
test_empty_reconstruction_has_failed_hausdorff_not_missing_hausdorff
test_ci_smoke_cannot_accept_even_with_perfect_metrics
```

Run:

```bash
pytest tests/test_l5_three_way_metrics.py tests/test_l5_refinement.py
```

Commit:

```text
fix: make R3A metric applicability and refinement evaluable
```

---

# H8 — Component re-seeding and leaf-scoped admission

## 8. `models.py`

Add `ReseedScope` and `ReseedDisposition`. Replace ambiguous aggregate `PASS` with explicit scope.

Suggested fields:

```text
local_seed_q_error
local_seed_pointing_error
local_lambda_error
local_tangent_error
symmetric_branch_q_distance
symmetric_branch_pointing_distance
return_status_match
branch_status_match
circuit_or_component_match
scope
 disposition
```

## 9. `leaf_family.py` re-seeding

In `audit_reseeded_component()`:

1. rebuild at start/middle/end;
2. continue each rebuild under the same component budget;
3. compute both directed distances for Q and pointing;
4. take the symmetric maximum;
5. require return/branch compatibility for component scope;
6. keep local seed errors separate.

Pseudo-law:

```python
local_pass = lambda_ok and seed_q_ok and seed_pointing_ok and tangent_ok
component_pass = (
    local_pass
    and original_returned
    and reseeded_returned
    and symmetric_q_ok
    and symmetric_pointing_ok
    and return_status_match
    and branch_status_match
    and component_identity
)
```

For open branches:

```text
local pass possible
component pass forbidden
```

## 10. Leaf-scoped audit graph

Create an adjacency map:

```python
neighbor_audits_by_leaf: dict[str, list[TransversalityAudit]]
chart_audits_by_leaf: dict[str, list[ChartOverlapAudit]]
intervals_by_leaf: dict[str, list[FamilyIntervalRecord]]
```

Compute each leaf's admissibility from its own required records. Do not use one global `neighbor_all_pass` flag.

## 11. Required versus optional chart transitions

Add `required: bool` and `claim_scope` to chart-overlap records.

Rules:

```text
required + COMPATIBLE   -> pass
required + UNRESOLVED   -> unresolved
required + INCOMPATIBLE -> fail
not required            -> not applicable
```

## 12. H8 tests

Add:

```text
test_open_reseed_can_local_pass_but_not_component_pass
test_component_pass_requires_symmetric_branch_distances
test_return_mismatch_blocks_component_pass
test_leaf_only_inherits_incident_neighbor_audits
test_unresolved_required_chart_overlap_blocks_leaf
test_optional_chart_overlap_is_not_required
```

Run:

```bash
pytest tests/test_l5_leaf_reseed.py \
       tests/test_l5_leaf_transversality.py \
       tests/test_l5_chart_overlap.py \
       tests/test_l5_leaf_admissibility.py
```

Commit:

```text
fix: scope R3A reseeding and family admission per leaf
```

---

# H9 — Chart responsibility and interval completeness

## 13. Config changes

Replace ambiguous global leaf cap with:

```json
{
  "chart_atlas_policy": {
    "policy_id": "max_sin_beta_v1",
    "canonical_assignment": "max_abs_sin_beta",
    "singularity_margin": 0.05,
    "overlap_margin": 0.10,
    "claim_scope": "multi_chart_declared_domain"
  },
  "campaign_modes": {
    "full": {
      "max_natural_leaves_per_chart": 13
    }
  }
}
```

Retain a total safety cap only as an explicit sum of per-chart allocations.

## 14. Canonical chart assignment

In `spherical_chart.py` add:

```python
def chart_quality(chart: SphericalClosureChart, R: Mat3) -> float:
    coords = chart.decompose(R)
    return abs(sin(coords.beta))


def canonical_chart(charts, R, *, tie_break_order):
    ...
```

Record chart responsibility on every discovery configuration and leaf seed.

## 15. Interval ledger

Always initialize intervals from all configured charts and all configured bins. Then overlay sampled leaves.

Never derive chart IDs only from leaves that happened to be discovered.

Use interval states from the execution spec. `SAMPLED_ADMISSIBLE` is not equivalent to `COMPLETE`.

## 16. Source-control records

Rename `parameter_interval_status="COMPLETE"` to an evidence-specific label:

```text
RETURNED_COMPONENT_FOUND
OPEN_ONLY
SINGULAR
UNRESOLVED
```

A global source-control cover can still pass from the set comparison even without a component-completeness theorem, but the component claim remains narrow.

## 17. H9 tests

Add:

```text
test_all_configured_charts_appear_even_without_leaves
test_chart_responsibility_is_deterministic
test_full_budget_covers_required_bins_by_policy
test_sampled_admissible_is_not_called_complete
test_missing_required_bin_blocks_natural_cover
test_not_required_chart_bin_does_not_block
test_source_returned_component_not_named_component_complete
```

Run:

```bash
pytest tests/test_l5_mode_fidelity.py \
       tests/test_l5_chart_responsibility.py \
       tests/test_l5_family_intervals.py \
       tests/test_l5_source_control_fibers.py
```

Commit:

```text
fix: freeze R3A chart responsibility and parameter-domain scope
```

---

# H10 — Artifact authority and compact closeout

## 18. Stage hashing

Implement:

```python
def file_sha256(path: Path) -> str:
    ...
```

Every stage writes a `StageResult` whose input and output refs include the recomputed content hash.

Before every stage, validate all required input hashes. The stage summary itself should also be hashed by the next stage.

## 19. Raw/compact result split

Add directories:

```text
outputs/r3a_full_raw/             # ignored, full traces
results/l5_reconstruction/r3a/    # compact committed evidence
```

Add script:

```text
scripts/package_r3a_campaign.py
```

Responsibilities:

```text
validate stage hashes
write compact per-probe summaries
select representative leaves/traces
copy figures/readouts
create raw tar.zst bundle
write raw bundle SHA-256 into manifest
```

Suggested `.gitignore`:

```gitignore
outputs/r3a_full_raw/
outputs/r3a_campaign_bundles/
```

Do not delete the current full artifact until a compact summary and raw-bundle hash have been produced.

## 20. Global failure-localization enum

Add:

```python
class CampaignBlocker(str, Enum):
    DIRECT_REFERENCE_BLOCKED = "DIRECT_REFERENCE_BLOCKED"
    STITCHING_CONTROL_BLOCKED = "STITCHING_CONTROL_BLOCKED"
    NATURAL_DECOMPOSITION_BLOCKED = "NATURAL_DECOMPOSITION_BLOCKED"
    CONTROLLED_COVER_ACCEPTED = "CONTROLLED_COVER_ACCEPTED"
```

Compute the first failing column globally and per probe.

The full campaign may close successfully with any of the first three outcomes.

## 21. Full rerun

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_v1.json \
  --outdir outputs/r3a_full_raw \
  --stage all \
  --mode full

python scripts/package_r3a_campaign.py \
  --raw-root outputs/r3a_full_raw \
  --results-root results/l5_reconstruction/r3a \
  --bundle-dir outputs/r3a_campaign_bundles \
  --replace-committed \
  --full-closeout
```

Then regenerate dashboards:

```bash
PYTHONPATH=src python -m grashof_workspace.project_dashboard --results-root results
```

## 22. H10 tests and checks

Add:

```text
test_artifact_hash_drift_is_refused
test_compact_results_exclude_raw_solver_banks
test_raw_bundle_hash_matches_manifest
test_global_blocker_localizes_direct_first
test_global_blocker_localizes_source_before_natural
test_global_blocker_localizes_natural_after_source_pass
test_full_acceptance_requires_all_five_probes
```

Run:

```bash
pytest
ruff check .
mypy src
python scripts/check_markdown_links.py
```

Commit code before results:

```text
chore: content-address and compact R3A campaign artifacts
```

Commit compact results separately:

```text
results: rerun full R3A and localize the controlling failure
```

---

## 23. Status/ADR closeout

Update `CURRENT_STATUS.md` with exactly one of:

```text
R3A direct reference blocked
R3A source stitching control blocked
R3A natural decomposition blocked
R3A controlled cover accepted at declared resolution
```

Do not use generic `PARTIAL` as the only human-readable conclusion.

Append ADR-051 from the execution document to `docs/reference/DECISIONS.md`.

Keep:

```text
general 5R factorization unresolved
R3B held unless the controlled operation is stable
L6 held
```

---

## 24. Pull request checklist

```text
[ ] branch rebased/merged with current main
[ ] H7 metric-state tests pass
[ ] full refinement metrics computed
[ ] H8 component-scope tests pass
[ ] leaf-scoped audit graph implemented
[ ] H9 chart responsibility frozen
[ ] all configured charts represented in interval ledger
[ ] artifact content hashes enforced
[ ] full raw campaign kept out of normal source diff
[ ] compact results committed
[ ] one global blocker/acceptance outcome recorded
[ ] pytest
[ ] ruff check .
[ ] mypy src
[ ] markdown link check
[ ] CI green on final head
```

---

## 25. Stop conditions

Stop tuning natural leaves when:

```text
direct reference has not passed
or
source h=c control has not passed
```

Stop claiming component equivalence when:

```text
only local reseed consistency has passed
or
branch return/component coverage is budget-limited
```

Stop committing raw artifacts when:

```text
the compact result and content-addressed raw bundle carry the same reproducibility information
```
