> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# V06 Implementation Plan — Spatial 5R Parent and Pointing Reconstruction

**Status:** subordinate implementation plan (does not replace the V05–V09 scientific program)  
**Scientific rung:** L5  
**Active sprint:** V06  
**Assumed base:** branch `4_bar_exploration` after L4 traced-arc `LOCAL_ONLY` (ADR-034)  
**Scientific source of truth:** [`KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md`](../programs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md)

## Governing documents

Read these before implementation:

- `docs/KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md`
- `docs/DECOMPOSITION_LADDER_L3_L7_PROGRAM.md`
- `docs/SPATIAL_POINTING_SLICE_CONTRACT.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/JACOBIAN_AND_DERIVATIVE_POLICY.md`

This plan supplements those documents. It does not replace their terminology, evidence hierarchy, or claim limits.

---

## 1. Program decision

Start the new scientific implementation at **spatial 5R**.

```text
planar 3R   fixed position -> M = 1 -> exact analytical direct leaf
spatial 4R  fixed position -> M = 1 -> numerical direct leaf
spatial 5R  fixed position -> M = 2 -> first true parent requiring a fiber family
```

Planar 3R remains the analytical regression oracle. Spatial 4R remains the direct-leaf and certificate regression case.

Neither smaller case tests the central V06 hypothesis:

```text
two-dimensional source parent
  -> explicit one-dimensional task fibers
  -> independently solved closed-mechanism children
  -> reconstruction of the parent pointing image
```

Do not launch another 3R sprint or a broad 4R-family campaign before V06. Use a simple analytical two-dimensional surface only to validate the new manifold software.

---

## 2. Implementation sequence

Preserve the official V06A–V06E labels, but execute them in this order:

| Implementation slice | Existing work package | Purpose |
|---|---|---|
| **V06A0** | implementation prerequisite | Generic two-dimensional implicit-manifold engine |
| **V06A1** | V06A | One local generic-5R fixed-position chart |
| **V06A2** | V06A | Multi-chart parent atlas and component discovery |
| **V06C** | V06C | Freeze direct source orientation and pointing truth |
| **V06B** | V06B | Structured compound-joint parent and equivalence audit |
| **V06D1** | V06D | Task-derived one-dimensional source fibers |
| **V06D2** | V06D plus pointing-slice contract | Candidate `U_v` child and equivalence audit |
| **V06E** | V06E | Fiber reconstruction, child reconstruction, and closeout |

V06C is executed before V06B so that the reduced parent is compared against an already frozen decomposition-free source reference.

---

## 3. Source problem

For a spatial 5R source chain,

\[
q\in\mathbb T^5,
\qquad
p^*=p(q_0).
\]

The fixed-position source parent is

\[
\mathcal P_{p^*}
=
\{q:p(q)=p^*\}.
\]

At a regular configuration,

\[
J_p(q)\in\mathbb R^{3\times5},
\qquad
\operatorname{rank}J_p=3,
\qquad
\dim\ker J_p=2.
\]

The parent engine must compute a complete orthonormal basis

\[
N_p(q)
=
\operatorname{basis}\ker J_p(q)
\in\mathbb R^{5\times2}.
\]

For tool pointing

\[
d(q)=R(q)\hat z_T\in S^2,
\]

compute the differential restricted to the parent:

\[
J_{d|\mathcal P}
=
J_dN_p
\in\mathbb R^{3\times2}.
\]

Every accepted parent sample must record:

```text
q
p residual
R
d
rank(Jp)
nullity(Jp)
singular values of Jp
tangent basis Np
rank(Jd Np)
singular values of Jd Np
chart and component identity
corrector condition
regularity and boundary status
```

The important audit is:

```text
rank(Jp) = 3
nullity(Jp) = 2
rank(Jd Np) = 2 for a locally two-dimensional pointing image
```

A two-dimensional configuration parent does not automatically produce a two-dimensional pointing image.

---

## 4. Claim boundaries

The implementation must enforce the following:

1. A regular seed is not a parent atlas.
2. A collection of one-dimensional traces is not a two-dimensional parent.
3. A two-dimensional parent is not automatically all of `S^2`.
4. A two-dimensional subset of `SO(3)` is not automatically a pure pointing surface.
5. Exact axis aggregation is separate from independent closed-parent equivalence.
6. `S_v -> U_v` requires an explicit task-derived level set.
7. Matching mobility and joint letters are not an equivalence certificate.
8. A local virtual-U tangent chart is not a global child certificate.
9. Source reconstruction uses only fibers connected to real parent components.
10. Child reconstruction uses only independently accepted children.
11. Finite sampling supports only declared-resolution coverage claims.
12. V06 may legitimately conclude that no useful lower-dimensional factorization exists.

For the MVP, treat revolute coordinates as periodic coordinates on `T^5`. Record joint limits as `not_modeled`; do not claim limited-joint workspace coverage.

---

## 5. Proposed modules

```text
src/grashof_workspace/spatial_experiments/
  implicit_manifold.py
  parent_atlas.py
  parent_images.py
  v06_corpus.py
  compound_parent.py
  parent_level_sets.py
  parent_reconstruction.py
  v06.py

src/grashof_workspace/decomposition_ladder/
  models.py
  spatial_l5.py
  readout.py
```

Suggested test modules:

```text
tests/test_implicit_manifold.py
tests/test_spatial_v06_parent_local.py
tests/test_spatial_v06_parent_atlas.py
tests/test_spatial_v06_parent_images.py
tests/test_spatial_v06_compound_parent.py
tests/test_spatial_v06_level_sets.py
tests/test_spatial_v06_child_equivalence.py
tests/test_spatial_v06_reconstruction.py
tests/test_spatial_v06_readout.py
```

`v06.py` should orchestrate tested modules and generate artifacts. It should not contain all numerical logic.

---

# PR 1 — V06A0: generic two-dimensional manifold engine

## Objective

Validate the new two-dimensional numerical machinery independently of 5R kinematics.

## Required abstraction

Add a typed protocol or equivalent adapter:

```python
class ImplicitManifoldProblem(Protocol):
    problem_id: str
    ambient_dimension: int
    constraint_dimension: int
    intrinsic_dimension: int
    coordinate_names: tuple[str, ...]
    periodic_coordinates: tuple[bool, ...]

    def residual(self, x: Array) -> Array: ...
    def jacobian(self, x: Array) -> Array: ...
    def evaluate_task(self, x: Array) -> TaskEvaluation: ...
```

Initial implementations:

```text
AnalyticalSphereProblem
FixedPositionParentProblem
ClosedCompoundParentProblem
```

Only `AnalyticalSphereProblem` is implemented in PR 1.

## Wrapped coordinate difference

For periodic coordinates use

\[
\Delta(q_a,q_b)
=
\operatorname{atan2}
\left(
\sin(q_a-q_b),
\cos(q_a-q_b)
\right).
\]

Use the wrapped difference for chart gauges, overlap tests, clustering, component matching, and Hausdorff metrics.

## Tangent basis

Compute an orthonormal nullspace basis. Align neighboring SVD bases through orthogonal Procrustes so arbitrary sign and in-plane basis changes do not look like physical discontinuities.

Record tangent-subspace change using a metric such as

\[
e_N
=
\|N_aN_a^T-N_bN_b^T\|_F.
\]

## Local chart corrector

At chart center `x_c`, with tangent basis `N_c`, and local coordinate `u`:

\[
x_{\mathrm{pred}}
=
x_c+N_cu.
\]

Correct using

\[
G(x)
=
\begin{bmatrix}
F(x)\\
N_c^T\Delta(x,x_{\mathrm{pred}})
\end{bmatrix}
=0.
\]

The Newton matrix is

\[
DG(x)
=
\begin{bmatrix}
J_F(x)\\
N_c^T
\end{bmatrix}.
\]

Store predictor, corrected state, constraint residual, gauge residual, correction norm, iterations, condition number, rank/nullity, and rejection reason.

## Analytical fixture

Use

\[
F(x)=x^Tx-1=0,
\qquad
x\in\mathbb R^3.
\]

Its solution is the unit sphere.

Build local hexagonal charts, triangulate them, grow neighboring charts, and verify that the sphere is represented as one closed component at declared resolution.

## Acceptance

- tangent bases are orthonormal and lie in the Jacobian nullspace;
- corrected vertices satisfy the analytical constraint;
- chart overlaps are deterministic;
- duplicate charts are rejected;
- the sphere has one connected closed component;
- approximate surface area approaches \(4\pi\) under refinement;
- strict JSON contains no `NaN` or `Infinity`.

## Claim ceiling

Software validation only. No 5R status changes.

## Cursor instruction

Implement only the generic two-dimensional implicit-manifold engine and analytical sphere fixture. Do not construct a 5R parent, pointing image, compound-joint parent, level set, or four-bar child in this PR.

---

# PR 2 — V06A1: one local generic-5R parent chart

## Objective

Construct one genuine local patch of

\[
\mathcal P_{p^*}
=
\{q:p(q)=p^*\}
\]

for the existing `generic_5r` source.

## Implementation

Add `FixedPositionParentProblem`:

```text
ambient dimension     5
constraint dimension  3
intrinsic dimension   2
residual              p(q)-p*
Jacobian              Jp(q)
task output           R(q), d(q)
```

Reuse the existing regular `generic_5r` seed.

Build one local center-plus-hexagonal-ring chart. At every vertex compute `Np`, `Jd Np`, pointing rank, residual, and condition.

Render:

- source-arm configurations;
- local `u` coordinates;
- mapped pointing directions on `S^2`;
- position residual;
- parent rank/nullity;
- pointing rank.

Emit a real `FixedPositionParentResult` with status:

```text
LOCAL_PATCH
```

Update the L5 ladder adapter only enough to replace `SEED_ONLY` with `LOCAL_PATCH`. All fibers, children, and reconstruction remain unresolved.

## Acceptance

- every accepted sample satisfies the fixed-position tolerance;
- every tangent basis has shape `5x2`;
- `rank(Jd Np)` is reported separately from `rank(Jp)`;
- no fiber records are emitted;
- no child is promoted;
- a local patch is not labeled as a complete parent component.

## Cursor instruction

Apply the manifold engine to `generic_5r` at one regular seed and stop at one local chart.

---

# PR 3 — V06A2: parent atlas and component discovery

## Objective

Grow local charts into an explicit two-dimensional source-parent atlas.

## Frontier growth

- treat chart boundary arcs as frontiers;
- spawn neighboring charts at uncovered frontier vertices;
- align neighboring tangent bases;
- adapt chart radius using corrector convergence, correction size, tangent change, condition number, and `sigma_min(Jp)`;
- shrink and retry failed frontiers;
- deduplicate centers with wrapped joint distance and tangent-subspace agreement;
- build chart and mesh adjacency graphs;
- retain singular, open, and budget-limited frontiers explicitly.

## Component discovery

A one-seed atlas cannot establish all components.

Use a deterministic Sobol or equivalent bank in `[-pi,pi)^5`. Project each sample toward the fixed-position manifold with a damped minimum-normal update:

\[
\Delta q
=
-J_p^T
\left(
J_pJ_p^T+\lambda I
\right)^{-1}
(p(q)-p^*).
\]

Cluster projected seeds by wrapped joint distance. Attach them to existing atlas components or begin new components.

Repeat with a larger frozen confirmation bank.

Record:

```text
component discovery status
bank ID and size
projected seed count
component count
unattached seed count
chart resolution
open frontier count
singular boundary count
budget-limited frontier count
completion reason
```

Suggested discovery statuses:

```text
ONE_SEED_ONLY
MULTISTART_STABLE_AT_DECLARED_RESOLUTION
NEW_COMPONENT_FOUND_ON_CONFIRMATION
UNRESOLVED_COMPONENT_DISCOVERY
```

## Parent representation statuses

```text
SEED_ONLY
LOCAL_PATCH
ATLAS_OPEN_FRONTIER
CLOSED_COMPONENT_AT_DECLARED_RESOLUTION
SINGULAR_BOUNDARY
BUDGET_LIMITED
MULTICOMPONENT_UNRESOLVED
REJECTED
```

These are representation statuses, not decomposition certificates.

## Acceptance

V06A passes when the source parent has an explicit multi-chart representation independent of every child mechanism, with components, overlaps, boundaries, singularities, resolution, and unresolved frontiers represented honestly.

## Cursor instruction

Extend the local chart into a parent atlas and add deterministic component discovery. Do not implement structured parents, `U_v`, or source fibers.

---

# PR 4 — V06C: direct source orientation and pointing truth

## Objective

Freeze the decomposition-free source task image before testing any reduction.

## Orientation result

Retain for every parent vertex:

```text
R
adjacency-stabilized quaternion
rotation vector or local orientation chart
source q
parent component
parent chart
orientation edge geodesic length
```

Do not describe the two-dimensional orientation image as all of `SO(3)`.

Use a V06-specific surface result or a dimension-aware common result. Do not silently reinterpret the V05 orientation-curve type.

## Pointing result

Map every parent vertex and face through

\[
d(q)=R(q)\hat z_T.
\]

Retain:

```text
spherical vertices
mapped spherical triangles
source-face provenance
rank(Jd Np)
critical and near-critical sets
boundary curves
source components
configuration multiplicity
unresolved cells
```

## Declared-resolution sphere grid

Create a deterministic icosphere or equivalent spherical grid.

Store:

```text
grid construction
subdivision level
maximum cell diameter
covered cells
uncovered cells
ambiguous boundary cells
unresolved cells
component multiplicity per cell
representative source configurations
```

Allowed coverage labels:

```text
COVERED_AT_DECLARED_RESOLUTION
PARTIAL_COVERAGE
UNRESOLVED
```

## Acceptance

The direct orientation and pointing images must exist without any child, aggregation, or decomposition input.

## Cursor instruction

Project the V06A source atlas directly into `SO(3)` and `S^2`. Freeze the result as the source oracle before implementing V06B.

---

# PR 5 — V06B: structured compound-joint parent

## Objective

Test one intentionally structured parent:

```text
5R + S_v
  -> S_v-U_phys-U_phys-R
```

## Corpus

Add:

### `generic_5r`

Existing nonstructured source.

### `exact_two_u_5r`

Design:

```text
J1/J2 -> exact intersecting orthogonal U_phys
J3/J4 -> exact intersecting orthogonal U_phys
J5    -> remaining generic R
```

Require:

- distinct U centers;
- off-axis tool origin;
- nontrivial pointing motion;
- regular fixed-position nullity two;
- preferably local pointing rank two;
- no overlapping selected aggregates.

### `near_two_u_5r`

Perturb one pair beyond the declared exact-intersection or orthogonality tolerance. It must be rejected as exact aggregation.

## Multi-aggregation record

Add a record containing:

```text
selected non-overlapping pair indices
individual pair certificates
coordinate map
inverse map
aggregate roles
FK identity residuals
tangent-coordinate residuals
joint-limit correspondence
axis-aggregation status
```

Exact physical regrouping may receive `EXACT_GLOBAL`. This does not certify the independent closed parent.

## Independent reduced parent

Instantiate:

```text
semantic family: S_v-U_phys-U_phys-R
scalar coordinates: 3 + 2 + 2 + 1 = 8
closure equations: 6
mobility: 2
```

Do not use the one-dimensional `continue_branch` solver. Wrap the closure as `ClosedCompoundParentProblem` and solve it with the same atlas engine used for the source.

Do not coerce the parent into the `UUUR` child identity.

## Source/reduced comparison

Compare symmetrically:

```text
closure residual
source position residual
full orientation error
pointing error
wrapped source-coordinate error
source-to-reduced distance
reduced-to-source distance
tangent-subspace error at multiple samples
component and boundary correspondence
joint-limit correspondence
```

Certificate policy:

```text
EXACT_ON_COMPONENT  complete scoped source/reduced components
LOCAL_ONLY          matched local patch or incomplete traced subset
REJECTED            failed equivalence or near control
UNRESOLVED          insufficient component or boundary evidence
```

## Acceptance

The exact source and near control must be distinguished correctly. A clean local, rejected, or unresolved closed-parent result is acceptable; false promotion is not.

## Cursor instruction

Implement one `SUUR` parent path and one near control. Do not add `U_v`, level-set fibers, or one-DOF predicates yet.

---

# PR 6 — V06D1: task-derived source level sets

## Objective

Construct one-dimensional source fibers from the represented two-dimensional parent.

## Scalar field

Use

\[
h(d)=n^Td,
\qquad
\|n\|=1.
\]

At each parent vertex compute

\[
\nabla_{\mathcal P}h
=
N_p^TJ_d^Tn.
\]

A regular level-set point requires

\[
\|\nabla_{\mathcal P}h\|>\varepsilon_h.
\]

Record approximate critical points and critical values.

## Slice selection

Begin with:

- one regular middle value;
- two additional interior values on opposite sides.

Do not call this a complete foliation.

## Mesh contour extraction

For every parent triangle:

- detect `h=c` edge crossings;
- interpolate using wrapped joint coordinates;
- correct the seed to the exact constraints;
- build a contour-segment graph;
- identify every connected contour component;
- label closed, open, boundary-touching, critical-touching, or unresolved contours.

## Direct source continuation

Solve

\[
F_c(q)
=
\begin{bmatrix}
p(q)-p^*\\
n^Td(q)-c
\end{bmatrix}
=0.
\]

At a regular point,

\[
J_{F_c}
=
\begin{bmatrix}
J_p\\
n^TJ_d
\end{bmatrix}
\in\mathbb R^{4\times5},
\qquad
\operatorname{rank}J_{F_c}=4,
\qquad
\dim\ker J_{F_c}=1.
\]

Use pseudo-arclength continuation from every distinct contour component seed.

Every fiber must record:

```text
parent and parent-component IDs
n and c
task-derived provenance
rank/nullity
criticality context
source component
branch status
pointing and orientation curves
mesh-contour comparison
unresolved reason
```

## Acceptance

At least one regular slice value must recover all discovered source-fiber components and agree with the independently represented parent contour.

## Cursor instruction

Implement source level sets only. Do not instantiate `U_v` or `UUUR` in this PR.

---

# PR 7 — V06D2: task-derived virtual U and one child

## Objective

Test one source-derived child:

```text
SUUR parent
  -> explicit h(d)=c level set
  -> UUUR child
```

## Local virtual-U derivation

At a seed, an infinitesimal angular velocity `omega` changes the scalar by

\[
\dot h
=
n^T(\omega\times d)
=
(d\times n)^T\omega.
\]

Allowed virtual rotations satisfy

\[
(d\times n)^T\omega=0.
\]

Choose two orthonormal axes `a,b` spanning that plane and place them at `p*`.

This produces a **local candidate** `U_v` chart. It does not prove global validity.

Record separately:

```text
parent slice status
virtual-U chart status
child closure status
tangent status
branch status
component correspondence
overall certificate
```

## Independent child

Instantiate role sequence:

```text
U_v, U_phys, U_phys, R_phys
```

Use branch arclength `s` as the canonical drive. Report `alpha(s)` and `beta(s)` as coupled outputs.

## Comparison

Compare both directions using:

```text
closure error
position error
h-c error
full orientation error
pointing error
wrapped source-coordinate error
tangent error at multiple samples
source-to-child distance
child-to-source distance
component return/boundary correspondence
```

The child status must be derived from the issued certificate. Never initialize it as accepted.

## Acceptance

One honest child comparison record is sufficient. The result may be exact, component-limited, local, rejected, or unresolved.

Only `EXACT_GLOBAL` and `EXACT_ON_COMPONENT` children may enter child reconstruction.

## Cursor instruction

Derive and test one `U_v` child only. Do not launch the six-family sweep.

---

# PR 8 — V06E: reconstruction and closeout

## Objective

Separate two questions:

1. Do direct source fibers reconstruct the source parent pointing image?
2. Do accepted closed-mechanism children reconstruct it?

## Stage 1: source-fiber reconstruction

\[
\widehat{\mathcal P}_{\text{source}}
=
\bigcup_{c\in C}
d(\mathcal F_c).
\]

This tests the scalar field, slice density, critical values, and component discovery without involving child compression.

## Stage 2: accepted-child reconstruction

\[
\widehat{\mathcal P}_{\text{children}}
=
\bigcup_{c\in C_{\text{accepted}}}
d(\mathcal C_c).
\]

Exclude:

```text
LOCAL_ONLY
APPROXIMATE unless separately authorized
REJECTED
UNRESOLVED
mechanism_explorer_only
```

## Metrics

Report:

```text
direct source covered cells
source-fiber reconstructed cells
accepted-child reconstructed cells
missed-cell fraction
false-positive fraction
ambiguous-boundary fraction
symmetric angular Hausdorff error
pointing multiplicity discrepancy
source-component discrepancy
critical-c intervals
unresolved-c intervals
accepted/rejected/unresolved fiber counts
```

Use the frozen V06C sphere grid.

## Adaptive refinement

Add `c` values where:

- source cells are missed;
- fiber topology changes;
- critical values are bracketed;
- multiplicity changes;
- reconstruction error is high;
- child certificate status changes.

Record the complete refinement history.

## Factorization result

Use the existing vocabulary:

```text
exact product
fiber bundle / sequential structure
conditional factorization
component-limited reconstruction
no valid recombination
unresolved
```

## V06 acceptance

V06 passes when:

1. the two-dimensional source parent exists independently of children;
2. direct orientation and pointing images are frozen;
3. every one-dimensional fiber has explicit task provenance;
4. compound-joint parents are certified or rejected honestly;
5. source-fiber reconstruction is compared against direct source truth;
6. child reconstruction uses only accepted children;
7. factorization status is explicit;
8. coverage is qualified by declared resolution;
9. critical values, unresolved components, boundaries, and missing joint limits remain explicit.

Successful child factorization and complete `S^2` coverage are results, not assumptions.

---

## Result directory

```text
results/kinematic_decomposition/v06/
  data/
    v06_run_manifest.json
    v06_parent.json
    v06_orientation_image.json
    v06_pointing_image.json
    v06_compound_parent.json
    v06_level_sets.json
    v06_child_equivalence.json
    v06_reconstruction.json
  figures/
    v06_parent_chart_atlas.png
    v06_parent_component_graph.png
    v06_parent_singularity_map.png
    v06_pointing_image.png
    v06_pointing_multiplicity.png
    v06_scalar_field_on_parent.png
    v06_selected_level_sets.png
    v06_source_child_overlay.png
    v06_reconstruction_comparison.png
  animations/
    v06_parent_source_arm.gif
    v06_selected_source_fiber.gif
    v06_selected_child.gif
  sprint_v06_spatial_5r_pointing_parent.html
```

The readout story should be:

```text
5R source
  -> fixed p*
  -> 2D source parent
  -> direct orientation and pointing images
  -> structured parent test
  -> scalar field h
  -> selected source fibers
  -> candidate child
  -> source-fiber reconstruction
  -> accepted-child reconstruction
  -> V06 factorization decision
```

---

## CI policy

Required on every commit:

- analytical sphere fixture;
- one local 5R chart;
- low-resolution atlas smoke;
- source pointing-image smoke;
- exact/near aggregation detector tests;
- one source level-set smoke;
- strict JSON and HTML artifact smoke;
- Ruff;
- mypy.

Mark larger campaigns as stress tests:

- refined multistart component discovery;
- larger parent atlas;
- multiple slice values;
- complete bidirectional child comparisons;
- refined sphere grid;
- reconstruction convergence.

---

## Definition of done

- [ ] generic two-dimensional manifold engine;
- [ ] explicit 5R `FixedPositionParentResult`;
- [ ] multi-chart components and boundaries;
- [ ] deterministic component-discovery evidence;
- [ ] direct orientation and pointing images;
- [ ] `rank(Jd Np)` and multiplicity;
- [ ] one structured `SUUR` parent;
- [ ] one near-aggregation control;
- [ ] source-derived `h(d)=c` fibers;
- [ ] one independently instantiated candidate child;
- [ ] source-fiber reconstruction;
- [ ] accepted-child reconstruction or explicit absence of accepted children;
- [ ] factorization classification;
- [ ] declared-resolution pointing result;
- [ ] cumulative JSON, figures, animations, and HTML;
- [ ] ladder, dashboard, and ADR updates;
- [ ] explicit go/hold decision for V07.

V06 may close successfully with:

```text
no valid recombination
```

provided the source parent and direct pointing image are correct and the factorization failure is localized honestly.

---

## First Cursor prompt

> Implement **V06A0 only**. Read the governing V06, L5, pointing-slice, Gate K2, and derivative-policy documents first. Add a dimension-independent two-dimensional implicit-manifold atlas engine with wrapped-coordinate support, tangent-basis alignment, augmented local-chart correction, chart overlap records, immutable typed outputs, strict JSON, and deterministic tests. Validate it on the analytical unit-sphere fixture. Do not construct the 5R parent, pointing image, compound-joint parent, task fibers, or four-bar children in this PR. Preserve process status separately from decomposition-certificate status.