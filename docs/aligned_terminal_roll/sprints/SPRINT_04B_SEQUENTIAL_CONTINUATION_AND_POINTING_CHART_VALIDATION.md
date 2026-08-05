# Sprint 04B — Sequential Continuation and Pointing-Chart Validation

**Sprint status:** Experiments complete — awaiting Check-in 4B
**Milestone target:** M4B — Validated local two-dimensional pointing chart
**Check-in:** Check-in 4B
**Authorized by:** Check-in 4 (`CONTINUE WITH CHANGED SCOPE`, 2026-08-04)
**Primary architectures:** `IntersectingPairsAligned6R`, `URLikeAligned6R`
**Timebox:** Continuation and chart validation only
**HTML diagnostic:** May be updated for developer convenience, but is not a deliverable, acceptance criterion, CI requirement, or source of record.

## 1. Sprint objective

Replace the fixed-tangent, independently corrected Sprint 04 sample grid with a sequential predictor-corrector implementation that follows the fixed-position manifold using locally updated tangent frames.

Demonstrate that the resulting local sample set is:

- connected to the seed configuration;
- reversible along one-dimensional paths;
- locally two-dimensional after correction;
- noncollapsed and free of duplicate solutions;
- numerically stable under step-size and grid refinement;
- usable through the same continuation interface on both the intersecting-pairs and UR-like architectures.

Sprint 04B must establish that the sampled object is a numerically valid local chart of the fixed-position manifold, not merely a collection of corrected configurations.

## 2. Hypotheses under test

### H1 — Sequential continuation

Given a regular fixed-position configuration `q_k`, a predictor formed from a locally evaluated reduced tangent basis and corrected back to

```text
p(q) = p0
q6 = q6*
```

remains on the same connected local branch.

### H2 — Chart dimensionality

The corrected mapping

```text
(s, t) -> q(s, t)
```

has numerical differential rank two throughout the approved interior of the patch.

### H3 — Pointing dimensionality

The corresponding pointing map

```text
(s, t) -> d(q(s, t))
```

has numerical differential rank two throughout the approved interior of the patch.

### H4 — Reversibility

A sequential path continued forward and then retraced using locally updated tangent directions returns to the seed configuration within the stated tolerance.

### H5 — Refinement stability

Reducing the continuation step size while preserving the nominal physical patch extent does not qualitatively change:

- regularity classification;
- chart rank;
- pointing rank;
- branch identity;
- configuration and pointing values at shared chart coordinates.

### H6 — Architecture-specific topology

The continuation algorithm does not require an `SUUR` topology.

`IntersectingPairsAligned6R` may carry architecture-specific pair-intersection and compound-coordinate diagnostics. `URLikeAligned6R` must use the same continuation interface without a forced compound-joint interpretation.

## 3. Nonclaims

Sprint 04B does not establish:

- a one-dimensional fiber;
- global connectedness of the fixed-position manifold;
- global pointing coverage on `S2`;
- path-independent coordinates over a finite curved patch;
- a spherical four-bar;
- a Grashof classification;
- applicability to an exact UR model.

A small rectangular continuation loop is a diagnostic of numerical integration, local-frame transport, and branch tracking. It is not required to close exactly on a curved manifold.

## 4. Research lane

### 4.1 Precise claim

At a regular seed configuration of an aligned-terminal 6R chain, fixing position and terminal roll produces a local two-dimensional configuration manifold. Sprint 04B validates a numerical chart for that manifold and its two-dimensional pointing image.

### 4.2 Failure interpretations

| Observation | Interpretation |
|---|---|
| Position corrector fails repeatedly | predictor step is too large, seed is near a singularity, or local chart construction is invalid |
| Tangent-frame principal angle jumps | basis transport is discontinuous, branch switching occurred, or the manifold is poorly conditioned |
| Configuration chart rank drops to one | sampled coordinates collapsed to a curve or chart construction is defective |
| Pointing chart rank drops to one while configuration chart remains rank two | the local pointing map is degenerate at that sample |
| Forward/reverse path does not return | branch tracking, sign alignment, corrector selection, or integration accuracy is unresolved |
| Distinct chart coordinates map to duplicate configurations | chart is noninjective at the tested scale or corrector converged to the same branch point |
| Refinement changes qualitative rank classification | the result is numerically unresolved |
| Intersecting pairs cease to intersect | the architecture-specific compound grouping is not valid over the sampled patch |
| UR-like continuation requires `SUUR` metadata | topology is being imposed rather than inferred from the arm |

## 5. Algorithm requirements

### 5.1 Local reduced tangent frame

At every corrected configuration `q_k`:

1. evaluate the position Jacobian `J_p(q_k)`;
2. calculate a basis for `ker(J_p(q_k))`;
3. remove the terminal-roll direction `e6`;
4. return a two-column reduced tangent frame

```text
N_k in R^(6 x 2)
```

5. verify

```text
rank(J_d(q_k) N_k) = 2
```

The implementation must not reuse only the basis calculated at `q0`.

### 5.2 Tangent-frame alignment

Null-space bases have arbitrary signs and arbitrary rotations within the two-dimensional subspace. Before using `N_k` as a predictor frame, align it to the previously accepted frame `B_(k-1)`.

Use orthogonal Procrustes alignment:

```text
N_k^T B_(k-1) = U Sigma V^T
R = U V^T
B_k = N_k R
```

Record the principal angles between the previous and current tangent subspaces.

Reject a step when:

- the reduced basis loses rank;
- the pointing differential loses rank;
- the largest principal angle exceeds the configured continuation limit;
- the corrector fails to converge.

### 5.3 Sequential predictor

For chart increment

```text
Delta u = [Delta s, Delta t]^T
```

predict from the current accepted configuration:

```text
q_(k+1)^pred = q_k + B_k Delta u
```

The predictor must use `q_k`, not `q0`.

Set `q6 = q6*` before correction.

### 5.4 Position corrector

Correct the predictor to:

```text
p(q) = p0
q6 = q6*
```

Use a least-norm Newton correction in coordinates `q1,...,q5`:

```text
Delta q_(1:5) = -J_(p,1:5)^+ (p(q) - p0)
```

Record for every attempted and accepted point:

- predictor configuration;
- corrected configuration;
- predictor-to-corrector displacement;
- number of corrector iterations;
- final position residual;
- Jacobian singular values;
- tangent-frame principal angles;
- regularity classification;
- step-reduction count;
- termination label.

A step fails when:

- the corrector exceeds its iteration limit;
- the position residual exceeds tolerance;
- the corrected displacement exceeds the maximum trust radius;
- the required ranks are lost.

### 5.5 Step rejection and reduction

When a step fails:

1. reduce the requested step by a factor of two;
2. retry from the last accepted configuration;
3. permit at most three reductions;
4. terminate the path with an explicit failure label if no reduced step succeeds.

No failed step may be silently omitted from the result.

## 6. Chart construction

### 6.1 Center and axes

Start at the known regular seed `q0`.

Construct four sequential center rays:

- `+s`;
- `-s`;
- `+t`;
- `-t`.

Each ray must transport and align its tangent frame sequentially.

### 6.2 Grid population

Use a row-wise chart convention:

1. construct all centerline points `q(s_i, 0)`;
2. from each accepted centerline point, continue sequentially in `+t`;
3. return to the centerline point and continue separately in `-t`;
4. store chart coordinates `(s_i, t_j)` and the path used to reach every configuration.

The row-wise path defines the nominal chart. A second `t`-then-`s` construction is used only as a path-sensitivity diagnostic.

### 6.3 Configuration-chart differential

For every interior node, calculate central-difference chart derivatives:

```text
Q_s = [q(s + Delta s, t) - q(s - Delta s, t)] / (2 Delta s)
Q_t = [q(s, t + Delta t) - q(s, t - Delta t)] / (2 Delta t)
Q = [Q_s  Q_t]
```

Joint differences must be wrapped before division.

Report:

- both singular values of `Q`;
- chart rank;
- chart condition number;
- angle between `Q_s` and `Q_t`.

The configuration chart passes locally when:

```text
rank(Q) = 2
```

### 6.4 Pointing-chart differential

At the same interior nodes, calculate:

```text
D_s = [d(s + Delta s, t) - d(s - Delta s, t)] / (2 Delta s)
D_t = [d(s, t + Delta t) - d(s, t - Delta t)] / (2 Delta t)
D = [D_s  D_t]
```

Report:

- both singular values of `D`;
- pointing-chart rank;
- pointing-chart condition number;
- comparison with the analytical rank of `J_d N_red`.

The pointing chart passes locally when:

```text
rank(D) = 2
```

## 7. Path validation

### 7.1 True forward-and-reverse rays

For each architecture and for both chart directions:

1. continue `m` sequential steps from the seed;
2. start the reverse run from the accepted endpoint;
3. reverse and align the accepted tangent direction;
4. continue `m` sequential steps back toward the seed;
5. compare the returned configuration and pointing direction with the originals.

Report:

```text
epsilon_q = ||wrap(q_return - q0)||
epsilon_p = ||p(q_return) - p0||
epsilon_d = ||d(q_return) - d(q0)||
```

### 7.2 Rectangular commutator loop

Continue sequentially:

```text
+m steps in +s
+m steps in +t
+m steps in -s
+m steps in -t
```

Repeat with half the step size.

Report configuration, position, and pointing closure errors.

Exact closure is not required. The refined run must reduce the loop error consistently. Failure to decrease indicates unresolved integration, frame-transport, corrector, or branch-tracking behavior.

### 7.3 Alternate-path comparison

For selected interior targets, construct the nominal coordinate through:

```text
Path A: s then t
Path B: t then s
```

Report:

- wrapped joint-space difference;
- position difference;
- pointing difference.

Do not require exact equality. Require that the discrepancy decreases under step-size refinement and remains small relative to the patch dimensions.

## 8. Duplicate and collapse detection

For all distinct chart samples:

1. calculate wrapped joint-space pair distances;
2. flag duplicate configurations below the duplicate tolerance;
3. calculate nearest-neighbor distances;
4. calculate configuration displacement from `q0`;
5. calculate pointing displacement from `d0`;
6. verify that no complete row or column collapses.

The patch fails when:

- two distinct chart coordinates converge to the same configuration within duplicate tolerance;
- an entire chart row or column collapses;
- the numerical configuration-chart differential loses rank;
- the pointing samples collapse to a one-dimensional curve despite regular analytical pointing rank.

## 9. Refinement matrix

Run three chart configurations on each architecture.

| Run | Grid | Nominal step | Purpose |
|---|---:|---:|---|
| Baseline | `9 x 9` | `0.03` | Preserve comparison with Sprint 04 |
| Fine | `17 x 17` | `0.015` | Same nominal chart extent at twice the resolution |
| Compact | `9 x 9` | `0.015` | Smaller local patch for conditioning comparison |

At coordinates shared by baseline and fine runs, compare:

- corrected `q`;
- pointing direction `d`;
- rank classifications;
- architecture-specific pair distances where applicable.

The fine and compact runs must not reveal rank loss, duplicate solutions, or branch behavior hidden by the baseline grid.

## 10. Architecture-specific requirements

### 10.1 `IntersectingPairsAligned6R`

At every accepted sample, report:

- distance between the axes defining `U_A`;
- distance between the axes defining `U_B`;
- whether the architecture-specific compound-coordinate grouping remains defined.

The pair distances must remain below the configured intersection tolerance.

This diagnostic is specific to the architecture and must not be part of the general continuation interface.

### 10.2 `URLikeAligned6R`

Run the identical continuation and chart diagnostics without:

- invoking `suur_map`;
- requiring two universal-joint pairs;
- relabeling its topology as `SUUR`.

The UR-like chain passes based on its fixed-position manifold and pointing-chart evidence alone.

## 11. Software deliverables

Modify:

```text
src/grashof_workspace/spatial_experiments/
    continuation.py
    manifold_experiments.py
```

Add:

```text
src/grashof_workspace/spatial_experiments/
    chart_diagnostics.py
    continuation_paths.py

scripts/
    validate_pointing_chart.py

tests/
    test_spatial_sequential_continuation.py
    test_spatial_chart_diagnostics.py
    test_spatial_continuation_refinement.py
```

Recommended data structures:

```text
ContinuationStep
ContinuationPath
TransportedTangentFrame
ChartSample
ChartDifferential
PointingDifferential
ChartDiagnostics
LoopDiagnostics
RefinementComparison
```

Existing names may be retained when they cleanly provide the required responsibilities.

## 12. Experiment IDs

| ID | Experiment | Required result |
|---|---|---|
| `ATR_EXP_021` | Sequential forward/reverse rays | Both chart directions return within tolerance on both architectures |
| `ATR_EXP_022` | Intersecting-pairs transported chart | Regular, rank-two, noncollapsed chart; pair intersections persist |
| `ATR_EXP_023` | UR-like transported chart | Regular, rank-two, noncollapsed chart without imposed compound topology |
| `ATR_EXP_024` | Grid and step-size refinement | Shared-node values and rank classifications remain stable |
| `ATR_EXP_025` | Rectangular-loop refinement | Loop error decreases as the integration step is reduced |
| `ATR_EXP_026` | Alternate-path and duplicate analysis | No duplicate solutions; path discrepancy decreases under refinement |

Rename the description of `ATR_EXP_018` from:

```text
IP coordinate-map + closure
```

to:

```text
IP compound-coordinate definedness and round-trip consistency
```

Do not describe `ATR_EXP_018` as an independent closed-mechanism validation.

## 13. Provisional numerical thresholds

The following are initial engineering gates. Every result manifest must record the actual thresholds used.

| Metric | Initial threshold |
|---|---:|
| Position residual | `<= 1e-10 m` |
| Forward/reverse joint return | `<= 1e-6 rad` |
| Forward/reverse pointing return | `<= 1e-8` |
| Duplicate joint-space distance | `< 1e-6 rad` |
| Maximum corrector iterations | `20` |
| Maximum step reductions | `3` |
| Required interior configuration-chart rank | `2` at every approved interior sample |
| Required interior pointing-chart rank | `2` at every approved interior sample |
| Failed corrected samples | `0` in the approved benchmark patch |
| Regular samples | `100%` in the approved benchmark patch |
| Fine-grid shared-node joint difference | `<= 1e-4 rad` |
| Fine-grid shared-node pointing difference | `<= 1e-6` |
| Loop refinement | closure error decreases when the step is halved |

Do not use an unexplained absolute lower bound on the second chart singular value. Report both singular values, their ratio, the coordinate scale, and the inferred numerical rank.

Thresholds may be revised only when the experiment record explains why and Check-in 4B reviews the change.

## 14. Machine-readable result requirements

Every chart CSV must include:

```text
architecture
experiment_id
s
t
path_id
step_index
q1
q2
q3
q4
q5
q6
d_x
d_y
d_z
position_residual_m
corrector_iterations
correction_norm
step_reductions
rank_jp
rank_jpd
rank_jd_nred
chart_sigma_1
chart_sigma_2
chart_condition
pointing_sigma_1
pointing_sigma_2
pointing_condition
tangent_principal_angle_1
tangent_principal_angle_2
dist_ua_m
dist_ub_m
regular
label
```

Fields that do not apply to an architecture must be blank or explicitly marked `not_applicable`; they must not be fabricated.

The result manifest must include:

```text
repository_commit
working_tree_dirty
source_identifier
source_file_sha256
experiment_configuration_sha256
architecture_parameters
seed_configuration
step_sizes
grid_dimensions
rank_tolerances
position_tolerance
duplicate_tolerance
```

Decision-bearing results must be generated from a clean committed implementation revision.

## 15. Test requirements

Unit and integration tests must verify:

- each sequential predictor starts from the previous corrected configuration;
- the tangent frame is recomputed at every accepted point;
- Procrustes alignment prevents arbitrary basis sign flips and column swaps;
- terminal roll remains fixed;
- rejected steps are halved and retried;
- failed steps are reported rather than silently dropped;
- the reverse path begins at the actual forward endpoint;
- chart differential rank is two on a known regular synthetic patch;
- duplicate detection catches deliberately duplicated samples;
- a deliberately collapsed synthetic chart fails;
- the general continuation path does not require `SUUR`;
- the UR-like architecture does not invoke architecture-specific pair diagnostics;
- planar and Sprint 01–04 regression tests still pass.

## 16. Documentation deliverables

- create experiment specifications for `ATR_EXP_021`–`ATR_EXP_026`;
- update `VALIDATION_PLAN.md` with chart-rank, reversibility, duplicate, and refinement evidence;
- update `ASSUMPTION_RISK_REGISTER.md`, especially branch-tracking risk `R05`;
- create `checkins/CHECKIN_04B_POINTING_CHART_VALIDATION.md`;
- update `PROJECT_PLAN.md` and `ROADMAP.md` at Check-in 4B;
- retain the HTML readout only as a developer diagnostic.

## 17. Sprint acceptance criteria

Sprint 04B passes only when all of the following hold:

1. Sequential continuation predicts from the last corrected configuration.
2. The reduced tangent frame is recomputed and aligned at every accepted step.
3. Forward-and-reverse rays pass on both architectures and both chart directions.
4. Every approved interior sample has configuration-chart rank two.
5. Every approved interior sample has pointing-chart rank two.
6. No failed or duplicate samples occur in the approved benchmark patches.
7. Baseline, fine, and compact patches retain the same qualitative rank classification.
8. Shared baseline/fine coordinates agree within the configured tolerances.
9. Rectangular-loop error decreases under step refinement.
10. Pair intersections persist on `IntersectingPairsAligned6R`.
11. `URLikeAligned6R` passes without an imposed `SUUR` interpretation.
12. Complete configuration and pointing data are committed in machine-readable form.
13. Result provenance identifies a clean committed implementation.
14. All planar and spatial regression tests pass.
15. No fiber or spherical-four-bar implementation is introduced.

## 18. Check-in 4B decision matrix

### Case A — Both architectures pass

Authorize Sprint 05.

Use `IntersectingPairsAligned6R` as the controlled primary fiber benchmark and retain `URLikeAligned6R` as the practical parallel architecture.

### Case B — Intersecting-pairs passes; UR-like fails

Authorize fiber work only on `IntersectingPairsAligned6R`.

Open a separate investigation for the UR-like continuation failure. Do not generalize that failure to the terminal-roll reduction.

### Case C — UR-like passes; intersecting-pairs fails

Do not proceed to the proposed compound-topology fiber program.

Determine whether the failure comes from the continuation algorithm, the seed, or the intersecting-pairs architecture.

### Case D — Either chart loses numerical dimension under refinement

Do not open Sprint 05.

Reduce the patch size, revise chart construction, or identify the singular set.

### Case E — Reversibility fails or duplicate samples occur

Do not open Sprint 05.

Treat branch tracking as unresolved.

## 19. Check-in 4B questions

1. Did the sequential algorithm follow one connected local branch?
2. Is the corrected `(s,t)` configuration chart genuinely rank two?
3. Is its pointing image genuinely rank two?
4. Are chart results stable under step-size and grid refinement?
5. Did any samples collapse, duplicate, or jump branches?
6. Does the intersecting-pairs topology remain valid across its patch?
7. Does the UR-like architecture pass without topology being imposed?
8. Is the numerical evidence sufficient to define one scalar fiber constraint?
9. Which architecture is authorized as the primary Sprint 05 benchmark?

## 20. Explicitly deferred

- selection of `h(q)=c`;
- one-dimensional fiber continuation;
- spherical-axis concurrency;
- fixed spherical arc dimensions;
- spherical `RRRR`;
- McCarthy–Soh `T1`, `T2`, `T3`, `T4`;
- exact UR geometry;
- global pointing or dexterity claims.
