# Audit — Tool-A / Tool-B Drive Semantics and the Role of phi

**Status:** corrective audit after V04B  
**Scope:** recent spatial four-bar explorer commits from Sprint V02 through V04B

## Executive conclusion

The original explorer intent was:

```text
task-derived virtual U
    -> R_a(alpha) + R_b(beta)
    -> ask whether tool_a can circulate
    -> ask whether tool_b can circulate
```

`tool_a` and `tool_b` are two rotatability questions on the same physical four-bar.
They are not two unrelated mechanism families.

The V03 solver correctly improved the implementation by solving one one-DOF closure
branch and reading both `alpha(s)` and `beta(s)` from that branch.  However, the
V03 GIFs only visualized the arclength continuation branch.  Because the canonical
branches are often strongly alpha-dominated, the figures could be read as though
the mechanism were only being driven about tool A.

V04B introduced `phi` only as a sensitivity experiment: rotate the arbitrarily
chosen virtual-U coordinate frame and see whether the reported winding changes.
The answer changed with `phi`.  That means the virtual-U axes cannot be chosen
arbitrarily.  It does **not** establish `phi` as a physical atlas parameter.

## Commit audit

### `ff84976` — Sprint V02 mock branch scaffold

Good conceptual state:

```text
family x {tool_a, tool_b}
```

The readout visibly separated `*_tool_a` and `*_tool_b`.  The values were mock
placeholders, but the questions were explicit.

### `9f34652` — shared seven-coordinate V03 closure/continuation

Good solver correction:

```text
one UXXX mechanism branch
    -> alpha(s), beta(s)
    -> two eventual classifications
```

This removed redundant closure solves without removing either rotatability question.

### `8b028aa` — V03 driven-branch GIFs

Visualization gap:

- one arclength-driven GIF per family;
- no prescribed tool-A view;
- no prescribed tool-B view;
- canonical traces can be strongly alpha-dominated.

The GIFs proved local one-DOF closure motion, but did not visually prove that both
tool-axis questions were being exercised.

### `1b55a45` — V04 true winding

Good numerical state:

```text
returned cycle -> (w_alpha, w_beta)
```

Both tool coordinates are classified from the same mechanism cycle.

### `330e76e` — V04B virtual-U robustness

Useful diagnostic, but the presentation needed a guardrail.

`phi` rotates the chosen virtual-U coordinate frame while holding the rest of the
standalone four-bar fixed.  The experiment tests sensitivity to that choice.

Correct interpretation:

> `phi` is diagnostic sensitivity evidence.  It must not be promoted to an atlas
> parameter for dexterity unless a task-derived pointing-fiber construction shows
> that changing `phi` corresponds to a different legitimate fiber of the original
> virtual spherical joint.

## Corrected visualization contract

The explorer must now publish, for every ordered family:

1. **tool-A prescribed drive attempt**
   - prescribe `tool_alpha` from 0 toward `2*pi`;
   - solve the remaining six scalar coordinates from the six closure constraints;
   - animate the physical four-bar;
   - report whether the full input turn completed or stopped at a turning/failure point.

2. **tool-B prescribed drive attempt**
   - prescribe `tool_beta` from 0 toward `2*pi`;
   - solve the remaining six scalar coordinates;
   - animate the same physical four-bar;
   - report the same status.

These are designated-input visual diagnostics.  They do not replace the returned-cycle
winding calculation in V04.

## Proof-of-resolution checklist

This correction is resolved only when all of the following are true:

- [ ] generated V03 readout shows A and B side-by-side for all six families;
- [ ] generated artifact set contains 12 axis-drive GIFs;
- [ ] generated artifact set contains 12 axis-drive coordinate plots;
- [ ] axis-drive JSON records `tool_axis`, `reached_angle`, `full_input_turn`, and status;
- [ ] tests verify the prescribed coordinate equals its target while closure remains satisfied;
- [ ] V04B source calls the `phi` sweep `diagnostic_sensitivity_only`;
- [ ] V04B committed JSON contains `experiment_role = diagnostic_sensitivity_only`;
- [ ] V04B HTML visibly says `DIAGNOSTIC ONLY`;
- [ ] V04B docs state that `phi` is not a dexterity-atlas parameter without task-derived fiber provenance.

## Research guardrail

The standalone spatial four-bar explorer remains a mechanism laboratory.

For dexterity evidence the eventual chain is:

```text
fixed task point
    -> S_v
    -> aligned terminal-roll quotient
    -> two-DOF pointing parent
    -> explicit pointing constraint h(d)=c
    -> induced U_v = R_a R_b
    -> induced UXXX one-DOF mechanism
    -> tool-A / tool-B rotatability
```

Arbitrary `phi` rotation is not inserted into this chain.


## Verification commands after applying the patch

```bash
pytest -q tests/test_spatial4bar_axis_drive.py tests/test_spatial4bar_v03.py
grashof-spatial4bar-explorer \
  --outdir results/spatial4bar_explorer/axis_ab_resolution \
  --sample-count 6
```

Expected generated evidence:

```text
figures/v03_uuur_tool_a_drive.gif
figures/v03_uuur_tool_b_drive.gif
...
figures/v03_urrs_tool_a_drive.gif
figures/v03_urrs_tool_b_drive.gif

figures/v03_uuur_tool_a_drive.png
figures/v03_uuur_tool_b_drive.png
...
figures/v03_urrs_tool_a_drive.png
figures/v03_urrs_tool_b_drive.png

data/v03_tool_axis_drive_traces.json
```

There must be 12 A/B GIFs and 12 A/B coordinate plots.  The generated Sprint V03
page must display A and B side-by-side for each of the six families.

The V04B generated page must visibly contain `DIAGNOSTIC ONLY`, and its JSON must
contain:

```json
"experiment_role": "diagnostic_sensitivity_only"
```
