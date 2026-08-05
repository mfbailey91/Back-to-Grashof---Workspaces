# Assumption and Risk Register — Aligned Terminal-Roll Reduction

**Review cadence:** Every formal check-in
**Status values:** `OPEN`, `VERIFIED`, `CONSTRAINED`, `REJECTED`, `MITIGATED`, `ACCEPTED`

## 1. Research assumptions

| ID | Assumption | Type | Verification method | Consequence if false | Status |
|---|---|---|---|---|---|
| A01 | Selected task point lies on `R6` | geometric | axis-distance test | terminal joint changes position | VERIFIED |
| A02 | Selected tool direction is parallel to `R6` | task definition | angular residual | terminal joint changes pointing | VERIFIED |
| A03 | `R6` has usable roll range | architecture | joint-range review at later stage | full orientation may remain incomplete | OPEN |
| A04 | Regular 6R fixed-position set has dimension 3 | mathematical | `J_p` SVD survey | reduction premise changes locally | VERIFIED |
| A05 | Terminal roll is the only kernel direction of `(p,d)` at regular poses | mathematical | `J_pd` SVD and kernel alignment | additional self-motion or degeneracy exists | VERIFIED |
| A06 | Reduced pointing tangent has rank 2 | mathematical | `rank(J_d N_red)` | local pointing coverage degenerates | VERIFIED |
| A07 | Two intersecting physical axis pairs admit a useful compound-joint representation | modeling | explicit coordinate-map, closure equivalence, pair persistence, and negative control | `SUUR`/related shorthand rejected | CONSTRAINED (local φ definedness and pair persistence only; not an independent SUUR mechanism solver) |
| A08 | UR-like ordering preserves the reduction | architecture | synthetic comparison | result is narrower than typical UR-like arms | CONSTRAINED (Stage A and local C10 patch on synthetic UR-like only; not exact UR) |
| A09 | Explicit regular task-space fiber constraints exist locally; a canonical or architecture-derived fiber may exist | research | constrained rank, primary and alternate task-space slices, endpoint reverse, refinement, and joint-freeze control | candidate spherical-fiber testing may proceed, but no tested slice may be treated as canonical | CONSTRAINED (primary and alternate task-space fibers verified locally; canonical or architecture-derived selection remains OPEN) |
| A10 | A useful fiber has four globally concurrent axes | research | branch-wide concurrency residual | spherical `RRRR` rejected |
| A11 | Spherical arc dimensions remain fixed | research | branch-wide angular invariants | only instantaneous quadrilateral exists |
| A12 | McCarthy-Soh rotatability maps to required pointing motion | research | compare against continued motion | Grashof classifier rejected for this use |
| A13 | Exact UR geometry satisfies the chosen aligned task definition | architecture | exact model audit | synthetic result requires special tooling or a different robot |

## 2. Project and software risks

| ID | Risk | Likelihood | Impact | Mitigation | Trigger | Status |
|---|---|---:|---:|---|---|---|
| R01 | Frame convention creates a false positive | Medium | High | freeze conventions; positive and negative controls | control behaves unexpectedly | MITIGATED |
| R02 | Rank threshold misclassifies near-singular cases | High | High | publish singular values; threshold sensitivity | conclusion changes with threshold | MITIGATED |
| R03 | Finite-difference scale masks implementation error | Medium | Medium | multi-step convergence study | no stable error plateau | MITIGATED |
| R04 | Transform-order bug preserves one fixture accidentally | Medium | High | independent geometric and numerical oracles | analytical/numerical disagreement | MITIGATED |
| R05 | Continuation jumps branches | High | High | sequential PC, transported frames, true reverse, loop/alternate-path, duplicate scan | discontinuous configuration jump | MITIGATED (Sprint 04B local sequential reverse/loop/duplicate gates; global branching still open) |
| R13 | Macro-grid consistency is read as independent refinement | High | High | ATR_EXP_024 labeled shared-microstep consistency; ATR_EXP_025 is the step-refinement gate | 024 exact Δq=0 treated as numerical convergence study | MITIGATED (Sprint 04C) |
| R14 | Alternate-path residual is read as proven holonomy | Medium | High | 026 uses stable-or-decreased language; holonomy not claimed | loop/alt residuals cited as geometric theorems | MITIGATED (Sprint 04C) |
| R06 | Coordinate fixing creates an artificial or privileged-looking fiber | High | High | use explicit task-space constraints, compare primary and alternate slices, retain joint-freeze negative control, and avoid canonical language | one chosen slice is treated as architecture-derived without evidence | CONSTRAINED (tested task-space fibers are regular and distinct from the named `q2` freeze; canonical selection remains unresolved) |
| R07 | Mobility count is mistaken for equivalence | Medium | High | require discriminating coordinate-map and continued-motion tests | matching count but mismatched motion | MITIGATED (negative control plus φ definedness; independent SUUR solver still absent) |
| R08 | Spherical candidate passes only at one pose | High | High | branch-wide concurrency and arc tests | residual grows under continuation | OPEN |
| R09 | Spatial work destabilizes planar v0.2 | Low | High | isolated package and tests; no planar API edits | planar regressions | MITIGATED |
| R10 | Scope expands into URDFs before reduction is established | Medium | Medium | milestone authorization gates | exact robot work begins before M5/M7 | OPEN |
| R11 | Results are not reproducible from chat history | Medium | High | experiment registry and manifests | missing command, seed, or parameters | MITIGATED |
| R12 | Negative result is treated as project failure | Medium | Medium | define obstruction-finding as valid outcome | pressure to skip failed gate | OPEN |

## 3. Escalation rules

Immediately stop the current stage when:

- a prerequisite geometric condition is not actually satisfied;
- the result changes qualitatively under reasonable numerical refinement;
- a later-stage mechanism label is being used before its defining tests pass;
- a local observation is being interpreted as global coverage;
- an experiment cannot be reproduced from its manifest.

A stopped stage must produce either a corrective sprint or a decision record closing the branch.
