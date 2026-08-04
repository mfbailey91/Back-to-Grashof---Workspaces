"""Generate Sprint 1 axis-geometry figures for architectures A/B/C."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.visualization import (
    format_geometry_report,
    plot_architecture_panel,
    plot_residual_sweeps,
    plot_robot_axes,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "sprint01_geometry"


def _dump(arch_name: str, arch, ew: float = 0.0, es: float = 0.0) -> None:  # type: ignore[no-untyped-def]
    q = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    fk = arch.forward(q)
    report = arch.geometry_report(q)
    stem = f"arch_{arch_name}_ew{ew:g}_es{es:g}"
    plot_robot_axes(fk, report, output=OUT / f"{stem}.png")
    (OUT / f"{stem}.txt").write_text(format_geometry_report(report) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _dump("A", ArchitectureA())
    for ew in (0.0, 0.05, 0.20):
        _dump("B", ArchitectureB(ArchitectureParams(epsilon_w=ew)), ew=ew)
    for es in (0.0, 0.05, 0.20):
        _dump("C", ArchitectureC(ArchitectureParams(epsilon_s=es)), es=es)
    plot_architecture_panel(output=OUT / "architecture_panel.png")
    plot_residual_sweeps(output=OUT / "residual_sweeps.png")
    print(f"Wrote geometry artifacts under {OUT}")


if __name__ == "__main__":
    main()
