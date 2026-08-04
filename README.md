# Grashof Workspace

A small research codebase for analytically characterizing planar 3R manipulator workspaces through the equivalent four-bar loop formed when the end-effector position is fixed.

## MVP question

For a planar 3R manipulator with link lengths \(l_1,l_2,l_3\), which Cartesian positions permit the terminal link to achieve every planar orientation?

Fixing a candidate end-effector position \(p\) closes the chain into a four-bar:

- ground: \(d=\|p\|\)
- input crank: \(l_3\)
- coupler: \(l_2\)
- output: \(l_1\)

The terminal link can rotate through \(2\pi\) exactly when its moving endpoint remains inside the reachable annulus of the first two links for every input angle.

## Scope of the first milestone

Included:

- rigid planar 3R geometry
- unrestricted revolute joints
- analytical reachable workspace
- analytical dexterous workspace
- equivalent four-bar construction
- assemblability and degenerate-loop classification
- Grashof classification and exact input-rotation test
- radial mechanism-state atlas
- sampled validation of the analytical result
- reproducible plots, tests, and CI

Explicitly deferred:

- joint limits
- self-collision and link thickness
- force, torque, stiffness, or dynamics
- singularity margins
- task-based capability fields
- spatial 6R manipulators

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" --config-settings editable_mode=strict
pytest
ruff check .
mypy src
grashof-workspace --l1 2.0 --l2 2.0 --l3 1.0 --output workspace.png
grashof-workspace --atlas --output-dir outputs/atlas
```

Validation uses exact interval containment as the workspace definition. Independent orientation sampling must report coverage `1.0` at dexterous radii (analytic tolerance `1e-12`) and always includes the wrist-distance extrema \(\phi=0,\pi\). Atlas generation writes:

- `atlas.csv` — family topology summary, including `contains_grashof_non_dexterous`
- `radial_mechanism_states.csv` — exact segment/boundary mechanism states
- `dashboard.json` + `index.html` — static radial-states dashboard
- Cartesian and radial-state figures under `figures/`
- virtual four-bar traces under `mechanisms/`

Open `outputs/atlas/index.html` directly in a browser (no server required).

**Grashof does not imply dexterity.** The canonical counterexample is `unequal_proximal` with \((l_1,l_2,l_3)=(3,1,2.5)\): the outer Grashof double-rocker band is reachable but not dexterous because the designated input cannot fully rotate.

## Repository map

```text
src/grashof_workspace/
  fourbar.py       Equivalent closed-loop model and Grashof tests
  planar3r.py      Analytical 3R workspace and radial mechanism state
  atlas.py         Link-ratio CSV atlas and experiment figures
  plotting.py      Cartesian and radial-state plots
  cli.py           Command-line entry point
src/sixr_grashof/
  classification/  McCarthy–Soh T1–T4 spherical 4R types
  architectures/   Synthetic 6R A/B/C generators
  kinematics/      Axis lines and forward kinematics
  reductions/      Concurrency residual labels
  visualization/   Reproducible axis plots
tests/             Mathematical regression and property tests
docs/              Charter, equations, decisions, roadmap, and sprint plans
.github/workflows/ Continuous integration
.cursor/rules/     Guardrails for Cursor-assisted development
```

## Core analytical result

Let

\[
r_{\min}=|l_1-l_2|,\qquad r_{\max}=l_1+l_2,\qquad \rho=\|p\|.
\]

As the desired end-effector orientation varies, the wrist distance from the base ranges over

\[
[|\rho-l_3|,\ \rho+l_3].
\]

The position is dexterous when this entire interval is contained in the 2R reachable annulus:

\[
|\rho-l_3|\ge r_{\min},
\qquad
\rho+l_3\le r_{\max}.
\]

The implementation keeps this exact geometric test separate from the conventional Grashof linkage classification so the research result is never hidden behind a label.

## Synthetic 6R spherical Grashof (Sprints 0–1)

Package `sixr_grashof` adds McCarthy–Soh spherical 4R classification and three idealized 6R architectures. See `docs/PROJECT_PLAN_6R_SPHERICAL_GRASHOF.md`, `docs/theory.md`, and `docs/synthetic_architectures.md`.

```bash
pytest tests/test_spherical_classification.py tests/test_known_linkage_types.py tests/test_architectures.py
sixr-grashof --architecture A --output results/arch_a.png
python scripts/generate_sprint01_visualizations.py
```

Figures land in `results/sprint00_classification/` (McCarthy–Soh types, spherical four-bars) and `results/sprint01_geometry/` (architectures A/B/C, residual sweeps).

Static HTML dashboards (no server):

```bash
python scripts/generate_sprint01_visualizations.py
python scripts/generate_sprint06_dashboard.py
# or: sixr-grashof --dashboard
open results/index.html
open results/sprint00_dashboard/index.html
open results/sprint06_dashboard/index.html
```

Interpretation of Gates 1–5 and inspector limitations: `docs/sprint06_interpretation.md`.
Sprint 5 densified experiment write-up: `docs/sprint05_results_summary.md`.

Hand-orientation link is the virtual output \(\beta\). Types `{2,3,10,11}` are documented as a dexterity **hypothesis**, never as an encoded truth.
