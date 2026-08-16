> **Historical audit / closeout note.** Not active roadmap. See `docs/CURRENT_STATUS.md` and `docs/reference/DECISIONS.md`.


# V05A–V05E Audit Corrections

**Status:** independent proximal `exact_u_pair_4r` closed-mechanism solve matches a budget-limited traced arc as `LOCAL_ONLY`; exact axis aggregation remains `EXACT_GLOBAL`  
**Date:** 2026-08-08

## Decision

The original regular spatial-4R corpus placed the tool point on the terminal axis and aligned the selected pointing direction with that axis. Therefore

\[
J_{p,4}=\omega_4\times(p-r_4)=0,
\qquad
J_{d,4}=\omega_4\times d=0,
\]

and at rank three / nullity one the fixed-position tangent was necessarily the terminal-roll direction. That case is retained as `terminal_roll_control_4r`, but it is no longer the active generic source.

The corrected active corpus places the tool origin transversely off the terminal axis. Each regular seed exports:

- terminal-axis point distance;
- position-Jacobian column norms;
- null tangent and upstream-joint participation;
- pointing speed along the tangent;
- analytical-versus-central-difference Jacobian error;
- source-motion signature.

## Corrected work packages

### V05A — corpus

The corpus now contains:

```text
generic_4r                    nontrivial off-axis source
terminal_roll_control_4r      explicit aligned-roll special case
exact_u_pair_4r               off-axis source with exact proximal RR→U_phys geometry
near_aligned_u_pair_4r        off-axis source with non-exact near-U geometry
singular_4r_parallel          rank-deficient exterior
```

### V05B — source continuation

The corrector solves the augmented pseudo-arclength equations

\[
\begin{bmatrix}
p(q)-p^*\\
t_k^T(q-q_{\mathrm{pred}})
\end{bmatrix}=0.
\]

The minus ray reverses the tangent but not the step sign, removing the previous double-sign reversal. Signed continuation coordinate, actual step length, arclength residual, and augmented-system condition are stored.

### V05C — orientation image

The one-dimensional image is classified as one of:

```text
PURE_TERMINAL_ROLL
FIXED_AXIS_ONE_PARAMETER_SUBGROUP
NONTRIVIAL_POINTING_CURVE
DEGENERATE_ORIENTATION_POINT
SINGULAR_OR_EMPTY
UNRESOLVED
```

Sampled geodesic path lengths in `SO(3)` and `S²` are diagnostics, not coverage claims.

### V05D — certificate split

Two claims are separated:

1. exact physical-axis regrouping `RR → U_phys`;
2. equivalence of an independently solved `S_v-U_phys-R-R` closed mechanism to a complete source component.

The exact proximal pair may receive:

```text
axis_aggregation_status = EXACT_GLOBAL
```

while aggregation alone historically left:

```text
closed_mechanism_status = UNRESOLVED
overall status = UNRESOLVED
```

After the independent `S_v-U_phys-R-R` comparison, proximal `exact_u_pair_4r`
currently records:

```text
closed_mechanism_status = LOCAL_ONLY
overall status = LOCAL_ONLY
```

because the accepted numerical trace is budget-limited and complete bidirectional
source/child component correspondence is not established. Same-source identity residuals
remain coordinate-regrouping diagnostics only and still cannot promote status.

### V05E — rejection and boundary suite

The large planted near miss remains an easy exterior regression. A tolerance-relative grid now evaluates distance and orthogonality errors at:

```text
0, 0.5×, 1×, 2×, 10×
```

Negative or otherwise invalid tolerances are rejected. The forced exact-U surrogate remains a same-coordinate task-error diagnostic, not an approximate decomposition certificate.

### Pointing-slice prototype

The earlier SUUR→UUUR artifact is relabeled as a V08-oriented prototype. It exports separate statuses:

```text
parent_slice_status
virtual_u_chart_status
child_reference_closure_status
parent_child_tangent_status
parent_child_branch_status
overall_status
```

The current worked case has a valid parent slice and local `U_v` chart, but its child tangent fails and global branch equivalence is unresolved.

## V05 gate after this patch

The patch clears the source-geometry, continuation, curve-classification, status-separation, strict-JSON, tolerance-validation, and CI-readout defects.

### Gate update (ADR-034 narrows ADR-028)

Proximal `exact_u_pair_4r` now has a valid independent closed-loop local comparison, but
the current source branch is `budget_limited`. It therefore remains `LOCAL_ONLY` until
source and child components are returned or explicitly bounded and compared in both
directions. Non-proximal pairs and other corpus architectures remain unresolved.
