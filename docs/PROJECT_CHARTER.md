# Project Charter

## Working title

**Back to Grashof: Analytical Workspace Characterization for Open-Chain Manipulators**

## Problem statement

Robot workspaces are often represented numerically, even when a manipulator's geometry contains enough structure to support an analytical characterization. This project investigates whether an open-chain manipulator can be reduced to a family of closed mechanisms whose mobility class directly defines regions of Cartesian capability.

The first case is the planar 3R manipulator. Fixing the end-effector position closes the serial chain into a four-bar. The question "can the end effector attain every planar orientation at this position?" becomes "can the terminal link rotate completely in the corresponding four-bar inversion?"

## First deliverable

A reproducible software and mathematical demonstration that:

1. constructs the equivalent four-bar at each Cartesian radius;
2. evaluates exact terminal-link rotatability;
3. recovers the analytical dexterous workspace;
4. validates the analytical boundary against direct kinematic sampling;
5. visualizes the reachable and dexterous workspace components.

## Research principle

The Grashof label is supporting structure, not a substitute for the exact geometric statement. The software must retain:

- the conventional shortest-plus-longest Grashof test;
- the inversion classification;
- the exact link-specific closure condition;
- a numerical validation path.

## Definition of done for Phase 1

Phase 1 is complete when the repository can generate figures for a matrix of link-length families and every plotted analytical boundary agrees with independent orientation sampling to a documented numerical tolerance.
