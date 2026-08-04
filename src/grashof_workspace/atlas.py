"""Link-ratio atlas for planar 3R dexterous workspaces."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import isclose
from pathlib import Path

from .planar3r import FULL_COVERAGE, Planar3R
from .plotting import plot_workspace

EXPERIMENT_MATRIX: tuple[tuple[str, float, float, float], ...] = (
    ("equal_proximal", 2.0, 2.0, 1.0),
    ("long_terminal", 1.0, 1.0, 3.0),
    ("unequal_proximal", 3.0, 1.0, 2.5),
    ("boundary_degenerate", 3.0, 2.0, 2.0),
    ("disk_and_annulus", 3.0, 2.0, 1.5),
    ("annulus", 3.0, 2.0, 0.5),
)


@dataclass(frozen=True, slots=True)
class AtlasRow:
    lambda2: float
    lambda3: float
    topology: str
    intervals: str
    boundary_radii: str
    boundary_grashof_margins: str
    sampled_validation: str
    family: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "lambda2": f"{self.lambda2:.6g}",
            "lambda3": f"{self.lambda3:.6g}",
            "topology": self.topology,
            "intervals": self.intervals,
            "boundary_radii": self.boundary_radii,
            "boundary_grashof_margins": self.boundary_grashof_margins,
            "sampled_validation": self.sampled_validation,
            "family": self.family,
        }


def _format_intervals(intervals: tuple[tuple[float, float], ...]) -> str:
    if not intervals:
        return ""
    return ";".join(f"[{inner:g},{outer:g}]" for inner, outer in intervals)


def _boundary_radii(intervals: tuple[tuple[float, float], ...]) -> list[float]:
    radii: list[float] = []
    for inner, outer in intervals:
        radii.append(inner)
        if outer != inner:
            radii.append(outer)
    return radii


def validate_robot_sampling(
    robot: Planar3R,
    *,
    samples: int = 360,
) -> str:
    """Return ``pass`` if analytical dexterity matches orientation sampling."""
    reachable_inner, reachable_outer = robot.reachable_radial_interval()
    probes = {
        reachable_inner,
        reachable_outer,
        0.5 * (reachable_inner + reachable_outer),
    }
    for inner, outer in robot.dexterous_radial_intervals():
        probes.add(inner)
        probes.add(outer)
        probes.add(0.5 * (inner + outer))

    for rho in sorted(probes):
        if rho < 0.0:
            continue
        analytical = robot.is_dexterous_radius(rho)
        coverage = robot.sampled_orientation_coverage(rho, 0.0, samples=samples)
        sampled_full = isclose(coverage, FULL_COVERAGE)
        if analytical != sampled_full:
            return f"fail@rho={rho:g}"
    return "pass"


def build_atlas_row(
    lambda2: float,
    lambda3: float,
    *,
    family: str = "",
    samples: int = 360,
) -> AtlasRow:
    robot = Planar3R(1.0, lambda2, lambda3)
    intervals = robot.dexterous_radial_intervals()
    boundaries = _boundary_radii(intervals)
    margins = [robot.fourbar_at_radius(rho).grashof_margin for rho in boundaries]
    return AtlasRow(
        lambda2=lambda2,
        lambda3=lambda3,
        topology=robot.dexterous_topology(),
        intervals=_format_intervals(intervals),
        boundary_radii=";".join(f"{rho:g}" for rho in boundaries),
        boundary_grashof_margins=";".join(f"{margin:.6g}" for margin in margins),
        sampled_validation=validate_robot_sampling(robot, samples=samples),
        family=family,
    )


def generate_atlas(
    output_dir: str | Path,
    *,
    lambda2_values: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0),
    lambda3_values: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5),
    samples: int = 360,
) -> Path:
    """Write CSV atlas and named-family figures under ``output_dir``."""
    out = Path(output_dir)
    figures = out / "figures"
    out.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    rows: list[AtlasRow] = []
    for lambda2 in lambda2_values:
        for lambda3 in lambda3_values:
            rows.append(build_atlas_row(lambda2, lambda3, samples=samples))

    for family, l1, l2, l3 in EXPERIMENT_MATRIX:
        lambda2 = l2 / l1
        lambda3 = l3 / l1
        rows.append(
            build_atlas_row(
                lambda2,
                lambda3,
                family=family,
                samples=samples,
            )
        )
        robot = Planar3R(l1, l2, l3)
        plot_workspace(
            robot,
            figures / f"{family}.png",
            title=f"{family}: l=({l1:g},{l2:g},{l3:g})",
        )

    csv_path = out / "atlas.csv"
    fieldnames = [
        "lambda2",
        "lambda3",
        "topology",
        "intervals",
        "boundary_radii",
        "boundary_grashof_margins",
        "sampled_validation",
        "family",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())

    return csv_path
