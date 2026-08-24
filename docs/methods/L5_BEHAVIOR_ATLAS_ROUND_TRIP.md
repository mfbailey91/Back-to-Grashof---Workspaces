# L5 Behavior Atlas Round-Trip Program

**Status:** PROPOSED ACTIVE R3C program; A0 infrastructure may land before the R3A scientific gate
**Project:** Characterization of Manipulator Workspaces by Kinematic Decomposition
**Scope:** Source-derived 5R pointing children and family-specific numerical behavior atlases

---

## 1. Decision

Build the first spatial mechanism atlas as a **round trip**:

\[
\boxed{
5R\ \text{parent}
\rightarrow
\text{source-derived child corpus}
\rightarrow
\text{family support}
\rightarrow
\text{exact child behavior}
\rightarrow
\text{numerical atlas}
\rightarrow
5R\ \text{reconstruction}
}
\]

The program is intentionally asymmetric:

1. **Manipulator → mechanism first** discovers which child families and which regions of each family actually arise from the fixed-position decomposition.
2. **Mechanism → atlas second** fills, refines, and stress-tests those source-derived regions using direct mechanism parameterization.
3. **Atlas → manipulator last** replaces expensive exact child behavior with the atlas and tests whether parent pointing reconstruction is preserved.

This ordering prevents a large standalone four-bar library from becoming workspace evidence merely because the mechanisms are mathematically valid.

---

## 2. Scientific question

After a source-derived natural-leaf reconstruction succeeds, can the behavior of those one-DOF children be compressed into family-specific numerical predicates without losing the parent workspace result?

The first target is L5 pointing:

\[
\mathcal D(p^*)
=
\{d(q):q\in \mathcal P_{p^*}\}
\subseteq S^2.
\]

The atlas is not itself the workspace. It is a replaceable evaluator used inside an already validated decomposition-and-stitching chain.

---

## 3. Three independent truth layers

The program keeps three references separate.

### 3.1 Parent reference

A decomposition-free source-chain solve estimates

\[
\mathcal D_{\mathrm{direct}}(p^*).
\]

This answers what the 5R source manipulator can point at.

### 3.2 Exact child reference

For each frozen source-derived child geometry \(C\), direct continuation / exact mechanism analysis produces a behavior record

\[
B_{\mathrm{exact}}(C).
\]

This answers how the actual child behaves.

### 3.3 Atlas surrogate

A family-conditioned numerical atlas predicts

\[
B_{\mathrm{atlas}}(C).
\]

This is allowed to return `UNRESOLVED` / out-of-distribution and fall back to the exact child solver.

The comparisons are therefore:

\[
B_{\mathrm{atlas}}(C)
\stackrel{?}{\approx}
B_{\mathrm{exact}}(C)
\]

and

\[
\widehat{\mathcal D}_{\mathrm{exact-child}}(p^*)
\stackrel{?}{\approx}
\mathcal D_{\mathrm{direct}}(p^*)
\]

and finally

\[
\widehat{\mathcal D}_{\mathrm{atlas-child}}(p^*)
\stackrel{?}{\approx}
\mathcal D_{\mathrm{direct}}(p^*).
\]

These comparisons localize failure rather than collapsing the whole theory into one pass/fail number.

---

## 4. Family identity is structural

The decomposition determines the child family.

A child is not matched to the nearest atlas by geometric similarity. The pipeline is:

```text
source parent
  -> exact reduction
  -> exact child family identity
  -> family-specific canonicalization
  -> family-specific atlas lookup
```

For example:

```text
SURU -> UURU
```

is a structural source-to-child map.

If a later source reduction emits `URUU`, it enters the `URUU` family program. If no atlas exists, the result is `UNRESOLVED` and the exact child solver remains available.

The atlas must retain both:

```text
joint_kind_sequence
joint_role_sequence
```

so role-aware identities are not collapsed into letter-string topology.

---

## 5. Data layers

Do not mix extraction, descriptors, behavior labels, and workspace claims.

### Layer E0 — Source-derived extraction record

Stores:

```text
record_id
family identity
source chain
fixed-position problem
source component
probe / task point
construction kind
chart
family-coordinate values
full frozen geometry
geometry hash
child certificate status
accepted-for-reconstruction flag
source artifact reference
```

No descriptor vector is required at E0.

### Layer E1 — Canonical descriptor record

A later family-specific canonicalizer maps frozen geometry to

\[
\xi_F(C).
\]

The canonicalizer must explicitly remove only justified symmetries such as rigid frame choice or uniform scale. It must not erase task roles, designated coordinates, circuit identity, or component information needed by the behavior certificate.

### Layer E2 — Exact behavior record

The exact child solver emits the R1-compatible mechanism behavior certificate. The atlas target is not assumed to be a single crank/non-crank bit.

Candidate fields may include:

```text
assemblability
component / circuit
designated-coordinate winding or rotation
return / closure status
range / interval
branch count
singular boundaries
uncertainty / numerical scope
```

The actual target schema is frozen only after exact-child behavior is audited.

### Layer E3 — Atlas prediction record

Stores:

```text
family
descriptor schema
query point
predicted behavior
confidence / local support
OOD status
fallback required
atlas version
training-support provenance
```

### Layer E4 — Parent substitution evidence

Records whether replacing exact child evaluation with atlas evaluation preserves the stitched parent task image.

---

## 6. Source support before broad mechanism sampling

For each accepted or diagnostic 5R parent campaign, extract every legitimate child and form the empirical support

\[
\mathcal M_F^{5R}
=
\{\xi_F(C):C\ \text{arose from a 5R source reduction}\}.
\]

Direct four-bar sampling then covers:

1. the observed source-derived support;
2. a controlled margin around that support;
3. behavior-transition boundaries;
4. explicitly chosen stress regions.

The first campaign does **not** attempt to uniformly cover the complete mathematical parameter space of every U/R four-bar topology.

That broader program remains downstream.

---

## 7. The effective-dimension test

The source-derived child cloud may occupy a lower-dimensional subset of the mathematical family space.

If a nominal family descriptor is

\[
\xi\in\mathbb R^n
\]

but 5R-derived children satisfy constraints

\[
f_i(\xi)=0,
\]

then the workspace-relevant atlas should first characterize the embedded support manifold rather than waste compute on unreachable combinations.

This is a scientific result, not merely an optimization. It may expose the special subfamilies for which compact Grashof-like conditions are possible.

---

## 8. Falsification logic

The program must preserve an eject button.

### Failure F1 — Exact-child reconstruction fails

If exact source-derived child behavior is correct but accepted exact children do not reconstruct the direct 5R parent:

```text
direct child behavior: PASS
exact-child parent reconstruction: FAIL
```

then the atlas is not the problem.

The decomposition / family completeness / compatibility / stitching theory is incomplete.

### Failure F2 — Atlas child prediction fails

If exact-child reconstruction passes but atlas-backed reconstruction fails:

```text
exact-child parent reconstruction: PASS
atlas-child parent reconstruction: FAIL
```

then the decomposition survives and the surrogate is inadequate.

Improve descriptors, sampling, labels, confidence, or fallback.

### Failure F3 — Transfer fails outside the positive control

If R3A passes but source-derived families or stitching fail systematically on held-out 5R architectures, do not proceed to L6 as though the L5 result generalized.

Document the architecture boundary or revise the decomposition hypothesis.

### Failure F4 — Atlas is not computationally useful

If reliable atlas prediction requires nearly the same work as direct child continuation, retain the exact numerical predicate. Scientific structure may still be valid even if the surrogate offers no speed advantage.

---

## 9. Sprint sequence

### R3C-A0 — Provenance and extraction contract

**Goal:** Establish the round-trip authority, typed extraction records, immutable geometry payload contract, and tests.

**No science claim. No parameter sweep. No descriptors.**

**Pass:** A source-derived, candidate, or explorer-only mechanism can be represented without conflating provenance or workspace eligibility.

Detailed execution: `R3C_A0_BEHAVIOR_ATLAS_CONTRACT.md`.

### R3C-A1 — Manipulator → mechanism exporter

**Goal:** Export R3A/R3B natural leaves into E0 records.

Required change: natural-leaf artifacts must include the full frozen mechanism geometry, not only a geometry hash.

**Pass:** Every exported mechanism can be reconstructed byte-for-byte / numerically from its stored geometry payload, with source provenance and family identity intact.

### R3C-A2 — Parent campaign and raw child corpus

**Goal:** Generate a controlled bank of 5R geometries and Cartesian points and collect source-derived children.

Start with:

```text
R3A positive control
exact_two_u_5r
generic_5r
near-architecture controls
```

Do not silently assume every source produces UURU.

**Pass:** Family counts, source-component counts, acceptance status, and raw geometry distributions are reproducible from frozen configs.

### R3C-A3 — Family canonicalization and support geometry

**Goal:** Define family-specific invariant descriptors only for families actually emitted with useful support.

Tasks:

```text
rigid-frame invariance
scale normalization
role-preserving canonical ordering
degeneracy handling
descriptor invertibility / reconstruction audit
effective-dimension analysis
```

**Pass:** Canonical descriptors are stable under declared symmetries and retain distinctions required by behavior certificates.

### R3C-A4 — Exact child behavior oracle

**Goal:** Freeze the expensive direct behavior evaluator used to label mechanisms.

**Pass:** Repeated continuation / refinement gives stable behavior records on a calibration corpus; unresolved cases remain unresolved rather than forced.

### R3C-A5 — Directed atlas builder

**Goal:** Sample family parameter space around source-derived support and refine behavior boundaries.

Sampling policy:

```text
interior low-discrepancy coverage
source-density-aware coverage
boundary refinement
controlled support margin
stress / degeneracy probes
```

**Pass:** Atlas stores support, confidence, OOD status, and exact fallback routing.

### R3C-A6 — Held-out child validation

**Goal:** Compare atlas behavior against exact child behavior on frozen mechanisms never used to build the atlas.

**Pass:** Predeclared classification / range / boundary metrics pass; no OOD mechanism is silently forced.

### R3C-A7 — Held-out parent substitution

**Goal:** Reconstruct new 5R pointing parents twice:

```text
exact child behavior -> stitching
atlas child behavior -> stitching
```

and compare both against direct source-chain \(S^2\) truth.

**Pass:** Atlas substitution preserves the parent result within declared error and false-positive limits.

### R3C-A8 — Closeout / L6 decision gate

Classify the outcome:

```text
A: decomposition + atlas transfer
B: decomposition transfers; atlas rejected / exact fallback retained
C: positive-control-only architecture result
D: decomposition/stitching hypothesis requires revision
```

Only A or B provide a strong basis to invest in the aligned-roll L6 program. C requires an explicit architecture-scoped decision. D is the eject condition.

---

## 10. Initial implementation boundary

A0 may land while R3A is still closing because it changes only data authority and infrastructure.

However:

- no extracted child is workspace evidence unless its source certificate allows it;
- no family atlas is promoted before an exact behavior target exists;
- no atlas is a workspace method before parent reconstruction succeeds;
- explorer-only mechanisms remain laboratory data;
- the current R3A `SURU -> UURU` positive control is not generalized by this program document.

---

## 11. L6 relationship

The aligned terminal-roll 6R hypothesis remains downstream:

\[
5R_{\mathrm{pointing}}
+
R_{\mathrm{roll}}
\rightarrow
SO(3)
\]

subject to the existing quotient and component requirements.

The purpose of R3C is to reach L6 with a tested answer to a narrower question:

> Can lower-dimensional source-derived mechanism behavior predict the 5R pointing parent, and can that behavior be evaluated by a conservative numerical atlas?

This makes L6 a test of the pointing-to-orientation lift rather than a simultaneous test of every lower-rung assumption.

---

## 12. Nonclaims

This program does not assert:

- every 5R manipulator admits the same child topology;
- UURU is the universal 5R child;
- the observed source-derived support equals the full mathematical family space;
- crank/rocker alone is the correct atlas label;
- a chart-specific child behavior is a chart-invariant workspace predicate;
- a numerical atlas is an analytical Grashof theorem;
- R3A positive-control success implies generic 5R success;
- pointing plus roll is globally the trivial product \(S^2\times S^1\).

The program exists to test these boundaries rather than assume them.
