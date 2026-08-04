# Workshop Note: Spherical Four-Bar Fibers for 6R Dexterity

**Date:** 2026-08-04  
**Status:** Research hypothesis and implementation handoff; not a proven reduction  
**Repository baseline:** v0.2 planar 3R work after PR #1, *Harden Grashof classification, radial mechanism atlas, and CI for v0.2*

## 1. Why this note exists

The first attempt to extend the planar 3R Grashof result directly to a spatial 6R manipulator moved too quickly. The project has been rolled back to the stable planar v0.2 baseline. The next spatial investigation should build upward slowly and should not assume that an arbitrary 6R arm is equivalent to one spherical four-bar.

The current hypothesis is narrower:

> For a restricted class of 6R architectures, the fixed-position orientation problem may admit a finite family of one-degree-of-freedom spherical `RRRR` fibers. If those fibers can be constructed exactly, McCarthy and Soh's spherical four-bar rotatability classification may provide a finite analytical shorthand for orientation capability.

The proposed finite family contains at most eight candidate spherical four-bars per Cartesian point.

This is a falsifiable mechanism-construction hypothesis, not yet a research claim.

## 2. Reference theory

The relevant Grashof framework is the spherical four-bar analysis in Chapter 7 of:

J. M. McCarthy and G. S. Soh, *Geometric Design of Linkages*, Interdisciplinary Applied Mathematics, vol. 11.

The intended tests are the McCarthy-Soh spherical `T1`-`T4` linkage-type and rotatability conditions. The ordinary planar inequality

```text
shortest + longest <= remaining two links
```

is not the operative test for this spatial work.

McCarthy-Soh applies only after an actual spherical `RRRR` linkage has been established:

- four revolute axes;
- all four axes concurrent at one fixed center;
- four fixed angular link dimensions;
- one internal degree of freedom;
- a designated ground, input, coupler, and output inversion.

Correct mobility alone does not prove spherical-four-bar equivalence.

## 3. Virtual closure at a fixed Cartesian point

For a general 6R manipulator, fixing the tool point while leaving orientation unrestricted closes the serial chain with a virtual spherical joint:

```text
Ground - R1 - R2 - R3 - R4 - R5 - R6 - Sv - Ground
```

Using the generic spatial mobility count,

```text
M = sum(joint freedoms) - 6
  = 6 + 3 - 6
  = 3.
```

This agrees with the three remaining orientation degrees of freedom at a fixed position.

### 3.1 Aligned terminal-axis special case

If the fixed task point lies on the `R6` axis and the final link/tool offset is collinear with that axis, `R6` supplies pure terminal roll without moving the task point or changing the terminal-axis pointing direction.

The pointing problem may then quotient out `R6`:

```text
5R + Sv, M = 5 + 3 - 6 = 2.
```

This two-degree-of-freedom mechanism represents the terminal-axis direction on `S^2`.

Selecting a one-parameter pointing slice, or equivalently removing one rotational freedom from the virtual spherical closure, replaces `Sv` with a virtual universal joint `Uv`:

```text
Uv + 5R, M = 2 + 5 - 6 = 1.
```

This is the minimal nontrivial architecture proposed for the first experiment.

### 3.2 General terminal geometry

If `R6` is not collinear with the final link/task point, rotation of `R6` changes the Cartesian point. It cannot be quotiented as pure roll. The appropriate parent closure remains:

```text
Sv + 6R, M = 3.
```

The first implementation should not attempt this general case.

## 4. Intersecting-axis reduction of the one-DOF parent

Start with the aligned one-DOF loop:

```text
Uv - R1 - R2 - R3 - R4 - R5.
```

Assume two disjoint pairs of consecutive physical revolute axes intersect:

```text
(Ri, Ri+1) -> UA
(Rj, Rj+1) -> UB
remaining revolute -> RC.
```

The reduced parent topology is:

```text
Uv - UA - UB - RC
```

or, generically, a `UUUR` spatial four-link loop.

Its generic mobility is:

```text
M = 2 + 2 + 2 + 1 - 6 = 1.
```

This reduction is a representation of the parent one-DOF mechanism. It is not yet a spherical four-bar.

## 5. Eight candidate RRRR fibers

Each universal joint is represented by two intersecting revolute axes:

```text
Uv = (Rv0, Rv1)
UA = (RA0, RA1)
UB = (RB0, RB1).
```

Choose one revolute axis from each universal joint and include the remaining physical revolute `RC`:

```text
Fb = Rv[bv] - RA[bA] - RB[bB] - RC,
```

where

```text
b = (bv, bA, bB) in {0,1}^3.
```

Therefore there are at most:

```text
2^3 = 8
```

candidate `RRRR` fibers:

```text
000, 001, 010, 011, 100, 101, 110, 111.
```

The hypothesis is not that all eight are valid. The hypothesis is that a robot architecture may admit a small, finite set of valid candidates that can be evaluated at each Cartesian point.

## 6. Conditions for a candidate to be an exact spherical four-bar

A chosen axis tuple is not a spherical four-bar merely because it forms a quadrilateral in one configuration. Each candidate must pass four tests.

### 6.1 Inactive-axis locking

For each universal joint, the unselected coordinate must remain constant along the complete one-DOF motion branch.

For a candidate selecting `(Rv0, RA1, RB0)`, for example:

```text
qv1 = constant
qA0 = constant
qB1 = constant.
```

A numerical residual can be defined as:

```text
lock_residual = max_s ||q_inactive(s) - q_inactive(0)||.
```

If an unused coordinate moves, that universal joint cannot be replaced by the selected revolute axis.

### 6.2 Global concurrency

The four selected revolute axes must pass through one common fixed point `O` for the entire motion.

For the intended virtual closure, the most natural candidate center is the fixed task point. Pairwise intersections at different shoulder, elbow, or wrist centers are insufficient.

For an axis with point `r` and unit direction `w`, its distance to candidate center `O` is:

```text
axis_distance = ||(I - w w^T)(O - r)||.
```

A candidate concurrency residual can combine the four axis distances and/or the least-squares common-axis intersection error.

This condition may be highly restrictive and may reject most ordinary industrial architectures.

### 6.3 Fixed spherical arc dimensions

For four concurrent selected axes `a1, a2, a3, a4`, define the adjacent angular dimensions:

```text
alpha = acos(a1^T a2)
beta  = acos(a2^T a3)
gamma = acos(a3^T a4)
eta   = acos(a4^T a1).
```

These four dimensions must remain constant over the complete motion branch.

A candidate arc residual is:

```text
arc_residual = max_s ||[alpha,beta,gamma,eta](s)
                         - [alpha,beta,gamma,eta](0)||.
```

This distinguishes a true fixed-geometry spherical linkage from an instantaneous spherical quadrilateral.

If inactive-axis locking and rigid-link grouping are exact, fixed arcs may follow automatically, but the check should remain independent because it catches incorrect axis ordering and grouping.

### 6.4 Motion equivalence

The selected spherical `RRRR` must reproduce the same one-dimensional configuration branch as the original `UUUR` parent.

A first local test compares tangent directions:

```text
J_parent(q) qdot = 0
J_4R(theta) thetadot = 0.
```

After lifting the four-bar tangent into parent coordinates, the two normalized tangent vectors should be parallel. A global test then continues both mechanisms over the full branch and compares their configurations and output motion.

Passing only at one pose is insufficient.

## 7. Architecture certification versus per-point computation

The eight-computation idea is useful only if the difficult mechanism-equivalence tests are not repeated expensively at every Cartesian point.

### 7.1 Architecture-level certification

Performed once for a synthetic architecture, robot family, or parameterized design:

- detect the two physical intersecting-axis pairs;
- define the virtual `U` decomposition and its axis convention;
- enumerate the eight candidate axis selections;
- test inactive-axis locking;
- test global concurrency;
- test fixed spherical arc dimensions;
- test local and global motion equivalence;
- identify which candidates are exact, approximate, or invalid;
- establish the correct McCarthy-Soh inversion and designated tool-side link.

Only candidates that pass this certification may enter the fast point classifier.

### 7.2 Cartesian-point evaluation

For each certified candidate at a Cartesian point:

1. construct the four selected axes and common center;
2. compute the four angular dimensions;
3. evaluate McCarthy-Soh `T1`-`T4`;
4. classify assemblability, linkage type, equality/change-point state, and designated-link rotatability;
5. record the candidate's pointing-motion tangent or output direction.

The point may receive an eight-state signature:

```text
G(p) = [G000, G001, G010, G011, G100, G101, G110, G111].
```

Invalid candidates remain explicit rather than inheriting a misleading Grashof label.

## 8. Why eight one-DOF fibers are not automatically dexterity

A fixed spherical four-bar generates a one-dimensional curve on `S^2`. Eight fixed curves cannot literally equal a two-dimensional sphere.

The more plausible role of the finite fiber set is to provide motion generators of the pointing manifold.

At pointing direction `d`, each valid candidate induces a tangent vector:

```text
gb(d) in T_d S^2.
```

Collect the valid tangent directions into a matrix:

```text
G(d) = [g000(d) g001(d) ... g111(d)].
```

A necessary local pointing-capability condition is:

```text
rank G(d) = 2.
```

A possible future sufficiency structure is:

```text
full McCarthy-Soh rotatability along required fibers
+ rank-2 tangent span on S^2
+ connectedness and branch-switching access
= complete pointing capability.
```

Then the aligned `R6` joint supplies full roll, potentially lifting complete pointing capability to complete orientation capability.

This implication is unproven. In particular, local rank does not guarantee global coverage, and valid branch switching may be obstructed by singularities or disconnected assembly modes.

## 9. Current research hypothesis

A working formulation is:

> For an aligned-terminal 6R architecture admitting two suitable intersecting-axis pairs, the fixed-position pointing problem may reduce to a one-DOF `UUUR` parent mechanism. Choosing one revolute axis from each of its three universal joints yields at most eight candidate `RRRR` fibers. Exact candidates may be classified by the McCarthy-Soh spherical Grashof conditions. A sufficient collection of fully rotatable fibers, together with tangent-space rank and global connectivity conditions, may analytically predict complete pointing capability; the aligned terminal revolute then supplies roll.

Every clause after "may" is to be tested.

## 10. First build: controlled synthetic mechanism

Do not begin with a URDF or a named industrial robot.

Construct one synthetic `Uv-UA-UB-RC` mechanism with deliberately controlled geometry:

- all axes and centers represented explicitly as Plucker lines or point-direction pairs;
- one selected axis tuple known by construction to form an exact spherical `RRRR`;
- one candidate deliberately failing concurrency;
- one candidate deliberately failing inactive-axis locking;
- one valid spherical rocker case;
- one valid spherical crank case;
- no joint limits, collision, dynamics, or approximate concurrency in the first experiment.

### 10.1 Initial software modules

A possible isolated package layout:

```text
src/grashof_workspace/spatial_experiments/
    axis_geometry.py
    compound_joints.py
    uuur_parent.py
    rrrr_fibers.py
    spherical_fourbar.py
    mccarthy_soh.py
    continuation.py
    residuals.py

scripts/
    build_synthetic_uuur.py
    enumerate_rrrr_fibers.py
    validate_fiber_equivalence.py

tests/
    test_uuur_mobility.py
    test_axis_choice_enumeration.py
    test_inactive_axis_locking.py
    test_global_concurrency.py
    test_spherical_arc_invariance.py
    test_parent_fiber_tangent_equivalence.py
    test_mccarthy_soh_against_continuation.py
```

Keep this experimental package separate from the trusted planar kernel.

### 10.2 First falsification gates

Stop or reformulate the hypothesis if:

1. no nondegenerate synthetic `UUUR` can admit an exact spherical `RRRR` fiber;
2. choosing one axis from a `U` cannot preserve the parent motion except in trivial locked mechanisms;
3. all four selected axes can be concurrent only in collapsed or singular geometries;
4. fixed-arc and motion-equivalence requirements are mutually incompatible;
5. the finite fiber set cannot generate rank two on any open region of `S^2`;
6. McCarthy-Soh rotatability has no stable relationship to the parent pointing motion.

A negative result is useful if it identifies the precise obstruction.

## 11. Questions intentionally left open

- What physical or virtual construction defines the selected `Uv` pointing slice without introducing an arbitrary coordinate artifact?
- Does the `UUUR` parent actually arise from a practical 6R architecture, or only from synthetic special geometry?
- Can inactive-axis locking be an architectural identity rather than a configuration-specific coincidence?
- Are the eight candidates separate configuration fibers, alternate coordinate descriptions, or only local tangent generators?
- How should the McCarthy-Soh ground, input, coupler, and output links be assigned for each candidate?
- Which `T1`-`T4` linkage types correspond to the required tool-side full rotation?
- Can tangent-rank and connectivity conditions be converted into a finite global test?
- Is the aligned terminal-axis case broad enough to include useful real manipulators?
- What changes in the general `Sv+6R` case when terminal roll cannot be quotiented?

## 12. Resume point

The next session should begin with one task only:

> Specify and draw a synthetic `Uv-UA-UB-RC` one-DOF loop in which one chosen axis from each `U`, together with `RC`, is an exact nondegenerate spherical `RRRR` linkage.

Before implementing the eight-state classifier, verify that this parent mechanism can exist and that its known spherical fiber reproduces the parent motion. If that succeeds, enumerate the other seven candidates and deliberately characterize why each passes or fails.

The project remains on the stable planar v0.2 baseline until this isolated experiment passes its first falsification gates.
