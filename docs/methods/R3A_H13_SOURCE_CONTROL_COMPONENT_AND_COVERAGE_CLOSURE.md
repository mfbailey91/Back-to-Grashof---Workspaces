# R3A-H13 — Source-Control Component and Coverage Closure

**Status:** §1 and H13A–H13F implemented
**Project:** Back to Grashof — Mechanism-Based Workspace Characterization
**Rung:** L5 spatial 5R
**Starting point:** current `origin/main` after PR #21 (`3750a55`); not the stale handoff `17d87ad`
**Parent result:** frozen H12 five-probe closeout `STITCHING_CONTROL_BLOCKED`
**Primary goal:** Make the decomposition-free source `h=c` control domain-complete, component-aware, termination-honest, and resolution-stable before the natural UURU column is interpreted.
**Non-goal:** Do not tune natural leaves, begin R3B/L6, or activate the numerical virtual-crank atlas in H13.
**Implementation:** §1 locked invariants and H13A–H13F are implemented. Frozen H12 config and compact hub remain the recorded closeout. The H13F five-probe tree is diagnostic under `outputs/`. The freeze rule is not claimed. Do not apply `r3a_h13_source_control_component_and_coverage_closure.patch`.

---

## 0. Scientific starting point

H12 established the first trustworthy column boundary:

```text
DIRECT REFERENCE       PASS
SOURCE h=c STITCHING   BLOCKED
NATURAL UURU FAMILY    NOT INTERPRETED
```

The source column is blocked for two independent reasons:

```text
1. required c intervals contain unfinished, singular, or unresolved traces;
2. the stitched source pointing set is not stable from the coarse to the fine grid.
```

The current H12 implementation is appropriately conservative, but it cannot yet
localize the source failure cleanly because:

```text
A. the required c domain comes from discovery extrema, not the analytical oracle;
B. only the first three nearby source configurations are continued at each c;
C. one returned trace can mask other distinct open traces in the same c bin;
D. an unfinished two-ray trace is called open even when it is budget-exhausted or
   when its positive and negative endpoints jointly close a loop;
E. a continuous source curve is painted as a sparse point cloud;
F. fixed c count is not tied to the declared sphere resolution.
```

H13 repairs those authority boundaries before another full scientific closeout.

---

## 1. Locked invariants

H13 preserves all of the following:

- The H12 compact hub and raw-bundle digest remain the recorded result until a later strict full-closeout package replaces them.
- The frozen H12 config continues to use the historical H12 source path.
- H13 is opt-in through a new policy version and a separate pilot config.
- The H13 pilot config cannot issue a full-campaign scientific disposition.
- `accepted_reconstruction` remains false throughout H13 pilot work.
- L5 remains `parent_incomplete`.
- The direct column is not retuned.
- Source control is evaluated before natural UURU leaves.
- Natural-leaf parameters and acceptance tolerances are not tuned while source control is blocked.
- `RETURNED_SET_FOUND` is declared-budget evidence, not a component-completeness theorem.
- `COMPONENT_COMPLETE` remains reserved for an independent component certificate.
- A finite family of sampled `h=c` curves is not called a global foliation.
- R3B, L6, and the virtual-crank atlas remain held.

H13A implements the opt-in dispatch and analytical `c` domain. H13B replaces the silent first-three seed rule on that path with wrapped-Q clustering, explicit caps, seed-count vocabulary, and quality-ordered symmetric dedup. H13C classifies each continued trace as seed return, plus/minus endpoint meeting, budget exhaustion, singularity, corrector failure, or open-unclassified, and applies the mixed-trace interval law. H13D geodesically densifies each pointing polyline before painting so occupancy uses a resolution-aware curve, not a sparse sample cloud. H13E freezes that policy in `configs/l5_positive_control_h13_source_pilot_v1.json`; every mode including `full` has `allows_full_campaign_disposition=false`. Frozen H12 config still has no `policy_version` and still uses `seeds[:3]`. H13F adds `configs/l5_positive_control_h13_source_v1.json` as an immutable copy whose `full` mode may close; this sprint does not `--full-closeout` or replace the H12 hub. The freeze rule is not claimed.

---

# H13A — Opt-in source policy and analytical c domain

## 2. Preserve the H12 execution path

`source_control.py` remains the historical implementation for configs without:

```json
"policy_version": "h13_component_closure_v1"
```

When that exact policy is present, the stage delegates to:

```text
source_control_h13.py
```

This keeps the H12 configuration, package, and reproduction command semantically
stable while allowing H13 to carry a different evidence contract.

## 3. Exact feasible c interval

For

\[
h(d)=n^T d=c,
\qquad
n=\frac{p^*}{\rho},
\qquad
\rho=\|p^*\|,
\]

and tool offset `t`, the wrist-center distance is

\[
\|p^*-td\|^2=\rho^2+t^2-2\rho t c.
\]

The two-link regional arm requires

\[
r_{\min}\leq \|p^*-td\|\leq r_{\max}.
\]

Therefore:

\[
\boxed{
 c_{\min}=\max\!\left(-1,\frac{\rho^2+t^2-r_{\max}^2}{2\rho t}\right),
 \qquad
 c_{\max}=\min\!\left(1,\frac{\rho^2+t^2-r_{\min}^2}{2\rho t}\right)
}
\]

Production H13 uses the declared probe radius `rho_m`, not rounded Cartesian norm,
as the scalar authority.

## 4. Resolution-aware c samples

The H13 pilot preserves the configured minimum c count, but also requires a maximum
angular spacing in pointing space:

```text
theta = arccos(c)
max adjacent theta spacing
    <= c_slice_max_angular_spacing_cell_fraction * confirmation cell diameter
```

The effective c count is therefore:

```text
max(configured source_c_value_count, resolution-derived count)
```

Both analytical endpoints are included exactly.

Endpoints are recorded as `CRITICAL_OR_BOUNDARY` and are not required to return a
regular one-dimensional curve. They remain subject to the source-vs-direct set gate,
so missing strict endpoint directions are not ignored.

## 5. H13A acceptance

- P1/P2/P4 produce `[-1, 1]` within tolerance.
- P3 produces `[-1, 0.875]`.
- P5 produces approximately `[-0.7234848485, 1]`.
- first and last sampled c values equal the analytical endpoints;
- adjacent `arccos(c)` spacing obeys the declared sphere-relative limit;
- the output records requested and effective c counts;
- the required domain is no longer inferred from finite discovery extrema.

---

# H13B — Component-aware projected seed discovery

## 6. Remove the silent first-three rule

At each sampled c:

1. pre-cluster the full discovery bank in wrapped source Q;
2. prioritize candidates inside the declared `h` window, then sort by `|h(q)-c|`;
3. apply an explicit candidate projection cap;
4. independently project each selected representative onto `p(q)=p*`, `h(q)=c`;
5. cluster successful projections in wrapped Q;
6. apply an explicit projected-cluster cap;
7. continue one source trace per selected projected cluster.

Every cap is serialized. If either cap truncates the candidate set, the c record is
`BUDGET_EXHAUSTED` even when the traces that were attempted return.

## 7. Seed-count vocabulary

The historical `expected_seed_count` field remains for backward JSON compatibility.
H13 additionally records:

```text
candidate_seed_count
projection_attempt_count
projected_seed_count
projected_seed_cluster_count
attempted_seed_count
projection_failure_count
seed_budget_exhausted
seed_count_semantics = attempted_projected_seed_clusters_not_expected_components
```

No sampled seed count is presented as an analytical component count.

## 8. Deduplication authority

Deduplication remains symmetric in wrapped source Q. Duplicate representatives are
ordered by evidence quality:

```text
closed trace
then nonempty trace
then longer trace
then lower residual
```

A closed trace may replace a budget-exhausted duplicate. A distinct nonclosed trace
may not be hidden by one returned trace. H13B uses `fiber.returned` as the closed-quality
bit; H13C trace-termination vocabulary is not yet implemented.

## 9. H13B acceptance

- all truncations are explicit and blocking;
- wrapped-near configurations cluster across ±pi;
- closed duplicates are retained over budget-exhausted duplicates;
- asymmetric source-Q subsets remain distinct;
- mixed distinct traces remain visible in the per-c record;
- JSON never describes attempted seeds as expected components.

H13B is implemented on the H13 path: each selected projected cluster continues through
H13 `continue_source_fiber_h13`. H13C termination honesty is implemented. H13D
rasterizes pointing curves before painting; raw continuation samples remain on the
fibers.

---

# H13C — Honest trace termination and interval status

## 10. Trace termination vocabulary

Each H13 source trace receives one of:

```text
PROJECTION_FAILED
RETURNED_TO_SEED
PLUS_MINUS_ENDPOINTS_CLOSED
BUDGET_EXHAUSTED
SINGULAR_OR_CRITICAL_ENDPOINT
CORRECTOR_FAILURE
OPEN_UNCLASSIFIED
```

It also records:

```text
closed
positive_accepted_steps
negative_accepted_steps
accepted_arclength
endpoint_state_distance
endpoint_tangent_abs_dot
rejection_reason_counts
```

## 11. Plus/minus endpoint closure

The shared continuation engine launches positive and negative arclength rays. A
compact loop may be covered when those ray endpoints meet away from the original
seed.

H13 recognizes sampled closure only when:

```text
accepted arclength >= shared minimum return arclength
wrapped endpoint-state distance <= source endpoint tolerance
absolute endpoint-tangent dot >= source tangent tolerance
```

This is returned-set evidence at the declared continuation budget. It is not an
independent circuit or topological component identity.

## 12. Budget exhaustion

A trace that consumes the declared ray-step budget without seed return, endpoint
meeting, singular termination, or corrector failure is:

```text
BUDGET_EXHAUSTED
```

It is not interpreted as a genuinely noncompact branch.

## 13. Per-c interval law

The interval classifier operates on deduplicated traces:

```text
non-required analytical endpoint
    -> CRITICAL_OR_BOUNDARY

seed-candidate or projected-cluster cap exhausted
    -> BUDGET_EXHAUSTED

any deduplicated trace budget exhausted
    -> BUDGET_EXHAUSTED

all deduplicated traces closed, with no unresolved projection evidence
    -> RETURNED_SET_FOUND

closed plus any distinct nonclosed trace
    -> MIXED_UNRESOLVED

no closed trace + singular evidence only
    -> SINGULAR

no closed trace + open evidence only
    -> OPEN_ONLY

otherwise
    -> UNRESOLVED or MIXED_UNRESOLVED
```

Only these satisfy a required source interval:

```text
RETURNED_SET_FOUND
COMPONENT_COMPLETE  # reserved for a stronger future certificate
```

`RETURNED_COMPONENT_FOUND` remains readable in historical JSON but is not a covered
H13 status.

Adjacent unresolved c spans are merged before serialization.

## 14. H13C acceptance

- mixed `returned + open` evidence is `MIXED_UNRESOLVED`;
- seed and trace budget exhaustion remain blocking;
- plus/minus endpoint meeting is distinct from seed return;
- analytical endpoints are explicit non-required critical records;
- no raw seed attempt can hide a distinct unresolved deduplicated trace.

H13C is implemented on the H13 path. Continuation uses `continue_source_fiber_h13`
and records `SourceTraceTermination`. H13D rasterizes those traces before painting.

---

# H13D — Resolution-aware curve rasterization

## 15. Continuous curve representation

A continued source fiber is an ordered curve, not an unordered point cloud. Before
painting the sphere, H13 geodesically densifies each pointing polyline so that:

```text
maximum adjacent pointing-space segment
    <= curve_segment_fraction * confirmation cell diameter
```

The pilot baseline uses:

```text
curve_segment_fraction = 0.50
```

Closed traces include their closing arc. Nonclosed traces are not artificially
closed.

## 16. Separate within-curve and between-slice resolution

Curve rasterization repairs sampling along each curve. Resolution-aware c spacing
controls sampling between neighboring level sets. The source result records both
limits independently.

## 17. H13D acceptance

- densified adjacent directions obey the declared maximum segment;
- raw and rasterized pointing counts are separate;
- closed curves paint their final closing arc;
- source comparison uses the rasterized occupancy mask;
- raw continuation samples remain in the raw campaign tree.

H13D is implemented on the H13 path. Occupancy uses the rasterized pointing mask.
Raw continuation samples remain on each fiber.

---

# H13E — Pilot configuration and focused campaign

## 18. Pilot config

The named diagnostic config is:

```text
configs/l5_positive_control_h13_source_pilot_v1.json
```

It freezes the initial H13 diagnostic policy, including:

```text
analytical c-domain selection
sphere-relative c spacing
wrapped-Q clustering tolerances
candidate and projected-cluster caps
endpoint closure tolerances
deduplication tolerance
curve raster spacing
continuation step size
```

All modes, including `full`, set:

```text
allows_full_campaign_disposition = false
```

This makes accidental `--full-closeout` impossible during the pilot.

## 19. Entry gate

Before pilot compute:

```text
focused H13 tests green
full pytest green
ruff green
mypy green
markdown links green
H13 P1/P3 ci diagnostic package smoke green
```

## 20. Pilot probes

Start with:

```text
P1_DEEP_COMPLETE       complete-sphere baseline
P4_OUTER_COMPLETE      near-boundary complete stress case
P5_OUTER_INCOMPLETE    outer negative stress case
```

Add P3 after the first pilot for inner-boundary symmetry.

## 21. Pilot command

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13_source_pilot_v1.json \
  --outdir outputs/r3a_h13_source_pilot \
  --stage all \
  --mode full \
  --probe P1_DEEP_COMPLETE \
  --probe P4_OUTER_COMPLETE \
  --probe P5_OUTER_INCOMPLETE

python scripts/package_r3a_campaign.py \
  --raw-root outputs/r3a_h13_source_pilot \
  --results-root outputs/r3a_h13_source_pilot_compact \
  --bundle-dir outputs/r3a_campaign_bundles \
  --config configs/l5_positive_control_h13_source_pilot_v1.json
```

The package must remain `diagnostic`. Do not use `--full-closeout` and do not replace
the committed H12 hub.

## 22. Staged convergence study

Use copied pilot configs rather than runtime flags so every result has an immutable
config hash. Progress one axis at a time:

```text
Stage 1: baseline termination and seed-cap diagnosis
Stage 2: continuation steps 48 -> 96 only where BUDGET_EXHAUSTED remains
Stage 3: c angular-spacing fraction 1.00 -> 0.75 -> 0.50
Stage 4: curve segment fraction 0.50 -> 0.25
Stage 5: candidate/cluster caps only where seed_budget_exhausted remains
```

Record per probe:

```text
analytical c interval
requested/effective c counts
required c records by status
trace termination counts
candidate/projection/cluster counts
raw/rasterized pointing counts
source-vs-direct fine and coarse metrics
refinement delta
runtime and peak memory
```

## 23. Pilot freeze rule

Freeze an H13 source policy only when:

- no required bin is mixed, budget-exhausted, singular, or unresolved;
- increasing continuation steps does not materially change the stitched set;
- reducing c angular spacing changes required metrics by no more than the frozen refinement tolerance;
- halving the curve-segment fraction does not materially change occupancy;
- P1 and P4 pass the complete-source set gate;
- P5 recalls the feasible subset and excludes strict infeasible cells;
- no candidate or projected-cluster cap is exhausted.

A failed pilot remains `STITCHING_CONTROL_BLOCKED`; it does not authorize natural-leaf
tuning.

H13E is implemented as the named diagnostic pilot JSON. All modes including `full`
cannot issue a full-campaign disposition. A focused diagnostic campaign writes
gitignored `outputs/` and does not replace the H12 hub. The freeze rule is not
claimed.

---

# H13F — Frozen five-probe rerun

## 24. Final immutable config

After pilot freeze, create:

```text
configs/l5_positive_control_h13_source_v1.json
```

The final config may set `full.allows_full_campaign_disposition=true`. Do not rename
the pilot config or silently mutate a config already used for evidence.

## 25. Full run and package

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13_source_v1.json \
  --outdir outputs/r3a_full_raw_h13 \
  --stage all \
  --mode full

python scripts/package_r3a_campaign.py \
  --raw-root outputs/r3a_full_raw_h13 \
  --results-root results/l5_reconstruction/r3a \
  --bundle-dir outputs/r3a_campaign_bundles \
  --replace-committed \
  --full-closeout
```

Preserve the H12 raw bundle and digest as historical evidence.

## 26. Valid H13 closeouts

```text
DIRECT_REFERENCE_BLOCKED
STITCHING_CONTROL_BLOCKED
NATURAL_DECOMPOSITION_BLOCKED
CONTROLLED_COVER_ACCEPTED
```

Interpretation order remains:

```text
direct reference
source control
natural decomposition
```

H13 makes no prediction that the campaign advances beyond the source column.

H13F is implemented as the named immutable five-probe config. `full` may issue a
full-campaign disposition. This sprint's five-probe run writes gitignored `outputs/`
and packages as `diagnostic` without `--full-closeout` or `--replace-committed`. The
H12 hub remains the recorded closeout. The freeze rule is not claimed.

---

## 27. Patch file plan

### Production

```text
src/grashof_workspace/spatial_experiments/l5_reconstruction/models.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/source_control.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/source_control_h13.py
configs/l5_positive_control_h13_source_pilot_v1.json
```

The shared continuation engine is not rewritten. H13 termination interpretation is
kept local to source control.

### Tests

```text
tests/test_l5_source_control_h13.py
```

Existing H12 source-control tests remain unchanged and continue exercising the frozen
legacy path.

### Documentation

```text
docs/methods/R3A_H13_SOURCE_CONTROL_COMPONENT_AND_COVERAGE_CLOSURE.md
docs/CURRENT_STATUS.md
docs/ROADMAP.md
docs/README.md
docs/reference/PROJECT_REFERENCE_INDEX.md
docs/reference/DECISIONS.md
```

No result artifact is modified by the code patch.

---

## 28. Commit sequence

```text
feat: add opt-in H13 source-control policy and analytical c domain
feat: discover projected source-Q clusters with explicit caps
fix: separate source closure budget exhaustion and mixed intervals
feat: rasterize source curves at declared sphere resolution
test: cover H13 domain seed termination and raster authority
docs: add R3A H13 source-control closure program
```

Pilot evidence and a later full closeout are separate commits.

---

## 29. Verification commands

Focused tests:

```bash
pytest tests/test_l5_source_control_h13.py \
       tests/test_l5_source_control_fibers.py \
       tests/test_l5_source_control_dedup.py \
       tests/test_l5_source_control_reconstruction.py \
       tests/test_l5_three_way_metrics.py \
       tests/test_l5_artifact_authority.py
```

Full quality gate:

```bash
ruff check .
mypy src
python scripts/check_markdown_links.py
pytest
```

Reduced H13 diagnostic smoke:

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_h13_source_pilot_v1.json \
  --outdir outputs/r3a_h13_ci \
  --stage all \
  --mode ci \
  --probe P1_DEEP_COMPLETE \
  --probe P3_INNER_INCOMPLETE

python scripts/package_r3a_campaign.py \
  --raw-root outputs/r3a_h13_ci \
  --results-root outputs/r3a_h13_ci_compact \
  --bundle-dir outputs/r3a_campaign_bundles \
  --config configs/l5_positive_control_h13_source_pilot_v1.json
```

Required smoke assertions:

```text
package_kind = diagnostic
campaign_mode = ci
probe scope = P1/P3
full_closeout_eligible = false
committed results hub unchanged
```

---

## 30. Stop conditions

Stop and localize instead of increasing every budget when:

```text
analytical c interval disagrees with the positive-control oracle
candidate or projected-cluster counts fail to stabilize
plus/minus closure is tolerance-sensitive
singular endpoints appear in an interior required bin
curve rasterization still changes occupancy after the spacing limit is halved
source-vs-direct refinement remains above tolerance as c spacing shrinks
package authority refuses the diagnostic tree
```

Do not begin natural-family or virtual-crank work while one of these conditions is
active.

---

## 31. Exit statement

H13 is complete only when the project can make one of these statements:

```text
A. The source h=c control reconstructs the independent direct pointing set at the
   frozen declared resolution; the natural UURU column may now be interpreted.

B. The source h=c control still fails, and the failure is localized to analytical
   domain, seed/component discovery, continuation termination, c-slice density, or
   curve rasterization with explicit evidence.
```

Either outcome is useful. The unacceptable outcome is a source pass produced by a
discovery-derived domain, silent seed truncation, mixed returned/open bins, or sparse
point-cloud painting.
