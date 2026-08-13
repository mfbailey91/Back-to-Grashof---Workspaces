# Why the Fixed-Position Solver Uses a Jacobian

## It is not required merely to find a solution

The fixed-position equation is

\[
p(q)-p^*=0.
\]

One can find configurations satisfying it without writing an analytical Jacobian. Possible approaches include:

- derivative-free nonlinear optimization;
- coordinate search;
- gridding one joint and solving the remaining equations;
- secant or Broyden methods;
- interval subdivision;
- random sampling followed by projection;
- automatic differentiation or finite-difference derivatives rather than hand-derived derivatives.

So the project does **not** assume that an analytical Jacobian is the only way to solve inverse kinematics.

## Why the derivative is useful for this project

V05 is not only asking for one configuration. It is asking for the structure of the complete fixed-position level set.

For a spatial 4R source,

\[
J_p(q)=\frac{\partial p}{\partial q}\in\mathbb R^{3\times4}.
\]

The Jacobian supplies four distinct pieces of information.

### 1. Local dimension

At a regular point,

\[
\dim\mathcal F_{p^*}=4-\operatorname{rank}J_p.
\]

Rank three establishes a local one-dimensional fiber. A black-box solver returning a point does not by itself establish that dimension.

### 2. Tangent direction

A local fiber tangent satisfies

\[
J_p(q)t=0.
\]

The null vector tells the continuation algorithm which direction lies along the fixed-position mechanism rather than away from it.

### 3. Pseudo-arclength correction

Prediction along the tangent is followed by correction with

\[
\begin{bmatrix}
J_p(q)\\
t_k^T
\end{bmatrix}\Delta q
=
-
\begin{bmatrix}
p(q)-p^*\\
t_k^T(q-q_{\mathrm{pred}})
\end{bmatrix}.
\]

The extra arclength equation selects one point from the one-dimensional solution set and allows continuation through folds where no single joint is a valid global parameter.

### 4. Singularity and conditioning

Small singular values of `J_p` reveal rank loss and poor conditioning. This is essential when deciding whether a branch is regular, approaching a singularity, or numerically unresolved.

## The Jacobian need not be analytical

All of the above can use an approximation:

\[
J_{p,ij}
\approx
\frac{p_i(q+h e_j)-p_i(q-h e_j)}{2h}.
\]

The patch therefore uses both:

- an analytical geometric Jacobian for efficient continuation;
- an independent central finite-difference Jacobian as a validation check.

Automatic differentiation would also be acceptable.

## A derivative-free alternative

For 4R, one could choose a local parameter, for example `q4`, and for every trial value solve

\[
p(q_1,q_2,q_3,q_4)-p^*=0
\]

for `(q1,q2,q3)` with a derivative-free root finder.

That can work on a monotone chart, but it has weaknesses:

- it can miss disconnected components;
- it can fail where `q4` turns around along the fiber;
- it does not directly expose tangent direction or rank;
- it makes singularity detection indirect;
- branch switching and duplicate solutions are harder to control;
- it can require many more forward-kinematics evaluations.

A secant continuation method can avoid an explicit Jacobian by estimating the tangent from previous samples and using Broyden updates. But a secant/Broyden matrix is still an approximation to the same derivative information.

## Project policy

Use the Jacobian as a **numerical structural instrument**, not as an extra kinematic assumption:

```text
forward kinematics defines the mechanism
Jacobian describes the local derivative of that same map
finite differences independently check the analytical derivative
source-chain conclusions never depend on an unchecked Jacobian alone
```
