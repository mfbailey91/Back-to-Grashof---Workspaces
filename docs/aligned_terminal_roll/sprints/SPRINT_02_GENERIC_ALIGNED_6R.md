# Sprint 02 — Generic Aligned 6R Reduction

**Sprint status:** Complete / Check-in 2 approved
**HTML readout:** `results/aligned_terminal_roll/sprint02_readout/index.html`
**Milestone target:** M2 — Two-dimensional reduction established
**Check-in:** Check-in 2 (Approved 2026-08-04, `CONTINUE`)
**Authorized by:** Check-in 1 (`CONTINUE`, 2026-08-04)
**Timebox:** Full-chain differential reduction only; no compound joints or continuation

## 1. Sprint objective

Show that aligned terminal-roll symmetry and the expected local ranks/nullities are properties of a generic synthetic aligned-terminal 6R chain, not only of the isolated terminal fixture.

## 2. Hypothesis under test

At a regular configuration of an aligned-terminal 6R manipulator:

```text
rank(J_p) = 3
dim ker(J_p) = 3
J_p e6 = 0
J_d e6 = 0
rank(J_pd) = 5
dim ker(J_pd) = 1
ker(J_pd) parallel to e6
rank(J_d N_red) = 2
```

where `N_red` spans `ker(J_p)` after removing the terminal-roll direction.

This sprint does not test mechanism equivalence, continuation, or spherical four-bars.

## 3. User story

As a robotics researcher, I want a minimal product-of-exponentials 6R kernel with explicit home axes so that Stage A rank claims can be checked independently of UR frames and compound-joint grouping.

## 4. Deliverables

### Software

```text
src/grashof_workspace/spatial_experiments/
    serial_chain.py
    jacobians.py
    aligned_6r.py
scripts/validate_aligned_6r_reduction.py
scripts/generate_atr_sprint02_readout.py
```

### Validation

- named regular configuration rank suite;
- analytical versus multi-`h` finite-difference Jacobians;
- full-chain terminal-roll check;
- negative control that breaks alignment;
- seeded survey plus one named singular or near-singular sample.

### Documentation

- this sprint note;
- experiment records ATR_EXP_006–010;
- Check-in 2 draft;
- HTML readout;
- risk-register updates for A04–A06.

## 5. Experiment IDs

| ID | Case | Expected result |
|---|---|---|
| `ATR_EXP_006` | named regular `q` | C6–C8 rank/nullity identities |
| `ATR_EXP_007` | FD refinement of `J_p`, `J_d` | derivative error converges over usable `h` |
| `ATR_EXP_008` | full-chain roll at regular `q` | `dp/dq6 = 0`, `dd/dq6 = 0`, roll changes |
| `ATR_EXP_009` | misaligned or off-axis task | `e6` leaves `ker(J_pd)` or the violated invariant fails |
| `ATR_EXP_010` | seeded survey + named singular sample | regular subset supports C6–C8; singular samples labeled |

## 6. Acceptance criteria

Sprint 02 implementation is complete when:

- all new spatial code remains under `spatial_experiments` with no `sixr_grashof` import;
- trusted planar tests and Sprint 01 tests still pass;
- regular samples exhibit the predicted ranks and `e6` kernel alignment;
- singular samples are reported separately rather than treated as generic failures;
- Check-in 2 packet is drafted and left for human decision;
- no `SUUR`, continuation, fiber, or spherical-four-bar code has been introduced.

## 7. Explicitly deferred

- compound-joint grouping and `SUUR` comparison;
- UR-like architecture;
- predictor-corrector continuation;
- one-dimensional fibers;
- spherical `RRRR` and McCarthy-Soh tests.
