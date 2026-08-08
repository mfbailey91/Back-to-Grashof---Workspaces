from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .closure import audit_reference_geometry
from .cycle_continuation import CycleTrace, continue_until_return
from .geometry import JointGeometry, SpatialFourBarGeometry, normalize, scale
from .geometry_descriptors import generate_physical_geometry_samples
from .models import OrderedFamily
from .winding import WindingClassification, classify_cycle, classify_geometry


@dataclass(frozen=True)
class RobustnessRun:
    label: str
    step_size: float
    direction: int
    returned: bool
    status: str
    w_alpha: int | None
    w_beta: int | None
    class_alpha: str
    class_beta: str
    coverage_alpha: float | None
    coverage_beta: float | None
    max_raw_increment: float | None
    points: int


@dataclass(frozen=True)
class OrientationSweepRun:
    phi_deg: float
    axis_order: str
    audit_status: str
    jacobian_rank: int
    jacobian_nullity: int
    returned: bool
    status: str
    w_alpha: int | None
    w_beta: int | None
    class_alpha: str
    class_beta: str
    coverage_alpha: float | None
    coverage_beta: float | None
    points: int


def _lincomb(a: tuple[float, float, float], sa: float, b: tuple[float, float, float], sb: float) -> tuple[float, float, float]:
    return normalize((sa * a[0] + sb * b[0], sa * a[1] + sb * b[1], sa * a[2] + sb * b[2]))


def with_tool_u_orientation(
    geometry: SpatialFourBarGeometry,
    *,
    phi_deg: float,
    axis_order: str = "ab",
) -> SpatialFourBarGeometry:
    """Rotate only the virtual tool-U frame in its own axis plane.

    All joint centers and all non-tool joint frames are unchanged.  ``axis_order``
    selects the ordered solver chart ``ab`` or ``ba`` for the same perpendicular
    axis lines.

    DIAGNOSTIC ONLY: this arbitrary reorientation is a sensitivity experiment.
    It is not a task-derived pointing-fiber parameter and must not be promoted
    into a dexterity atlas without separate geometric justification.
    """
    if axis_order not in {"ab", "ba"}:
        raise ValueError("axis_order must be 'ab' or 'ba'")

    tool_index = geometry.tool_joint
    tool = geometry.joints[tool_index]
    if len(tool.motion_axes) != 2:
        raise ValueError("tool joint must be U")
    x_axis, y_axis, z_axis = tool.frame
    phi = math.radians(phi_deg)
    c = math.cos(phi)
    s = math.sin(phi)
    a_axis = _lincomb(x_axis, c, y_axis, s)
    b_axis = _lincomb(x_axis, -s, y_axis, c)

    if axis_order == "ab":
        new_frame = (a_axis, b_axis, z_axis)
    else:
        # Keep a right-handed orthonormal frame while exposing motion axes in
        # reversed serial order through JointGeometry.motion_axes -> (x, y).
        new_frame = (b_axis, a_axis, scale(z_axis, -1.0))

    new_tool = JointGeometry(tool.name, tool.kind, tool.center, new_frame)
    joints = list(geometry.joints)
    joints[tool_index] = new_tool
    return replace(geometry, joints=tuple(joints))  # type: ignore[arg-type]


def _coverage(classification: WindingClassification) -> tuple[float | None, float | None]:
    two_pi = 2.0 * math.pi
    alpha = classification.tool_range_alpha
    beta = classification.tool_range_beta
    return (
        None if alpha is None else min(1.0, alpha / two_pi),
        None if beta is None else min(1.0, beta / two_pi),
    )


def _max_raw_increment(cycle: CycleTrace) -> float | None:
    if len(cycle.points) < 2:
        return None
    q = np.asarray([point.q for point in cycle.points], dtype=float)
    return float(np.max(np.abs(np.diff(q, axis=0))))


def _run_from_cycle(label: str, cycle: CycleTrace, step_size: float, direction: int) -> RobustnessRun:
    classification = classify_cycle(label, cycle)
    coverage_alpha, coverage_beta = _coverage(classification)
    return RobustnessRun(
        label=label,
        step_size=step_size,
        direction=direction,
        returned=cycle.returned,
        status=cycle.status,
        w_alpha=classification.w_alpha,
        w_beta=classification.w_beta,
        class_alpha=classification.class_alpha.value,
        class_beta=classification.class_beta.value,
        coverage_alpha=coverage_alpha,
        coverage_beta=coverage_beta,
        max_raw_increment=_max_raw_increment(cycle),
        points=len(cycle.points),
    )


def step_size_sweep(
    geometry: SpatialFourBarGeometry,
    *,
    step_sizes: Iterable[float] = (0.10, 0.05, 0.025),
    arclength_budget: float = 60.0,
) -> list[RobustnessRun]:
    results: list[RobustnessRun] = []
    for step_size in step_sizes:
        max_steps = max(2, math.ceil(arclength_budget / step_size))
        cycle = continue_until_return(
            geometry,
            step_size=step_size,
            max_steps=max_steps,
            direction=1,
        )
        results.append(_run_from_cycle(f"step_{step_size:g}", cycle, step_size, 1))
    return results


def direction_reversal_check(
    geometry: SpatialFourBarGeometry,
    *,
    step_size: float = 0.05,
    arclength_budget: float = 60.0,
) -> tuple[RobustnessRun, RobustnessRun]:
    max_steps = max(2, math.ceil(arclength_budget / step_size))
    positive = continue_until_return(
        geometry,
        step_size=step_size,
        max_steps=max_steps,
        direction=1,
    )
    negative = continue_until_return(
        geometry,
        step_size=step_size,
        max_steps=max_steps,
        direction=-1,
    )
    return (
        _run_from_cycle("direction_plus", positive, step_size, 1),
        _run_from_cycle("direction_minus", negative, step_size, -1),
    )


def orientation_sweep(
    geometry: SpatialFourBarGeometry,
    *,
    phi_degrees: Iterable[float] = tuple(range(0, 360, 30)),
    axis_order: str = "ab",
    step_size: float = 0.05,
    max_steps: int = 1600,
) -> list[OrientationSweepRun]:
    rows: list[OrientationSweepRun] = []
    for phi_deg in phi_degrees:
        variant = with_tool_u_orientation(geometry, phi_deg=float(phi_deg), axis_order=axis_order)
        audit = audit_reference_geometry(variant)
        classification = classify_geometry(
            variant,
            sample_id=f"uuur_phi_{float(phi_deg):07.2f}_{axis_order}",
            step_size=step_size,
            max_steps=max_steps,
        )
        coverage_alpha, coverage_beta = _coverage(classification)
        rows.append(
            OrientationSweepRun(
                phi_deg=float(phi_deg),
                axis_order=axis_order,
                audit_status=audit.status,
                jacobian_rank=audit.jacobian_rank,
                jacobian_nullity=audit.jacobian_nullity,
                returned=classification.cycle.returned,
                status=classification.cycle.status,
                w_alpha=classification.w_alpha,
                w_beta=classification.w_beta,
                class_alpha=classification.class_alpha.value,
                class_beta=classification.class_beta.value,
                coverage_alpha=coverage_alpha,
                coverage_beta=coverage_beta,
                points=len(classification.cycle.points),
            )
        )
    return rows


def _plot_step_sweep(rows: list[RobustnessRun], path: Path) -> None:
    xs = [row.step_size for row in rows]
    wa = [np.nan if row.w_alpha is None else row.w_alpha for row in rows]
    wb = [np.nan if row.w_beta is None else row.w_beta for row in rows]
    plt.figure(figsize=(7.5, 4.5))
    plt.plot(xs, wa, marker="o", label="w_alpha")
    plt.plot(xs, wb, marker="o", label="w_beta")
    plt.xlabel("Continuation step size")
    plt.ylabel("Returned-cycle winding")
    plt.title("V04B step-size winding convergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _plot_orientation_winding(rows: list[OrientationSweepRun], path: Path) -> None:
    xs = [row.phi_deg for row in rows]
    wa = [np.nan if row.w_alpha is None else row.w_alpha for row in rows]
    wb = [np.nan if row.w_beta is None else row.w_beta for row in rows]
    plt.figure(figsize=(8.5, 4.5))
    plt.plot(xs, wa, marker="o", label="w_alpha")
    plt.plot(xs, wb, marker="o", label="w_beta")
    plt.xlabel("Virtual tool-U in-plane orientation phi (deg)")
    plt.ylabel("Returned-cycle winding")
    plt.title(f"V04B virtual-U orientation sweep ({rows[0].axis_order if rows else 'n/a'} order)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _plot_orientation_coverage(rows: list[OrientationSweepRun], path: Path) -> None:
    xs = [row.phi_deg for row in rows]
    ca = [np.nan if row.coverage_alpha is None else row.coverage_alpha for row in rows]
    cb = [np.nan if row.coverage_beta is None else row.coverage_beta for row in rows]
    plt.figure(figsize=(8.5, 4.5))
    plt.plot(xs, ca, marker="o", label="alpha coverage")
    plt.plot(xs, cb, marker="o", label="beta coverage")
    plt.xlabel("Virtual tool-U in-plane orientation phi (deg)")
    plt.ylabel("Angular coverage fraction")
    plt.ylim(-0.05, 1.05)
    plt.title(f"V04B tool-coordinate coverage ({rows[0].axis_order if rows else 'n/a'} order)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _fmt(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _write_html(
    outdir: Path,
    *,
    step_rows: list[RobustnessRun],
    direction_rows: tuple[RobustnessRun, RobustnessRun],
    ab_rows: list[OrientationSweepRun],
    ba_rows: list[OrientationSweepRun],
) -> None:
    def robustness_table(rows: Iterable[RobustnessRun]) -> str:
        return "".join(
            "<tr>"
            f"<td>{row.label}</td><td>{row.step_size}</td><td>{row.direction}</td>"
            f"<td>{row.status}</td><td>{row.returned}</td><td>{_fmt(row.w_alpha)}</td>"
            f"<td>{_fmt(row.w_beta)}</td><td>{row.class_alpha}</td><td>{row.class_beta}</td>"
            f"<td>{_fmt(row.coverage_alpha)}</td><td>{_fmt(row.coverage_beta)}</td>"
            f"<td>{_fmt(row.max_raw_increment)}</td><td>{row.points}</td></tr>"
            for row in rows
        )

    def orientation_table(rows: Iterable[OrientationSweepRun]) -> str:
        return "".join(
            "<tr>"
            f"<td>{row.phi_deg:.1f}</td><td>{row.axis_order}</td><td>{row.audit_status}</td>"
            f"<td>{row.jacobian_rank}</td><td>{row.jacobian_nullity}</td><td>{row.status}</td>"
            f"<td>{_fmt(row.w_alpha)}</td><td>{_fmt(row.w_beta)}</td>"
            f"<td>{row.class_alpha}</td><td>{row.class_beta}</td>"
            f"<td>{_fmt(row.coverage_alpha)}</td><td>{_fmt(row.coverage_beta)}</td>"
            f"<td>{row.points}</td></tr>"
            for row in rows
        )

    plus, minus = direction_rows
    reversal_ok = (
        plus.returned
        and minus.returned
        and plus.w_alpha is not None
        and plus.w_beta is not None
        and minus.w_alpha == -plus.w_alpha
        and minus.w_beta == -plus.w_beta
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Sprint V04B — virtual-U robustness</title></head>
<body>
<h1>Sprint V04B — virtual-U robustness and orientation sweep</h1>
<p><strong>Purpose:</strong> validate V04 winding before V05 descriptor mining.</p>
<p><strong>DIAGNOSTIC ONLY:</strong> the <code>phi</code> sweep rotates an arbitrary
standalone virtual-U coordinate frame to test sensitivity.  It is not a
task-derived pointing-fiber sweep and <code>phi</code> is not a dexterity-atlas
parameter unless a later <code>S_v -&gt; U_v</code> construction proves that
interpretation.</p>
<p><code>tool_a</code> and <code>tool_b</code> are the two perpendicular revolute coordinates inside one virtual tool U. They are two classifications read from the same mechanism cycle, not two closure solves.</p>
<h2>Step-size convergence</h2>
<img src="figures/v04b_step_size_winding.png" alt="step-size winding convergence" style="max-width:850px;">
<table border="1" cellpadding="5"><tr><th>Run</th><th>ds</th><th>dir</th><th>Status</th><th>Returned</th><th>w_alpha</th><th>w_beta</th><th>class alpha</th><th>class beta</th><th>coverage alpha</th><th>coverage beta</th><th>max raw dq</th><th>points</th></tr>{robustness_table(step_rows)}</table>
<h2>Direction reversal</h2>
<p>Expected on the same returned branch: <code>W_minus = -W_plus</code>. Result: <strong>{'PASS' if reversal_ok else 'REVIEW'}</strong>.</p>
<table border="1" cellpadding="5"><tr><th>Run</th><th>ds</th><th>dir</th><th>Status</th><th>Returned</th><th>w_alpha</th><th>w_beta</th><th>class alpha</th><th>class beta</th><th>coverage alpha</th><th>coverage beta</th><th>max raw dq</th><th>points</th></tr>{robustness_table(direction_rows)}</table>
<h2>Controlled virtual-U orientation sweep — ab order</h2>
<img src="figures/v04b_orientation_winding_ab.png" alt="orientation winding ab" style="max-width:900px;">
<img src="figures/v04b_orientation_coverage_ab.png" alt="orientation coverage ab" style="max-width:900px;">
<table border="1" cellpadding="5"><tr><th>phi</th><th>order</th><th>audit</th><th>rank</th><th>nullity</th><th>Status</th><th>w_alpha</th><th>w_beta</th><th>class alpha</th><th>class beta</th><th>coverage alpha</th><th>coverage beta</th><th>points</th></tr>{orientation_table(ab_rows)}</table>
<h2>Tool-U axis-order comparison — ba order</h2>
<img src="figures/v04b_orientation_winding_ba.png" alt="orientation winding ba" style="max-width:900px;">
<img src="figures/v04b_orientation_coverage_ba.png" alt="orientation coverage ba" style="max-width:900px;">
<table border="1" cellpadding="5"><tr><th>phi</th><th>order</th><th>audit</th><th>rank</th><th>nullity</th><th>Status</th><th>w_alpha</th><th>w_beta</th><th>class alpha</th><th>class beta</th><th>coverage alpha</th><th>coverage beta</th><th>points</th></tr>{orientation_table(ba_rows)}</table>
<h2>Guardrail for V05</h2>
<p>Do not treat <code>phi</code> or axis order as dexterity-atlas parameters. Their observed sensitivity means the virtual-U convention must be derived from the pointing task/fiber before V05 uses the resulting UXXX mechanisms as dexterity evidence.</p>
</body></html>"""
    (outdir / "sprint_04b_virtual_u_robustness.html").write_text(html, encoding="utf-8")


def build_v04b_readout(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    figures = outdir / "figures"
    data = outdir / "data"
    figures.mkdir(exist_ok=True)
    data.mkdir(exist_ok=True)

    sample = generate_physical_geometry_samples(OrderedFamily.UUUR, count=1, seed=202)[0]
    geometry = sample.geometry
    step_rows = step_size_sweep(geometry)
    direction_rows = direction_reversal_check(geometry)
    ab_rows = orientation_sweep(geometry, axis_order="ab")
    ba_rows = orientation_sweep(geometry, axis_order="ba")

    payload = {
        "sample_id": sample.sample_id,
        "experiment_role": "diagnostic_sensitivity_only",
        "step_size_sweep": [asdict(row) for row in step_rows],
        "direction_reversal": [asdict(row) for row in direction_rows],
        "orientation_sweep_ab": [asdict(row) for row in ab_rows],
        "orientation_sweep_ba": [asdict(row) for row in ba_rows],
    }
    (data / "v04b_virtual_u_robustness.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    _plot_step_sweep(step_rows, figures / "v04b_step_size_winding.png")
    _plot_orientation_winding(ab_rows, figures / "v04b_orientation_winding_ab.png")
    _plot_orientation_coverage(ab_rows, figures / "v04b_orientation_coverage_ab.png")
    _plot_orientation_winding(ba_rows, figures / "v04b_orientation_winding_ba.png")
    _plot_orientation_coverage(ba_rows, figures / "v04b_orientation_coverage_ba.png")
    _write_html(
        outdir,
        step_rows=step_rows,
        direction_rows=direction_rows,
        ab_rows=ab_rows,
        ba_rows=ba_rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build V04B virtual-U robustness readout.")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/spatial4bar_explorer/v04b"),
    )
    args = parser.parse_args()
    build_v04b_readout(args.outdir)


if __name__ == "__main__":
    main()
