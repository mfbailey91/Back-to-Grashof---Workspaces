# Sprint 04 — Pointing Manifold

**Sprint status:** Implementation complete / Check-in 4 draft
**HTML readout:** `results/aligned_terminal_roll/sprint04_readout/index.html`
**Milestone target:** M4 — Two-dimensional pointing surface (local patch)
**Check-in:** Check-in 4 (draft; not auto-approved)
**Authorized by:** Check-in 3 (`CONTINUE WITH CHANGED SCOPE`, 2026-08-04)
**Timebox:** Discriminating SUUR tests plus physical 6R predictor-corrector continuation; no fibers

## 1. Sprint objective

Produce a local two-dimensional fixed-position pointing patch on `IntersectingPairsAligned6R` (then the same interface on `URLikeAligned6R`), and replace non-discriminating compound-tangent tests with an explicit SUUR coordinate map, pair persistence, and a nonintersecting negative control.

## 2. Hypothesis under test

1. `φ(θ; q6*)=(θ, q6*)` is defined exactly when `R1∩R2` and `R3∩R4` persist.
2. On `IntersectingPairsAligned6R`, both pair distances remain 0 away from home.
3. On `GenericAligned6R`, `φ` is undefined while the old `N_red` embedding comparison still reports zero principal angles.
4. Predictor-corrector continuation of `p(q)=p0`, `q6` constant yields a local 2D regular subset with `rank(J_d N_red)=2` away from labeled singular samples.

Do **not** read continuation through SUUR unless `φ` is defined on the regular subset. Do not claim fibers or spherical `RRRR`.

## 3. User story

As a robotics researcher, I want a reproducible fixed-position continuation patch and discriminating compound-joint tests so that Stage C fiber work is not built on a mobility slogan.

## 4. Deliverables

```text
src/grashof_workspace/spatial_experiments/
    suur_coordinates.py
    continuation.py
    manifold_experiments.py
    sprint04_readout.py
scripts/validate_pointing_manifold.py
scripts/generate_atr_sprint04_readout.py
```

## 5. Experiment IDs

| ID | Case | Expected result |
|---|---|---|
| `ATR_EXP_016` | IP pair persistence | both distances 0 at regular and seeded `q` |
| `ATR_EXP_017` | Generic negative control | pairs skew; `φ` undefined; old principal angles ~0 |
| `ATR_EXP_018` | IP coordinate-map + closure | `φ` defined; closure residuals below tol |
| `ATR_EXP_019` | IP continuation patch | 2D regular subset; rank-two pointing away from labeled singular set |
| `ATR_EXP_020` | UR-like continuation | same C10 claim via the same API; no SUUR map required |

## 6. Acceptance criteria

- new spatial code stays under `spatial_experiments` with no `sixr_grashof` import;
- planar tests and Sprint 01–03 tests still pass;
- artifacts carry `repository_commit` and committed `SOURCE_IDENTIFIER`;
- Check-in 4 is drafted, not auto-approved;
- no fiber, spherical-four-bar, or exact-UR modules.

## 7. Explicitly deferred

- scalar fiber constraints `h(q)=c`;
- spherical `RRRR` / McCarthy–Soh;
- exact UR / URDF.
