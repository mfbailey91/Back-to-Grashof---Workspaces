"""Immutable typed records for the visual probe.

Conventions
-----------
- Joint order is base ``R1`` through terminal ``R6``.
- Points and directions are world-frame metres / unit vectors as
  ``tuple[float, float, float]``.
- Axis sign is visually meaningful for frame display, not for incidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Vec3 = tuple[float, float, float]
Mat4 = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]

AxisRelation = Literal[
    "collinear",
    "intersecting",
    "parallel_distinct",
    "skew",
    "numerically_ambiguous",
]

PairSetId = Literal["P12_P34", "P12_P45", "P23_P45"]
TopologyLabel = Literal["SRUU", "SURU", "SUUR"]


@dataclass(frozen=True, slots=True)
class AxisLine:
    """Directed line ``AxisLine(point, direction)`` with unit direction."""

    point: Vec3
    direction: Vec3


@dataclass(frozen=True, slots=True)
class JointSpec:
    """One revolute joint in the home (zero) configuration."""

    index: int
    home_point: Vec3
    home_direction: Vec3
    label: str


@dataclass(frozen=True, slots=True)
class LinkSpec:
    """Simple centerline link between successive joint origins."""

    start_joint: int
    end_joint: int
    label: str


@dataclass(frozen=True, slots=True)
class ProbeConfig:
    """Architecture configuration loaded from JSON."""

    name: str
    description: str
    joints: tuple[JointSpec, ...]
    default_q: tuple[float, float, float, float, float, float]
    tool_offset_along_r6: float
    roll_compare_q6: float
    axis_length: float
    frame_length: float
    incidence_tol: float
    parallel_tol: float
    ambiguous_tol: float

    def __post_init__(self) -> None:
        if len(self.joints) != 6:
            raise ValueError("probe config requires exactly six joints")
        if self.tool_offset_along_r6 <= 0.0:
            raise ValueError("tool_offset_along_r6 must be positive")


@dataclass(frozen=True, slots=True)
class JointPose:
    """World-frame pose of one revolute joint after FK."""

    index: int
    label: str
    origin: Vec3
    axis: AxisLine
    frame: Mat4


@dataclass(frozen=True, slots=True)
class ForwardKinematicsResult:
    """Homogeneous-transform FK snapshot."""

    joints: tuple[JointPose, ...]
    tool_point: Vec3
    pointing: Vec3
    tool_transform: Mat4
    link_endpoints: tuple[tuple[Vec3, Vec3], ...]
    q: tuple[float, float, float, float, float, float]


@dataclass(frozen=True, slots=True)
class AxisRelationship:
    """Classification of one adjacent axis pair."""

    joint_a: int
    joint_b: int
    relation: AxisRelation
    distance: float
    intersection: Vec3 | None


@dataclass(frozen=True, slots=True)
class CompoundParent:
    """One combinatorial compound-parent reduction of R1..R5."""

    pair_set: PairSetId
    topology: TopologyLabel
    pairs: tuple[tuple[int, int], ...]
    remaining_r: int
    enabled: bool
    reason: str


@dataclass(frozen=True, slots=True)
class CandidateAxis:
    """One selected display axis with provenance."""

    role: Literal["S", "U", "R"]
    source_id: str
    axis: AxisLine


@dataclass(frozen=True, slots=True)
class CandidateTuple:
    """Coordinate-dependent candidate RRRR axis tuple (not certified)."""

    candidate_id: str
    pair_set: PairSetId
    topology: TopologyLabel
    s_choice: str
    u_first_choice: str
    u_second_choice: str
    remaining_r: int
    axes: tuple[CandidateAxis, ...]


@dataclass(frozen=True, slots=True)
class SceneRecord:
    """Metadata for one exported scene HTML file."""

    scene_id: str
    title: str
    path: str
    kind: str
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class Manifest:
    """Top-level output manifest."""

    project: str
    disclaimer: str
    config_name: str
    output_dir: str
    scenes: tuple[SceneRecord, ...]
    data_files: tuple[str, ...]
