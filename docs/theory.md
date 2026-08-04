# Spherical 6R theory (Sprint 0)

This document locks conventions for the spherical Grashof characterization of synthetic 6R manipulators. Equations here and in `docs/MATH_NOTES.md` §7 are the mathematical source of truth for `sixr_grashof`.

Primary project plan: `docs/PROJECT_PLAN_6R_SPHERICAL_GRASHOF.md`.

## 1. Frame and joint conventions

- Right-handed frames.
- Joint angle \(q_i\) is the rotation about axis \(\hat a_i\) using the product-of-exponentials / successive homogeneous transform convention documented in each architecture module.
- Revolute axis \(i\) is the directed line \(\ell_i=(p_i,\hat a_i)\) with \(\|\hat a_i\|=1\).
- Link indices \(1,\ldots,6\) run base → end-effector.
- Nominal lengths are dimensionless; the project normalizes so architecture, not absolute scale, determines classification.

## 2. Virtual spherical four-bar link order

At a fixed Cartesian position, when a spherical orientation reduction is valid, the residual orientation motion is modeled as a spherical 4R with ordered angular lengths

\[
(\alpha,\beta,\gamma,\eta)
\]

in the Murray–Larochelle / McCarthy–Soh convention:

| Symbol | Role |
|--------|------|
| \(\alpha\) | input (driving) link |
| \(\beta\) | output link |
| \(\gamma\) | ground (fixed) link |
| \(\eta\) | coupler link |

All angular lengths lie in \((0,\pi]\).

**Hand-orientation link (locked convention):** the virtual link representing end-effector orientation is the **output** link \(\beta\).

This assignment is never inferred from Grashof product alone. Alternative assignments for sensitivity analysis must be recorded explicitly in result records.

## 3. Characteristics \(T_1,T_2,T_3,T_4\)

Following Murray and Larochelle (1998), as used by McCarthy and Soh:

\[
\begin{aligned}
T_1 &= \gamma - \alpha + \eta - \beta,\\
T_2 &= \gamma - \alpha - \eta + \beta,\\
T_3 &= \eta + \beta - \gamma - \alpha,\\
T_4 &= 2\pi - (\alpha + \beta + \gamma + \eta).
\end{aligned}
\]

Grashof family (contains a fully rotatable link, excluding change-points):

\[
T_1 T_2 T_3 T_4 > 0.
\]

### Input motion

1. Fully rotates (crank): \(T_1 T_2 \ge 0\) and \(T_3 T_4 \ge 0\)
2. Rocks through \(0\): \(T_1 T_2 \ge 0\) and \(T_3 T_4 < 0\)
3. Rocks through \(\pi\): \(T_1 T_2 < 0\) and \(T_3 T_4 \ge 0\)
4. Rocks over two ranges: \(T_1 T_2 < 0\) and \(T_3 T_4 < 0\)

### Output motion

1. Fully rotates (crank): \(T_2 T_4 \le 0\) and \(T_1 T_3 \le 0\)
2. Rocks through \(0\): \(T_2 T_4 \le 0\) and \(T_1 T_3 > 0\)
3. Rocks through \(\pi\): \(T_2 T_4 > 0\) and \(T_1 T_3 \le 0\)
4. Rocks over two ranges: \(T_2 T_4 > 0\) and \(T_1 T_3 > 0\)

When any \(T_i = 0\) (within the boundary band), the linkage is a change-point / foldable case and is reported separately from ordinary type labels.

## 4. Sixteen linkage types

Sign patterns of \((T_1,T_2,T_3,T_4)\) map bijectively to types 1–16 (machine-readable table: `src/sixr_grashof/data/mccarthy_soh_types.json`).

Types 1–8 have \(T_4 > 0\). Types 9–16 have \(T_4 < 0\) (wrap-around family: angular lengths sum to more than \(2\pi\)).

**\(T_4 < 0\) correspondence:** type \(k+8\) has \((T_1,T_2,T_3)\) equal to the negation of those for type \(k\), and shares the same input/output crank–rocker motion class as type \(k\).

## 5. Dexterity hypothesis (not encoded as truth)

Working conjecture: at a fixed reachable position, complete orientation capability requires the hand-orientation link (\(\beta\)) to be a crank.

Under the output-hand convention, the candidate set is

\[
\text{rocker-crank}\ \cup\ \text{double-crank}
\quad\Leftrightarrow\quad
\text{types }\{2,3,10,11\}.
\]

The product \(T_1 T_2 T_3 T_4 > 0\) alone must never be treated as dexterity.

## 6. Concurrency residual thresholds

For wrist axes \(C=\{4,5,6\}\), the least-squares spherical center \(c^*\) and normalized residual

\[
\rho_C = \frac{\max_{i\in C} d(c^*,\ell_i)}{L_2}
\]

use named thresholds (see `configs/` and `sixr_grashof.reductions.residuals`):

| Status | Condition |
|--------|-----------|
| `exact` | \(\rho_C \le \rho_{\mathrm{exact}}\) |
| `approximate` | \(\rho_{\mathrm{exact}} < \rho_C \le \rho_{\mathrm{invalid}}\) |
| `invalid` | \(\rho_C > \rho_{\mathrm{invalid}}\) |

Default: \(\rho_{\mathrm{exact}}=10^{-9}\), \(\rho_{\mathrm{invalid}}=0.05\).

## 7. Architecture A worked spherical closure (hand fixture)

**Physical state (Architecture A, nominal):** \(L_2=1\), \(L_3=0.8\), \(L_t=0.25\), concurrent wrist at \(C_w\).

**Virtual spherical angles (illustrative exact-wrist fiber, type-1 crank-rocker):**

\[
\alpha=0.5,\quad \beta=1.0,\quad \gamma=1.2,\quad \eta=0.8.
\]

\[
\begin{aligned}
T_1 &= 0.5 > 0,\\
T_2 &= 0.9 > 0,\\
T_3 &= 0.1 > 0,\\
T_4 &= 2\pi - 3.5 > 0.
\end{aligned}
\]

Classification: McCarthy–Soh type **1** (crank-rocker). Input is a crank; output (hand-orientation link \(\beta\)) is a rocker. Under the working conjecture this state is **not** a dexterity candidate (candidate types are 2, 3, 10, 11 only).

Fixtures covering all 16 sign patterns live in `src/sixr_grashof/data/mccarthy_soh_types.json` and `tests/test_known_linkage_types.py`.

## References

- A. P. Murray and P. M. Larochelle, “A Classification Scheme for Planar 4R, Spherical 4R, and Spatial RCCC Linkages…,” ASME DETC, 1998.
- J. M. McCarthy and G. S. Soh, *Geometric Design of Linkages*, Springer (spherical 4R / type map material).
