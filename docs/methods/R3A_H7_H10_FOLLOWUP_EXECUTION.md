# R3A-H7–H10 Follow-Up — Full-Mode Acceptance Semantics and Family Scope

**Status:** Proposed active follow-up after R3A-H0–H6  
**Project:** Back to Grashof — Mechanism-Based Workspace Characterization  
**Rung:** L5 spatial 5R  
**Source branch reviewed:** `R3A_Stiching_Stitch_Tests` at/after `e376a0db89fe335dcc9ef9f40f41650907a7c62e`  
**Primary target:** Make the full-mode R3A result mathematically evaluable, correctly scoped, reproducible, and small enough to review.  
**Non-goal:** This sprint does not require an accepted L5 reconstruction. An honest, localized failure is a valid closeout.

---

## 1. Why a follow-up sprint is required

R3A-H0–H6 successfully converted the original positive-control scaffold into a real evidence pipeline:

```text
manifest
  -> fixture
  -> decomposition-free direct truth
  -> source h=c control
  -> natural UURU leaves
  -> direct/source/natural comparison
  -> JSON-backed readout
```

The full five-point run is now generated and remains correctly unaccepted:

```text
accepted_reconstruction = false
campaign disposition = PARTIAL
```

That run exposed a narrower set of remaining defects.

### 1.1 Acceptance-law defects

The current `reconstruction_pass()` correctly refuses missing metrics, but it treats every `None` as failed evidence. Two `None` cases have different meanings:

```text
NOT_APPLICABLE
  Example: false-positive fraction when no strict-uncovered cells exist.

UNEVALUABLE
  Example: refinement delta when no refinement comparison was performed.
```

At pointing-complete probes such as P1/P2, `strict_uncovered_count = 0`. Their false-positive fraction is therefore not applicable, not failed. The current law makes complete `S^2` coverage impossible to accept.

The full run also writes `refinement_delta = null` for every comparison column. Because refinement is required by the gate, no production comparison can pass even when all other metrics are exact.

### 1.2 Re-seeding scope is stronger locally than globally

The follow-up re-seeding implementation now rebuilds a new `ClosedUURULeafProblem` from start/middle/end samples. That is real progress. However, the stored “symmetric branch distance” fields currently contain seed reconstruction errors, while whole-branch set distances remain diagnostic. Return and branch-status agreement are recorded but do not participate in the pass law.

The code therefore supports:

```text
local reseed consistency
```

more strongly than:

```text
same complete component reconstructed from a different seed
```

These scopes must be named and gated separately.

### 1.3 Family admissibility is still too global and permissive

Current family admission can inherit a global neighbor result and may treat unresolved chart overlap as acceptable. A leaf can therefore receive a family-level pass without every required audit incident to that leaf being resolved.

The family law must become leaf-scoped:

```text
component certificate
AND local/component reseed certificate
AND incident neighbor transversality
AND required chart transition compatibility
AND required parameter-domain coverage
```

### 1.4 Chart and lambda-bin requirements are not frozen

Full mode declares three charts and thirteen lambda bins per chart, but the leaf cap is global. Configured charts that produce no leaves can disappear from the interval ledger. A bin is also labeled `COMPLETE` when a single accepted sample exists, even though its boundaries, critical values, and topology are not resolved.

The program needs an explicit chart-atlas responsibility policy rather than assuming every chart must fill every bin or silently omitting empty chart domains.

### 1.5 Generated results have become too large for normal review

The latest full-mode commit adds multi-million-line direct-truth JSON files and large per-probe natural-family/source-control payloads. These artifacts are useful for reproducibility but are poor default Git history objects.

The project needs a results-retention contract:

```text
small committed summaries and figures
+
content-addressed raw campaign bundle outside normal source review
```

---

## 2. Scientific interpretation of the current full run

The current full run is already useful as a failure-localization baseline.

At the complete probes, the direct numerical reference agrees with the oracle at the sampled resolution, but the acceptance law rejects the result because:

```text
false_positive_fraction = null   # no strict-uncovered cells
refinement_delta = null          # refinement not computed
```

The source `h=c` control currently paints only a partial fraction of strict-covered cells; representative misses are roughly one third of the pointing sphere. The accepted natural-leaf union remains empty.

Therefore the correct order is:

1. repair metric applicability and compute refinement;
2. rerun the direct/source/natural gates;
3. only attribute failure to the natural decomposition after the source-control column passes.

The follow-up sprint must not tune natural leaves around a source-control failure.

---

## 3. Program decision

Create one follow-up program:

# R3A-H7–H10 — Full-Mode Acceptance and Family-Scope Follow-Up

```text
H7  metric applicability + actual refinement
H8  component-scoped re-seeding + leaf-scoped admission
H9  chart responsibility + parameter-domain completeness
H10 artifact authority + compact full-campaign closeout
```

R3B and L6 remain held until this follow-up closes.

---

# H7 — Metric applicability and actual refinement

## 4. Goal

Make the set-comparison law mathematically capable of accepting a valid pointing-complete or pointing-partial result while continuing to reject missing evidence.

## 5. Metric-state contract

Add an explicit metric-state enum:

```python
class MetricState(str, Enum):
    VALUE = "VALUE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNEVALUABLE = "UNEVALUABLE"
```

Preferred record:

```python
@dataclass(frozen=True, slots=True)
class ScalarMetric:
    state: MetricState
    value: float | None
    reason: str
```

Apply this to at least:

```text
missed_covered_fraction
false_positive_fraction
hausdorff_rad
refinement_delta
```

A backward-compatible JSON view may retain the numeric field while adding:

```text
<metric>_state
<metric>_reason
```

## 6. Denominator-aware rules

### 6.1 Covered-cell recall

```text
strict_covered_count > 0
  -> missed_covered_fraction must be VALUE and within tolerance

strict_covered_count == 0
  -> missed_covered_fraction = NOT_APPLICABLE
```

A reconstruction with no covered reference population cannot claim positive coverage from this metric alone.

### 6.2 Uncovered-cell false positives

```text
strict_uncovered_count > 0
  -> false_positive_fraction must be VALUE and within tolerance

strict_uncovered_count == 0
  -> false_positive_fraction = NOT_APPLICABLE and passes that one sub-gate
```

This is required for a pointing-complete reference where every strict cell is covered.

### 6.3 Hausdorff distance

Hausdorff is `VALUE` only when both reconstructed and reference direction sets are nonempty.

```text
reference nonempty + reconstruction empty -> VALUE = +infinity or explicit failed state
reference empty + reconstruction empty     -> NOT_APPLICABLE
otherwise                                  -> UNEVALUABLE only for numerical failure
```

Do not encode a failed empty reconstruction as `null`.

## 7. Refinement contract

Full-mode acceptance requires one actual refinement comparison.

For each of the five columns:

```text
direct vs oracle
source vs direct
natural vs direct
source vs oracle
natural vs oracle
```

compute metrics on two declared grids:

```text
coarse level = confirmation_level - 1
fine level   = confirmation_level
```

Use the same underlying direction/curve samples for both grids. Repaint those samples onto each grid and reclassify the oracle/direct reference at that grid.

Define normalized Hausdorff:

\[
\widehat H = H / \delta_{cell},
\]

where \(\delta_{cell}\) is the maximum cell diameter of that grid.

Define:

\[
\Delta_{refine}
=
\max
\left(
|m_f-m_c|,
|f_f-f_c|,
|\widehat H_f-\widehat H_c|
\right)
\]

using only metrics whose states are `VALUE` on both grids. `NOT_APPLICABLE` paired with `NOT_APPLICABLE` contributes zero. A transition between `VALUE` and `NOT_APPLICABLE` is `UNEVALUABLE` unless explicitly justified by a reference-domain topology change.

## 8. H7 acceptance

H7 passes when:

- a synthetic complete-sphere reference can pass with zero strict-uncovered cells;
- a synthetic negative/partial reference still requires feasible-set recall;
- empty reconstruction fails;
- missing refinement remains unresolved;
- full mode computes a non-null refinement record for every evaluable comparison;
- `ci` and `smoke` remain unable to issue campaign acceptance.

## 9. H7 files

```text
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/comparison.py
src/.../l5_reconstruction/sphere_grid.py
src/.../l5_reconstruction/direct_truth.py
configs/l5_positive_control_v1.json
tests/test_l5_three_way_metrics.py
tests/test_l5_refinement.py               # new
```

---

# H8 — Component-scoped re-seeding and leaf-scoped family admission

## 10. Goal

Separate local coordinate consistency from complete-component identity, then make family admission depend on the audits required by each individual leaf.

## 11. Re-seeding disposition

Add:

```python
class ReseedScope(str, Enum):
    LOCAL = "LOCAL"
    COMPONENT = "COMPONENT"

class ReseedDisposition(str, Enum):
    LOCAL_PASS = "LOCAL_PASS"
    COMPONENT_PASS = "COMPONENT_PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"
```

### 11.1 Local re-seed pass

Requires:

```text
same fixed lambda
seed reconstructed in wrapped Q
seed pointing agreement
child-tangent agreement
no chart singularity at the reseed
```

This is sufficient to say the local coordinate leaf is seed-consistent.

### 11.2 Component re-seed pass

Requires every local condition plus:

```text
symmetric wrapped-Q branch-set distance <= tolerance
symmetric pointing-set distance <= tolerance
return status compatible
branch status compatible
component/circuit identity compatible
both traces cover the claimed component scope
```

An open or budget-limited branch cannot earn `COMPONENT_PASS`.

Rename the existing fields so their meaning matches their contents. Do not place a seed error into a field named symmetric branch distance.

## 12. Leaf-scoped family admissibility

For each leaf, collect only audits incident to that leaf:

```text
reseed audit for leaf
neighbor transversality audits touching leaf
chart-transition audits touching leaf or its responsibility domain
parameter intervals containing leaf
```

Then compute:

```python
component_ok = leaf_component_status in accepted_component_statuses
reseed_ok = reseed.disposition == COMPONENT_PASS
neighbor_ok = all(required incident neighbor audits PASS)
chart_ok = all(required incident chart audits COMPATIBLE)
interval_ok = all(required intervals SATISFIED)

accepted_for_reconstruction = (
    component_ok
    and reseed_ok
    and neighbor_ok
    and chart_ok
    and interval_ok
)
```

A `LOCAL_ONLY` leaf may remain useful for visualization and local geometry but cannot enter the accepted union.

## 13. Unresolved chart overlap

Use one of two explicit scopes:

### Single-chart scope

```text
claim_scope = declared chart domain only
chart overlap outside that domain = NOT_REQUIRED
```

### Multi-chart atlas scope

```text
all responsibility transitions used by the reconstruction must be COMPATIBLE
UNRESOLVED overlap blocks family acceptance
```

Do not treat `UNRESOLVED` as favorable by default.

## 14. H8 acceptance

H8 passes when:

- a local rebuild can earn `LOCAL_PASS` without being called component-equivalent;
- a returned independently rebuilt component can earn `COMPONENT_PASS` only from symmetric set and circuit checks;
- open branches cannot earn component identity;
- a failed incident neighbor audit rejects only the leaves it touches;
- a leaf with no required neighbor evidence remains unresolved rather than inheriting a global pass;
- unresolved required chart overlap blocks reconstruction.

## 15. H8 files

```text
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/uuru_leaf.py
src/.../l5_reconstruction/leaf_family.py
tests/test_l5_leaf_reseed.py
tests/test_l5_leaf_transversality.py
tests/test_l5_chart_overlap.py
tests/test_l5_leaf_admissibility.py       # new
```

---

# H9 — Chart responsibility and parameter-domain completeness

## 16. Goal

Freeze which chart is responsible for which source configurations and replace sampled-bin language with an honest finite-domain coverage ledger.

## 17. Chart-atlas policy

Add a configuration object:

```python
@dataclass(frozen=True, slots=True)
class ChartAtlasPolicy:
    policy_id: str
    chart_ids: tuple[str, ...]
    canonical_assignment: str
    singularity_margin: float
    overlap_margin: float
    claim_scope: str
```

Recommended canonical assignment:

```text
At each source orientation, select the nonsingular chart maximizing |sin(beta)|.
Use deterministic chart-id tie breaking.
Retain a hysteresis/overlap band for chart-transition audits.
```

This creates a responsibility mask:

```text
source configuration -> canonical chart
```

The family ledger must include every configured chart even when it produces no leaves.

## 18. Capacity contract

Replace one global `max_natural_leaves_per_probe` with either:

```text
max_natural_leaves_per_chart
```

or an explicit total-cap allocation:

```text
chart_id -> leaf budget
```

Full mode must have enough capacity to sample every required responsibility bin, including fallback charts. A truncated budget is `UNRESOLVED`, not an empty scientific interval.

## 19. Interval vocabulary

Replace `COMPLETE` for a sampled bin with:

```python
class IntervalStatus(str, Enum):
    UNSAMPLED = "UNSAMPLED"
    SAMPLED_LOCAL = "SAMPLED_LOCAL"
    SAMPLED_COMPONENT = "SAMPLED_COMPONENT"
    SAMPLED_ADMISSIBLE = "SAMPLED_ADMISSIBLE"
    CRITICAL_OR_BOUNDARY = "CRITICAL_OR_BOUNDARY"
    UNRESOLVED = "UNRESOLVED"
    NOT_REQUIRED = "NOT_REQUIRED"
```

A bin is not “complete” merely because one accepted leaf exists.

For each required interval, record:

```text
responsible chart
lambda interval
seed count
leaf count
component-status counts
admissibility-status counts
duplicate groups
singular/critical samples
birth/death/merge evidence
budget exhaustion
interval status
```

## 20. Source-control vocabulary

Similarly replace source-control `COMPLETE` from “at least one returned component” with:

```text
RETURNED_COMPONENT_FOUND
```

Reserve `COMPONENT_COMPLETE` for evidence that all components at that `c` are found.

## 21. Family coverage gate

A declared-resolution set-cover claim requires:

```text
all required chart-responsibility intervals sampled
no required interval UNSAMPLED or UNRESOLVED
all leaves used in the union admissible
all required chart transitions compatible
critical/birth/death/merge events resolved or excluded from the claim domain
```

A finite sampled cover may pass as a declared-resolution cover without proving a global foliation. Keep those claims separate.

## 22. H9 acceptance

H9 passes when:

- every configured chart appears in the ledger;
- empty responsibility domains are marked `NOT_REQUIRED`, not silently omitted;
- full mode cannot be structurally short of its declared bin budget;
- accepted samples are labeled `SAMPLED_ADMISSIBLE`, not `COMPLETE`;
- unresolved required bins block natural reconstruction;
- source-control bins distinguish a returned component from component completeness.

## 23. H9 files

```text
configs/l5_positive_control_v1.json
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/spherical_chart.py
src/.../l5_reconstruction/leaf_family.py
src/.../l5_reconstruction/source_control.py
src/.../l5_reconstruction/readout.py
tests/test_l5_mode_fidelity.py
tests/test_l5_chart_responsibility.py      # new
tests/test_l5_family_intervals.py          # new
```

---

# H10 — Artifact authority, results compaction, and full-campaign closeout

## 24. Goal

Make campaign artifacts content-addressed and reviewable, rerun the full five-point experiment, and close with the first failing scientific column rather than a generic `PARTIAL` label.

## 25. Content-addressed stage authority

`StageArtifactRef` already exists. Make it operative.

Every stage summary records hashes for every required upstream and downstream artifact:

```text
path
sha256
config_hash
mode
probe scope
schema version
```

Before a downstream stage runs, recompute every input SHA-256 and refuse drift.

The manifest should include the source git commit and dirty-tree flag where available.

## 26. Results-retention policy

Do not commit multi-million-line raw per-target/per-leaf JSON by default.

Commit:

```text
campaign summary
per-probe comparison summary
compact direct-reference cell table
compact family/source-control interval summary
representative accepted/excluded leaves
figures and HTML
manifest with hashes and reproduction command
```

Publish or retain outside normal source review:

```text
all IK starts and clusters
all continuation samples
all raw direct-truth targets
all raw source-control traces
all raw natural-leaf traces
```

Recommended raw bundle:

```text
r3a_full_<config-hash>_<git-sha>.tar.zst
```

H11 packaging for a frozen full closeout:

```bash
python scripts/package_r3a_campaign.py \
  --raw-root outputs/r3a_full_raw \
  --results-root results/l5_reconstruction/r3a \
  --bundle-dir outputs/r3a_campaign_bundles \
  --replace-committed \
  --full-closeout
```

A `ci`/`smoke` or incomplete probe run is a diagnostic package and must not use `--full-closeout`. See [R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md](R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md).

Store its SHA-256 in the committed manifest. GitHub Actions artifacts, a release attachment, or an explicitly ignored local campaign directory are acceptable. Git LFS may be used only if the repository intentionally adopts it.

## 27. Branch hygiene

Before final review:

```text
rebase or merge current main
resolve the branch being behind main
regenerate only compact results
run CI on the rebased head
```

Do not mix a second full raw-data commit into the normal PR after compaction.

## 28. Full-campaign decision tree

Run full mode only after H7–H9 pass.

### Outcome A — Direct reference fails

```text
direct vs oracle fails or remains unresolved
```

Disposition:

```text
DIRECT_REFERENCE_BLOCKED
```

Do not interpret source or natural failures.

### Outcome B — Direct passes, source control fails

```text
source h=c vs direct/oracle fails
```

Disposition:

```text
STITCHING_CONTROL_BLOCKED
```

The failure belongs to source continuation, component discovery, curve density, or set painting—not yet to the four-bar decomposition.

### Outcome C — Source control passes, natural leaves fail

Disposition:

```text
NATURAL_DECOMPOSITION_BLOCKED
```

Now the failure can be attributed to child construction, family admission, interval completeness, or natural-leaf coverage.

### Outcome D — All five columns pass

Disposition:

```text
R3A_CONTROLLED_COVER_ACCEPTED
```

This means a declared-resolution controlled set cover only. It does not establish general 5R factorization or a global fiber bundle.

## 29. H10 acceptance

H10 passes when:

- stage hashes are generated and verified;
- the branch is current with `main`;
- committed results are compact and raw bundles are content-addressed;
- one full five-point run completes under the frozen config;
- the campaign reports the first failing column per probe and globally;
- no full acceptance is issued unless all five probes and all mandatory gates pass;
- `CURRENT_STATUS.md` is updated to the actual closeout, including failure if applicable.

## 30. H10 files

```text
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/cli.py
src/.../l5_reconstruction/comparison.py
src/.../l5_reconstruction/readout.py
scripts/package_r3a_campaign.py              # new
.gitignore                                   # raw campaign directory policy
.github/workflows/ci.yml
docs/CURRENT_STATUS.md
docs/reference/DECISIONS.md                  # ADR-051 closeout
results/l5_reconstruction/r3a/               # compact artifacts only
```

---

## 31. Proposed ADR-051

### ADR-051 — R3A acceptance metrics distinguish not-applicable from unevaluable evidence

**Decision:** A missing numerical value is not sufficient to determine pass/fail. R3A comparison metrics carry explicit `VALUE`, `NOT_APPLICABLE`, or `UNEVALUABLE` state. Zero-denominator metrics such as false-positive fraction on an all-covered reference are `NOT_APPLICABLE`; missing refinement is `UNEVALUABLE`. Full-campaign acceptance requires a computed refinement comparison, leaf-scoped family admissibility, declared chart responsibility, resolved required parameter intervals, and content-addressed artifacts.

**Reason:** Treating every `None` as failure makes valid complete coverage impossible, while treating every `None` as pass fabricates evidence. Explicit applicability preserves conservative gates without making the intended theorem untestable.

**Consequence:** R3A-H0–H6 artifacts remain valid historical diagnostics but are re-evaluated under H7–H10 before any controlled cover is accepted. R3B and L6 remain held.

---

## 32. Commit sequence

Recommended commits:

```text
1. docs: record R3A-H7–H10 follow-up contract and ADR-051 draft
2. fix: add denominator-aware metric states and two-resolution refinement
3. fix: split local/component reseed scope and leaf-scoped family admission
4. fix: freeze chart responsibility and parameter-domain interval semantics
5. chore: enforce artifact hashes and compact full-campaign outputs
6. results: rerun full R3A and record the first failing scientific column
```

Keep generated compact results in the final commit only.

---

## 33. Definition of done

The follow-up sprint is complete when the software can distinguish all of these without ambiguity:

```text
valid metric not applicable
missing metric unevaluable
local leaf consistency
complete component identity
leaf component status
leaf family admissibility
sampled interval
required interval completeness
direct-reference failure
source-stitching failure
natural-decomposition failure
accepted controlled cover
```

A scientifically honest failure after these gates is a successful sprint closeout.

---

## 34. Nonclaims

This follow-up does not claim:

- that source `h=c` fibers will pass after metric repair;
- that any existing `EXACT_ON_COMPONENT` leaf will become family-admissible;
- that all three spherical charts define one invariant leaf family;
- that a declared-resolution set cover is a global foliation;
- that R3A transfers to generic 5R manipulators;
- that spatial crank/winding behavior is a workspace predicate;
- that R3B or L6 may begin before the controlled gate closes.
