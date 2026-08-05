# Sprint 03 — Architecture Comparison

**Sprint status:** Complete / Check-in 3 approved (`CONTINUE WITH CHANGED SCOPE`)
**HTML readout:** `results/aligned_terminal_roll/sprint03_readout/index.html`
**Milestone target:** M3 — Architecture comparison (local Stage B only)
**Check-in:** Check-in 3 (Approved 2026-08-04, `CONTINUE WITH CHANGED SCOPE`)
**Authorized by:** Check-in 2 (`CONTINUE`, 2026-08-04)
**Timebox:** Stage A on two new architectures plus local compound-joint probes; no continuation solver

## 1. Sprint objective

Test whether Stage A identities survive on two controlled synthetic aligned-terminal 6R architectures, and whether a literal compound-joint grouping of the intersecting-pair chain matches the physical reduced tangent locally.

## 2. Hypothesis under test

1. `IntersectingPairsAligned6R` and `URLikeAligned6R` satisfy C6–C8 at a named regular configuration.
2. Grouping `UA=(R1,R2)`, `UB=(R3,R4)`, `RC=R5` with `q6` held fixed produces a reduced tangent whose principal angles to physical `N_red` are below the stated tolerance (local C9).
3. Short Euler steps along unit `N_red` keep `p` near `p0` and produce agreeing pointing increments between the physical 6R and the embedded compound model.

This sprint does **not** claim global continued equivalence, a 2D pointing manifold, fibers, spherical `RRRR`, or exact UR.

## 3. User story

As a robotics researcher, I want synthetic intersecting-pair and UR-like aligned 6R models so that Stage A and local compound-joint claims can be compared before committing to a continuation parent.

## 4. Deliverables

### Software

```text
src/grashof_workspace/spatial_experiments/
    architectures.py
    compound_joints.py
    architecture_experiments.py
    sprint03_readout.py
scripts/validate_architecture_comparison.py
scripts/generate_atr_sprint03_readout.py
```

### Validation

- intersecting-pairs Stage A at a named regular `q`;
- UR-like Stage A at a named regular `q`;
- principal-angle comparison of physical `N_red` vs compound embedding;
- local `N_red` step probes (1–3 steps, optional position corrector);
- three-architecture comparison table with a recorded, not auto-selected, continuation parent.

### Documentation

- this sprint note;
- experiment records ATR_EXP_011–015;
- Check-in 3 draft;
- HTML readout;
- risk-register updates for A07/A08.

## 5. Experiment IDs

| ID | Case | Expected result |
|---|---|---|
| `ATR_EXP_011` | intersecting-pairs Stage A | C6–C8 hold; pair intersections exact |
| `ATR_EXP_012` | UR-like Stage A | C6–C8 hold; wrist concurrency exact; `R2∥R3` |
| `ATR_EXP_013` | principal angles vs compound embedding | max principal angle below stated rad tolerance |
| `ATR_EXP_014` | local `N_red` steps, physical vs compound | `p` stays near `p0`; pointing increments agree |
| `ATR_EXP_015` | three-architecture comparison | Stage A survives all three; local C9 reported; continuation parent recorded, not auto-selected |

## 6. Acceptance criteria

Sprint 03 implementation is complete when:

- all new spatial code remains under `spatial_experiments` with no `sixr_grashof` import;
- trusted planar tests and Sprint 01–02 tests still pass;
- both new architectures satisfy Stage A at their named regular configurations;
- compound grouping is tested only on `IntersectingPairsAligned6R`;
- local step probes are finite Euler/RK steps, not a predictor-corrector manifold solver;
- Check-in 3 packet is drafted and left for human decision;
- no fiber, spherical-four-bar, exact-UR, or continuation-solver code has been introduced.

## 7. Explicitly deferred

- predictor-corrector / pointing-manifold continuation (Sprint 04 / C10);
- fibers, spherical `RRRR`, McCarthy-Soh;
- exact UR / URDF / `sixr_grashof`;
- planar kernel edits.
