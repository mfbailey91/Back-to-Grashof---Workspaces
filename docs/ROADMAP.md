# Roadmap

**Status:** ACTIVE (future dependency gates only)
**Authority:** This file is the sole forward plan. Historical sprint numbering lives under `archive/`. Current evidence lives in [CURRENT_STATUS.md](CURRENT_STATUS.md).

---

## R0 — Canonicalize the project contract

**Question:** Can a new reader find one thesis, one status ledger, one ladder, and one roadmap?

**Required inputs:** Cleanup sprint documents and existing theory/ADR corpus.

**Deliverable:** Canonical docs hierarchy; archived lineage; root hygiene.

**Pass/fail gate:** One thesis, one status ledger, one active ladder, one roadmap; internal Markdown links resolve; no scientific-behavior change.

**Blockers:** None for documentation work.

---

## R1 — Freeze the mechanism-behavior certificate

**Question:** Can planar and spatial explorers emit semantically compatible behavior records without claiming the same theorem?

**Required inputs:** [theory/MECHANISM_BEHAVIOR_AND_STITCHING.md](theory/MECHANISM_BEHAVIOR_AND_STITCHING.md); existing planar and spatial explorer outputs.

**Deliverable:** Family-independent behavior result contract (circuit, designated coordinate, completeness, uncertainty, provenance).

**Pass/fail gate:** Compatible behavior records with declared domain; no false workspace promotion.

**Blockers:** R0 canonical language.

---

## R2 — Complete an independent L4 reference

**Question:** Does at least one spatial 4R fixed-position family have a trusted behavior certificate and independent task-image comparison?

**Required inputs:** Spatial 4R source fiber; orientation-curve machinery; component handling.

**Deliverable:** Component-aware L4 behavior certificate and independent orientation-curve validation.

**Pass/fail gate:** Trusted L4 behavior certificate + independent task-image comparison for one family.

**Blockers:** Incomplete global component certification (`local_only` today).

---

## R3 — L5 family construction and stitching

**Question:** Can source-derived one-DOF mechanism families reconstruct independent \(S^2\) pointing evidence with declared completeness and uncertainty?

### R3A — Five-point positive-control reconstruction

Use an unrestricted idealized `U_shoulder-R_elbow-U_wrist` 5R source with an analytical pointing oracle. Freeze five Cartesian probes: deep pointing-complete, inner-complete, inner-incomplete, outer-complete, and outer-incomplete.

Compare four columns:

```text
analytical direction oracle
independent source-chain target-direction IK
stitched source h=c control fibers
stitched exact virtual-coordinate UURU natural leaves
```

The natural child fixes one coordinate of an exact virtual-spherical chart, then follows its own frozen-geometry one-DOF branch. It is not required to remain on the earlier `h=c` pointing level set.

**Required inputs:** R1 certificate vocabulary; shared pseudo-arclength continuation; source-chain FK/Jacobians; [methods/NATURAL_LEAF_FAMILY_CONTRACT.md](methods/NATURAL_LEAF_FAMILY_CONTRACT.md).

**Deliverable:** Five-point analytical/numerical truth, source-control reconstruction, exact `UURU` leaf family, re-seeding/transversality/chart audits, accepted-child union, and three-way comparison dashboard.

**Pass/fail gate:** All five direct classifications agree with the analytical oracle; accepted natural leaves reconstruct the direct pointing image within one declared confirmation-cell diameter, with zero strict false positives and stable refinement.

**Blockers:** No accepted L5 child today. The current fixed-axis `UUUR` remains rejected only as the selected `h=c` source-fiber equivalence. R2 may proceed in parallel and is not a hard blocker for this controlled L5 positive control.

Detailed execution: [methods/R3A_L5_FIVE_POINT_EXECUTION.md](methods/R3A_L5_FIVE_POINT_EXECUTION.md).

#### R3A-H — Evidence hardening gate

The merged R3A software establishes the positive-control arm, oracle, direct IK kernel, source `h=c` control, spherical charts, and frozen-`lambda` `UURU` branch kernel. Before the five-point campaign may issue an accepted reconstruction, harden:

```text
stage dependency and artifact authority
deterministic geometry/artifact identity
direct numerical confirmation as an independent reference
real branch re-seeding consistency
actual child-tangent family transversality
source-space duplicate and chart-overlap semantics
c/lambda interval completeness
negative-probe feasible-set recall
real evidence visualizations and reduced end-to-end CI
```

**Pass/fail gate:** The current ceremonial family audits are replaced by evaluative gates; empty or missing reconstructions cannot pass; all five points receive an honest direct/source/natural set comparison.

Hardening execution: [methods/R3A_HARDENING_EXECUTION.md](methods/R3A_HARDENING_EXECUTION.md).

#### R3A-H7–H10 — Full-mode acceptance and family-scope follow-up

H0–H6 landed an honest unaccepted full-mode hub. Before any controlled cover may be accepted, distinguish not-applicable from unevaluable metrics, compute two-resolution refinement, scope re-seeding and family admission per leaf, freeze chart responsibility and parameter-domain completeness, and compact campaign artifacts.

```text
H7  metric applicability + actual refinement
H8  component-scoped re-seeding + leaf-scoped admission
H9  chart responsibility + parameter-domain completeness
H10 artifact authority + compact full-campaign closeout
```

**Pass/fail gate:** A complete-sphere reference can pass the false-positive sub-gate; missing refinement remains unevaluable; `ci`/`smoke` cannot accept; an honest first-failing-column closeout is valid. R3B and L6 remain held.

Follow-up execution: [methods/R3A_H7_H10_FOLLOWUP_EXECUTION.md](methods/R3A_H7_H10_FOLLOWUP_EXECUTION.md).

#### R3A-H11 — Acceptance-authority hardening before the frozen full rerun

H11 preserves the H7–H10 experiment while hardening the authority boundary around its final run:

```text
package mode/probe/config/provenance fidelity
overlap-band responsibility-transition audits
leaf-pair chart correspondence
returned-set claim narrowing
budget-exhaustion and topology-event honesty
CI test-fixture isolation
strict full-closeout packaging
```

**Pass/fail gate:** A diagnostic package cannot resemble a full package; only actual overlap-band handoffs create required chart audits; required truncated bins remain unresolved; CI is green; and `--full-closeout` accepts exactly one clean, five-probe, full-mode campaign with one explicit first-failing-column outcome.

**H11E disposition withdrawn:** The H11E package itself is authoritative, but its `DIRECT_REFERENCE_BLOCKED` interpretation is not. The H12 rerun replaced the compact hub.

Hardening execution: [methods/R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md](methods/R3A_H11_ACCEPTANCE_AUTHORITY_HARDENING.md).

#### R3A-H12 — Direct-comparison metric repair and closeout revalidation

```text
same-grid strict Hausdorff representatives
ambiguous-boundary exclusion from strict set distances
real non-nested-grid refinement regressions
RETURNED_SET_PASS distinct from component identity
package-side probe and global blocker recomputation
clean frozen five-probe rerun
```

**Pass/fail gate:** A complete-sphere direct result has zero Hausdorff and zero refinement on both declared grids; found boundary cells cannot fail the strict gate; the full-closeout packager independently reproduces every per-probe classification, disposition, and blocker plus the global blocker.

**Recorded H12 closeout:** Frozen `--mode full` at producer `9505a87` packaged as `full_closeout` with `semantic_revalidation=true` records `STITCHING_CONTROL_BLOCKED`. Direct-vs-oracle Hausdorff and refinement are zero on all five probes. Source `h=c` reconstruction fails with unresolved `c` intervals. Do not interpret the natural column. L5 remains `parent_incomplete`. R3B remains held.

Execution: [methods/R3A_H12_DIRECT_COMPARISON_METRIC_REPAIR.md](methods/R3A_H12_DIRECT_COMPARISON_METRIC_REPAIR.md).

#### R3A-H13 — Source-control component and coverage closure (queued)

H13A analytical `c`-domain dispatch exists on a separate config; the H12 compact hub and frozen config remain authoritative. H13B–H13F remain unimplemented. L5 stays `parent_incomplete`. Direct-column metrics and natural-leaf parameters are not retuned while source control is blocked. `RETURNED_SET_FOUND` is declared-budget evidence; `COMPONENT_COMPLETE` stays reserved.

Execution: [methods/R3A_H13_SOURCE_CONTROL_COMPONENT_AND_COVERAGE_CLOSURE.md](methods/R3A_H13_SOURCE_CONTROL_COMPONENT_AND_COVERAGE_CLOSURE.md).

### R3B — Transfer and falsification

Apply the same direct/source/natural comparison to the existing `exact_two_u_5r`, `generic_5r`, and a near-architecture control. Determine which virtual-coordinate families remain exact, how chart choice changes individual leaf behavior, and whether the accepted family still reconstructs the parent pointing image.

**Pass/fail gate:** At least one non-positive-control architecture reproduces independent parent evidence, or the failure is localized to a documented construction/component/coverage gate.

### R3C — L5 behavior-atlas round trip and falsification

After a controlled natural-leaf reconstruction exists, build the first numerical mechanism atlas as a round trip:

```text
5R parent
  -> source-derived child corpus
  -> exact family identity + frozen geometry
  -> family support / canonical descriptors
  -> exact child behavior reference
  -> directed numerical atlas + OOD fallback
  -> held-out 5R reconstruction
```

The order is deliberate: **manipulator → mechanism first** discovers which families and which parameter-space regions matter; **mechanism → atlas second** fills and refines those regions; **atlas → manipulator last** tests whether the compressed predicate preserves the parent pointing result.

Family identity is structural and role-aware. A child is never assigned to the “closest” family. Out-of-distribution atlas queries remain unresolved and route to the exact child solver.

**Pass/fail gate:** On a held-out 5R parent, atlas-backed child evaluation preserves an exact-child reconstruction that already agrees with decomposition-free \(S^2\) truth, or the failure is localized to the atlas while the exact-child decomposition remains valid.

**Eject gate:** If exact child behavior is trustworthy but exact-child stitching fails to reconstruct held-out parent truth, the decomposition/stitching hypothesis is incomplete; do not blame or scale the atlas.

Detailed program: [methods/L5_BEHAVIOR_ATLAS_ROUND_TRIP.md](methods/L5_BEHAVIOR_ATLAS_ROUND_TRIP.md). A0 contract: [methods/R3C_A0_BEHAVIOR_ATLAS_CONTRACT.md](methods/R3C_A0_BEHAVIOR_ATLAS_CONTRACT.md). A1 exporter: [methods/R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER.md](methods/R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER.md).

**A1 authority:** Exporting the frozen H12 natural leaves proves mechanism-definition portability only. H12 source-parent component IDs remain unresolved, so current E0 specimens are not workspace evidence and the H12 `STITCHING_CONTROL_BLOCKED` closeout is unchanged.

**A2 diagnostic campaign:** [methods/R3C_A2_5R_PARENT_CAMPAIGN.md](methods/R3C_A2_5R_PARENT_CAMPAIGN.md) may inventory exact source structure and reconstructible child-family support without promoting R3A. Exact parent patterns are separated from actual E0 children; near/generic controls are never nearest-matched; S-physical candidate families remain outside the first detector scope.

**R3 completion gate:** R3A must pass, transfer evidence must exist, and R3C must reach a parent-level falsification result before the aligned-roll L6 program becomes the primary workstream. A0 infrastructure may land earlier because it makes no scientific promotion.

---

## R4 — L6 decomposition-free orientation reference

**Question:** Can we build an independent fixed-position \(SO(3)\) reference for a controlled 6R architecture?

**Required inputs:** L6 contracts; component-aware orientation truth machinery.

**Deliverable:** Reproducible decomposition-free orientation reference.

**Pass/fail gate:** Component-aware orientation truth for a controlled 6R architecture.

**Blockers:** R3C parent-level falsification gate; L6 remains `scaffold_only`. Thin L6 contract/scaffold maintenance may continue, but the aligned-roll numerical program stays downstream of the L5 round trip.

---

## R5 — L6 nested reconstruction

**Question:** Can child-family stitching reconstruct full \(SO(3)\) coverage, including roll handling and component correspondence?

**Required inputs:** R4 reference; nested child-family contract; roll quotient tests where claimed.

**Deliverable:** Reconstructed orientation image vs independent L6 reference.

**Pass/fail gate:** Agreement over a declared architecture domain.

**Blockers:** R3 transfer evidence and R4; roll factorization only after invariance tests.

---

## R6 — L7 redundancy and gauge

**Question:** Can orientation coverage be separated from self-motion/gauge freedom without conflating redundancy with dexterity?

**Required inputs:** Completed L6 reconstruction contract; gauge formulation.

**Deliverable:** Extended reconstruction contract with explicit redundancy handling.

**Pass/fail gate:** Orientation claims remain distinct from self-motion certificates.

**Blockers:** L6 completion.

---

## R7 — Broad rule discovery and atlas generalization

**Question:** After the L5 round-trip atlas and higher-rung reconstruction are demonstrated, which broader family atlases and Grashof-like rules are evidence-supported beyond the source-derived L5 support?

**Required inputs:** R3C family atlases and exact fallback policy; successful higher-rung reconstruction examples.

**Deliverable:** Expanded family domains, cross-architecture atlas support, compact rules where supported, and workspace certificates with uncertainty.

**Pass/fail gate:** No rule is promoted beyond the mechanism and architecture domain on which parent reconstruction has been validated.

**Blockers:** R3C round-trip evidence and subsequent reconstruction gates. Broad mathematical coverage of arbitrary spatial four-bars remains downstream of source-derived support.
