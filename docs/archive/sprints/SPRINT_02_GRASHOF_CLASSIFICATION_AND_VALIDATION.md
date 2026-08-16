> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# Sprint 02 — Grashof Classification and Validation Hardening

## Sprint intent

Close the remaining correctness and research-infrastructure gaps in the planar 3R workspace implementation before beginning capability-field development.

The analytical workspace kernel is already functioning and has passed the existing test suite. This sprint does **not** revise the central derivation. It strengthens the mechanism classification, makes the Grashof-to-dexterity relationship visible in the generated atlas, expands independent validation, and places automated quality gates around the repository.

## Sprint goal

For every end-effector radius \(\rho\), the software shall distinguish:

1. whether the equivalent four-bar can assemble;
2. whether it is Grashof, change-point, or non-Grashof;
3. whether the loop is a conventional or degenerate inversion;
4. whether the terminal link \(l_3\) can rotate completely;
5. whether the corresponding Cartesian radius belongs to the dexterous workspace.

These results shall be tested, exported, and visualized reproducibly.

---

## Why this sprint comes before capability fields

The next research phase will replace binary dexterity with graded orientation capability. That work will depend on the same loop construction and radial decomposition used here.

Beginning capability-field development before resolving the following issues would create technical debt in the research foundation:

- non-assemblable link sets are currently labeled as mechanisms;
- coincident ground pivots are classified using conventional inversion names;
- the atlas reports workspace topology but does not yet show the mechanism-state transitions producing it;
- equality and near-boundary validation are not yet systematic;
- the repository lacks continuous integration.

This sprint creates a trusted geometric kernel on which later capability metrics can be built.

---

## Scope

### In scope

- four-bar assemblability;
- explicit degenerate-loop classification;
- improved workspace-topology representation;
- radial mechanism-state evaluation;
- Grashof-versus-dexterity atlas output;
- boundary and randomized property tests;
- GitHub Actions quality gates;
- removal of unused dependencies;
- documentation updates.

### Out of scope

- finite joint limits;
- self-collision or link thickness;
- force, torque, stiffness, or dynamic capability;
- singularity-margin metrics;
- task-based workspace decomposition;
- Zacharias-style capability maps;
- spatial or spherical mechanisms;
- URDF parsing.

---

# Work packages

## WP1 — Four-bar assemblability

### Objective

Prevent impossible link sets from being reported as conventional four-bar mechanisms.

### Required implementation

Add an assembly test based on the polygon inequality:

\[
L_{\max}\leq \sum_{i\neq\max}L_i.
\]

A useful signed form is

\[
m_a=\sum_iL_i-2L_{\max}.
\]

Interpretation:

- \(m_a>0\): assemblable with a finite configuration range;
- \(m_a=0\): degenerate collinear assembly;
- \(m_a<0\): non-assemblable.

### Proposed API

```python
@property
def assembly_margin(self) -> float:
    ...

def is_assemblable(self, *, tol: float = 1e-12) -> bool:
    ...
```

### Classification precedence

`inversion_type()` shall evaluate states in this order:

1. non-assemblable;
2. degenerate ground geometry;
3. conventional Grashof/change-point/non-Grashof classification.

### Acceptance tests

- `FourBar(10, 1, 1, 1)` is non-assemblable.
- `FourBar(3, 1, 1, 1)` is a degenerate collinear assembly.
- Existing valid four-bar classifications remain unchanged.
- A non-assemblable loop can never report full input rotation.

---

## WP2 — Degenerate-loop semantics

### Objective

Preserve mathematically valid workspace calculations without applying misleading conventional mechanism names.

### Required cases

At minimum, identify:

- coincident ground pivots: `ground == 0`;
- zero assembly margin;
- tied shortest links;
- isolated change-point conditions.

### Proposed classification labels

Use explicit labels such as:

- `non-assemblable`;
- `degenerate-coincident-ground-pivots`;
- `degenerate-collinear`;
- `change-point`;
- `special-grashof-tied-shortest`;
- conventional `double-crank`, `crank-rocker`, and `double-rocker`.

The exact names may change, but they must be documented and stable once exported to CSV.

### Design constraint

The exact input-rotation predicate remains geometric and independent of the textual inversion label.

### Acceptance tests

- A zero-ground loop is not labeled `double-crank`.
- The origin can still be classified as dexterous when the interval-containment conditions hold.
- Degenerate labels do not alter the analytical workspace boundaries.
- Exported labels are deterministic under tied-length permutations that represent the same ordered inversion.

---

## WP3 — Structured workspace topology

### Objective

Represent full-dimensional workspace components separately from zero-width boundary sets.

### Problem

A workspace containing a disk plus an isolated circle should not collapse to the single label `degenerate`.

### Proposed model

Introduce a structured result, for example:

```python
@dataclass(frozen=True, slots=True)
class WorkspaceTopology:
    finite_components: tuple[str, ...]
    degenerate_components: tuple[str, ...]
```

Possible finite components:

- `disk`;
- `annulus`;
- `disk_and_annulus`;
- `empty`.

Possible degenerate components:

- `origin_point`;
- `boundary_circle`.

The exact implementation may instead use enums or component objects. The requirement is that topology information must not be lost.

### Compatibility

Retain a human-readable summary string for CLI and CSV use.

### Acceptance tests

Cover:

- empty workspace;
- disk;
- annulus;
- disk plus annulus;
- origin point only;
- boundary circle only;
- disk plus boundary circle;
- annulus plus boundary circle.

---

## WP4 — Radial mechanism-state model

### Objective

Make the relationship between Cartesian radius and equivalent mechanism class directly inspectable.

### Proposed data structure

```python
@dataclass(frozen=True, slots=True)
class RadialMechanismState:
    rho: float
    assemblable: bool
    assembly_margin: float
    grashof_margin: float
    grashof_class: str
    inversion_type: str
    input_can_fully_rotate: bool
    dexterous: bool
```

For sampled atlas data, include a normalized radius:

\[
\bar{\rho}=\rho/l_1.
\]

### Required invariant

For unrestricted planar 3R geometry:

```python
state.input_can_fully_rotate == state.dexterous
```

This invariant shall be asserted in tests and atlas generation.

### Acceptance tests

- States outside the reachable workspace are represented, not silently discarded.
- Non-assemblable and assemblable regions are distinguishable.
- Every change in mechanism label occurs at a reproducible analytical or sampled radial boundary.
- The terminal-link rotation flag exactly matches the analytical dexterity predicate.

---

## WP5 — Grashof-to-dexterity atlas

### Objective

Generate the figure that demonstrates the central research claim rather than only plotting the resulting workspace.

### Required outputs

For each selected link-length family, generate:

1. the existing Cartesian reachable/dexterous workspace plot;
2. a radial mechanism-state plot;
3. a machine-readable CSV row set.

### Radial plot contents

The horizontal axis is \(\rho\) or normalized \(\rho/l_1\).

Show aligned bands or tracks for:

- position reachable;
- loop assemblable;
- Grashof/change-point/non-Grashof;
- inversion type;
- terminal link fully rotatable;
- dexterous workspace.

Analytical boundary radii shall be drawn and labeled.

### Minimum example families

| Family | Link lengths \((l_1,l_2,l_3)\) | Purpose |
|---|---:|---|
| Symmetric proximal links | \(2,2,1\) | Simple dexterous disk |
| Terminal link too long | \(1,1,3\) | Empty dexterous workspace |
| Unequal proximal links | \(3,1,2.5\) | Inner dexterous island |
| Split topology | \(3,2,1.5\) | Disk plus annulus |
| Degenerate boundary | \(3,2,2\) | Change-point circle |
| Generic annulus | Select from sweep | No central dexterous disk |

### CSV requirements

Each radial sample or analytical interval shall include:

- link lengths;
- normalized link ratios;
- radius and normalized radius;
- reachable flag;
- assemblable flag;
- assembly margin;
- Grashof margin;
- Grashof class;
- inversion label;
- input-rotation flag;
- dexterous flag;
- analytical boundary identifier, where applicable.

### Acceptance criteria

- The atlas visually exposes why the workspace changes topology.
- The plot does not imply that generic Grashof membership alone is sufficient for dexterity.
- CSV and plotted classifications come from the same state-evaluation API.
- Atlas generation is deterministic.

---

## WP6 — Validation hardening

### Objective

Strengthen evidence that the analytical predicates and classifications are correct across parameter space.

### Boundary validation

For every analytical radial boundary \(\rho_b\), test:

\[
\rho_b-\epsilon,\qquad \rho_b,\qquad \rho_b+\epsilon.
\]

Select \(\epsilon\) relative to the link scale, for example:

\[
\epsilon=10^{-8}\max(l_1,l_2,l_3).
\]

### Orientation validation

The numerical orientation set must always include the extrema producing the wrist-distance bounds:

\[
\phi=0,\qquad \phi=\pi.
\]

Do not depend on an even sample count to include them accidentally.

### Seeded property tests

Add a deterministic randomized test:

- generate at least 250 valid positive link triples;
- evaluate at least 20 radii per triple;
- compare the analytical dexterity predicate against dense orientation sampling;
- store the random seed;
- report the failing geometry and radius in assertion messages.

A slower, larger stress test may be marked separately from the normal unit suite.

### Four-bar consistency properties

Test:

- `input_can_fully_rotate` implies assemblable;
- exact input rotation equals planar dexterity under the documented reduction;
- change-point equality is accepted within tolerance;
- results are scale invariant when all lengths and \(\rho\) are multiplied by the same positive constant.

### Acceptance criteria

- Normal test suite remains fast enough for every commit.
- A larger stress suite can run in CI or manually.
- Boundary failures identify the exact link set, radius, and expected state.
- No analytical result is replaced with sampled classification.

---

## WP7 — Continuous integration and repository hygiene

### Objective

Prevent regressions as Cursor-assisted development accelerates.

### GitHub Actions workflow

Run on pushes and pull requests:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src
grashof-workspace --atlas --output-dir outputs/atlas
```

Upload generated atlas artifacts on failure or on manually triggered runs if useful.

### Dependency cleanup

Remove NumPy unless the implementation begins using it during this sprint.

### Recommended additional checks

- verify package installation in a clean environment;
- ensure the CLI exits nonzero on invalid link lengths;
- ensure generated files are not committed unless intentionally treated as reference artifacts;
- add a `python -m grashof_workspace...` fallback only if needed.

### Acceptance criteria

- The default branch displays a passing CI status.
- Linting, typing, tests, and atlas generation all pass from a clean checkout.
- No unused runtime dependencies remain.

---

# Implementation sequence

## Step 1 — Lock current behavior

Before changing classifications:

- retain all existing passing tests;
- add regression tests for current analytical interval results;
- record representative CLI output.

## Step 2 — Add assemblability and degeneracy

Implement WP1 and WP2 first because every later exported classification depends on these semantics.

## Step 3 — Refactor topology representation

Introduce the structured topology model while preserving the existing CLI-facing summary.

## Step 4 — Build one radial-state API

All plots, CSV export, and tests shall consume the same mechanism-state evaluation function.

## Step 5 — Extend atlas outputs

Create the radial state figure and enriched CSV.

## Step 6 — Harden validation

Add boundary probes, scale-invariance tests, and seeded randomized comparisons.

## Step 7 — Add CI and clean dependencies

Make the quality gate mandatory before merging the sprint.

---

# Suggested issue breakdown

## S02-01 — Four-bar assembly model

**Deliverable:** `assembly_margin`, `is_assemblable`, tests, and documentation.

## S02-02 — Degenerate inversion classifications

**Deliverable:** explicit labels and classification precedence.

## S02-03 — Structured workspace topology

**Deliverable:** topology/component data model and compatibility summary.

## S02-04 — Radial mechanism-state API

**Deliverable:** one typed record connecting \(\rho\), Grashof state, rotatability, and dexterity.

## S02-05 — Radial Grashof atlas visualization

**Deliverable:** aligned state-band figure for all canonical link families.

## S02-06 — Atlas CSV enrichment

**Deliverable:** machine-readable mechanism-state export.

## S02-07 — Boundary and property testing

**Deliverable:** deterministic boundary, scale, and randomized tests.

## S02-08 — GitHub Actions and dependency cleanup

**Deliverable:** passing CI workflow and minimal dependency set.

---

# Definition of done

Sprint 02 is complete when:

- impossible loops are never labeled as conventional mechanisms;
- zero-ground and collinear cases have explicit degenerate classifications;
- workspace topology preserves both finite-area and zero-width components;
- a single radial-state API reports assemblability, Grashof state, inversion type, input rotatability, and dexterity;
- the atlas shows the mechanism-state transitions underlying each workspace;
- analytical dexterity and exact terminal-link rotatability agree for every tested case;
- deterministic boundary and randomized property tests pass;
- CI runs tests, Ruff, mypy, and atlas generation on every pull request;
- all equations and exported labels are documented;
- no capability-field functionality has entered the codebase.

---

# Sprint review demonstration

At sprint review, run:

```bash
pytest
ruff check .
mypy src
grashof-workspace --atlas --output-dir outputs/atlas
```

Then present, for the split-topology example \((3,2,1.5)\):

1. the Cartesian workspace figure;
2. the radial mechanism-state figure;
3. the analytical boundary equations;
4. the CSV rows around each boundary;
5. numerical orientation validation immediately inside and outside each region.

The demonstration should make the following statement visually and computationally evident:

> Fixing a planar 3R end-effector position creates an equivalent four-bar. The dexterous workspace consists exactly of the radii for which the terminal link of that ordered inversion can rotate completely—not merely the radii for which the unordered link set satisfies a generic Grashof inequality.

---

# Exit decision

Once Sprint 02 passes review, freeze the unrestricted planar 3R workspace kernel as `v0.2`.

The next sprint may begin graded planar orientation capability:

\[
C(p)=\frac{\mu\{\phi\in S^1:\phi\text{ is reachable at }p\}}{2\pi},
\]

while retaining the binary dexterous workspace as the level set

\[
W_D=\{p:C(p)=1\}.
\]
