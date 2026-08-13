# Universal-Joint Drive Contract

## The simple explanation

A universal joint has two angles:

\[
\alpha,
\qquad
\beta.
\]

But the complete closed four-bar child has only one degree of freedom.

Therefore we cannot freely command both angles. Loop closure couples them:

\[
\alpha=\alpha(s),
\qquad
\beta=\beta(s),
\]

where \(s\) is the mechanism's one-dimensional branch parameter.

The safest mental model is:

> **We drive the whole mechanism around its branch. The U joint reports two coupled angles while the mechanism moves.**

---

## Canonical numerical drive

The continuation solver uses pseudo-arclength:

\[
q_{\mathrm{pred}}=q_k+\Delta s\,t_k.
\]

It then solves:

\[
\begin{bmatrix}
r_{\mathrm{closure}}(q)\\
t_k^T(q-q_{\mathrm{pred}})
\end{bmatrix}
=0.
\]

So the numerical input is \(\Delta s\), not \(\Delta\alpha\) and \(\Delta\beta\).

The output is:

```text
alpha(s)
beta(s)
all other joint coordinates
closure residual
singularity margin
```

Over a returned cycle, each U coordinate can be classified separately:

\[
w_\alpha
=
\operatorname{round}\frac{\Delta\widetilde\alpha}{2\pi},
\qquad
w_\beta
=
\operatorname{round}\frac{\Delta\widetilde\beta}{2\pi}.
\]

The two winding questions come from one branch solve.

---

## What does “drive alpha” mean?

A prescribed-alpha solve adds one equation:

\[
\alpha(q)=\alpha_{\mathrm{command}}.
\]

The solver then finds beta and every other coordinate that satisfies loop closure.

Locally, alpha can parameterize the branch only when

\[
\frac{d\alpha}{ds}\neq0.
\]

At an alpha turning point,

\[
\frac{d\alpha}{ds}=0,
\]

alpha is not a valid local coordinate. The solver must:

1. switch to beta if \(d\beta/ds\neq0\); or
2. return to pseudo-arclength \(s\).

This is why pseudo-arclength is the canonical solver parameter.

---

## Source-parent pointing fibers

For a spatial 5R parent, the first operation is not to command a U angle. It is to choose a task-derived pointing level set:

\[
h(d(q))=c.
\]

For example:

\[
h(d)=n^Td.
\]

Holding \(c\) fixed selects one one-dimensional source fiber. While that fiber is continued, a local virtual-U chart may be derived and its coordinates read as

\[
\alpha(s),\beta(s).
\]

The task slice chooses **which fiber** is being solved. It does not provide two independent U-joint commands.

---

## Three modes in the software

### `FREE_BRANCH`

```text
command: ds
solve: closure + arclength
read: alpha(s), beta(s), all other coordinates
```

This is canonical for continuation and winding.

### `TASK_DERIVED_FIBER`

```text
fix: p(q)=p*, h(T(q))=c
command: ds along the constrained source fiber
read: source q(s), derived alpha(s), beta(s)
```

This is canonical for parent-to-child construction.

### `PRESCRIBED_ALPHA` or `PRESCRIBED_BETA`

```text
command: one U coordinate
solve: closure for every other coordinate
valid: only while the commanded coordinate is a regular local chart
```

This is useful for diagnostics, physical actuation studies, or a task that truly prescribes that coordinate.

---

## Interpretation rule

Do not say:

> alpha and beta are two independent inputs to the one-DOF four-bar.

Say:

> alpha and beta are two coordinates of one compound joint, coupled by the one-dimensional closed-mechanism branch.

And do not say:

> tool-alpha and tool-beta are two constituent four-bars.

Say:

> one constituent four-bar produces two U-coordinate functions, alpha(s) and beta(s), and therefore two winding/coverage questions.
