# R3A-H13H — Source-Control Failure Localization and Convergence

**Status:** PROPOSED SPRINT — implementation and numerical validation remain to be done.

**H13H-0 receipt:** [R3A_H13H_BASELINE_RECEIPT.md](R3A_H13H_BASELINE_RECEIPT.md) records the located historical pilot and the protected hashes. Source policy validated: false.

**H13H-2 diagnosis:** [R3A_H13H_CONTINUATION_DIAGNOSIS.md](R3A_H13H_CONTINUATION_DIAGNOSIS.md) classifies the selected continuation cases. `accepted_reconstruction`: false. The production solver is unchanged.

**H13H-3 diagnosis:** [R3A_H13H_RASTER_DIAGNOSIS.md](R3A_H13H_RASTER_DIAGNOSIS.md) classifies the selected raster cases. Raster midpoints stay on the chord section. `accepted_reconstruction`: false. Continuation is unchanged.

**H13H-4 study:** [R3A_H13H_CONVERGENCE_STUDY.md](R3A_H13H_CONVERGENCE_STUDY.md) records the P1/P4/P5 matrix. No three-probe candidate. `accepted_reconstruction`: false.

**H13H-5 validation:** [R3A_H13H_FIVE_PROBE_VALIDATION.md](R3A_H13H_FIVE_PROBE_VALIDATION.md) retains `REQUIRED_INTERVALS_UNRESOLVED`. No frozen policy. P2/P3 were not evaluated. `accepted_reconstruction`: false.

**Authority:** [ROADMAP.md](../ROADMAP.md) owns future dependency gates. [CURRENT_STATUS.md](../CURRENT_STATUS.md) owns scientific status. This document is the detailed H13H execution plan.

| Field | Value |
|---|---|
| Project | Characterization of Manipulator Workspaces / Back to Grashof |
| Prepared | November 15, 2026, America/Los_Angeles |
| Starting implementation | H13G commit `81f1e2059040b74e503d166f4e6588922ddafb8c` on `R3A_H13_locked_invariants` |
| Recorded main checkpoint | PR #22, merge commit `201b10f7779c671b9da2a8d88e4da83ab8b9cc9e` |
| Suggested working branch | `r3a-h13h-source-convergence` |
| Successor | H13I all-column rerun, conditional on validated source policy |

## 1. Sprint objective

Establish whether the existing source-control implementation can reconstruct the controlled 5R pointing image at the declared resolution, with explainable continuation, valid kinematic rasterization, and stable results under independently increased numerical effort.

The immediate work starts from the **already implemented and already piloted H13G**, rather than rebuilding H13G. The pilot reportedly accounted for all projected representatives but retained required bins with exhausted or unresolved traces, incomplete rasterization, and excessive coarse/fine metric change. The raw pilot outputs, when available, are the starting evidence. The committed ADR is a description of that evidence, not a substitute for the traces needed to diagnose it. [S1, S2]

H13H has two legitimate outcomes:

- **Source policy validated:** one frozen source policy passes the source-specific gates on all five probes and passes the independent convergence study.
- **Source control remains blocked:** a reproducible, bounded set of failures identifies what still prevents validation, with a concrete next correction or a documented geometric limitation.

A diagnostic repair sprint may close honestly with the second outcome. It must not label an unresolved source policy as validated.

### Milestone and follow-on boundary

**H13H ends with a source-only five-probe evidence package and a handoff.** It preserves the H12 authoritative hub and `accepted_reconstruction=false`.

**H13I is the proposed follow-on:** rerun all columns with the validated source policy, evaluate the frozen natural UURU family, and apply the existing strict full-closeout procedure. Source success alone does not accept natural reconstruction, prove a complete parent, or establish a global foliation.

This separation reflects the current software: the existing `compare` stage requires natural-family artifacts, and the full-closeout packager requires the full campaign. H13H therefore needs a small diagnostic evaluator that reuses the existing metrics without manufacturing natural artifacts. [S7, S8]

## 2. Verified starting point and scientific boundaries

### 2.1 What is already established

| Area | Starting evidence | Consequence for this sprint |
|---|---|---|
| Direct reference | H12 direct-versus-oracle comparison passes all five probes under its declared grids and metric rules. | Preserve those definitions and independently verify direct validity in new runs. |
| Source stitching | The recorded blocker is `STITCHING_CONTROL_BLOCKED`. | This is the workstream being repaired and tested. |
| H13G implementation | Opposite-ray sign correction, ray-local termination, trace-and-cover, separated projection-failure classes, and corrected kinematic rasterization exist. | Reuse them; test remaining failures. |
| H13G pilot | P1/P4/P5 reportedly explained all projected representatives, while required-bin, rasterization, and refinement failures remain. | Explain the residual failures before adding numerical effort. |
| Natural UURU | Not interpreted while source control is blocked. | Preserve construction and tuning settings; shared-engine regressions are checked separately. |
| R3C | A0/A1 exporter and A2 census exist; UURU is the actual A3 family queue. | Atlas work remains a downstream handoff. |
| L5 / L6 | L5 `parent_incomplete`; L6 `scaffold_only`. | H13H does not promote either rung. |

Sources: latest status, ADR-062, H13G implementation contract, and the merged A2 closeout. [S1–S3, S11]

### 2.2 The source problem being solved

At a fixed Cartesian point `p_star`, the regular source fiber for a selected scalar value `c` satisfies

\[
F_c(q)=
\begin{bmatrix}
p(q)-p^*\\
n^\mathsf{T}d(q)-c
\end{bmatrix}=0.
\]

For the controlled 5R arm this is a four-equation system in five joint coordinates. Continuation follows its regular one-dimensional branches. The reconstruction collects the **actual FK pointing directions** from those traced configurations over the declared `c`-domain.

The analytical direction oracle supplies the independent comparison and the justified domain calculation. An analytical small circle may appear as a plot overlay; it must never be inserted into reconstructed occupancy. [S4, S5]

### 2.3 Preserve these controls

- Preserve the original H12 config, compact hub, historical raw-bundle digest, and interpretation. The recorded bundle digest is `d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec`.
- Preserve H13E, H13F, and H13G evidence-producing configs. Create new versioned configs for experiments.
- Keep source geometry, five probes, direct IK policy, discovery bank policy, Sobol seeds, comparison grids, strict-boundary margin, and acceptance tolerances fixed.
- Keep natural charts, lambda bins, leaf admission rules, natural budgets, and reconstruction rules fixed.
- Keep all H13H campaign modes diagnostic-only: `allows_full_campaign_disposition=false`.
- Do not widen closure, deduplication, trace-cover, residual, or acceptance tolerances to obtain a pass.
- Retain non-required analytical boundary records and their directions in the source comparison. Boundary treatment does not authorize removing inconvenient directions.
- Retain `RETURNED_SET_FOUND` scope. Explaining a finite seed bank does not establish `COMPONENT_COMPLETE`.
- Preserve unknown, singular, budget-limited, and failed-correction outcomes as such.

A necessary correction to a shared solver must be isolated, supported by a counterexample, and accompanied by default-behavior and affected-call-site regression checks. “Source-focused” does not imply that changes to a shared engine have no downstream effects.

## 3. Acceptance contract

### 3.1 Existing set gates remain unchanged

For each probe, retain both `source_vs_direct` and `source_vs_oracle`. The direct reference must pass before source results can be evaluated.

| Existing quantity | Limit | Interpretation |
|---|---:|---|
| Hausdorff distance | At most 1.0 confirmation-cell diameter | Angular distance, normalized using the appropriate grid's diameter. |
| Missed strict-covered fraction | At most 0.05 | At most 5% under the existing strict-cell rule. |
| Strict false positives | Zero | Preserve existing legitimate not-applicable handling when no strict-negative denominator exists. |
| Within-run refinement metric | At most 0.02 | Dimensionless coarse/fine change defined by the existing evaluator. |
| Reconstruction | Nonempty and required metrics evaluable | Missing metrics cannot pass. |
| Required source intervals | None unresolved | A favorable occupancy score cannot override a blocked interval. |
| Required-fiber rasterization | Complete under declared checks | No hidden correction, residual, or recursion failure. |
| Discovery/trace work | No relevant exhausted cap or unexplained representative | Finite-bank scope remains explicit. |

Apply the existing evaluators rather than reproducing their numerical law in a second implementation. [S6]

### 3.2 Do not conflate two kinds of refinement

The existing `compute_refinement_delta` compares the same reconstructed directions on coarse and fine grids. It takes the maximum absolute change of:

1. Missed strict-covered fraction.
2. Strict false-positive fraction.
3. Hausdorff distance divided by that grid's maximum cell diameter.

That is **within-run grid consistency**. It does not test convergence when continuation effort, spacing between slices, or sampling along a curve changes. H13H must retain that metric and separately test **between-run numerical convergence**. [S6]

### 3.3 New H13H cross-run criterion

The following is a proposed sprint criterion, not an existing repository gate. Freeze it before examining experimental outcomes.

Compare two source settings produced by the same code SHA, differing only in the numerical configuration fields declared for that experiment. Different config hashes are expected. Both runs must use the same fine grid (level 3), the same coarse grid (level 2), and identical scientific oracle/direct reference data and label masks. A before/after repair comparison with different code belongs to diagnostic verification, not a single-axis numerical-convergence pair.

First require both runs to pass the existing run-level direct/source gates with their attached two-resolution refinement records. Both runs must also have no required unresolved bin, relevant exhausted cap, or required-fiber raster failure, and zero strict false-positive hits. These requirements apply to the candidate and stronger runs on all five probes.

Then compare scalar values and occupancy separately on each fixed grid and for each reference column. Do not call the run-level acceptance function on a coarse-only metric record that lacks its attached refinement:

- The absolute change of each applicable scalar metric—miss fraction, false-positive fraction, and cell-normalized Hausdorff—is at most **0.02**.
- Among strict-covered reference cells, the fraction whose occupied/unoccupied state changes is at most **0.02**.

Write the occupancy condition as

\[
\delta_{\mathrm{occ}}
=\frac{|(A\triangle B)\cap C_{\mathrm{strict}}|}
{|C_{\mathrm{strict}}|}
\le 0.02.
\]

Here `A` and `B` are occupancy masks on the same grid; `C_strict` is that comparison's strict-covered reference mask. Empty covered denominators remain unevaluable. Existing legitimate not-applicable false-positive metrics remain not applicable; other missing data blocks the comparison.

Record every scalar change and occupancy disagreement, not just their maximum. This prevents unchanged aggregate scores from hiding holes that move between runs. Each run must also independently satisfy the existing within-run refinement threshold.

A single converged parameter axis is insufficient. After individual-axis checks, run a combined stronger profile to detect interactions.

## 4. Work breakdown and sequencing

The effort estimate is **6–8 engineering days plus measured campaign runtime**, assuming the failures can be localized without a new continuation method. It is a planning estimate, not a deadline guarantee. If diagnosis identifies a larger mathematical or algorithmic issue, close the sprint as blocked with the reproducer and revise the next work package.

| Work package | Outcome | Dependency | Planning allowance |
|---|---|---|---:|
| H13H-0 | Baseline, inputs, and invariant receipt | None | 0.5 day |
| H13H-1 | Source-only evaluator, failure inventory, replay records | H13H-0 | 1–1.5 days |
| H13H-2 | Continuation causes localized and demonstrated defects repaired | H13H-1 | 1–2 days |
| H13H-3 | Rasterization causes localized and demonstrated defects repaired | H13H-1 | 1–2 days |
| H13H-4 | P1/P4/P5 controlled convergence study | H13H-2 and H13H-3 | 1 day plus runs |
| H13H-5 | Frozen-policy P2/P3 validation and combined five-probe check | H13H-4 | 0.5–1 day plus runs |
| H13H-6 | Reproducible source evidence package and H13I handoff | H13H-5, or a documented stop | 0.5 day |

H13H-2 and H13H-3 can proceed in parallel after the diagnostic schema is stable. Give the shared source wrapper and serialization fields one integration owner.

### H13H-0 — Establish a reproducible baseline

**Tasks**

1. Inspect current branch status and existing instructions. Start an isolated working branch that contains the H13G implementation; preserve unrelated local work.
2. Record actual starting SHA, branch ancestry, dependency versions, and whether the H13G commit has since been merged or superseded.
3. Locate the existing H13G raw pilot, compact diagnostic package, and hashes. Validate their actual config, producer, mode, and P1/P4/P5 scope.
4. If the raw pilot is unavailable, reproduce it under a pinned H13G worktree with unchanged settings. A fresh reproduction receives new provenance; do not describe it as the historical pilot.
5. Record protected config and H12 hub hashes.
6. Capture baseline per-probe metrics, bin status counts, cap flags, representative accounting, and raster failures.
7. Measure runtime and artifact size before scheduling the larger matrix.

**Existing full-mode baseline**

| Setting | Value | Caution |
|---|---:|---|
| Shared `continuation_steps` | 48 per ray | Also controls natural runs today. |
| Initial continuation step | 0.08 | Adaptive growth can reach the engine's 0.25 maximum. |
| `c`-spacing cell fraction | 0.75 | Angular spacing is in `theta=arccos(c)`. |
| Minimum source `c`-count | 17 | Resolution-aware construction may produce more slices. |
| Curve-segment cell fraction | 0.50 | Controls within-curve sampling. |
| Raster recursion depth | 8 | A work budget, not evidence of convergence. |
| Candidate budget per `c` | 1024 | Preserve until an actual cap failure warrants study. |
| Source traces per `c` | 16 | Preserve until unexplained representatives warrant study. |
| Trace-cover / dedup distance | 0.35 / 0.35 rad | Keep fixed during numerical-effort sweeps. |
| Endpoint state tolerance | 0.10 rad | Do not loosen to manufacture closure. |
| Endpoint tangent absolute dot | 0.85 | Preserve the current policy. |

The pilot JSON and actual effective runtime values are authoritative. [S3, S4]

**Exit gate:** baseline identity, invariant receipt, and either validated raw evidence or an explicitly identified reproduction exist. Missing historical detail remains marked unavailable.

Recorded receipt: [R3A_H13H_BASELINE_RECEIPT.md](R3A_H13H_BASELINE_RECEIPT.md).

### H13H-1 — Build a source-only diagnostic evaluator and replay records

**Why this is needed**

The current source record retains aggregate termination and rasterization data, but drops much of the in-memory `BranchTrace` evidence and the corrected raster configurations. Also, `MIXED_UNRESOLVED` can combine closed traces with projection or raster failures. Its count is not a count of missing mechanism components. [S4, S5]

**Implementation**

Create a narrow module, proposed as:

`src/grashof_workspace/spatial_experiments/l5_reconstruction/source_diagnostics.py`

It should provide three diagnostic operations: audit a source campaign, replay a selected failure, and compare two source reports.

The audit must:

- Require manifest, fixture, truth, and source-control artifacts with valid hashes, config identity, mode, and probe scope.
- Reuse existing same-grid and coarse/fine comparison helpers.
- Report direct-versus-oracle, source-versus-direct, source-versus-oracle, interval blockers, and reconstruction masks.
- Remain separate from `campaign.json`, `natural_family.json`, and full-campaign acceptance.
- Preserve current stage prerequisites; do not bypass them or invent empty natural results.
- Match the direct/source portions of a genuine all-column comparison in a parity regression.

**New diagnostic outputs**

| Proposed output | Contents |
|---|---|
| `source_failure_inventory.csv` | One row per relevant bin with separate continuation, projection, candidate-cap, trace-cap, representative, and raster flags. |
| `source_diagnostic_report.json` | Direct/source metrics and masks on both grids, declared scope, input hashes, and report schema. |
| `selected_trace_diagnostics.json` | Seeds, signed steps, per-ray evidence, and exact replay identities for selected cases. |
| `selected_raster_segments.json` | Corrected configurations and failed segment/refinement evidence. |
| `source_diagnostic_review.html` | Linked plots of a small, deterministic set of representative cases. |

Preserve full details only for selected cases; record aggregate counts for the full campaign. This keeps diagnostics bounded.

**Trace sidecar fields**

Record probe, exact `c`, seed identity and original projected state, fiber ID, source commit, config hash, diagnostic overrides, periodic-coordinate convention, and `BranchTrace` data:

- Signed arclength, predicted/corrected states, tangent and branch identity.
- Actual attempted and accepted step sizes.
- Constraint and gauge residuals, correction norm, Newton iterations.
- Rank/conditioning evidence and rejection history.
- Per-ray termination, endpoint, accepted steps, and accepted arclength.
- Return/endpoint-closure operands and the conditions that failed.

Do not infer the seed from the first serialized sample: the trace is sorted by signed arclength, so the first sample need not be the seed. Reproduce missing seed information through the deterministic construction with an observational callback.

**Raster sidecar fields**

Record original segment index, closing-segment flag, endpoints, midpoint guess/corrected state, recursion depth, correction outcome, position and `h` residuals, wrapped correction distance, local tangent information, and achieved angular gaps.

**Selection rule**

Choose a passing regular fiber, a budget-exhausted fiber, a mixed bin, and a raster-failing fiber when those categories exist. Include a singular/corrector failure only when actually present. Select deterministically, retain all underlying counts, and avoid choosing only visually favorable cases.

**Exit gate:** instrumentation reproduces the baseline numerical result, the metric parity regression passes, and each reported failure category points to inspectable data.

### H13H-2 — Diagnose continuation and repair demonstrated defects

**Use existing code first**

Start with `continue_implicit_branch`, `continue_source_fiber_h13g`, and `build_source_control_h13g(..., max_steps=...)`. The last function already supports a source-only step-budget override. [S4, S5]

**Classify each selected failure**

- Regular branch with insufficient traversal budget.
- Repeated corrector rejection or reduction to minimum step.
- Genuine critical/singular level set.
- Return detection sensitive to discrete sampling.
- Ray-local failure hidden by aggregate classification.
- Closed trace whose bin is blocked by another stage.

Keep possible causes distinct from demonstrated causes. For example, maximum adaptive step 0.25 versus seed-return state tolerance 0.08 makes missed-return sampling a reasonable experiment; it does not establish that this caused the pilot failures.

**Bounded replay matrix**

1. Reproduce the exact baseline.
2. For regular exhausted cases, compare 48 and 96 steps per ray.
3. Try 192 only if the 96-step evidence still requires it. Stop that escalation if no regular-progress explanation emerges.
4. If actual step history implicates return sampling, add an opt-in maximum-step parameter and compare genuinely bounded schedules at comparable allowed traversal effort.
5. Test unequal ray budgets only for endpoint-meeting sensitivity; a shorter unfinished ray may legitimately remain open.

Halving the initial step alone is not a valid step-resolution experiment, because the existing engine grows it after easy corrections.

**Repair rule**

Every production correction must have a reproducible counterexample and a regression. Potential remedies—only if the evidence supports them—include event localization near a missed return, a local corrector improvement, or more accurate cause propagation.

Do not translate budget exhaustion into closure. Do not classify a broad numerical exception as a proven singularity without retaining the cause and rank evidence. A complete seed return on one ray can be valid without a completed second ray; preserve the distinction between that route and plus/minus endpoint meeting.

**Policy integration**

Add an explicit source-only step-budget field for regular campaign execution, proposed as `source_control.continuation_max_steps_per_ray` with mode-specific values. Preserve the shared natural budget. Any bounded-step parameter must be opt-in, with existing defaults retained.

If behavior changes, register an explicit proposed `h13h_source_convergence_v1` policy. Add parser, dispatch, and serialization coverage together. Current dispatch recognizes only H13/H13G tokens and can fall back to the H12 path for an unknown token; reject unknown nonempty tokens instead of allowing a typo to select the wrong algorithm. Do not copy the entire H13G implementation into a new module merely to change its name.

**Exit gate:** each selected continuation failure is explained or remains explicitly unresolved; demonstrated repairs have meaningful regressions; source-only overrides are reproducible and do not alter natural configuration.

**Recorded result:** [R3A_H13H_CONTINUATION_DIAGNOSIS.md](R3A_H13H_CONTINUATION_DIAGNOSIS.md). The selected cases are classified. No continuation defect was demonstrated, so the solver, the shared step budget, and policy dispatch are unchanged. Raster diagnosis remains H13H-3.

### H13H-3 — Diagnose corrected rasterization and repair demonstrated defects

**Audit the actual contract**

Every inserted occupancy sample must have a source configuration whose FK satisfies the fixed position and scalar slice constraints. Serialized residual maxima must participate in completion checks. Inspect whether raw endpoints, inserted points, and the closing segment all meet the same declared obligations.

The current code checks short endpoint pointing distance before interior refinement, and midpoint correction solves the four level-set equations without a local branch section. These are algorithmic risks to test, not established explanations of the pilot failure. [S4, S5]

**Required investigations**

1. Reproduce one captured failing real-arm segment.
2. Determine whether failure is due to correction, recursion depth, periodic wrapping, local conditioning, or excessive movement away from the intended segment.
3. Measure interior pointing excursion; nearby endpoint directions alone do not certify the intervening curve.
4. Check the closing segment of returned fibers.
5. Verify that residual exceedance, nonlocal correction, failed correction, or required depth exhaustion cannot yield a successful raster record.
6. Verify that incomplete required rasterization blocks the corresponding interval even when aggregate occupancy metrics look favorable.

**Conditional repair direction**

If a branch jump or midpoint stagnation is demonstrated, anchor correction to the local traced segment using a suitable pseudo-arclength/section constraint and bounded local correction. Retain the original kinematic equations. If a hidden excursion is demonstrated, use actual interior samples and local trace-span/curvature evidence to decide further subdivision.

Neither midpoint residuals nor endpoint chords alone prove global branch identity. The outcome remains a numerical certificate at declared resolution.

**Exit gate:** the reproduced failure is corrected or localized; every accepted raster sample has verifiable kinematic provenance; missing information remains blocking.

**Recorded result:** [R3A_H13H_RASTER_DIAGNOSIS.md](R3A_H13H_RASTER_DIAGNOSIS.md). The selected open-ray closing chords are classified. A chord whose correction leaves the chord is rejected, and that gap stays unresolved. Continuation and the shared step budget are unchanged.

### H13H-4 — Run the P1/P4/P5 convergence study

Use P1 deep-complete, P4 outer-complete, and P5 outer-incomplete as the diagnostic set. Preserve P2/P3 from parameter selection.

Proceed through the experiment matrix in Section 5. Do not run a full Cartesian product of all budgets. Promote a setting to the next comparison only after the current failure is understood.

If two settings are both passing, apply the cross-run criteria in Section 3.3. If either is blocked, report the cause; similar occupancy does not override the blocker.

**Exit gate:** a single candidate source policy passes the three diagnostic probes, the single-axis stability checks, and a combined stronger-profile check.

**Recorded result:** [R3A_H13H_CONVERGENCE_STUDY.md](R3A_H13H_CONVERGENCE_STUDY.md). Baseline, 96-step, and 192-step source-only profiles were run on P1/P4/P5. No profile cleared required intervals. Section 3.3 comparisons were not formed. The shared natural budget and H13G pilot config are unchanged.

### H13H-5 — Validate the frozen policy on all five probes

Freeze candidate numerical settings before evaluating P2 inner-complete and P3 inner-incomplete.

Evaluate both additional probes and produce a combined five-probe source report in configured order. Confirm the same policy across all five, including the stronger-profile convergence evidence needed for validation. Reuse already-valid P1/P4/P5 runs only when their exact producer, config, and scientific inputs match the frozen candidate; otherwise rerun them.

If P2/P3 fail, reopen diagnosis. Do not create probe-specific winning settings. Once those probes inform tuning, record that they are no longer untouched validation cases; describe the final result as validation on five fixed probes, not fresh held-out generalization.

**Exit gate:** every probe satisfies the source gates and convergence requirements under one recorded policy, or the closeout retains the precise blocker.

**Recorded result:** [R3A_H13H_FIVE_PROBE_VALIDATION.md](R3A_H13H_FIVE_PROBE_VALIDATION.md). H13H-4 left `candidate_policy: null`, so no numerical policy was frozen and P2/P3 were not run. The closeout retains `REQUIRED_INTERVALS_UNRESOLVED` after `steps192`. Source policy validated: false. `accepted_reconstruction`: false.

### H13H-6 — Freeze the evidence and hand off to H13I

Create a versioned diagnostic config, proposed as:

`configs/l5_positive_control_h13h_source_frozen_v1.json`

This file remains diagnostic-only. Freeze its numerical policy only after H13H-5 passes. If the validated candidate used another filename, create a byte-for-byte copy so its config hash remains unchanged. Any content change, including a schema or policy token, requires appropriately rerun and revalidated evidence. Never relabel prior artifacts with a new config identity. Retain the actual producer SHA even when a later documentation commit records the closeout.

The evidence package must include:

- Exact producer SHA, config and artifact hashes, dependency versions, and probe order.
- Baseline receipt and protected H12 hashes.
- Failure inventory, selected replay records, and the repair/reproducer mapping.
- Per-run direct/source metrics, both grids' masks, and all required interval/cap/raster results.
- Cross-run comparison records, effective parameter values, and actual adaptive-step summaries.
- A single clearly scoped source-policy outcome.
- H13I prerequisites and remaining limitations.

A proposed standalone `source_policy_validated` Boolean may summarize this new diagnostic report. It must not overwrite existing campaign acceptance or blocker enums. The official H12 hub remains unchanged.

Update the live status ledger, roadmap, documentation index, and next available ADR with actual results. Do not reserve a future ADR number before checking the current repository.

## 5. Experiment matrix

All experimental names below are proposed. Save every profile before running it. Keep the direct-reference policy, masks, geometry, seed policy, thresholds, and natural settings fixed.

| Study | First comparison | Fixed inputs | Escalation / stop rule |
|---|---|---|---|
| Baseline reproduction | H13G evidence versus unchanged reproduction | Everything numerical | Explain mismatches before optimization. |
| Continuation effort | 48 → 96 source steps/ray | Same c samples, initial/adaptive-step policy, seed bank, raster settings | 192 only for a localized remaining traversal question; then stop and diagnose. |
| Actual step resolution | Recorded baseline versus a genuinely smaller maximum step | Same selected branch, closure tolerances, comparable traversal allowance | Run only if return/corrector evidence implicates step resolution; log actual steps. |
| Between-slice resolution | c fraction 0.75 → 0.50 | Validated tracing and within-curve policy | Try 0.25 only if a second profile is needed for convergence; do not retune unrelated knobs. |
| Within-curve resolution | curve fraction 0.50 → 0.25 | Frozen raw fibers for the isolating replay | Keep corrections kinematic; run full source policy afterward to confirm integration. |
| Raster depth | depth 8 versus one predeclared higher budget | Same failing segment and segment fraction | Only after depth exhaustion is identified; do not use depth to conceal nonlocal correction. |
| Discovery/trace budget | Current cap versus one declared increase | Other settings unchanged | Only where actual cap or unexplained-representative evidence remains. |
| Combined stronger profile | Candidate versus jointly strengthened numerical effort | Scientific inputs and tolerances unchanged | Must satisfy cross-run criteria; failure reopens diagnosis. |
| Additional probes | Frozen candidate on P2/P3 | One candidate policy | No per-probe setting selection. |

For within-curve replay, unchanged raw fibers isolate the rasterizer. The later end-to-end source run checks the integrated result. A replay override is recorded diagnostic evidence; it is not silently relabeled as a regular campaign.

### Configuration and provenance rule

Changing any experimental JSON changes its config hash. Existing stage guards correctly reject mixing old artifacts with a new config.

Default approach: rerun required upstream stages for each immutable config. If computation cost later justifies upstream caching, implement a separate tested compatibility/provenance mechanism; do not edit hashes or copy old artifacts into a new campaign directory.

Paired reports must establish identical **scientific reference contents** and grid identities. Whole JSON hashes can legitimately differ because producer/config provenance differs. Compare canonical reference data and retain both original artifact hashes.

## 6. Diagnostic visualization

Build a compact report for one ordinary returned fiber, one exhausted fiber, and one raster-failing fiber when present.

For each case show:

1. Joint coordinates versus signed arclength, separated by ray, with rejected steps and termination markers.
2. Constraint residuals, actual step size, and correction size along the trace.
3. The pointing sphere with raw FK samples and corrected raster samples; show the analytical small circle only as an explanatory overlay.
4. The selected segment's endpoints, corrected midpoints, recursion depth, and local failure.
5. The associated bin causes and source-versus-reference disagreement cells.

Include a simple source-arm pose/trace scrubber only if existing rendering can be reused cheaply. The required deliverable is the linked diagnostic evidence, not a new visualization framework.

The report should make it possible to distinguish “the curve was not fully traced” from “the traced curve was not represented adequately in occupancy.”

## 7. Verification plan

Run focused regressions as each defect is isolated. Run the repository integration gates once the candidate is ready. A long numerical campaign is not a replacement for a counterexample-based test.

| Test / fixture | Required result |
|---|---|
| Closed known curve with insufficient and sufficient traversal budgets | Insufficient budget stays unresolved; a valid return requires its actual geometric conditions. |
| Open curve with increased and asymmetric budgets | Exhaustion or endpoint coincidence cannot manufacture closure. |
| One ray singular or corrector-failed, other ray exhausted, nearby endpoints | Mixed ray-local failure cannot pass endpoint closure. |
| Periodic seam at ±pi | Wrapped states, midpoint construction, and distances remain consistent. |
| Return-event counterexample under bounded steps | Reproduces any demonstrated sampling defect before repair. |
| Closed trace plus raster/projection failure | Bin stays unresolved with the correct, separate cause. |
| Captured regular real-arm raster failure | Preserves p and h, stays local, and meets declared sampling/completion checks after repair. |
| Insufficient recursion depth or correction failure | Failure is explicit, linked to a segment, and blocks required coverage. |
| Nearby endpoint directions with large interior excursion | Endpoint separation cannot silently certify an under-resolved arc. |
| Nontrivial closing segment | Receives the same kinematic and refinement checks. |
| Residual exceedance | Cannot coexist with accepted raster completion. |
| Diagnostic replay/serialization | Seed, ray evidence, policy overrides, and provenance survive round trip. |
| Source-only evaluator parity | Matches direct/source columns of a genuine all-column comparison. |
| Cross-run masks with equal aggregate scores but moving holes | Occupancy-disagreement criterion detects the difference. |
| Wrong grid/reference, different producer code, or undeclared config differences | Cross-run comparison refuses incompatible evidence; declared numerical config differences and their different hashes are expected. |
| Unknown policy token | Fails explicitly; does not dispatch to historical H12. |
| Source-only budget | Changes source effort without changing natural configuration. |
| Protected evidence | H12 config/hub and historical evidence configs remain unchanged. |

Existing relevant tests include `test_spatial_v06h3_branch_continuation.py`, `test_l5_source_control_h13g.py`, and `test_l5_h13_locked_invariants.py`. Add targeted H13H tests rather than renaming historical tests or weakening their expectations.

### Integration commands

These repository commands already exist:

```bash
ruff check .
mypy src
python scripts/check_markdown_links.py

pytest tests/test_spatial_v06h3_branch_continuation.py \
       tests/test_l5_source_control_h13g.py \
       tests/test_l5_h13_locked_invariants.py

pytest
```

Add the actual new diagnostic/policy tests to the focused command once implemented. The default pytest suite excludes the repository's stress marker; broaden only if a concrete changed behavior requires it.

## 8. Implementation map

| Existing file | Planned responsibility |
|---|---|
| `branch_continuation.py` | Reuse trace evidence; add opt-in bounded-step/replay controls only if needed; preserve default behavior. |
| `parent_level_sets.py` | Inspect and, only with reproduced evidence, repair local midpoint correction. |
| `l5_reconstruction/source_control.py` | Explicit policy dispatch, compatible source records, unknown-token handling. |
| `l5_reconstruction/source_control_h13g.py` | Reuse trace-and-cover, ray diagnostics, corrected rasterization; factor shared logic only where required. |
| `l5_reconstruction/models.py` | Typed source policy and diagnostic schema support where appropriate. |
| `l5_reconstruction/comparison.py` | Reuse the established metric law; extract shared pure helpers if needed without numerical change. |
| `l5_reconstruction/artifacts.py` | Reuse artifact validation; retain the full-campaign prerequisite contract. |
| New `l5_reconstruction/source_diagnostics.py` | Source-only audit, bounded replay, paired-run comparison, and report generation. |
| New H13H JSON configs | Immutable profiles with source-only settings and diagnostic authority. |
| New focused H13H tests | Counterexamples, parity, convergence, policy, and provenance. |
| `docs/CURRENT_STATUS.md`, `docs/ROADMAP.md`, `docs/README.md`, `docs/reference/DECISIONS.md` | Actual result and dependency updates at closeout. |

Keep the number of new modules small. Do not introduce a generic experiment platform, broad atlas framework, or another copy of the full source solver.

### Suggested reviewable commits

1. **Baseline and diagnostic contract:** starting receipt, protected evidence, report schema, source-only metric parity.
2. **Replay and failure visibility:** bounded trace/raster sidecars and linked case review.
3. **Continuation corrections:** only reproduced defects and source-only policy controls.
4. **Raster corrections:** only reproduced defects and explicit completion obligations.
5. **Convergence evaluator and profiles:** fixed-grid paired-run checks, immutable study settings.
6. **Five-probe source evidence and handoff:** actual numerical result, hashes, compact readout, status/roadmap updates.

Keep observed numerical results out of documentation until the corresponding evidence exists.

## 9. Runbook

### 9.1 Existing CLI: produce source-only upstream artifacts

The following commands use existing stages and flags. They show how to reproduce the current H13G three-probe source baseline in a fresh output directory without running natural leaves.

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13g_source_pilot_v1.json \
  --outdir outputs/r3a_h13h/baseline_h13g \
  --stage manifest --mode full

python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13g_source_pilot_v1.json \
  --outdir outputs/r3a_h13h/baseline_h13g \
  --stage fixture --mode full \
  --probe P1_DEEP_COMPLETE --probe P4_OUTER_COMPLETE --probe P5_OUTER_INCOMPLETE

python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13g_source_pilot_v1.json \
  --outdir outputs/r3a_h13h/baseline_h13g \
  --stage truth --mode full \
  --probe P1_DEEP_COMPLETE --probe P4_OUTER_COMPLETE --probe P5_OUTER_INCOMPLETE

python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13g_source_pilot_v1.json \
  --outdir outputs/r3a_h13h/baseline_h13g \
  --stage source-control --mode full \
  --probe P1_DEEP_COMPLETE --probe P4_OUTER_COMPLETE --probe P5_OUTER_INCOMPLETE
```

Run the baseline under the pinned source version. The manifest may list all configured probes while subsequent stages record the selected scope, as supported by the current prerequisite contract.

For H13H profiles, use the new profile's path and a new output directory for every config. Run all five probes in configured order for final source validation.

### 9.2 Proposed diagnostic commands — implement before use

These are the intended interfaces for H13H-1, not commands available at the starting commit.

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics audit \
  --config configs/l5_positive_control_h13g_source_pilot_v1.json \
  --campaign-root outputs/r3a_h13h/baseline_h13g \
  --outdir outputs/r3a_h13h/reports/baseline_h13g

python -m grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics replay \
  --case outputs/r3a_h13h/reports/baseline_h13g/selected_case.json \
  --steps-per-ray 96 \
  --outdir outputs/r3a_h13h/replays/selected_case_steps96

python -m grashof_workspace.spatial_experiments.l5_reconstruction.source_diagnostics compare-runs \
  --left outputs/r3a_h13h/reports/candidate/source_diagnostic_report.json \
  --right outputs/r3a_h13h/reports/stronger/source_diagnostic_report.json \
  --outdir outputs/r3a_h13h/convergence/candidate_vs_stronger
```

The implementation may adjust names for repository conventions, but must preserve scope and provenance. The audit should export individual replay case files in addition to the aggregate selection record.

### 9.3 Packaging boundary

Do not feed a source-only report to the existing campaign packager, which expects a campaign. Do not fake missing stages.

H13H's report package is explicitly diagnostic. Keep raw traces under `outputs/`; retain a reproducible raw bundle and digest with a compact, reviewable source summary. Select any new committed summary destination without overwriting `results/l5_reconstruction/r3a/`.

For H13I, every eventual call to `scripts/package_r3a_campaign.py` must supply an explicit `--config`: its default is the old H12 config. The existing `l5_positive_control_h13_source_v1.json` belongs to the older H13A–F policy, so it is not an appropriate H13G/H13H final config. Create a new immutable all-column config only after the numerical policy is frozen. [S8]

H13H uses neither `--full-closeout` nor `--replace-committed`.

## 10. Review gates and stop conditions

### Gate A — Diagnosis is trustworthy

Proceed to repair only when:

- The baseline is reproducible or discrepancies are explained.
- Required-bin failures are decomposed into actual causes.
- Selected cases can be replayed with correct seeds and provenance.
- Source-only metric parity passes.
- Instrumentation has not altered the numerical baseline.

### Gate B — Repairs are justified

Proceed to the convergence study only when:

- Every code correction is linked to a counterexample.
- Kinematic constraints and trace/raster evidence remain inspectable.
- Closure is established by the declared geometric tests.
- Source-only settings do not silently change natural budgets.
- New policy dispatch cannot fall back to a different algorithm.
- Focused tests pass.

### Gate C — Source policy is validated

Freeze only when:

- All five probes pass both source reference columns.
- Direct validity remains established.
- Required intervals, caps, projected-representative accounting, and raster obligations pass.
- Each run passes the unchanged within-run refinement gate.
- The separate cross-run stability checks pass.
- The combined stronger-profile check passes.
- One immutable numerical policy is used across probes, with a clean recorded producer for the final validation.

### Stop and document the blocker if

- A required critical/singular interval cannot be resolved under the declared source construction.
- A trace still lacks an explanation after the bounded replay escalation.
- Closure depends on relaxed tolerances or unsupported component assumptions.
- Corrected samples leave the intended local branch or their provenance cannot be established.
- Occupancy changes materially under the strengthened settings.
- New parameter settings merely move missed regions.
- A comparison requires changed direct truth, discarded boundary evidence, or fabricated stage artifacts.
- The diagnosis requires a materially larger solver or topology project.

A stop produces a reproducer, a failure classification, the attempted settings, and a next-action recommendation. It does not authorize natural tuning or atlas expansion.

## 11. H13I handoff and subsequent roadmap

After H13H validates the source policy:

1. Create a new all-column config with the exact frozen source settings and unchanged natural settings.
2. Run the full five-probe pipeline from a clean producer commit.
3. Verify the direct and source columns again.
4. Evaluate the natural UURU family using the corrected shared engine.
5. Let the existing first-failing-column law determine the outcome.
6. Package the result through full semantic closeout validation; preserve H12 history.

Possible H13I outcomes include a newly isolated natural-decomposition blocker or an accepted controlled cover. Neither follows automatically from H13H.

After controlled reconstruction and transfer/falsification gates, resume the R3C sequence: UURU descriptors and support, exact behavior evaluator, directed atlas, held-out child checks, and held-out parent substitution. The aligned-terminal-roll 6R program remains downstream. [S10]

## 12. Cursor implementation handoff

```text
Implement the proposed R3A-H13H source-control diagnosis and convergence sprint.

Start from the verified H13G implementation at commit
81f1e2059040b74e503d166f4e6588922ddafb8c, reconciling any later repository
changes before editing. Preserve unrelated local work.

First implement H13H-0 and H13H-1: establish baseline provenance, add a
source-only diagnostic evaluator using the existing metrics, preserve
selected full trace/raster evidence, and reproduce representative
failures. Do not change solver behavior before obtaining those records.

Then localize continuation and rasterization failures. Change only
demonstrated defects, with a regression for each. Keep natural settings,
direct-reference definitions, scientific tolerances, historical configs,
and the H12 hub unchanged. Use explicit source-only controls for numerical
effort. A new policy token must be parsed and dispatched explicitly; an
unknown token must not silently select H12.

Keep existing coarse/fine refinement separate from the new same-grid
between-run convergence checks. Use P1/P4/P5 for diagnosis, freeze one
candidate policy, and then validate P2/P3 and the combined five-probe set.
A failed check reopens diagnosis; do not choose a separate winning policy
for each probe.

All H13H outputs remain diagnostic. Do not fabricate natural artifacts,
issue campaign acceptance, replace the H12 hub, start R3C-A3, or advance L6.
End with either validated five-probe source evidence or an explicit
reproducible blocker and the H13I handoff.
```

## 13. Source references

All code references below are pinned to the inspected H13G commit unless otherwise indicated. Proposed fields, files, commands, and additional convergence criteria in this plan are explicitly labeled as new work.

- **S1 — Latest H13G status:** [Current scientific status](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/docs/CURRENT_STATUS.md).
- **S2 — Reported pilot result:** [ADR-062](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/docs/reference/DECISIONS.md#adr-062--h13g-evidence-safe-corrections-are-diagnostic-only).
- **S3 — H13G contract and baseline:** [Corrective follow-up](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/docs/methods/R3A_H13G_NARROW_CORRECTIVE_FOLLOW_UP.md) and [pilot config](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/configs/l5_positive_control_h13g_source_pilot_v1.json).
- **S4 — Source tracing, aggregation, and rasterization:** [H13G source implementation](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/src/grashof_workspace/spatial_experiments/l5_reconstruction/source_control_h13g.py).
- **S5 — Continuation and constraints:** [Shared branch engine](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/src/grashof_workspace/spatial_experiments/branch_continuation.py) and [parent level sets](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/src/grashof_workspace/spatial_experiments/parent_level_sets.py).
- **S6 — Existing metrics and acceptance:** [Comparison implementation](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/src/grashof_workspace/spatial_experiments/l5_reconstruction/comparison.py).
- **S7 — Stage and provenance contracts:** [CLI](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/src/grashof_workspace/spatial_experiments/l5_reconstruction/cli.py) and [artifact prerequisites](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/src/grashof_workspace/spatial_experiments/l5_reconstruction/artifacts.py).
- **S8 — Packaging authority:** [Campaign packaging and semantic closeout](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/src/grashof_workspace/spatial_experiments/l5_reconstruction/campaign_package.py).
- **S9 — Original convergence/freeze contract:** [H13 source-control program](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/docs/methods/R3A_H13_SOURCE_CONTROL_COMPONENT_AND_COVERAGE_CLOSURE.md).
- **S10 — Downstream dependencies:** [Roadmap](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/docs/ROADMAP.md) and [L5 atlas round trip](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/blob/81f1e2059040b74e503d166f4e6588922ddafb8c/docs/methods/L5_BEHAVIOR_ATLAS_ROUND_TRIP.md).
- **S11 — Family census closeout:** [Merged PR #21](https://github.com/mfbailey91/Back-to-Grashof---Workspaces/pull/21).
