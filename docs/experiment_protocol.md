# Experiment protocol (Sprints 4–5)

Numerical orientation ground truth and architecture comparison. Complements
[`docs/theory.md`](theory.md), [`docs/spherical_reduction.md`](spherical_reduction.md),
and [`docs/MATH_NOTES.md`](MATH_NOTES.md) §9.

## 1. Separation of claims

- Analytical McCarthy–Soh labels are **predictions**, never ground truth.
- Numerical coverage and connectivity are **estimates** under a fixed sample set.
- Solver failure is **not** geometric non-reachability.
- Exact / approximate / invalid reductions must never be pooled without labels.
- Product \(T_1 T_2 T_3 T_4 > 0\) is never treated as dexterity.
- Hand-orientation link default remains output \(\beta\); types `{2,3,10,11}` are a hypothesis.

## 2. \(SO(3)\) sampling

Deterministic Hopf-coordinate unit quaternions with a fixed integer seed:

| Resolution | Target count |
|------------|--------------|
| coarse     | ~500         |
| medium     | ~5,000       |
| fine       | ~50,000      |

Committed figures and default dashboards use coarse and medium. Fine is a
`stress` / CLI path. The same `(seed, resolution)` pair must reproduce the
identical orientation list.

## 3. IK failure taxonomy

For each target pose \((p, R)\):

| Status           | Meaning |
|------------------|---------|
| `solved`         | Residual below tolerance; configuration retained |
| `unreachable`    | Geometric precheck fails (e.g. wrist center outside regional annulus for Architecture A) |
| `solver_failed`  | Precheck passes (or unavailable) but multi-start numerical IK did not converge |

Never record `solver_failed` as evidence of orientation non-capability without noting the taxonomy.

## 4. Coverage and connectivity

At fixed Cartesian \(p\):

\[
C(p)=\frac{\#\{\text{solved orientations}\}}{\#\{\text{sampled orientations}\}}.
\]

Build an adjacency graph over **solved** samples: connect two samples if their
geodesic distance on \(SO(3)\) is below a neighbor radius (fraction of median
nearest-neighbor distance). Report:

- `orientation_coverage` \(= C(p)\);
- `orientation_component_count`;
- `strict_sampled_dexterity` — high coverage **and** a single large connected component (thresholds in code / configs);
- solver status histogram.

## 5. Gate 2 (before Sprint 5 interpretation)

Coarse → medium → fine aggregate metrics must stabilize. If medium coverage and
component counts diverge sharply from coarse, treat numerical labels as
unverified and do not interpret Architecture B/C conjecture tests.

## 6. Sprint 5 comparison

Join each fixed-position numerical record with `predict_orientation_capability`:

- `prediction_outcome`: agreement / false_positive / false_negative / regional_unreachable / invalid_reduction / boundary;
- never count \(T_i \approx 0\) boundary states as ordinary model error;
- stratify by `spherical_reduction_status`.

Gates 3–5:

- **Gate 3:** Does the hand-crank subset `{2,3,10,11}` show predictive value on Architecture A?
- **Gate 4:** Does prediction error scale with \(\epsilon_w\) (Architecture B)?
- **Gate 5:** Does Architecture C keep orientation labels meaningful while regional status degrades?
