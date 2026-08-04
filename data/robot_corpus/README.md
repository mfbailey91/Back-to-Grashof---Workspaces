# Robot corpus

The corpus separates **source repositories** from **robot models**. A source is
cloned once, while any number of variants can point into that snapshot. This is
important for the seven Universal Robots models and four KUKA models selected
from only two repositories.

## Selected external robots

- 13 primary spatial 6R manipulators;
- 4 redundant 7R controls;
- 1 external planar 3R model.

The project also generates six planar 3R URDF fixtures whose link ratios exercise
analytically meaningful workspace topologies.

Raw upstream repositories are not vendored. Run:

```bash
python scripts/fetch_robot_corpus.py --list-models
python scripts/fetch_robot_corpus.py --dry-run --group all
python scripts/fetch_robot_corpus.py --group all
```

Snapshots are cloned under `third_party/robot_corpus/`. Resolved commits and
entry-point results are written under `data/robot_corpus/provenance/`.

Generate or verify the project planar models with:

```bash
python scripts/generate_planar3r_urdfs.py
python scripts/generate_planar3r_urdfs.py --check
```

## Fetch arm selection

The Fetch robot is intentionally not treated as one giant manipulator. The
selected chain begins at `torso_lift_link` and ends at `wrist_roll_link`. It
contains the seven arm revolute joints only. The wheeled base, torso prismatic
joint, head, sensors, and gripper are excluded from arm-kinematics analysis.
