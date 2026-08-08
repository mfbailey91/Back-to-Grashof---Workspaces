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
