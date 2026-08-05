# Sprint 01 — Spatial Foundations and Terminal-Roll Fixture

**Sprint status:** Complete
**Milestone target:** M1 — Terminal-roll symmetry established
**Check-in:** Check-in 1 (draft ready for decision)
**Timebox:** One implementation cycle; do not extend scope to a full 6R chain
**Completed:** 2026-08-04 — `spatial_experiments` fixture, ATR_EXP_001–005 PASS
**HTML readout:** `results/aligned_terminal_roll/sprint01_readout/index.html`

## 1. Sprint objective

Establish the geometric and software conventions for spatial experiments and verify, using an isolated terminal-joint fixture, that an aligned terminal revolute preserves the selected task point and tool pointing direction while changing full tool roll.

## 2. Hypothesis under test

For a revolute axis `R6 = (r6, w6)`, task point `p`, and selected tool direction `d`:

```text
p lies on R6
d parallel w6
```

implies:

```text
dp/dq6 = 0
dd/dq6 = 0
```

while the full tool orientation changes by roll about `d`.

This sprint does not test the dimensionality of a complete 6R fixed-position mechanism.

## 3. User story

As a robotics researcher, I want an isolated, independently validated terminal-roll fixture so that later 6R results cannot be confused with frame, transform-order, or task-definition errors.

## 4. Deliverables

### Research

- frozen provisional definition of aligned terminal roll;
- derivation of position and pointing derivatives;
- explicit interpretation of both negative controls;
- documented distinction between full orientation and pointing.

### Software

Create the minimum isolated package:

```text
src/grashof_workspace/spatial_experiments/
    __init__.py
    axis_geometry.py
    rotations.py
    terminal_roll_fixture.py
    diagnostics.py
```

Create one deterministic runner:

```text
scripts/validate_terminal_roll_fixture.py
```

### Validation

Implement:

- positive aligned-terminal control;
- off-axis task-point control;
- misaligned pointing-direction control;
- optional combined control;
- analytical derivative checks;
- central finite-difference checks at multiple step sizes;
- full `q6` sweep;
- orientation-axis/angle verification.

### Documentation

- update conventions if implementation exposes ambiguity;
- create experiment records for all controls;
- prepare Check-in 1 packet;
- update risk-register statuses.

## 5. Work packages

### WP1 — Axis-line geometry

Tasks:

- implement immutable point-direction axis representation;
- normalize and validate axis directions;
- implement point-to-axis distance;
- implement parallelism residual;
- implement rotation about an arbitrary axis;
- add unit tests for all primitives.

Acceptance:

- known hand-calculated cases pass;
- invalid zero-length directions fail clearly;
- results are invariant to choosing another point on the same axis.

### WP2 — Terminal-roll fixture

Tasks:

- define a pre-joint transform and terminal axis;
- attach a tool frame and explicit task point;
- define a tool-frame pointing vector;
- compute world-frame `p(q6)`, `d(q6)`, and `R(q6)`;
- avoid DH parameters and robot-specific geometry.

Acceptance:

- fixture behavior is deterministic;
- task point and direction are explicit inputs, not implicit frame assumptions.

### WP3 — Positive control

Tasks:

- place `p` exactly on `R6`;
- align `d` exactly with `R6`;
- sweep `q6` over at least one full revolution;
- verify position and pointing invariance;
- verify relative orientation is roll about `d`.

Acceptance:

- maximum position residual below configured tolerance;
- maximum pointing residual below configured tolerance;
- recovered roll angle agrees with commanded angle within tolerance.

### WP4 — Negative controls

#### N1 — Off-axis task point

- perturb `p` transversely;
- retain `d parallel R6`;
- verify that `q6` moves `p`;
- verify that pointing remains invariant.

#### N2 — Misaligned pointing direction

- keep `p` on `R6`;
- rotate `d` away from `R6`;
- verify that position remains invariant;
- verify that pointing changes.

Acceptance:

- each negative control fails exactly the invariant associated with the violated hypothesis;
- no control is accepted merely because a tolerance is too loose.

### WP5 — Independent derivatives

Tasks:

- derive analytical `dp/dq6` and `dd/dq6`;
- compute central finite differences at multiple `h`;
- compare analytical and numerical results;
- report convergence rather than one scalar pass/fail.

Acceptance:

- expected convergence is visible;
- analytical/numerical disagreement blocks the check-in.

### WP6 — Experiment reporting

Tasks:

- add machine-readable metrics;
- record model parameters and tolerances;
- produce a compact plot showing position, pointing, and roll residuals versus `q6`;
- create experiment summaries using the experiment template.

Acceptance:

- every control is reproducible from a documented command;
- results are stored under deterministic experiment IDs.

## 6. Initial experiment IDs

| ID | Case | Expected result |
|---|---|---|
| `ATR_EXP_001` | aligned positive control | position invariant; pointing invariant; roll changes |
| `ATR_EXP_002` | off-axis task point | position changes; pointing invariant |
| `ATR_EXP_003` | misaligned pointing direction | position invariant; pointing changes |
| `ATR_EXP_004` | combined violation | position and pointing both change |
| `ATR_EXP_005` | finite-difference refinement | derivative error converges over usable step-size range |

## 7. Acceptance criteria

Sprint 01 is complete when:

- all spatial code is isolated under `spatial_experiments`;
- the trusted planar tests remain unchanged and pass;
- positive and negative controls exhibit the predicted qualitative behavior;
- analytical derivatives agree with independent finite differences;
- full orientation roll is verified without Euler-angle subtraction;
- tolerances and units are explicit;
- experiment manifests and summaries are generated;
- Check-in 1 packet is ready;
- no complete 6R model, continuation solver, compound joint, or spherical-four-bar code has been introduced.

## 8. Falsification and failure interpretations

| Observation | Interpretation |
|---|---|
| aligned case changes position | point is not on axis, transform order is wrong, or hypothesis implementation is invalid |
| aligned case changes pointing | direction is not aligned, frame mapping is wrong, or hypothesis implementation is invalid |
| aligned case does not change orientation | fixture does not represent terminal roll |
| off-axis case preserves position | negative control or metric is wrong |
| misaligned case preserves pointing | negative control or metric is wrong |
| result changes with finite-difference step | derivative evidence is inconclusive |
| only one hand-picked pose passes | implementation is not sufficiently validated |

## 9. Check-in 1 questions

1. Are the task point and pointing direction defined in the correct frames?
2. Do the two aligned-terminal conditions independently control position and pointing invariance?
3. Does the orientation residual unambiguously measure terminal roll?
4. Are tolerances appropriately scaled?
5. Are the axis-line and transform conventions ready to support a full serial chain?
6. Should Sprint 02 build the generic 6R kernel, or is a conventions-correction sprint required?

## 10. Explicitly deferred

- complete 6R forward kinematics;
- fixed-position Jacobian rank;
- quotient tangent basis;
- compound-joint grouping;
- UR-like architecture;
- continuation;
- one-dimensional fibers;
- spherical `RRRR`;
- McCarthy-Soh tests.
