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
- Grashof classification and exact input-rotation test
- sampled validation of the analytical result
- reproducible plots and tests

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
pip install -e ".[dev]"
pytest
grashof-workspace --l1 2.0 --l2 2.0 --l3 1.0 --output workspace.png
grashof-workspace --atlas --output-dir outputs/atlas
```

Validation uses exact interval containment as the workspace definition. Independent orientation sampling must report coverage `1.0` at dexterous radii (analytic tolerance `1e-12`). Atlas rows that disagree are marked `fail@rho=...` rather than silently accepted.

## Repository map

```text
src/grashof_workspace/
  fourbar.py       Equivalent closed-loop model and Grashof tests
  planar3r.py      Analytical 3R workspace model
  atlas.py         Link-ratio CSV atlas and experiment figures
  plotting.py      Reproducible workspace plots
  cli.py           Command-line entry point
tests/             Mathematical regression tests
docs/              Charter, equations, decisions, roadmap, and sprint plan
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
