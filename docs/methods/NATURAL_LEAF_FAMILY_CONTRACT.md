# Natural Mechanism Leaf Family Contract

**Status:** Proposed canonical method for the R3A L5 program
**Project:** Characterization of Manipulator Workspaces by Kinematic Decomposition
**Scope:** One-DOF closed-mechanism curves used to reconstruct a higher-dimensional fixed-position task image

---

## 1. Decision

A source-derived one-DOF child mechanism is not required to reproduce an arbitrarily selected pointing level set such as

\[
h(d)=n^T d=c.
\]

Once a child mechanism is instantiated, it may follow its own exact closed-mechanism branch, provided that every accepted child configuration lifts to the original fixed-position source parent and the resulting family is validated as a cover of the declared parent task image.

This contract distinguishes:

```text
task-sliced source fiber
mechanism-coordinate leaf
seed-derived diagnostic curve
accepted natural leaf family
```

They are not interchangeable.

---

## 2. Source parent

For a 5R source manipulator with position map \(p(q)\), fix a Cartesian point \(p^*\):

\[
\mathcal P_{p^*}
=
\{q\in Q:p(q)=p^*\}.
\]

At a regular spatial 5R configuration,

\[
\dim\mathcal P_{p^*}=5-3=2.
\]

Let the pointing map be

\[
d:\mathcal P_{p^*}\rightarrow S^2.
\]

The parent pointing image is

\[
\mathcal D(p^*)
=
\{d(q):q\in\mathcal P_{p^*}\}.
\]

The reconstruction target is \(\mathcal D(p^*)\), not the coordinates used to parameterize it.

---

## 3. Three curve types

### 3.1 Task-sliced source fiber

A declared task scalar produces

\[
\mathcal F_c
=
\{q\in\mathcal P_{p^*}:h(q)=c\}.
\]

This is a valid source fiber whenever the level set is regular. It need not correspond to a known four-bar.

Provenance:

```text
task_level_set_control
```

### 3.2 Mechanism-coordinate leaf

Choose a coordinate \(\lambda\) of the exact virtual closure and fix it:

\[
\mathcal C_\lambda
=
\{q\in\mathcal P_{p^*}:\lambda(q)=\lambda_0\}.
\]

When fixing \(\lambda\) converts the source closure into an exact one-DOF closed mechanism, \(\mathcal C_\lambda\) is a mechanism-coordinate leaf candidate.

Provenance:

```text
virtual_orientation_coordinate
```

### 3.3 Seed-derived diagnostic curve

A child may be constructed from local tangent geometry at a seed without a proven global coordinate or exact slice.

Provenance:

```text
seed_derived_diagnostic
```

Such a curve may be mechanically valid and source-embedded, but it is not promoted to a family leaf until re-seeding and family-consistency gates pass.

---

## 4. Meaning of natural motion

“Let the four-bar move as it pleases” means:

1. derive a fixed child geometry from the source problem and a declared family parameter;
2. instantiate an independent closed mechanism;
3. freeze all axes, centers, link transforms, and fixed coordinate values;
4. continue the exact one-DOF branch by pseudo-arclength;
5. accept or reject the resulting branch from source-embedding and family evidence.

It does **not** mean:

- use any standalone four-bar from the explorer;
- rederive the child axes at every continuation step;
- change the fixed mechanism dimensions while continuing;
- ignore source position or orientation residuals;
- combine incompatible source components because their pointing curves overlap;
- call a collection of curves a foliation without additional evidence.

A continuously changing instantaneous reduction may be useful differential geometry, but it is not one four-bar behavior experiment.

---

## 5. Initial exact L5 construction

The first R3A positive control uses a source parent

```text
S_v — U_phys — R_phys — U_phys
```

or `SURU`.

Represent the virtual spherical orientation in a chart

\[
R_v(\alpha,\beta,\lambda)
=
C R_z(\alpha)R_y(\beta)R_z(\lambda)C^T R_{\mathrm{ref}}.
\]

Fixing \(\lambda=\lambda_i\) yields

\[
R_v(\alpha,\beta;\lambda_i)
=
C R_z(\alpha)R_y(\beta)
K(\lambda_i),
\]

where

\[
K(\lambda_i)=R_z(\lambda_i)C^T R_{\mathrm{ref}}
\]

is fixed for the leaf.

The resulting child is

```text
U_v — U_phys — R_phys — U_phys
```

or `UURU`.

The two virtual-U coordinates \(\alpha(s),\beta(s)\) are coupled outputs of one continued one-DOF branch. Neither coordinate is an independent drive unless a separate prescribed-coordinate experiment is declared.

---

## 6. Family map

Let \(s\) parameterize a child component and \(\lambda\) select a child:

\[
\Phi:\Lambda\times S\rightarrow\mathcal P_{p^*},
\qquad
\Phi(\lambda,s)=q_\lambda(s).
\]

The pointing reconstruction is

\[
\widehat{\mathcal D}(p^*)
=
\bigcup_{\lambda\in\Lambda}
\{d(q_\lambda(s)):s\in S_\lambda\}.
\]

This union is a numerical reconstruction target. Equality

\[
\widehat{\mathcal D}(p^*)=\mathcal D(p^*)
\]

must be demonstrated, not assumed.

---

## 7. Required evidence gates

### Gate N1 — Source derivation

Every leaf records:

```text
source_chain_id
fixed_position_problem_id
source_component_id
family_parameter_name
family_parameter_value
child_family
joint_kind_sequence
joint_role_sequence
chart_id
full fixed geometry
```

A standalone mechanism with no source derivation remains `mechanism_explorer_only`.

### Gate N2 — Fixed geometry

The mechanism geometry is immutable over branch continuation. The record stores a geometry hash or equivalent immutable identifier.

### Gate N3 — Source embedding

Every accepted child sample must satisfy:

\[
\|p(q)-p^*\|\leq\varepsilon_p,
\]

and the child/source orientation and pointing maps must agree within declared tolerances.

For a coordinate leaf, the fixed family coordinate must also satisfy

\[
|\operatorname{wrap}(\lambda(q)-\lambda_i)|
\leq\varepsilon_\lambda.
\]

### Gate N4 — Component scope

Rank, nullity, return status, singular boundaries, and continuation budget are explicit. An open or budget-limited branch cannot silently become a complete component.

### Gate N5 — Re-seeding consistency

If \(q_1\) lies on a child component, reconstructing the same chart and family parameter from \(q_1\) should reproduce the same component over the claimed scope.

Required metrics:

```text
symmetric wrapped-Q set distance
symmetric pointing-set distance
tangent error
component identity
```

Failure means the construction is seed-dependent. It may form a mechanism web, but it is not yet a leaf family.

### Gate N6 — Transversality

Neighboring leaves must add an independent parent direction. At regular points,

\[
\operatorname{rank}
\begin{bmatrix}
t_s & t_\lambda
\end{bmatrix}=2,
\]

where \(t_s\) is the leaf tangent and \(t_\lambda\) is the cross-leaf direction.

Repeatedly finding the same curve does not reconstruct a parent.

### Gate N7 — Duplicate and crossing semantics

Curves are compared in source configuration space before task space.

- same source point + same tangent: likely duplicate leaf;
- same source point + different tangent: not a foliation at that point;
- different source points + same pointing direction: valid task-space multiplicity;
- incompatible source components must not be merged solely because task images overlap.

### Gate N8 — Chart overlap

A global reconstruction generally requires more than one orientation chart. Overlap regions must establish:

```text
same source configurations
compatible family coordinate transform
same or explicitly different leaf component
consistent task image
```

Individual leaf shapes may depend on chart. The reconstructed parent task image should not.

### Gate N9 — Family completeness

The family records:

```text
covered λ intervals
critical λ values
missing λ intervals
leaf births/deaths/merges
component transitions
unresolved chart regions
```

A finite sampled family may issue only a declared-resolution result.

### Gate N10 — Independent task-image comparison

Compare the accepted leaf union with a decomposition-free source reference using:

- strict covered-cell recall;
- strict uncovered-cell false positives;
- angular Hausdorff distance;
- boundary error;
- multiplicity;
- source-component count;
- refinement stability.

---

## 8. Certificate fields

A natural leaf certificate should contain at least:

```text
leaf_id
source_chain_id
fixed_position_problem_id
source_component_id
construction_kind
chart_id
family_parameter_name
family_parameter_value
child_family
joint_kind_sequence
joint_role_sequence
geometry_hash
construction_status
closed_mechanism_status
component_scope
branch_status
returned
sample_count
max_closure_residual
max_position_residual_m
max_orientation_error_rad
max_pointing_error_rad
max_joint_lift_error_rad
max_family_coordinate_error_rad
reseed_status
transversality_status
chart_overlap_status
accepted_for_reconstruction
failure_or_scope_reason
```

Accepted reconstruction statuses remain:

```text
EXACT_GLOBAL
EXACT_ON_COMPONENT
```

`LOCAL_ONLY`, `APPROXIMATE`, `REJECTED`, and `UNRESOLVED` are retained for diagnostics but do not count toward the accepted-child task-image union.

---

## 9. Set cover versus foliation

R3A distinguishes three levels of result.

### Level A — Embedded mechanism curves

At least one child branch is a valid source-embedded closed-mechanism curve.

### Level B — Certified set cover

A finite accepted family reconstructs the declared parent pointing image at a stated resolution and uncertainty.

### Level C — Foliation / factorization

The family additionally has unique local leaf identity, consistent crossings, complete parameter intervals, chart transitions, and a valid reconstruction map over the claimed parent components.

A Level B workspace classifier may be useful without a Level C global fiber-bundle theorem, but the language must remain “certified cover” or “set reconstruction,” not “exact factorization.”

---

## 10. Role of the `h=c` source control

The earlier pointing level set remains a required control:

\[
h(d)=n^T d=c.
\]

It validates source continuation and curve-union stitching without invoking a child mechanism.

The natural child does not fail merely because \(h(d)\) changes along its branch. It fails only when one of its declared obligations fails, such as:

- source parent membership;
- exact chart-coordinate slice;
- child/source pose agreement;
- component completeness;
- re-seeding consistency;
- family transversality;
- independent coverage comparison.

---

## 11. Coordinate dependence

Different valid spherical charts may produce different natural leaf families. This is expected.

The program must separate:

```text
leaf-level behavior
from
parent task-image invariance
```

A crank/rocker or winding label on one chart-specific child may not be invariant under a different decomposition. No individual behavior is promoted to a workspace predicate until the chart-conditioned family reconstruction is understood.

---

## 12. Computational-value gate

A natural-leaf method is computationally useful only if a one-dimensional family parameter and one-dimensional continuation parameter reconstruct the parent more efficiently than a dense direct parent solve.

The campaign therefore records:

```text
number of direct target solves
number of accepted leaves
continuation steps
wall-clock time
unresolved rate
coverage error
refinement slope
```

If a dense two-dimensional seed grid and heavy deduplication are required, the mechanism interpretation may remain scientifically useful but has not yet earned a computational workspace advantage.

---

## 13. Nonclaims

This contract does not assert:

- that every 5R parent admits a global natural-leaf family;
- that a natural family is unique;
- that a fixed-axis virtual U is always exact;
- that source membership alone proves family completeness;
- that task-space curve overlap proves source compatibility;
- that favorable four-bar winding implies pointing completeness;
- that a numerical set cover is an analytical theorem;
- that R3A generalizes beyond its declared architecture and probe bank.

---

## 14. Canonical summary

\[
\boxed{
\text{natural mechanism leaf}
=
\text{fixed source-derived child geometry}
+
\text{exact one-DOF branch}
+
\text{validated source embedding}
}
\]

and

\[
\boxed{
\text{parent pointing reconstruction}
=
\text{accepted leaf family}
+
\text{transversality/component/chart audits}
+
\text{independent set comparison}.
}
\]
