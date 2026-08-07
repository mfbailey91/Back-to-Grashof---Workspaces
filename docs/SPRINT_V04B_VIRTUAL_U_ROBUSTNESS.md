# Sprint V04B — Virtual-U Robustness and Orientation Sweep

**Status:** insertion sprint before V05 descriptor mining  
**Purpose:** verify that V04 crank/rocker labels are stable numerical properties of the continued mechanism branch and are not artifacts of continuation direction, step size, or one arbitrary virtual-tool `U` coordinate convention.

## Why V04B exists

V04 established a real numerical result for `UUUR`: one physical mechanism solve produces a returned one-DOF cycle and both tool-`U` coordinates on that same branch,

```text
UUUR mechanism -> alpha(s), beta(s) -> (w_alpha, w_beta).
```

The explorer still exposes two tool-axis questions (`tool_a` and `tool_b`), but they are not separate mechanisms or separate closure solves. They are the two perpendicular revolute coordinates inside the same virtual tool universal joint:

```text
U_t(alpha, beta) = R_a(alpha) R_b(beta).
```

`tool_a` asks whether the `alpha` coordinate winds on the returned branch.  
`tool_b` asks whether the `beta` coordinate winds on that same returned branch.

Before V05 correlates geometry descriptors with crank labels, V04B checks that the label survives reasonable numerical and virtual-coordinate choices.

## Interpretation correction

The `phi` sweep below is a **diagnostic sensitivity experiment**, not proof that arbitrary in-plane rotations of the provisional `U` are physically distinct pointing fibers. The original pointing hierarchy retains the virtual spherical closure `S_v`; a research-evidence `U_v` must be induced by an explicit one-dimensional pointing slice of that two-DOF parent.

Therefore V04B establishes:

```text
winding is numerically robust,
but winding depends on how the provisional U is constructed.
```

It does **not** establish:

```text
phi is automatically a physical atlas parameter.
```

See [`SPATIAL_POINTING_SLICE_CONTRACT.md`](SPATIAL_POINTING_SLICE_CONTRACT.md).

## V04B tests

### A. Step-size convergence

For one physical `UUUR` sample, repeat the returned-cycle solve at several pseudo-arclength step sizes while holding an approximately fixed arclength budget.

Record:

- returned / open / change-point status;
- `W = (w_alpha, w_beta)`;
- maximum raw coordinate increment between continuation samples;
- tool-coordinate coverage fractions.

A winding result is considered numerically stable when the returned-cycle winding pair agrees across the tested step sizes.

### B. Direction reversal

Continue the same physical branch deliberately in both tangent directions.

For a returned cycle, expect

```text
W_minus = -W_plus
```

up to the chosen coordinate orientation. Therefore crank status must agree under reversal even though winding sign changes.

### C. Controlled virtual-U orientation sweep

Hold all joint centers and all non-tool joint frames fixed. Rotate only the virtual tool `U` frame in its own perpendicular-axis plane:

```text
phi = 0 ... 360 deg.
```

For each `phi`:

1. rebuild only the tool-`U` axes;
2. audit reference closure rank/nullity;
3. continue the one-DOF cycle;
4. compute `W(phi)`;
5. record tool-coordinate coverage.

This is intentionally different from the V02B perturbation corpus, where tool-frame rotation is coupled to changes in the rest of the mechanism geometry.

### D. Tool-U axis-order sensitivity

Evaluate both solver coordinate orders:

```text
R_a(alpha) R_b(beta)
R_b(beta) R_a(alpha)
```

The two perpendicular axis lines are unchanged; only their serial coordinate order is changed. Differences diagnose coordinate sensitivity. They do not by themselves establish a new physical mechanism parameter; physical interpretation waits for the task-derived `S_v -> U_v` fiber construction.

### E. Winding versus angular coverage

Retain both predicates:

```text
crank_i    := |w_i| >= 1
coverage_i := min(1, unwrapped_range_i / 2pi)
```

A nonzero winding implies complete angular coverage, but the software should not assume the converse without checking the observed continuous range.

## Deliverables

- `v04b.py` robustness/orientation-sweep runner;
- JSON result export;
- step-size convergence plot;
- direction-reversal table;
- `W(phi)` orientation-sweep plot;
- angular-coverage plot;
- axis-order comparison table;
- `sprint_04b_virtual_u_robustness.html`;
- targeted tests.

## Acceptance

V04B is complete when:

1. at least one returned `UUUR` sample has the same crank/rocker status under step-size refinement;
2. a returned branch satisfies `W_minus = -W_plus` for both defined tool windings;
3. a controlled tool-`U` orientation sweep reports closure audit + winding/coverage at each sampled `phi`;
4. both `ab` and `ba` tool-axis orders are explicitly evaluated;
5. V05 is blocked from treating tool-frame orientation/order as irrelevant unless V04B data supports that simplification;
6. arbitrary `phi` variants remain diagnostic-only until a task-derived pointing slice proves what physical fiber, if any, they represent.
