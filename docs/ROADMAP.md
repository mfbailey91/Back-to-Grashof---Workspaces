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

### R3B — Transfer and falsification

Apply the same direct/source/natural comparison to the existing `exact_two_u_5r`, `generic_5r`, and a near-architecture control. Determine which virtual-coordinate families remain exact, how chart choice changes individual leaf behavior, and whether the accepted family still reconstructs the parent pointing image.

**Pass/fail gate:** At least one non-positive-control architecture reproduces independent parent evidence, or the failure is localized to a documented construction/component/coverage gate.

### R3C — Mechanism behavior compression

Only after R3A or R3B succeeds, test whether winding, crank/rocker, circuit, branch, or a numerical atlas can compress the accepted family result without losing reconstruction provenance.

**R3 completion gate:** One controlled reconstruction must pass before L6 positive-control work begins. General 5R claims and broad rule discovery remain blocked until transfer evidence exists.

---

## R4 — L6 decomposition-free orientation reference

**Question:** Can we build an independent fixed-position \(SO(3)\) reference for a controlled 6R architecture?

**Required inputs:** L6 contracts; component-aware orientation truth machinery.

**Deliverable:** Reproducible decomposition-free orientation reference.

**Pass/fail gate:** Component-aware orientation truth for a controlled 6R architecture.

**Blockers:** R3A controlled reconstruction gate; L6 remains `scaffold_only`. R3B transfer may continue in parallel after the positive-control stitching operation is stable.

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

## R7 — Rule discovery, atlases, and certificates

**Question:** After source-to-child-to-parent reconstruction is demonstrated, which family atlases and Grashof-like rules are evidence-supported?

**Required inputs:** Successful reconstruction examples; conservative numerical atlas + exact fallback policy.

**Deliverable:** Scaled family atlases; compact rules where supported; workspace certificates with uncertainty.

**Pass/fail gate:** No atlas or rule is promoted as workspace method without reconstruction provenance.

**Blockers:** Reconstruction gate (R3+). The old broad spatial-four-bar atlas program belongs here, not at the front of the program.
