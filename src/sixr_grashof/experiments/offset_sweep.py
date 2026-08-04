"""Architecture A/B/C controlled experiments (Sprint 5)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.classification.predictors import (
    HandLinkRole,
    predict_orientation_capability,
)
from sixr_grashof.experiments.fixed_position import run_fixed_position_experiment
from sixr_grashof.io.schemas import ExperimentRecord, PredictionOutcome
from sixr_grashof.kinematics.ik import ForwardArm
from sixr_grashof.reductions.engine import (
    reduce_architecture_a,
    reduce_architecture_b,
    reduce_architecture_c,
)
from sixr_grashof.sampling.orientations import SampleResolution
from sixr_grashof.sampling.workspace import (
    WorkspaceSample,
    architecture_a_workspace_samples,
    radial_grid_positions,
)

BOUNDARY_ABS = 1e-3


def _attach_analytical(
    record: ExperimentRecord,
    *,
    architecture_id: str,
    q: tuple[float, float, float, float, float, float],
    params: ArchitectureParams,
    numerical_dexterity: bool,
    regional_reachable: bool,
) -> ExperimentRecord:
    if architecture_id == "A":
        reduction = reduce_architecture_a(ArchitectureA(params), q)
    elif architecture_id.startswith("B"):
        reduction = reduce_architecture_b(
            ArchitectureB(
                ArchitectureParams(
                    L2=params.L2,
                    L3=params.L3,
                    Lt=params.Lt,
                    epsilon_w=params.epsilon_w,
                )
            ),
            q,
        )
    else:
        reduction = reduce_architecture_c(
            ArchitectureC(
                ArchitectureParams(
                    L2=params.L2,
                    L3=params.L3,
                    Lt=params.Lt,
                    epsilon_s=params.epsilon_s,
                )
            ),
            q,
        )

    pred = predict_orientation_capability(reduction, hand_link=HandLinkRole.BETA)
    outcome: PredictionOutcome
    if not regional_reachable or not reduction.regional.wrist_reachable:
        outcome = "regional_unreachable"
    elif pred.reduction_status == "invalid" or pred.linkage_type is None:
        outcome = "invalid_reduction"
    elif pred.is_boundary or (
        pred.T1 is not None
        and min(abs(pred.T1), abs(pred.T2 or 0), abs(pred.T3 or 0), abs(pred.T4 or 0))
        < BOUNDARY_ABS
    ):
        outcome = "boundary"
    elif pred.dexterity_candidate_hypothesis and numerical_dexterity:
        outcome = "agreement"
    elif pred.dexterity_candidate_hypothesis and not numerical_dexterity:
        outcome = "false_positive"
    elif (not pred.dexterity_candidate_hypothesis) and numerical_dexterity:
        outcome = "false_negative"
    else:
        outcome = "agreement"

    record.regional_reduction_status = reduction.regional.status
    record.regional_reachable = reduction.regional.wrist_reachable
    record.spherical_reduction_status = reduction.spherical.status
    record.concurrency_residual = reduction.spherical.concurrency.residual_rho
    if pred.spherical_link_angles is not None:
        record.spherical_link_angles = pred.spherical_link_angles
    record.T1 = pred.T1
    record.T2 = pred.T2
    record.T3 = pred.T3
    record.T4 = pred.T4
    record.T_sign_tuple = pred.sign_tuple
    record.T_product = pred.T_product
    record.linkage_type = pred.linkage_type
    record.input_motion_class = pred.input_motion_class
    record.output_motion_class = pred.output_motion_class
    record.hand_link_motion_class = pred.hand_link_motion_class
    record.analytical_prediction = pred.dexterity_candidate_hypothesis
    record.prediction_outcome = outcome
    record.notes = "Sprint 5 analytical+numerical comparison"
    return record


def _run_on_arm(
    arm: ForwardArm,
    sample: WorkspaceSample,
    *,
    architecture_id: str,
    params: ArchitectureParams,
    resolution: SampleResolution,
    seed: int,
    n_ik_starts: int,
    orientation_count: int | None = None,
) -> ExperimentRecord:
    result = run_fixed_position_experiment(
        arm,
        sample,
        resolution=resolution,
        seed=seed,
        n_ik_starts=n_ik_starts,
        architecture_id=architecture_id if architecture_id in {"A", "B", "C"} else architecture_id[0],
        params=params,
        orientation_count=orientation_count,
    )
    return _attach_analytical(
        result.record,
        architecture_id=architecture_id if architecture_id in {"A", "B", "C"} else architecture_id[0],
        q=sample.joint_seed,
        params=params,
        numerical_dexterity=result.record.strict_sampled_dexterity,
        regional_reachable=result.record.regional_reachable,
    )


@dataclass(frozen=True, slots=True)
class ConfusionCell:
    linkage_type: int
    n_states: int
    mean_coverage: float
    frac_numerical_dexterous: float
    false_positives: int
    false_negatives: int
    agreements: int


@dataclass(frozen=True, slots=True)
class ExperimentSummary:
    records: list[ExperimentRecord]
    confusion: list[ConfusionCell]
    gate3_crank_precision: float | None
    gate3_crank_recall: float | None
    gate4_residual_error_correlation: float | None
    gate5_c_orientation_stable: bool | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_records": len(self.records),
            "confusion": [asdict(c) for c in self.confusion],
            "gate3_crank_precision": self.gate3_crank_precision,
            "gate3_crank_recall": self.gate3_crank_recall,
            "gate4_residual_error_correlation": self.gate4_residual_error_correlation,
            "gate5_c_orientation_stable": self.gate5_c_orientation_stable,
            "notes": self.notes,
            "records": [r.to_dict() for r in self.records],
        }


def _build_confusion(records: list[ExperimentRecord]) -> list[ConfusionCell]:
    by_type: dict[int, list[ExperimentRecord]] = defaultdict(list)
    for r in records:
        if r.linkage_type is None:
            continue
        if r.prediction_outcome in {"regional_unreachable", "invalid_reduction", "boundary"}:
            continue
        by_type[r.linkage_type].append(r)
    cells: list[ConfusionCell] = []
    for t in sorted(by_type):
        rows = by_type[t]
        mean_c = sum(r.orientation_coverage for r in rows) / len(rows)
        frac_d = sum(1 for r in rows if r.strict_sampled_dexterity) / len(rows)
        cells.append(
            ConfusionCell(
                linkage_type=t,
                n_states=len(rows),
                mean_coverage=mean_c,
                frac_numerical_dexterous=frac_d,
                false_positives=sum(1 for r in rows if r.prediction_outcome == "false_positive"),
                false_negatives=sum(1 for r in rows if r.prediction_outcome == "false_negative"),
                agreements=sum(1 for r in rows if r.prediction_outcome == "agreement"),
            )
        )
    return cells


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx < 1e-15 or dy < 1e-15:
        return None
    return num / (dx * dy)


def run_architecture_experiments(
    *,
    resolution: SampleResolution = "coarse",
    seed: int = 0,
    n_ik_starts: int = 4,
    n_a_positions: int = 4,
    epsilon_w_values: tuple[float, ...] = (0.0, 0.05, 0.2),
    epsilon_s_values: tuple[float, ...] = (0.0, 0.05, 0.2),
    orientation_count: int | None = None,
) -> ExperimentSummary:
    """Run A workspace + B εw sweep + C εs sweep comparisons."""
    records: list[ExperimentRecord] = []
    a_samples = architecture_a_workspace_samples()[:n_a_positions]

    # Architecture A
    for sample in a_samples:
        params = ArchitectureParams()
        arm = ArchitectureA(params)
        records.append(
            _run_on_arm(
                arm,
                sample,
                architecture_id="A",
                params=params,
                resolution=resolution,
                seed=seed,
                n_ik_starts=n_ik_starts,
                orientation_count=orientation_count,
            )
        )

    # Architecture B εw sweep at first A position seed
    base = a_samples[0]
    for ew in epsilon_w_values:
        params = ArchitectureParams(epsilon_w=ew)
        arm = ArchitectureB(params)
        fk = arm.forward(base.joint_seed)
        sample = WorkspaceSample(
            position=fk.tool_position,
            joint_seed=base.joint_seed,
            label=f"B_ew={ew:g}:{base.label}",
            rho_w=base.rho_w,
        )
        records.append(
            _run_on_arm(
                arm,
                sample,
                architecture_id="B",
                params=params,
                resolution=resolution,
                seed=seed,
                n_ik_starts=n_ik_starts,
                orientation_count=orientation_count,
            )
        )

    # Architecture C εs sweep
    for es in epsilon_s_values:
        params = ArchitectureParams(epsilon_s=es)
        arm = ArchitectureC(params)
        fk = arm.forward(base.joint_seed)
        sample = WorkspaceSample(
            position=fk.tool_position,
            joint_seed=base.joint_seed,
            label=f"C_es={es:g}:{base.label}",
            rho_w=base.rho_w,
        )
        records.append(
            _run_on_arm(
                arm,
                sample,
                architecture_id="C",
                params=params,
                resolution=resolution,
                seed=seed,
                n_ik_starts=n_ik_starts,
                orientation_count=orientation_count,
            )
        )

    confusion = _build_confusion(records)

    # Gate 3: crank-subset precision/recall on Architecture A ordinary outcomes
    a_rows = [
        r
        for r in records
        if r.architecture_id == "A"
        and r.prediction_outcome in {"agreement", "false_positive", "false_negative"}
    ]
    tp = sum(
        1
        for r in a_rows
        if r.analytical_prediction and r.strict_sampled_dexterity
    )
    fp = sum(
        1
        for r in a_rows
        if r.analytical_prediction and not r.strict_sampled_dexterity
    )
    fn = sum(
        1
        for r in a_rows
        if (not r.analytical_prediction) and r.strict_sampled_dexterity
    )
    prec = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None

    # Gate 4: residual vs error indicator on B
    b_rows = [r for r in records if r.architecture_id == "B"]
    xs = [r.concurrency_residual for r in b_rows]
    ys = [
        0.0
        if r.prediction_outcome == "agreement"
        else 1.0
        if r.prediction_outcome in {"false_positive", "false_negative", "invalid_reduction"}
        else 0.5
        for r in b_rows
    ]
    corr = _pearson(xs, ys)

    # Gate 5: C keeps spherical exact and outcomes not dominated by invalid_reduction
    c_rows = [r for r in records if r.architecture_id == "C"]
    gate5 = None
    if c_rows:
        gate5 = all(r.spherical_reduction_status == "exact" for r in c_rows) and all(
            r.prediction_outcome != "invalid_reduction" for r in c_rows
        )

    return ExperimentSummary(
        records=records,
        confusion=confusion,
        gate3_crank_precision=prec,
        gate3_crank_recall=rec,
        gate4_residual_error_correlation=corr,
        gate5_c_orientation_stable=gate5,
        notes="Sprint 5 controlled architecture experiments",
    )


def run_architecture_a_type_grid(
    *,
    resolution: SampleResolution = "coarse",
    seed: int = 0,
    n_radial: int = 4,
    n_elbow: int = 3,
    n_ik_starts: int = 3,
    orientation_count: int | None = None,
) -> list[ExperimentRecord]:
    """Small Architecture A grid for agreement maps."""
    params = ArchitectureParams()
    arm = ArchitectureA(params)
    out: list[ExperimentRecord] = []
    for sample in radial_grid_positions(n_radial=n_radial, n_elbow=n_elbow, params=params):
        out.append(
            _run_on_arm(
                arm,
                sample,
                architecture_id="A",
                params=params,
                resolution=resolution,
                seed=seed,
                n_ik_starts=n_ik_starts,
                orientation_count=orientation_count,
            )
        )
    return out
