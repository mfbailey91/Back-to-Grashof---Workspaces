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
5. `special-tied-shortest`;
6. conventional `double-crank`, `crank-rocker`, `grashof-double-rocker`, or `non-grashof-double-rocker`.

A separate `grashof_class` field reports `non-assemblable`, `grashof`, `change-point`, or `non-grashof`. Exact terminal-link rotatability is still decided by loop-closure interval containment and never by the textual inversion label alone.

## 6. Grashof classification versus designated-link rotatability

\[
\text{Grashof} \not\Rightarrow \text{terminal input fully rotates}.
\]

Canonical counterexample `unequal_proximal` with \((l_1,l_2,l_3)=(3,1,2.5)\):

| Radius | Grashof | Inversion | Input rotates | Dexterous |
|---|---|---|---:|---:|
| \(0<\rho<0.5\) | Grashof | double-crank | yes | yes |
| \(\rho=0.5\) | change-point | change-point | yes | yes |
| \(0.5<\rho<1.5\) | non-Grashof | double-rocker | no | no |
| \(1.5<\rho<4.5\) | Grashof | grashof-double-rocker | no | no |
| \(4.5<\rho<6.5\) | non-Grashof | double-rocker | no | no |

Exact radial partitions use analytical transition radii (reachable/dexterous bounds, \(\rho\in\{l_1,l_2,l_3\}\), and exact zeros of the piecewise-linear Grashof margin), not coarse sampling.

## 7. Spherical 4R characteristics (6R extension)

See `docs/theory.md` for full conventions. For spherical link angles \((\alpha,\beta,\gamma,\eta)\) in the Murray–Larochelle / McCarthy–Soh ordering (input, output, ground, coupler),

\[
\begin{aligned}
T_1 &= \gamma - \alpha + \eta - \beta,\\
T_2 &= \gamma - \alpha - \eta + \beta,\\
T_3 &= \eta + \beta - \gamma - \alpha,\\
T_4 &= 2\pi - (\alpha + \beta + \gamma + \eta).
\end{aligned}
\]

Grashof family: \(T_1 T_2 T_3 T_4 > 0\). The hand-orientation link is the output \(\beta\). Dexterity is never inferred from the product alone.

## 8. Regional and spherical reductions (6R Sprints 2–3)

See `docs/spherical_reduction.md` for Architecture A conventions:

- base-azimuth quotient about \(\hat a_1\);
- regional reachability \(|L_2-L_3|\le\rho_w\le L_2+L_3\) and planar virtual four-bar \((\rho_p,L_t,L_3,L_2)\);
- spherical virtual four-bar angles from meridional normal and wrist axes \((n,a_4,a_5,a_6)\) with \(\beta=\angle(a_5,a_6)\) as the hand-orientation link;
- invalid concurrency residuals must not emit spherical angles.

## 9. Numerical orientation ground truth (6R Sprints 4–5)

See `docs/experiment_protocol.md`:

- reproducible Hopf \(SO(3)\) samples at coarse / medium / fine resolutions;
- IK status taxonomy `solved` | `unreachable` | `solver_failed`;
- coverage \(C(p)\) and connected components over feasible orientation samples;
- Gate 2: aggregate metrics must converge with sample density before Sprint 5 interpretation;
- analytical prediction is compared to numerical labels; product \(\neq\) dexterity.

## 10. Aligned-terminal pointing fiber (spatial Sprint 05)

Conventions: joint order \((q_1,\ldots,q_6)\) in radians; space-frame pointing \(d(q)\) is the unit terminal axis; \(p(q)\) is the task point. The Sprint 04B/04C parent is the roll-quotiented fixed-position set

\[
P_{p_0,q_6^*}=\bigl\{q:p(q)=p_0,\ q_6=q_6^*\bigr\}.
\]

An explicit one-dimensional fiber is the additional task-space level set

\[
F_c=\bigl\{q\in P_{p_0,q_6^*}:h(q)=c\bigr\},
\]

with primary scalar

\[
h(q)=n\cdot d(q),
\]

where \(n\) is a fixed world-frame unit vector, recorded in the experiment manifest, and \(c=h(q_0)\) at a named regular seed. The analytical gradient is

\[
\frac{\partial h}{\partial q_i}=n\cdot\bigl(w_i(q)\times d(q)\bigr)=\bigl(n^\top J_d(q)\bigr)_i.
\]

Under the aligned-terminal conditions \(p\in R_6\) and \(d\parallel w_6\), terminal roll does not change pointing, so

\[
\frac{\partial h}{\partial q_6}=0.
\]

The stacked reduced constraint on \((q_1,\ldots,q_5)\) is

\[
\mathcal{F}(q)=\begin{bmatrix}p(q)-p_0\\ h(q)-c\end{bmatrix}\in\mathbb{R}^4,
\qquad
J_{\mathcal{F}}=\begin{bmatrix}J_p\\ n^\top J_d\end{bmatrix}_{:,1:5}\in\mathbb{R}^{4\times 5}.
\]

At a regular independent seed, \(\operatorname{rank}(J_{\mathcal{F}})=4\) and \(\operatorname{nullity}(J_{\mathcal{F}})=1\). The fiber tangent is that one-dimensional kernel, embedded in \(\mathbb{R}^6\) with a zero \(q_6\) component.

An alternate task-space scalar \(h'(q)=n'\cdot d(q)\) with a second fixed unit \(n'\) is a distinct slice of the same pointing parent. Freezing a single non-terminal joint is a coordinate control, not a candidate primary \(h\).

This section does not assert spherical \(RRRR\) equivalence, McCarthy–Soh classification, or exact-UR geometry.

## 11. Topology-derived spherical candidate axes (spatial Sprint 06)

Conventions: the same joint order, space-frame axes \(A_i=(r_i,w_i)\), task point \(p_0\), and unit fiber tangent \(t=(t_1,\ldots,t_5,0)\) as in §10. The intersecting-pairs architecture is

\[
U_A=(R_1,R_2),\qquad U_B=(R_3,R_4),\qquad R_C=R_5.
\]

The reduced cyclic parent is

\[
S-U_A-U_B-R_5.
\]

This construction is a named, unverified C12 hypothesis. It is not a scan of physical four-axis subsets. The UR-like arm has no \(U_A\)/\(U_B\) parent; any physical four-subset scan there is exploratory only.

Live pair centers are accepted only when \(\operatorname{dist}(R_1,R_2)\le 10^{-12}\,\mathrm{m}\) and \(\operatorname{dist}(R_3,R_4)\le 10^{-12}\,\mathrm{m}\). Instantaneous candidate axes, with continuously sign-aligned unit directions, are

\[
\Omega_A=t_1\omega_1+t_2\omega_2
\quad\text{through the current \(U_A\) center},
\]

\[
\Omega_B=t_3\omega_3+t_4\omega_4
\quad\text{through the current \(U_B\) center},
\]

\[
\Omega_R=\omega_5
\quad\text{on the physical \(R_5\) line},
\]

\[
\Omega_S=\sum_{i=1}^{5}t_i\omega_i
\quad\text{through the fixed task point \(p_0\)}.
\]

\(\Omega_A\), \(\Omega_B\), and \(\Omega_S\) are well-posed only when each has norm greater than \(10^{-8}\). The cyclic order is

\[
S_{\mathrm{eff}},\ U_{A,\mathrm{eff}},\ U_{B,\mathrm{eff}},\ R_5.
\]

Adjacent spherical arc angles are \(\alpha_i=\arccos(a_i^\top a_{i+1})\in(0,\pi]\) on that cycle. Arc drift is \(\max_\sigma\|\alpha(\sigma)-\alpha(0)\|\).

Exact concurrency is a single branch-global center, not a per-sample best-fit point. With samples \(j\) and candidate axes \(k\),

\[
c^*=\arg\min_c\sum_{j,k}
\left\|
\bigl(I-a_{jk}a_{jk}^{\mathsf T}\bigr)(c-r_{jk})
\right\|^2.
\]

Report the global RMS line-to-center residual, the maximum line-to-center residual, per-sample four-axis centers \(c_j\) and drift \(\|c_j-c^*\|\), and residuals versus \(\sigma\). A spherical mechanism requires a fixed center.

Two distinct legitimacy tests must not be conflated:

1. **Simple coordinate locking.** One coordinate in each \(U\) pair remains constant to within \(10^{-6}\) rad. On the committed primary IP segment this already fails (\(q_1,\ldots,q_5\) all move).
2. **Body-fixed effective-axis invariance** (Sprint 06 gate). Both \(U\) coordinates may move, but each effective revolute direction remains fixed in its two adjacent body frames: \(S\) in ground and the body after \(R_5\); \(U_A\) in ground and the body after \(R_2\); \(U_B\) in the bodies after \(R_2\) and \(R_4\); \(R_5\) in the bodies after \(R_4\) and \(R_5\).

These identities do not assert an exact spherical \(RRRR\), McCarthy–Soh roles, or mechanism equivalence until the named residuals pass.

