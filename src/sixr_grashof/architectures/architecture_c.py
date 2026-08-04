"""Architecture C: parameterized shoulder offset + exact spherical wrist.

Conventions
-----------
Identical to Architecture A except the base offset

    epsilon_s = d(z1, z2) > 0

is realized by placing joint 2 at ``(epsilon_s, 0, 0)`` in the base at the
zero configuration, with ``z2 || (0,1,0)``. The wrist axes remain concurrent
for every ``epsilon_s``.
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


class ArchitectureC:
    """Elbow-like arm with shoulder offset and concurrent spherical wrist."""

    architecture_id = "C"

    def __init__(self, params: ArchitectureParams | None = None) -> None:
        self.params = params or ArchitectureParams()
        if self.params.epsilon_w != 0.0:
            raise ValueError("Architecture C does not use epsilon_w")

    def forward(
        self,
        q: tuple[float, float, float, float, float, float],
    ) -> ForwardKinematicsResult:
        L2, L3, Lt = self.params.L2, self.params.L3, self.params.Lt
        es = self.params.epsilon_s
        q1, q2, q3, q4, q5, q6 = q

        T = identity4()
        a1 = (0.0, 0.0, 1.0)
        p1 = (0.0, 0.0, 0.0)
        T = matmul(T, rotation_about(a1, q1))
        joints: list[JointPose] = [JointPose(1, AxisLine(p1, a1), p1)]

        # Shoulder offset: joint 2 displaced by epsilon_s along base x at q1=0.
        T = matmul(T, translation((es, 0.0, 0.0)))
        a2_local = (0.0, 1.0, 0.0)
        p2 = transform_point(T, (0.0, 0.0, 0.0))
        a2 = transform_direction(T, a2_local)
        T = matmul(T, rotation_about(a2_local, q2))
        joints.append(JointPose(2, AxisLine(p2, normalize(a2)), p2))

        T = matmul(T, translation((L2, 0.0, 0.0)))
        a3_local = (0.0, 1.0, 0.0)
        p3 = transform_point(T, (0.0, 0.0, 0.0))
        a3 = transform_direction(T, a3_local)
        T = matmul(T, rotation_about(a3_local, q3))
        joints.append(JointPose(3, AxisLine(p3, normalize(a3)), p3))

        T = matmul(T, translation((L3, 0.0, 0.0)))
        cw = transform_point(T, (0.0, 0.0, 0.0))

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
        return build_geometry_report(
            architecture_id=self.architecture_id,
            params=self.params,
            fk=self.forward(q),
            expect_z2_z3_z4_parallel=False,
            regional_exact_candidate=self.params.epsilon_s == 0.0,
        )
