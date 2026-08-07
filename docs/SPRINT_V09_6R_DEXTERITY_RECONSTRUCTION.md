# Sprint V09 — 6R Dexterity Reconstruction and Validation

**Status:** planned after V08  
**Purpose:** reconnect the spatial-four-bar machinery to an aligned-terminal 6R manipulator and test the central workspace hypothesis against independently computed orientation truth.

## Central research gate

Does virtual spatial-four-bar crank / coverage structure predict actual manipulator orientation capability at a Cartesian point?

This sprint is the make-or-break gate for the dexterous-workspace claim.

## Scope

Start with a **synthetic aligned-terminal 6R manipulator** whose geometry is explicit and controllable. Do not begin with URDF parsing or industrial robot idiosyncrasies.

Terminal-roll assumption:

```text
(6R + S_v) / R6 -> 5R + S_v, M = 2
```

The one-DOF `UXXX` mechanisms remain constrained pointing fibers / slices of that two-DOF parent.

## Phase V09A — robot-to-virtual-mechanism extraction

At selected Cartesian point `p`:

1. construct or solve physical arm configurations reaching `p`;
2. quotient terminal roll under the aligned-terminal assumption;
3. identify the applicable compound-joint parent / ordered one-DOF family;
4. construct the virtual tool joint and canonical slice parameterization;
5. extract an actual `SpatialFourBarGeometry` through the same data contract used in V05–V08;
6. visualize the robot and extracted virtual mechanism together.

The extraction must be deterministic and debuggable; no manual relabeling in the final pipeline.

## Phase V09B — fiber crank / coverage field

Across the retained slice parameter `phi` (or its V04C replacement), evaluate:

```text
G_p(phi) = crank / rocker / boundary / no assembly / uncertain
```

and preserve:

- `W(phi)`;
- angular coverage;
- branch connectivity;
- singularity margin;
- evaluator provenance / confidence.

## Phase V09C — independent orientation truth

For the same Cartesian point, compute a reference capability estimate independently of the virtual-four-bar classifier:

- sample target pointing directions / orientations;
- solve IK or use a trusted numerical orientation-coverage procedure;
- measure achievable orientation coverage;
- explicitly track numerical resolution and failure modes.

The reference procedure must not use the virtual-crank label as an input.

## Phase V09D — pointwise validation

Compare virtual-mechanism prediction against numerical orientation truth over selected Cartesian points:

```text
virtual prediction
vs
independent orientation coverage
```

Track:

- true / false dexterous predictions;
- coverage disagreement;
- uncertainty;
- failure due to branch connectivity;
- singularity effects;
- terminal-roll assumptions.

Use deliberately difficult boundary points, not only easy interior examples.

## Phase V09E — workspace reconstruction

After pointwise agreement is credible:

1. evaluate a Cartesian grid / adaptive point set;
2. classify points as high-confidence dexterous, non-dexterous, or unresolved;
3. visualize the resulting workspace region;
4. compare with brute-force numerical dexterous-workspace estimation;
5. compare computational cost.

## Required visualizations

- transparent 6R robot + extracted virtual four-bar overlay;
- slice/fiber construction sequence;
- `W(phi)` / coverage field at representative points;
- predicted-versus-reference orientation-coverage plots;
- false-positive / false-negative point gallery;
- final 3D dexterous / non-dexterous / unresolved workspace map.

## Deliverables

- synthetic aligned-terminal 6R model;
- deterministic virtual-four-bar extractor;
- pointwise fiber-field evaluator;
- independent numerical orientation-reference evaluator;
- pointwise validation dataset;
- workspace reconstruction and comparison;
- runtime comparison;
- visual failure gallery;
- `sprint_09_6r_dexterity_reconstruction.html`.

## Acceptance

V09 supports the workspace hypothesis only when:

1. robot-to-virtual-mechanism extraction is reproducible and visually auditable;
2. virtual predictions are compared to an independent orientation reference;
3. errors and unresolved states are quantified rather than hidden;
4. workspace boundaries show meaningful agreement, not merely selected examples;
5. computational benefit is measured against the reference method;
6. the terminal-roll and pointing-slice assumptions remain explicit.

## Gate C — interpretation

Possible closeout states:

```text
SUPPORTED:
virtual crank/coverage structure predicts manipulator dexterity within stated assumptions.

PARTIAL:
useful correlation exists but extra branch/connectivity or pointing-coverage conditions are required.

NOT SUPPORTED:
spatial-four-bar classification does not reliably predict 6R orientation capability.
```

Even a `NOT SUPPORTED` outcome does not invalidate the spatial-four-bar mechanism results from V05–V08; it limits the robotics-workspace claim.
