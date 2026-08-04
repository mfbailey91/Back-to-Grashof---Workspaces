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
