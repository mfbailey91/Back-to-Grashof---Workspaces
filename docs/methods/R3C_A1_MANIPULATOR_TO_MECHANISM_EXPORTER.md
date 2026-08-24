# R3C-A1 — Manipulator → Mechanism Exporter

**Status:** IMPLEMENTATION SPRINT
**Base:** `R3C_A0_behavior_atlas` or the commit that merges A0
**Scientific authority:** Downstream extraction only; no R3A numerical changes, no new L5 reconstruction claim
**Parent program:** `L5_BEHAVIOR_ATLAS_ROUND_TRIP.md`

---

## 1. Objective

Turn the existing R3A natural-leaf artifacts into reconstructible E0 child-mechanism records.

A1 must establish the round trip

\[
\boxed{
\text{natural leaf artifact}
+
\text{frozen source config}
\rightarrow
\text{full UURU geometry payload}
\rightarrow
\text{standalone reconstructed child}
}
\]

and prove that the reconstructed child has the same defining equations as the original frozen child.

A1 does **not** classify mechanism behavior.

---

## 2. Why A1 can remain downstream of R3A

The current R3A `ClosedUURULeafProblem` is defined by:

```text
source serial-chain geometry
independent copied serial chain
spherical chart
fixed lambda
fixed Cartesian point p*
child joint kind / role contract
```

The source seed chooses an initial point on the mechanism but does not change the frozen child geometry.

Therefore A1 does not need to rerun discovery or modify `leaf_family.py`.

It may reconstruct a leaf definition from:

```text
configs/l5_positive_control_v1.json
results/l5_reconstruction/r3a/<probe>/natural_family.json
```

then serialize the complete mechanism definition.

This keeps the H12 R3A numerical package immutable.

---

## 3. Current scientific boundary

The frozen H12 closeout is:

```text
campaign_blocker = STITCHING_CONTROL_BLOCKED
accepted_reconstruction = false
natural column = not interpreted
L5 = parent_incomplete
```

A1 must not reinterpret that result.

In particular, R3A natural-leaf artifacts record a component **scope** such as a
returned/local branch, but do not provide an independently established source-parent
component identifier.

A1 therefore uses:

```text
source_component_id = UNRESOLVED_SOURCE_COMPONENT
```

for the current R3A export.

The leaf's own `accepted_for_reconstruction` and component-status fields are preserved
as source metadata, but `workspace_evidence_eligible` remains false while the source
component identity is unresolved.

This is an expected A1 result, not an A1 failure.

---

## 4. Frozen UURU geometry schema

Add:

```text
uuru_frozen_geometry_v1
```

The payload contains no leaf ID, probe ID, campaign name, or source artifact path.
Those are provenance, not geometry.

### 4.1 Source chain

```text
home revolute axes:
  r_i [m]
  w_i [unit direction]
home task point p0 [m]
home pointing d0
home orientation R0
source joint-kind sequence
source joint-role sequence
```

### 4.2 Independent child chain

Store a second complete serial-chain payload even though the current R3A child uses
an exact copy of the source chain.

Do **not** replace it by `"same_as_source": true`.

The current `ClosedUURULeafProblem` requires the independent chain to be a distinct
object. Storing it separately also keeps the schema usable when later exact children
do not reuse identical serial-chain geometry.

### 4.3 Virtual spherical closure

```text
chart_id
Euler sequence
basis C
reference R_ref
chart singularity tolerance
lambda_fixed
```

### 4.4 Fixed-position closure

```text
p_star [m]
```

### 4.5 Child contract

```text
joint_kind_sequence = UURU
joint_role_sequence = U_v, U_phys, R_phys, U_phys
ambient_dimension = 7
constraint_dimension = 6
periodic_coordinates
```

### 4.6 Explicit conventions

```text
length_unit = m
angle_unit = rad
frame = W
```

---

## 5. Geometry hash authority

The existing R3A `NaturalLeafSpec.geometry_hash` is a legacy leaf-construction hash
based on chart data and fixed `lambda`.

Do not rewrite it in A1 because that would mutate the R3A artifact contract.

E0 introduces the stronger authority:

```text
MechanismGeometryRecord.geometry_sha256
```

computed from the full canonical `uuru_frozen_geometry_v1` payload.

A1 verifies that the legacy hash still agrees with the chart / lambda recorded by the
source artifact, then stores the legacy hash only as provenance metadata.

---

## 6. Standalone reconstruction

Implement:

```python
reconstruct_uuru_problem(geometry_record, ...)
```

The function may use only the E0 geometry payload plus non-geometric identifiers used
for runtime labels.

It must **not** require:

```text
CampaignConfig
natural_family.json
original source seed
PositiveControlArm
R3A result directory
```

The reconstructed `ClosedUURULeafProblem` must contain newly allocated source and
independent chains.

---

## 7. Round-trip proof

For every exported leaf, A1 performs two levels of proof.

### Gate G1 — Canonical geometry identity

Serialize:

\[
C \rightarrow J(C)
\]

reconstruct from `J(C)`, then serialize again:

\[
J(C)\rightarrow C'\rightarrow J(C').
\]

Require:

```text
geometry_sha256(C) == geometry_sha256(C')
```

This proves that the serialized payload is sufficient to recreate its own frozen
geometry exactly under the schema.

### Gate G2 — Defining-equation numerical identity

At every stored natural-leaf sample \(x_i\), compare the source/config reconstructed
problem \(C\) against the payload-only problem \(C'\).

Record:

```text
max residual-vector delta
max Jacobian-entry delta
max source-chain FK position delta
max source-chain FK orientation delta
max independent-chain FK position delta
max independent-chain FK orientation delta
```

Initial implementation tolerances:

```text
residual delta        <= 1e-12
Jacobian max abs      <= 1e-10
FK position delta     <= 1e-12 m
FK orientation delta  <= 1e-12 rad
```

These are serializer/reconstructor tolerances, not scientific mechanism-closure
tolerances.

If a diagnostic leaf contains no samples, G1 may issue:

```text
GEOMETRY_ONLY_PASS
```

but never fabricate G2 evidence.

A failed round trip blocks export.

---

## 8. Source-package authority

A1 exports from the frozen R3A package, not from an arbitrary folder of JSON files.

Require:

```text
compact_manifest.json exists
program_id matches config
producer_config_hash matches CampaignConfig.config_hash
semantic_revalidation == true
package_kind == full_closeout
all_configured_probes_present == true
```

Record source package metadata in the A1 audit:

```text
campaign mode
package kind
producer git commit
campaign blocker
raw bundle SHA-256
```

A1 does not require `accepted_reconstruction=true`; the current H12 package is
intentionally unaccepted.

---

## 9. E0 record mapping

For each natural leaf:

```text
family_id                <- child_family
parent_family_id         <- source config parent_family
joint kinds / roles      <- natural leaf artifact
source_chain_id          <- source architecture id
fixed_position_problem   <- probe id
probe_id                 <- probe id
task_point               <- p_star
source_artifact          <- <probe>/natural_family.json
leaf_id                  <- source leaf id
construction_kind        <- virtual_orientation_coordinate
chart_id                 <- source chart id
family parameter         <- lambda
child certificate status <- leaf_component_status
accepted flag            <- source leaf flag
provenance               <- source_derived_natural_leaf
source_component_id      <- UNRESOLVED_SOURCE_COMPONENT (A1/R3A)
geometry                 <- full uuru_frozen_geometry_v1
```

The E0 geometry hash is independent of record ID and source artifact path.

---

## 10. Files

### New

```text
docs/methods/R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER.md

src/grashof_workspace/spatial_experiments/l5_behavior_atlas/
  uuru_geometry.py
  exporter.py

tests/
  test_l5_behavior_atlas_uuru_roundtrip.py
```

### Modified

```text
src/.../l5_behavior_atlas/models.py
src/.../l5_behavior_atlas/__init__.py
tests/test_l5_behavior_atlas_contract.py

docs/methods/L5_BEHAVIOR_ATLAS_ROUND_TRIP.md
docs/ROADMAP.md
docs/README.md
docs/reference/DECISIONS.md
```

Do not modify:

```text
l5_reconstruction/leaf_family.py
l5_reconstruction/uuru_leaf.py
l5_reconstruction/continuation
R3A committed numerical results
CURRENT_STATUS.md
```

---

## 11. CLI

Run:

```bash
PYTHONPATH=src python -m \
  grashof_workspace.spatial_experiments.l5_behavior_atlas.exporter \
  --config configs/l5_positive_control_v1.json \
  --campaign-dir results/l5_reconstruction/r3a \
  --outdir outputs/r3c_a1_h12
```

Outputs:

```text
outputs/r3c_a1_h12/e0_manifest.json
outputs/r3c_a1_h12/e0_roundtrip_audit.json
```

The first file is the A0 E0 extraction manifest.

The second is serializer/reconstruction evidence and source-package authority metadata.

Do not commit a large generated E0 corpus in A1 unless its size and repository policy
are reviewed. A2 owns corpus packaging.

---

## 12. Required tests

### A1-T1 — Payload-only UURU reconstruction

Build a real positive-control UURU leaf problem, serialize it, reconstruct it without
the config, and require stable full-geometry SHA-256.

### A1-T2 — Residual identity

At the real leaf seed:

```text
||F_original(x) - F_rebuilt(x)|| <= 1e-12
```

### A1-T3 — Jacobian identity

At the same seed:

```text
max_abs(J_original - J_rebuilt) <= 1e-10
```

### A1-T4 — FK identity

Source and independent chains agree numerically between original and reconstructed
problems.

### A1-T5 — Source config mismatch refuses export

A `compact_manifest.json` whose producer config hash differs from the requested config
is a hard failure.

### A1-T6 — Legacy leaf hash mismatch refuses export

Do not export a leaf whose legacy chart/lambda hash does not match its source artifact.

### A1-T7 — Structural family mismatch refuses export

A1 understands the current exact R3A `SURU -> UURU` child only. A leaf relabeled
`URUU`, or with the wrong role sequence, is not nearest-matched or coerced.

### A1-T8 — Unresolved source component cannot become workspace evidence

Even if a source leaf carries:

```text
accepted_for_reconstruction = true
leaf_component_status = EXACT_ON_COMPONENT
```

an A1 R3A record with `UNRESOLVED_SOURCE_COMPONENT` remains
`workspace_evidence_eligible=false`.

### A1-T9 — Deterministic export

Repeated extraction of the same frozen package yields byte-identical
`e0_manifest.json` and round-trip audit files.

---

## 13. Full test sequence

```bash
python -m pytest tests/test_l5_behavior_atlas_contract.py
python -m pytest tests/test_l5_behavior_atlas_uuru_roundtrip.py
python -m pytest
ruff check .
mypy src/grashof_workspace
python scripts/check_markdown_links.py
```

Then run the H12 exporter command from §11.

---

## 14. Expected H12 readout

A successful A1 H12 export should say, conceptually:

```text
source package:
  full_closeout
  semantic_revalidation = true
  campaign_blocker = STITCHING_CONTROL_BLOCKED

families:
  UURU = <number of emitted R3A natural leaves>

geometry round trip:
  FAIL = 0
  NUMERICAL_PASS = leaves with stored samples
  GEOMETRY_ONLY_PASS = any sampleless diagnostic leaves

workspace evidence eligible:
  0
```

`workspace evidence eligible = 0` is expected because source-parent component identity
has not been independently frozen by R3A H12.

A1 succeeds if it exports honest, reconstructible mechanism specimens. It does not
need R3A to have accepted a reconstruction.

---

## 15. A1 closeout statement

The strongest permitted closeout is:

> The frozen R3A natural-leaf artifacts can be deterministically converted into
> role-aware E0 UURU mechanism records whose complete frozen geometry reconstructs
> the same child closure equations at stored samples. The current H12 source package
> does not provide independent source-parent component identities, so these exported
> specimens are not promoted to workspace evidence.

---

## 16. A2 handoff

A2 starts only after A1 round-trip failures are zero.

A2 then expands:

```text
one frozen R3A package
        ↓
multiple parent geometries / task points / architectures
        ↓
raw source-derived child corpus
        ↓
family counts and observed support
```

A2 still does **not** choose the canonical UURU descriptor vector. That remains A3.
