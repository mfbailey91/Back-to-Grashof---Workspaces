"""Architecture A: exact regional reduction + exact spherical wrist.

Conventions
-----------
Joint angles ``q = (q1,...,q6)`` are right-handed rotations about successive
axes. At the zero configuration:

- ``z1 = (0,0,1)`` at the origin;
- ``z2 = (0,1,0)`` at the origin (``z1 ⊥ z2``);
- ``z3 = (0,1,0)`` at ``(L2, 0, 0)`` (``z2 || z3``);
- wrist center ``Cw = (L2 + L3, 0, 0)``;
- ``z4, z5, z6`` concurrent at ``Cw``, mutually orthogonal in sequence;
- tool frame offset ``Lt`` along ``z6``.
"""

from __future__ import annotations

from sixr_grashof.architectures.base import (
    ArchitectureParams,
    GeometryReport,
    build_geometry_report,
)
from sixr_grashof.kinematics.axes import AxisLine, normalize
from sixr_grashof.kinematics.forward import (
    ForwardKinematicsResult,
    JointPose,
    identity4,
    matmul,
    rotation_about,
    transform_direction,
    transform_point,
    translation,
)


class ArchitectureA:
    """Canonical elbow manipulator with concurrent spherical wrist."""

    architecture_id = "A"

    def __init__(self, params: ArchitectureParams | None = None) -> None:
        self.params = params or ArchitectureParams()
        if self.params.epsilon_w != 0.0 or self.params.epsilon_s != 0.0:
            raise ValueError("Architecture A does not use epsilon_w or epsilon_s")

    def forward(
        self,
        q: tuple[float, float, float, float, float, float],
    ) -> ForwardKinematicsResult:
        L2, L3, Lt = self.params.L2, self.params.L3, self.params.Lt
        q1, q2, q3, q4, q5, q6 = q

        # Home axis directions / points in the preceding link frame.
        # Build cumulatively in the base frame.
        T = identity4()

        # Joint 1 at origin about z.
        a1 = (0.0, 0.0, 1.0)
        p1 = (0.0, 0.0, 0.0)
        T = matmul(T, rotation_about(a1, q1))
        joints: list[JointPose] = [
            JointPose(1, AxisLine(p1, a1), p1),
        ]

        # Joint 2 at origin about y (in base at q1=0); rotate by q2 about current y.
        a2_local = (0.0, 1.0, 0.0)
        p2 = transform_point(T, (0.0, 0.0, 0.0))
        a2 = transform_direction(T, a2_local)
        T = matmul(T, rotation_about(a2_local, q2))
        joints.append(JointPose(2, AxisLine(p2, normalize(a2)), p2))

        # Translate along x by L2 to joint 3 (parallel to joint 2).
        T = matmul(T, translation((L2, 0.0, 0.0)))
        a3_local = (0.0, 1.0, 0.0)
        p3 = transform_point(T, (0.0, 0.0, 0.0))
        a3 = transform_direction(T, a3_local)
        T = matmul(T, rotation_about(a3_local, q3))
        joints.append(JointPose(3, AxisLine(p3, normalize(a3)), p3))

        # Forearm to wrist center.
        T = matmul(T, translation((L3, 0.0, 0.0)))
        cw = transform_point(T, (0.0, 0.0, 0.0))

        # Spherical wrist: z4 along forearm (x), z5 along y, z6 along z at home.
        a4_local = (1.0, 0.0, 0.0)
        a4 = transform_direction(T, a4_local)
        T = matmul(T, rotation_about(a4_local, q4))
        joints.append(JointPose(4, AxisLine(cw, normalize(a4)), cw))

        a5_local = (0.0, 1.0, 0.0)
        a5 = transform_direction(T, a5_local)
        T = matmul(T, rotation_about(a5_local, q5))
        joints.append(JointPose(5, AxisLine(cw, normalize(a5)), cw))

        a6_local = (0.0, 0.0, 1.0)
        a6 = transform_direction(T, a6_local)
        T = matmul(T, rotation_about(a6_local, q6))
        joints.append(JointPose(6, AxisLine(cw, normalize(a6)), cw))

        T = matmul(T, translation((0.0, 0.0, Lt)))
        tool = transform_point(T, (0.0, 0.0, 0.0))
        return ForwardKinematicsResult(tuple(joints), tool, T)

    def geometry_report(
        self,
        q: tuple[float, float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    ) -> GeometryReport:
        fk = self.forward(q)
        axes = [j.axis for j in fk.joints]
        # Regional exact candidate: z1⊥z2 and z2||z3.
        z1z2_dot = abs(
            axes[0].direction[0] * axes[1].direction[0]
            + axes[0].direction[1] * axes[1].direction[1]
            + axes[0].direction[2] * axes[1].direction[2]
        )
        regional = z1z2_dot < 1e-9 and abs(
            abs(
                axes[1].direction[0] * axes[2].direction[0]
                + axes[1].direction[1] * axes[2].direction[1]
                + axes[1].direction[2] * axes[2].direction[2]
            )
            - 1.0
        ) < 1e-9
        return build_geometry_report(
            architecture_id=self.architecture_id,
            params=self.params,
            fk=fk,
            expect_z2_z3_z4_parallel=False,
            regional_exact_candidate=regional,
        )
