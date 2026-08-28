# R3A-H13G — Narrow Corrective Follow-Up for Source-Control Evidence Semantics

**Project:** Back to Grashof — Mechanism-Based Workspace Characterization
**Rung:** L5 spatial 5R
**Parent result:** H12 five-probe closeout remains `STITCHING_CONTROL_BLOCKED`
**Starting code:** `main` after PR #22 / merge commit `201b10f7779c671b9da2a8d88e4da83ab8b9cc9e`
**Sprint character:** corrective, diagnostic, non-expansive
**Proposed policy token:** `h13g_evidence_safe_v1`
**Implementation:** Corrective software landed. Diagnostic P1/P4/P5 packaged under gitignored `outputs/` as `package_kind=diagnostic` with `campaign_blocker=STITCHING_CONTROL_BLOCKED`. Freeze is not claimed. H12 hub remains current.

## 1. Purpose

H13A–F correctly preserved the H12 authority boundary and exposed the source-control failure, but the review found five evidence-semantics defects that must be corrected before another source-control freeze attempt:

1. the shared continuation engine launches the negative ray with both tangent and step sign reversed, so the two sign changes cancel;
2. projected seed clusters are capped before tracing, even though local seed clusters are samples rather than components;
3. great-circle SLERP rasterization leaves the exact `h(d)=n·d=c` small circle and can paint unsupported directions;
4. one global branch status collapses different positive- and negative-ray termination causes;
5. distant exploratory projection failures are counted as missing-component evidence.

H13G repairs those defects only. It does not tune natural UURU leaves, start R3B, advance L6, activate the behavior atlas, or replace the H12 hub.

## 2. Locked invariants

The patch must preserve all of the following:

- `configs/l5_positive_control_v1.json` remains unchanged and has no `policy_version`;
- `results/l5_reconstruction/r3a/compact_manifest.json` remains the recorded `full_closeout`;
- the recorded raw-bundle digest remains `d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec`;
- `campaign_blocker=STITCHING_CONTROL_BLOCKED` and `accepted_reconstruction=false` remain authoritative;
- H13E and H13F configs remain historical diagnostic inputs and are not silently mutated;
- H13G is selected only by `source_control.policy_version=h13g_evidence_safe_v1`;
- every H13G campaign mode has `allows_full_campaign_disposition=false`;
- natural UURU remains `NOT INTERPRETED`;
- L5 remains `parent_incomplete`;
- no source-control pass is claimed from this code patch alone.

## 3. Work packages

### H13G-A — Correct the shared signed-ray contract

Change `continue_implicit_branch` so direction is encoded exactly once:

```python
t_cur = t0.copy()
ds_local = sign * ds_mag
```

Do not negate both `t_cur` and `ds_local` on the negative ray.

Add `BranchRayRecord` to preserve, for each ray:

- direction (`positive` or `negative`);
- termination cause;
- accepted step count;
- accepted arclength;
- endpoint state;
- rejection-reason counts.

Required regression:

```text
<delta_x_positive, t0> > 0
<delta_x_negative, t0> < 0
```

The unit-circle fixture must demonstrate opposite first steps. The parabola fixture must not produce endpoint closure.

### H13G-B — Make trace termination ray-local and conservative

The H13G trace classifier consumes `BranchRayRecord` rather than inferring all termination meaning from one global `branch_status`.

Overall precedence when there is no seed return:

```text
valid plus/minus endpoint closure
singular or critical endpoint
corrector failure
budget exhaustion
open or unclassified
```

Plus/minus endpoint meeting is eligible only when both opposite rays genuinely exist and both ended by declared-budget exhaustion. A singular or failed ray cannot be converted into a closed loop because its endpoint happens to lie near the other endpoint.

Serialize:

```text
positive_ray_termination
negative_ray_termination
```

alongside the existing aggregate termination.

### H13G-C — Replace projected-cluster truncation with trace-and-cover

Projection still pre-clusters the discovery bank and applies an explicit candidate projection budget. It no longer interprets the number of projected local clusters as a component count.

At each `c`:

1. project candidate configurations;
2. cluster only near-identical projected representatives;
3. select one unexplained projected representative;
4. trace one source fiber;
5. mark every projected representative lying within `trace_cover_q_tol_rad` of that traced fiber as explained;
6. repeat until no unexplained representatives remain or `max_source_traces_per_c` is exhausted.

The blocking condition becomes:

```text
unexplained projected representatives remain after the trace-work budget
```

not:

```text
more than N projected local clusters existed before tracing
```

Record:

```text
trace_attempt_count
explained_projected_seed_count
failed_trace_seed_count
unexplained_projected_seed_count
trace_budget_exhausted
```

`attempted_seed_count` remains for compatibility but is explicitly labeled:

```text
trace_attempts_not_expected_components
```

### H13G-D — Separate required and exploratory projection failures

Candidates inside `seed_h_window` are locally justified. If none exist, the nearest candidate is promoted as a required fallback.

Projection failures are split into:

```text
blocking_projection_failure_count
    required/local candidates only

diagnostic_projection_failure_count
    exploratory distant candidates
```

Exploratory failures remain visible but do not by themselves prove that a source component is missing.

Candidate-cap truncation remains blocking because it can still hide unattempted discovery evidence.

### H13G-E — Replace SLERP painting with corrected kinematic refinement

Raw continuation samples remain unchanged on each fiber.

For every adjacent pair of source-Q samples:

1. compute the wrapped-Q midpoint;
2. correct the midpoint back to `p(q)=p*` and `n·d(q)=c`;
3. evaluate the real chain pointing `d(q)`;
4. recurse until the pointing-space segment is within the declared fraction of the confirmation-cell diameter.

Closed fibers include a corrected closing segment. No unconstrained great-circle interpolation is used.

Every added raster sample must satisfy:

```text
position residual <= configured source tolerance
abs(n dot d - c) <= configured source tolerance
```

Record:

```text
rasterized_pointing_samples
rasterization_complete
rasterization_failure_count
rasterization_budget_exhausted
max_rasterized_position_residual_m
max_rasterized_h_residual
```

Any incomplete required-fiber rasterization keeps the corresponding `c` bin unresolved.

### H13G-F — Diagnostic pilot only

Add:

```text
configs/l5_positive_control_h13g_source_pilot_v1.json
```

All modes remain unable to issue a campaign disposition. The first campaign is limited to:

```text
P1_DEEP_COMPLETE
P4_OUTER_COMPLETE
P5_OUTER_INCOMPLETE
```

Do not package with `--full-closeout`. Do not use `--replace-committed`.

## 4. Files

### Production

```text
src/grashof_workspace/spatial_experiments/branch_continuation.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/source_control.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/source_control_h13g.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/models.py
configs/l5_positive_control_h13g_source_pilot_v1.json
```

### Tests

```text
tests/test_spatial_v06h3_branch_continuation.py
tests/test_l5_source_control_h13g.py
tests/test_l5_h13_locked_invariants.py
```

### Documentation shipped in this patch

```text
docs/methods/R3A_H13G_NARROW_CORRECTIVE_FOLLOW_UP.md
```

### Bookkeeping deferred until diagnostic evidence exists

```text
docs/CURRENT_STATUS.md
docs/ROADMAP.md
docs/reference/DECISIONS.md
```

Do not mark H13G active, frozen, or closed merely because the corrective code lands. Update the live status ledger, roadmap state, and ADR log with the actual pilot disposition after the diagnostic campaign is packaged.

## 5. Acceptance gates

### Software gate

```bash
ruff check .
mypy src
python scripts/check_markdown_links.py
pytest tests/test_spatial_v06h3_branch_continuation.py \
       tests/test_l5_source_control_h13g.py \
       tests/test_l5_h13_locked_invariants.py
pytest
```

### Signed-ray gate

- positive and negative first accepted steps leave the seed on opposite tangent sides;
- a finite-budget open fixture cannot be called plus/minus closed;
- ray-local termination is serialized for both rays;
- mixed singular/budget evidence remains visible.

### Trace-and-cover gate

- one traced fiber can explain multiple projected representatives on the same sampled component;
- increasing projected sample density along an already traced fiber does not automatically create cap exhaustion;
- unexplained representatives, not raw cluster count, control trace-budget blocking;
- candidate-cap exhaustion remains explicit.

### Projection-authority gate

- required/local projection failures block;
- exploratory projection failures remain diagnostic;
- when no local candidate exists, one nearest fallback is required;
- JSON reports both failure classes.

### Rasterization gate

- no SLERP-generated directions enter source occupancy;
- every refined sample is produced from a corrected source-Q state;
- every refined sample preserves `p=p*` and `h=c` within tolerance;
- unresolved correction or recursion depth remains blocking;
- halving the curve-segment fraction is reserved for a later copied-config convergence test, not tuned in this patch.

### Authority gate

- H12 config, hub, digest, blocker, and acceptance state remain unchanged;
- H13G packages only as `diagnostic`;
- no H13G result is copied into `results/l5_reconstruction/r3a/`;
- no natural-family acceptance code is changed.

## 6. Pilot commands

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13g_source_pilot_v1.json \
  --outdir outputs/r3a_h13g_source_pilot \
  --stage all \
  --mode full \
  --probe P1_DEEP_COMPLETE \
  --probe P4_OUTER_COMPLETE \
  --probe P5_OUTER_INCOMPLETE

python scripts/package_r3a_campaign.py \
  --raw-root outputs/r3a_h13g_source_pilot \
  --results-root outputs/r3a_h13g_source_pilot_compact \
  --bundle-dir outputs/r3a_campaign_bundles \
  --config configs/l5_positive_control_h13g_source_pilot_v1.json
```

Expected package assertions:

```text
package_kind = diagnostic
allows_full_campaign_disposition = false
full_closeout_eligible = false
recorded H12 hub digest unchanged
campaign blocker remains STITCHING_CONTROL_BLOCKED unless every source gate passes
```

## 7. Stop conditions

Stop and localize rather than increasing all budgets when:

- opposite-ray regression fails;
- endpoint closure changes when the two ray budgets are made asymmetric;
- trace-and-cover leaves unexplained representatives that move substantially when `trace_cover_q_tol_rad` changes modestly;
- corrected midpoint projection repeatedly fails on otherwise regular raw segments;
- rasterization depth is exhausted on required fibers;
- source occupancy still changes materially when only the corrected-refinement spacing is halved;
- candidate-cap exhaustion persists after same-component projected representatives are consumed by traced fibers.

## 8. Exit statement

H13G closes only as a corrective software sprint when the project can state:

> The source-control implementation now launches genuinely opposite continuation rays, preserves ray-local termination evidence, allocates trace work by unexplained projected representatives, distinguishes required from exploratory projection failures, and paints occupancy only from corrected kinematic states. The H12 scientific closeout remains unchanged, and no source-control freeze or natural-UURU interpretation has yet been claimed.
