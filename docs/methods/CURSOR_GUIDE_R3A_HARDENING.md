# Cursor Guide — R3A-H Natural-Leaf Evidence Hardening

**Base branch:** `main` at or after `959463b4bec24c9a9fc2240142d0f4cfc189f8d2`  
**Recommended branch:** `r3a-hardening-evidence-gates`  
**Authority:** `docs/methods/R3A_HARDENING_EXECUTION.md`

---

## 1. Branch setup

```bash
git switch main
git pull --ff-only
git switch -c r3a-hardening-evidence-gates
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" --config-settings editable_mode=strict
pytest
ruff check .
mypy src
```

Freeze the baseline test count and current R3A artifact disposition before editing.

---

## 2. Implementation order

Do not begin with re-seeding or continuation tuning. Correct status and artifact authority first.

```text
H0 semantics and stage graph
H1 direct reference
H2 re-seeding
H3 transversality/chart overlap
H4 family completeness/mode fidelity
H5 comparison acceptance
H6 readout/CI/closeout
```

Each slice should be separately reviewable.

---

# H0 — Stage authority and deterministic identity

## A. `models.py`

Add records similar to:

```python
@dataclass(frozen=True, slots=True)
class StageArtifactRef:
    stage: str
    path: str
    sha256: str
    config_hash: str
    mode: str
    probe_ids: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class StageResult:
    stage: str
    stage_status: ProcessStageStatus
    scientific_disposition: str
    config_hash: str
    mode: str
    probe_ids: tuple[str, ...]
    inputs: tuple[StageArtifactRef, ...]
    outputs: tuple[StageArtifactRef, ...]
    limitations: tuple[str, ...]
```

Add:

```python
class FamilyAdmissibilityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"
```

Change `NaturalLeafCertificate` so it stores:

```text
leaf_component_status
family_admissibility_status
accepted_for_reconstruction
```

Do not infer family admissibility from `returned`.

## B. `uuru_leaf.py`

Replace:

```python
return str(abs(hash(blob)))
```

with canonical SHA-256:

```python
payload = {
    "chart_id": chart.chart_id,
    "sequence": chart.sequence,
    "basis": np.asarray(chart.basis).round(15).tolist(),
    "reference": np.asarray(chart.reference).round(15).tolist(),
    "lambda_fixed": float(lambda_fixed),
}
blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
return hashlib.sha256(blob.encode("utf-8")).hexdigest()
```

At leaf issuance:

```text
component status may be EXACT_ON_COMPONENT
family admissibility remains UNRESOLVED
accepted_for_reconstruction = false
```

until H2/H3/H4 run.

## C. `cli.py`

Implement prerequisite map:

```python
PREREQUISITES = {
    "fixture": ("manifest",),
    "truth": ("manifest", "fixture"),
    "source-control": ("manifest", "fixture", "truth"),
    "leaves": ("manifest", "fixture", "truth"),
    "compare": ("manifest", "fixture", "truth", "source-control", "leaves"),
    "render": ("manifest", "fixture", "truth", "source-control", "leaves", "compare"),
}
```

Every stage validates config hash, mode, and probe scope.  
Do not synthesize empty inputs in `compare`.

## D. `comparison.py`

Before metrics:

```python
if any(required artifact missing):
    raise FileNotFoundError(...)
```

Delete the current behavior that paints empty masks and still writes a completed comparison.

For negative probes, require feasible-set recall:

```python
if miss is None or miss > threshold:
    return PARTIAL
if fp is None or fp > threshold:
    return REJECTED
```

An empty reconstruction must fail.

## E. `readout.py`

If real artifacts are missing:

```text
either raise FileNotFoundError
or render a panel with a prominent SCAFFOLD_NO_DATA watermark
```

Do not generate evidence-like flat-line plots.

## H0 tests

Write tests before implementation:

```text
missing compare inputs raises
manifest status correct
geometry hash stable in subprocess
empty P3/P5 reconstruction does not pass
returned component remains family-unresolved
```

---

# H1 — Independent direct confirmation cells

## A. `models.py`

Add `DirectReferenceCell`.

## B. `direct_truth.py`

Build confirmation records from each target direction. Preserve direct status.

Count both:

```text
strict feasible NOT_FOUND
strict feasible UNRESOLVED
```

as direct-reference blockers.

## C. `comparison.py`

Load direct truth and create a resolved-direct mask. Never derive the direct mask from the oracle.

Compute separate metric objects:

```text
direct_vs_oracle
source_vs_direct
natural_vs_direct
source_vs_oracle
natural_vs_oracle
```

`direct_complete` is `None` when any strict confirmation cell is unresolved.

## H1 tests

Use tiny grids with explicit synthetic statuses to prove:

- oracle does not rewrite direct;
- strict feasible unresolved blocks;
- boundary cells are excluded from strict denominators;
- direct/source/natural masks remain independent.

---

# H2 — Real re-seeding

## A. `uuru_leaf.py`

Extend `problem_from_source_seed()`:

```python
def problem_from_source_seed(..., lambda_fixed: float | None = None)
```

When supplied, preserve the original family parameter. Recover only the initial `alpha,beta`.

Add:

```python
def child_tangent(problem, x) -> np.ndarray:
    basis = orthonormal_tangent_basis(problem.jacobian(x), expected_nullity=1)
    t = basis[:, 0]
    phys = t[2:7]
    return phys / np.linalg.norm(phys)
```

## B. `leaf_family.py`

Replace `reseed_audit(q_samples, pointing, ...)` completely.

Pseudo-code:

```python
def audit_reseeded_component(arm, chart, original_problem, original_samples, ...):
    audits = []
    for sample in choose_arclength_samples(original_samples, count):
        rebuilt = problem_from_source_seed(
            arm,
            chart,
            sample.q_source,
            original_problem.p_star,
            leaf_id=...,
            lambda_fixed=original_problem.lambda_fixed,
        )
        if rebuilt is None:
            audits.append(UNRESOLVED)
            continue
        problem_i, x_i = rebuilt
        reseeded_samples, branch_status, returned = continue_uuru_leaf(...)
        q_dist = symmetric_q_distance(...)
        p_dist = symmetric_pointing_distance(...)
        tangent_err = signed_subspace_error(
            child_tangent(original_problem, sample.x),
            child_tangent(problem_i, x_i),
        )
        component_identity = ...
        audits.append(...)
    return aggregate(audits)
```

Continue the same branch budget and direction policy.

## C. Tests

Add one intentionally wrong-lambda case and one budget-limited case. The current self-distance test must be deleted.

---

# H3 — Transversality and chart overlap

## A. `leaf_family.py`

Store internal work records during discovery:

```text
certificate
problem
seed_x
seed_q
chart
lambda_fixed
```

After deduplication, sort leaves circularly by `lambda_fixed` within each chart.

For each neighboring pair:

1. choose nearest compatible samples;
2. compute `t_s` from the actual child Jacobian;
3. compute wrapped `delta_q / delta_lambda`;
4. project into `ker(Jp)`;
5. remove `t_s`;
6. compute two-column SVD;
7. enforce config threshold.

Write a per-neighbor audit, then aggregate.

## B. Chart overlap

For candidate overlap leaves:

```text
compare source-Q sets first
compare recovered rotations
transform chart coordinates
compare pointing sets
check component identity
```

Replace the current directed-distance asymmetry heuristic.

## C. Acceptance recomputation

After reseed, transversality, interval, and chart audits:

```python
leaf = replace(
    leaf,
    family_admissibility_status=...,
    accepted_for_reconstruction=component_ok and family_ok and interval_ok,
)
```

## H3 tests

- identical leaves duplicate;
- same task image but disjoint Q components are not duplicates;
- actual colinear child/cross direction fails;
- rank-two pair passes configured sigma;
- one bad neighbor prevents family pass;
- same source curve in two charts is compatible.

---

# H4 — Completeness and mode fidelity

## A. `source_control.py`

Replace global `unresolved_c_intervals` logic with per-`c` records.

Track each projected seed and continued component.

## B. `leaf_family.py`

Track circular lambda intervals, uncovered bins, critical/singular bins, and chart gaps.

## C. `write_leaves_stage()`

Remove silent caps:

```python
max_leaves=min(6, ...)
lambda_bins=min(5, ...)
max_steps=12
```

Use frozen mode values. Add a named `ci` override if needed.

## H4 tests

- one failed `c` bin creates unresolved interval;
- one open natural leaf creates unresolved lambda interval;
- full mode equals config;
- CI override is explicitly labeled and cannot produce full-campaign disposition.

---

# H5 — Reconstruction acceptance

Implement one helper:

```python
def reconstruction_pass(metrics, config) -> bool:
    return (
        metrics.missed_covered_fraction is not None
        and metrics.missed_covered_fraction <= config.max_missed...
        and metrics.false_positive_fraction is not None
        and metrics.false_positive_fraction <= config.max_false...
        and metrics.hausdorff_rad is not None
        and metrics.hausdorff_rad <= ...
        and metrics.refinement_delta is not None
        and metrics.refinement_delta <= ...
    )
```

Do not allow `None` to mean pass.

For a negative probe, run the same set gate, then require point classification `PARTIAL`.

Require source-control reconstruction to pass before attributing natural-leaf failure to the decomposition.

---

# H6 — Readout and CI

## Real plotting

Read actual JSON artifacts. Use consistent sphere-cell panels:

```text
oracle
direct
source control
natural accepted
natural excluded
difference maps
```

Plot accepted and excluded leaves separately.

## CI

Add a reduced P1/P3 end-to-end smoke. Keep full campaign manual if necessary.

## Closeout

Regenerate all R3A results only after H0-H5 are merged on the hardening branch.

---

## 3. Review checkpoints

Request review after:

```text
H0-H1: evidence semantics
H2: re-seeding
H3-H4: family geometry
H5-H6: campaign and evidence
```

Do not combine all numerical and semantic changes into one unreviewable commit.

---

## 4. Commands

```bash
pytest tests/test_l5_reconstruction_models.py
pytest tests/test_l5_three_way_metrics.py
pytest tests/test_l5_leaf_reseed.py
pytest tests/test_l5_leaf_transversality.py
pytest tests/test_l5_chart_overlap.py
pytest tests/test_l5_source_control_reconstruction.py
pytest tests/test_l5_five_point_campaign.py
pytest
ruff check .
mypy src
python scripts/check_markdown_links.py
```

Reduced end-to-end:

```bash
PYTHONPATH=src python -m \
  grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_v1.json \
  --outdir outputs/r3a_hardening_smoke \
  --stage all \
  --mode ci
```

Full closeout:

```bash
PYTHONPATH=src python -m \
  grashof_workspace.spatial_experiments.l5_reconstruction.cli \
  --config configs/l5_positive_control_v1.json \
  --outdir results/l5_reconstruction/r3a \
  --stage all \
  --mode full
```
