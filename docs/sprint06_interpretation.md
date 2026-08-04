# Sprint 6 interpretation

Static-but-interactive inspector over precomputed Sprint 5 experiment records
(`results/sprint06_dashboard/`). No live IK in the browser; εw/εs sliders filter
saved Architecture B/C rows client-side.

Companion numbers: [`docs/sprint05_results_summary.md`](sprint05_results_summary.md)
and `results/sprint05_experiments/experiment_summary.json`.

## Results summary

- Architecture A reductions remain exact; observed spherical type is **11**
  (hand-crank hypothesis candidate) on every ordinary classified row.
- Numerical `strict_sampled_dexterity` is false across the densified A grid under
  current coverage/component thresholds → Gate 3 precision 0, recall undefined.
- Architecture B: ρ_C grows with εw; spherical status becomes `invalid` for larger
  wrist offsets (εw ≥ 0.10 in the published fixture).
- Architecture C: spherical concurrency stays exact while regional reachability
  fails as εs increases (`regional_unreachable` stratum) — Gate 5 holds.
- Regional-unreachable and invalid_reduction are never counted as ordinary
  prediction error.

## Gates 1–5 status

| Gate | Question | Status |
|------|----------|--------|
| 1 | Spherical closure well-defined? | **Pass** (Sprint 0 worked Architecture A closure; McCarthy–Soh types implemented). |
| 2 | Numerical orientation labels trustworthy enough to proceed? | **Pass** (Sprint 4 Gate-2 convergence badge on Architecture A). |
| 3 | Hand-crank subset predictive on A? | **Open / weak** — densified run yields only false positives under strict sampled dexterity; eligible solve rates are moderate but product≠dexterity. |
| 4 | Error scale with residual (B)? | **Inconclusive metric, clear trend** — Pearson corr undefined (constant error indicator); residual and coverage plots show monotonic degradation with εw. |
| 5 | Regional separable from orientation (C)? | **Pass** — spherical exact throughout; regional failure labeled separately. |

## Limitations

- No joint limits, collision, dynamics, or URDF models (Sprint 01 / stretch scope).
- Published orientation count is coarse 512, not fine (~50k).
- Strict sampled dexterity thresholds remain research knobs; low SO(3) coverage at
  fixed \(p\) is partly geometric (wrist sphere ∩ regional annulus), not only solver miss.
- Confusion table currently observes type 11 only — other hypothesis types are not
  exercised by the synthetic fixture.
- Formal crank ⇒ SO(3) proof is out of scope; hypothesis types `{2,3,10,11}` are not
  encoded as truth.

## Next steps (forward pointers only)

- Optional medium/fine stress sampling for Gate-2 sensitivity.
- Broader Architecture A type maps (vary DH angles) if Gate 3 needs non-type-11 cases.
- Stretch: capability metrics, commercial robots, limits/collision — not part of this sprint.
