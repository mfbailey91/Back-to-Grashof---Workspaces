from __future__ import annotations

"""One-DOF predictor-corrector continuation for UUUR closure.

The free parameter is a tool-U coordinate selected by `ExplorerCase.tool_axis`:
- tool axis `a` freezes index 0 (`u0_alpha`)
- tool axis `b` freezes index 1 (`u0_beta`)

Dependent joint angles are corrected at each step by least-squares reduction of
the SE(3) closure residual. Singularity hooks monitor the smallest singular
value of the constrained Jacobian.

True winding numbers are not computed here (Sprint V04).
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .closure import (
    ClosureProblem,
    SeedSolveResult,
    closure_residual,
    is_near_singular,
    residual_norm,
    solve_seed_assembly,
)
from .geometry import PhysicalGeometrySample
from .models import (
    BranchClass,
    BranchResult,
    BranchTrajectory,
    ExplorerCase,
    ToolAxis,
    TrajectorySample,
)

Array = NDArray[np.float64]


@dataclass(frozen=True)
class ContinuationConfig:
    step: float = 0.08
    max_steps: int = 180
    return_tol: float = 0.12
    residual_tol: float = 1e-6
    singular_tol: float = 1e-4
    max_corrector_iters: int = 12


def free_parameter_index(case: ExplorerCase) -> int:
    if case.tool_axis is ToolAxis.A:
        return 0
    if case.tool_axis is ToolAxis.B:
        return 1
    raise ValueError(f"unsupported tool axis: {case.tool_axis}")


def free_parameter_name(case: ExplorerCase) -> str:
    return "u0_alpha" if case.tool_axis is ToolAxis.A else "u0_beta"


def _correct_dependent(
    problem: ClosureProblem,
    angles: Array,
    *,
    free_index: int,
    residual_tol: float,
    max_iters: int,
) -> tuple[Array, bool, float]:
    current = np.asarray(angles, dtype=float).copy()
    free_value = current[free_index]
    for _ in range(max_iters):
        residual = closure_residual(problem, current)
        norm = float(np.linalg.norm(residual))
        if norm < residual_tol:
            current[free_index] = free_value
            return current, True, norm
        jac = np.zeros((6, problem.n_dof - 1), dtype=float)
        eps = 1e-7
        dependent = [i for i in range(problem.n_dof) if i != free_index]
        for col, index in enumerate(dependent):
            stepped = current.copy()
            stepped[index] += eps
            jac[:, col] = (closure_residual(problem, stepped) - residual) / eps
        try:
            delta, *_ = np.linalg.lstsq(jac, -residual, rcond=None)
        except np.linalg.LinAlgError:
            return current, False, norm
        for col, index in enumerate(dependent):
            current[index] += float(delta[col])
        current[free_index] = free_value
    norm = residual_norm(problem, current)
    return current, norm < residual_tol * 10.0, norm


def continue_uuur_branch(
    problem: ClosureProblem,
    case: ExplorerCase,
    *,
    sample_id: str,
    branch_id: str = "branch_00",
    seed: SeedSolveResult | None = None,
    config: ContinuationConfig | None = None,
) -> tuple[BranchTrajectory, BranchResult]:
    """Continue a UUUR one-DOF branch from a local seed assembly."""
    cfg = config or ContinuationConfig()
    free_index = free_parameter_index(case)
    seed_result = seed or solve_seed_assembly(problem)
    notes = [
        "closure_continuation_v03",
        "winding_pending_v04",
        f"free_parameter={free_parameter_name(case)}",
    ]

    if not seed_result.success:
        trajectory = BranchTrajectory(
            sample_id=sample_id,
            case=case,
            branch_id=branch_id,
            family=problem.geometry.family,
            free_parameter=free_parameter_name(case),
            samples=[],
            branch_closed=False,
            singularity_count=0,
            notes=[*notes, "seed_solve_failed", seed_result.message],
        )
        result = BranchResult(
            sample_id=sample_id,
            case=case,
            branch_id=branch_id,
            branch_closed=False,
            singularity_count=0,
            w_alpha=None,
            w_beta=None,
            class_alpha=BranchClass.NO_ASSEMBLY,
            class_beta=BranchClass.NO_ASSEMBLY,
            tool_range_alpha=None,
            tool_range_beta=None,
            notes=trajectory.notes,
        )
        return trajectory, result

    angles = seed_result.angles.copy()
    samples: list[TrajectorySample] = [
        TrajectorySample(
            parameter=float(angles[free_index]),
            joint_angles=tuple(float(v) for v in angles),
            residual_norm=seed_result.residual_norm,
            singular=is_near_singular(
                problem, angles, free_index=free_index, tol=cfg.singular_tol
            ),
        )
    ]
    singularity_count = int(samples[0].singular)
    start_parameter = float(angles[free_index])
    start_angles = angles.copy()
    branch_closed = False
    stop_note = "max_steps_reached"

    for _ in range(cfg.max_steps):
        step = cfg.step
        advanced = False
        for _retry in range(4):
            predicted = angles.copy()
            predicted[free_index] += step
            corrected, ok, norm = _correct_dependent(
                problem,
                predicted,
                free_index=free_index,
                residual_tol=cfg.residual_tol,
                max_iters=cfg.max_corrector_iters,
            )
            if ok:
                advanced = True
                break
            step *= 0.5
        if not advanced:
            stop_note = "corrector_failed"
            break

        singular = is_near_singular(
            problem, corrected, free_index=free_index, tol=cfg.singular_tol
        )
        if singular:
            singularity_count += 1
            samples.append(
                TrajectorySample(
                    parameter=float(corrected[free_index]),
                    joint_angles=tuple(float(v) for v in corrected),
                    residual_norm=norm,
                    singular=True,
                )
            )
            stop_note = "singularity_detected"
            angles = corrected
            break

        samples.append(
            TrajectorySample(
                parameter=float(corrected[free_index]),
                joint_angles=tuple(float(v) for v in corrected),
                residual_norm=norm,
                singular=False,
            )
        )
        angles = corrected

        delta_param = float(angles[free_index] - start_parameter)
        if delta_param > 2.0 * np.pi - cfg.return_tol:
            config_error = float(np.linalg.norm((angles - start_angles + np.pi) % (2 * np.pi) - np.pi))
            if config_error < 0.35:
                branch_closed = True
                stop_note = "free_parameter_period"
                break

    notes.append(stop_note)
    alphas = np.asarray([sample.joint_angles[0] for sample in samples], dtype=float)
    betas = np.asarray([sample.joint_angles[1] for sample in samples], dtype=float)
    tool_range_alpha = float(np.ptp(alphas)) if len(alphas) else None
    tool_range_beta = float(np.ptp(betas)) if len(betas) else None

    if branch_closed:
        class_label = BranchClass.ROCKER
        notes.append("provisional_label_pending_true_winding_v04")
    elif singularity_count > 0 and stop_note == "singularity_detected":
        class_label = BranchClass.CHANGE_POINT
    else:
        class_label = BranchClass.OPEN_BRANCH

    trajectory = BranchTrajectory(
        sample_id=sample_id,
        case=case,
        branch_id=branch_id,
        family=problem.geometry.family,
        free_parameter=free_parameter_name(case),
        samples=samples,
        branch_closed=branch_closed,
        singularity_count=singularity_count,
        notes=notes,
    )
    result = BranchResult(
        sample_id=sample_id,
        case=case,
        branch_id=branch_id,
        branch_closed=branch_closed,
        singularity_count=singularity_count,
        w_alpha=None,
        w_beta=None,
        class_alpha=class_label,
        class_beta=class_label,
        tool_range_alpha=tool_range_alpha,
        tool_range_beta=tool_range_beta,
        notes=notes,
    )
    return trajectory, result


def continue_physical_uuur_sample(
    sample: PhysicalGeometrySample,
    case: ExplorerCase,
    *,
    config: ContinuationConfig | None = None,
) -> tuple[BranchTrajectory, BranchResult]:
    from .closure import build_uuur_closure_problem

    if sample.provenance != "physical_geometry_v02b":
        raise ValueError("V03 continuation accepts only V02B physical geometry samples")
    problem = build_uuur_closure_problem(sample.geometry)
    return continue_uuur_branch(
        problem,
        case,
        sample_id=sample.sample_id,
        config=config,
    )
