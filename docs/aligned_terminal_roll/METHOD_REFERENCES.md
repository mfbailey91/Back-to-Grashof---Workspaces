# Method references — aligned terminal-roll spatial kernel

**Status:** Sprint 04C audit  
**Rule:** Curated list only. Project-specific constructions are labeled as such.

## Product of exponentials / screw kinematics

Murray, Li, and Sastry, *A Mathematical Introduction to Robotic Manipulation*, CRC Press, 1994, Ch. 2–3.

**Use:** Space-frame PoE FK in `serial_chain.py` and screw columns of `J_p`, `J_d` in `jacobians.py`. Joint order and distal-to-proximal product follow `GEOMETRIC_CONVENTIONS.md`.

## Numerical rank by SVD

Golub and Van Loan, *Matrix Computations*, 4th ed., Johns Hopkins, 2013, Ch. 2 and 8.

**Use:** `matrix_rank_report` / `nullspace` / `reduced_pointing_basis` with explicit absolute and relative singular-value thresholds.

## Least-norm Newton corrector

Nocedal and Wright, *Numerical Optimization*, 2nd ed., Springer, 2006, Ch. 10 (nonlinear least squares / Gauss–Newton).

**Use:** Frozen-roll position corrector `correct_position_detailed` solving `J_{p,1:5} Δq_{1:5} ≈ −(p−p0)`.

## Orthogonal Procrustes and principal angles

Golub and Van Loan, *Matrix Computations*, 4th ed., §6.4 (orthogonal Procrustes); Björck and Golub, “Numerical methods for computing angles between linear subspaces,” *Math. Comp.* 27 (1973).

**Use:** `procrustes_align_frame` transports `N_red`; `principal_angles` records subspace change between accepted steps.

## Predictor-corrector continuation

Allgower and Georg, *Introduction to Numerical Continuation Methods*, SIAM, 2003, Ch. 2–3.

**Use:** Sequential fixed-position continuation in `continuation.py`. Chart coordinates `(s,t)` are local continuation parameters, not intrinsic manifold coordinates.

## Project-specific constructions (not textbook identities)

| Construction | Where | Note |
|---|---|---|
| Aligned-terminal roll quotient `N_red = ker(J_p) ⊖ span{e6}` | `jacobians.reduced_pointing_basis` | Valid only under aligned `p∈R6`, `d∥w6` |
| Row-wise sequential pointing chart | `continue_sequential_chart` | Path-dependent local chart |
| Internal continuation microstep `0.005` | `MAX_MICROSTEP` | Integrator subdivision; ATR_EXP_024 consistency, not independent refinement |
| Architecture-specific pair map `φ(θ;q6*)` | `suur_coordinates.py` | Definedness/round-trip only; not a closed SUUR FK solver |
| Seed-frozen Sprint 04 patch | `continue_fixed_position_patch` | Historical / regression only |

## Developer-only paths

- `sprint04_readout.py` HTML diagnostic (not an acceptance criterion).
- `compound_joints.py` principal-angle probes (ADR 002: non-discriminating for SUUR).
