# Report — Aligned Terminal-Roll Visual Probe

**Date:** 2026-08-06  
**Status:** Closeout  
**Production status:** Isolated visual probe — not certification

## Purpose

This report records what the visualization-first probe produced and what it deliberately does **not** claim.

## What was built

A synthetic aligned-terminal 6R architecture with exact adjacent intersections among `R1`–`R5`, homogeneous-transform forward kinematics, virtual spherical closure display, terminal-roll quotient graphics, compound-parent enumeration (`SRUU` / `SURU` / `SUUR`), and coordinate-dependent candidate `RRRR` axis tuples rendered as static HTML.

Primary outputs live under `outputs/aligned_terminal_visual_probe/`:

- `index.html` — interactive static browser
- `scenes/` — Scenes A–D
- `contact_sheets/candidates.html`
- `data/axis_relationships.json`, `compound_parents.json`, `candidates.json`, `visual_audit.json`

## Visual findings

1. The physical chain, joint origins, infinite axes, task point `p`, and pointing `d` are readable at the default asymmetric pose.
2. The virtual spherical closure sits at the FK task point with tool-aligned `Sx`, `Sy`, `Sz`.
3. Changing only `q6` preserves `p` and `d` while the tool triad roll changes; `R6` remains drawn (quotiented, not deleted).
4. All three combinatorial pair sets enable on this fixture: `P12_P34`→`SRUU`, `P12_P45`→`SURU`, `P23_P45`→`SUUR`.
5. Each enabled parent expands to 12 candidates (36 total). Enumeration is coordinate-convention-dependent and not exhaustive over the spherical-axis continuum.

## Historical failure mapping

The first two previously rejected topology-derived spherical-four-bar interpretations from the ATR fiber track **cannot be rematerialized** here without preserved axis provenance from those experiments. They are recorded in `data/visual_audit.json` as `unmappable_without_prior_axis_provenance`.

## False-positive caution

Single-pose visual near-concurrency can look persuasive while branch-wide concurrency fails. The audit bundle includes explicit false-positive / one-pose-pass captions. **Visual passage at one pose is insufficient.**

## Shortlist for a later validation project

Candidates that select `Sz` (task-aligned spherical coordinate) from each enabled parent are listed in `data/visual_audit.json` under `shortlist_for_later_validation`. That shortlist is a screening convenience only.

A later validation project may add least-squares concurrency residuals, branch-wide concurrency, spherical arc invariance, inactive-coordinate locking, fiber continuation, motion equivalence, and McCarthy–Soh classification.

## Forbidden claims

- No candidate is called a spherical four-bar based on this project alone.
- No mobility proof beyond descriptive bookkeeping is asserted.
- The planar analytical kernel remains untouched; this package must not be imported into planar modules.

## Reproduction

```bash
.venv/bin/grashof-visual-probe --output-dir outputs/aligned_terminal_visual_probe
.venv/bin/pytest tests/visual_probe -q
```
