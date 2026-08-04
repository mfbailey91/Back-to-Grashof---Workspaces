# Robot Corpus Selection

## Research roles

The corpus is not meant to maximize robot count. It is designed to test whether
structural reductions can be detected reliably across related families,
different industrial morphologies, and deliberately incompatible controls.

## Primary 6R corpus

### Universal Robots family

- UR3e
- UR5e
- UR8 Long
- UR10e
- UR15
- UR20
- UR30

All seven use one upstream description repository and one parameterized Xacro
entry point. This family is useful for determining which structural conclusions
remain invariant under changes in dimensional parameters and joint limits.

### KUKA family

- KR 6 R700-2 — compact AGILUS
- KR 20 R1810-2 — medium CYBERTECH
- KR 120 R2700-2 — large QUANTEC

These span three industrial scales while retaining conventional six-axis serial
architecture.

### Additional 6R arms

- FANUC M-710iC/50
- Kinova Jaco2 J2N6S300
- UFACTORY xArm6

These broaden the corpus beyond the UR/KUKA families. Gripper or finger joints
are never counted as arm degrees of freedom.

## Redundant controls

- Franka Research 3 v2.1
- Franka Emika Robot / Panda
- KUKA LBR iiwa 14 R820
- Fetch arm-only chain

These are seven-revolute-joint controls. They are expected to reject assumptions
that depend specifically on a nonredundant six-joint chain.

### Fetch arm-only interpretation

The full Fetch URDF includes a mobile base, torso lift, head, sensors, arm, and
gripper. The selected manipulator is the subchain

```text
torso_lift_link -> wrist_roll_link
```

with joints:

```text
shoulder_pan_joint
shoulder_lift_joint
upperarm_roll_joint
elbow_flex_joint
forearm_roll_joint
wrist_flex_joint
wrist_roll_joint
```

The torso lift is not part of this arm-only model.

## Planar corpus

The external `lesson_urdf` model tests ingestion of someone else's planar 3R
URDF. Project-generated models then provide controlled link-ratio families:

| Instance | Link lengths | Intended analytical role |
|---|---:|---|
| symmetric_disk | 2, 2, 1 | dexterous disk |
| split_disk_annulus | 3, 2, 1.5 | disconnected disk and annulus |
| inner_island | 3, 1, 2.5 | inner dexterous island |
| terminal_heavy_empty | 1, 1, 3 | empty dexterous workspace |
| change_point_boundary | 3, 2, 2 | equality/change-point boundary |
| lesson_ratio | 0.5, 0.5, 0.18 | same ratios as external lesson model |

## License policy

Third-party repositories remain unmodified and gitignored. Before republishing
any model, mesh, or transformed derivative, review the license in the exact
fetched snapshot. In particular:

- several newer Universal Robots mesh sets have additional graphical terms;
- Fetch description assets use a noncommercial Creative Commons license;
- FANUC support is community maintained rather than OEM supported.
