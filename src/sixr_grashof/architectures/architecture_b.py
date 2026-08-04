"""Architecture B: exact regional + parameterized wrist offset.

Conventions
-----------
At the zero configuration:

- ``z1 = (0,0,1)`` at the origin;
- ``z2 || z3 || z4`` along ``(0,1,0)``;
- joints 2,3,4 located along the arm plane with spacing ``L2``, ``L3``;
- distal wrist axes 5 and 6 are orthogonal in sequence;
- ``epsilon_w`` shifts axis 6 off the common wrist intersection (offset
  perpendicular to ``z6``) so concurrency residual grows with ``epsilon_w``
  (exact at ``epsilon_w = 0``).
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


class ArchitectureB:
    """UR-like arm with parallel z2||z3||z4 and offsettable wrist."""

    architecture_id = "B"

    def __init__(self, params: ArchitectureParams | None = None) -> None:
        self.params = params or ArchitectureParams()
        if self.params.epsilon_s != 0.0:
            raise ValueError("Architecture B does not use epsilon_s")

    def forward(
        self,
        q: tuple[float, float, float, float, float, float],
    ) -> ForwardKinematicsResult:
        L2, L3, Lt = self.params.L2, self.params.L3, self.params.Lt
        ew = self.params.epsilon_w
        q1, q2, q3, q4, q5, q6 = q

        T = identity4()
        a1 = (0.0, 0.0, 1.0)
        p1 = (0.0, 0.0, 0.0)
        T = matmul(T, rotation_about(a1, q1))
        joints: list[JointPose] = [JointPose(1, AxisLine(p1, a1), p1)]

        # Shoulder joint 2 about y at origin.
        a2_local = (0.0, 1.0, 0.0)
        p2 = transform_point(T, (0.0, 0.0, 0.0))
        a2 = transform_direction(T, a2_local)
        T = matmul(T, rotation_about(a2_local, q2))
        joints.append(JointPose(2, AxisLine(p2, normalize(a2)), p2))

        # Elbow joint 3, parallel, after L2.
        T = matmul(T, translation((L2, 0.0, 0.0)))
        a3_local = (0.0, 1.0, 0.0)
        p3 = transform_point(T, (0.0, 0.0, 0.0))
        a3 = transform_direction(T, a3_local)
        T = matmul(T, rotation_about(a3_local, q3))
        joints.append(JointPose(3, AxisLine(p3, normalize(a3)), p3))

        # Wrist-1 joint 4, parallel, after L3.
        T = matmul(T, translation((L3, 0.0, 0.0)))
        a4_local = (0.0, 1.0, 0.0)
        p4 = transform_point(T, (0.0, 0.0, 0.0))
        a4 = transform_direction(T, a4_local)
        T = matmul(T, rotation_about(a4_local, q4))
        joints.append(JointPose(4, AxisLine(p4, normalize(a4)), p4))

        # Wrist-2 joint 5 about local x through p4 (orthogonal sequence).
        a5_local = (1.0, 0.0, 0.0)
        p5 = p4
        a5 = transform_direction(T, a5_local)
        T = matmul(T, rotation_about(a5_local, q5))
        joints.append(JointPose(5, AxisLine(p5, normalize(a5)), p5))

        # Wrist-3 joint 6: at epsilon_w = 0 concurrent with 4/5 at p4;
        # nonzero epsilon_w offsets the axis point perpendicular to z6 so that
        # the directed line no longer passes through the wrist intersection.
        T_offset = matmul(T, translation((ew, 0.0, 0.0)))
        a6_local = (0.0, 0.0, 1.0)
        p6 = transform_point(T_offset, (0.0, 0.0, 0.0))
        a6 = transform_direction(T_offset, a6_local)
        T = matmul(T_offset, rotation_about(a6_local, q6))
        joints.append(JointPose(6, AxisLine(p6, normalize(a6)), p6))

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
            expect_z2_z3_z4_parallel=True,
            regional_exact_candidate=True,
        )
