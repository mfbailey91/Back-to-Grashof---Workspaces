> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# Sprint V02B — Physical Geometry Hardening

**Status:** insertion sprint before V03 closure/continuation  
**Purpose:** replace descriptor-first pseudo-geometries with actual spatial four-bar reference assemblies and derived geometry descriptors.

## Problem statement

Sprint V01 successfully established the parameter inventory and visualization/readout pipeline, but its corpus samples descriptor-like scalar values directly. Those values are useful for testing tables and graphs; they are not yet a physically constructed `UUUR`, `UURU`, `URUU`, `USRR`, `URSR`, or `URRS` mechanism.

Sprint V03 must not solve closure on top of descriptor vectors. It needs actual joint centers, axis frames, compound-joint structure, and rigid-link adjacency.

## Research-data contract

Starting with V02B, the accepted pipeline is:

```text
SpatialFourBarGeometry
    -> GeometryDescriptor[]
    -> closure / continuation
    -> branch trajectory
    -> W = (w_alpha, w_beta)
    -> crank atlas
```

The V01/V02 random descriptor corpus is retained only for software-scaffold regression tests.

## Geometry object

Each mechanism stores:

- ordered family;
- four joint centers;
- one full orthonormal reference frame per joint;
- motion axes derived from the joint kind:
  - `R`: one frame axis;
  - `U`: two perpendicular frame axes;
  - `S`: three concurrent orthogonal frame axes;
- four rigid-link adjacencies forming the loop;
- the grounded link;
- the tool joint, always `U`.

The reference assembly is not yet a crank or mobility result. It is the geometric state from which V03 will derive loop transforms and solve actual motion.

## Canonical corpus

Create one intentionally generic, asymmetric reference assembly for each ordered family:

```text
UUUR
UURU
URUU
USRR
URSR
URRS
```

The canonical samples should avoid accidental planar, parallel, concurrent, or symmetric degeneracies unless deliberately introduced later.

## Perturbed corpus

Generate nearby geometry samples by perturbing:

- joint-center locations;
- complete joint frames.

Perturb entire orthonormal frames rather than individual axes so:

- `U` axes remain exactly perpendicular;
- `S` axes remain exactly concurrent and orthogonal;
- the ordered joint topology cannot change.

Remove irrelevant global translation by keeping the tool joint center fixed at the origin.

## Derived descriptor inventory

Compute descriptors from stored geometry, not from sampled stand-ins.

Initial V02B descriptors include:

- four normalized loop-center distances: `L12`, `L23`, `L34`, `L41`;
- two normalized center diagonals: `D13`, `D24`;
- primary-axis twists around the loop;
- tool-U internal angle sanity check;
- tool-to-ground primary-axis angle;
- nonadjacent common-normal distances;
- signed axis offsets;
- axis-to-opposite-center distances;
- normalized signed tetrahedral volume;
- coplanarity residual;
- chirality;
- approximate mirror-symmetry flag;
- adjacent-primary-axis intersection flag;
- structural-validity flag.

All dimensional quantities used for comparison are normalized by a reference length defined as the mean of the four loop center distances.

## Visual outputs

Publish at least two views per family:

1. canonical geometry;
2. one perturbed geometry.

Each 3D view shows:

- the four link centerlines;
- the grounded link with heavier line weight;
- all four joint centers;
- every motion axis of every `R`, `U`, or `S` joint;
- joint labels and joint kinds.

The V02B HTML page must pair each figure with the geometry validation result and a compact descriptor summary.

## Software deliverables

- `geometry.py`
  - joint/link/reference-geometry dataclasses;
  - vector and line-geometry utilities;
  - canonical geometry construction;
  - topology-preserving perturbation.
- `geometry_descriptors.py`
  - descriptor derivation;
  - stable physical geometry sampler;
  - validation helpers.
- `geometry_readouts.py`
  - V02B HTML readout.
- `plots.py`
  - 3D physical geometry plotter.
- `cli.py`
  - V02B JSON/PNG/HTML generation.
- tests covering the V02B data contract.

## Acceptance gates

V02B closes only if:

1. all six canonical family objects validate;
2. the family symbols exactly match the joint kinds;
3. the tool joint is always a two-axis `U`;
4. perturbations preserve every compound-joint internal axis constraint;
5. repeated sampling with the same seed produces identical geometries;
6. descriptor values recompute from geometry to numerical tolerance;
7. JSON serialization preserves centers, frames, kinds, and descriptors;
8. canonical and perturbed 3D figures exist for all six families;
9. the HTML readout explicitly warns that no closure or crank solution has occurred yet;
10. V03 consumes only the V02B physical geometry source.

## Non-goals

Do not in V02B:

- solve loop closure;
- infer mobility numerically;
- continue a branch;
- compute winding numbers;
- call any sample a crank or rocker;
- infer Grashof-like rules;
- introduce joint limits.

Those begin in V03/V04 and later.
