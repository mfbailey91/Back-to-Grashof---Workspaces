"""Diagnostics, controls, and experiment reporting for the terminal-roll fixture.

Units
-----
- position residuals: metres
- pointing residuals: dimensionless (``||d(q) - d(0)||``) and angle via ``||d0 x d||``
- roll residuals: radians
- finite-difference step ``h``: radians
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .axis_geometry import AxisLine, parallelism_residual
from .rotations import axis_angle_from_rotation, relative_rotation
from .terminal_roll_fixture import TerminalRollFixture, analytical_dd_dq6, analytical_dp_dq6

Vec3 = NDArray[np.floating]

# Explicit provisional tolerances (Sprint 01 / Check-in 1).
POSITION_ABS_TOL_M = 1e-12
POINTING_ABS_TOL = 1e-12
ROLL_ABS_TOL_RAD = 1e-10
POSITION_MOTION_FLOOR_M = 1e-6
POINTING_MOTION_FLOOR = 1e-6
DEFAULT_SWEEP_SAMPLES = 361
DEFAULT_FD_STEPS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6)


@dataclass(frozen=True, slots=True)
class SweepMetrics:
    experiment_id: str
    max_position_residual_m: float
    max_pointing_residual: float
    max_roll_angle_error_rad: float
    max_roll_axis_misalignment: float
    mean_position_residual_m: float
    mean_pointing_residual: float
    position_changes: bool
    pointing_changes: bool
    roll_recovered: bool


@dataclass(frozen=True, slots=True)
class FDRefinementRow:
    h: float
    dp_error: float
    dd_error: float


@dataclass(frozen=True, slots=True)
class ControlResult:
    experiment_id: str
    status: str
    expected: str
    observed: str
    metrics: SweepMetrics
    notes: str = ""


def make_aligned_fixture(
    *,
    r6: tuple[float, float, float] = (0.1, -0.2, 0.3),
    w6: tuple[float, float, float] = (0.0, 0.0, 1.0),
    axial_offset_m: float = 0.05,
) -> TerminalRollFixture:
    """Positive-control fixture: ``p`` on axis, ``d`` parallel to ``w6``."""
    axis = AxisLine(r6, w6)
    p0 = (
        r6[0] + axial_offset_m * axis.w[0],
        r6[1] + axial_offset_m * axis.w[1],
        r6[2] + axial_offset_m * axis.w[2],
    )
    return TerminalRollFixture.from_explicit(axis=axis, p0=p0, d0=axis.w)


def make_off_axis_fixture(
    *,
    transverse_offset_m: float = 0.02,
) -> TerminalRollFixture:
    """N1: task point offset transversely; pointing remains axis-aligned."""
    base = make_aligned_fixture()
    axis = base.axis
    # Build a unit transverse direction.
    helper = np.array([1.0, 0.0, 0.0], dtype=float)
    if abs(float(np.dot(helper, axis.w_array))) > 0.9:
        helper = np.array([0.0, 1.0, 0.0], dtype=float)
    transverse = np.cross(axis.w_array, helper)
    transverse = transverse / float(np.linalg.norm(transverse))
    p0 = base.p0_array + transverse_offset_m * transverse
    return TerminalRollFixture.from_explicit(axis=axis, p0=tuple(p0), d0=base.d0)


def make_misaligned_pointing_fixture(
    *,
    tilt_rad: float = 0.2,
) -> TerminalRollFixture:
    """N2: ``p`` on axis; pointing tilted away from ``w6``."""
    base = make_aligned_fixture()
    axis = base.axis
    helper = np.array([1.0, 0.0, 0.0], dtype=float)
    if abs(float(np.dot(helper, axis.w_array))) > 0.9:
        helper = np.array([0.0, 1.0, 0.0], dtype=float)
    transverse = np.cross(axis.w_array, helper)
    transverse = transverse / float(np.linalg.norm(transverse))
    d0 = math.cos(tilt_rad) * axis.w_array + math.sin(tilt_rad) * transverse
    return TerminalRollFixture.from_explicit(axis=axis, p0=base.p0, d0=tuple(d0))


def make_combined_violation_fixture(
    *,
    transverse_offset_m: float = 0.02,
    tilt_rad: float = 0.2,
) -> TerminalRollFixture:
    """N3: off-axis point and misaligned pointing."""
    off = make_off_axis_fixture(transverse_offset_m=transverse_offset_m)
    mis = make_misaligned_pointing_fixture(tilt_rad=tilt_rad)
    return TerminalRollFixture.from_explicit(axis=off.axis, p0=off.p0, d0=mis.d0)


def signed_roll_about_direction(R_rel: NDArray[np.floating], d: Vec3) -> tuple[float, float]:
    """Return ``(signed_angle, axis_misalignment)`` for relative rotation about ``d``.

    Uses a probe vector perpendicular to ``d`` and ``atan2`` so the angle covers
    a full ``(-pi, pi]`` range without Euler subtraction.
    """
    d_hat = np.asarray(d, dtype=float).reshape(3)
    d_hat = d_hat / float(np.linalg.norm(d_hat))
    helper = np.array([1.0, 0.0, 0.0], dtype=float)
    if abs(float(np.dot(helper, d_hat))) > 0.9:
        helper = np.array([0.0, 1.0, 0.0], dtype=float)
    v = np.cross(d_hat, helper)
    v = v / float(np.linalg.norm(v))
    v_rot = np.asarray(R_rel, dtype=float) @ v
    # Remove any numerical component along d before measuring planar angle.
    v_rot = v_rot - float(np.dot(v_rot, d_hat)) * d_hat
    n = float(np.linalg.norm(v_rot))
    if n < 1e-14:
        return 0.0, 0.0
    v_rot = v_rot / n
    y = np.cross(d_hat, v)
    signed = math.atan2(float(np.dot(v_rot, y)), float(np.dot(v_rot, v)))
    axis, angle = axis_angle_from_rotation(R_rel)
    if abs(angle) < 1e-14:
        axis_mis = 0.0
    else:
        if float(np.dot(axis, d_hat)) < 0.0:
            axis = -axis
        axis_mis = parallelism_residual(axis, d_hat)
    return signed, axis_mis


def sweep_residuals(
    fixture: TerminalRollFixture,
    *,
    experiment_id: str,
    n_samples: int = DEFAULT_SWEEP_SAMPLES,
    q0: float = 0.0,
) -> tuple[SweepMetrics, dict[str, NDArray[np.floating]]]:
    """Sweep ``q6`` over one full revolution and accumulate residuals vs ``q0``."""
    if n_samples < 2:
        raise ValueError("n_samples must be >= 2")
    q = np.linspace(0.0, 2.0 * math.pi, n_samples, endpoint=True)
    s0 = fixture.evaluate(q0)
    pos = np.zeros(n_samples)
    pointing = np.zeros(n_samples)
    roll_err = np.zeros(n_samples)
    axis_mis = np.zeros(n_samples)
    for i, qi in enumerate(q):
        si = fixture.evaluate(float(qi))
        pos[i] = float(np.linalg.norm(si.p - s0.p))
        pointing[i] = float(np.linalg.norm(si.d - s0.d))
        R_rel = relative_rotation(s0.R, si.R)
        signed, mis = signed_roll_about_direction(R_rel, s0.d)
        commanded = _wrap_to_pi(float(qi) - q0)
        roll_err[i] = abs(_wrap_to_pi(signed - commanded))
        axis_mis[i] = mis

    metrics = SweepMetrics(
        experiment_id=experiment_id,
        max_position_residual_m=float(np.max(pos)),
        max_pointing_residual=float(np.max(pointing)),
        max_roll_angle_error_rad=float(np.max(roll_err)),
        max_roll_axis_misalignment=float(np.max(axis_mis)),
        mean_position_residual_m=float(np.mean(pos)),
        mean_pointing_residual=float(np.mean(pointing)),
        position_changes=float(np.max(pos)) > POSITION_MOTION_FLOOR_M,
        pointing_changes=float(np.max(pointing)) > POINTING_MOTION_FLOOR,
        roll_recovered=float(np.max(roll_err)) <= ROLL_ABS_TOL_RAD
        and float(np.max(axis_mis)) <= 1e-8,
    )
    series = {
        "q6": q,
        "position_residual_m": pos,
        "pointing_residual": pointing,
        "roll_angle_error_rad": roll_err,
        "roll_axis_misalignment": axis_mis,
    }
    return metrics, series


def central_difference_derivatives(
    fixture: TerminalRollFixture,
    q6: float,
    h: float,
) -> tuple[Vec3, Vec3]:
    """Central finite-difference estimates of ``dp/dq6`` and ``dd/dq6``."""
    if h <= 0.0:
        raise ValueError("finite-difference step h must be positive")
    sp = fixture.evaluate(q6 + h)
    sm = fixture.evaluate(q6 - h)
    dp = (sp.p - sm.p) / (2.0 * h)
    dd = (sp.d - sm.d) / (2.0 * h)
    return dp, dd


def finite_difference_refinement(
    fixture: TerminalRollFixture,
    *,
    q6: float = 0.3,
    steps: Sequence[float] = DEFAULT_FD_STEPS,
) -> list[FDRefinementRow]:
    """Compare analytical derivatives to central FD over multiple step sizes."""
    state = fixture.evaluate(q6)
    rows: list[FDRefinementRow] = []
    for h in steps:
        dp_fd, dd_fd = central_difference_derivatives(fixture, q6, float(h))
        dp_err = float(np.linalg.norm(dp_fd - state.dp_dq6))
        dd_err = float(np.linalg.norm(dd_fd - state.dd_dq6))
        # Cross-check named analytical helpers against state fields.
        assert float(np.linalg.norm(state.dp_dq6 - analytical_dp_dq6(state.p, fixture.axis))) < 1e-15
        assert float(np.linalg.norm(state.dd_dq6 - analytical_dd_dq6(state.d, fixture.axis))) < 1e-15
        rows.append(FDRefinementRow(h=float(h), dp_error=dp_err, dd_error=dd_err))
    return rows


def fd_converges(rows: Sequence[FDRefinementRow]) -> bool:
    """Return True when error decreases over the usable (non-roundoff) step range."""
    if len(rows) < 3:
        return False
    # Ignore the smallest step if round-off inflates error.
    usable = list(rows[:-1]) if rows[-1].dp_error > rows[-2].dp_error else list(rows)
    if len(usable) < 3:
        return False
    dp_ok = usable[0].dp_error > usable[1].dp_error > usable[2].dp_error or (
        usable[0].dp_error >= usable[-1].dp_error * 10.0
    )
    dd_ok = usable[0].dd_error > usable[1].dd_error > usable[2].dd_error or (
        usable[0].dd_error >= usable[-1].dd_error * 10.0
    )
    # Also accept near-machine-zero errors throughout (aligned analytic zero case).
    if all(r.dp_error < 1e-10 and r.dd_error < 1e-10 for r in usable):
        return True
    return bool(dp_ok and dd_ok)


def evaluate_positive_control(fixture: TerminalRollFixture | None = None) -> ControlResult:
    fixture = fixture or make_aligned_fixture()
    metrics, _ = sweep_residuals(fixture, experiment_id="ATR_EXP_001")
    ok = (
        not metrics.position_changes
        and not metrics.pointing_changes
        and metrics.max_position_residual_m <= POSITION_ABS_TOL_M
        and metrics.max_pointing_residual <= POINTING_ABS_TOL
        and metrics.roll_recovered
    )
    return ControlResult(
        experiment_id="ATR_EXP_001",
        status="PASS" if ok else "FAIL",
        expected="position invariant; pointing invariant; roll recovers Delta q6",
        observed=(
            f"max|dp|={metrics.max_position_residual_m:.3e} m; "
            f"max|dd|={metrics.max_pointing_residual:.3e}; "
            f"max roll err={metrics.max_roll_angle_error_rad:.3e} rad"
        ),
        metrics=metrics,
    )


def evaluate_off_axis_control(fixture: TerminalRollFixture | None = None) -> ControlResult:
    fixture = fixture or make_off_axis_fixture()
    metrics, _ = sweep_residuals(fixture, experiment_id="ATR_EXP_002")
    ok = metrics.position_changes and not metrics.pointing_changes
    return ControlResult(
        experiment_id="ATR_EXP_002",
        status="PASS" if ok else "FAIL",
        expected="position changes; pointing invariant",
        observed=(
            f"position_changes={metrics.position_changes}; "
            f"pointing_changes={metrics.pointing_changes}; "
            f"max|dp|={metrics.max_position_residual_m:.3e} m"
        ),
        metrics=metrics,
    )


def evaluate_misaligned_control(fixture: TerminalRollFixture | None = None) -> ControlResult:
    fixture = fixture or make_misaligned_pointing_fixture()
    metrics, _ = sweep_residuals(fixture, experiment_id="ATR_EXP_003")
    ok = (not metrics.position_changes) and metrics.pointing_changes
    return ControlResult(
        experiment_id="ATR_EXP_003",
        status="PASS" if ok else "FAIL",
        expected="position invariant; pointing changes",
        observed=(
            f"position_changes={metrics.position_changes}; "
            f"pointing_changes={metrics.pointing_changes}; "
            f"max|dd|={metrics.max_pointing_residual:.3e}"
        ),
        metrics=metrics,
    )


def evaluate_combined_control(fixture: TerminalRollFixture | None = None) -> ControlResult:
    fixture = fixture or make_combined_violation_fixture()
    metrics, _ = sweep_residuals(fixture, experiment_id="ATR_EXP_004")
    ok = metrics.position_changes and metrics.pointing_changes
    return ControlResult(
        experiment_id="ATR_EXP_004",
        status="PASS" if ok else "FAIL",
        expected="position and pointing both change",
        observed=(
            f"position_changes={metrics.position_changes}; "
            f"pointing_changes={metrics.pointing_changes}"
        ),
        metrics=metrics,
    )


def evaluate_fd_refinement(fixture: TerminalRollFixture | None = None) -> tuple[ControlResult, list[FDRefinementRow]]:
    # Use off-axis + misaligned so derivatives are nonzero and convergence is visible.
    fixture = fixture or make_combined_violation_fixture()
    rows = finite_difference_refinement(fixture)
    ok = fd_converges(rows)
    metrics, _ = sweep_residuals(fixture, experiment_id="ATR_EXP_005", n_samples=37)
    result = ControlResult(
        experiment_id="ATR_EXP_005",
        status="PASS" if ok else "FAIL",
        expected="analytical vs central-FD derivative error converges over usable h",
        observed="; ".join(f"h={r.h:g}: dp_err={r.dp_error:.3e}, dd_err={r.dd_error:.3e}" for r in rows),
        metrics=metrics,
        notes="Fixture intentionally violates alignment so derivatives are nonzero.",
    )
    return result, rows


def git_commit_hash(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def write_experiment_artifacts(
    *,
    repo_root: Path,
    experiment_id: str,
    control: ControlResult,
    fixture: TerminalRollFixture,
    series: dict[str, NDArray[np.floating]] | None = None,
    fd_rows: Sequence[FDRefinementRow] | None = None,
    extra_manifest: dict[str, Any] | None = None,
) -> Path:
    """Write ``results/aligned_terminal_roll/<id>/{manifest,metrics,summary,figures}``."""
    out = repo_root / "results" / "aligned_terminal_roll" / experiment_id
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    if series is None:
        _, series = sweep_residuals(fixture, experiment_id=experiment_id)

    metrics_path = out / "metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "q6_rad",
                "position_residual_m",
                "pointing_residual",
                "roll_angle_error_rad",
                "roll_axis_misalignment",
            ]
        )
        for i in range(len(series["q6"])):
            writer.writerow(
                [
                    f"{float(series['q6'][i]):.16e}",
                    f"{float(series['position_residual_m'][i]):.16e}",
                    f"{float(series['pointing_residual'][i]):.16e}",
                    f"{float(series['roll_angle_error_rad'][i]):.16e}",
                    f"{float(series['roll_axis_misalignment'][i]):.16e}",
                ]
            )

    if fd_rows is not None:
        fd_path = out / "fd_refinement.csv"
        with fd_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["h_rad", "dp_error", "dd_error"])
            for row in fd_rows:
                writer.writerow([f"{row.h:.16e}", f"{row.dp_error:.16e}", f"{row.dd_error:.16e}"])

    figure_path = fig_dir / "residuals_vs_q6.png"
    _plot_residuals(series, figure_path, title=experiment_id)

    manifest: dict[str, Any] = {
        "experiment_id": experiment_id,
        "repository_commit": git_commit_hash(repo_root),
        "status": control.status,
        "units": {
            "length": "metre",
            "angle": "radian",
            "axis_direction": "dimensionless unit vector",
        },
        "tolerances": {
            "position_abs_tol_m": POSITION_ABS_TOL_M,
            "pointing_abs_tol": POINTING_ABS_TOL,
            "roll_abs_tol_rad": ROLL_ABS_TOL_RAD,
            "position_motion_floor_m": POSITION_MOTION_FLOOR_M,
            "pointing_motion_floor": POINTING_MOTION_FLOOR,
        },
        "model": {
            "axis_r_m": list(fixture.axis.r),
            "axis_w": list(fixture.axis.w),
            "p0_m": list(fixture.p0),
            "d0": list(fixture.d0),
        },
        "metrics": asdict(control.metrics),
        "expected": control.expected,
        "observed": control.observed,
        "notes": control.notes,
        "random_seed": None,
        "software_version": "grashof-workspace spatial_experiments sprint01",
    }
    if extra_manifest:
        manifest.update(extra_manifest)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    summary = "\n".join(
        [
            f"# {experiment_id}",
            "",
            f"**Status:** {control.status}",
            f"**Commit:** {manifest['repository_commit']}",
            "",
            "## Expected",
            "",
            control.expected,
            "",
            "## Observed",
            "",
            control.observed,
            "",
            "## Metrics",
            "",
            f"- max position residual: {control.metrics.max_position_residual_m:.6e} m",
            f"- max pointing residual: {control.metrics.max_pointing_residual:.6e}",
            f"- max roll angle error: {control.metrics.max_roll_angle_error_rad:.6e} rad",
            f"- max roll axis misalignment: {control.metrics.max_roll_axis_misalignment:.6e}",
            f"- position_changes: {control.metrics.position_changes}",
            f"- pointing_changes: {control.metrics.pointing_changes}",
            f"- roll_recovered: {control.metrics.roll_recovered}",
            "",
            "## Figure",
            "",
            f"![residuals](figures/{figure_path.name})",
            "",
        ]
    )
    (out / "summary.md").write_text(summary, encoding="utf-8")
    return out


def run_all_controls(repo_root: Path) -> list[ControlResult]:
    """Execute ATR_EXP_001–005 and write artifacts."""
    results: list[ControlResult] = []

    cases: list[tuple[str, Callable[[], ControlResult], Callable[[], TerminalRollFixture]]] = [
        ("ATR_EXP_001", evaluate_positive_control, make_aligned_fixture),
        ("ATR_EXP_002", evaluate_off_axis_control, make_off_axis_fixture),
        ("ATR_EXP_003", evaluate_misaligned_control, make_misaligned_pointing_fixture),
        ("ATR_EXP_004", evaluate_combined_control, make_combined_violation_fixture),
    ]
    for exp_id, eval_fn, fixture_fn in cases:
        fixture = fixture_fn()
        control = eval_fn()
        assert control.experiment_id == exp_id
        metrics, series = sweep_residuals(fixture, experiment_id=exp_id)
        # Re-bind metrics from the series used for artifacts.
        control = ControlResult(
            experiment_id=control.experiment_id,
            status=control.status,
            expected=control.expected,
            observed=control.observed,
            metrics=metrics,
            notes=control.notes,
        )
        write_experiment_artifacts(
            repo_root=repo_root,
            experiment_id=exp_id,
            control=control,
            fixture=fixture,
            series=series,
        )
        results.append(control)

    fixture5 = make_combined_violation_fixture()
    control5, fd_rows = evaluate_fd_refinement(fixture5)
    _, series5 = sweep_residuals(fixture5, experiment_id="ATR_EXP_005")
    write_experiment_artifacts(
        repo_root=repo_root,
        experiment_id="ATR_EXP_005",
        control=control5,
        fixture=fixture5,
        series=series5,
        fd_rows=fd_rows,
        extra_manifest={"fd_refinement": [asdict(r) for r in fd_rows]},
    )
    results.append(control5)
    return results


def _plot_residuals(series: dict[str, NDArray[np.floating]], path: Path, *, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    q = series["q6"]
    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    axes[0].plot(q, series["position_residual_m"])
    axes[0].set_ylabel("position residual [m]")
    axes[0].set_title(title)
    axes[1].plot(q, series["pointing_residual"])
    axes[1].set_ylabel("pointing residual")
    axes[2].plot(q, series["roll_angle_error_rad"])
    axes[2].set_ylabel("roll angle error [rad]")
    axes[2].set_xlabel("q6 [rad]")
    for ax in axes:
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _wrap_to_pi(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi
