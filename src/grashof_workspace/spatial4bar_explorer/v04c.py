from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .closure import audit_reference_geometry
from .geometry import SpatialFourBarGeometry
from .geometry_descriptors import generate_physical_geometry_samples
from .models import BranchClass, OrderedFamily
from .v04b import OrientationSweepRun, orientation_sweep, with_tool_u_orientation
from .winding import classify_geometry


@dataclass(frozen=True)
class AxisOrderSymmetryRow:
    ba_phi_deg: float
    matched_ab_phi_deg: float
    status_match: bool
    class_match: bool
    winding_match: bool
    coverage_match: bool
    passed: bool


@dataclass(frozen=True)
class HalfTurnPeriodicityRow:
    phi_deg: float
    matched_phi_deg: float
    status_match: bool
    class_match: bool
    winding_magnitude_match: bool
    coverage_match: bool
    passed: bool


@dataclass(frozen=True)
class BudgetResolutionRun:
    phi_deg: float
    axis_order: str
    max_steps: int
    returned: bool
    status: str
    w_alpha: int | None
    w_beta: int | None
    class_alpha: str
    class_beta: str
    points: int


@dataclass(frozen=True)
class TransitionProbe:
    phi_deg: float
    audit_status: str
    status: str
    returned: bool
    w_alpha: int | None
    w_beta: int | None
    class_alpha: str
    class_beta: str
    coverage_alpha: float | None
    coverage_beta: float | None
    min_singular_value: float | None
    points: int


def _phi_key(phi_deg: float) -> float:
    value = float(phi_deg) % 360.0
    if math.isclose(value, 360.0, abs_tol=1e-9):
        value = 0.0
    return round(value, 9)


def _close_optional(a: float | None, b: float | None, *, atol: float) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, abs_tol=atol, rel_tol=0.0)


def compare_axis_order_symmetry(
    ab_rows: Sequence[OrientationSweepRun],
    ba_rows: Sequence[OrientationSweepRun],
    *,
    shift_deg: float = 90.0,
    coverage_tol: float = 5e-3,
) -> list[AxisOrderSymmetryRow]:
    """Compare BA(phi) with shifted AB(phi + 90 deg).

    The tested coordinate convention predicts equal alpha winding, opposite beta
    winding, equal crank/rocker classes, and equal angular coverage.
    """
    ab_by_phi = {_phi_key(row.phi_deg): row for row in ab_rows}
    comparisons: list[AxisOrderSymmetryRow] = []
    for ba in ba_rows:
        matched_phi = _phi_key(ba.phi_deg + shift_deg)
        if matched_phi not in ab_by_phi:
            raise ValueError(f"missing AB comparison row at phi={matched_phi}")
        ab = ab_by_phi[matched_phi]
        status_match = ba.status == ab.status and ba.returned == ab.returned
        class_match = ba.class_alpha == ab.class_alpha and ba.class_beta == ab.class_beta
        winding_match = (
            ba.w_alpha == ab.w_alpha
            and (
                (ba.w_beta is None and ab.w_beta is None)
                or (
                    ba.w_beta is not None
                    and ab.w_beta is not None
                    and ba.w_beta == -ab.w_beta
                )
            )
        )
        coverage_match = _close_optional(
            ba.coverage_alpha, ab.coverage_alpha, atol=coverage_tol
        ) and _close_optional(ba.coverage_beta, ab.coverage_beta, atol=coverage_tol)
        passed = status_match and class_match and winding_match and coverage_match
        comparisons.append(
            AxisOrderSymmetryRow(
                ba_phi_deg=ba.phi_deg,
                matched_ab_phi_deg=matched_phi,
                status_match=status_match,
                class_match=class_match,
                winding_match=winding_match,
                coverage_match=coverage_match,
                passed=passed,
            )
        )
    return comparisons


def compare_half_turn_periodicity(
    ab_rows: Sequence[OrientationSweepRun],
    *,
    coverage_tol: float = 5e-3,
) -> list[HalfTurnPeriodicityRow]:
    """Compare AB(phi) with AB(phi + 180 deg) using invariant labels/magnitudes."""
    by_phi = {_phi_key(row.phi_deg): row for row in ab_rows}
    comparisons: list[HalfTurnPeriodicityRow] = []
    base_phis = sorted(phi for phi in by_phi if phi < 180.0)
    for phi in base_phis:
        matched_phi = _phi_key(phi + 180.0)
        if matched_phi not in by_phi:
            raise ValueError(f"missing half-turn comparison row at phi={matched_phi}")
        a = by_phi[phi]
        b = by_phi[matched_phi]
        status_match = a.status == b.status and a.returned == b.returned
        class_match = a.class_alpha == b.class_alpha and a.class_beta == b.class_beta
        winding_magnitude_match = (
            (a.w_alpha is None and b.w_alpha is None)
            or (
                a.w_alpha is not None
                and b.w_alpha is not None
                and abs(a.w_alpha) == abs(b.w_alpha)
            )
        ) and (
            (a.w_beta is None and b.w_beta is None)
            or (
                a.w_beta is not None
                and b.w_beta is not None
                and abs(a.w_beta) == abs(b.w_beta)
            )
        )
        coverage_match = _close_optional(
            a.coverage_alpha, b.coverage_alpha, atol=coverage_tol
        ) and _close_optional(a.coverage_beta, b.coverage_beta, atol=coverage_tol)
        passed = status_match and class_match and winding_magnitude_match and coverage_match
        comparisons.append(
            HalfTurnPeriodicityRow(
                phi_deg=phi,
                matched_phi_deg=matched_phi,
                status_match=status_match,
                class_match=class_match,
                winding_magnitude_match=winding_magnitude_match,
                coverage_match=coverage_match,
                passed=passed,
            )
        )
    return comparisons


def resolve_budget_limited_orientation(
    geometry: SpatialFourBarGeometry,
    *,
    phi_deg: float,
    axis_order: str = "ab",
    max_steps_budgets: Iterable[int] = (1600, 3200, 6400),
    step_size: float = 0.05,
) -> list[BudgetResolutionRun]:
    rows: list[BudgetResolutionRun] = []
    for max_steps in max_steps_budgets:
        result = orientation_sweep(
            geometry,
            phi_degrees=(phi_deg,),
            axis_order=axis_order,
            step_size=step_size,
            max_steps=max_steps,
        )[0]
        rows.append(
            BudgetResolutionRun(
                phi_deg=phi_deg,
                axis_order=axis_order,
                max_steps=max_steps,
                returned=result.returned,
                status=result.status,
                w_alpha=result.w_alpha,
                w_beta=result.w_beta,
                class_alpha=result.class_alpha,
                class_beta=result.class_beta,
                points=result.points,
            )
        )
        if result.returned or result.status not in {"open_branch"}:
            break
    return rows


def budget_resolution_label(rows: Sequence[BudgetResolutionRun]) -> str:
    if not rows:
        return "not_run"
    first = rows[0]
    final = rows[-1]
    if first.status == "open_branch" and final.returned:
        return "budget_limited_return"
    if final.status == "open_branch":
        return "persistent_open_within_tested_budget"
    return final.status


def _coverage_from_range(value: float | None) -> float | None:
    if value is None:
        return None
    return min(1.0, value / (2.0 * math.pi))


def transition_probe(
    geometry: SpatialFourBarGeometry,
    *,
    phi_deg: float,
    step_size: float = 0.05,
    max_steps: int = 2400,
) -> TransitionProbe:
    variant = with_tool_u_orientation(geometry, phi_deg=phi_deg, axis_order="ab")
    audit = audit_reference_geometry(variant)
    classification = classify_geometry(
        variant,
        sample_id=f"uuur_v04c_phi_{phi_deg:07.2f}",
        step_size=step_size,
        max_steps=max_steps,
    )
    singular_values = [
        point.smallest_singular_value
        for point in classification.cycle.points
        if point.converged and point.smallest_singular_value > 0.0
    ]
    return TransitionProbe(
        phi_deg=phi_deg,
        audit_status=audit.status,
        status=classification.cycle.status,
        returned=classification.cycle.returned,
        w_alpha=classification.w_alpha,
        w_beta=classification.w_beta,
        class_alpha=classification.class_alpha.value,
        class_beta=classification.class_beta.value,
        coverage_alpha=_coverage_from_range(classification.tool_range_alpha),
        coverage_beta=_coverage_from_range(classification.tool_range_beta),
        min_singular_value=min(singular_values) if singular_values else None,
        points=len(classification.cycle.points),
    )


def _state_signature(row: OrientationSweepRun) -> tuple[str, str, str]:
    return (row.status, row.class_alpha, row.class_beta)


def transition_intervals(
    coarse_rows: Sequence[OrientationSweepRun],
    *,
    domain_end_deg: float = 180.0,
) -> list[tuple[float, float]]:
    rows = sorted(
        (row for row in coarse_rows if 0.0 <= row.phi_deg <= domain_end_deg),
        key=lambda row: row.phi_deg,
    )
    intervals: list[tuple[float, float]] = []
    for left, right in pairwise(rows):
        if _state_signature(left) != _state_signature(right):
            intervals.append((left.phi_deg, right.phi_deg))
    return intervals


def dense_transition_sweep(
    geometry: SpatialFourBarGeometry,
    coarse_rows: Sequence[OrientationSweepRun],
    *,
    dense_step_deg: float = 5.0,
    max_steps: int = 2400,
) -> tuple[list[tuple[float, float]], list[TransitionProbe]]:
    intervals = transition_intervals(coarse_rows)
    phi_values: set[float] = set()
    for start, stop in intervals:
        count = max(1, math.ceil((stop - start) / dense_step_deg))
        for value in np.linspace(start, stop, count + 1):
            phi_values.add(round(float(value), 9))
    probes = [
        transition_probe(geometry, phi_deg=phi, max_steps=max_steps)
        for phi in sorted(phi_values)
    ]
    return intervals, probes


def _state_code(row: TransitionProbe) -> int:
    if row.status == "open_branch":
        return -1
    if row.status == "change_point":
        return -2
    if row.status == "invalid":
        return -3
    crank_a = row.class_alpha == BranchClass.CRANK.value
    crank_b = row.class_beta == BranchClass.CRANK.value
    if crank_a and crank_b:
        return 3
    if crank_a:
        return 1
    if crank_b:
        return 2
    return 0


def _plot_symmetry(rows: Sequence[AxisOrderSymmetryRow], path: Path) -> None:
    xs = [row.ba_phi_deg for row in rows]
    ys = [1 if row.passed else 0 for row in rows]
    plt.figure(figsize=(8.0, 4.0))
    plt.step(xs, ys, where="mid")
    plt.scatter(xs, ys)
    plt.yticks([0, 1], ["REVIEW", "PASS"])
    plt.ylim(-0.2, 1.2)
    plt.xlabel("BA orientation phi (deg)")
    plt.title("V04C BA(phi) vs shifted AB(phi + 90 deg)")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _plot_transition_state(rows: Sequence[TransitionProbe], path: Path) -> None:
    xs = [row.phi_deg for row in rows]
    ys = [_state_code(row) for row in rows]
    plt.figure(figsize=(9.0, 4.5))
    plt.plot(xs, ys, marker="o")
    plt.yticks(
        [-3, -2, -1, 0, 1, 2, 3],
        ["invalid", "change", "open", "rock/rock", "crank a", "crank b", "both"],
    )
    plt.xlabel("Canonical tool-U orientation phi (deg)")
    plt.ylabel("Returned-cycle state")
    plt.title("V04C dense transition map")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _plot_transition_margin(rows: Sequence[TransitionProbe], path: Path) -> None:
    xs = [row.phi_deg for row in rows]
    ys = [np.nan if row.min_singular_value is None else row.min_singular_value for row in rows]
    plt.figure(figsize=(9.0, 4.5))
    plt.plot(xs, ys, marker="o")
    plt.xlabel("Canonical tool-U orientation phi (deg)")
    plt.ylabel("Minimum nonzero closure-Jacobian singular value")
    plt.title("V04C transition singularity margin")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _fmt(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _write_html(
    outdir: Path,
    *,
    symmetry_rows: Sequence[AxisOrderSymmetryRow],
    periodicity_rows: Sequence[HalfTurnPeriodicityRow],
    budget_runs: Mapping[str, Sequence[BudgetResolutionRun]],
    intervals: Sequence[tuple[float, float]],
    transition_rows: Sequence[TransitionProbe],
) -> None:
    symmetry_pass = bool(symmetry_rows) and all(row.passed for row in symmetry_rows)
    periodicity_pass = bool(periodicity_rows) and all(row.passed for row in periodicity_rows)
    axis_decision = "provisionally canonicalize to ab" if symmetry_pass else "retain axis_order"
    phi_decision = (
        "provisionally reduce phi modulo 180 deg"
        if periodicity_pass
        else "retain 0..360 deg"
    )

    symmetry_table = "".join(
        "<tr>"
        f"<td>{row.ba_phi_deg:.1f}</td><td>{row.matched_ab_phi_deg:.1f}</td>"
        f"<td>{row.status_match}</td><td>{row.class_match}</td>"
        f"<td>{row.winding_match}</td><td>{row.coverage_match}</td>"
        f"<td>{'PASS' if row.passed else 'REVIEW'}</td></tr>"
        for row in symmetry_rows
    )
    periodicity_table = "".join(
        "<tr>"
        f"<td>{row.phi_deg:.1f}</td><td>{row.matched_phi_deg:.1f}</td>"
        f"<td>{row.status_match}</td><td>{row.class_match}</td>"
        f"<td>{row.winding_magnitude_match}</td><td>{row.coverage_match}</td>"
        f"<td>{'PASS' if row.passed else 'REVIEW'}</td></tr>"
        for row in periodicity_rows
    )
    budget_sections = []
    for label, rows in budget_runs.items():
        table = "".join(
            "<tr>"
            f"<td>{row.max_steps}</td><td>{row.status}</td><td>{row.returned}</td>"
            f"<td>{_fmt(row.w_alpha)}</td><td>{_fmt(row.w_beta)}</td>"
            f"<td>{row.class_alpha}</td><td>{row.class_beta}</td><td>{row.points}</td></tr>"
            for row in rows
        )
        budget_sections.append(
            f"<h3>{label}: {budget_resolution_label(rows)}</h3>"
            "<table border='1' cellpadding='5'><tr><th>max steps</th><th>status</th>"
            "<th>returned</th><th>w alpha</th><th>w beta</th><th>class alpha</th>"
            f"<th>class beta</th><th>points</th></tr>{table}</table>"
        )
    transition_table = "".join(
        "<tr>"
        f"<td>{row.phi_deg:.1f}</td><td>{row.status}</td><td>{_fmt(row.w_alpha)}</td>"
        f"<td>{_fmt(row.w_beta)}</td><td>{row.class_alpha}</td><td>{row.class_beta}</td>"
        f"<td>{_fmt(row.coverage_alpha)}</td><td>{_fmt(row.coverage_beta)}</td>"
        f"<td>{_fmt(row.min_singular_value)}</td><td>{row.points}</td></tr>"
        for row in transition_rows
    )
    interval_text = ", ".join(f"[{a:.1f}, {b:.1f}]" for a, b in intervals) or "none"
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Sprint V04C — virtual-U equivalence</title></head>
<body>
<h1>Sprint V04C — virtual-U equivalence and fiber interpretation</h1>
<p><strong>Purpose:</strong> decide which virtual-U parameters must survive into V05.</p>
<h2>Provisional canonicalization decision</h2>
<ul>
<li>Axis order: <strong>{axis_decision}</strong>.</li>
<li>Orientation domain: <strong>{phi_decision}</strong>.</li>
<li>These decisions apply only to the tested canonical UUUR geometry until repeated
 on a broader corpus.</li>
</ul>
<h2>AB / BA shifted symmetry</h2>
<p>Tested hypothesis: <code>BA(phi) ~ AB(phi + 90 deg)</code>, with beta winding sign reversal.</p>
<img src="figures/v04c_axis_order_symmetry.png" alt="axis-order symmetry" style="max-width:850px;">
<table border="1" cellpadding="5"><tr><th>BA phi</th><th>AB phi</th>
<th>status</th><th>classes</th><th>winding</th><th>coverage</th><th>result</th></tr>
{symmetry_table}</table>
<h2>Half-turn periodicity</h2>
<p>Tested hypothesis: <code>AB(phi) ~ AB(phi + 180 deg)</code> in status, classes,
 winding magnitude, and coverage.</p>
<table border="1" cellpadding="5"><tr><th>phi</th><th>phi+180</th><th>status</th>
<th>classes</th><th>|W|</th><th>coverage</th><th>result</th></tr>
{periodicity_table}</table>
<h2>Budget-limited open cases</h2>
{''.join(budget_sections)}
<h2>Adaptive transition sweep</h2>
<p>Coarse state changes triggered dense probing in: <code>{interval_text}</code>.</p>
<img src="figures/v04c_transition_state.png" alt="transition state" style="max-width:950px;">
<img src="figures/v04c_transition_singularity_margin.png"
 alt="transition singularity margin" style="max-width:950px;">
<table border="1" cellpadding="5"><tr><th>phi</th><th>status</th><th>w alpha</th>
<th>w beta</th><th>class alpha</th><th>class beta</th><th>coverage alpha</th>
<th>coverage beta</th><th>min sigma</th><th>points</th></tr>
{transition_table}</table>
<h2>Guardrail for V05</h2>
<p>Do not fit Grashof-like descriptor rules until the retained virtual-U parameters
 from this readout are included in the atlas key. Any canonicalization here remains
 provisional until repeated across multiple physical geometries.</p>
</body></html>"""
    (outdir / "sprint_04c_virtual_u_equivalence.html").write_text(html, encoding="utf-8")


def build_v04c_readout(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    figures = outdir / "figures"
    data = outdir / "data"
    figures.mkdir(exist_ok=True)
    data.mkdir(exist_ok=True)

    sample = generate_physical_geometry_samples(OrderedFamily.UUUR, count=1, seed=202)[0]
    geometry = sample.geometry
    phis = tuple(float(value) for value in range(0, 360, 30))
    ab_rows = orientation_sweep(geometry, phi_degrees=phis, axis_order="ab")
    ba_rows = orientation_sweep(geometry, phi_degrees=phis, axis_order="ba")

    symmetry_rows = compare_axis_order_symmetry(ab_rows, ba_rows)
    periodicity_rows = compare_half_turn_periodicity(ab_rows)
    budget_runs = {
        "ab_phi_120": resolve_budget_limited_orientation(geometry, phi_deg=120.0),
        "ab_phi_300": resolve_budget_limited_orientation(geometry, phi_deg=300.0),
    }

    coarse_half_domain = orientation_sweep(
        geometry,
        phi_degrees=tuple(float(value) for value in range(0, 181, 30)),
        axis_order="ab",
        max_steps=2400,
    )
    intervals, transition_rows = dense_transition_sweep(geometry, coarse_half_domain)

    axis_order_equivalent = bool(symmetry_rows) and all(row.passed for row in symmetry_rows)
    half_turn_periodic = bool(periodicity_rows) and all(row.passed for row in periodicity_rows)
    payload = {
        "sample_id": sample.sample_id,
        "axis_order_shift_deg": 90.0,
        "axis_order_equivalent_on_tested_geometry": axis_order_equivalent,
        "half_turn_periodic_on_tested_geometry": half_turn_periodic,
        "provisional_axis_order_decision": (
            "canonicalize_to_ab" if axis_order_equivalent else "retain_axis_order"
        ),
        "provisional_phi_domain": "[0,180)" if half_turn_periodic else "[0,360)",
        "axis_order_symmetry": [asdict(row) for row in symmetry_rows],
        "half_turn_periodicity": [asdict(row) for row in periodicity_rows],
        "budget_resolution": {
            label: {
                "resolution": budget_resolution_label(rows),
                "runs": [asdict(row) for row in rows],
            }
            for label, rows in budget_runs.items()
        },
        "transition_intervals": intervals,
        "transition_probes": [asdict(row) for row in transition_rows],
        "guardrail": (
            "Canonicalization is provisional for canonical UUUR only; repeat across the "
            "physical geometry corpus before removing dimensions globally."
        ),
    }
    (data / "v04c_virtual_u_equivalence.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    _plot_symmetry(symmetry_rows, figures / "v04c_axis_order_symmetry.png")
    _plot_transition_state(transition_rows, figures / "v04c_transition_state.png")
    _plot_transition_margin(transition_rows, figures / "v04c_transition_singularity_margin.png")
    _write_html(
        outdir,
        symmetry_rows=symmetry_rows,
        periodicity_rows=periodicity_rows,
        budget_runs=budget_runs,
        intervals=intervals,
        transition_rows=transition_rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build V04C virtual-U equivalence readout.")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/spatial4bar_explorer/v04c"),
    )
    args = parser.parse_args()
    build_v04c_readout(args.outdir)


if __name__ == "__main__":
    main()
