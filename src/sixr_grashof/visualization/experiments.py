"""Sprint 4–5 numerical experiment visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from sixr_grashof.architectures import ArchitectureA
from sixr_grashof.experiments.convergence import run_convergence_study
from sixr_grashof.experiments.fixed_position import run_fixed_position_experiment
from sixr_grashof.experiments.offset_sweep import (
    ExperimentSummary,
    run_architecture_a_type_grid,
    run_architecture_experiments,
)
from sixr_grashof.io.schemas import ExperimentRecord
from sixr_grashof.sampling.orientations import sample_orientations
from sixr_grashof.sampling.workspace import architecture_a_workspace_samples

_INK = "#1a1f24"
_STEEL = "#2f6f8f"
_TEAL = "#1f7a6c"
_AMBER = "#c47b2c"
_ROSE = "#a34848"
_MUTED = "#6b7280"
_PANEL = "#f3f5f7"
_GRID = "#d7dde3"


def _save(fig: Any, output: str | Path | None, show: bool) -> Path | None:
    out_path: Path | None = None
    if output is not None:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return out_path


def plot_orientation_sample_cloud(
    *,
    output: str | Path | None = None,
    show: bool = False,
    orientation_count: int = 96,
    seed: int = 0,
) -> Path | None:
    """Feasible vs failed orientation samples projected via quaternion XYZ."""
    arch = ArchitectureA()
    sample = architecture_a_workspace_samples()[0]
    result = run_fixed_position_experiment(
        arch,
        sample,
        resolution="coarse",
        seed=seed,
        n_ik_starts=4,
        orientation_count=orientation_count,
    )
    rotations = sample_orientations("coarse", seed=seed, count=orientation_count)
    from sixr_grashof.sampling.orientations import rotation_to_quaternion

    xs, ys, zs, colors = [], [], [], []
    for i, R in enumerate(rotations):
        q = rotation_to_quaternion(R)
        xs.append(q[1])
        ys.append(q[2])
        zs.append(q[3])
        st = result.statuses[i]
        colors.append(
            _TEAL if st == "solved" else (_ROSE if st == "unreachable" else _AMBER)
        )

    fig = plt.figure(figsize=(8, 6.5))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(xs, ys, zs, c=colors, s=28, depthshade=True)
    ax.set_title(
        f"SO(3) samples @ fixed p  |  C={result.record.orientation_coverage:.2f}  |  "
        f"eligible solve={result.eligible_solve_rate:.2f}",
        color=_INK,
        fontsize=11,
    )
    ax.set_xlabel("qx")
    ax.set_ylabel("qy")
    ax.set_zlabel("qz")
    fig.text(
        0.5,
        0.02,
        "teal=solved  amber=solver_failed  rose=unreachable",
        ha="center",
        color=_MUTED,
        fontsize=8,
    )
    return _save(fig, output, show)


def plot_connectivity_components(
    *,
    output: str | Path | None = None,
    show: bool = False,
    orientation_count: int = 96,
    seed: int = 0,
) -> Path | None:
    arch = ArchitectureA()
    sample = architecture_a_workspace_samples()[0]
    result = run_fixed_position_experiment(
        arch,
        sample,
        resolution="coarse",
        seed=seed,
        n_ik_starts=4,
        orientation_count=orientation_count,
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(_PANEL)
    labels = list(result.component_labels)
    if labels:
        counts = np.bincount(np.array(labels, dtype=int))
        ax.bar(range(len(counts)), counts, color=_STEEL)
    ax.set_xlabel("component id")
    ax.set_ylabel("solved samples")
    ax.set_title(
        f"Feasible-orientation components  |  n_comp={result.record.orientation_component_count}",
        color=_INK,
    )
    ax.grid(True, axis="y", color=_GRID)
    return _save(fig, output, show)


def plot_gate2_coverage_convergence(
    *,
    output: str | Path | None = None,
    show: bool = False,
    seed: int = 0,
) -> Path | None:
    report = run_convergence_study(
        seed=seed,
        resolutions=("coarse", "medium"),
        n_ik_starts=3,
        orientation_counts={"coarse": 64, "medium": 128},
        coverage_tol=0.2,
    )
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(_PANEL)
    xs = [m.sample_count for m in report.metrics]
    ys = [m.coverage for m in report.metrics]
    ax.plot(xs, ys, "o-", color=_STEEL, linewidth=2.2, markersize=8, label="C(p)")
    ax.set_xlabel("orientation sample count")
    ax.set_ylabel("coverage")
    badge = "PASS" if report.gate2_pass else "FAIL"
    ax.set_title(f"Gate 2 coverage convergence  |  {badge}", color=_INK)
    ax.grid(True, color=_GRID)
    ax.legend(frameon=False)
    fig.text(0.5, 0.02, report.notes, ha="center", fontsize=8, color=_MUTED)
    return _save(fig, output, show)


def plot_solver_diagnostics(
    *,
    output: str | Path | None = None,
    show: bool = False,
    orientation_count: int = 96,
    seed: int = 0,
) -> Path | None:
    arch = ArchitectureA()
    sample = architecture_a_workspace_samples()[0]
    result = run_fixed_position_experiment(
        arch,
        sample,
        resolution="coarse",
        seed=seed,
        n_ik_starts=4,
        orientation_count=orientation_count,
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(_PANEL)
    labels = ["solved", "unreachable", "solver_failed"]
    vals = [
        result.record.solved_count,
        result.record.unreachable_count,
        result.record.solver_failed_count,
    ]
    colors = [_TEAL, _ROSE, _AMBER]
    ax.bar(labels, vals, color=colors)
    ax.set_ylabel("count")
    ax.set_title("IK status taxonomy (never confuse failure with geometry)", color=_INK)
    ax.grid(True, axis="y", color=_GRID)
    return _save(fig, output, show)


def plot_confusion_heatmap(
    summary: ExperimentSummary | None = None,
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    if summary is None:
        summary = run_architecture_experiments(
            orientation_count=24,
            n_a_positions=3,
            n_ik_starts=3,
            seed=0,
        )
    types = list(range(1, 17))
    fp = np.zeros(16)
    fn = np.zeros(16)
    ag = np.zeros(16)
    for cell in summary.confusion:
        i = cell.linkage_type - 1
        fp[i] = cell.false_positives
        fn[i] = cell.false_negatives
        ag[i] = cell.agreements
    data = np.vstack([ag, fp, fn])
    fig, ax = plt.subplots(figsize=(10, 3.8))
    fig.patch.set_facecolor("white")
    im = ax.imshow(data, aspect="auto", cmap="YlGnBu")
    ax.set_yticks([0, 1, 2], ["agreement", "false +", "false −"])
    ax.set_xticks(range(16), [str(t) for t in types])
    ax.set_xlabel("linkage type")
    ax.set_title("Sprint 5 — type-wise prediction outcomes", color=_INK)
    fig.colorbar(im, ax=ax, fraction=0.03)
    return _save(fig, output, show)


def plot_residual_vs_error(
    summary: ExperimentSummary | None = None,
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    if summary is None:
        summary = run_architecture_experiments(
            orientation_count=24, n_a_positions=2, n_ik_starts=3, seed=0
        )
    b_rows = [r for r in summary.records if r.architecture_id == "B"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(_PANEL)
    for r in b_rows:
        err = 0.0 if r.prediction_outcome == "agreement" else 1.0
        color = _TEAL if err == 0 else _ROSE
        ax.scatter(
            [r.concurrency_residual],
            [err],
            c=color,
            s=70,
            edgecolors="white",
            label=f"εw={r.offset_parameters['epsilon_w']:g}",
        )
    ax.set_xlabel(r"concurrency residual $\rho_C$")
    ax.set_ylabel("prediction error indicator")
    ax.set_title("Architecture B — residual vs prediction error", color=_INK)
    ax.grid(True, color=_GRID)
    ax.set_ylim(-0.1, 1.1)
    return _save(fig, output, show)


def plot_offset_sweeps(
    summary: ExperimentSummary | None = None,
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    if summary is None:
        summary = run_architecture_experiments(
            orientation_count=24, n_a_positions=2, n_ik_starts=3, seed=0
        )
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor("white")
    for ax in (ax0, ax1):
        ax.set_facecolor(_PANEL)
        ax.grid(True, color=_GRID)

    b_rows = sorted(
        [r for r in summary.records if r.architecture_id == "B"],
        key=lambda r: r.offset_parameters["epsilon_w"],
    )
    ax0.plot(
        [r.offset_parameters["epsilon_w"] for r in b_rows],
        [r.orientation_coverage for r in b_rows],
        "o-",
        color=_STEEL,
        label="coverage",
    )
    ax0.plot(
        [r.offset_parameters["epsilon_w"] for r in b_rows],
        [r.concurrency_residual for r in b_rows],
        "s--",
        color=_AMBER,
        label=r"$\rho_C$",
    )
    ax0.set_xlabel(r"$\varepsilon_w$")
    ax0.set_title("Architecture B sweep", color=_INK)
    ax0.legend(frameon=False, fontsize=8)

    c_rows = sorted(
        [r for r in summary.records if r.architecture_id == "C"],
        key=lambda r: r.offset_parameters["epsilon_s"],
    )
    ax1.plot(
        [r.offset_parameters["epsilon_s"] for r in c_rows],
        [r.orientation_coverage for r in c_rows],
        "o-",
        color=_TEAL,
        label="coverage",
    )
    ax1.plot(
        [r.offset_parameters["epsilon_s"] for r in c_rows],
        [1.0 if r.spherical_reduction_status == "exact" else 0.0 for r in c_rows],
        "s--",
        color=_MUTED,
        label="spherical exact",
    )
    ax1.set_xlabel(r"$\varepsilon_s$")
    ax1.set_title("Architecture C sweep", color=_INK)
    ax1.legend(frameon=False, fontsize=8)
    fig.suptitle("Sprint 5 — offset sweeps", color=_INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, output, show)


def plot_agreement_map(
    records: list[ExperimentRecord] | None = None,
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    if records is None:
        records = run_architecture_a_type_grid(
            n_radial=4, n_elbow=3, orientation_count=16, n_ik_starts=3, seed=0
        )
    fig, ax = plt.subplots(figsize=(7.5, 6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(_PANEL)
    for r in records:
        q2 = r.joint_configuration_seed[1]
        q3 = r.joint_configuration_seed[2]
        color = {
            "agreement": _TEAL,
            "false_positive": _ROSE,
            "false_negative": _AMBER,
            "boundary": _MUTED,
            "invalid_reduction": _ROSE,
            "regional_unreachable": _MUTED,
            "not_applicable": _MUTED,
        }.get(r.prediction_outcome, _MUTED)
        ax.scatter([q2], [q3], c=color, s=55, edgecolors="white")
    ax.set_xlabel("q2")
    ax.set_ylabel("q3")
    ax.set_title("Architecture A — prediction agreement map", color=_INK)
    ax.grid(True, color=_GRID)
    return _save(fig, output, show)
