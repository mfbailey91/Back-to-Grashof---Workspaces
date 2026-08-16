# Mathematical Notes

## 1. Planar 3R chain

For link lengths \(l_1,l_2,l_3>0\), let the end-effector position be \(p\), with

\[
\rho=\|p\|.
\]

For a desired terminal orientation \(\phi\), the wrist point is

\[
w(\phi)=p-l_3
\begin{bmatrix}
\cos\phi\\
\sin\phi
\end{bmatrix}.
\]

The first two links can reach the wrist when

\[
|l_1-l_2|\le \|w(\phi)\|\le l_1+l_2.
\]

## 2. Quotient by base rotation

With unrestricted planar revolute joints, workspace membership is invariant under global rotation about the base. Therefore the position test depends only on \(\rho\), not the polar angle of \(p\).

This symmetry reduction is an explicit assumption of the first milestone. It must not be generalized to arbitrary spatial joints without proving the corresponding task-space symmetry.

## 3. Four-bar reduction

Fixing \(p\) produces a loop with ordered lengths

\[
(d,\ a,\ b,\ c)=(\rho,\ l_3,\ l_2,\ l_1),
\]

where \(d\) is ground and \(a=l_3\) is the link whose complete rotation represents full orientation capability.

As \(a\) rotates, the distance between its free endpoint and the opposite ground pivot spans

\[
[|d-a|,\ d+a].
\]

The remaining two links can close the loop over

\[
[|c-b|,\ c+b].
\]

Therefore the terminal link can rotate completely iff

\[
|d-a|\ge |c-b|,
\qquad
d+a\le c+b.
\]

Substitution gives

\[
|\rho-l_3|\ge |l_1-l_2|,
\qquad
\rho+l_3\le l_1+l_2.
\]

## 4. Dexterous radial components

Let

\[
r_i=|l_1-l_2|,
\qquad
r_o=l_1+l_2-l_3.
\]

The outer constraint requires \(0\le \rho\le r_o\). The inner constraint splits into

\[
\rho\le l_3-r_i
\quad\text{or}\quad
\rho\ge l_3+r_i.
\]

After intersecting these branches with \([0,r_o]\), the dexterous workspace may be:

- empty;
- one disk;
- one annulus;
- a disk and a disconnected annulus;
- a degenerate boundary circle at equality.

The implementation preserves degenerate intervals because they identify change-point geometries that may matter to the analytical classification.

Structured topology reports finite components (`disk`, `annulus`, `disk_and_annulus`, or empty) separately from degenerate components (`origin_point`, `boundary_circle`).

## 5. Four-bar assemblability and classification

For ordered lengths \(L=(d,a,b,c)\), the assembly margin is

\[
m_a=\sum_i L_i-2L_{\max}.
\]

- \(m_a>0\): assemblable with a finite configuration range;
- \(m_a=0\): degenerate collinear assembly;
- \(m_a<0\): non-assemblable.

The Grashof margin remains \(P+Q-S-L\) on the sorted lengths. Exported labels use the precedence

1. `non-assemblable`;
2. `degenerate-coincident-ground-pivots` when \(d=0\);
3. `degenerate-collinear` when \(m_a=0\);
4. `change-point`;
5. `special-grashof-tied-shortest`;
6. conventional `double-crank`, `crank-rocker`, or `double-rocker`.

A separate `grashof_class` field reports `non-assemblable`, `grashof`, `change-point`, or `non-grashof`. Exact terminal-link rotatability is still decided by loop-closure interval containment and never by the textual inversion label alone.

---

## 6. Fixed-position fibers for general manipulators

Let

\[
g(q)=\bigl(p(q),R(q)\bigr),
\qquad q\in Q,
\]

where \(p(q)\) is tool position and \(R(q)\) is tool orientation.

At a selected position \(p^*\), define the fixed-position fiber

\[
\mathcal F_{p^*}
=
\{q\in Q:p(q)=p^*\}
=
p^{-1}(p^*).
\]

The full fiber may contain multiple connected components and singular points. A numerical continuation trace usually represents one connected component

\[
\mathcal C_{p^*,k}\subseteq\mathcal F_{p^*},
\]

not automatically the full fiber.

At a regular configuration,

\[
\dim\mathcal F_{p^*}
=
 n-\operatorname{rank}J_p(q).
\]

For full translational rank:

- planar position constraints: \(\dim\mathcal F_{p^*}=n-2\);
- spatial position constraints: \(\dim\mathcal F_{p^*}=n-3\).

The count is local and generic. Singularities, dependent constraints, special overconstraints, joint limits, and disconnected components affect the global result.

## 7. Exact virtual closure

Fixing position can be represented by closing the tool point back to ground:

- planar: a virtual revolute closure at \(p^*\);
- spatial: a virtual spherical closure \(S_v\) at \(p^*\).

Thus:

\[
\text{planar }nR
\longrightarrow
(nR+R_v),
\qquad M=n-2,
\]

and

\[
\text{spatial }nR
\longrightarrow
(nR+S_v),
\qquad M=n-3.
\]

Examples:

\[
\begin{aligned}
\text{planar }2R &: M=0,\\
\text{planar }3R &: M=1,\\
\text{spatial }4R &: M=1,\\
\text{spatial }5R &: M=2,\\
\text{spatial }6R &: M=3.
\end{aligned}
\]

The virtual closure is an exact representation of the fixed-position constraint. It is not by itself a proof that the result is a planar or spatial four-bar.

## 8. Orientation image, pointing image, and coverage target

The orientation image at \(p^*\) is

\[
\mathcal O(p^*)
=
\{R(q):q\in\mathcal F_{p^*}\}
\subseteq SO(3).
\]

For a selected tool axis \(\hat z_T\), the pointing projection is

\[
\pi(R)=R\hat z_T,
\]

and the pointing image is

\[
\mathcal P(p^*)
=
\{R(q)\hat z_T:q\in\mathcal F_{p^*}\}
\subseteq S^2.
\]

These should remain distinct from the coverage target \(Y\), which is imposed by the task.

Examples:

- planar full orientation: \(Y=SO(2)\);
- specified one-parameter spatial task: \(Y=Y_1\subset SO(3)\);
- arbitrary pointing with roll ignored: \(Y=S^2\);
- full spatial orientation: \(Y=SO(3)\).

A point is conventionally dexterous only when

\[
\mathcal O(p^*)=SO(2)
\]

in the planar case or

\[
\mathcal O(p^*)=SO(3)
\]

in the spatial case.

For a pointing task, define a separate pointing-complete condition

\[
\mathcal P(p^*)=S^2.
\]

## 9. Dimensional ladder

A necessary regularity-level condition for covering a target \(Y\) while holding position fixed is

\[
n-d_p\geq\dim Y,
\]

where \(d_p=2\) for planar position and \(d_p=3\) for spatial position.

| Source chain | Fixed-position mobility | Maximum-dimensional orientation image | Appropriate coverage question |
|---|---:|---|---|
| planar 2R | 0 | zero-dimensional subset of \(SO(2)\) | no continuous orientation sweep |
| planar 3R | 1 | one-dimensional subset of \(SO(2)\) | does it cover all \(SO(2)\)? |
| spatial 4R | 1 | curve in \(SO(3)\) | does it cover a specified one-parameter orientation family? |
| spatial 5R | 2 | surface-like subset of \(SO(3)\), pointing projection in \(S^2\) | does pointing cover all \(S^2\)? |
| spatial 6R | 3 | three-dimensional subset of \(SO(3)\) | does it cover all \(SO(3)\)? |
| spatial 7R | 4 | potentially all \(SO(3)\) plus self-motion | can full orientation coexist with redundancy? |

Dimension matching does not prove coverage, connectivity, nonsingularity, or correct mechanism factorization.

## 10. Why planar 3R produces a Grashof-relevant four-bar

For planar 3R,

\[
\dim\mathcal F_{p^*}=3-2=1
=
\dim SO(2).
\]

The exact virtual closure is a planar 4R. Tool orientation is the rotation of a designated virtual link up to a fixed offset. Therefore complete planar orientation becomes a complete link-rotation problem.

This is the structural reason four-bar rotatability and Grashof-type classification are relevant in the planar case.

## 11. Spatial 4R as the first spatial decomposition test

For a regular spatial 4R,

\[
4R+S_v,
\qquad M=1.
\]

Its orientation image is generically a curve

\[
C_{p^*}=R(\mathcal F_{p^*})\subset SO(3).
\]

There is no general reason for this curve to be rotation about one fixed axis.

If two consecutive physical revolute axes intersect orthogonally, they may be exactly regrouped as a universal joint:

\[
RR\longleftrightarrow U.
\]

Then the source closure may admit a role-aware representation such as

\[
S_v U_{\mathrm{phys}} R R
\]

with the virtual closure retained as the semantic origin. Depending on which physical pair is aggregated, use `S_v-U_phys-R-R`, `S_v-R-U_phys-R`, or `S_v-R-R-U_phys`. These topologies may be cyclically isomorphic to existing `USRR`-class solver strings, but the compound-joint roles differ. The physical universal joint must not inherit virtual tool-joint winding semantics. The aggregation must preserve source forward kinematics, components, tangent spaces, limits, and the full continued branch over the claimed scope.

## 12. Spatial 5R and the two-dimensional pointing parent

For a regular spatial 5R,

\[
5R+S_v,
\qquad M=2.
\]

The source orientation image is at most two-dimensional in \(SO(3)\). Its pointing projection may be compared with \(S^2\), but a generic 5R does not automatically produce a pure pointing task or complete pointing coverage.

Exact physical axis aggregation may yield parent topologies such as

\[
S_v U_{\mathrm{phys}} U_{\mathrm{phys}} R
\]

or

\[
S_v S_{\mathrm{phys}} R R
\]

up to cyclic ordering. These are still two-degree-of-freedom parents.

A one-dimensional child requires an additional regular scalar task constraint

\[
\mathcal G_{p^*,c}
=
\{q\in\mathcal F_{p^*}:h(R(q)\hat z_T)=c\}.
\]

The function \(h\), value \(c\), parent component, and task provenance must be recorded.

## 13. Aligned terminal-roll quotient

For a generic spatial 6R,

\[
6R+S_v,
\qquad M=3.
\]

Let the selected tool pointing direction be \(R\hat z_T\). Orientations with the same pointing direction differ by an \(SO(2)\cong S^1\) roll fiber.

A terminal revolute joint \(R_6\) can parameterize this roll fiber only if:

1. its axis is coincident with the selected tool-roll axis;
2. the tool origin lies on the axis;
3. changing \(q_6\) leaves tool position unchanged;
4. changing \(q_6\) leaves pointing unchanged;
5. the required roll range is available;
6. quotient and reconstruction preserve the relevant components;
7. limits, coupling, and singularities do not defeat the separation.

Then

\[
(6R+S_v)/R_6
\longrightarrow
5R+S_v,
\qquad M:3\rightarrow2.
\]

Full orientation coverage requires both complete pointing coverage and complete roll coverage over every required pointing direction.

The bundle should not be treated globally as the Cartesian product \(S^2\times S^1\); the software uses explicit quotient/reconstruction maps rather than assuming a global product chart.

## 14. Kinematic-decomposition operations

Use the following operation types:

1. **axis aggregation** — exact regrouping of physical axes, with no mobility change;
2. **symmetry quotient** — remove a verified group action and separately retain its task coordinate;
3. **task slice** — impose an explicit additional level-set constraint;
4. **mechanism factorization** — represent a parent through coupled lower-dimensional mechanisms;
5. **predicate application** — evaluate a property without changing geometry;
6. **coverage reconstruction** — infer source coverage through a stated compatibility law.

Each operation has separate proof obligations. Equal DOF counts or matching joint-letter strings are not sufficient. A mechanism identity must include both `joint_kind_sequence` and `joint_role_sequence`; cyclically identical kind strings can represent different task semantics.

## 15. Decomposition certificate

A proposed reduction receives one status:

```text
EXACT_GLOBAL
EXACT_ON_COMPONENT
LOCAL_ONLY
APPROXIMATE
REJECTED
UNRESOLVED
```

At minimum the certificate records:

- source and reduced topology;
- coordinate and reconstruction maps;
- source component scope;
- rank/nullity checks;
- closure residuals;
- tangent-subspace error;
- trajectory reconstruction error;
- task-map error;
- joint-limit correspondence;
- failure or scope reason.

## 16. Analytical and numerical status

The structural reduction and coverage criterion may be analytical even when a family-specific mechanism predicate is numerical.

A careful description is:

> a mechanism-based orientation-coverage criterion evaluated with an exact numerical continuation solver or a conservative numerical atlas.

`Semi-analytical` is appropriate only when the analytical reduction, numerical predicate, uncertainty policy, and exact fallback are stated separately.

Finite numerical sampling should use qualified labels such as

```text
COVERED_AT_DECLARED_RESOLUTION
PARTIAL_COVERAGE
UNRESOLVED
```

rather than an unqualified exact theorem.

---

## 17. V05 pseudo-arclength correction and derivative policy

<!-- V05_AUDIT_CORRECTION_2026_08_08 -->

For a spatial-4R fixed-position fiber, solve

\[
G(q)=
\begin{bmatrix}
p(q)-p^*\\
t_k^T(q-q_{\mathrm{pred}})
\end{bmatrix}=0
\]

with Newton matrix

\[
DG(q)=
\begin{bmatrix}
J_p(q)\\
t_k^T
\end{bmatrix}.
\]

The arclength equation selects a unique corrected point from the one-dimensional position level set and avoids treating a single joint as a global parameter.

The project does not require a hand-derived Jacobian as a matter of principle. Finite differences, automatic differentiation, secant/Broyden approximations, or derivative-free local solvers may be used. However, the following structural quantities require derivative information or an approximation:

- local rank and fiber dimension;
- null tangent;
- pseudo-arclength correction;
- singularity and conditioning diagnostics.

The active implementation uses the analytical geometric Jacobian and independently checks it against a central finite-difference Jacobian.

---

## 18. Nested level-set decomposition from L3 through L7

<!-- DECOMPOSITION_LADDER_L3_L7_2026_08_12 -->

Let a regular fixed-position source parent have dimension

\[
m=n-d_p,
\]

where \(d_p=2\) for planar position and \(d_p=3\) for spatial position. Choose
\(m-1\) independent scalar constraints

\[
h_1(q)=c_1,\ldots,h_{m-1}(q)=c_{m-1}.
\]

At regular values, the nested level set

\[
\mathcal F_{\mathbf c}
=
\{q:p(q)=p^*,\ h_i(q)=c_i\}
\]

is one-dimensional. This is the common source-fiber construction for the L3–L7
decomposition ladder (active architecture; see `docs/theory/DECOMPOSITION_LADDER.md`
and `docs/CURRENT_STATUS.md`):

```text
L3 planar 3R: no additional slice
L4 / V05 spatial 4R: no additional slice
L5 / V06 spatial 5R: one task slice
L6 / V07-first then V08: two task slices after independent SO(3) truth
L7 deferred: one redundancy gauge plus two task slices (BLOCKED until V05 gate lifts)
```

A one-dimensional source fiber is defined by the source chain and the explicit level-set constraints. It is not automatically a known four-bar family. Mechanism compression is a second operation requiring an equivalence certificate that preserves the ADR-021 split between axis aggregation and closed-mechanism equivalence.

For an L5 pointing parent, a useful scalar field is

\[
h(d)=n^Td=c.
\]

Regular values define one-dimensional pointing fibers. The parent is reconstructed as a union of fibers only after the parameter domain, critical values, components, and singular fibers have been audited:

\[
\mathcal P_{p^*}
=
\bigcup_c \mathcal F_c.
\]

This is a fiber-family statement, not a claim that the parent is globally a Cartesian product.

## 19. Universal-joint coordinates on a one-DOF child

A universal joint has two local coordinates,

\[
U(\alpha,\beta)=R_a(\alpha)R_b(\beta),
\]

but a closed one-degree-of-freedom child supplies only one independent branch parameter. The canonical parameter is pseudo-arclength \(s\):

\[
\alpha=\alpha(s),
\qquad
\beta=\beta(s).
\]

The numerical solver advances \(s\) and solves loop closure for both universal-joint coordinates and all remaining coordinates. The two winding questions are read from the same returned branch:

\[
w_\alpha
=
\operatorname{round}\frac{\Delta\widetilde\alpha}{2\pi},
\qquad
w_\beta
=
\operatorname{round}\frac{\Delta\widetilde\beta}{2\pi}.
\]

Prescribing \(\alpha\) means adding

\[
\alpha=\alpha_{\mathrm{command}}
\]

as one equation and solving all other coordinates. It is a valid local chart only where

\[
\frac{d\alpha}{ds}\neq0.
\]

At an \(\alpha\) turning point, switch to \(\beta\) when valid or return to pseudo-arclength. Thus \(\alpha\) and \(\beta\) are two coupled coordinates of one compound joint, not two independent inputs to the one-DOF mechanism.
