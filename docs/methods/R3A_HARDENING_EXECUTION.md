# R3A-H — Natural-Leaf Evidence Hardening Sprint

**Project:** Back to Grashof — Mechanism-Based Workspace Characterization  
**Repository:** `mfbailey91/Back-to-Grashof---Workspaces`  
**Base:** `main` after PR #17 (`959463b4bec24c9a9fc2240142d0f4cfc189f8d2`)  
**Scientific rung:** L5 spatial 5R  
**Program:** R3A five-point `SURU -> UURU` positive control  
**Status:** H0–H6 CONTRACT (superseded as the live gate by R3A-H7–H10)  
**Primary target:** Make the existing R3A implementation capable of issuing an honest declared-resolution reconstruction result.  
**Successor:** [R3A_H7_H10_FOLLOWUP_EXECUTION.md](R3A_H7_H10_FOLLOWUP_EXECUTION.md)

---

## 1. Sprint decision

The R3A architecture is retained.

The following implementation elements are accepted as the correct foundation:

```text
controlled U_shoulder-R_elbow-U_wrist 5R source
analytical direction and point-completeness oracle
five frozen Cartesian probes
independent source-chain target-direction IK
rotated Z-Y-Z spherical closure charts
frozen-lambda UURU branch kernel
source h=c continuation control
three-column campaign namespace
```

The sprint does **not** introduce another kinematic pivot. It hardens the evidence chain around the implementation already merged.

The blocking review result is:

> Individual source-embedded UURU branches can be constructed, but family-level re-seeding, transversality, chart compatibility, completeness, independent set comparison, stage authority, and evidence rendering are not yet enforced strongly enough to support an accepted reconstruction.

The sprint therefore converts several current metadata fields into actual acceptance gates.

---

## 2. Scientific disposition before the sprint

```text
positive-control geometry and oracle       implemented
direct IK kernel                           implemented, not yet campaign-authoritative
source h=c control                         implemented, incomplete family accounting
frozen-lambda UURU branch kernel           implemented
leaf component residual checks             implemented
re-seeding consistency                     placeholder / non-evaluative
family transversality                      proxy / non-evaluative
chart overlap                              heuristic / incomplete
family completeness                        not represented
three-way comparison                       oracle-centered, not direct-reference-centered
negative-probe reconstruction gate         incorrect
stage dependency graph                     not enforced
rendered evidence                          mostly placeholder
accepted R3A reconstruction                false
general 5R factorization                   unresolved
```

No L5 status is promoted by starting this sprint.

---

## 3. Core semantic split

R3A-H separates three dispositions that must never be collapsed.

### 3.1 Leaf component status

Does one frozen-geometry one-DOF child reproduce one source-parent component over the declared continuation scope?

```text
EXACT_GLOBAL
EXACT_ON_COMPONENT
LOCAL_ONLY
APPROXIMATE
REJECTED
UNRESOLVED
```

This is issued from closure, fixed-position, pose-map, family-coordinate, rank, singularity, and component-completeness evidence.

### 3.2 Family admissibility status

Can this component participate in the sampled parent cover?

```text
PASS
FAIL
UNRESOLVED
```

This requires:

```text
real re-seeding consistency
actual child-tangent transversality
duplicate/component semantics
chart overlap compatibility
declared lambda interval accounting
```

### 3.3 Reconstruction disposition

Does the accepted family reconstruct the independent parent pointing image at the frozen confirmation resolution?

```text
PASS_AT_DECLARED_RESOLUTION
PARTIAL
REJECTED
UNRESOLVED
```

The acceptance law is:

```text
accepted_for_reconstruction =
    leaf_component_status in {EXACT_GLOBAL, EXACT_ON_COMPONENT}
    and family_admissibility_status == PASS
    and parameter_scope_status in {COMPLETE_AT_DECLARED_RESOLUTION,
                                   BOUNDED_COMPONENT_SCOPE}
```

A returned branch is not automatically an admissible family member.

---

## 4. Stage graph and artifact authority

The executable stage graph is:

```text
manifest
  -> fixture
  -> truth
  -> source-control
  -> leaves
  -> compare
  -> render
```

A stage may not mark itself `COMPLETE` unless every required upstream artifact exists and matches:

```text
program_id
schema_version
config_hash
campaign mode
probe scope
upstream artifact SHA-256
software commit SHA when available
```

Every stage writes:

```text
stage
stage_status
scientific_disposition
config_hash
mode
probe_ids
input_artifacts
input_hashes
output_artifacts
limitations
```

`compare` must refuse missing direct truth, source-control, or natural-family artifacts.  
`render` must either consume real artifacts or visibly issue `SCAFFOLD_NO_DATA`; placeholder plots may not use evidence-like filenames without that watermark.

---

# 5. Hardening slices

## R3A-H0 — Evidence semantics, stage DAG, and deterministic identity

### Goal

Stop incomplete or missing evidence from looking complete before changing the numerical algorithms.

### Primary files

```text
src/grashof_workspace/spatial_experiments/l5_reconstruction/models.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/cli.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/comparison.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/readout.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/uuru_leaf.py
tests/test_l5_reconstruction_models.py
tests/test_l5_five_point_campaign.py
tests/test_l5_three_way_metrics.py
```

### Changes

1. Add typed stage-artifact records and prerequisite validation.
2. Make `manifest` mark only `manifest=COMPLETE`.
3. Refuse `compare` unless `truth`, `source-control`, and `leaves` exist for every requested probe.
4. Refuse cross-mode and cross-probe resume.
5. Replace Python `hash()` geometry identity with canonical SHA-256.
6. Split:
   - `leaf_component_status`;
   - `family_admissibility_status`;
   - `accepted_for_reconstruction`.
7. Mark current family audits `UNRESOLVED` until H1-H3 evaluate them.
8. Fix negative-probe semantics:
   - an empty reconstruction cannot pass;
   - partial-workspace probes must recover their strict feasible subset and exclude strict infeasible cells.
9. Strict feasible/infeasible direct `UNRESOLVED` cells block point classification.
10. Placeholder figures receive `SCAFFOLD_NO_DATA`, or rendering refuses them.

### H0 pass gate

- no missing-input campaign can mark `compare=COMPLETE`;
- no zero-hit reconstruction can pass P3 or P5;
- identical geometry hashes are stable across separate Python processes;
- current committed scaffold remains `PARTIAL` / `UNRESOLVED`;
- all JSON remains finite.

---

## R3A-H1 — Independent direct-reference cell model and comparison contract

### Goal

Make the direct source-chain solve a real independent comparison column rather than a nullable oracle-agreement summary.

### Primary files

```text
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/direct_truth.py
src/.../l5_reconstruction/sphere_grid.py
src/.../l5_reconstruction/comparison.py
tests/test_l5_direct_truth_oracle_agreement.py
tests/test_l5_direct_truth_solver.py
tests/test_l5_three_way_metrics.py
```

### New confirmation-cell record

```text
cell_id
vertex_or_barycenter_direction
oracle_status = FEASIBLE / INFEASIBLE / BOUNDARY
direct_status = FOUND / NOT_FOUND_AT_DECLARED_BUDGET / UNRESOLVED
direct_cluster_count
best_position_residual_m
best_pointing_error_rad
strict_reference_eligible
```

The analytical oracle and direct numerical solve remain separate.

### Required comparisons

For every probe, report:

```text
direct vs oracle
source h=c vs resolved direct
natural UURU vs resolved direct
source h=c vs oracle
natural UURU vs oracle
```

### Direct-reference pass rules

- `FOUND` in strict oracle-infeasible cells is a false positive.
- `NOT_FOUND_AT_DECLARED_BUDGET` or `UNRESOLVED` in strict oracle-feasible cells blocks direct completeness.
- Boundary cells do not enter strict precision/recall denominators.
- Oracle labels never overwrite direct statuses.
- Direct unresolved fraction is explicit.

### H1 pass gate

At smoke resolution, direct truth agrees with the analytical oracle on every strict resolved cell for all five probes, and unresolved strict cells prevent—not fabricate—a pass.

---

## R3A-H2 — Real re-seeding consistency and component identity

### Goal

Test whether a leaf is intrinsic to the fixed chart/family coordinate rather than an artifact of one seed.

### Primary files

```text
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/uuru_leaf.py
src/.../l5_reconstruction/leaf_family.py
tests/test_l5_leaf_reseed.py
tests/test_l5_uuru_leaf.py
tests/test_l5_uuru_leaf_certificate.py
```

### Required algorithm

For each candidate component, select at least:

```text
start sample
middle-arclength sample
end sample
```

At each sample:

1. recover the same chart coordinates;
2. force the original `lambda_fixed`, not a newly chosen family value;
3. instantiate a new independent `ClosedUURULeafProblem`;
4. correct onto the branch;
5. continue in both directions with the same continuation budget;
6. compare original and re-seeded branches.

### Re-seeding metrics

```text
reseed_id
seed_s
lambda_error_rad
symmetric_wrapped_q_distance_rad
symmetric_pointing_distance_rad
tangent_error
returned_match
branch_status_match
component_identity
status
```

Aggregate:

```text
max_symmetric_q_distance_rad
max_symmetric_pointing_distance_rad
max_tangent_error
all_component_ids_match
reseed_status
```

### Required negative controls

- same component re-seeded from another point: pass;
- deliberately changed `lambda`: fail;
- chart-singular reseed: unresolved;
- truncated continuation budget: unresolved, not pass;
- seed-dependent synthetic curve: fail.

### H2 pass gate

No self-comparison remains. A leaf cannot receive family admissibility `PASS` unless all required re-seeds pass.

---

## R3A-H3 — Actual transversality, duplicate semantics, and chart overlap

### Goal

Prove that neighboring accepted leaves add a second parent direction and that chart copies do not fabricate extra coverage.

### Primary files

```text
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/spherical_chart.py
src/.../l5_reconstruction/leaf_family.py
tests/test_l5_leaf_transversality.py
tests/test_l5_leaf_dedup.py
tests/test_l5_chart_overlap.py
```

### Leaf tangent

At a source/child sample, compute the one-dimensional null tangent from the actual child Jacobian:

\[
J_{\mathrm{child}}(x)t_x=0.
\]

Map its physical coordinates into source joint space and normalize:

\[
t_s = \operatorname{normalize}(t_x[2:7]).
\]

Do not use an arbitrary column of `ker(J_p)` as a proxy.

### Cross-leaf direction

For neighboring family values \(\lambda_i,\lambda_{i+1}\):

1. establish nearest compatible source points or a transported correspondence;
2. compute the wrapped source displacement;
3. divide by wrapped \(\Delta\lambda\);
4. project into the parent nullspace;
5. remove the leaf-tangent component.

Evaluate:

\[
\sigma_{\min}
\left(
\begin{bmatrix}
t_s & t_\lambda
\end{bmatrix}
\right)
\geq \sigma_{\mathrm{configured}}.
\]

### Family audit scope

Evaluate every neighboring accepted pair, not only the first two discovered leaves.

### Duplicate and crossing states

```text
DUPLICATE_SAME_COMPONENT
DISTINCT_COMPATIBLE
CROSSING_DIFFERENT_TANGENT
INCOMPATIBLE_COMPONENT
UNRESOLVED
```

### Chart overlap

For overlapping chart leaves, verify:

```text
source-Q set correspondence
chart-coordinate transform
family-parameter correspondence
component identity
pointing-set correspondence
```

`abs(d_ab-d_ba)` is not a chart-compatibility test.

### H3 pass gate

- every accepted family interval has verified rank-two sweep;
- duplicates are removed in source space;
- chart overlap is either compatible or explicitly unresolved;
- configured `minimum_transversality_sigma` is enforced.

---

## R3A-H4 — Family completeness, source-control completeness, and mode fidelity

### Goal

Represent what portions of the one-parameter family and the control foliation are actually known.

### Primary files

```text
src/.../l5_reconstruction/models.py
src/.../l5_reconstruction/source_control.py
src/.../l5_reconstruction/leaf_family.py
configs/l5_positive_control_v1.json
tests/test_l5_source_control_fibers.py
tests/test_l5_source_control_dedup.py
tests/test_l5_source_control_reconstruction.py
tests/test_l5_leaf_family_p1.py
```

### Source-control records per `c`

```text
c
expected_seed_count
projected_seed_count
continued_component_count
returned_count
open_count
singular_count
unresolved_count
deduplicated_component_ids
parameter_interval_status
```

Unresolved intervals are derived from actual missing/open/singular components, not from whether the entire fiber list is empty.

### Natural-family interval records

```text
chart_id
lambda_interval
sampled_lambda_values
accepted_leaf_ids
rejected_leaf_ids
unresolved_leaf_ids
duplicate_groups
critical_values
birth_death_merge_events
interval_status
```

### Mode fidelity

`--mode full` must use the frozen full budgets:

```text
lambda bins
leaf cap
continuation steps
reseed samples
truth Sobol starts
truth max_nfev
source c values
confirmation grid
```

CI-specific small budgets use explicit overrides or a named `ci` mode; they must not silently redefine `full`.

### H4 pass gate

Every missing `c` or `lambda` interval is visible, full mode honors configuration, and no finite sample bank is described as a complete global foliation.

---

## R3A-H5 — Honest reconstruction metrics and acceptance law

### Goal

Issue a declared-resolution set result only when direct truth, source control, and accepted natural leaves all support it.

### Primary files

```text
src/.../l5_reconstruction/comparison.py
src/.../l5_reconstruction/models.py
tests/test_l5_three_way_metrics.py
tests/test_l5_source_control_reconstruction.py
tests/test_l5_five_point_campaign.py
```

### Metrics

For both source-control and natural-leaf reconstructions:

```text
strict feasible recall
strict infeasible false-positive fraction
resolved-direct recall
resolved-direct false-positive fraction
angular Hausdorff distance
boundary-to-boundary error
unresolved direct fraction
unresolved family fraction
component discrepancy
multiplicity discrepancy
refinement delta
```

### Positive probe pass

```text
direct strict agreement passes
source control passes direct-reference metrics
natural family passes direct-reference metrics
strict feasible recall >= threshold
strict false positives <= threshold
Hausdorff <= cell-diameter threshold
refinement stable
no blocking family interval unresolved
```

### Negative probe pass

A negative probe must reconstruct the **partial feasible set** and preserve strict infeasible directions. Merely refusing `COMPLETE` is insufficient.

### Campaign pass

All five points pass their set-reconstruction gates and their point classification matches the oracle.

### H5 pass gate

The empty reconstruction fixture fails all five reconstruction gates. A synthetic perfect reconstruction passes all five. Boundary-only ambiguity never fabricates a strict pass.

---

## R3A-H6 — Evidence readout, CI, and closeout

### Goal

Make generated artifacts correspond to actual data and close the R3A positive-control campaign honestly.

### Primary files

```text
src/.../l5_reconstruction/readout.py
src/.../l5_reconstruction/cli.py
src/grashof_workspace/project_dashboard.py
.github/workflows/ci.yml
tests/test_l5_five_point_campaign.py
tests/test_project_dashboard.py
results/l5_reconstruction/r3a/*
docs/CURRENT_STATUS.md
docs/reference/DECISIONS.md
```

### Real probe figures

```text
arm_geometry.png
direct_oracle_vs_ik.png
source_control_curves.png
natural_leaf_components.png
accepted_vs_excluded_leaves.png
three_way_cell_comparison.png
selected_leaf_overlay.png
selected_leaf_residuals.png
family_parameter_coverage.png
```

Every figure includes:

```text
probe id
mode
config hash
stage status
scientific disposition
declared resolution
accepted/excluded status
```

No dummy lines or repeated one-frame GIFs are evidence artifacts.

### CI

Default CI adds a reduced end-to-end smoke with:

```text
P1 deep complete
P3 inner incomplete
manifest -> fixture -> truth -> source-control -> leaves -> compare -> render
```

The full five-point campaign may remain an explicit workflow/manual artifact if too expensive for every commit, but it must be reproducible from the frozen config.

### Closeout outcomes

#### PASS_AT_DECLARED_RESOLUTION

```text
R3A positive-control set reconstruction accepted at frozen resolution;
not a general 5R factorization;
R3B transfer authorized;
L6 remains blocked until the declared R3 dependency decision is revisited.
```

#### PARTIAL

```text
one or more reconstruction columns incomplete;
failure localized to direct truth, source control, leaf component,
family admissibility, chart coverage, or set comparison;
R3B and L6 held.
```

#### REJECTED

```text
the frozen-lambda UURU family fails the controlled reconstruction
despite adequate direct truth and source-control reconstruction;
positive-control construction rejected over the declared scope.
```

#### UNRESOLVED

```text
numerical budgets, singularities, missing intervals, or stage artifacts
prevent a qualified result.
```

---

# 6. File-level implementation map

| File | Required change |
|---|---|
| `models.py` | Split statuses; stage artifact records; direct cell records; detailed reseed/transversality/family interval records |
| `cli.py` | Enforce stage DAG, artifact hashes, mode/probe consistency, transactional statuses |
| `direct_truth.py` | Produce confirmation-cell truth without oracle rewriting; count strict unresolved |
| `sphere_grid.py` | Stable cell identities and shared painting/reference utilities |
| `uuru_leaf.py` | Deterministic SHA-256 geometry hash; fixed-lambda reseed constructor; actual child tangents |
| `leaf_family.py` | Real re-seeding, all-neighbor transversality, chart overlap, interval completeness, post-audit acceptance |
| `source_control.py` | Per-`c` component accounting and unresolved intervals |
| `comparison.py` | Direct-centered five-way comparison; negative recall; unresolved blocking |
| `readout.py` | Real artifacts or explicit scaffold watermark |
| `project_dashboard.py` | Distinguish scaffold, implemented kernels, and accepted reconstruction |
| `ci.yml` | Reduced two-probe end-to-end R3A smoke |
| tests | Replace permissive schema assertions with positive and negative scientific gates |

---

# 7. Required regression tests

The sprint is not complete without tests that would fail the current implementation.

```text
test_compare_refuses_missing_truth_source_and_leaves
test_manifest_marks_only_manifest_complete
test_geometry_hash_stable_across_processes
test_empty_negative_reconstruction_fails
test_strict_feasible_unresolved_blocks_direct_complete
test_reseed_reconstructs_same_component
test_changed_lambda_reseed_fails
test_budget_limited_reseed_is_unresolved
test_transversality_uses_child_tangent
test_colinear_neighbor_leaves_fail_sigma_gate
test_all_neighbor_pairs_audited
test_chart_overlap_requires_source_correspondence
test_returned_leaf_not_accepted_before_family_audits
test_full_mode_honors_frozen_budgets
test_source_control_reports_missing_c_intervals
test_direct_source_natural_metrics_are_independent
test_p1_p3_end_to_end_smoke
test_placeholder_render_is_watermarked_or_refused
```

Avoid assertions that allow either `PASS` or `FAIL` for the same fixture.

---

# 8. Recommended commit sequence

```text
1. docs: freeze R3A hardening evidence contract
2. fix(r3a): enforce stage DAG and deterministic artifact identity
3. fix(r3a): make direct confirmation an independent reference
4. feat(r3a): implement real leaf re-seeding audits
5. feat(r3a): implement child-tangent transversality and chart overlap
6. feat(r3a): track source and lambda family completeness
7. fix(r3a): harden five-point set-reconstruction acceptance
8. feat(r3a): replace scaffold plots with evidence readouts
9. ci(r3a): add reduced end-to-end campaign smoke
10. results/docs: regenerate and close R3A-H
```

Do not commit regenerated `results/l5_reconstruction/r3a/` before the acceptance semantics stabilize.

---

# 9. Definition of done

R3A-H is complete only when:

- stage authority is enforced;
- geometry and artifacts are reproducibly identified;
- direct truth remains independent from the oracle;
- re-seeding actually reconstructs and compares branches;
- transversality uses actual child tangents;
- chart overlap is checked in source space;
- family acceptance is recomputed after all audits;
- source and natural family intervals expose incompleteness;
- negative probes reconstruct their feasible subsets;
- source control gates decomposition interpretation;
- all five points receive honest set results;
- evidence plots contain real data;
- no L5 or L6 claim exceeds the closeout result.

---

# 10. Non-goals

This sprint does not:

- prove a global 5R foliation theorem;
- transfer the result to generic 5R architectures;
- begin L6;
- promote crank/winding to a workspace predicate;
- build the twelve-family numerical atlas;
- add joint limits;
- claim a computational advantage before timing evidence exists.

Rule discovery and the numerical virtual-crank atlas remain downstream of successful source-to-child-to-parent reconstruction.
