# Implementation rationale — aligned terminal-roll spatial kernel

**Status:** Sprint 04C audit  
**Scope:** Decision-bearing methods used through Check-in 4B  
**Nonclaim:** This note does not authorize fibers, spherical `RRRR`, McCarthy–Soh, or exact UR.

## Inventory

| Module | Functions | Claims | Tests / experiments | Scope |
|---|---|---|---|---|
| `serial_chain.py` | `SerialRevoluteChain.evaluate` | C1–C5 FK | ATR_EXP_001–010 | general |
| `jacobians.py` | `position_jacobian`, `pointing_jacobian`, `matrix_rank_report`, `reduced_pointing_basis` | C6–C8 | ATR_EXP_006–012 | general |
| `continuation.py` | `sequential_predictor_step`, `continue_sequential_chart`, `procrustes_align_frame` | C10 | ATR_EXP_021–026 | general |
| `chart_diagnostics.py` | `chart_differentials`, `true_forward_reverse`, `rectangular_loop`, `duplicate_report` | C10 | ATR_EXP_021–026 | general |
| `suur_coordinates.py` | `pair_intersection_distances`, `suur_map` | C9 local / A07 | ATR_EXP_016–018, 022 | IP only |
| `continuation.py` | `continue_fixed_position_patch` | historical Sprint 04 | ATR_EXP_019–020 | developer / regression |
| `compound_joints.py` | principal-angle probes | ADR 002 negative control | ATR_EXP_013–014 | developer / labeled non-discriminating |
| `sprint04_readout.py` | HTML assembly | none | diagnostic only | developer-only |

## Product-of-exponentials forward kinematics

- **What:** Space-frame PoE from distal to proximal, returning `p`, `d`, `R`, and current axes.
- **Why:** Matches the frozen geometric conventions; screw columns of `J_p` and `J_d` are then exact.
- **Validity:** Rigid revolute 6R; home axes and joint order as constructed.
- **Check:** Analytical vs central-difference Jacobians; aligned-terminal roll invariance.
- **Does not authorize:** Dynamics, collision, URDF identity, or global workspace claims.

## Position and pointing Jacobians

- **What:** `J_p[:,i] = w_i × (p − r_i)`, `J_d[:,i] = w_i × d`.
- **Why:** Standard spatial velocity maps for a point and a body-fixed direction.
- **Validity:** Same configuration used for FK and Jacobian; `d` is a unit pointing vector.
- **Check:** Multi-`h` finite-difference agreement on named regular poses.
- **Does not authorize:** Rank conclusions away from the tested regular set.

## SVD rank and null space

- **What:** `threshold = max(1e-10, 1e-9 σ_max)`; rank counts singular values above threshold.
- **Why:** Explicit, reproducible numerical rank with published singular values.
- **Validity:** Well-scaled metre/radian models; near-singular cases must be labeled, not forced regular.
- **Check:** Named regular vs constructed singular / near-singular examples.
- **Does not authorize:** Treating threshold choice as a geometric theorem.

## Terminal-roll quotient

- **What:** `N_red` is `ker(J_p)` with `e6` removed; Stage A expects `rank(J_pd)=5`, `ker ∥ e6`, `rank(J_d N_red)=2`.
- **Why:** Aligned terminal roll is a symmetry of `(p,d)` when `p` lies on `R6` and `d ∥ w6`.
- **Validity:** Aligned-terminal fixtures only.
- **Check:** ATR_EXP_001–012 positive and negative controls.
- **Does not authorize:** Quotienting an off-axis or misaligned terminal joint.

## Sequential predictor-corrector continuation

- **What:** From accepted `q_k`, predict `q_k + B_k Δu`, freeze `q6`, Newton-correct `p(q)=p0` on `q1…q5`. Failed steps are halved up to three times and recorded.
- **Why:** Follows the fixed-position manifold sequentially instead of projecting a seed-frozen tangent plane.
- **Validity:** Regular seed; small chart steps; corrector residual `≤ 1e-10 m`.
- **Check:** ATR_EXP_021 reverse from the true endpoint; rejected-step reporting tests.
- **Does not authorize:** Global connectedness or a one-dimensional fiber.

Internal chart microstep `MAX_MICROSTEP=0.005` is a project-specific integrator subdivision. Shared-node exact agreement under different macro grids that share this microstep is consistency, not independent refinement.

## Tangent-frame alignment

- **What:** Orthogonal Procrustes `B_k = N_k (U V^T)` from `N_k^T B_{k-1} = U Σ V^T`, plus principal angles.
- **Why:** Null-space bases have arbitrary sign and in-plane rotation; alignment keeps chart axes continuous.
- **Validity:** Both frames two-column and full rank; large principal angles reject the step.
- **Check:** Sign-flip / column-swap unit test; reverse-ray return.
- **Does not authorize:** Path-independent finite `(s,t)` coordinates on a curved manifold.

## Configuration- and pointing-chart rank

- **What:** Interior wrapped central differences `Q=[Q_s Q_t]` and `D=[D_s D_t]`; require numerical rank 2.
- **Why:** Tests that corrected samples form a genuine 2-parameter chart and a 2-parameter pointing image.
- **Validity:** Interior nodes with neighbors at `±Δs`, `±Δt`; joint wrap before division.
- **Check:** ATR_EXP_022/023; collapsed synthetic chart fails.
- **Does not authorize:** Global covering of `S2`.

## Duplicate, reverse, and loop diagnostics

- **What:** Wrapped pairwise `q` distances; forward then reverse from the endpoint; rectangular `+s+t−s−t` with true integrator steps (`max_microstep=None`).
- **Why:** Detect collapse, branch jumps, and integrator/frame-transport error.
- **Validity:** Local patch only. Loop error is a diagnostic; exact closure is not required.
- **Check:** ATR_EXP_021, 025, 026.
- **Does not authorize:** Geometric holonomy measurement or global injectivity.
