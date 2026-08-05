# Sprint 04C — Bounded Implementation and Method Audit

**Sprint status:** Complete — Check-in 04C approved Pass  
**Milestone target:** Close implementation-review debt before Check-in 4B approval  
**Authorized by:** Pre-approval amendment to Sprint 04B (before human Check-in 4B review)  
**Timebox:** One bounded audit cycle  
**Scope rule:** Review and clarify existing implementation; do not add fiber, spherical-four-bar, exact-UR, or broad refactoring work.

## 1. Objective

Make the aligned-terminal spatial implementation understandable, traceable, and clean enough to support a honest Check-in 4B decision without allowing the audit to become a general codebase rewrite.

This sprint will:

1. document how the decision-bearing algorithms are implemented;
2. explain why those implementations are valid for the claims being tested;
3. connect major methods to references, tests, and experiments;
4. correct misleading Sprint 04B experiment descriptions;
5. remove or clearly label stale, tautological, or developer-only validation paths;
6. preserve all accepted Sprint 04B numerical behavior.

## 2. Required corrections

### ATR_EXP_024 — Grid and step-size consistency

Revise the interpretation to state:

> Baseline and fine grids agree exactly at shared coordinates because both resolve to the same internal `0.005` continuation microstep sequence. This establishes deterministic consistency between the two macro-grid descriptions, but it is not an independent numerical-refinement result.

Retain ATR_EXP_025 as the primary step-refinement evidence.

### ATR_EXP_026 — Alternate-path sensitivity

Replace language claiming discrepancy reduction with:

> No duplicate solutions were detected. Alternate-path discrepancies remain small and stable under the tested refinement. The results are compatible with finite-path noncommutativity of the transported chart, but do not independently establish geometric holonomy.

Rename any field such as:

```text
discrepancy_decreased
```

to:

```text
discrepancy_stable_or_decreased
```

Update the experiment pass predicate and documentation to match the actual criterion.

## 3. Work packages

### WP1 — Implementation inventory

Create a compact map of:

- decision-bearing modules and functions;
- associated mathematical claims;
- tests and experiment IDs;
- architecture-independent versus architecture-specific logic;
- developer-only diagnostics.

### WP2 — Implementation rationale

Create:

```text
docs/aligned_terminal_roll/IMPLEMENTATION_RATIONALE.md
```

For each major method, record:

- what it computes;
- why it is appropriate;
- validity conditions;
- independent checks;
- conclusions it does and does not authorize.

Cover at minimum:

- product-of-exponentials forward kinematics;
- position and pointing Jacobians;
- SVD rank and null-space calculations;
- terminal-roll quotient;
- predictor-corrector continuation;
- tangent-frame alignment;
- configuration-chart rank;
- pointing-chart rank;
- duplicate and refinement diagnostics.

### WP3 — Method references

Create:

```text
docs/aligned_terminal_roll/METHOD_REFERENCES.md
```

Use a short curated list grouped by method. For each reference, state where and how it is used in the repository.

Do not add citations to every helper function.

### WP4 — Test and terminology review

Review for:

- tautological or non-discriminating tests;
- expected values derived from the implementation under test;
- permissive pass predicates;
- silent filtering of failed samples;
- topology-imposing language;
- claims stronger than the evidence.

Correct misleading uses of:

- `SUUR`;
- “closure equivalence”;
- “global”;
- “exact”;
- “holonomy”;
- “refinement.”

### WP5 — Bounded cleanup

Clean only issues identified by the audit:

- duplicate validation logic;
- stale Sprint 03/04 comparison paths;
- architecture-specific code leaking into general APIs;
- obsolete experiment labels;
- missing or inconsistent result provenance;
- unclear major-function docstrings.

Do not change APIs only for style.

### WP6 — Revalidation

Run:

- full planar tests;
- full spatial tests;
- ATR_EXP_021–026;
- any experiment affected by corrected predicates or terminology;
- clean-source provenance checks.

Regenerate decision-bearing artifacts when behavior or stored fields change.

## 4. Deliverables

```text
docs/aligned_terminal_roll/
    IMPLEMENTATION_RATIONALE.md
    METHOD_REFERENCES.md

docs/aligned_terminal_roll/checkins/
    CHECKIN_04C_IMPLEMENTATION_METHOD_AUDIT.md
```

Also update:

- ATR_EXP_024 documentation and summary;
- ATR_EXP_026 code, field names, documentation, and summary;
- affected tests and generated artifacts;
- risk register entries related to branch tracking, numerical interpretation, and provenance.

## 5. Acceptance criteria

Sprint 04C passes when:

1. Every decision-bearing algorithm has a plain-language rationale.
2. Every major numerical method has a traceable reference or is identified as a project-specific construction.
3. Validity conditions and independent checks are documented.
4. ATR_EXP_024 is described as deterministic macro-grid consistency, not independent refinement.
5. ATR_EXP_026 uses `stable_or_decreased` language and a matching pass predicate.
6. Tautological or non-discriminating tests are labeled, replaced, or removed.
7. General continuation APIs do not impose architecture-specific topology.
8. Decision-bearing results identify a clean source revision.
9. No accepted Sprint 04B conclusion changes without an explicit defect record.
10. All planar and spatial tests pass.
11. Fiber, spherical-four-bar, and exact-UR work remain unimplemented.
12. Check-in 04C explicitly authorizes or blocks Sprint 05 pending human review of 4B+04C.

## 6. Check-in 04C decision

### Pass

Authorize Sprint 05 — explicit one-dimensional fiber definition and continuation — after human approval of Check-in 4B together with this audit.

### Conditional pass

Authorize Sprint 05 only after named documentation or low-risk cleanup items are completed.

### Fail

Run a corrective implementation sprint before fiber work.

## 7. Explicitly deferred

- selection of `h(q)=c`;
- fiber continuation;
- spherical concurrency and fixed-arc tests;
- spherical `RRRR`;
- McCarthy–Soh classification;
- exact UR or URDF integration;
- broad codebase rearchitecture;
- HTML diagnostic polish.
