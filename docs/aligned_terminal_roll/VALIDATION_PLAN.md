# Validation Plan — Aligned Terminal-Roll Reduction

**Status:** Provisional
**Validation principle:** Every major claim requires an independent oracle or a deliberately constructed negative control.

## 1. Validation levels

1. **Geometric identity** — direct consequence of defined axis and task geometry.
2. **Analytical differential test** — Jacobian or screw calculation.
3. **Finite-difference oracle** — independent numerical approximation.
4. **Deterministic configuration suite** — named regular and singular cases.
5. **Randomized survey** — seeded sampling over a bounded configuration domain.
6. **Perturbation control** — deliberately violate one hypothesis at a time.
7. **Continuation test** — verify behavior beyond a single pose.
8. **Refinement test** — vary step size, finite-difference scale, and rank threshold.
9. **Architecture comparison** — synthetic, UR-like, and exact robot models.

## 2. Claim-to-evidence matrix

| ID | Claim | Required evidence | Initial pass criterion | Failure interpretation |
|---|---|---|---|---|
| C1 | Task point lies on terminal axis | axis-distance calculation | residual <= configured geometry tolerance | invalid fixture or task definition |
| C2 | Pointing direction aligns with terminal axis | cross-product residual | residual <= angular tolerance | invalid pointing definition |
| C3 | Terminal roll preserves task position | analytical derivative, finite difference, sweep | all residuals below tolerance | off-axis point, implementation error, or wrong transform order |
| C4 | Terminal roll preserves pointing | analytical derivative, finite difference, sweep | all residuals below tolerance | misaligned direction or wrong frame convention |
| C5 | Terminal roll changes full orientation | relative rotation extraction | nonzero commanded roll recovered | fixture does not represent terminal roll |
| C6 | Fixed-position set is locally 3D for regular 6R | SVD of `J_p` | `rank(J_p)=3` | singular point or deficient architecture |
| C7 | Position-and-pointing kernel is terminal roll only | SVD of `J_pd` and alignment to `e6` | nullity 1 and kernel parallel to roll | extra self-motion, singularity, or incorrect task map |
| C8 | Reduced pointing tangent is 2D | `rank(J_d N_red)` | rank 2 | pointing degeneracy or incorrect quotient basis |
| C9 | Compound-joint model matches physical chain | tangent principal angles and continued trajectories | thresholds satisfied over branch | representation only instantaneous or incorrectly ordered |
| C10 | Fixed-position parent is a 2D manifold | two-parameter continuation and correction residuals | noncollapsed patch stable under refinement | singularity, branch issue, or wrong constraint count |
| C11 | Scalar constraint defines a 1D fiber | constrained Jacobian and continuation | nullity 1 over nonzero branch | redundant, singular, or coordinate-artifact constraint |
| C12 | Candidate is exact spherical `RRRR` | concurrency, arc invariance, locking, motion equivalence | every prerequisite passes | candidate rejected; do not apply McCarthy-Soh |
| C13 | McCarthy-Soh predicts fiber rotatability | classification versus numerical continuation | stable agreement over accepted cases | classifier not useful for intended output motion |
| C14 | Synthetic conclusions generalize to exact UR | repeat relevant tests with exact geometry | supported claims remain within stated conditions | architecture or frame-specific limitation |

## 3. Sprint 03 local architecture matrix

Positive geometric identities:

```text
IntersectingPairsAligned6R: R1 ∩ R2 and R3 ∩ R4 exact; p on R6; d ∥ w6
URLikeAligned6R: R2 ∥ R3; R4 ∩ R5 ∩ R6 exact; p on R6 beyond wrist; d ∥ w6
```

Local compound-joint probe (intersecting pairs only):

```text
principal angles(N_red, embed(ker(J_p[:,:5]))) <= 1e-8 rad
1–3 Euler steps along unit N_red with p(q)=p0 corrector
```

This is not a C10 continuation test.

## 4. Sprint 01 test matrix

### Positive control P0

```text
p lies exactly on R6
d is exactly parallel to R6
```

Expected:

- position invariant under `q6`;
- pointing invariant under `q6`;
- full orientation changes by commanded roll.

### Negative control N1 — off-axis task point

Perturb the task point by a transverse vector.

Expected:

- position changes under `q6`;
- pointing may remain unchanged when `d` remains axis-aligned.

### Negative control N2 — misaligned pointing direction

Rotate `d` away from the terminal axis while keeping `p` on-axis.

Expected:

- position remains unchanged;
- pointing changes under `q6`.

### Optional combined negative control N3

Use both an off-axis point and misaligned direction.

Expected:

- both position and pointing change.

## 5. Numerical oracles

### Finite differences

Use central differences:

```text
df/dqi ≈ [f(q + h ei) - f(q - h ei)] / (2h)
```

Run at multiple `h` values and report the convergence trend. A single step size is insufficient evidence.

### Orientation residual

Use the relative rotation:

```text
R_rel = R(q0)^T R(q1)
```

Extract the axis-angle representation. For the aligned case, the axis should align with `d` and the angle should match the commanded terminal roll modulo numerical wrapping.

### Subspace comparison

When comparing tangent spaces, use principal angles or projection-matrix residuals rather than comparing arbitrary basis columns directly.

## 6. Singular-case policy

- singular configurations are valid observations, not generic test failures;
- deterministic singular examples should be named and reported;
- randomized rank surveys must separate regular and singular samples;
- acceptance criteria for a regular claim apply only where the stated regularity conditions hold;
- unexpectedly frequent singular samples trigger architecture review.

## 7. Reproducibility

Every decision-bearing run records:

- commit hash;
- experiment ID;
- deterministic seed;
- model parameters;
- configuration vector;
- transform convention;
- finite-difference steps;
- rank thresholds;
- solver tolerances;
- generated metrics and plots.

## 8. Check-in evidence package

A formal check-in must include:

1. experiment summaries;
2. pass/fail matrix;
3. residual and singular-value tables;
4. representative plots;
5. unexpected observations;
6. sensitivity results;
7. interpretation;
8. explicit continue, revise, pivot, or stop decision.
