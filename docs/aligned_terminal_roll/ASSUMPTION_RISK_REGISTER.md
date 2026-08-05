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
| A07 | Two intersecting physical axis pairs admit a useful compound-joint representation | modeling | tangent and continuation comparison | `SUUR`/related shorthand rejected | CONSTRAINED (local tangent / short steps only; continuation still open) |
| A08 | UR-like ordering preserves the reduction | architecture | synthetic comparison | result is narrower than typical UR-like arms | CONSTRAINED (Stage A on synthetic UR-like only; not exact UR) |
| A09 | A nonarbitrary scalar fiber constraint exists | research | constrained-rank and coordinate-invariance tests | spherical-fiber program stops |
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
| R05 | Continuation jumps branches | High | High | predictor-corrector diagnostics, reverse runs, branch IDs | discontinuous configuration jump | OPEN |
| R06 | Coordinate fixing creates an artificial fiber | High | High | prefer task-space constraint; compare parameterizations | fiber disappears under reparameterization | OPEN |
| R07 | Mobility count is mistaken for equivalence | Medium | High | require tangent and continued-motion tests | matching count but mismatched motion | MITIGATED (local principal-angle and step probes; global continuation still open) |
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
