> **Historical program document.** This file preserves planning lineage that led to the current decomposition ladder. It is not the active roadmap. See `docs/ROADMAP.md` and `docs/CURRENT_STATUS.md`.
>
> **Status label:** see `docs/archive/README.md`.


# Kinematic Decomposition Program — V05 to V09

**Status:** Active proposed replacement for the spatial-four-bar-first V05–V09 program
**Project:** Characterization of Manipulator Workspaces
**Software branch basis:** `4_bar_exploration` after V04C
**Date:** 2026-08-07

---

## 1. Program Decision

The V05–V09 sequence should be restructured.

The previous program began with a broad classification problem for standalone one-degree-of-freedom spatial four-bar families and delayed the decisive robot-to-mechanism equivalence test until V09:

```text
all-family winding atlas
  -> descriptor mining
  -> candidate Grashof-like rules
  -> fast crank evaluator
  -> 6R dexterity reconstruction
```

That ordering develops a downstream mechanism predicate before establishing that the mechanism being classified is the exact reduction required by the manipulator workspace problem.

The revised program begins with the fixed-position virtual mechanism and walks upward through the minimum-DOF ladder:

```text
planar 3R solved reference
  -> spatial 4R fixed-position mechanism, M = 1
  -> spatial 5R fixed-position parent, M = 2
  -> spatial 6R fixed-position parent, M = 3
  -> aligned-roll 6R quotient, M = 2 + 1
  -> validated decomposition, predicate, and reconstruction
```

The central question is now:

> For which open-chain architectures can the exact fixed-position virtual mechanism be reduced or factored into lower-dimensional mechanism families whose intrinsic properties determine the required orientation coverage?

Grashof-like rule discovery remains a possible downstream result. It is no longer the premise of the spatial program.

---

## 2. Why V05 Starts with a Spatial 4R Serial Manipulator

The planar 3R case is the trusted reference construction:

```text
planar 3R serial chain
  -> fix (x, y)
  -> exact closed planar 4R
  -> M = 1
  -> orientation image in SO(2)
  -> exact terminal-link rotatability
```

The next clean rung is a **spatial 4R serial manipulator**, not a standalone spatial four-bar linkage.

At a regular fixed Cartesian point,

\[
4R+S_v,
\qquad
M=4-3=1.
\]

This case is the correct bridge because:

1. the complete fixed-position fiber is already one-dimensional;
2. no arbitrary pointing slice is needed to obtain a one-dimensional mechanism;
3. its orientation image is a curve in \(SO(3)\);
4. continuation can trace the full source mechanism directly;
5. any proposed spatial-four-bar reduction can be compared against the complete source fiber;
6. a failed reduction can be identified as a decomposition failure rather than mistaken for failure of the fixed-position framework.

For architectures with an exact pair of consecutive intersecting orthogonal revolute axes, those two physical \(R\) joints may be regrouped as a universal joint \(U\) without changing mobility. The source closure may then take an architecture-derived role-aware form such as

\[
S_v U_{\mathrm{phys}} R R,
\]

with the virtual closure retained as the semantic origin. Depending on which physical pair is aggregated, the ordered source families are

```text
S_v-U_phys-R-R
S_v-R-U_phys-R
S_v-R-R-U_phys
```

These are direct, unsliced one-degree-of-freedom families. Their joint-kind strings are cyclically isomorphic to some existing `USRR`-class solver topologies, but their semantic roles are different: the `S_v` joint is the tool-position closure and `U_phys` is a physical axis aggregate. Solver reuse is permitted; reuse of `tool_a`/`tool_b` interpretation is not.

If no exact axis aggregation exists, the source remains the five-joint loop \(4R+S_v\). That is still a valid V05 result; decomposition is not forced.

---

## 3. Definitions the Software Must Lock

The software should distinguish the following objects and operations explicitly.

### 3.1 Source open chain

The physical serial manipulator before any task constraint or reduction:

```text
OpenChainModel
```

It preserves joint order, screw axes, link transforms, limits, tool frame, and architecture metadata.

### 3.2 Fixed-position fiber

For the position map \(p:Q\rightarrow\mathbb R^d\),

\[
\mathcal F_{p^*}=p^{-1}(p^*)
=
\{q\in Q:p(q)=p^*\}.
\]

The full fiber may contain multiple connected components, singular points, and isolated configurations. A continuation trace follows one **fiber component**, not automatically the entire fiber.

At a regular configuration,

\[
\dim\mathcal F_{p^*}
=
 n-\operatorname{rank}J_p(q).
\]

### 3.3 Virtual closure

The exact closed-mechanism representation of the fixed-position constraint:

- planar: add a virtual revolute joint at \(p^*\);
- spatial: add a virtual spherical joint \(S_v\) at \(p^*\).

The virtual closure is exact at the task-constraint level. It is not yet a four-bar decomposition.

### 3.4 Orientation image

\[
\mathcal O(p^*)
=
\{R(q):q\in\mathcal F_{p^*}\}
\subseteq SO(3).
\]

This is the orientation set the source mechanism actually generates.

### 3.5 Pointing image

For a selected tool axis \(\hat z_T\),

\[
\mathcal P(p^*)
=
\{R(q)\hat z_T:q\in\mathcal F_{p^*}\}
\subseteq S^2.
\]

The pointing image is a projection of the orientation image. It is not automatically the correct task target for every manipulator.

### 3.6 Coverage target

The set required by the task:

- planar full orientation: \(SO(2)\);
- specified one-parameter spatial orientation task: \(Y_1\subset SO(3)\);
- arbitrary tool pointing: \(S^2\);
- full spatial orientation: \(SO(3)\).

Dimension matching is necessary, not sufficient, for coverage.

### 3.7 Kinematic decomposition

Use **kinematic decomposition** as the umbrella term for a sequence of justified operations applied after the exact virtual closure is known.

| Operation | Meaning | Typical mobility effect | Required evidence |
|---|---|---:|---|
| **Axis aggregation** | Regroup consecutive intersecting/coincident physical \(R\) axes as exact \(U\) or \(S\) coordinates. | none | identical forward kinematics, joint subspace, and limits after coordinate mapping |
| **Symmetry quotient** | Remove a known group action that changes only a separately handled task coordinate. | subtract group-orbit dimension | orbit invariance, quotient map, reconstruction, range/limit conditions |
| **Task slice** | Add an explicit scalar task constraint to a higher-dimensional parent. | usually minus one at a regular value | recorded level-set function, rank check, provenance, parent-child agreement |
| **Mechanism factorization** | Represent a higher-mobility mechanism through coupled lower-dimensional factors. | distributed among factors | compatibility law, reconstruction map, component correspondence |
| **Predicate application** | Evaluate an intrinsic property on an accepted mechanism. | none | exact or qualified numerical definition of the property |
| **Coverage reconstruction** | Combine factor results into a statement about the source orientation target. | none | explicit necessity/sufficiency and independent source-chain validation |

These operations must not be treated as interchangeable. In particular, an \(M=2\) mechanism is not automatically the Cartesian product of two \(M=1\) mechanisms.

### 3.8 Mechanism predicate

A property evaluated on a validated mechanism or factor, for example:

- assemblability;
- branch/circuit structure;
- complete designated-coordinate winding;
- angular coverage;
- complete link rotation;
- singularity margin;
- a Grashof or Grashof-like condition;
- an exact continuation result;
- a conservative numerical atlas lookup.

### 3.9 Decomposition certificate

Every proposed reduction should produce one of:

```text
EXACT_GLOBAL
EXACT_ON_COMPONENT
LOCAL_ONLY
APPROXIMATE
REJECTED
UNRESOLVED
```

The certificate records:

```text
source_chain_id
fixed_position_problem_id
source_component_id
source_mobility
joint_kind_sequence
joint_role_sequence
cyclic_origin_role
designated_task_joint_role
reduction_operations
reduced_topology
coordinate_map
inverse_or_reconstruction_map
task_map
rank_and_nullity_checks
closure_residuals
tangent_subspace_error
trajectory_reconstruction_error
component_correspondence
joint_limit_correspondence
status
failure_or_scope_reason
```

### 3.10 Naming and role guardrails

A joint-kind string is not a complete mechanism identity. Every compound joint must also carry a semantic role. At minimum distinguish:

```text
S_v       virtual spherical closure at the tool point
U_v       virtual universal closure on a task-derived pointing level set
U_phys    universal joint formed by exact aggregation of physical R axes
S_phys    spherical joint formed by exact aggregation of physical R axes
R_phys    ordinary physical revolute joint
```

For example, `S_v-U_phys-R-R` and cyclic `U_phys-R-R-S_v` share a solver topology, but they are not semantically equivalent to `U_v-R-R-S_phys`. Designated winding and task coordinates must be selected by joint role, never by string position alone.

Keep these phrases distinct:

- **spatial 4R serial manipulator** — an open chain with four revolute joints;
- **spatial four-bar linkage** — a closed one-DOF linkage with four joint locations;
- **fixed-position fiber** — the complete position level set;
- **fiber component** — one connected component of that level set;
- **pointing level-set fiber** — a one-dimensional slice inside a higher-dimensional pointing parent;
- **dexterous workspace** — full \(SO(2)\) or \(SO(3)\) coverage at each included point;
- **pointing-complete workspace** — full \(S^2\) pointing coverage when roll is intentionally ignored.

---

## 4. Revised Program Ladder

| Sprint | Source mechanism | Generic mobility after fixing position | Primary image/target | Main scientific gate |
|---|---|---:|---|---|
| **V05** | spatial 4R + \(S_v\) | 1 | orientation curve in \(SO(3)\) | Can the complete source fiber be built and can any architecture-derived one-DOF reduction be certified? |
| **V06** | spatial 5R + \(S_v\) | 2 | orientation surface / pointing image in \(S^2\) | Can the full two-dimensional parent be represented before introducing one-dimensional slices or factors? |
| **V07** | spatial 6R + \(S_v\) | 3 | orientation image in \(SO(3)\) | Can the project establish an independent decomposition-free numerical reference? |
| **V08** | aligned-roll 6R and its 5R quotient | \(2+1\) | pointing \(S^2\) plus roll \(S^1\) | Is the terminal-roll quotient exact over the tested domain, and are task-derived one-dimensional fibers legitimate? |
| **V09** | certified reductions from V05–V08 | architecture-dependent | reconstructed target coverage | Do mechanism predicates and compatibility laws reproduce independent source-chain truth? |

---

# Sprint V05 — Spatial 4R Fixed-Position Fiber and One-DOF Decomposition Baseline

## Research question

Can the fixed-position fiber of a synthetic spatial 4R serial manipulator be constructed, continued, visualized, and—where architecture permits—mapped exactly to a one-degree-of-freedom closed mechanism?

## Source problem

\[
4R+S_v,
\qquad
M=1,
\qquad
C_{p^*}=R(\mathcal F_{p^*})\subset SO(3).
\]

## Work packages

### V05A — source-chain corpus

Define a small exact corpus before broad sampling:

1. a generic 4R architecture with no intentional axis aggregation;
2. an architecture with one exact consecutive orthogonal-intersecting \(RR\rightarrow U\) pair;
3. a near-aligned perturbation that must **not** be treated as an exact \(U\);
4. one singular or rank-deficient counterexample;
5. one architecture expected to yield multiple fiber components if practical.

Use explicit screw axes and home transforms. Do not begin with URDF import.

### V05B — fixed-position source mechanism

**Status (2026-08-08):** MVP implemented on the minimal V05A spatial-4R corpus.

For a regular seed \(q_0\):

1. set \(p^*=p(q_0)\);
2. solve \(p(q)-p^*=0\);
3. verify \(\operatorname{rank}J_p=3\) and nullity one;
4. continue each discovered component using pseudo-arclength methods;
5. preserve closure residual, tangent, singular values, return status, and component identity;
6. distinguish a returned cycle from an open or budget-limited branch.

Software: `src/grashof_workspace/spatial_experiments/{open_chain,fixed_position,fixed_position_continuation,v05_corpus,v05b}.py`.
Readout: [`results/kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html`](../../../results/kinematic_decomposition/v05b/sprint_v05b_fixed_position_fiber.html).
Note: ± rays from one seed do not certify full multi-component completeness. V05C–E are implemented on this corpus. Explorer `spatial4bar_explorer/v05a` is not this work package.

### V05C — orientation-curve truth

**Status (2026-08-08):** MVP implemented on V05B fixed-position fibers.

Render and export:

- the physical open chain and all joint axes;
- the virtual spherical closure at \(p^*\);
- the continued source component;
- the tool-axis path on \(S^2\);
- a complementary orientation representation such as quaternions, rotation vectors, or a local chart;
- orientation multiplicity along the curve where observable;
- singular and near-singular locations.

Do not reduce the orientation curve to a single angle unless the architecture proves a one-parameter subgroup or another valid scalar coordinate.

Software: `src/grashof_workspace/spatial_experiments/{orientation_image,v05c}.py`.
Readout: [`results/kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html`](../../../results/kinematic_decomposition/v05c/sprint_v05c_orientation_curve.html).
These exports are orientation-curve / pointing-curve truth, not coverage certificates. V05D aggregation certificates and V05E near-aligned rejection are implemented.

### V05D — exact axis aggregation and candidate spatial four-bar

**Status:** MVP complete for proximal exact `RR→U` on `exact_u_pair_4r`: axis aggregation is `EXACT_GLOBAL`, while the current independent budget-limited closed-loop match is `LOCAL_ONLY`; `generic_4r` rejects exact aggregation.

For architectures with an exact \(RR\rightarrow U\) pair:

1. build the role-aware aggregated `S_v-U_phys-R-R`, `S_v-R-U_phys-R`, or `S_v-R-R-U_phys` representation;
2. prove identical source-chain forward kinematics under the coordinate map;
3. compare closure residuals and tangent spaces;
4. continue source and reduced mechanisms from matched seeds;
5. compare full returned branches or the explicitly scoped component;
6. issue a decomposition certificate.

The existing generic `U/S/R` closure and continuation kernel may be reused, but V05 introduces role-aware source families `S_v-U_phys-R-R`, `S_v-R-U_phys-R`, and `S_v-R-R-U_phys`. Existing `tool_a`/`tool_b` winding semantics must not be reused because the universal joint is physical and the virtual tool closure is spherical.

Software: `src/grashof_workspace/spatial_experiments/{axis_aggregation,decomposition_certificate,v05d}.py`.
Readout: [`results/kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html`](../../../results/kinematic_decomposition/v05d/sprint_v05d_axis_aggregation.html).
Complete bidirectional source/child component correspondence, non-proximal pair embeddings,
and multi-component `EXACT_GLOBAL` remain unverified. V05E near-aligned rejection is
implemented.

### V05E — rejection tests

**Status:** MVP complete for `near_aligned_u_pair_4r` (`REJECTED` as exact aggregation) with declared geometric tolerances and a diagnostic `false_u_surrogate` task-error report.

The near-aligned perturbation must be rejected as exact aggregation. The software should show the geometric tolerance and the task error caused by treating it as a universal joint.

Software: `src/grashof_workspace/spatial_experiments/{axis_aggregation,decomposition_certificate,v05_corpus,v05e}.py`.
Readout: [`results/kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html`](../../../results/kinematic_decomposition/v05e/sprint_v05e_near_aligned_rejection.html).
The forced exact-U surrogate is diagnostic-only and is **not** an `APPROXIMATE` DecompositionCertificate.

## Deliverables

- `OpenChainModel` for synthetic spatial chains;
- `FixedPositionProblem`;
- `VirtualClosureResult`;
- `FixedPositionFiberResult` with component-level data;
- orientation-curve exports;
- exact-axis-aggregation detector;
- `DecompositionCertificate` schema;
- source-versus-reduced overlay plots/GIFs;
- `sprint_v05_spatial_4r_fixed_position.html`.

## Acceptance gate

V05 passes when:

1. at least one regular spatial 4R fixed-position component is constructed and independently verified;
2. rank/nullity and component status are explicit;
3. its orientation curve is exported without assuming full orientation coverage;
4. at least one exact axis aggregation passes or one proposed aggregation is cleanly rejected;
5. no standalone spatial-four-bar result is promoted to manipulator evidence without a certificate.

A certified four-bar reduction is desirable but not required for V05 to be scientifically successful.

---

# Sprint V06 — Spatial 5R Fixed-Position Parent and Pointing Image

## Research question

What is the complete two-dimensional fixed-position mechanism of a spatial 5R chain, what pointing image does it generate on \(S^2\), and which lower-dimensional structures are architecture- or task-derived rather than arbitrary slices?

## Source problem

\[
5R+S_v,
\qquad
M=2,
\qquad
\mathcal O(p^*)\subset SO(3),
\qquad
\mathcal P(p^*)\subseteq S^2.
\]

## Work packages

Implementation slices (does not replace V06A–E): V06A0 generic 2D manifold engine → V06A1 one local 5R chart → V06A2 parent atlas → V06C source images → V06B compound parent → V06D1/D2 fibers and children → V06E reconstruction. Details: [`V06_SPATIAL_5R_PARENT_AND_POINTING_EXECUTION.md`](../sprints/V06_SPATIAL_5R_PARENT_AND_POINTING_EXECUTION.md).

### V06A — two-dimensional parent first

**V06A0 (implementation prerequisite):** a generic two-dimensional implicit-manifold engine, validated on the analytical unit sphere, with no 5R parent or certificate claim.

1. construct synthetic 5R architectures using the same source-chain representation as V05;
2. verify rank three and source nullity two at regular seeds;
3. represent the parent with local charts, triangulated samples, continuation patches, or another explicit two-dimensional method;
4. track chart overlap, singularity, components, and configuration multiplicity;
5. avoid defining the parent only through a collection of arbitrarily chosen one-dimensional traces.

### V06B — architecture-derived compound-joint parents

Where exact physical axis structure permits, test reductions such as:

```text
5R + S_v
  -> S_v-U_phys-U_phys-R
```

or

```text
5R + S_v
  -> S_v-S_phys-R-R
```

up to cyclic ordering.

These are two-degree-of-freedom parent mechanisms. They are not yet one-degree-of-freedom four-bars and should not yet receive crank/rocker labels.

### V06C — pointing projection

Map the parent to \(S^2\):

- covered cells or charts;
- boundary curves;
- multiplicity;
- source component identity;
- singularity structure;
- unresolved regions;
- representative configurations for selected pointing directions.

Use a qualified numerical label such as:

```text
COVERED_AT_DECLARED_RESOLUTION
PARTIAL_COVERAGE
UNRESOLVED
```

rather than claiming an exact global theorem from finite sampling.

### V06D — controlled one-dimensional level sets

Only after the parent is visible, define

\[
\mathcal G_{p^*,c}
=
\{q\in\mathcal F_{p^*}:h(R(q)\hat z_T)=c\}.
\]

Every such level set must record:

- the scalar function \(h\);
- the value \(c\);
- why this slice is task- or architecture-relevant;
- the regularity/rank check;
- its parent component;
- whether it is closed, open, singular, or unresolved.

### V06E — factorization audit

Test, but do not assume, whether the two-dimensional parent admits:

- a foliation by one-dimensional mechanism fibers;
- a sequential/fibered decomposition;
- two coupled one-degree-of-freedom factors;
- no useful lower-dimensional factorization.

Any factorization must supply a compatibility and reconstruction law.

## Deliverables

- `FixedPositionParentResult` for \(M=2\);
- `OrientationImageResult` and `PointingImageResult`;
- chart/component/multiplicity exports;
- exact compound-joint parent certificates;
- explicit pointing-level-set provenance;
- factorization audit and certificates;
- `sprint_v06_spatial_5r_pointing_parent.html`.

## Acceptance gate

V06 passes when the complete two-dimensional parent and its pointing projection are represented independently of any proposed four-bar factorization, and every one-dimensional child is labeled as task-derived, architecture-derived, diagnostic, or arbitrary.

Complete \(S^2\) coverage is a result to evaluate, not an assumption.

---

V06A direct source-parent construction is not blocked by the L4 local certificate. Any
claim that a V06 one-dimensional child or reconstructed pointing image inherits a reduced
mechanism equivalence remains blocked until its own source-derived certificate passes.

# Sprint V07 — Generic Spatial 6R Fixed-Position Orientation Reference

## Research question

Can a generic synthetic spatial 6R fixed-position mechanism and its orientation image in \(SO(3)\) be represented well enough to serve as an independent numerical truth model for later decompositions?

## Source problem

\[
6R+S_v,
\qquad
M=3,
\qquad
\mathcal O(p^*)\subseteq SO(3).
\]

## Work packages

1. construct at least one generic synthetic 6R architecture without relying on aligned terminal roll;
2. verify regular three-dimensional fixed-position mobility;
3. define a decomposition-free numerical orientation reference using multiple charts, rotation cells, or an equivalent representation;
4. recover source-chain configurations for accepted orientation samples;
5. preserve multiplicity, source components, singularities, and unresolved cells;
6. separate local rank sufficiency from global orientation coverage;
7. test coordinate/chart invariance of the reported result;
8. freeze this reference before V08/V09 decomposition comparisons.

## Deliverables

- `FixedPositionParentResult` for \(M=3\);
- chart-aware `OrientationImageResult` on \(SO(3)\);
- independent configuration-recovery checks;
- multiplicity/component/singularity reports;
- declared-resolution coverage and uncertainty metadata;
- `sprint_v07_generic_6r_orientation_reference.html`.

## Acceptance gate

V07 passes when the project has an independent, decomposition-free numerical reference for orientation capability at selected Cartesian points.

The claim at this stage is numerical orientation coverage at a declared resolution, not a closed-form global theorem.

---

# Sprint V08 — Aligned Terminal-Roll Quotient and Task-Derived Four-Bar Fibers

## Research question

Under what exact geometric and joint-range conditions can terminal roll be separated from a 6R fixed-position mechanism, and when do legitimate one-dimensional pointing fibers reduce to the existing `UUUR`/`USRR` spatial four-bar families?

## Source and quotient problems

\[
6R+S_v,
\qquad M=3,
\]

and, when terminal-roll conditions hold,

\[
(6R+S_v)/R_6
\longrightarrow
5R+S_v,
\qquad M=2.
\]

## Required terminal-roll conditions

The sprint must verify that:

1. the sixth joint axis is coincident with the selected tool-roll axis;
2. the tool origin lies on that axis;
3. changing \(q_6\) leaves tool position unchanged;
4. changing \(q_6\) leaves tool pointing unchanged;
5. the joint range provides the required roll coverage;
6. the quotient and reconstruction maps preserve components over the tested domain;
7. limits, singularities, or coupling do not invalidate the separation.

## Work packages

### V08A — quotient certification

Compare the full 6R source mechanism with the 5R pointing parent:

- matched configurations;
- quotient tangent spaces;
- pointing images;
- component correspondence;
- roll reconstruction;
- joint-limit coverage.

### V08B — pointing-plus-roll reconstruction

Compare

\[
\text{pointing image} + \text{terminal roll}
\]

against the direct V07 \(SO(3)\) reference.

Full spatial dexterity requires both:

\[
\mathcal P(p^*)=S^2
\]

and complete roll availability over every required pointing direction.

### V08C — explicit pointing slices

Use the V06 parent representation and `SPATIAL_POINTING_SLICE_CONTRACT.md` to define legitimate one-dimensional pointing level sets. The slice must be a recorded task constraint, not an arbitrary virtual-`U` orientation parameter.

### V08D — child spatial-four-bar reductions

Only after parent-child equivalence passes may the virtual spherical closure be represented on a one-dimensional slice by \(U_v\), then decomposed as

\[
U_v(\alpha,\beta)=R_a(\alpha)R_b(\beta).
\]

Architecture-derived physical axis aggregations may then produce role-aware one-degree-of-freedom children. With the virtual closure kept first, the two parent classes become permutations of:

```text
U_v-U_phys-U_phys-R
U_v-S_phys-R-R
```

Their joint-kind strings are the familiar families

```text
UUUR, UURU, URUU,
USRR, URSR, URRS.
```

but every child row must retain the virtual/physical role assignment, cyclic origin, designated task coordinates, parent, slice, coordinate map, and certificate.

## Deliverables

- terminal-roll eligibility checker;
- quotient/reconstruction certificates;
- 5R-parent versus 6R-quotient overlays;
- pointing-plus-roll versus direct-\(SO(3)\) comparison;
- task-derived slice registry;
- parent-to-four-bar decomposition certificates;
- `sprint_v08_aligned_roll_quotient.html`.

## Acceptance gate

V08 passes when the aligned-roll reduction is demonstrated as exact or explicitly component-limited, and at least one one-dimensional four-bar child is traced back to a legitimate source parent and task slice.

A DOF count or visually similar animation is not sufficient.

---

# Sprint V09 — Validated Mechanism Predicates and Coverage Reconstruction

## Research question

Can certified lower-dimensional mechanisms, their intrinsic predicates, and explicit compatibility laws reconstruct the independent orientation-capability truth of selected 4R/5R/6R source architectures?

## Work packages

### V09A — certified inputs only

Select only reductions carrying accepted V05, V06, or V08 certificates. Standalone mechanism-explorer geometries remain useful diagnostics but cannot enter robot-workspace evidence.

### V09B — mechanism predicates

Reuse the existing spatial-four-bar kernel for:

- closure;
- continuation;
- returned-cycle detection;
- winding;
- angular coverage;
- singularity diagnostics;
- branch/circuit status.

Define exactly which predicate is hypothesized to correspond to which source coverage requirement.

### V09C — recombination law

State the parent reconstruction as one of:

```text
exact product
fiber bundle / sequential structure
conditional factorization
component-limited reconstruction
no valid recombination
```

Do not combine binary crank labels with an unstated logical rule.

### V09D — independent comparison

Compare the reconstructed result against:

- the V05 spatial 4R orientation curve;
- the V06 5R pointing image;
- the V07 direct 6R \(SO(3)\) reference;
- the V08 pointing-plus-roll reconstruction.

Report:

- false positives;
- false negatives;
- unresolved cases;
- boundary/singularity failures;
- component mismatches;
- runtime and fallback rate;
- representative counterexamples.

### V09E — downstream decision

Produce a go/no-go decision for broad family atlas and Grashof-like rule discovery.

## Deliverables

- end-to-end provenance graph;
- `MechanismPredicateResult`;
- `CoverageCertificate`;
- selected-architecture reconstruction;
- independent comparison report;
- success/rejection/counterexample gallery;
- `sprint_v09_decomposition_coverage_validation.html`.

## Acceptance gate

A downstream atlas program may begin only when:

1. the source open-chain problem is explicit;
2. the virtual closure is verified;
3. the manipulator-to-mechanism decomposition is accepted;
4. the mechanism predicate is defined exactly;
5. the recombination rule is explicit;
6. reconstructed coverage agrees with independent source-chain truth within documented tolerances;
7. unresolved and out-of-domain cases remain explicit.

Failure at V09 does not invalidate the fixed-position framework. It localizes the failure to decomposition, predicate sufficiency, compatibility, or reconstruction.

---

## 5. Fate of the Existing Spatial-Four-Bar Program

The V00–V04C spatial-four-bar code and data remain valuable as a **mechanism laboratory**:

- physical compound-joint geometry;
- closure and continuation;
- returned-cycle detection;
- winding and angular coverage;
- tool-coordinate diagnostics;
- visualizations, GIFs, and HTML infrastructure.

The previous V05–V09 sequence is deferred and remapped after the new V09 gate:

| Previous plan | Revised downstream role |
|---|---|
| V05 all-family winding atlas | **V10** validated-family atlas using only certified source provenance |
| V06 descriptor trend mining | **V11** descriptor discovery |
| V07 candidate spatial Grashof rules | **V12** candidate-rule testing and analytical follow-up |
| V08 fast crank evaluator | **V13** conservative rule/atlas evaluator |
| V09 broad 6R reconstruction | **V14** broad workspace and architecture validation |

Standalone samples keep the provenance label

```text
mechanism_explorer_only
```

until connected to a certified source-chain decomposition.

---

## 6. Cross-Sprint Software Architecture

```text
OpenChainModel
  -> FixedPositionProblem
  -> VirtualClosureResult
  -> FixedPositionFiberResult / FixedPositionParentResult
  -> OrientationImageResult / PointingImageResult
  -> DecompositionCertificate
  -> MechanismPredicateResult
  -> CoverageCertificate
  -> WorkspaceClassification
```

### Minimum provenance record

```text
source_chain_id
architecture_signature
joint_kind_sequence
joint_role_sequence
cyclic_origin_role
designated_task_joint_role
joint_geometry
joint_limits
tool_frame_definition
selected_tool_axis
cartesian_point
seed_configuration
position_rank
source_mobility
source_component_id
coverage_target
virtual_closure_definition
reduction_operations
reduced_topology
coordinate_map
reconstruction_map
decomposition_status
equivalence_residuals
mechanism_predicate
predicate_confidence
recombination_rule
reference_oracle
coverage_result
unresolved_reason
```

No result should jump directly from a standalone four-bar family label to a robot-workspace claim.

---

## 7. Evidence Levels

Use this hierarchy in every readout:

1. **source-chain numerical result** — fixed-position fiber/parent and orientation image;
2. **virtual-closure result** — exact representation of the position constraint;
3. **decomposition result** — certified source-to-reduced equivalence status;
4. **mechanism result** — winding, rotation, branch, or another intrinsic predicate;
5. **empirical trend** — descriptor association in a certified corpus;
6. **candidate rule** — falsifiable predictive hypothesis;
7. **analytical result** — derived theorem or inequality;
8. **workspace result** — agreement with independent orientation truth.

Do not promote one level to another by wording alone.

---

## 8. Common Visualization Contract

Every sprint should expose the same sequence:

1. physical open chain and joint axes;
2. selected tool point \(p^*\);
3. virtual spherical closure;
4. complete fixed-position component or parent;
5. orientation or pointing image;
6. proposed axis aggregation, quotient, slice, or factorization;
7. candidate reduced mechanism;
8. source-versus-reduced overlay;
9. mechanism predicate;
10. reconstructed versus independent coverage.

The physical manipulator remains visible as a transparent reference through every reduction step.

---

## 9. Program Thesis

The revised program is not:

> Grashof worked for planar 3R, so search for spatial Grashof conditions for 6R robots.

It is:

> Fixing tool position produces an exact virtual closed mechanism whose mobility equals the residual configuration freedom available for orientation generation. The project walks from spatial 4R to 5R to 6R, establishes the source orientation image at each rung, and then tests whether architecture-dependent kinematic decomposition exposes lower-dimensional mechanisms whose intrinsic properties determine global coverage.

That ordering makes spatial-four-bar classification a justified analytical or numerical tool rather than the premise of the workspace theory.

---

## V05 audit correction status

<!-- V05_AUDIT_CORRECTION_2026_08_08 -->

The initial V05A–E implementation is superseded by `V05_AUDIT_CORRECTIONS.md`.

Current disposition:

```text
V05A source corpus                 CORRECTED: off-axis active cases + terminal-roll control
V05B source continuation           CORRECTED MVP: augmented pseudo-arclength + FD Jacobian check
V05C orientation image             CORRECTED MVP: explicit curve classification
V05D exact axis aggregation        EXACT_GLOBAL where geometry permits
V05D closed-mechanism equivalence  LOCAL_ONLY for proximal exact_u_pair_4r (traced arc)
V05E rejection/boundary            CORRECTED MVP: tolerance-relative suite
V05 overall gate                   LOCAL_ONLY (exact_u_pair_4r); other architectures UNRESOLVED
```

V06A direct source-parent construction is not blocked by the L4 local certificate. Decomposition-dependent children remain gated. Multi-component `EXACT_GLOBAL` and non-proximal embeddings remain unverified.
