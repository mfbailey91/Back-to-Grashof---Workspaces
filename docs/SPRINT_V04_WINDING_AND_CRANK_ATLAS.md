# Sprint V04 — True Winding and Crank Atlas

**Status:** UUUR-first numerical winding  
**Purpose:** compute winding numbers of the two tool-U coordinates from continued one-DOF closure branches, then classify each tool axis as crank or rocker from that winding.

## Research question

For a V02B physical UUUR mechanism on a returned one-DOF closure branch, what integer windings do `tool_alpha` and `tool_beta` accumulate, and does either coordinate full-rotate?

V04 answers only this numerical question for UUUR first.

It does **not**:

- promote planar Grashof inequalities;
- treat the twelve tool-axis explorer cases as twelve separate closure solves;
- mine descriptor trends (V05);
- classify other families until UUUR winding is verified.

## Inputs

Use V02B physical geometries only. V01/V02 random-descriptor samples and mock windings remain scaffold/test data and must not appear in the V04 crank atlas.

Each physical mechanism is solved once with the V03 seven-coordinate PoE closure kernel. Both tool-U windings are read from that single continued cycle.

## Angle unwrap

Along a continuation trace, each scalar joint coordinate is stored in a continuous (unwrapped) chart. Given successive raw samples `θ_k`, the unwrap recurrence is:

```text
Δ_k = θ_k − θ_{k−1}
θ̃_k = θ̃_{k−1} + (Δ_k − 2π round(Δ_k / 2π))
θ̃_0 = θ_0
```

Interior steps with `|Δ| ≪ π` leave the unwrap unchanged. A raw jump near `±2π` is absorbed into the continuous chart rather than counted as motion.

## Branch return

Start at the reference assembly `q_0 = 0`. Continue with pseudo-arclength predictor/corrector.

1. Leave a departure neighborhood when the wrapped configuration distance from `q_0` exceeds `leave_tol`.
2. After departure, declare **return** when every scalar coordinate is within `return_tol` of an integer multiple of `2π` relative to `q_0` (equivalently, wrapped distance to `q_0` is below `return_tol`) and the closure residual remains small.
3. If the chosen direction fails within `max_steps`, try the opposite direction once. Do not invent a second branch topology claim from that second attempt.

An open (non-returning) trace within budget is labeled `open_branch`, not a crank.

## Winding

For a returned cycle with unwrapped endpoint `θ̃_N` and start `θ̃_0`:

```text
w_i = round( (θ̃_N,i − θ̃_0,i) / 2π )
```

for each tool coordinate `i ∈ {tool_alpha, tool_beta}`:

```text
W = (w_alpha, w_beta)
```

## Classification (link-specific full rotation)

These labels are **not** conventional planar Grashof class names. They are link-specific full-rotation tests on the tool-U coordinates of one continued branch.

| Condition | Label |
| --- | --- |
| returned and `\|w_i\| ≥ 1` | `crank` |
| returned and `w_i = 0` | `rocker` |
| no return within budget | `open_branch` |
| singularity / corrector failure (under-specified) | `change_point` or `invalid` (mark `REVIEW` / research note) |

Tool ranges reported in the atlas are the peak-to-peak span of the unwrapped tool coordinate on the continued segment.

## UUUR-first atlas procedure

1. Continue canonical `uuur_physical_000` until return (or budget).
2. Continue additional UUUR physical perturbations from V02B until the atlas contains at least one crank and one rocker example among the two tool axes across selected samples.
3. If neither class appears under the default budget, leave status `REVIEW` rather than forcing a label.

## Artifacts

- `v04_uuur_cycle_traces.json`
- `v04_uuur_winding_results.json`
- unwrapped tool-angle plots
- winding / classification summary plots
- representative crank and rocker cards
- `sprint_04_winding_and_crank.html`

## Guardrails

- Winding must come from continued branches, never from V02 mock heuristics.
- Conventional planar `double-crank` / `crank-rocker` / `double-rocker` labels stay out of V04.
- S-joint chart axes remain solver coordinates only.
- Dexterity and pointing-space fiber fields belong to later sprints.

## Acceptance

V04 (UUUR-first) is complete when:

1. unwrap, return detection, and winding are named and tested (interior / exterior / boundary);
2. at least one UUUR physical sample yields a defined winding from a continued branch;
3. the HTML readout visualizes at least one crank and one rocker example;
4. mock V02 classifications are not used as crank evidence.
