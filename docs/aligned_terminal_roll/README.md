# Aligned Terminal-Roll Spatial Investigation

**Status:** Active research workstream
**Parent project:** Back to Grashof — Workspaces
**Baseline:** Stable planar v0.2 kernel remains trusted and unchanged
**Primary workshop note:** `docs/WORKSHOP_2026-08-04_ALIGNED_TERMINAL_ROLL_REDUCTION.md`

## Purpose

This directory is the project operating system for testing the aligned terminal-roll reduction and its possible extension to spherical four-bar fibers.

The workstream separates four questions that must not be conflated:

1. Does an aligned terminal revolute generate pure roll for the position-and-pointing task?
2. Does quotienting that roll leave the expected two-dimensional fixed-position pointing mechanism for a 6R chain?
3. Can useful one-dimensional fibers be defined without coordinate artifacts?
4. Do any such fibers admit exact spherical `RRRR` representations whose rotatability is meaningfully classified by McCarthy-Soh?

A negative result at any later stage does not invalidate an earlier established reduction.

## Working documents

- `PROJECT_PLAN.md` — living project definition, milestone state, and governance.
- `ROADMAP.md` — phase sequence and decision gates.
- `GEOMETRIC_CONVENTIONS.md` — frames, axes, tasks, signs, tolerances, and nomenclature.
- `VALIDATION_PLAN.md` — evidence required for each claim.
- `ASSUMPTION_RISK_REGISTER.md` — research assumptions, project risks, and mitigations.
- `sprints/SPRINT_01_SPATIAL_FOUNDATIONS.md` — first executable sprint.
- `sprints/SPRINT_02_GENERIC_ALIGNED_6R.md` — generic aligned 6R Stage A reduction.
- `sprints/SPRINT_05_EXPLICIT_ONE_DIMENSIONAL_FIBER.md` — Stage C fiber sprint note (closed).
- `sprints/SPRINT_05_REVIEW_CURSOR_WRITEUP.md` — Sprint 05 review and closeout writeup.
- `sprints/SPRINT_06_CANDIDATE_SPHERICAL_EQUIVALENCE.md` — candidate spherical-equivalence planning note.
- `IMPLEMENTATION_RATIONALE.md` / `METHOD_REFERENCES.md` — method audit through Sprint 05 local C11.
- `decisions/` — architecture and research decision records.
- `experiments/` — experiment specifications and result records.
- `checkins/` — completed check-in packets and decisions.

## Governance rule

No stage may claim the result of a later stage.

In particular:

- terminal-roll invariance is not proof of global dexterity;
- correct mobility is not proof of mechanism equivalence;
- a local tangent match is not proof of a global fiber;
- a one-dimensional fiber is not automatically a spherical four-bar;
- a spherical four-bar is not automatically a useful dexterity classifier.

## Current next action

Sprint 05 is closed. Review the Sprint 06 planning note (`SPRINT_06_CANDIDATE_SPHERICAL_EQUIVALENCE.md`) before implementing candidate spherical tests. McCarthy–Soh and exact UR remain blocked.
