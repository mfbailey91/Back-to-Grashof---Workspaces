> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# Sprint V03 — Closure and Continuation Proof

**Status:** refined after V02B geometry hardening  
**Purpose:** prove that the six physical `UXXX` mechanism families possess the expected local one-dimensional closure motion before computing winding or crank classifications.

## Research question

For each physically constructed V02B four-bar geometry, does the closed mechanism admit a regular one-dimensional configuration branch?

V03 answers only this question.

It does **not** answer whether either tool-U coordinate is a crank, whether a branch closes globally, or whether a Cartesian point is dexterous.

## Common solver representation

All six ordered families have seven scalar rotational freedoms:

```text
UUUR = 2 + 2 + 2 + 1 = 7
UURU = 2 + 2 + 1 + 2 = 7
URUU = 2 + 1 + 2 + 2 = 7
USRR = 2 + 3 + 1 + 1 = 7
URSR = 2 + 1 + 3 + 1 = 7
URRS = 2 + 1 + 1 + 3 = 7
```

Internally, the solver uses the V02B axis-frame conventions:

```text
R -> z
U -> x, y
S -> x, y, z
```

These are ordered solver coordinates. In particular, the `S` coordinate triad is a coordinate chart, not a claim that the spherical joint has three physically privileged axes.

The compound-joint expansion yields one seven-coordinate rotational loop for every family. The closure problem is therefore shared rather than family-specific.

## Closure residual

Use each V02B reference assembly as the zero state. Each scalar revolute axis is represented as a space-frame screw through its stored joint center and reference direction. The product of the seven revolute exponentials must return to identity:

```text
C(q) = Exp(S1 q1) ... Exp(S7 q7) = I
```

The six-component residual is:

```text
r(q) = [translation_error, SO3_log(rotation_error)]
```

At the stored reference state:

```text
r(0) = 0
```

within numerical precision.

## V03A — reference mobility audit

Compute:

```text
Jc = dr/dq, shape = 6 x 7
```

For a regular one-DOF mechanism:

```text
rank(Jc) = 6
nullity(Jc) = 1
```

Record the singular spectrum. The smallest nonzero singular value is retained as a local conditioning / singularity-margin diagnostic.

### Stop conditions

Review the geometry or formulation if:

- reference closure is not near zero;
- rank is below 6 at an intended generic reference pose;
- nullity exceeds 1 unexpectedly;
- a family needs a separate closure convention merely to pass the zero-state audit.

## V03B — detailed `UUUR` branch proof

`UUUR` is the first detailed mechanism because it requires only R/U solver coordinates.

At each regular point, use SVD to obtain the one-dimensional null direction:

```text
Jc(q) v = 0
```

Predict:

```text
q_pred = q_k + ds v_k
```

Correct using the six closure equations plus one pseudo-arclength equation. The corrector therefore solves seven equations for seven scalar coordinates.

### Required visualizations

1. Seven scalar joint coordinates versus continuation arclength.
2. Closure residual norm versus arclength.
3. Smallest nonzero singular value versus arclength.
4. `tool_alpha` versus `tool_beta` local path.
5. Five fixed-camera 3D snapshots distributed across the branch segment.

These plots are diagnostics, not crank evidence.

## V03C — all six families

Run the same continuation kernel on one canonical V02B mechanism from each family. Report:

- number of continued points;
- achieved arclength;
- convergence fraction;
- maximum closure residual;
- minimum nonzero singular-value margin.

Do not duplicate a mechanism solve for tool axis `a` and tool axis `b`. One branch contains both tool coordinates.

## Small refinements carried into later sprints

### Six solves, twelve later classifications

The research table still contains 12 family/tool-coordinate classification questions, but the numerical pipeline should be:

```text
6 mechanism branches
    -> record tool_alpha(s), tool_beta(s)
    -> 12 later crank classifications
```

### Physical descriptors versus chart descriptors

Before V05 trend mining, mark descriptors as either:

- physical / coordinate-invariant or intentionally inversion-dependent geometry; or
- solver-chart descriptors.

No rule involving an arbitrary `S` chart axis may be promoted as a physical Grashof-like condition without additional justification.

### Full cycle belongs to V04

V03 only proves and visualizes local continued motion. V04 owns:

- branch return detection;
- angle unwrapping over a complete branch;
- winding computation;
- crank / rocker classification.

## Acceptance

V03 is complete when:

1. all six canonical V02B mechanisms satisfy reference closure;
2. all six reference closure Jacobians are rank 6 / nullity 1 at generic poses;
3. `UUUR` has a clean pseudo-arclength branch segment and all required diagnostics;
4. the same kernel continues nontrivial branch segments for the other five families;
5. generated JSON, PNG, and HTML artifacts are reproducible;
6. all readouts explicitly avoid crank, winding, and dexterity claims.
