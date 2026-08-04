"""Gate-2 coarse/medium/fine convergence report (Sprint 4)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sixr_grashof.architectures import ArchitectureA, ArchitectureParams
from sixr_grashof.experiments.fixed_position import run_fixed_position_experiment
from sixr_grashof.sampling.orientations import SampleResolution
from sixr_grashof.sampling.workspace import WorkspaceSample, architecture_a_workspace_samples


@dataclass(frozen=True, slots=True)
class ResolutionMetrics:
    resolution: SampleResolution
    sample_count: int
    coverage: float
    component_count: int
    strict_sampled_dexterity: bool
    solved_count: int
    unreachable_count: int
    solver_failed_count: int


@dataclass(frozen=True, slots=True)
class ConvergenceReport:
    """Gate-2 convergence diagnostics for one Architecture A position."""

    position_label: str
    position: tuple[float, float, float]
    seed: int
    metrics: tuple[ResolutionMetrics, ...]
    coverage_delta_coarse_medium: float
    gate2_pass: bool
    notes: str

    def to_dict(self) -> dict:
        return {
            "position_label": self.position_label,
            "position": list(self.position),
            "seed": self.seed,
            "metrics": [asdict(m) for m in self.metrics],
            "coverage_delta_coarse_medium": self.coverage_delta_coarse_medium,
            "gate2_pass": self.gate2_pass,
            "notes": self.notes,
        }


def run_convergence_study(
    *,
    sample: WorkspaceSample | None = None,
    seed: int = 0,
    params: ArchitectureParams | None = None,
    resolutions: tuple[SampleResolution, ...] = ("coarse", "medium"),
    include_fine: bool = False,
    n_ik_starts: int = 4,
    coverage_tol: float = 0.12,
    orientation_counts: dict[str, int] | None = None,
) -> ConvergenceReport:
    """Compare aggregate metrics across sampling densities at one position."""
    arch = ArchitectureA(params)
    if sample is None:
        sample = architecture_a_workspace_samples(params=params)[0]
    res_list: list[SampleResolution] = list(resolutions)
    if include_fine and "fine" not in res_list:
        res_list.append("fine")

    metrics: list[ResolutionMetrics] = []
    for res in res_list:
        count = None if orientation_counts is None else orientation_counts.get(res)
        result = run_fixed_position_experiment(
            arch,
            sample,
            resolution=res,
            seed=seed,
            n_ik_starts=n_ik_starts,
            orientation_count=count,
        )
        r = result.record
        metrics.append(
            ResolutionMetrics(
                resolution=res,  # type: ignore[arg-type]
                sample_count=r.orientation_sample_count,
                coverage=r.orientation_coverage,
                component_count=r.orientation_component_count,
                strict_sampled_dexterity=r.strict_sampled_dexterity,
                solved_count=r.solved_count,
                unreachable_count=r.unreachable_count,
                solver_failed_count=r.solver_failed_count,
            )
        )

    by_name = {m.resolution: m for m in metrics}
    delta = 0.0
    gate = True
    notes = "Gate 2 convergence"
    if "coarse" in by_name and "medium" in by_name:
        delta = abs(by_name["medium"].coverage - by_name["coarse"].coverage)
        gate = delta <= coverage_tol
        if not gate:
            notes = (
                f"Gate 2 fail: |C_medium - C_coarse|={delta:.3f} > tol={coverage_tol}; "
                "Sprint 5 interpretation unverified"
            )
    return ConvergenceReport(
        position_label=sample.label,
        position=sample.position,
        seed=seed,
        metrics=tuple(metrics),
        coverage_delta_coarse_medium=delta,
        gate2_pass=gate,
        notes=notes,
    )
