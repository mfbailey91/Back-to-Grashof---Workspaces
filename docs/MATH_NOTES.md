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
