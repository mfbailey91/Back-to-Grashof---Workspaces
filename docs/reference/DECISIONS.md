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

## ADR-023 — L3–L7 ladder scaffold (historical; superseded by ADR-048)

<!-- DECOMPOSITION_LADDER_L3_L7_2026_08_12 -->
<!-- SUPERSEDED by ADR-048 (2026-08-16): ladder is now the active architecture. -->

> **Superseded by ADR-048.** Retained as historical decision text. The L3–L7
> ladder is now the active architecture; V05–V09 documents are archived lineage.

**Decision (historical):** Keep the V05–V09 program Markdown as the then-active
scientific sequence. Treat the L3–L7 program Markdown as an interface scaffold
mapping L3→planar calibration, L4→V05, L5→V06, L6→V07-first then V08, and L7 as
deferred/BLOCKED until the V05 closed-mechanism gate lifts.

**Reason (historical):** The dimensional parent→fiber→child contract is reusable,
but promoting a parallel general program at that time would have demoted the
audited V05 HOLD and reopened the V05A undifferentiated-PASS failure mode.

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

## ADR-031 — L4 wraps V05 closed-mechanism evidence into shared ladder records

<!-- L4_V05_INTERFACE_2026_08_13 -->

**Decision:** The L4 ladder adapter emits shared evidence records from the existing V05
proximal `exact_u_pair_4r` independent closed-mechanism path (plus V05C orientation-curve
truth on the claimed component). Catalog `FiberFamilySpec` status may be
`EXACT_ON_COMPONENT` only with that scoped meaning; multi-component `EXACT_GLOBAL` and
other architectures remain unresolved. Process status stays `SCAFFOLD`. V05–V09 remains
the scientific source of truth; the ladder does not re-solve the reduced loop.

**Reason:** L4 acceptance is interface expression of the audited V05 gate, not a parallel
scientific sequence or an over-claim of global spatial-4R coverage.

## ADR-032 — L5 scaffold is not a V06A parent or pointing reconstruction

<!-- L5_SCAFFOLD_INTERFACE_2026_08_13 -->

**Decision:** The L5 ladder adapter may promote process status to `SCAFFOLD` with a
synthetic spatial-5R seed audit (`rank Jp=3`, `nullity=2`) and candidate letter-family
records whose axis aggregation, closed-mechanism, and reconstruction statuses remain
`UNRESOLVED`. This does **not** constitute a two-dimensional `FixedPositionParentResult`,
does not reconstruct the pointing image, and must not promote `U_v` leaf roles to
`source_chain_evidence`. Reconstruction stays blocked until accepted source-derived
children exist and an independent parent image is available (Gate K2 / ADR-024 /
ADR-026). V06A remains the next scientific step; V05–V09 primacy is unchanged.

**Reason:** Architecture-scoped interface exercise after the proximal exact-U gate is
useful, but claiming a complete M=2 parent from a seed audit or 1D fiber placeholders
would violate the evidence chain.

## ADR-034 — Budget-limited L4 matches are LOCAL_ONLY and reconstruction is target-aware

<!-- L4_TRACED_ARC_SCOPE_HARDENING_2026_08_13 -->

**Decision:** The current proximal `exact_u_pair_4r` independent
`S_v-U_phys-R-R` comparison remains valid numerical evidence, but its source branch is
budget-limited and the solver has not established complete bidirectional source/child
component correspondence. Therefore the closed-mechanism disposition is
`LOCAL_ONLY`, with scope `local_on_traced_arc:*`; `EXACT_ON_COMPONENT` is reserved for
a complete explicitly bounded or returned source/child component comparison. Exact
physical `RR→U_phys` aggregation remains independently `EXACT_GLOBAL`.

For an L4 target `Y1 ⊂ SO(3)`, ladder reconstruction must use the full orientation
geodesic error, not only pointing error. A local orientation match may be reported as
`matched_on_traced_arc`, but it does not populate `accepted_fiber_ids`.

The L5 scaffold must not list its one-dimensional placeholder as a discovered
two-dimensional parent component. Direct V06A source-parent construction may proceed
without inheriting an L4 component certificate; any decomposition-dependent child or
reconstruction claim remains gated.

**Reason:** A finite traced arc is evidence for local equivalence, not equality of complete
connected components. Task-aware metrics and honest parent/component identity prevent a
numerically good local result from being silently promoted into a global reconstruction.

## ADR-035 — V06A0 is manifold-engine software validation, not a parent certificate

<!-- V06A0_MANIFOLD_ENGINE_2026_08_13 -->

**Decision:** V06A0 implements a generic two-dimensional implicit-manifold atlas engine and validates it on the analytical unit-sphere fixture. Process/software status may be recorded as `SOFTWARE_VALIDATION`. This does **not** issue a `DecompositionCertificate`, does not construct a spatial-5R `FixedPositionParentResult`, and does not change L5 reconstruction or catalog certificate statuses. V06A1 is the first 5R local-chart claim.

**Reason:** A collection of numerical charts on an analytical surface is not source-chain evidence. Mixing engine tests with parent certificates would violate Gate K2 / ADR-032.

## ADR-036 — LOCAL_PATCH is a parent-representation status, not a certificate

<!-- V06A1_LOCAL_PATCH_2026_08_13 -->

**Decision:** V06A1 may emit a `FixedPositionParentResult` with representation status
`LOCAL_PATCH` for one hexagonal chart of `generic_5r`. This is not a complete
connected component, not `S^2` coverage, not L5 reconstruction, and not a
`DecompositionCertificate`. L5 process status stays `SCAFFOLD`; fibers, children,
and reconstruction remain `UNRESOLVED`. `component_ids` stay empty until V06A2
component discovery.

**Reason:** A visually plausible local chart is not the two-dimensional parent
(Gate K2). Representation statuses must stay separate from certificate statuses.

## ADR-037 — A parent atlas is a representation, not a closed component or certificate

<!-- V06A2_PARENT_ATLAS_2026_08_13 -->

**Decision:** V06A2 may emit a multi-chart `ParentAtlasResult` for `generic_5r` with
representation statuses such as `ATLAS_OPEN_FRONTIER`, `BUDGET_LIMITED`,
`SINGULAR_BOUNDARY`, or `MULTICOMPONENT_UNRESOLVED`, plus a separate
`ComponentDiscoveryStatus`. These are not `DecompositionCertificate` statuses.
A one-seed atlas, even with Sobol confirmation, is not a complete parent and is
not `S^2` coverage. L5 may name the seed-grown `component_ids` only as a
representation handle. Fibers, children, and reconstruction stay `UNRESOLVED`.
`CLOSED_COMPONENT_AT_DECLARED_RESOLUTION` is reserved for an actually closed
atlas at a declared resolution.

**Reason:** Growing charts and clustering projected seeds can still leave open,
singular, or extra-component frontiers. Treating that work as reconstruction or
as `EXACT_ON_COMPONENT` would violate Gate K2 / ADR-032 / ADR-036.

## ADR-038 — V06C source images are task truth at declared resolution, not coverage or certificates

<!-- V06C_SOURCE_IMAGES_2026_08_14 -->

**Decision:** V06C may emit a `ParentOrientationSurfaceResult` and
`ParentPointingImageResult` by mapping the V06A2 source atlas through `R(q)` and
`d=R z_T`, plus a declared-resolution icosphere grid. These are not V05
orientation-curve objects, not all of `SO(3)`, not `S^2` completeness, and not
`DecompositionCertificate`s. While the atlas is `BUDGET_LIMITED`, open, or
multicomponent-unresolved, image-level coverage is `PARTIAL_COVERAGE` or
`UNRESOLVED` — never global `COVERED_AT_DECLARED_RESOLUTION`. L5 reconstruction
stays `UNRESOLVED`. V06B remains the next scientific slice.

**Reason:** A mapped pointing mesh from an incomplete parent atlas is an oracle
for later comparison, not a workspace theorem (Gate K2 / ADR-008 / ADR-013).

## ADR-039 — Two-pair EXACT_GLOBAL aggregation is not a complete SUUR parent

<!-- V06B_SUUR_PARENT_2026_08_14 -->

**Decision:** V06B may certify exact non-overlapping `RR→U_phys` pairs on
`exact_two_u_5r` as `axis_aggregation_status=EXACT_GLOBAL` and instantiate an
independent `S_v-U_phys-U_phys-R` (`8` coordinates, `6` equations, `M=2`) atlas.
Closed-mechanism status remains `LOCAL_ONLY` while source/reduced correspondence
is budget-limited. `near_two_u_5r` and `generic_5r` must not receive exact
two-pair aggregation. Semantic family SUUR is not `UUUR` and must not introduce
`U_v`. L5 letter-family children and reconstruction stay `UNRESOLVED`.

**Reason:** Physical regrouping of screws is not equivalence of complete
two-dimensional parent components (ADR-010 / ADR-021 / Gate K2).

## ADR-040 — Task-derived h=c fibers are not parent completeness or U_v

<!-- V06D1_SOURCE_LEVEL_SETS_2026_08_14 -->

**Decision:** V06D1 may continue one-dimensional source fibers of
`h(d)=n·d = c` on the already represented `generic_5r` parent atlas. Provenance
is `task-derived`. These fibers are evidence for a declared slice only. They do
not complete the two-dimensional parent (Gate K2), do not instantiate `U_v` or
`UUUR`, and do not accept reconstruction. A budget-limited atlas typically
yields open or boundary-touching contours, not a complete foliation. V06D2
remains the next scientific slice.

**Reason:** Level-set traces of a pointing scalar are not a virtual-U chart,
not a child mechanism, and not coverage reconstruction (ADR-008 / ADR-013 /
ADR-024).

## ADR-041 — A local U_v chart and one UUUR child are not reconstruction

<!-- V06D2_VIRTUAL_U_CHILD_2026_08_14 -->

**Decision:** V06D2 may derive a local candidate `U_v` from the kernel of
`(d×n)^T` on one `exact_two_u_5r` `h=c` fiber and instantiate a single
independent `U_v-U_phys-U_phys-R` child (7 coordinates, 6 equations, drive `s`).
The chart is local, not a global child proof. Other letter families are not
swept. Closed-mechanism status is issued from the comparison and is not
initialized as accepted. Only `EXACT_GLOBAL` or `EXACT_ON_COMPONENT` may enter
reconstruction; budget-limited open fibers typically remain `LOCAL_ONLY` or
`REJECTED`. V06E remains the next scientific slice.

**Reason:** Task-derived virtual-U replacement of `S_v` on a slice is not parent
completeness and not coverage reconstruction (Gate K2 / ADR-024 / ADR-040).

## ADR-042 — Source-fiber cell paint is not reconstruction from accepted children

<!-- V06E_RECONSTRUCTION_CLOSEOUT_2026_08_14 -->

**Decision:** V06E may compare task-derived `h=c` fibers to the frozen V06C
sphere grid (stage 1) and must leave stage 2 empty unless a child carries
`EXACT_GLOBAL` or `EXACT_ON_COMPONENT`. A `LOCAL_ONLY` UUUR child is excluded.
Partial fiber-hit metrics, Hausdorff error, and an explicit factorization
status such as `no valid recombination` do not complete the 2D parent, do not
pass the V06 coverage gate, and do not lift ADR-026 descriptor discovery.
V07A remains the next scientific slice.

**Reason:** Gate K2 / ADR-024 reconstruct a parent from an audited accepted
fiber/child family, not from a stack of open traces (ADR-026 / ADR-038).

## ADR-043 — Conjunctive local equivalence and non-vacuous coverage metrics

<!-- V06H0_H2_SEMANTIC_HARDENING_2026_08_14 -->

**Decision:** `LOCAL_ONLY` for a task-derived UUUR child is conjunctive: every
named local metric must pass, including independent directed distances
\(d_{S\to C}\) and \(d_{C\to S}\), `|h-c|`, tangent error, and scoped sample
support. The virtual-U chart remains `LOCAL_CANDIDATE` until a later global
chart audit. An empty interior `COVERED` cell population makes the missed-cell
fraction undefined (`None` / JSON `null`); factorization and reconstruction
coverage are then `unresolved` / `UNRESOLVED`. Current V06D2/V06E dispositions
are re-opened under this contract (see `docs/V06_HARDENING_PATCH.md`). H0–H2
do not rewrite continuation, stitch atlases, or promote `EXACT_*`.

**Reason:** Issuing `LOCAL_ONLY` from a subset of residuals, or a zero miss
fraction from `max(1, 0)` COVERED cells, is a vacuous certificate and a
vacuous coverage metric. Gate K2 still requires independently reconstructed
parent task images from accepted children.

## ADR-044 — Shared 1D pseudo-arclength engine is not a D1/D2 migration

<!-- V06H3_BRANCH_CONTINUATION_2026_08_15 -->

**Decision:** V06H3 adds `branch_continuation.py` as shared infrastructure for
one-dimensional implicit branches: predictor `x_k + ds t_k`, augmented
corrector `[F(x); t_k^T Δ(x,x_pred)]=0`, step adaptation, and conjunctive
return (minimum arclength, wrapped state, tangent alignment, branch identity).
Position-only return detection is forbidden. V06H4 migrates D1/D2 onto this
engine (ADR-045). The engine itself does not issue certificates, reconstruct a
parent, or authorize V07A.

**Reason:** Replacing underdetermined D1/D2 correctors before the shared
augmented solver exists would mix a numerical rewrite with a scientific
re-audit (Gate K2 / ADR-043).

## ADR-045 — D1/D2 traces use the H3 augmented corrector

<!-- V06H4_D1_D2_MIGRATE_2026_08_15 -->

**Decision:** V06D1 `continue_level_set` and V06D2 `continue_uuur` continue with
the shared pseudo-arclength engine. Source and child equations are unchanged.
Seed projection may still use the existing minimum-norm projectors; the
continuation loop does not. UUUR local status is whatever the conjunctive H1
audit issues after migration (`REJECTED`, `LOCAL_ONLY`, or `UNRESOLVED`). That
is not parent completeness, not `EXACT_*` without component correspondence, and
not V07A authorization.

**Reason:** Underdetermined min-norm correction along a 1D fiber is not
pseudo-arclength (ADR-044). Re-auditing the child after the numerical fix
prevents carrying a vacuous pre-H3 disposition (ADR-043).

## ADR-046 — Stitch atlas charts and grow clustered unattached seeds

<!-- V06H5_PARENT_STITCH_2026_08_15 -->

**Decision:** V06A2/H5 clusters projected Sobol seeds before attachment, may
grow extra atlas components from unattached cluster representatives within a
declared total chart budget, and assigns component ids from chart-overlap
connectivity. Vertices and faces are globally deduplicated in wrapped joint
space. Chart-ring vertices in overlaps are seams, not global frontiers.
Singular and budget-limited frontiers remain explicit. D1 contours are taken
on the stitched mesh and continued fibers at the same `c` are deduplicated by
symmetric wrapped set distance. This is not a closed parent, not `S^2`
coverage, and not V07A authorization.

**Reason:** Chart-local rings and unpaired D1 traces cannot decide whether
extra Sobol projections are new components or overlap duplicates (Gate K2 /
ADR-037).

## ADR-047 — V06H6 closeout: UUUR rejected; factorization unresolved; V07A held

<!-- V06H6_CLOSEOUT_2026_08_15 -->

**Decision:** V06 campaign closeout answers, without inventing a pass:

1. **Parent completeness:** No. The atlas is stitched (ADR-046) but remains
   `BUDGET_LIMITED`; unattached Sobol seeds remain; this is not a closed 2D
   component.
2. **Source pointing fibers:** Task-derived and H3-continued; seam-stitched
   and deduplicated. Not a complete foliation or a globally identified fiber
   family.
3. **Fixed-axis UUUR vs source fiber:** No. The conjunctive H1 audit remains
   `REJECTED` (failed `h_c` and directed source-to-child distance on the
   regenerated D2 artifact). Chart status stays `LOCAL_CANDIDATE`.
4. **Accepted children for reconstruction:** None (`EXACT_*` empty).
5. **Factorization:** `unresolved` for the campaign. Empty accepted children
   do not earn `no valid recombination` even if a nonempty `COVERED` cell
   makes the miss fraction numerically defined (ADR-043 / hardening plan §4).
6. **V07A:** Not authorized. Held pending parent/continuation completeness.

Canonical line:

```text
current fixed-axis UUUR construction rejected;
broader 5R factorization unresolved;
V07A held pending parent/continuation completion.
```

**Reason:** Dimension matching, a rejected child, or a defined miss metric is
not recombination. Descriptor discovery stays blocked (ADR-026).

## ADR-048 — Mechanism behavior and coverage stitching are the general framework

<!-- CANONICAL_AUTHORITY_2026_08_16 -->

**Decision:** The project’s active architecture is the L3–L7 fixed-position
kinematic-decomposition ladder. Grashof classification is treated as one possible
four-bar behavior descriptor rather than the universal premise. Higher-dimensional
workspace claims require source-derived child families, behavior certificates,
coverage/compatibility stitching, and independent parent-image validation.
Historical V05–V09 program documents are archived as lineage; the roadmap is
rung-centric ([`../ROADMAP.md`](../ROADMAP.md)); numerical predicates remain permitted
when uncertainty and exact fallback are explicit.

**Reason:** The planar reference succeeds because its fixed-position problem is a
one-DOF four-bar rotatability problem. Spatial source mechanisms have higher
mobility and require decomposition and reconstruction before a four-bar predicate
can support a workspace claim.

**Consequence:** Prior wording that treated the ladder as non-primary relative to
V05–V09 is withdrawn. [`../CURRENT_STATUS.md`](../CURRENT_STATUS.md) is the sole
live status ledger.
[`../theory/MECHANISM_BEHAVIOR_AND_STITCHING.md`](../theory/MECHANISM_BEHAVIOR_AND_STITCHING.md)
states the behavior-certificate and stitching contract.

## ADR-033 — L6 scaffold is not a V07 frozen SO(3) reference

<!-- L6_SCAFFOLD_INTERFACE_2026_08_13 -->

**Decision:** The L6 ladder adapter may promote process status to `SCAFFOLD` with a
synthetic non-aligned spatial-6R seed audit (`rank Jp=3`, `nullity=3`) and empty
child/certificate lists whose reconstruction status remains `UNRESOLVED`. This does
**not** freeze a decomposition-free SO(3) orientation reference (Gate K3 / V07A), does
not authorize nested orientation-slice reconstruction, and does not start V08
terminal-roll quotient work. V07A remains held pending the independent L6 reference
gate (ADR-048 / `CURRENT_STATUS.md`). L5 `PARENT_CHILD_FAMILIES` must not be reused
as an L6 letter corpus.

**Reason:** Architecture-scoped interface exercise is useful after the proximal exact-U
gate, but claiming an SO(3) parent or V08 readiness from a seed audit would violate
ADR-013 / ADR-024.

## ADR-049 — Natural mechanism leaves may differ from a selected pointing level set

<!-- R3A_NATURAL_LEAF_FAMILY_2026_08_17 -->

**Decision:** Rejection of the current fixed-axis `UUUR` as an `h(d)=c` source-fiber
match does not reject every `UXXX` child. R3A may construct a source-derived child by
fixing one exact coordinate of the virtual spherical closure, then continue the
resulting frozen-geometry one-DOF mechanism along its natural branch. The first
positive control is `S_v-U_phys-R-U_phys -> U_v-U_phys-R-U_phys` (`SURU -> UURU`)
using a rotated Z-Y-Z closure chart. The earlier `h=c` family remains a direct
source-chain stitching control and is not a natural-child acceptance constraint.

**Required evidence:** Every accepted natural leaf must pass source-parent embedding,
child/source pose agreement, fixed family-coordinate error, component scope,
re-seeding consistency, family transversality, duplicate/crossing semantics, chart
overlap, and independent task-image reconstruction. Geometry is immutable over one
leaf continuation; continuously rederived axes are not one four-bar experiment.
Only `EXACT_GLOBAL` and `EXACT_ON_COMPONENT` leaves enter accepted reconstruction.

**Reason:** A mechanically valid child may generate a legitimate source-parent curve
that is different from an arbitrarily chosen pointing latitude. Allowing the exact
child branch removes an unnecessary task-slice equivalence requirement, but it
replaces that easy indexing with stronger family-completeness and compatibility
obligations.

**Consequence:** R3A initially claims at most a controlled, declared-resolution set
cover. Terms such as `foliation`, `fiber bundle`, or `exact factorization` remain
reserved until uniqueness, chart transitions, complete parameter intervals, and
component correspondence are established. Individual chart-specific crank or winding
behavior is not a workspace predicate until the family reconstruction is validated.

## ADR-050 — R3A acceptance requires evaluative family gates and an independent direct reference

<!-- R3A_HARDENING_EVIDENCE_GATES_2026_08_17 -->

**Decision:** The merged R3A positive-control software is retained, but returned
`UURU` components are not accepted for parent reconstruction until family-level
re-seeding, child-tangent transversality, chart compatibility, parameter-interval
accounting, and independent set comparison are evaluated rather than represented by
placeholder or proxy fields. Leaf component status, family admissibility, and
reconstruction disposition are separate decisions.

The executable campaign must enforce:

```text
manifest -> fixture -> truth -> source-control -> leaves -> compare -> render
```

with matching config hash, mode, probe scope, and upstream artifact hashes. Missing
inputs cannot produce a completed comparison. Python process-randomized `hash()` is
not an acceptable geometry identifier; canonical SHA-256 is required.

The analytical oracle and decomposition-free target-direction IK remain independent
columns. Oracle labels do not overwrite numerical statuses. Strict feasible or
infeasible numerical `UNRESOLVED` cells block a qualified point result. Both positive
and negative probes must reconstruct their feasible pointing subsets; an empty set
does not pass merely because it refuses full `S^2` coverage.

**Reason:** PR #17 established the correct controlled architecture and branch kernel,
but several family audits were non-evaluative, comparison authority centered the
oracle rather than the direct source result, negative controls could pass with zero
reconstructed directions, and stage/readout scaffolds could look complete without
their prerequisites. Those are evidence-semantic defects, not a reason to abandon
the natural-leaf hypothesis.

**Consequence:** R3A-H proceeds before R3B or L6. Current status remains
`parent_incomplete`; no accepted L5 reconstruction, foliation, exact factorization,
or workspace rule is issued until the hardening closeout passes. The numerical
virtual-crank atlas remains downstream of reconstruction provenance.

## ADR-051 — R3A acceptance metrics distinguish not-applicable from unevaluable evidence

<!-- R3A_H12_2026_08_23 recorded frozen full closeout; not a general 5R theorem -->

**Status:** RECORDED (H12 frozen full-mode closeout; not a reconstruction acceptance and not a general 5R theorem)

**Decision:** A missing numerical value is not sufficient to determine pass/fail. R3A comparison metrics carry explicit `VALUE`, `NOT_APPLICABLE`, or `UNEVALUABLE` state. Zero-denominator metrics such as false-positive fraction on an all-covered reference are `NOT_APPLICABLE`; missing refinement is `UNEVALUABLE`. Full-campaign acceptance requires a computed refinement comparison, leaf-scoped family admissibility, declared chart responsibility, resolved required parameter intervals, and content-addressed artifacts.

**Reason:** Treating every `None` as failure makes valid complete coverage impossible, while treating every `None` as pass fabricates evidence. Explicit applicability preserves conservative gates without making the intended theorem untestable.

**Consequence:** H11 package scope, hashes, producer provenance, and chart/interval authority remain valid. H12 grid-local strict Hausdorff and boundary exclusion withdrew the H11E `DIRECT_REFERENCE_BLOCKED` interpretation as comparison-metric dependent. The producer `9505a87` five-probe `--mode full` package is `package_kind=full_closeout` with `semantic_revalidation=true`, `campaign_blocker=STITCHING_CONTROL_BLOCKED`, and `accepted_reconstruction=false`. All five probes have `direct_complete=true` with zero fine/coarse Hausdorff and zero refinement. Source `h=c` reconstruction fails with unresolved `c` intervals; the natural column is not interpreted. L5 remains `parent_incomplete`. R3B and L6 remain held. This is not a complete parent, a foliation, or a general 5R factorization.

## ADR-052 — Build the first L5 mechanism atlas as a source-derived round trip

<!-- R3C_L5_BEHAVIOR_ATLAS_ROUND_TRIP_2026_08_23 -->

**Status:** ACTIVE (A0 infrastructure only; not a reconstruction or workspace claim)

**Decision:** The first spatial mechanism atlas is built in three directions, in
order: (1) manipulator → mechanism to discover exact child families and the
source-derived support of each family; (2) direct mechanism parameterization to
fill, refine, and stress-test those supported regions; and (3) atlas → manipulator
to test whether atlas-backed child behavior preserves a parent reconstruction that
already agrees with independent source-chain pointing truth. Family identity is
structural and role-aware, never nearest-family matching. Out-of-distribution atlas
queries remain unresolved and route to the exact child evaluator.

R3C begins with an E0 extraction record containing source provenance and full frozen
mechanism geometry before any canonical descriptor vector is chosen. The R3A
`SURU -> UURU` positive control seeds this infrastructure but is not promoted to a
general 5R factorization or universal child family.

**Reason:** A bottom-up atlas built over arbitrary U/R four-bars can spend most of its
compute on mechanism regions that no legitimate 5R reduction produces, while a
manipulator-only corpus may undersample behavior boundaries and cannot establish a
reliable surrogate. The round trip uses the parent to define relevance and the
direct mechanism space to provide coverage.

**Falsification rule:** If exact child behavior is trustworthy but exact-child
stitching fails against held-out direct 5R pointing truth, the decomposition /
family-completeness / stitching hypothesis is incomplete and scaling the atlas is
blocked. If exact-child stitching passes but atlas-backed stitching fails, the
decomposition survives and the atlas/descriptor/sampling layer is rejected or
reworked.

**Consequence:** The aligned-roll L6 numerical program remains downstream of the R3C
parent-level falsification gate. Thin L6 interface scaffolding may remain in the
repository. Broad arbitrary spatial-four-bar rule discovery remains later work.
A0 records provenance and frozen geometry only; it does not issue descriptors,
behavior labels, or workspace certificates.

## ADR-053 — E0 UURU geometry is payload-reconstructible and H12 component identity remains unresolved

<!-- R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER_2026_08_23 -->

**Status:** ACTIVE IMPLEMENTATION CONTRACT; no new L5 reconstruction claim

**Decision:** R3C-A1 exports the existing frozen R3A `SURU -> UURU` natural leaves
downstream of the numerical campaign. The complete E0 UURU geometry consists of the
source serial chain, an independently allocated child serial chain, spherical closure
chart, fixed `lambda`, fixed task point, and child coordinate contract. Campaign,
probe, leaf, and artifact identifiers remain provenance and are excluded from the
geometry hash. A payload-only reconstructor must reproduce the canonical geometry hash
and the defining closure residuals, Jacobian, and FK at stored leaf samples before an
E0 record is emitted.

The existing R3A leaf `geometry_hash` is retained as a legacy chart/`lambda`
construction check and is not redefined. E0 `geometry_sha256` is the full frozen
mechanism-geometry authority.

The H12 natural artifacts do not contain an independently established source-parent
component identifier. A1 therefore records `UNRESOLVED_SOURCE_COMPONENT`. Such records
may preserve leaf-local `accepted_for_reconstruction` / `EXACT_*` fields as provenance
but are not `workspace_evidence_eligible`.

**Reason:** A1 needs reconstructible mechanism specimens for the future atlas without
mutating the frozen R3A experiment or fabricating component correspondence. Separating
geometry identity from source provenance also prevents the same mechanism geometry
from receiving different hashes merely because it arose from a different probe or
artifact path.

**Consequence:** A1 may succeed while the H12 campaign remains
`STITCHING_CONTROL_BLOCKED` and L5 remains `parent_incomplete`. A1 proves data
portability of the child mechanism definition only; it does not classify behavior,
validate stitching, choose canonical atlas descriptors, or authorize L6.

## ADR-054 — A2 separates exact parent patterns from actually instantiated child families

<!-- R3C_A2_5R_PARENT_CAMPAIGN_2026_08_23 -->

**Status:** ACTIVE DIAGNOSTIC CAMPAIGN; no workspace promotion

**Decision:** The first 5R parent campaign inventories exact source structure before
mechanism parameterization. A2 uses exact consecutive `RR -> U_phys` detection and
non-overlapping pair combinations to identify U-based four-compound-joint parent
patterns. A registered mapping such as `SUUR -> UUUR` is recorded as
`REGISTERED_PARENT_PATTERN_ONLY` unless a reconstructible source-derived E0 child of
that family exists. `EXACT_CHILD_EXPORTED` is reserved for actual E0 mechanism
specimens that passed the A1 geometry round trip. Near architectures are retained as
exact-aggregation negative controls and are never nearest-matched into a family.

The frozen bank is the R3A SURU positive control, `exact_two_u_5r`, `generic_5r`,
`near_two_u_5r`, and two A2-local near-SURU controls that break the proximal or
distal physical U pair separately. A2 does not modify the historical V06 corpus.

A2's initial detector is explicitly limited to `RR -> U_phys`. Registered families
whose parent patterns require `S_phys` or another unimplemented aggregation
(`USRR`, `URSR`, `URRS`) are reported `OUT_OF_DETECTOR_SCOPE`, not absent.

**Reason:** Counting a parent letter pattern as an observed child would recreate the
same evidence error that earlier audits rejected: matching mobility and letters do
not prove a source-derived closed mechanism. Conversely, forcing every registered
family to appear would turn the parent campaign into synthetic label balancing rather
than an empirical support study.

**Consequence:** A3 receives only families with actual reconstructible E0 specimens.
Exact registered parent patterns without children enter a construction backlog. It is
acceptable for the current campaign to close with only UURU in the A3 queue. Such a
result is an architecture/support statement, not a claim that UURU is universal.
The H12 `STITCHING_CONTROL_BLOCKED` closeout and L5 `parent_incomplete` status are
unchanged.

## ADR-055 — H13 locked invariants preserve the H12 recorded closeout

<!-- R3A_H13_LOCKED_INVARIANTS_2026_08_23 -->

**Status:** RECORDED LOCK (§1; H13A and H13B implemented; H13C–H13F unimplemented; not a new scientific closeout)

**Decision:** Until a later strict full-closeout package replaces them, the compact
hub at `results/l5_reconstruction/r3a/` and its raw-bundle digest remain the recorded
R3A closeout. The frozen `configs/l5_positive_control_v1.json` keeps the historical
H12 source path (`source_control` has no `policy_version`). H13, when implemented, is
opt-in via a separate pilot config and `policy_version=h13_component_closure_v1`; that
pilot cannot issue a full-campaign disposition. `accepted_reconstruction` stays false;
L5 stays `parent_incomplete`. Direct-column metrics and natural-leaf
parameters/tolerances are not retuned while source control is blocked.
`RETURNED_SET_FOUND` is declared-budget evidence; `COMPONENT_COMPLETE` stays reserved;
a finite `h=c` family is not a foliation. R3B, L6, and the virtual-crank atlas remain
held.

**Reason:** H12 localized the first trustworthy column boundary to source `h=c`
stitching. Mixing a new H13 evidence contract into the frozen H12 config, hub, or
historical source path would retune the recorded closeout before the source column is
domain-complete, component-aware, and resolution-stable.

**Consequence:** This ADR records invariants only. It does not replace the compact hub,
interpret the natural UURU column, or authorize R3B/L6. H13A implements opt-in
dispatch and the analytical `c` domain under ADR-056. H13B implements projected-seed
discovery under ADR-057. Neither retunes H12.

## ADR-056 — H13A source path is opt-in and the c domain is the analytical rho_m interval

<!-- R3A_H13A_ANALYTICAL_C_DOMAIN_2026_08_23 -->

**Status:** IMPLEMENTED (H13A only; not a scientific closeout)

**Decision:** Preserve the frozen H12 source-control implementation for configs without
`source_control.policy_version`. Enable H13A only through
`policy_version=h13_component_closure_v1` on a separate config that cannot issue a
full-campaign disposition. The required `c` interval is the regional-shell oracle
evaluated at declared probe `rho_m`, not discovery extrema and not `||p*||`. Slice
count is `max(configured source_c_value_count, resolution-derived count)` so adjacent
`arccos(c)` spacing stays within a declared fraction of the confirmation-cell
diameter. Analytical endpoints are `CRITICAL_OR_BOUNDARY` and are not required to
return a regular one-dimensional curve. Seed discovery remains the H12 first-three
law until H13B (ADR-057).

**Reason:** H12 blocked the source column in part because the required `c` domain was
inferred from a finite discovery bank and because the slice count was not tied to
the declared sphere resolution. Those two authority defects can be repaired without
retuning the recorded H12 closeout.

**Consequence:** H13A does not replace the compact hub, interpret the natural UURU
column, or claim component completeness. Seed discovery on the H13 path is H13B
(ADR-057). H13C–H13F remain unimplemented. L5 remains `parent_incomplete` and the
campaign blocker remains `STITCHING_CONTROL_BLOCKED`.

## ADR-057 — H13B discovers projected source-Q clusters with explicit caps

<!-- R3A_H13B_PROJECTED_SEEDS_2026_08_23 -->

**Status:** IMPLEMENTED (H13B only; not a scientific closeout)

**Decision:** On the H13 source path, replace the H12 silent first-three seed rule with
wrapped-Q clustering, explicit candidate and projected-cluster caps, seed-count
vocabulary, and quality-ordered symmetric dedup. Pre-cluster the discovery bank, order
candidates by in-window then `|h(q)-c|`, project onto `p=p*` and `h=c`, cluster
successful projections, and continue one H12 `continue_source_fiber` per selected
cluster. If either cap truncates, the required bin is `BUDGET_EXHAUSTED` even when
attempted traces return. Historical `expected_seed_count` on that path is the attempted
projected-cluster count and is labeled
`attempted_projected_seed_clusters_not_expected_components`. Dedup is a duplicate only
when `max(d_ab, d_ba) <= tol` and `abs(d_ab - d_ba) <= tol`; returned traces win over
non-returned duplicates; asymmetric Q subsets stay distinct. H12 `build_source_control`
keeps `seeds[:3]`.

**Reason:** Defect B of H13 is that a finite first-three nearby sample is not a
component census. Caps, seed-count semantics, and symmetric subset-preserving dedup
make truncation and duplicate authority inspectable without claiming an analytical
component count or inventing H13C termination vocabulary.

**Consequence:** H13B does not replace the compact hub, add H13C termination honesty,
H13D curve rasterization, or an H13E pilot JSON. Painting remains sparse H12
pointings. L5 remains `parent_incomplete` and the campaign blocker remains
`STITCHING_CONTROL_BLOCKED`.

