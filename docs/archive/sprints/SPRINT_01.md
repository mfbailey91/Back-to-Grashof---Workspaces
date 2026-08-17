> **Completed / historical sprint document.** Not active implementation authority. See `docs/CURRENT_STATUS.md` and `docs/ROADMAP.md`.


# Sprint 01 — Analytical Planar 3R Workspace

## Sprint goal

Produce a mathematically validated implementation of the reachable and dexterous position workspaces of an unrestricted planar 3R manipulator using the equivalent four-bar reduction.

## User story

As a robotics researcher, I want to specify \(l_1,l_2,l_3\) and obtain the analytical workspace regions, the corresponding four-bar classification, and a validation plot so that I can test the Grashof-based characterization before extending it to capability fields.

## Work packages

### WP1 — Mathematical kernel

- implement `Planar3R`;
- compute the complete position-reachable radial interval;
- compute exact dexterous radial components;
- preserve equality and degenerate-circle cases;
- document all equations and conventions.

### WP2 — Equivalent four-bar

- construct the ordered loop \((\rho,l_3,l_2,l_1)\);
- compute Grashof margin;
- classify the inversion conservatively;
- compute exact full rotation of the terminal link;
- test that workspace membership and link rotatability are identical.

### WP3 — Independent validation

- sample terminal orientations for selected Cartesian positions;
- verify interior, exterior, and boundary cases;
- run a grid sweep over link ratios;
- fail tests if analytical and sampled classifications disagree beyond tolerance.

### WP4 — Visualization

- plot reachable workspace;
- overlay every dexterous component;
- label link lengths and radial boundaries;
- export a repeatable PNG from the CLI.

## Acceptance criteria

- `pytest` passes from a clean environment.
- The CLI creates a workspace figure from three link lengths.
- Every analytical dexterous interval is independently verified by orientation sampling.
- The code distinguishes generic Grashof classification from exact input-link rotatability.
- Assumptions and exclusions are visible in the README.
- No joint-limit, dynamics, or task-capability code is introduced in this sprint.

## Suggested first experiment matrix

| Family | Example | Expected topology |
|---|---:|---|
| Equal proximal links | 2, 2, 1 | Dexterous disk |
| Long terminal link | 1, 1, 3 | Empty |
| Unequal proximal links | 3, 1, 2.5 | Inner dexterous island |
| Boundary case | 3, 2, 2 | Degenerate outer component |
| Generic annular case | Select by parameter sweep | Annulus or split components |

## Exit artifact

A figure set and CSV atlas indexed by normalized ratios

\[
\lambda_2=l_2/l_1,\qquad \lambda_3=l_3/l_1,
\]

with analytical topology, boundaries, Grashof margin at each boundary, and sampled validation status.
