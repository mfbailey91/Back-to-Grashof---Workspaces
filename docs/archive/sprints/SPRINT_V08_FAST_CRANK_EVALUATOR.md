> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# Sprint V08 — Fast Crank Evaluator

> **Superseded sprint number:** retained as deferred **V13 conservative fast
> evaluator**. Active V08 verifies the aligned terminal-roll quotient and
> constructs task-derived one-dimensional four-bar children.

**Historical status:** planned after V07 Gate B
**Purpose:** provide a computationally efficient and conservative crank-capability evaluator whether the underlying family is governed by a compact candidate rule or requires a numerical surrogate atlas.

## Research question

Can a spatial four-bar query be classified much faster than full continuation while preserving agreement with the exact numerical solver and explicitly refusing uncertain / out-of-distribution cases?

## Two supported evaluator paths

### Path A — rule-backed
For families with strong V07 rules:

```text
canonical geometry -> descriptors -> g_F(x) -> class + margin
```

### Path B — numerical-atlas-backed
For families without a reliable compact rule:

```text
canonical geometry -> descriptor vector -> sparse atlas / local surrogate -> class + confidence
```

The two paths should expose the same external query/result contract.

## Atlas construction

Avoid a dense Cartesian grid. Use:

1. Sobol or Latin-hypercube coverage;
2. exact continuation labels;
3. adaptive densification near class boundaries and low-confidence regions;
4. sparse coverage inside uniform regions;
5. canonicalization from V04C before similarity lookup.

Separate atlases by ordered family unless V07 proves a valid equivalence.

## Query result contract

Return at least:

```text
family
predicted class
winding capability if predicted
coverage estimate if available
confidence / distance-to-data
boundary margin
in_distribution
source = analytical_rule / numerical_atlas / exact_fallback
```

Allowed result states must include:

```text
crank
rocker
change_point / boundary
no_assembly
uncertain
out_of_distribution
```

## Hybrid active-learning fallback

```text
query geometry
   -> fast evaluator
   -> high confidence? yes -> accept
                      no  -> exact continuation
                              -> return exact result
                              -> optionally add to atlas
```

Never force an uncertain query into a binary class.

## Benchmark campaign

Measure:

- exact continuation runtime;
- fast-evaluator runtime;
- speedup;
- class agreement on held-out mechanisms;
- false crank / false rocker rates;
- rejection / OOD rate;
- performance near class boundaries.

Benchmark by family and by outcome class.

## Deliverables

- common crank-evaluator API;
- rule-backed adapters where justified;
- sparse numerical atlas / surrogate for remaining families;
- exact-solver fallback;
- confidence and OOD logic;
- held-out benchmark corpus;
- speed / accuracy plots;
- boundary and rejection diagnostics;
- `sprint_08_fast_crank_evaluator.html`.

## Acceptance

V08 passes when:

1. fast evaluation is materially faster than exact continuation on the benchmark corpus;
2. class agreement is quantified on held-out data;
3. uncertain/OOD cases are rejected rather than guessed;
4. exact fallback is callable through the same interface;
5. false-positive crank claims are separately reported;
6. the evaluator preserves provenance showing whether the answer came from a rule, atlas, or exact solver.

## Non-goal

V08 still does not establish that the virtual mechanism predicts robot dexterity. That is V09.
