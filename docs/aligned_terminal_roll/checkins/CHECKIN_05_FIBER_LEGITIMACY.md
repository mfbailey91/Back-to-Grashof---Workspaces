# Check-in 05 — Explicit Pointing-Fiber Legitimacy

**Date:** 2026-08-04
**Milestone:** M5 — Fiber legitimacy
**Sprint:** Sprint 05
**Validated source revision:** `9eaf0ff` (implementation); artifacts regenerated at `5afc87a`
**Decision owner:** Michael Bailey
**Decision status:** Approved 2026-08-04 — `CONTINUE WITH CHANGED SCOPE`

## 1. Claim under review

Determine whether an explicit scalar task-space constraint

```text
h(q) = n^T d(q) = c
```

defines a regular, nondegenerate, reproducible one-dimensional local fiber of the fixed-position, fixed-terminal-roll parent on:

1. `IntersectingPairsAligned6R`;
2. `URLikeAligned6R`.

The review distinguishes:

- existence of explicit regular task-space fibers;
- uniqueness or canonicity of the selected fiber;
- architecture-derived fiber selection;
- spherical-four-bar equivalence.

Only the first item is tested in Sprint 05.

## 2. Evidence reviewed

| Experiment | Purpose | Result |
|---|---|---|
| `ATR_EXP_027` | Primary scalar independence | PASS — stacked reduced constraint Jacobian has rank 4/nullity 1 at both seeds; `dh/dq6 = 0` |
| `ATR_EXP_028` | Intersecting-pairs primary fiber | PASS — regular sequential branch, endpoint-based reverse return, noncollapsed pointing image |
| `ATR_EXP_029` | UR-like primary fiber | PASS — same general fiber interface; no imposed `SUUR` requirement |
| `ATR_EXP_030` | Alternate task-space slice and `q2`-freeze control | PASS — alternate slice is regular and reversible; primary slice is distinct from the named joint-frozen path |
| `ATR_EXP_031` | Independent-step refinement | PASS — reverse errors decrease when `Delta sigma` is halved; shared stations remain close |

All decision-bearing artifacts identify a clean source revision.

## 3. Acceptance-criteria results

| Criterion | Required | Observed | Status |
|---|---|---|---|
| Scalar independence | Rank 4/nullity 1 at the seed | Passed on both architectures | PASS |
| Terminal-roll invariance | `dh/dq6 = 0` | Zero within numerical precision | PASS |
| Fiber regularity | Rank 4/nullity 1 along accepted branch | Passed at all accepted samples | PASS |
| Sequential tracking | Predict from previous corrected point | Implemented | PASS |
| Reverse validation | Reverse starts from forward endpoint | Implemented and within configured gates | PASS |
| Position and scalar constraints | Residuals below tolerance | Passed | PASS |
| Pointing image | Noncollapsed with nonzero local tangent | Passed | PASS |
| Alternate task-space slice | Independent and reversible | Passed on both architectures | PASS |
| Coordinate-frozen control | Distinct from primary task-space path | Passed for the tested `q2` freeze | PASS |
| Independent-step refinement | Errors decrease under half-step refinement | Passed on both architectures | PASS |
| Architecture neutrality | UR-like path does not require `SUUR` | Passed | PASS |
| Explicit duplicate scan | No repeated configurations at distinct `sigma` | Deferred to Sprint 06 as the first formal metric | DEFERRED TO S06 |

## 4. Interpretation

**SUPPORTED LOCALLY**

Sprint 05 establishes explicit regular one-dimensional task-space pointing fibers through the named regular seeds of `IntersectingPairsAligned6R` and `URLikeAligned6R`.

For the primary scalar

```text
h(q) = n^T d(q)
n = (0, 1, 0)
```

the stacked reduced constraint Jacobian has rank four and nullity one at both seeds, and terminal roll does not affect the scalar. Sequential continuation produces regular connected local branches with no failed accepted samples, endpoint-based reverse return, and noncollapsed pointing images.

An alternate scalar using

```text
n' = (1, 0, 0)
```

also produces regular reversible fibers. This supports the existence of multiple explicit task-space slices and demonstrates that the primary fiber is not unique.

The `q2`-freeze control establishes only that the primary task-space fiber is distinct from that named joint-coordinate slice. It does not establish that the primary fiber is canonical or architecture-derived.

The meaningful pointing-image test is that the local pointing tangent is nonzero and the image is noncollapsed. Calling a nonzero `3 x 1` derivative “rank one” is mathematically true but is not an independent dimensional discovery.

The supported claim is therefore:

> Explicit regular local task-space pointing fibers exist for the tested architectures, seeds, and scalar directions.

The following remain open:

- whether any fiber is canonical or selected by the architecture;
- whether either tested fiber admits an exact spherical `RRRR`;
- whether failure of one candidate rules out other spherical fibers;
- global branch structure or global pointing coverage;
- exact UR applicability.

## 5. Decision

**`CONTINUE WITH CHANGED SCOPE`**

Authorize Sprint 06 candidate spherical-four-bar tests.

Sprint 06 must treat the primary and alternate task-space fibers as **candidate slices**, not canonical fibers.

The controlled test matrix should include:

| Architecture | Primary fiber `n=(0,1,0)` | Alternate fiber `n'=(1,0,0)` |
|---|---:|---:|
| `IntersectingPairsAligned6R` | Required | Required |
| `URLikeAligned6R` | Required parallel comparison | Required parallel comparison |

For each candidate, test in order:

1. explicit duplicate-configuration scan over the accepted fiber segment;
2. branch-wide candidate-axis concurrency;
3. fixed spherical arc dimensions;
4. inactive-coordinate locking, where applicable;
5. local tangent equivalence;
6. continued-motion equivalence.

McCarthy–Soh classification remains blocked until a candidate passes every spherical-mechanism prerequisite.

Failure of one candidate fiber means only:

> The selected task-space slice is not an exact spherical `RRRR`.

It does not establish that no spherical fiber exists for the architecture.

## 6. Required project updates

### Assumption A09

Replace “a nonarbitrary scalar fiber constraint exists” with:

> Explicit regular task-space fiber constraints exist locally for the tested primary and alternate slices. A canonical or architecture-derived fiber remains open.

### Risk R06

Record that the tested task-space fibers are distinct from one named joint-coordinate freeze, while canonical fiber selection remains unresolved.

### Metric language

Sprint 05 closeout renamed `local_rank_one` to `local_pointing_tangent_nonzero` and retained the noncollapse metric. An explicit pairwise duplicate-configuration report remains a Sprint 06 first metric.

These are interpretation and closeout corrections; they do not invalidate Sprint 05.

## 7. Method comprehension review

### Claim being tested

A scalar level set of the two-dimensional pointing parent can define a regular one-dimensional local branch.

### Plain-language implementation

Add one task-space scalar constraint to the fixed-position, fixed-roll system. Follow the remaining null direction with sequential predictor-corrector continuation.

### Why the method tests the claim

Five active joint coordinates are constrained by three position equations and one independent scalar equation. At a regular sample, rank four leaves one local tangent direction.

### Standard numerical machinery

- Jacobian rank by SVD;
- null-space tangent extraction;
- Newton/pseudoinverse correction;
- sequential continuation;
- endpoint-based reverse validation;
- step-size refinement.

### Project-specific modeling decisions

- quotient terminal roll;
- choose `h(q)=n^T d(q)`;
- select the world-frame vectors `n` and `n'`;
- treat these level sets as candidate fibers.

### Known ways the method could mislead us

- treating an arbitrary explicit slice as canonical;
- interpreting one failed slice as nonexistence of all spherical fibers;
- treating a nonzero `3 x 1` derivative rank as independent evidence;
- overlooking repeated configurations at different fiber parameters;
- inferring spherical closure before branch-wide invariants pass.

## 8. Next sprint recommendation

Create Sprint 06 as a candidate spherical-equivalence sprint.

The Sprint 06 exit decision must distinguish:

1. accepted exact spherical `RRRR` candidate;
2. instantaneous or approximate spherical resemblance only;
3. rejected candidate fiber;
4. unresolved candidate due to numerical or branch limitations.

The terminal-roll reduction and local fiber-existence results remain valid regardless of the Sprint 06 outcome.
