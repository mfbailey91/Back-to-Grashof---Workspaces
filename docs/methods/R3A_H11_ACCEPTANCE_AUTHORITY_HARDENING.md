# R3A-H11 — Acceptance-Authority Hardening Before the Full-Mode Rerun

**Status:** ACTIVE hardening follow-up
**Project:** Back to Grashof — Mechanism-Based Workspace Characterization
**Rung:** L5 spatial 5R
**Starting branch:** `R3A_Stiching_Stitch_Tests`
**Reviewed head:** `25cbf80f6b786cdd0ed695aa37029ef8c40c984f`
**Parent program:** R3A-H7–H10
**Primary goal:** Make the H7–H10 evidence law, chart-atlas responsibility, and artifact package authority strong enough that one frozen-config full run can issue an honest first-failing-column closeout.
**Non-goal:** Do not tune continuation budgets, change the positive-control geometry, or claim a natural-leaf reconstruction in this sprint.

---

## 0. Applying the companion patch

The companion unified diff is generated against reviewed head
`25cbf80f6b786cdd0ed695aa37029ef8c40c984f`.

```bash
git switch R3A_Stiching_Stitch_Tests
git status --short

git apply --check --unidiff-zero r3a_h11_acceptance_authority_hardening.patch
git apply --unidiff-zero r3a_h11_acceptance_authority_hardening.patch
```

Use a clean working tree. The `--unidiff-zero` option is required because the patch
is assembled from exact reviewed file regions rather than a local repository checkout.

## 1. Why H11 exists

H7–H10 landed the correct overall architecture:

```text
explicit metric applicability
two-resolution refinement
local versus component reseed scope
leaf-scoped family admission
canonical chart assignment
finite chart-by-lambda ledger
content-addressed stage artifacts
first-failing-column campaign localization
```

The implementation review found four bounded authority defects:

```text
1. a diagnostic ci package can be named and described as a full package;
2. chart-overlap audits do not yet follow the declared overlap-band responsibility transitions;
3. sampled returned-set agreement is named more strongly than its evidence supports;
4. budget truncation, unevaluated topology events, and test-module coupling remain ambiguous.
```

These are hardening defects, not a reason to redesign the R3A experiment.

---

## 2. Program invariants

H11 must preserve all of the following:

- `accepted_reconstruction` remains false unless all five full-mode probes pass every mandatory gate;
- `ci` and `smoke` remain diagnostic-only;
- direct truth is evaluated before source stitching;
- source stitching is evaluated before natural decomposition;
- no tuning of natural leaves occurs while direct or source-control evidence is blocked;
- `SAMPLED_ADMISSIBLE` remains a declared-resolution sample status, not a foliation theorem;
- L5 remains `parent_incomplete`;
- R3B and L6 remain held until the R3A controlled operation is stable;
- the virtual-crank atlas remains downstream of validated reconstruction provenance.

---

# H11A — Package scope and producer provenance

## 3. Goal

A package must describe the campaign that actually produced it.

## 4. Required package kinds

Add two explicit package paths:

```text
diagnostic
full_closeout
```

### Diagnostic package

May contain:

```text
mode = ci or smoke or full
one or more declared probes
an incomplete stage tree
campaign_blocker = null
```

It must record its actual mode and probe subset and must not look like a full closeout.

### Full-closeout package

Requires:

```text
mode == full
probe_ids == all five configured probes in configured order
all seven stage summaries present
all per-probe stage artifacts present
campaign config hash == loaded config hash
all stage modes and probe scopes consistent
producer git commit present
producer tree clean
one explicit CampaignBlocker outcome
```

## 5. Manifest contract

`compact_manifest.json` must include:

```text
package_kind
campaign_mode
probe_ids
all_configured_probes_present
allows_full_campaign_disposition
full_closeout_eligible
producer_config_hash
packager_config_hash
producer_git
packager_git
raw_bundle
raw_bundle_sha256
raw_bundle_codec
raw_bundle_archive_root
reproduction
```

The legacy `git` field may remain as an alias of `producer_git`.

## 6. Naming and reproduction

Do not unconditionally use `r3a_full_*`.

Examples:

```text
r3a_ci_2probes_<config>_<producer>.tar.zst
r3a_full_all5_<config>_<producer>.tar.zst
```

The reproduction command must preserve:

```text
actual config path
actual raw root
actual mode
actual probe flags when the run is a subset
```

## 7. H11A acceptance

- a P1/P3 `ci` package is labeled `diagnostic`, `campaign_mode=ci`, and lists P1/P3;
- `--full-closeout` rejects `ci`, `smoke`, or incomplete probe sets;
- config-hash mismatch is refused before packaging;
- full closeout refuses a missing stage or missing per-probe artifact;
- producer and packager provenance are stored separately;
- the raw bundle digest matches the manifest.

---

# H11B — Responsibility-transition chart audits

## 8. Goal

Required chart audits must correspond to actual canonical-chart handoffs in the configured overlap band, not every populated chart pair.

## 9. Responsibility transition construction

For every source configuration used by discovery:

```text
R(q)
  -> canonical_chart(R)
  -> charts_in_overlap_band(R)
  -> required canonical/alternate chart pair
```

Record:

```text
responsibility_transition_id
chart_id_a
chart_id_b
transition_sample_count
claim_scope
required
```

A chart pair outside the overlap band is:

```text
status = NOT_APPLICABLE
required = false
```

## 10. Leaf/component matching

For each required chart pair:

1. locate the nearest discovered leaf in each chart to each transition source configuration;
2. deduplicate repeated leaf-pair matches;
3. audit each matched leaf pair separately;
4. store `leaf_id_a` and `leaf_id_b`;
5. emit a required `UNRESOLVED` chart-level audit when no matched pair exists.

Do not concatenate every leaf in chart A and chart B into one aggregate comparison.

## 11. Chart compatibility evidence

A compatible transition requires:

```text
symmetric source-Q correspondence
round-trip source rotation agreement in both charts
chart-coordinate transform agreement
each leaf's own frozen-lambda agreement
pointing-set agreement
```

The audit does **not** claim an independent circuit or component signature. Keep that field null unless such a signature is implemented later.

## 12. Leaf-scoped inheritance

When `leaf_id_a` / `leaf_id_b` are present, only those leaves inherit the audit. A chart-level unresolved transition may still attach to every leaf in the affected charts.

## 13. H11B acceptance

- a wide overlap band produces required transition pairs;
- a unique canonical chart with zero overlap margin produces no required transition pair;
- an out-of-band chart pair is `NOT_APPLICABLE`;
- a required transition without matched leaves is `UNRESOLVED`;
- multiple frozen-lambda leaves are audited as separate pairs;
- an unresolved pair blocks only incident leaves when leaf IDs are available.

---

# H11C — Claim vocabulary and interval honesty

## 14. Goal

Keep strong evidence, narrow the names.

## 15. Reseed wording

The current re-seed law supports:

```text
returned symmetric branch-set match at the declared continuation budget
```

It does not independently establish:

```text
circuit identity
assembly-mode identity
topological component identity
```

Preserve backward-compatible fields where needed, but serialize:

```text
returned_symmetric_set_match
component_identity = null
circuit_or_component_match = null
```

A future circuit signature may use winding, assembly-mode, or another independently computed invariant.

## 16. Budget exhaustion

For a required chart-by-lambda interval:

```text
budget_exhausted == true
  -> interval_status = UNRESOLVED
```

This takes precedence over one sampled admissible member.

## 17. Topology-event scope

An empty `birth_death_merge_events` list must not imply that topology events were checked and absent.

Record:

```text
topology_event_status =
  NOT_EVALUATED_EXCLUDED_FROM_DECLARED_RESOLUTION_SET_COVER
```

This keeps the finite set-cover claim separate from a global foliation claim.

## 18. H11C acceptance

- no user-facing record calls sampled returned-set agreement “circuit identity”;
- required truncated bins are unresolved;
- interval JSON explicitly states the topology-event scope;
- no status uses `COMPLETE` for one sampled bin.

---

# H11D — CI isolation and regression coverage

## 19. Goal

Restore a fully green workflow and prevent test-collection coupling.

## 20. Shared test support

Move `_two_neighbor_works` and its construction helpers into:

```text
tests/l5_test_support.py
```

The support file must not begin with `test_`.

Update tests to import the support helper directly rather than importing one test module from another.

## 21. Required tests

```text
test_diagnostic_package_preserves_mode_and_probe_scope
test_full_closeout_refuses_ci_subset
test_campaign_config_hash_mismatch_is_refused_before_packaging
test_strict_campaign_tree_requires_every_stage
test_overlap_band_drives_required_transition_pairs
test_leaf_only_inherits_incident_chart_audits
test_required_budget_exhaustion_overrides_sampled_member
test_returned_set_match_does_not_claim_circuit_identity
```

## 22. H11D acceptance commands

```bash
pytest tests/test_l5_artifact_authority.py \
       tests/test_l5_chart_responsibility.py \
       tests/test_l5_chart_overlap.py \
       tests/test_l5_leaf_admissibility.py \
       tests/test_l5_leaf_transversality.py \
       tests/test_l5_family_intervals.py

ruff check .
mypy src
python scripts/check_markdown_links.py
```

Then run the complete workflow:

```bash
pytest
```

The reduced P1/P3 `ci` smoke must complete after Ruff and mypy rather than being skipped.

---

# H11E — Frozen full-mode acceptance closeout

## 23. Entry gate

Do not start the full run until:

```text
targeted tests green
full pytest green
ruff green
mypy green
markdown links green
P1/P3 ci package smoke green
```

## 24. Full run

```bash
python -m grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_v1.json \
  --outdir outputs/r3a_full_raw \
  --stage all \
  --mode full
```

Do not pass probe filters.

## 25. Strict package

```bash
python scripts/package_r3a_campaign.py \
  --raw-root outputs/r3a_full_raw \
  --results-root results/l5_reconstruction/r3a \
  --bundle-dir outputs/r3a_campaign_bundles \
  --replace-committed \
  --full-closeout
```

Regenerate the project dashboard only after the strict package validates.

## 26. Valid closeout outcomes

```text
DIRECT_REFERENCE_BLOCKED
STITCHING_CONTROL_BLOCKED
NATURAL_DECOMPOSITION_BLOCKED
CONTROLLED_COVER_ACCEPTED
```

Interpretation order:

```text
direct first
source stitching second
natural decomposition third
```

No generic `PARTIAL` is sufficient as the final scientific statement.

---

## 27. File plan

### Production

```text
src/grashof_workspace/spatial_experiments/l5_reconstruction/artifacts.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/campaign_package.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/models.py
src/grashof_workspace/spatial_experiments/l5_reconstruction/leaf_family.py
```

### Tests

```text
tests/l5_test_support.py
tests/test_l5_artifact_authority.py
tests/test_l5_chart_responsibility.py
tests/test_l5_chart_overlap.py
tests/test_l5_leaf_admissibility.py
tests/test_l5_leaf_transversality.py
tests/test_l5_leaf_reseed.py
tests/test_l5_family_intervals.py
tests/test_l5_leaf_family_p1.py
```

### Documentation

```text
docs/methods/R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md
docs/methods/R3A_H7_H10_FOLLOWUP_EXECUTION.md
docs/methods/CURSOR_GUIDE_R3A_H7_H10_FOLLOWUP.md
docs/README.md
docs/ROADMAP.md
```

---

## 28. Commit sequence

```text
fix: preserve R3A package mode probe scope and producer provenance
fix: audit only declared chart responsibility transitions
fix: narrow reseed and interval evidence claims
test: isolate R3A fixtures and close H11 regression gaps
docs: add R3A H11 acceptance-authority hardening gate
```

Do not commit compact full results with the code commits.

After the frozen run:

```text
results: close R3A at the first failing scientific column
```

---

## 29. Stop conditions

Stop and localize rather than tune when:

```text
direct reference does not pass
source h=c control does not pass
a required chart transition is unresolved
a required interval is budget exhausted
the strict package refuses scope or provenance
```

Do not begin the virtual-crank atlas evaluator until the full campaign has an honest closeout and the accepted/rejected reconstruction provenance is stable.
