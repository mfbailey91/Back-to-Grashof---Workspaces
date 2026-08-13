# Kinematic Decomposition Ladder — L3 through L7

**Status:** optional software scaffold subordinate to active V05–V09  
**Active scientific sequence:** [`KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md`](KINEMATIC_DECOMPOSITION_V05_V09_PROGRAM.md)  
**Project:** Characterization of Manipulator Workspaces  
**Purpose:** provide shared parent → fiber → child → reconstruction interfaces from the trusted planar 3R calibration through deferred spatial 7R work without demoting the audited V05 closed-mechanism HOLD.

This document does **not** replace the active V05–V09 program. L4 maps to V05, L5 to V06, L6 is V07-first then V08, and L7 remains BLOCKED until the V05 gate lifts.

---

## 1. Program thesis

For a source manipulator with position map

\[
p:Q\rightarrow\mathbb R^{d_p},
\]

fix a Cartesian position \(p^*\) and construct the exact source parent

\[
\mathcal P_{p^*}=\{q:p(q)=p^*\}.
\]

At a regular point,

\[
\dim\mathcal P_{p^*}=n-d_p.
\]

When the source parent has dimension \(m>1\), introduce exactly \(m-1\) justified scalar level-set constraints:

\[
h_i(q)=c_i,
\qquad i=1,\ldots,m-1.
\]

The resulting source leaf

\[
\mathcal F_{\mathbf c}
=
\{q\in\mathcal P_{p^*}:h_i(q)=c_i\}
\]

is one-dimensional at regular values.

The complete pipeline is:

```text
source open chain
  -> fixed-position source parent
  -> task/redundancy level-set family
  -> one-dimensional source fiber
  -> candidate one-DOF closed-mechanism child
  -> independent parent/child equivalence certificate
  -> leaf continuation and mechanism predicate
  -> parent orientation/pointing reconstruction
```

A one-dimensional source fiber is always meaningful when its level-set construction is regular. A known four-bar compression is architecture-dependent and may be exact, component-limited, approximate, rejected, or unresolved.

---

## 2. Ladder

| Rung | Source chain | Fixed-position mobility | Target | Constraints required to reach a 1-DOF leaf |
|---|---|---:|---|---:|
| **L3** | planar 3R | 1 | \(SO(2)\) | 0 |
| **L4** | spatial 4R | 1 | specified \(Y_1\subset SO(3)\) | 0 |
| **L5** | spatial 5R | 2 | \(S^2\) pointing | 1 task slice |
| **L6** | spatial 6R | 3 | \(SO(3)\) orientation | 2 task slices |
| **L7** | spatial 7R | 4 | \(SO(3)\) plus 1D self-motion | 2 task slices + 1 redundancy gauge |

The dimensional count is the common software contract. It is not, by itself, a coverage theorem or a decomposition certificate.

---

## 3. Two-dimensional parents and one-dimensional children

For a role-aware four-joint spatial loop,

\[
M=\sum_i f_i-6,
\qquad
f_R=1,
\quad f_U=2,
\quad f_S=3.
\]

The candidate 2-DOF L5 parent families are:

```text
SUUR  SURU  SRUU
SSRR  SRSR  SRRS
```

where the leading `S` is `S_v`, the virtual spherical closure at the fixed tool point, and later `U`/`S` joints are exact physical-axis aggregates.

A regular scalar pointing slice changes only the task closure role:

```text
S_v -> U_v
```

and produces the one-DOF children:

```text
SUUR -> UUUR
SURU -> UURU
SRUU -> URUU
SSRR -> USRR
SRSR -> URSR
SRRS -> URRS
```

These children form a fiber family indexed by the slice parameter. The parent is not assumed to be the Cartesian product of two independent 1-DOF mechanisms.

---

## 4. U-joint drive contract

A universal joint has two local coordinates:

\[
U(\alpha,\beta)=R_a(\alpha)R_b(\beta).
\]

A closed child such as `UUUR` nevertheless has only one global degree of freedom. Therefore

\[
\alpha=\alpha(s),
\qquad
\beta=\beta(s),
\]

where \(s\) is continuation arclength.

The canonical solver contract is:

```text
command: pseudo-arclength increment ds
solve:   six loop-closure equations plus one arclength equation
output:  alpha(s), beta(s), and all remaining joint coordinates
```

A prescribed-alpha diagnostic adds

\[
\alpha=\alpha_{\mathrm{command}}
\]

and solves all remaining coordinates. It is valid only where

\[
\frac{d\alpha}{ds}\neq0.
\]

At an alpha turning point, switch to beta or return to pseudo-arclength. The two U coordinates are not two independent mechanism inputs.

See [`U_JOINT_DRIVE_CONTRACT.md`](U_JOINT_DRIVE_CONTRACT.md).

---

## 5. Common software objects

The new package is:

```text
src/grashof_workspace/decomposition_ladder/
  models.py       typed rung, slice, family, evidence, and drive contracts
  registry.py     L3-L7 rung registry and parent/child family map
  u_drive.py      free-branch and prescribed-coordinate semantics
  planar_l3.py   trusted planar 3R calibration adapter
  leaf_engine.py  provenance-preserving adapter to the current four-bar solver
  readout.py      JSON/SVG/GIF/HTML program readout
  cli.py          reproducible entry point
```

Reproduce the scaffold readout with:

```bash
PYTHONPATH=src python -m grashof_workspace.decomposition_ladder.cli \
  --outdir results/decomposition_ladder
```

The readout includes:

- the L3-L7 ladder;
- the 2-DOF parent → 1-DOF child family table;
- a conceptual U-joint coordinate graph;
- an animation labeled `param=s`;
- machine-readable program and evidence contracts.

The conceptual U animation is explanatory only and must not be used as mechanism evidence.

---

# 6. Rung implementation plan

## L3 — planar 3R calibration

### Goal

Refit the trusted analytical planar result into the common interfaces. The radius-level adapter is implemented in `planar_l3.py`; broader source-component visualization remains follow-up work.

### Source and child

```text
planar 3R source
  -> fix (x,y)
  -> exact planar 4R
  -> one-dimensional component
  -> tool orientation theta in SO(2)
```

### Required outputs

- `SourceParentRecord` (doc alias for the earlier `SourceProblemRecord` name);
- exact virtual-closure record;
- source component;
- exact reduced mechanism;
- global equivalence certificate;
- orientation winding / link-specific rotatability;
- reconstructed analytical dexterous-workspace membership.

### Acceptance

The common interface reproduces the existing exact planar workspace with no change to the trusted mathematical kernel.

### Visualization follow-up

Workspace exemplar PNGs/GIFs under `outputs/workspace_exemplars/` compare reduced four-bar
motion at dexterous / reachable-nondexterous / boundary radii. They are a visualization aid
for the trusted planar map, not an additional certificate path.

---

## L4 — spatial 4R direct one-dimensional equivalence

### Goal

Close the current V05 independent reduced-mechanism gate.

### Source

\[
4R+S_v,
\qquad M=1.
\]

### Procedure

1. continue a complete regular source component;
2. retain the source orientation curve in \(SO(3)\);
3. construct a role-aware candidate such as `S_v-U_phys-R-R` only when architecture permits;
4. instantiate the reduced closed mechanism independently;
5. continue the reduced component independently;
6. construct a component map;
7. compare closure, tangent, position, pointing, and full orientation;
8. issue `EXACT_GLOBAL`, `EXACT_ON_COMPONENT`, `LOCAL_ONLY`, `REJECTED`, or `UNRESOLVED`.

### Acceptance

At least one nontrivial source component and one independently solved reduced component have matching orientation maps over the claimed scope.

---

## L5 — spatial 5R parent and pointing-fiber family

### Goal

Implement the first full parent → fiber family → child → reconstruction experiment.

### Source parent

\[
5R+S_v,
\qquad M=2.
\]

### Procedure

1. construct and visualize the complete two-dimensional source parent;
2. project it to the pointing image on \(S^2\);
3. choose a justified scalar field, initially
   \[
   h(d)=n^Td;
   \]
4. identify regular and critical values of \(c\);
5. continue every discovered source-fiber component for selected \(c\);
6. derive candidate `UUUR`/`USRR`-line children where architecture permits;
7. solve each child with the existing four-bar leaf engine;
8. compare source and child task curves and issue certificates;
9. sweep \(c\);
10. reconstruct the parent pointing image from accepted fibers.

### Readouts

- transparent source arm with `S_v`;
- two-dimensional parent mesh/chart;
- scalar field \(h\) on the parent;
- matching latitude/level set on \(S^2\);
- child mechanism animation for selected fibers;
- source-versus-child overlay;
- fiber atlas over \(c\);
- direct-parent versus reconstructed-pointing comparison.

### Acceptance

The complete parent is represented independently of the child family, and reconstruction uses only accepted source-derived children.

---

## L6 — spatial 6R after independent orientation truth (V07-first)

### Goal

Freeze a decomposition-free \(SO(3)\) reference first (active V07). Only then construct nested orientation leaves / any V08 quotient and compare reconstruction against that independent truth.

### Source parent

\[
6R+S_v,
\qquad M=3.
\]

### Procedure

1. freeze a decomposition-free \(SO(3)\) reference (V07 gate);
2. select two independent orientation coordinates \(h_1,h_2\);
3. define leaves
   \[
   h_1(R)=c_1,
   \qquad
   h_2(R)=c_2;
   \]
4. solve source leaves and candidate compressed mechanisms only after certificates exist;
5. sweep \((c_1,c_2)\);
6. reconstruct and compare against the frozen V07 reference.

The aligned terminal-roll case (V08) may quotient roll only after its geometric, range, component, and reconstruction conditions pass against V07 truth.

---

## L7 — spatial 7R orientation plus redundancy (deferred / BLOCKED)

### Goal

Separate the one excess self-motion dimension from the three-dimensional orientation task without treating redundancy as an orientation coordinate.

### Status

L7 is outside the active V05–V09 sequence. Software may retain dimensional contracts with `ProcessStatus.BLOCKED`. Do not treat L7 as an active scientific claim until the V05 closed-mechanism gate lifts.

### Source parent

\[
7R+S_v,
\qquad M=4.
\]

### Procedure

1. identify a redundancy gauge \(r(q)=\rho\);
2. impose two orientation slices;
3. obtain one-dimensional leaves;
4. preserve the relation between task orientation and redundancy component;
5. require nonempty compatible redundancy fibers across the reconstructed target.

### Acceptance

Full orientation coverage and the existence/connectivity of redundancy fibers are reported separately.

---

## 7. Leaf-engine evidence contract

The current spatial-four-bar solver remains the leaf engine:

```text
SpatialFourBarGeometry
  -> scalar R/U/S chart
  -> six closure equations
  -> one-dimensional null tangent
  -> pseudo-arclength continuation
  -> returned-cycle detection
  -> alpha/beta winding and angular coverage
```

The new `leaf_engine.py` adapter adds:

```text
source rung
source parent
source component
slice id
source provenance
EquivalenceCertificateRecord (optional)
drive contract
```

A leaf result is promoted to `source_chain_evidence` only when:

```text
source_provenance = source_derived
and
certificate is not None
and
certificate.closed_mechanism_status in {EXACT_GLOBAL, EXACT_ON_COMPONENT}
```

Caller-supplied status strings alone never promote. Axis aggregation may be `EXACT_*` while closed-mechanism remains `UNRESOLVED` (ADR-021 / ADR-027). Otherwise the result remains `mechanism_explorer_only` or `unresolved_source_correspondence`.

---

## 8. Visualization contract

Every rung should retain the current visual style and add parent context.

### Parent view

- source links and axes;
- fixed tool point and virtual closure;
- parent chart/mesh;
- task image;
- scalar slice field;
- singular and critical sets.

### Fiber view

- selected level set on the parent;
- corresponding target-space curve;
- source fiber animation;
- child four-bar animation;
- branch parameter and all U coordinates;
- source-child residuals and certificate.

### Reconstruction view

- direct source image;
- union of accepted fiber images;
- missing/unresolved cells;
- multiplicity;
- critical slice values;
- reconstruction error.

---

## 9. Program gates

1. **Source-parent gate:** do not infer the full parent from a small set of traces.
2. **Fiber gate:** every scalar constraint records formula, value, rank, component, and provenance.
3. **Compression gate:** a source fiber is not a known four-bar merely because mobility and joint letters match.
4. **Drive gate:** canonical leaf solves use `s`; prescribed alpha/beta is local and diagnostic unless explicitly required by the task.
5. **Reconstruction gate:** use only accepted source-derived children.
6. **Descriptor gate:** descriptor mining begins only after a reconstructed source task image agrees with independent truth.
