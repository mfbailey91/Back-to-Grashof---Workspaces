# R3C-A2 — 5R Parent Campaign and Family Census

**Status:** IMPLEMENTATION SPRINT
**Base:** `R3C_A1_manipulator_to_mechanism` at or after commit `17573b38`
**Scientific authority:** Architecture/family-support census only; no new workspace reconstruction claim
**Parent program:** `L5_BEHAVIOR_ATLAS_ROUND_TRIP.md`

---

## 1. Objective

Build the first controlled 5R **parent population** and answer:

> Which registered four-compound-joint parent patterns are actually produced by the current source architectures, and which one-DOF child families have actually been instantiated as reconstructible E0 mechanisms?

A2 separates three statements that must not be conflated:

\[
\boxed{
\text{exact physical parent pattern}
\neq
\text{source-derived child mechanism}
\neq
\text{workspace-valid child evidence}
}
\]

The campaign starts with:

```text
R3A SURU positive control
exact_two_u_5r
generic_5r
near_two_u_5r
near-SURU shoulder control
near-SURU wrist control
```

A2 does not add architectures merely to populate every family label.

---

## 2. Why this sprint is needed

The registered L5 corpus contains candidate mappings such as:

```text
SUUR -> UUUR
SURU -> UURU
SRUU -> URUU
```

and additional families containing `S_phys`.

Those labels are hypotheses / test-corpus identities, not evidence that a particular source manipulator actually produces the child.

The current code already supplies two independent evidence streams:

1. **Source physical geometry**
   - exact consecutive `RR -> U_phys` aggregation;
   - rejection of near-intersecting/non-exact pairs;
   - generic architectures with no designed exact pairs.

2. **A1 E0 mechanisms**
   - reconstructible UURU specimens exported from the frozen R3A positive control.

A2 joins those streams without upgrading either one.

---

## 3. Meaning of “arises”

A2 freezes a three-level vocabulary.

### Level F0 — `EXACT_CHILD_EXPORTED`

A child family has actually arisen when at least one source-derived mechanism exists as a reconstructible E0 record with:

```text
family identity
full frozen geometry
source provenance
successful A1 round trip
```

This is a **mechanism specimen** statement.

It is not automatically workspace evidence.

### Level F1 — `REGISTERED_PARENT_PATTERN_ONLY`

A source architecture admits an exact role-aware physical aggregation whose parent label maps to a registered candidate child family, but no reconstructible source-derived child of that family exists.

Example candidate outcome:

```text
exact_two_u_5r
    exact physical pattern: SUUR
    registry child hypothesis: UUUR
    actual E0 UUUR specimens: 0
```

This does **not** count as “UUUR arose.”

### Level F2 — `NO_REGISTERED_FOURBAR_PARENT_PATTERN`

The source does not contain two non-overlapping exact consecutive `RR -> U_phys` pairs that reduce the 5R+S_v closure to one of the U-based four-compound-joint parent patterns.

This is not proof that no useful decomposition exists. It only states that the current exact-U aggregation route did not produce one.

### Near controls — `NEAR_PATTERN_REJECTED`

A control lies close to a structured architecture but fails at least one exact aggregation condition.

Near controls prove that A2 is detecting exact source structure, not nearest-family similarity.

---

## 4. Detector scope

A2's first source-structure detector is deliberately narrow:

```text
exact consecutive RR -> U_phys
```

For five physical revolute joints, two non-overlapping exact pairs can produce:

```text
pair set (0,2) -> SUUR -> candidate UUUR
pair set (0,3) -> SURU -> candidate UURU
pair set (1,3) -> SRUU -> candidate URUU
```

The mapping itself is generated from `multi_u_kind_role_sequences(...)` and the registered `PARENT_CHILD_FAMILIES`; do not nearest-match letter strings.

The following registered child families are **out of A2 detector scope** because their parents require `S_phys` aggregation or other operations not implemented by the exact-U detector:

```text
USRR
URSR
URRS
```

A2 must report them as:

```text
OUT_OF_DETECTOR_SCOPE
```

not as “not observed.”

---

## 5. Required source bank

### 5.1 R3A positive control

Use the existing frozen positive-control geometry from:

```text
configs/l5_positive_control_v1.json
```

The physical architecture is expected to recover the exact parent pattern:

```text
SURU
```

The actual child census comes from A1, not from the parent label.

A2 consumes:

```text
e0_manifest.json
e0_roundtrip_audit.json
```

from a successful A1 export.

### 5.2 `exact_two_u_5r`

Use the existing V06 corpus builder.

The source has designed exact physical U pairs at:

```text
J1/J2
J3/J4
```

A2 discovers the resulting parent pattern from geometry.

If it is `SUUR`, the registered `UUUR` family remains `REGISTERED_PARENT_PATTERN_ONLY` unless an actual E0 UUUR child exists.

The previously rejected fixed-axis `UUUR`/`h=c` construction is not revived by this census.

### 5.3 `generic_5r`

Use the existing generic V06 source.

No four-bar parent pattern is forced.

If no exact pair combination is found, record that result.

### 5.4 `near_two_u_5r`

Use the existing near-miss V06 control.

Its perturbed physical pair must not be promoted through tolerance inflation.

### 5.5 Near-SURU shoulder control

Clone the positive-control source geometry and offset the second shoulder axis transversely by the frozen near-control distance.

This breaks:

```text
R1/R2 -> U_phys
```

while leaving the rest of the source architecture unchanged.

### 5.6 Near-SURU wrist control

Clone the positive-control source and offset the final wrist axis transversely.

This breaks:

```text
R4/R5 -> U_phys
```

The two near-SURU controls answer whether the SURU family disappears when either exact U requirement is removed.

---

## 6. Parent-point population

A2 is not a complete 2D parent continuation campaign.

It creates a deterministic set of **regular fixed-position seed problems** so later work can attach mechanism specimens to a reproducible parent population.

### Positive control

Use the five frozen R3A probes and their analytic fixture seeds.

### Other architectures

Use:

```text
regular_q
+
frozen q-offset bank
```

from `configs/l5_parent_campaign_v1.json`.

For each seed:

1. evaluate the source chain to obtain \(p^*\);
2. pose the fixed-position problem;
3. record rank \(J_p\);
4. record nullity;
5. record regularity;
6. reject no result silently.

Expected regular 5R seed:

\[
\operatorname{rank}J_p=3,\qquad
\operatorname{nullity}J_p=2.
\]

A nonregular seed remains in the campaign as a diagnostic record.

---

## 7. Parent-pattern discovery

For each source architecture:

1. run `detect_exact_u_pairs(model)` on the home source screws;
2. retain exact pair indices;
3. enumerate every size-two non-overlapping subset;
4. derive role-aware parent kinds/roles with `multi_u_kind_role_sequences`;
5. derive the parent label from those kinds;
6. look up the label in the registered parent/child corpus;
7. run `build_multi_u_aggregation(...)` to preserve exact aggregation diagnostics and FK identity residuals.

No registered match means the exact aggregate pattern is retained but is not assigned to a child atlas family.

No exact two-pair combination means no U-based four-bar parent pattern arose.

---

## 8. Near-pattern diagnostics

A non-exact consecutive pair may be marked `near_u_candidate` only for diagnostics when:

```text
distance_m <= configured near_pair_distance_max_m
orthogonality_abs_dot <= configured near_pair_orthogonality_abs_dot_max
```

`near_u_candidate` is never an exact U.

The campaign must preserve the raw values:

```text
distance_m
parallelism_residual
orthogonality_abs_dot
exact_intersecting
exact_orthogonal
exact_u_candidate
```

so tolerance sensitivity remains inspectable.

---

## 9. A1 authority gate

A2 requires the A1 outputs.

Validate:

```text
A1 program id
A1 source config hash == current frozen R3A config hash
roundtrip FAIL count == 0
roundtrip_failures empty when present
```

A1 `workspace_evidence_eligible_count` may remain zero.

That is not an A2 blocker.

A2 uses A1 only to answer:

> Which child families have actual reconstructible mechanism specimens?

It does not reinterpret the H12 natural column or source component scope.

---

## 10. Family census outputs

### 10.1 `parent_campaign.json`

Machine-readable complete campaign:

```text
config hash
A1 authority
architecture records
probe records
exact-U diagnostics
parent pattern observations
actual E0 family counts
registered candidate family counts
detector-scope statement
A3 queue
construction backlog
architecture-boundary cases
```

### 10.2 `parent_family_census.csv`

One row per architecture with:

```text
case id
control role
source geometry hash
regular probes / total probes
exact U pair indices
near pair indices
exact parent patterns
registered candidate child families
actual E0 child families
architecture disposition
```

### 10.3 `parent_probes.csv`

One row per frozen seed:

```text
case id
probe id
q seed
p_star
rank Jp
nullity Jp
regular
audit status
```

### 10.4 `a3_family_queue.json`

Contains **only actual E0 child families** with nonzero reconstructible specimen counts.

A candidate-only family does not enter A3 descriptor work.

### 10.5 `child_construction_backlog.json`

Exact registered parent patterns whose child family has zero actual E0 specimens.

This is where a likely `SUUR -> UUUR` result belongs.

---

## 11. Expected current-corpus interpretation

The sprint must not hard-code this as the answer, but current source definitions make the following a useful regression expectation:

```text
R3A positive control
  physical parent pattern: SURU
  actual E0 child family: UURU

exact_two_u_5r
  physical parent pattern: SUUR
  child family: UUUR candidate only unless separately constructed

generic_5r
  no exact-U four-bar parent pattern expected

near_two_u_5r
  exact two-U parent pattern rejected

near_suru_shoulder
  SURU broken by loss of proximal exact U

near_suru_wrist
  SURU broken by loss of distal exact U
```

If the code finds something else, preserve and investigate the result rather than forcing these labels.

---

## 12. What A2 does not do

Do not implement:

```text
UURU canonical descriptor vector
PCA / manifold learning
mechanism behavior labels
crank / rocker classification
exact child continuation for UUUR
exact child continuation for URUU
S_phys aggregation
atlas interpolation
atlas sampling
workspace reconstruction
L6 work
```

A2 decides **what mechanism-family population we currently have**, not how those mechanisms behave.

---

## 13. Files

### New

```text
configs/l5_parent_campaign_v1.json

docs/methods/R3C_A2_5R_PARENT_CAMPAIGN.md

src/grashof_workspace/spatial_experiments/l5_behavior_atlas/
  parent_campaign.py

tests/
  test_l5_behavior_atlas_parent_campaign.py
```

### Modified

```text
docs/methods/L5_BEHAVIOR_ATLAS_ROUND_TRIP.md
docs/ROADMAP.md
docs/README.md
docs/reference/DECISIONS.md
```

No changes are required to A1 E0 geometry schemas.

Do not modify:

```text
l5_reconstruction/*
v06_corpus.py
axis_aggregation.py
decomposition_ladder/registry.py
CURRENT_STATUS.md
committed R3A results
```

---

## 14. CLI

First produce / retain a successful A1 export.

Then:

```bash
PYTHONPATH=src python -m \
  grashof_workspace.spatial_experiments.l5_behavior_atlas.parent_campaign \
  --config configs/l5_parent_campaign_v1.json \
  --a1-manifest outputs/r3c_a1_h12/e0_manifest.json \
  --a1-audit outputs/r3c_a1_h12/e0_roundtrip_audit.json \
  --outdir outputs/r3c_a2_parent_campaign
```

---

## 15. Required tests

### A2-T1 — Positive control recovers SURU

Exact pair discovery yields the physical pair set corresponding to `SURU`.

### A2-T2 — `exact_two_u_5r` recovers SUUR

The existing designed two-U corpus produces an exact registered `SUUR` parent pattern.

The test checks parent structure, not UUUR child equivalence.

### A2-T3 — Generic source is not nearest-matched

`generic_5r` receives no registered U-based four-bar parent unless exact structure is actually detected.

### A2-T4 — Existing near-two-U control stays rejected

Its perturbed pair is not `exact_u_candidate`.

### A2-T5 — Near-SURU controls break SURU

Breaking either required physical U pair removes the exact SURU parent pattern.

### A2-T6 — A1 exact child census is distinct from parent patterns

A synthetic / fixture A1 manifest with UURU records produces:

```text
actual child UURU > 0
```

while an SUUR parent observation with no E0 UUUR records remains candidate-only.

### A2-T7 — A1 round-trip failures block A2

A2 refuses a source manifest whose A1 audit has any round-trip failure.

### A2-T8 — S-physical families are out of scope, not absent

`USRR`, `URSR`, `URRS` are reported separately as `OUT_OF_DETECTOR_SCOPE`.

### A2-T9 — Fixed-position seed bank is reproducible

Repeated campaign runs yield identical probe records and source-geometry hashes.

### A2-T10 — Deterministic artifacts

Repeated runs with identical A1 inputs produce byte-identical JSON/CSV outputs.

---

## 16. Acceptance gate

A2 passes when:

```text
all six required source/control cases are present
A1 authority passes
all parent structure records are deterministic
positive-control SURU consistency check passes
exact_two_u_5r exact aggregation is represented honestly
near controls are not promoted by similarity
actual-child and candidate-only counts are separated
detector out-of-scope families are explicit
A3 queue contains only actual E0 child families
no R3A numerical artifact changes
```

A2 does **not** require more than one actual child family.

A result such as:

```text
A3 queue = [UURU]
construction backlog = [UUUR]
```

is a valid and scientifically useful closeout.

---

## 17. A2 closeout decision table

### Outcome A — Multiple actual child families

Proceed to A3 family-by-family, starting with the best-supported family.

### Outcome B — UURU only

Proceed to UURU A3 canonicalization.

Keep UUUR/URUU candidate construction as a separate future decomposition task.

This is not evidence that UURU is universal.

### Outcome C — Positive-control UURU plus no transferable parent pattern

Record the architecture boundary before spending heavily on atlas scaling.

### Outcome D — A1 specimens do not align with source structural census

Stop.

That is a provenance / decomposition inconsistency and must be resolved before A3.

---

## 18. A3 handoff

A3 receives:

```text
a3_family_queue.json
A1 E0 manifest(s)
A2 source architecture census
A2 source geometry hashes
```

For each queued family, A3 asks:

> What role-preserving, symmetry-reduced coordinates parameterize the actual E0 geometry support?

A3 does not start from the full mathematical UURU parameter space.

It starts from the specimens the parent campaign actually produced.
