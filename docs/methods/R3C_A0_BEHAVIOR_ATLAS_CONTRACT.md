# R3C-A0 — L5 Behavior Atlas Provenance and Extraction Contract

**Status:** IMPLEMENTATION SPRINT
**Scientific authority:** Infrastructure only; no new L5 certificate or workspace claim
**Parent program:** `L5_BEHAVIOR_ATLAS_ROUND_TRIP.md`

---

## 1. Objective

Create the minimum durable infrastructure required for the L5 round-trip atlas program before parameterization begins.

A0 answers one question:

> Can every mechanism entering the future atlas be represented with exact family identity, source provenance, immutable frozen geometry, and explicit workspace eligibility?

A0 does **not** decide how UURU, URUU, or any other family should be parameterized.

---

## 2. Why this sprint comes first

The current R3A natural-leaf records already preserve:

```text
leaf id
probe id
construction kind
chart id
fixed lambda
task point
geometry hash
joint-kind sequence
joint-role sequence
certificate / acceptance state
```

The atlas program needs one additional durable object:

```text
full frozen mechanism geometry
```

A hash proves identity but cannot reconstruct or canonicalize a mechanism by itself.

Therefore the first atlas sprint freezes the extraction schema before A1 modifies the leaf exporter.

---

## 3. Deliverables

### Documentation

```text
docs/methods/L5_BEHAVIOR_ATLAS_ROUND_TRIP.md
docs/methods/R3C_A0_BEHAVIOR_ATLAS_CONTRACT.md
docs/ROADMAP.md
docs/reference/DECISIONS.md
docs/README.md
```

### Code

```text
src/grashof_workspace/spatial_experiments/l5_behavior_atlas/
  __init__.py
  models.py
```

### Tests

```text
tests/test_l5_behavior_atlas_contract.py
```

No CLI is added in A0. The first writer/exporter belongs to A1.

---

## 4. E0 extraction schema

### 4.1 Mechanism family identity

`MechanismFamilyIdentity` stores:

```text
family_id
parent_family_id
joint_kind_sequence
joint_role_sequence
```

The role sequence is part of identity.

No nearest-family matching is permitted.

### 4.2 Source provenance

`SourceProvenanceRecord` stores:

```text
source_chain_id
fixed_position_problem_id
source_component_id
probe_id
task_point
source_artifact
leaf_id
construction_kind
chart_id
family_parameters
child_certificate_status
accepted_for_reconstruction
provenance
```

Allowed provenance classes:

```text
source_derived_natural_leaf
source_derived_candidate
mechanism_explorer_only
```

`mechanism_explorer_only` may never set `accepted_for_reconstruction=true`.

### 4.3 Frozen geometry

`MechanismGeometryRecord` stores:

```text
geometry_schema_id
canonical JSON payload
SHA-256 of canonical payload
```

The payload is intentionally opaque to A0. Family-specific geometry schemas are added by A1/A3.

A0 requires:

1. finite JSON values;
2. deterministic key ordering;
3. reproducible geometry hash;
4. exact payload preservation.

### 4.4 Extracted record

`ExtractedMechanismRecord` combines:

```text
record_id
family
source provenance
frozen geometry
notes
```

Derived `workspace_evidence_eligible` is true only when:

```text
provenance == source_derived_natural_leaf
accepted_for_reconstruction == true
child_certificate_status in {EXACT_GLOBAL, EXACT_ON_COMPONENT}
```

The atlas may retain diagnostic records, but only eligible records may contribute to a workspace-supported source distribution.

### 4.5 Manifest

`ExtractionManifest` stores a frozen campaign collection and validates:

```text
schema version
unique record ids
source campaign id
source config hash
record geometry hashes
```

A0 does not deduplicate geometrically identical mechanisms across different source contexts. Those duplicates may be scientifically meaningful provenance.

---

## 5. Explicit non-goals

Do not implement any of the following in A0:

```text
UURU descriptor vector
URUU descriptor vector
normalization by scale
axis canonicalization
PCA / manifold learning
crank labels
winding labels
behavior continuation
atlas interpolation
nearest-neighbor classification
OOD thresholds
parent stitching substitution
large sampling campaigns
```

If any of these appear in the A0 patch, the sprint has expanded too far.

---

## 6. Required tests

### T1 — Canonical geometry hashing

Equivalent JSON mappings with different key insertion order produce the same canonical payload and SHA-256.

### T2 — Nonfinite geometry rejection

`NaN` and infinities are rejected before a geometry record is created.

### T3 — Role-aware family identity

Two records with the same letter kinds but different roles do not compare equal.

### T4 — Explorer provenance cannot become workspace evidence

Construction of an explorer-only record with `accepted_for_reconstruction=true` raises an error.

### T5 — Workspace eligibility is conjunctive

A source-derived natural leaf is eligible only with:

```text
accepted_for_reconstruction=true
AND
EXACT_GLOBAL or EXACT_ON_COMPONENT
```

### T6 — Manifest ids are unique

Duplicate `record_id` values fail manifest construction.

### T7 — Strict JSON output

Manifest serialization contains no NaN/Infinity and is deterministic.

---

## 7. Cursor implementation order

1. Add `l5_behavior_atlas/models.py`.
2. Implement canonical JSON normalization and hashing.
3. Add enums and frozen dataclasses.
4. Add validation in `__post_init__`.
5. Add `to_json_dict()` methods.
6. Add `ExtractionManifest.to_json_text()`.
7. Add focused contract tests.
8. Add package exports in `__init__.py`.
9. Update roadmap/docs/ADR.
10. Run existing non-stress tests plus the new contract file.

Do not touch R3A continuation, direct truth, leaf construction, or comparison code in A0.

---

## 8. Acceptance gate

A0 passes when:

```text
new contract tests pass
existing non-stress suite is unchanged
no R3A numerical output changes
no scientific status is promoted
no canonical descriptor is introduced
```

The patch should be reviewable as a data-authority change.

---

## 9. A1 handoff

A1 will connect the existing natural-leaf implementation to this schema.

Its first job is to define and serialize a reconstructible geometry payload for the current exact `UURU` natural leaf, then export one E0 record per leaf with provenance.

A1 must demonstrate:

\[
\text{serialized geometry}
\rightarrow
\text{reinstantiated child}
\]

with agreement to the original frozen child within declared numerical tolerance before any descriptor mining begins.
