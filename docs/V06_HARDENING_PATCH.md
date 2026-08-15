# V06 Hardening Patch Plan

**Project:** Characterization of Manipulator Workspaces  
**Repository:** `mfbailey91/Back-to-Grashof---Workspaces`  
**Base:** `main` at merge commit `1f2333e0fd4e70c2a537e795d99eb4d6f3b633fc`  
**Recommended branch:** `v06-hardening`  
**Scientific rung:** L5, spatial 5R fixed-position parent  
**Status:** hardening before V07A

## 1. Patch decision

V06 built the correct high-level evidence pipeline:

```text
2D source parent
  -> direct source orientation/pointing image
  -> task-derived 1D source fibers
  -> candidate closed-mechanism child
  -> reconstruction audit
```

The implementation should not be discarded. The hardening patch corrects two evidence-semantic defects first, then improves continuation and parent completeness:

1. a mechanically closed child was labeled `LOCAL_ONLY` without satisfying the defining source-fiber task;
2. a zero-population coverage comparison produced a numerical zero and the stronger conclusion `no valid recombination`;
3. D1 and D2 use tangent prediction plus underdetermined normal correction rather than an augmented pseudo-arclength corrector;
4. the A2 atlas and D1 contours are chart-local and not globally stitched.

The patch is intentionally sequenced so that **incorrect claims are removed before numerical machinery is expanded**.

---

## 2. Implementation sequence

| Slice | Purpose | Claim effect |
|---|---|---|
| **V06H0** | Freeze hardening contracts and status rules | Documentation only |
| **V06H1** | Correct D2 source-fiber/UUUR equivalence | Current child becomes `REJECTED` unless all local metrics pass |
| **V06H2** | Make E reconstruction metrics non-vacuous | Current factorization becomes `unresolved` |
| **V06H3** | Add shared 1D pseudo-arclength continuation | Numerical infrastructure only |
| **V06H4** | Re-run D1/D2 with H3 engine | Re-evaluate the current negative result |
| **V06H5** | Stitch parent charts and grow unattached multistart seeds | Improve parent/component completeness |
| **V06H6** | Regenerate artifacts and close V06 | Explicit V07A go/no-go |

The first reviewable patch contains **H0–H2 only**. Do not combine atlas growth or continuation rewriting with the evidence-semantic correction.

---

# V06H0 — Freeze the hardening contract

## 3. Source-fiber/child equivalence is conjunctive

For a child to receive `LOCAL_ONLY`, every required metric must be finite and within its declared tolerance over a declared local comparison scope:

```text
sample support
closure residual
fixed-position residual
|h(d)-c|
full-orientation geodesic error
pointing geodesic error
joint-map error
source-to-child directed set distance
child-to-source directed set distance
tangent error
```

The directed distances are distinct:

\[
d_{S\rightarrow C}
=
\sup_{q_s\in S}\inf_{q_c\in C}
 d_{\mathbb T^5}(q_s,q_c),
\]

\[
d_{C\rightarrow S}
=
\sup_{q_c\in C}\inf_{q_s\in S}
 d_{\mathbb T^5}(q_c,q_s).
\]

Reusing the child-to-source distance for both fields is forbidden.

### Initial synthetic-corpus tolerances

```text
closure residual                 <= 1e-6
position residual (m)            <= 1e-8
|h-c|                            <= 1e-5
orientation error (rad)          <= 1e-6
pointing error (rad)             <= 1e-6
joint-map error (rad)            <= 1e-8
directed set distance (rad)      <= 5e-2
tangent error                    <= 5e-2
local comparison radius (rad)    = 5e-1 in wrapped T^5 distance
minimum samples per set          = 3
```

These are evidence gates for the current synthetic experiment, not universal mechanism tolerances.

### Status rule

```text
all local checks pass, incomplete component -> LOCAL_ONLY
all checks pass, complete component scope    -> EXACT_ON_COMPONENT
required check fails                         -> REJECTED
required evidence unavailable                -> UNRESOLVED
```

The virtual-U chart itself remains `LOCAL_CANDIDATE`; chart existence is not child acceptance.

---

## 4. Reconstruction comparisons require a nonempty denominator population

When the direct source grid contains zero interior `COVERED` cells:

```text
coverage_comparison_evaluable = false
missed_cell_fraction = null
factorization_status = unresolved
```

Do not replace `len(covered)==0` by a denominator of one. A zero miss fraction in that case is vacuous.

`no valid recombination` is reserved for a campaign with:

- a sufficiently represented source image;
- a nonempty comparison population;
- a complete or explicitly bounded source-fiber family;
- an accepted candidate-child campaign covering the intended scope;
- a failed reconstruction comparison under frozen tolerances.

The current V06 evidence does not satisfy those conditions.

---

# V06H1 — Correct the D2 equivalence audit

## 5. Files

```text
src/grashof_workspace/spatial_experiments/virtual_u_child.py
tests/test_spatial_v06d2_virtual_u_child.py
src/grashof_workspace/spatial_experiments/v06d2.py
docs/DECISIONS.md
```

## 6. Implementation

In `virtual_u_child.py`:

1. add named tolerances and a declared wrapped-joint comparison radius;
2. add a true directed wrapped-set-distance helper;
3. scope source and child samples to the same wrapped ball about the source-fiber seed;
4. compute all metric maxima on scoped samples;
5. store a metric acceptance map and `failed_metrics`;
6. define `accepted_local = all(metric_checks)`;
7. issue `REJECTED` when any required local metric fails;
8. report the failed metric names in the certificate reason.

The current result is expected to fail at least the tangent check. It may also fail `h-c` and set-distance checks. The correct scientific interpretation is:

```text
The seed-derived fixed-axis U_v chart is an instantaneous candidate,
but the finite UUUR branch has not reproduced the source h=c fiber.
```

Do not reinterpret this as failure of every possible virtual-U construction.

## 7. Acceptance tests

- a synthetic asymmetric set proves the two directed distances are not aliases;
- the current exact-two-U architecture still constructs a local virtual-U chart and a rank-six/nullity-one closed branch;
- its comparison is not accepted locally;
- its certificate is `REJECTED`;
- `failed_metrics` is nonempty and includes the tangent mismatch for the current fixture;
- generic and near-two-U controls remain rejected;
- no child enters reconstruction.

---

# V06H2 — Make reconstruction non-vacuous

## 8. Files

```text
src/grashof_workspace/spatial_experiments/parent_reconstruction.py
src/grashof_workspace/spatial_experiments/v06e.py
tests/test_spatial_v06e_reconstruction.py
src/grashof_workspace/decomposition_ladder/spatial_l5.py  # inspect only; change if wording is status-specific
```

## 9. Implementation

In `ReconstructionMetrics`:

```text
missed_covered_fraction: float | None
false_positive_fraction: float | None
coverage_comparison_evaluable: bool
coverage_comparison_reason: str
```

In `_metrics()`:

```text
covered nonempty   -> compute missed fraction
covered empty      -> missed fraction None; comparison unevaluable
uncovered nonempty -> compute false-positive fraction
uncovered empty    -> false-positive fraction None
```

In `build_parent_reconstruction()`:

- do not launch missed-cell refinement when the miss metric is undefined;
- keep accepted-child reconstruction empty;
- set factorization to `unresolved` for the current campaign;
- set reconstruction coverage to `UNRESOLVED` when the comparison is unevaluable;
- make the gate distinguish “cell paint generated” from “coverage reconstruction compared”;
- remove hard-coded wording that assumes the D2 child is `LOCAL_ONLY`.

## 10. Expected current result

```text
direct source coverage label      PARTIAL_COVERAGE
direct COVERED cell count         0
coverage comparison evaluable     false
missed-cell fraction              null
accepted children                 0
factorization status              unresolved
reconstruction coverage           UNRESOLVED
V06 program passed                false
```

## 11. Acceptance tests

- JSON emits `null`, not `NaN` or a fabricated zero;
- the HTML readout prints `unevaluable` rather than formatting `None` as a float;
- the current factorization status is exactly `unresolved`;
- `source_fiber_reconstruction_compared` is false while `source_fiber_cell_paint_generated` is true;
- no adaptive refinement is triggered by an undefined miss fraction.

---

# V06H3 — Shared one-dimensional pseudo-arclength engine

## 12. New module

```text
src/grashof_workspace/spatial_experiments/branch_continuation.py
```

Define a protocol for a one-dimensional implicit branch:

```python
class ImplicitBranchProblem(Protocol):
    problem_id: str
    ambient_dimension: int
    constraint_dimension: int
    periodic_coordinates: tuple[bool, ...]

    def residual(self, x: Array) -> Array: ...
    def jacobian(self, x: Array) -> Array: ...
```

At state `x_k`, tangent `t_k`, and step `ds`:

\[
x_{pred}=x_k+ds\,t_k.
\]

Correct using:

\[
G(x)=
\begin{bmatrix}
F(x)\\
t_k^T\Delta(x,x_{pred})
\end{bmatrix}=0.
\]

Record:

```text
predictor
corrected state
constraint residual
gauge residual
correction norm
step size
Newton iterations
condition number
rank/nullity
tangent alignment
rejection reason
```

### Step adaptation

Shrink when:

- the corrector fails;
- correction norm is large relative to `ds`;
- augmented condition number exceeds the declared threshold;
- tangent rotation exceeds the declared threshold.

Grow only after several easy accepted steps.

### Return detection

Require all of:

```text
minimum accumulated arclength
wrapped state distance to seed below tolerance
absolute tangent dot product above tolerance
compatible branch/component identity
```

Position-only return detection is forbidden.

---

# V06H4 — Migrate D1 and D2 to H3

## 13. Files

```text
src/grashof_workspace/spatial_experiments/parent_level_sets.py
src/grashof_workspace/spatial_experiments/virtual_u_child.py
tests/test_spatial_v06d1_level_sets.py
tests/test_spatial_v06d2_virtual_u_child.py
```

Replace the underdetermined minimum-normal correctors in:

```text
continue_level_set()
continue_uuur()
```

Do not change the source or child equations in this slice. Re-run the H1 equivalence audit after migration.

Possible outcomes:

1. the fixed-axis child remains rejected: finite-model failure strengthened;
2. the previous drift disappears and all local checks pass: child may return to `LOCAL_ONLY`;
3. continuation becomes unresolved: status is `UNRESOLVED`, not accepted.

---

# V06H5 — Global parent and contour stitching

## 14. Parent atlas work

- cluster projected Sobol seeds before attachment;
- grow new atlas components from unattached projected seeds;
- build component identity from chart-overlap connectivity;
- globally deduplicate vertices in wrapped joint space;
- stitch edges and faces across overlaps;
- distinguish chart-ring boundaries from actual global frontiers;
- retain singular and budget-limited boundaries explicitly.

## 15. Level-set work

- extract contours on the stitched global mesh;
- stitch contour segments across chart seams;
- classify open/closed/boundary/critical status globally;
- continue one branch per global contour component;
- deduplicate continued fibers with symmetric wrapped set distance.

The six current D1 traces remain “discovered traces” until this stitching pass determines whether paired traces at each `c` are distinct components or overlap duplicates.

---

# V06H6 — Closeout

## 16. Required artifacts

```text
results/kinematic_decomposition/v06a2
results/kinematic_decomposition/v06c
results/kinematic_decomposition/v06d1
results/kinematic_decomposition/v06d2
results/kinematic_decomposition/v06e
results/kinematic_decomposition/index.html
results/decomposition_ladder
results/index.html
```

## 17. Closeout questions (ADR-047, 2026-08-15)

Answered without inventing a pass:

1. **Parent completeness:** No. Stitched atlas (ADR-046) is still
   `BUDGET_LIMITED`; unattached Sobol seeds remain; not a closed 2D component.
2. **Source pointing fibers:** Task-derived and H3-continued; seam-stitched
   and deduplicated. Not a complete foliation or a globally identified fiber
   family.
3. **Fixed-axis UUUR vs source fiber:** No. Conjunctive H1 audit still
   `REJECTED` (failed `h_c` and source-to-child distance on the regenerated
   D2 artifact). Chart stays `LOCAL_CANDIDATE`.
4. **Accepted children:** None (`EXACT_*` empty).
5. **Factorization:** `unresolved` for the campaign (empty accepted children
   do not earn `no valid recombination`).
6. **V07A:** Not authorized. Held pending parent/continuation completeness.

```text
current fixed-axis UUUR construction rejected;
broader 5R factorization unresolved;
V07A held pending parent/continuation completion.
```

---

# 18. Branch and commit sequence

```bash
git switch main
git pull --ff-only
git switch -c v06-hardening
```

Recommended commits:

```text
1. docs: define V06 hardening evidence contracts
2. fix(v06d2): require complete local source-fiber equivalence metrics
3. fix(v06e): make zero-population reconstruction metrics unevaluable
4. feat: add shared pseudo-arclength branch continuation
5. refactor(v06): migrate D1 and D2 continuation
6. feat(v06a2): stitch parent components and grow unattached seeds
7. docs/results: regenerate V06 closeout and ladder artifacts
```

Do not commit regenerated results in commits 2–5. Regenerate them once the scientific disposition has stabilized.
