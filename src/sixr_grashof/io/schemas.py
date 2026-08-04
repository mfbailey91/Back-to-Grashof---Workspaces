"""Result record schemas for Sprint 4–5 experiments (project plan §10)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

PredictionOutcome = Literal[
    "agreement",
    "false_positive",
    "false_negative",
    "regional_unreachable",
    "invalid_reduction",
    "boundary",
    "not_applicable",
]


@dataclass(slots=True)
class ExperimentRecord:
    """Serializable evaluated-state record."""

    architecture_id: str
    offset_parameters: dict[str, float]
    position: tuple[float, float, float]
    position_branch_id: str
    joint_configuration_seed: tuple[float, float, float, float, float, float]
    regional_reduction_status: str
    regional_reachable: bool
    spherical_reduction_status: str
    concurrency_residual: float
    spherical_link_angles: tuple[float, float, float, float] | None
    T1: float | None
    T2: float | None
    T3: float | None
    T4: float | None
    T_sign_tuple: tuple[int, int, int, int] | None
    T_product: float | None
    linkage_type: int | None
    input_motion_class: str | None
    output_motion_class: str | None
    hand_link_motion_class: str | None
    analytical_prediction: bool | None
    orientation_sample_count: int
    orientation_coverage: float
    orientation_component_count: int
    strict_sampled_dexterity: bool
    singularity_flags: int
    solved_count: int
    unreachable_count: int
    solver_failed_count: int
    prediction_outcome: PredictionOutcome
    sample_resolution: str
    random_seed: int
    software_version: str = "0.3.0"
    notes: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["position"] = list(d["position"])
        d["joint_configuration_seed"] = list(d["joint_configuration_seed"])
        if d["spherical_link_angles"] is not None:
            d["spherical_link_angles"] = list(d["spherical_link_angles"])
        if d["T_sign_tuple"] is not None:
            d["T_sign_tuple"] = list(d["T_sign_tuple"])
        return d
