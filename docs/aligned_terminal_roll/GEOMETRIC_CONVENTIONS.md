# Geometric Conventions — Aligned Terminal-Roll Workstream

**Status:** Frozen after Check-in 1 (approved 2026-08-04)
**Rule:** A convention change after Check-in 1 requires a decision record and rerun of affected experiments.

## 1. Units

- length: metres in software and result manifests;
- angle: radians in calculations;
- displayed angle: degrees permitted only in figures and human-readable summaries;
- axis direction: dimensionless unit vector;
- tolerance values: always carry units in documentation.

## 2. Frames

- `W`: inertial world frame;
- `B`: robot base frame;
- `F`: terminal flange frame immediately after `R6`;
- `T`: task/tool frame;
- `p`: selected Cartesian task point expressed in `W`;
- `d`: selected unit tool pointing direction expressed in `W`.

For synthetic models, use `W = B` unless an experiment explicitly tests a base transform.

## 3. Revolute-axis representation

Represent every revolute axis by a point-direction pair:

```text
A = (r, w)
```

where:

- `r in R3` is any point on the axis;
- `w in R3` is a unit direction;
- positive rotation follows the right-hand rule about `w`.

Equivalent points on the same line are permitted. Equality of axes must therefore be tested as line equality, not point equality.

Distance from point `x` to axis `(r, w)`:

```text
||(I - w w^T)(x - r)||
```

Parallelism residual for unit vectors `a` and `b`:

```text
||a x b||
```

Use sign-insensitive parallelism for axis alignment unless directed orientation is explicitly required.

## 4. Terminal-roll task definition

The aligned-terminal condition is:

```text
distance(p, R6) = 0
d parallel R6
```

The reduced task map is:

```text
Psi(q) = (p(q), d(q))
```

`q6` is a terminal-roll symmetry only when:

```text
dp/dq6 = 0
dd/dq6 = 0
```

The full tool orientation may still change.

## 5. Orientation representation

- use rotation matrices as the canonical orientation representation;
- quaternions may be used for interpolation or residuals but are not the source of truth;
- never subtract Euler angles to define an orientation residual;
- terminal roll is measured as the relative rotation about `d` after verifying that `p` and `d` are unchanged;
- for a full ``(-π, π]`` signed roll about known unit ``d``, rotate a probe vector perpendicular to ``d`` and recover the planar angle with ``atan2`` (axis-angle alone returns ``[0, π]``).

## 6. Kinematic formulation

The spatial experiment kernel should use an explicit axis-line/product-of-exponentials formulation.

Denavit-Hartenberg parameters may be introduced only as an adapter for exact robot data. DH frame choices must not define the research claim.

## 7. Jacobian conventions

For `q in R^n`:

```text
J_p = dp/dq            shape (3, n)
J_d = dd/dq            shape (3, n)
J_pd = [J_p; J_d]      shape (6, n)
```

Although `d` has three coordinates, its differential lies in the two-dimensional tangent plane of `S2`.

At a regular aligned-terminal 6R configuration, expected quantities are:

```text
rank(J_p) = 3
dim ker(J_p) = 3
J_p e6 = 0
J_d e6 = 0
rank(J_pd) = 5
dim ker(J_pd) = 1
```

After removing the `e6` roll direction from `ker(J_p)`, let `N_red` be a basis for the remaining two-dimensional fixed-position tangent space. Then:

```text
rank(J_d N_red) = 2
```

This is the correct local pointing-rank test. The nullity of `J_pd` is not two; it is one at a regular aligned-terminal 6R configuration.

## 8. Rank and tolerance policy

Do not hard-code one absolute tolerance for every scale.

Report:

- all singular values;
- matrix norm;
- absolute threshold;
- relative threshold;
- inferred rank.

Initial provisional policy:

```text
rank threshold = max(abs_tol, rel_tol * largest singular value)
abs_tol = 1e-10
rel_tol = 1e-9
```

These values must be stress-tested and may be changed at Check-in 1 or 2.

## 9. Exact, numerical, local, and global language

Use these terms consistently:

- **exact by construction:** follows symbolically or from defined geometry;
- **numerically verified:** residual below a stated threshold;
- **local equivalence:** tangent or differential agreement near one configuration;
- **continued equivalence:** agreement over a numerically followed branch;
- **global equivalence:** proof or exhaustive characterization of all relevant branches;
- **approximate intersection:** nonzero concurrency residual;
- **singular configuration:** expected local rank is lost.

Do not call a result global when it is based on a single continued branch.

## 10. Naming

- use `aligned terminal roll`, not merely `intersecting terminal axis`;
- use `redundant 7R`, not `over-defined 7R`;
- use `position-and-pointing task` for `(p, d)`;
- use `fixed-position pointing manifold` for the quotient parent;
- use `fiber` only after an explicit scalar constraint is identified;
- use `spherical RRRR` only after concurrency and fixed-arc conditions pass.
