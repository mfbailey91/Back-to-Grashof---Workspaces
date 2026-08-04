# Project Plan: Spherical Grashof Characterization of Synthetic 6R Manipulators

## 1. Project Objective

Extend the virtual four-bar workspace characterization developed for planar 3R manipulators to idealized spatial 6R manipulators.

The project will construct several synthetic 6R kinematic architectures, reduce their regional and orientation structures to planar and spherical virtual four-bars where the geometry permits, classify the spherical linkage using the McCarthy-Soh \(T_1,T_2,T_3,T_4\) conditions, and test whether a subset of spherical linkage types predicts complete end-effector orientation capability at a Cartesian position.

The project deliberately begins with idealized kinematic structures rather than URDF models. This avoids mixing the core analytical question with model parsing, manufacturer conventions, joint limits, calibration offsets, and collision geometry.

---

## 2. Central Research Question

> For which idealized 6R kinematic architectures can the regional and orientation structures be reduced to planar and spherical virtual four-bars, and do the McCarthy-Soh spherical linkage types predict end-effector orientation capability?

A narrower experimental question is:

> At a fixed Cartesian position, does complete orientation capability require the virtual link associated with end-effector orientation to belong to a spherical crank class?

---

## 3. Working Conjecture

The spherical Grashof product condition

\[
T_1T_2T_3T_4>0
\]

identifies the Grashof family, but it does not by itself identify dexterity.

The working conjecture is:

> The dexterous subset of spherical Grashof linkages is the subset in which the virtual link representing hand orientation is a crank.

Under an output-link convention for the hand-orientation link, the initial candidate set is:

\[
\boxed{\text{rocker-crank}\;\cup\;\text{double-crank}}
\]

corresponding to McCarthy-Soh types:

\[
\boxed{2,3,10,11}
\]

The following are explicitly not assumed to be dexterous:

- Grashof double-rocker linkages;
- non-Grashof double-rocker linkages;
- crank-rocker linkages when the hand-orientation variable is assigned to the output rocker;
- approximate spherical reductions whose geometric residual exceeds the accepted tolerance.

This is a hypothesis to test, not a claim to encode as truth.

---

## 4. Scope

### Included

- Idealized 6R serial manipulators;
- Revolute joints only;
- Synthetic link lengths, offsets, and axis orientations;
- Unlimited revolute-joint motion in the primary experiment;
- Base-symmetry quotienting where mathematically justified;
- Planar virtual four-bar regional reductions;
- Spherical virtual four-bar orientation reductions;
- McCarthy-Soh \(T_1,T_2,T_3,T_4\) evaluation;
- All 16 spherical 4R linkage types;
- Numerical orientation-reachability validation;
- Exact and parameterized approximate spherical architectures;
- Interactive dashboard and reproducible experiment outputs.

### Excluded from the first implementation

- URDF parsing;
- Named commercial robot models;
- Manufacturer joint limits;
- Self-collision and environmental collision;
- Dynamics, torque, stiffness, compliance, and actuator limits;
- General skew-axis 6R closed-form inverse kinematics;
- A formal proof that crank classification is sufficient for full \(SO(3)\) coverage;
- Optimization of industrial robot dimensions.

---

## 5. Synthetic Manipulator Corpus

The first corpus contains three controlled architectures. All dimensions are normalized so that the architecture, rather than a particular robot scale, determines the result.

Suggested nominal dimensions:

\[
L_2=1.0,\qquad L_3=0.8,\qquad L_t=0.25.
\]

All revolute joints initially use periodic motion with no physical stops.

### Architecture A: Exact Regional Reduction + Exact Spherical Wrist

A canonical elbow manipulator with:

\[
z_1\perp z_2,\qquad z_2\parallel z_3,
\]

and three concurrent wrist axes:

\[
z_4\cap z_5\cap z_6=C_w.
\]

Purpose:

- positive control;
- exact quotient of base azimuth;
- exact planar regional reduction;
- exact spherical orientation reduction;
- cleanest test of the linkage-type conjecture.

### Architecture B: Exact Regional Reduction + Parameterized Offset Wrist

A UR-like synthetic architecture with:

\[
z_2\parallel z_3\parallel z_4,
\]

and a distal wrist whose axes are orthogonal in sequence but not concurrent.

Introduce a normalized wrist offset:

\[
\epsilon_w\in\{0,0.025,0.05,0.10,0.20\}.
\]

At \(\epsilon_w=0\), the architecture reduces to an exact spherical-wrist case. Increasing \(\epsilon_w\) measures how prediction quality degrades as the spherical assumption is violated.

Purpose:

- controlled spherical-reduction perturbation;
- test robustness of the classification;
- establish a geometric confidence measure.

### Architecture C: Parameterized Regional Offset + Exact Spherical Wrist

Preserve a concurrent wrist:

\[
z_4\cap z_5\cap z_6=C_w,
\]

while introducing a proximal shoulder/base offset:

\[
\epsilon_s=d(z_1,z_2)>0.
\]

Suggested sweep:

\[
\epsilon_s\in\{0,0.025,0.05,0.10,0.20\}.
\]

Purpose:

- isolate failure or degradation of the regional reduction;
- determine whether an exact spherical orientation classification remains locally useful when the proximal architecture is less reducible;
- separate regional reachability errors from orientation-classification errors.

---

## 6. Analytical Framework

### 6.1 Kinematic Representation

Represent each revolute axis as a line:

\[
\ell_i=(p_i,\hat a_i),
\]

with a point \(p_i\) and unit direction \(\hat a_i\).

Use either product-of-exponentials or homogeneous-transform forward kinematics, but maintain axis geometry explicitly so that intersection, parallelism, and concurrency tests are not inferred indirectly from sampled poses.

### 6.2 Architecture Detection

For each relevant axis pair or cluster, calculate:

- angular separation;
- parallel or antiparallel status;
- shortest line-to-line distance;
- intersection point when one exists;
- best-fit common center for candidate spherical clusters;
- residual from exact concurrency.

For a candidate axis cluster \(C\), define the least-squares spherical center:

\[
c^*=\arg\min_c\sum_{i\in C}
\left\|
\left(I-\hat a_i\hat a_i^T\right)(c-p_i)
\right\|^2.
\]

Define the normalized concurrency residual:

\[
\rho_C=
\frac{
\max_{i\in C}d(c^*,\ell_i)
}{L_2}.
\]

The result must be labeled as:

- exact;
- approximate;
- invalid for spherical reduction.

The thresholds are configuration parameters and must never be hidden in code.

### 6.3 Regional Reduction

For architectures admitting rotational symmetry about \(J_1\):

1. quotient the base azimuth;
2. work in a meridional plane;
3. identify the residual position chain;
4. construct the corresponding planar virtual four-bar closure;
5. classify regional reachability independently from wrist orientation capability.

The project must distinguish:

\[
\text{regional reachability}
\]

from:

\[
\text{orientation capability at a reachable position}.
\]

### 6.4 Spherical Orientation Closure

At a fixed Cartesian position \(p\):

1. impose the position constraint;
2. identify the residual orientation motion;
3. construct the spherical virtual four-bar closure;
4. assign which virtual link is the input, coupler, output, and ground;
5. explicitly designate the virtual link representing hand orientation;
6. calculate the four spherical link angles;
7. evaluate \(T_1,T_2,T_3,T_4\);
8. classify the linkage type from 1 through 16.

The implementation must not infer dexterity from the product alone.

### 6.5 McCarthy-Soh Classification Output

Each evaluated spherical state must return:

```text
T1, T2, T3, T4
sign tuple
T1*T2*T3*T4
Grashof / non-Grashof family
McCarthy-Soh type 1-16
input crank or rocker
output crank or rocker
hand-orientation link crank or rocker
T4 wrap-around family
exact / approximate / invalid reduction
concurrency residual
boundary/change-point warning
```

When \(T_4<0\), retain both:

- the actual type 9-16;
- the equivalent crank-motion class obtained through the sign correspondence described by McCarthy and Soh.

---

## 7. Numerical Ground Truth

### 7.1 Fixed-Position Orientation Set

For a Cartesian position \(p\), define:

\[
\mathcal R_p=
\left\{
R\in SO(3):\exists q\text{ such that }f(q)=(p,R)
\right\}.
\]

The numerical experiment estimates the orientation coverage:

\[
C(p)=
\frac{\mu(\mathcal R_p)}{\mu(SO(3))}.
\]

### 7.2 Orientation Sampling

Use a reproducible approximately uniform orientation set, such as:

- Hopf-coordinate sampling;
- low-discrepancy unit quaternions;
- deterministic spherical direction samples combined with roll samples.

The initial implementation should support at least three resolutions:

```text
coarse:  approximately 500 orientations
medium:  approximately 5,000 orientations
fine:    approximately 50,000 orientations
```

Exact sample counts may be adjusted after convergence testing.

### 7.3 IK and Continuation

For each target orientation:

- solve all discoverable IK branches;
- use multiple seeds;
- retain branch identity where possible;
- record singularities;
- record whether neighboring orientation samples remain connected through feasible joint motion;
- distinguish isolated IK success from continuous orientation traversal.

A simple fraction of solved orientation samples is not enough to establish full orientation capability. The project should track both coverage and connectivity.

### 7.4 Numerical Labels

For each position, report:

- orientation sample coverage \(C(p)\);
- strict sampled dexterity;
- number of connected feasible-orientation components;
- maximum uncovered orientation gap;
- IK branch count;
- singularity encounters;
- analytical predicted label;
- agreement or disagreement category.

---

## 8. Comparison Metrics

### Primary metrics

- analytical/numerical classification accuracy;
- false-positive rate;
- false-negative rate;
- precision and recall for sampled strict dexterity;
- correlation between concurrency residual and prediction error;
- error versus wrist offset \(\epsilon_w\);
- error versus regional offset \(\epsilon_s\).

### Linkage-type confusion analysis

Build a confusion table indexed by all 16 spherical linkage types.

For each type, measure:

- number of observed states;
- mean orientation coverage;
- fraction numerically dexterous;
- fraction connected across the orientation sample graph;
- frequency of analytical false positives and false negatives.

This is more informative than reducing all results to Grashof/non-Grashof.

### Boundary analysis

States near:

\[
T_i=0
\]

must be flagged and analyzed separately. Classification instability at change points should not be counted as ordinary model error.

---

## 9. Software Architecture

Suggested repository structure:

```text
sixr-spherical-grashof/
├── README.md
├── pyproject.toml
├── configs/
│   ├── architecture_a.yaml
│   ├── architecture_b.yaml
│   ├── architecture_c.yaml
│   └── experiments/
├── docs/
│   ├── theory.md
│   ├── synthetic_architectures.md
│   ├── spherical_reduction.md
│   ├── experiment_protocol.md
│   └── results_schema.md
├── src/
│   └── sixr_grashof/
│       ├── kinematics/
│       │   ├── axes.py
│       │   ├── forward.py
│       │   ├── jacobian.py
│       │   └── ik.py
│       ├── architectures/
│       │   ├── base.py
│       │   ├── architecture_a.py
│       │   ├── architecture_b.py
│       │   └── architecture_c.py
│       ├── reductions/
│       │   ├── symmetry.py
│       │   ├── planar_fourbar.py
│       │   ├── spherical_fourbar.py
│       │   └── residuals.py
│       ├── classification/
│       │   ├── mccarthy_soh.py
│       │   ├── linkage_types.py
│       │   └── predictors.py
│       ├── sampling/
│       │   ├── workspace.py
│       │   └── orientations.py
│       ├── experiments/
│       │   ├── fixed_position.py
│       │   ├── offset_sweep.py
│       │   └── convergence.py
│       ├── visualization/
│       │   ├── robot_plot.py
│       │   ├── axis_plot.py
│       │   ├── spherical_linkage.py
│       │   └── workspace_maps.py
│       └── io/
│           ├── schemas.py
│           └── results.py
├── tests/
│   ├── test_axis_geometry.py
│   ├── test_architectures.py
│   ├── test_spherical_classification.py
│   ├── test_known_linkage_types.py
│   └── test_reproducibility.py
├── dashboard/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── results/
    └── .gitkeep
```

---

## 10. Result Data Schema

Each evaluated state should be serializable as one record containing:

```text
architecture_id
offset_parameters
position
position_branch_id
joint_configuration_seed
regional_reduction_status
regional_linkage_data
spherical_reduction_status
spherical_center
concurrency_residual
spherical_link_angles
T1, T2, T3, T4
T_sign_tuple
T_product
linkage_type
input_motion_class
output_motion_class
hand_link_motion_class
analytical_prediction
orientation_sample_count
orientation_coverage
orientation_component_count
strict_sampled_dexterity
singularity_flags
prediction_outcome
software_version
random_seed
```

All plots and dashboard views should be generated from saved result records rather than from unrecoverable in-memory calculations.

---

## 11. Project Sprints

## Sprint 0 — Mathematical Specification and Test Fixtures

### Goal

Convert the conceptual reduction into an unambiguous implementation specification.

### Tasks

- Define all joint axes and dimensions for architectures A, B, and C;
- establish frame conventions;
- define the virtual spherical four-bar link ordering;
- identify the hand-orientation link convention;
- transcribe and verify the McCarthy-Soh linkage table;
- document the formulas for \(T_1,T_2,T_3,T_4\);
- create hand-calculated fixtures for at least one example of every basic motion class;
- define tolerances and boundary behavior.

### Deliverables

- `docs/theory.md`;
- `docs/synthetic_architectures.md`;
- machine-readable linkage-type table;
- mathematical test fixtures.

### Acceptance criteria

- Every one of the 16 sign patterns maps to exactly one expected linkage type;
- \(T_4<0\) correspondence reproduces McCarthy and Soh’s stated motion equivalence;
- input, output, ground, and hand-orientation links are never implicit.

---

## Sprint 1 — Synthetic 6R Kinematics and Visualization

### Goal

Create the three idealized manipulators and verify their geometry visually and numerically.

### Tasks

- implement axis-line and transform representations;
- implement forward kinematics;
- generate architectures A, B, and C from parameters;
- visualize links, axes, offsets, and wrist-center candidates;
- implement pairwise parallelism, intersection, and shortest-distance tests;
- implement common-center residual calculation;
- add unit tests for known exact and offset cases.

### Deliverables

- architecture generator;
- static and interactive 3D visualizations;
- axis-geometry report for each architecture.

### Acceptance criteria

- Architecture A reports exact planar and spherical geometry;
- Architecture B reports exact spherical geometry only at \(\epsilon_w=0\);
- Architecture C reports exact spherical geometry for every \(\epsilon_s\) value;
- geometric residuals scale predictably with the imposed offsets.

---

## Sprint 2 — Regional and Spherical Reduction Engine

### Goal

Construct the virtual planar and spherical closures from the synthetic manipulators.

### Tasks

- detect base-generated task-space symmetry;
- quotient base azimuth for applicable architectures;
- construct the regional planar closure;
- impose a fixed Cartesian position;
- derive the residual orientation closure;
- construct the virtual spherical four-bar;
- calculate spherical link angles;
- return exact/approximate/invalid status with residuals;
- visualize the physical 6R chain beside its virtual linkage.

### Deliverables

- planar reduction module;
- spherical reduction module;
- reduction diagnostics;
- virtual-linkage animation or pose viewer.

### Acceptance criteria

- Architecture A produces repeatable virtual-linkage parameters for the same physical state;
- the virtual closure reconstructs the imposed geometry within numerical tolerance;
- invalid reductions fail explicitly rather than returning plausible-looking values.

---

## Sprint 3 — McCarthy-Soh Classification and Analytical Predictor

### Goal

Implement the complete spherical linkage classification and the crank-based dexterity hypothesis.

### Tasks

- implement \(T_1,T_2,T_3,T_4\);
- implement type 1-16 lookup;
- implement boundary detection at \(T_i\approx0\);
- report input/output crank-rocker status;
- implement hand-link crank predictor;
- support alternative virtual-link assignments for sensitivity analysis;
- produce linkage-type maps over selected position and closure parameters.

### Deliverables

- classification library;
- tests for all 16 types;
- analytical prediction records;
- first linkage-type visualizations.

### Acceptance criteria

- all test fixtures classify correctly;
- Grashof double-rocker is never labeled dexterous solely from positive product;
- changing the hand-link assignment changes crank-rocker interpretation explicitly and traceably.

---

## Sprint 4 — Numerical Orientation-Capability Ground Truth

### Goal

Estimate actual orientation capability at fixed positions without relying on the analytical classification.

### Tasks

- implement reproducible \(SO(3)\) sampling;
- implement numerical IK or constrained solve for the synthetic arms;
- use multi-start solving;
- identify multiple branches;
- build an adjacency graph over feasible orientation samples;
- calculate coverage and connectivity metrics;
- conduct coarse/medium/fine convergence tests;
- validate known fully spherical wrist behavior.

### Deliverables

- fixed-position orientation experiment;
- coverage and connectivity metrics;
- solver diagnostics;
- convergence report.

### Acceptance criteria

- results are repeatable for a fixed seed and sample set;
- increasing sampling density produces convergent aggregate metrics;
- solver failures can be distinguished from genuinely unreachable orientations.

---

## Sprint 5 — Controlled Architecture Experiments

### Goal

Test the conjecture across exact and perturbed kinematic structures.

### Tasks

- choose representative radial and Cartesian position samples;
- run Architecture A across its workspace;
- sweep \(\epsilon_w\) for Architecture B;
- sweep \(\epsilon_s\) for Architecture C;
- record linkage type and numerical orientation capability;
- create type-by-type confusion analysis;
- analyze prediction error near \(T_i=0\);
- determine whether residual thresholds can identify unreliable reductions.

### Deliverables

- full experiment dataset;
- prediction confusion matrices;
- residual-versus-error plots;
- architecture comparison report.

### Acceptance criteria

- every reported data point is reproducible from a saved configuration;
- exact and approximate reductions are never pooled without labels;
- results distinguish failure of regional reachability from failure of orientation prediction.

---

## Sprint 6 — Dashboard and Research Interpretation

### Goal

Make the analytical and numerical results inspectable rather than burying them in aggregate statistics.

### Dashboard views

1. Synthetic manipulator with joint axes;
2. selected Cartesian position and IK branch;
3. virtual planar four-bar;
4. virtual spherical four-bar;
5. \(T_1,T_2,T_3,T_4\) values and sign tuple;
6. linkage type 1-16;
7. hand-link crank/rocker prediction;
8. sampled orientation sphere or quaternion projection;
9. feasible-orientation connectivity;
10. prediction-versus-ground-truth badge;
11. offset sliders for \(\epsilon_w\) and \(\epsilon_s\);
12. exact/approximate/invalid reduction indicator.

### Deliverables

- browser dashboard;
- exportable figures;
- results summary;
- limitations and next-step document.

### Acceptance criteria

- a user can select a state and see how the physical arm, virtual linkage, classification, and numerical orientation set correspond;
- the dashboard distinguishes Grashof family from specific linkage type;
- the dashboard displays the reduction residual beside every approximate result.

---

## 12. Decision Gates

### Gate 1: Is the spherical closure well-defined?

Proceed only if the virtual-link construction is geometrically and conventionally unambiguous.

If not, stop and revise the reduction before running large experiments.

### Gate 2: Can numerical orientation reachability be trusted?

Proceed only after sampling and solver convergence tests show that apparent coverage gaps are not mostly numerical artifacts.

### Gate 3: Does the crank subset show predictive value in Architecture A?

If no meaningful relationship appears in the exact positive-control architecture, do not expand to commercial robots. Revisit the mapping between the virtual link and spatial orientation.

### Gate 4: Does approximation error scale with geometric residual?

If Architecture B error grows predictably with \(\epsilon_w\), retain approximate spherical reduction with a confidence measure.

If error is discontinuous or uncorrelated with residual, approximate reduction should be treated as exploratory only.

### Gate 5: Is regional reduction separable from orientation classification?

Architecture C must demonstrate whether the wrist classification remains meaningful when the proximal architecture is perturbed. If not, the theory must be framed as a whole-chain reduction rather than a modular regional/orientation decomposition.

---

## 13. Primary Risks and Mitigations

### Risk: A spherical crank is only a one-parameter result

Full dexterity requires coverage of \(SO(3)\), not merely complete rotation of one virtual link.

Mitigation:

- phrase crank status as a candidate or necessary condition until validated;
- measure full orientation coverage and connectivity;
- inspect whether the remaining orientation coordinates introduce independent restrictions.

### Risk: The virtual hand link is assigned incorrectly

The linkage type depends on link ordering and ground/input/output conventions.

Mitigation:

- make the assignment explicit in every record;
- test alternative assignments;
- include diagrams generated from the exact convention used by the classifier.

### Risk: IK failure is mistaken for geometric non-reachability

Mitigation:

- use multi-start methods;
- exploit known synthetic geometry;
- use continuation from neighboring orientation samples;
- retain solver residuals and failure codes.

### Risk: Near-boundary linkage types are numerically unstable

Mitigation:

- define a boundary band around \(T_i=0\);
- report boundary states separately;
- avoid treating type transitions as ordinary classification mistakes.

### Risk: Approximate spherical reduction looks more meaningful than it is

Mitigation:

- display normalized concurrency residual everywhere;
- never suppress exact/approximate/invalid labels;
- compare prediction error directly against the residual.

### Risk: Scope expands into general 6R kinematics too early

Mitigation:

- retain synthetic structures;
- use numerical ground truth rather than pursuing a universal analytical IK solution;
- defer URDF and named robot models until after the exact synthetic case is understood.

---

## 14. Minimum Viable Research Result

The project is publishable as a meaningful internal result if it produces all of the following:

1. A reproducible mapping from an exact spherical-wrist 6R arm state to a spherical virtual four-bar;
2. complete McCarthy-Soh type classification rather than only the product test;
3. a numerical orientation-capability map at fixed positions;
4. evidence showing whether types 2, 3, 10, and 11 are better dexterity predictors than the full Grashof family;
5. an explicit counterexample if any candidate crank type fails to produce full orientation capability;
6. a parameterized offset study showing where the spherical reduction ceases to be reliable.

A negative result remains valuable if it identifies precisely why complete spherical-link rotation does not imply full \(SO(3)\) coverage.

---

## 15. Stretch Goals

After the synthetic study succeeds:

- introduce finite joint limits;
- introduce tool offsets;
- add self-collision;
- import a UR-like URDF as a validation case;
- automatically detect reducible structures from arbitrary kinematic descriptions;
- compare spherical linkage classes with Jacobian-based orientation manipulability;
- extend the classification to spherical-change-point surfaces over workspace;
- investigate multiple spherical closures or multiple orientation fibers at the same Cartesian point;
- formulate sufficient conditions for full orientation capability.

---

## 16. Immediate Next Actions

1. Lock the virtual spherical four-bar convention and hand-link assignment;
2. extract the exact \(T_1,T_2,T_3,T_4\) definitions from McCarthy and Soh Section 7;
3. create the 16-type machine-readable classification table;
4. define Architecture A completely with frames, axes, and dimensions;
5. produce one hand-worked fixed-position spherical closure before writing the general reduction engine;
6. implement Sprint 0 tests before beginning the numerical orientation sampler.

The first code milestone should not be a workspace plot. It should be one physical 6R state, one virtual spherical four-bar, one verified \(T\)-classification, and one explicit designation of the hand-orientation link as a crank or rocker.
