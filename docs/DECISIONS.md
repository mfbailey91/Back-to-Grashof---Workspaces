# Architecture Decisions

## ADR-001 — Start with unrestricted planar 3R

**Decision:** Phase 1 assumes all three revolute joints can traverse \(2\pi\).

**Reason:** This exposes rotational symmetry and produces a clean analytical baseline. Joint limits are a separate mechanism that break or restrict that symmetry and should not be mixed into the first proof.

## ADR-002 — Keep analytical and sampled methods independent

**Decision:** The analytical workspace is computed from interval containment. Direct orientation sampling is used only for validation.

**Reason:** A sampled map must not silently become the definition of the workspace being claimed as analytical.

## ADR-003 — Track link-specific rotatability

**Decision:** Use Grashof classification as metadata, but determine whether \(l_3\) rotates fully through exact loop-closure bounds.

**Reason:** The generic Grashof condition only states that at least one link may rotate in a linkage family. The workspace question concerns one specific link in one specific inversion.

## ADR-004 — No robotics framework dependency in the MVP

**Decision:** Use Matplotlib only for visualization. The analytical kernel is pure Python.

**Reason:** The initial mathematics is small enough to inspect directly. URDF parsing, symbolic packages, NumPy, and general robot libraries can be added after the core result is stable.

## ADR-005 — Capability fields begin only after workspace validation

**Decision:** Do not build task decomposition or capability scoring into Sprint 1–2.

**Reason:** The first research claim is the workspace boundary. Capability fields should be layered on a trusted geometric kernel rather than developed simultaneously.

## ADR-006 — Classification precedence and radial mechanism state

**Decision:** Classify equivalent four-bars with assemblability and degeneracy before conventional Grashof inversion names, and expose a single `RadialMechanismState` record for atlas CSV and radial plots.

**Reason:** Non-assemblable and coincident-ground loops must not inherit misleading mechanism labels, and the Grashof-to-dexterity relationship must be inspectable from one API.

---

## ADR-007 — The fixed-position fiber is the foundational spatial object

**Decision:** Define the spatial problem from

\[
\mathcal F_{p^*}=\{q:p(q)=p^*\}
\]

before proposing any virtual four-bar family.

**Reason:** The fiber is determined by the manipulator and task. A candidate decomposed mechanism is architecture-dependent and may be accepted, component-limited, or rejected without invalidating the source construction.

## ADR-008 — Separate fiber, image, and coverage target

**Decision:** Store the fixed-position configuration set, the orientation/pointing image it generates, and the task coverage target as separate data objects.

**Reason:** A mechanism may have the right mobility but generate only a proper subset of the target. The image is a result; the target is a requirement.

## ADR-009 — Start the active spatial ladder at the 4R serial chain

**Decision:** V05 begins with a spatial 4R serial manipulator and its exact \(4R+S_v\), \(M=1\) closure. The program then advances to 5R and 6R source mechanisms.

**Reason:** Planar 3R is already the trusted reference. Spatial 4R is the minimum regular spatial case with a one-dimensional fixed-position fiber, allowing direct continuation and exact comparison against any proposed one-DOF reduction without an arbitrary pointing slice.

## ADR-010 — Exact virtual closure is not a four-bar decomposition

**Decision:** Adding \(S_v\) at the fixed tool point is treated as an exact task-constraint representation. Axis aggregation, quotienting, slicing, and factorization are recorded as separate operations.

**Reason:** Conflating closure with decomposition makes it impossible to localize whether a failure comes from the basic fixed-position model or from a proposed lower-dimensional representation.

## ADR-011 — Use an explicit decomposition-operation taxonomy

**Decision:** Every reduction step is labeled as one of:

```text
axis_aggregation
symmetry_quotient
task_slice
mechanism_factorization
predicate_application
coverage_reconstruction
```

**Reason:** These operations have different mathematical meanings, mobility effects, and proof obligations. In particular, an \(M=2\) parent is not automatically two independent \(M=1\) factors.

## ADR-012 — Require decomposition certificates

**Decision:** Every proposed source-to-reduced mechanism mapping receives one of:

```text
EXACT_GLOBAL
EXACT_ON_COMPONENT
LOCAL_ONLY
APPROXIMATE
REJECTED
UNRESOLVED
```

with coordinate maps, reconstruction maps, component scope, rank checks, tangent error, trajectory error, and joint-limit correspondence.

**Reason:** A visually plausible topology or matching DOF count is not sufficient evidence of kinematic equivalence.

## ADR-013 — Build the source-chain reference before mechanism reconstruction

**Decision:** V05, V06, and V07 establish source-chain orientation/pointing truth before V09 applies mechanism predicates and recombination laws.

**Reason:** Validation is not independent if the reference result is built from the same decomposition being tested.

## ADR-014 — Treat terminal roll as a conditional quotient

**Decision:** Factor \(R_6\) only when the joint is coincident with the selected tool-roll axis, leaves tool position and pointing invariant, has the required range, and admits component-preserving quotient/reconstruction maps.

**Reason:** The aligned-roll case is a structured special case. A DOF count alone does not prove that full orientation equals complete pointing plus available roll.

## ADR-015 — Reserve dexterity for full orientation coverage

**Decision:** Use `dexterous_workspace` for full \(SO(2)\) or \(SO(3)\) coverage. Use `pointing_image` and `pointing_complete_workspace` when roll is intentionally excluded.

**Reason:** A spatial 5R may have the correct residual dimension for \(S^2\) pointing but cannot generically cover all of \(SO(3)\).

## ADR-016 — Preserve components and qualified numerical coverage

**Decision:** Continuation and coverage reports identify source components, singular boundaries, chart scope, sampling resolution, confidence, and unresolved regions. Finite numerical evidence uses labels such as `COVERED_AT_DECLARED_RESOLUTION`, not an unqualified theorem.

**Reason:** One returned branch does not establish the full fiber, and finite sampling cannot silently become proof of global coverage.

## ADR-017 — Defer the broad spatial-four-bar atlas until decomposition validation

**Decision:** The previous all-family atlas, descriptor mining, candidate-rule, fast-evaluator, and broad 6R validation sequence is remapped from V05–V09 to V10–V14.

**Reason:** Broadly optimizing a mechanism classifier is premature until at least one manipulator-to-mechanism reduction, predicate, and recombination law reproduce independent source-chain truth.

## ADR-018 — Structural analysis may use a numerical mechanism predicate

**Decision:** A workspace method may be described as structural or semi-analytical when the source reduction and coverage criterion are derived analytically but a family-specific crank/coverage decision is evaluated numerically, provided the numerical status and fallback are explicit.

**Reason:** The absence of a closed-form spatial Grashof inequality does not erase the analytical content of an exact kinematic reduction, but numerical classification must not be mislabeled as an analytical theorem.

## ADR-019 — Mechanism identities are role-aware, not letter-string-only

**Decision:** Every compound-joint mechanism record stores both `joint_kind_sequence` and `joint_role_sequence`, including explicit roles such as `S_v`, `U_v`, `S_phys`, `U_phys`, and `R_phys`. The cyclic origin and designated task/winding joint are also recorded.

**Reason:** A V05 source mechanism `S_v-U_phys-R-R` can be cyclically isomorphic to a `USRR`-class solver topology without being semantically equivalent to a V08 child `U_v-...` mechanism. The same joint letters can assign the virtual tool closure, physical axis aggregate, and designated winding coordinate to different joints. Solver topology may be reused; task interpretation may not.

---

## ADR-020 — Preserve terminal roll as a control, not the generic V05 source

<!-- V05_AUDIT_CORRECTION_2026_08_08 -->

**Decision:** Active spatial-4R V05 sources place the tool point transversely off the terminal axis. The original on-axis geometry is retained as `terminal_roll_control_4r`.

**Reason:** With the tool point on the final axis and pointing collinear with it, the final position- and pointing-Jacobian columns vanish. At rank three / nullity one the fixed-position fiber is necessarily pure terminal roll, not a nontrivial coupled spatial self-motion.

## ADR-021 — Separate exact axis aggregation from closed-mechanism equivalence

**Decision:** `RR → U_phys` receives its own exact axis-aggregation status. An independently instantiated and continued `S_v-U_phys-R-R` mechanism receives a separate closed-mechanism status.

**Reason:** Comparing a serial source chain to the same chain under an identity coordinate regrouping proves the regrouping but cannot prove source-component correspondence to an independent closed mechanism.

## ADR-022 — Jacobians may be analytical, automatic, or numerical, but must be checked

**Decision:** The continuation kernel may use an analytical geometric Jacobian, automatic differentiation, or a numerical derivative. The analytical V05 Jacobian is cross-checked against central finite differences at each seed.

**Reason:** A derivative is not required merely to find one configuration, but rank, tangent, pseudo-arclength correction, conditioning, and singularity diagnostics require derivative information or an approximation to it.

---

## ADR-023 — Optional L3–L7 ladder scaffold subordinate to active V05–V09

<!-- DECOMPOSITION_LADDER_L3_L7_2026_08_12 -->

**Decision:** Keep `docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md` as the active scientific sequence. Treat `docs/DECOMPOSITION_LADDER_L3_L7_PROGRAM.md` as an optional interface scaffold that maps L3→planar calibration, L4→V05, L5→V06, L6→V07-first then V08, and L7 as deferred/BLOCKED until the V05 closed-mechanism gate lifts.

**Reason:** The dimensional parent→fiber→child contract is reusable, but promoting a parallel “active general program” would demote the audited V05 HOLD and reopen the V05A undifferentiated-PASS failure mode.

## ADR-024 — A higher-dimensional parent is reconstructed from an audited fiber family, not assumed to be a product

**Decision:** Treat L5/L6/L7 parents as unions or foliations of level-set fibers only after slice-parameter coverage, critical values, components, and singular fibers are represented. Do not assume \(P^m\cong F^1\times B^{m-1}\).

**Reason:** Fibers may appear, disappear, split, merge, or collapse at critical values. A stack of selected curves is not automatically the complete parent.

## ADR-025 — Canonical U-joint drive is the one-dimensional branch parameter

**Decision:** For a one-DOF child containing `U_v`, drive pseudo-arclength `s` by default and read `alpha(s)` and `beta(s)` from one branch. A prescribed-alpha or prescribed-beta solve is a local chart valid only when the selected coordinate derivative is nonzero.

**Reason:** A universal joint has two chart coordinates, but loop closure leaves the complete child with one global DOF. Treating alpha and beta as independent inputs would violate the mechanism mobility.

## ADR-026 — Descriptor discovery remains downstream of successful reconstruction

**Decision:** Keep the historical descriptor-mining sprint deferred until at least one independently computed source-parent task image is reconstructed from accepted source-derived child mechanisms within documented tolerances.

**Reason:** Otherwise the project risks discovering correlations for representation-dependent winding labels that have not been shown to determine manipulator orientation coverage.

## ADR-027 — Ladder certificates preserve the ADR-021 aggregation/closed split

**Decision:** Ladder `EquivalenceCertificateRecord` stores `axis_aggregation_status` and `closed_mechanism_status` separately; overall status mirrors closed-mechanism status. Leaf promotion to `source_chain_evidence` requires a real accepted closed-mechanism certificate object, never caller status strings alone. Process labels (`PLANNED`/`SCAFFOLD`/`BLOCKED`/`REVIEW`) live in `ProcessStatus`, not in the certificate taxonomy.

**Reason:** Re-merging process labels into certificate statuses and trusting forged provenance strings recreates the audit defects that forced V05 overall HOLD.

---

## ADR-028 — Scoped EXACT_ON_COMPONENT closes the V05 gate for exact_u_pair_4r

<!-- V05_CLOSED_MECHANISM_GATE_2026_08_13 -->

**Decision:** An independently instantiated and continued proximal `S_v-U_phys-R-R` loop that matches the `exact_u_pair_4r` source fiber over an explicit component scope may receive `closed_mechanism_status=EXACT_ON_COMPONENT`. Axis aggregation remains a separate `EXACT_GLOBAL` claim. Multi-component `EXACT_GLOBAL`, non-proximal pairs, and other corpus architectures remain unresolved. Identity-on-same-chain residuals still cannot promote closed-mechanism status.

**Reason:** The audited HOLD required an independent reduced solve, not merely scalar regrouping. One scoped accepted component is sufficient to close the V05 gate for that architecture while preserving honesty about incomplete global coverage.

## ADR-029 — L3 emits shared ladder records from the analytical planar map

<!-- L3_INTERFACE_RETROFIT_2026_08_13 -->

**Decision:** The L3 planar calibration adapter emits shared ladder evidence records
(`SourceParentRecord`, fiber/child/certificate/leaf/reconstruction) from the existing
`Planar3R`/`FourBar` analytical map at each radius. `EXACT_GLOBAL` certifies the 3R↔4R
map (including non-assemblable exterior radii); dexterity/rotatability remain separate
predicates. Process status stays `SCAFFOLD`. The program-doc name `SourceProblemRecord`
aliases `SourceParentRecord`. This does not demote V05–V09 primacy or substitute for
spatial closed-mechanism certificates.

**Reason:** The ladder acceptance criterion is interface retrofit without changing the
trusted mathematical kernel; a duplicate problem-record type would only create drift.

## ADR-030 — Workspace exemplar viz is not a certificate path

<!-- WORKSPACE_EXEMPLAR_VIZ_2026_08_13 -->

**Decision:** Planar workspace exemplar statics/GIFs under `outputs/workspace_exemplars/`
reuse existing `Planar3R`/`FourBar` classification and a visualization-only pose sampler.
They do not change analytical workspace predicates and do not issue
`DecompositionCertificate` / ladder equivalence claims.

**Reason:** Side-by-side reduced-mechanism behavior is an evidence aid for the trusted
planar map; conflating renders with certificates would recreate provenance defects.
