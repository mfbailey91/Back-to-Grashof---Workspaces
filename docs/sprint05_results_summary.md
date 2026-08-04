# Sprint 5 results summary

Source of truth for the numbers below: `results/sprint05_experiments/experiment_summary.json` (regenerated with full ε sweeps, Architecture A workspace seeds + radial grid, `orientation_count=512` coarse).

## Experiment density

| Stratum | Count | Notes |
|---------|------:|-------|
| Total records | 24 | Reconstructible from saved offsets, seed `q`, and resolution |
| Architecture A | 14 | Seed poses + radial grid samples |
| Architecture B | 5 | εw ∈ {0, 0.025, 0.05, 0.10, 0.20} |
| Architecture C | 5 | εs ∈ {0, 0.025, 0.05, 0.10, 0.20} |

Outcome strata (never pooled into ordinary error):

| Outcome | Count |
|---------|------:|
| `false_positive` | 18 |
| `invalid_reduction` | 2 |
| `regional_unreachable` | 4 |
| `agreement` / `false_negative` / `boundary` | 0 |

Observed linkage type in ordinary A/B rows: **type 11** only (crank–crank, hand-crank hypothesis candidate). Confusion FP/FN/agreement are reported per observed type; regional-unreachable and invalid stay outside that table.

## Gates 3–5

| Gate | Metric | Value | Reading |
|------|--------|------:|---------|
| 3 | crank precision | 0.0 | All ordinary A rows are analytical candidates with `strict_sampled_dexterity=false` (false positives under current coverage/component thresholds). |
| 3 | crank recall | — | No true positives and no false negatives among ordinary A rows. |
| 4 | corr(ρ_C, error indicator) on B | — | Undefined: B error indicator is constant across the εw sweep (all rows disagreement or invalid), so Pearson correlation has zero variance. Residual **does** rise with εw while coverage falls — see `residual_vs_error.png` / `offset_sweeps.png`. |
| 5 | C orientation labels stable | true | Every C row keeps `spherical_reduction_status=exact` and none is `invalid_reduction`. Regional status becomes approximate/unreachable as εs grows — regional failure ≠ orientation disagreement. |

## Residual vs prediction error

Architecture B: concurrency residual ρ_C scales roughly as εw/2; spherical status flips to `invalid` by εw ≥ 0.10 in this fixture. Architecture C: ρ_C stays 0 (exact spherical concurrency) while regional reachability fails for εs > 0. Exact / approximate / invalid labels are always retained on each record.

## Caveats

- Product test ≠ dexterity. Types `{2,3,10,11}` remain a hypothesis.
- Fixed-`p` SO(3) coverage is low because many orientations are geometrically ineligible (wrist sphere ∩ regional annulus); prefer eligible solve rate when reading Gate 3.
- Published default is `orientation_count=512`. Use `--fast` (128) for local iteration. Medium/fine remain CLI/stress paths.
