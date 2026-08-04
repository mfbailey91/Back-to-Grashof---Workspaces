"""Reproducibility of geometry reports / plots."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.architectures import ArchitectureA, ArchitectureB, ArchitectureParams
from sixr_grashof.cli import main
from sixr_grashof.visualization import format_geometry_report, plot_robot_axes


def test_geometry_report_stable() -> None:
    a = ArchitectureA().geometry_report()
    b = ArchitectureA().geometry_report()
    assert format_geometry_report(a) == format_geometry_report(b)


def test_cli_writes_report_and_plot(tmp_path: Path) -> None:
    report = tmp_path / "report.txt"
    png = tmp_path / "arch_a.png"
    main(
        [
            "--architecture",
            "A",
            "--report",
            str(report),
            "--output",
            str(png),
        ]
    )
    assert report.is_file()
    assert "spherical_status: exact" in report.read_text(encoding="utf-8")
    assert png.is_file()


def test_plot_offset_architecture(tmp_path: Path) -> None:
    arch = ArchitectureB(ArchitectureParams(epsilon_w=0.1))
    fk = arch.forward((0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    report = arch.geometry_report()
    out = plot_robot_axes(fk, report, output=tmp_path / "b.png")
    assert out is not None
    assert out.is_file()
