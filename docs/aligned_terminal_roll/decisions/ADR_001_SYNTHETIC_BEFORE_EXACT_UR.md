# ADR 001 — Validate Synthetic Geometry Before Exact UR Models

**Status:** Accepted
**Date:** 2026-08-04

## Context

A UR-like 6R manipulator is recognizable, common, and favorable for testing an aligned terminal-roll hypothesis. Beginning directly with an exact UR model would also introduce manufacturer frame conventions, dimensional offsets, joint limits, tool-flange choices, and possible approximate rather than exact geometric relationships.

Those variables would make a failed reduction difficult to interpret.

## Decision

Use the following sequence:

1. isolated terminal-roll fixture;
2. generic synthetic aligned 6R chain;
3. controlled synthetic compound-joint and UR-like architectures;
4. exact UR geometry only as a later generalization test.

The trusted planar v0.2 kernel remains unchanged. Spatial work is isolated in an experimental package.

## Consequences

### Positive

- geometric claims can be tested independently;
- positive and negative controls are exact by construction;
- failures have clearer interpretations;
- the later UR comparison becomes scientifically meaningful.

### Negative

- the first implementation is not immediately a named industrial robot;
- some code may be replaced when exact robot adapters are added;
- practical joint-limit conclusions are delayed.

## Reversal criteria

Revisit this decision only if:

- the synthetic representation cannot express a required real architectural feature;
- exact UR geometry is necessary to define the task point or terminal-axis relation;
- a validated reusable robot-description adapter becomes available without obscuring the geometric tests.
