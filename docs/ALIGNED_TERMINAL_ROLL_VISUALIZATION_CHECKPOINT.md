# Checkpoint — Visualizing the Aligned Terminal-Roll Project

**Date:** 2026-08-05  
**Status:** Research interpretation checkpoint  
**Purpose:** Preserve the conceptual reset that motivates the visualization-first probe

## Current project arc

The spatial investigation progressed through:

1. terminal-roll symmetry;
2. quotienting terminal roll from the reduced position-and-pointing task;
3. identifying a local two-dimensional reduced object;
4. constructing one-dimensional pointing level-set fibers;
5. testing whether selected fibers behave like spherical four-bars;
6. rejecting the first two tested spherical-four-bar candidates.

## What appears solid so far

- The aligned terminal joint preserves the selected task point and pointing direction while changing full roll.
- The reduced Jacobian structure leaves two local pointing directions after terminal roll is removed.
- Numerical continuation produced a regular local two-parameter object.
- Scalar pointing constraints produced regular local one-dimensional curves.
- The first two tested topology-derived spherical-four-bar interpretations failed strongly.

## Where the interpretation became uncertain

A proposed description of the fixed-position parent was:

> a family of nearby configurations all hitting that point.

That set-theoretic description may be mathematically valid while still being mechanically misleading.

The current implementation treats the fixed-position parent as configurations satisfying

```text
p(q) = p0
q6 = q6*
```

but the better mechanical interpretation may instead be:

- a reduced mechanism assembled from constituent joint motions;
- a virtual closed chain induced by the task constraint;
- a task-relative mechanism whose physical and virtual joints should be shown explicitly;
- a motion object understood through moving axes, virtual links, and closure geometry before configuration-manifold language is introduced.

## Main unresolved question

> What is the correct mechanical object represented by the two-dimensional reduced construction?

## Visualization-first reset

The next implementation should begin from an assembled synthetic manipulator and proceed geometrically:

1. draw a hypothetical aligned-terminal 6R manipulator at one FK pose;
2. draw all physical joint origins and infinite joint axes;
3. place the virtual spherical closure at the task point;
4. show the terminal-roll quotient without physically deleting the terminal joint;
5. identify exact adjacent intersecting-axis pairs;
6. show every valid compound-joint reduction of the five remaining revolutes;
7. decompose the compound joints into candidate four-revolute axis selections;
8. draw the selected infinite axes in space for visual concurrency inspection.

This probe should not begin with manifolds, fibers, continuation, McCarthy–Soh classification, or numerical equivalence testing.

## Important caution

Do not assume the correct explanatory order is

```text
configuration family
-> surface
-> fiber
-> spherical four-bar
```

The visualization probe will instead test the order

```text
physical chain
-> virtual closure
-> quotient symmetry
-> compound-joint representation
-> candidate revolute-axis tuple
-> later mathematical validation
```

## Terminology guardrail

- Two sequential revolute joints form an exact universal joint only when their axes intersect and are not collinear.
- Collinear sequential axes collapse toward one effective revolute axis; they do not form a universal joint.
- Skew axes must not be snapped together and labeled equivalent.
- A four-axis selection is only a candidate `RRRR` axis tuple until global concurrency, fixed arc dimensions, inactive-coordinate locking, and motion equivalence are established.

