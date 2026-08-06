from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class OrderedFamily(str, Enum):
    UUUR = "UUUR"
    UURU = "UURU"
    URUU = "URUU"
    USRR = "USRR"
    URSR = "URSR"
    URRS = "URRS"


class ToolAxis(str, Enum):
    A = "a"
    B = "b"


class BranchClass(str, Enum):
    CRANK = "crank"
    ROCKER = "rocker"
    CHANGE_POINT = "change_point"
    NO_ASSEMBLY = "no_assembly"
    OPEN_BRANCH = "open_branch"
    INVALID = "invalid"


@dataclass(frozen=True)
class ExplorerCase:
    family: OrderedFamily
    tool_axis: ToolAxis

    @property
    def slug(self) -> str:
        return f"{self.family.value.lower()}_tool_{self.tool_axis.value}"


@dataclass
class GeometryDescriptor:
    name: str
    value: float | int | str | bool
    group: str
    description: str


@dataclass
class GeometrySample:
    sample_id: str
    family: OrderedFamily
    inversion: str
    seed: int
    raw_parameters: dict[str, float]
    descriptors: list[GeometryDescriptor]

    def descriptor_map(self) -> dict[str, Any]:
        return {d.name: d.value for d in self.descriptors}


@dataclass
class BranchResult:
    sample_id: str
    case: ExplorerCase
    branch_id: str
    branch_closed: bool
    singularity_count: int
    w_alpha: int | None
    w_beta: int | None
    class_alpha: BranchClass
    class_beta: BranchClass
    tool_range_alpha: float | None
    tool_range_beta: float | None
    notes: list[str] = field(default_factory=list)


@dataclass
class SprintArtifactIndex:
    sprint_name: str
    outdir: Path
    html_files: list[str]
    image_files: list[str]
    json_files: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sprint_name": self.sprint_name,
            "outdir": str(self.outdir),
            "html_files": self.html_files,
            "image_files": self.image_files,
            "json_files": self.json_files,
        }


def dataclass_to_jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return getattr(value, "value")
    if isinstance(value, list):
        return [dataclass_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: dataclass_to_jsonable(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return dataclass_to_jsonable(asdict(value))
    return value
