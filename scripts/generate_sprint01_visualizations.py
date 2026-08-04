"""Generate all Sprint 0–1 visualizations (reproducible)."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.classification import SphericalFourBar, fixtures
from sixr_grashof.visualization import (
    format_geometry_report,
    plot_architecture_a_worked_closure,
    plot_architecture_panel,
    plot_residual_sweeps,
    plot_robot_axes,
    plot_sign_type_table,
    plot_spherical_fourbar,
    plot_type_fixture_gallery,
)

ROOT = Path(__file__).resolve().parents[1]
OUT0 = ROOT / "results" / "sprint00_classification"
OUT1 = ROOT / "results" / "sprint01_geometry"


def _geometry_dump(arch_name: str, arch, ew: float = 0.0, es: float = 0.0) -> None:  # type: ignore[no-untyped-def]
    q = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    fk = arch.forward(q)
    report = arch.geometry_report(q)
    stem = f"arch_{arch_name}_ew{ew:g}_es{es:g}"
    plot_robot_axes(fk, report, output=OUT1 / f"{stem}.png")
    (OUT1 / f"{stem}.txt").write_text(format_geometry_report(report) + "\n", encoding="utf-8")


def generate_sprint0(out: Path = OUT0) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    p = plot_architecture_a_worked_closure(output=out / "arch_a_worked_spherical_closure.png")
    assert p is not None
    paths.append(p)

    p = plot_type_fixture_gallery(output=out / "mccarthy_soh_T_gallery.png")
    assert p is not None
    paths.append(p)

    p = plot_sign_type_table(output=out / "mccarthy_soh_type_table.png")
    assert p is not None
    paths.append(p)

    # One sphere plot for each basic motion class (types 1–4) plus wrap type 10.
    wanted = {1, 2, 3, 4, 10}
    for row in fixtures():
        t = int(row["type"])  # type: ignore[arg-type]
        if t not in wanted:
            continue
        linkage = SphericalFourBar(
            float(row["alpha"]),  # type: ignore[arg-type]
            float(row["beta"]),  # type: ignore[arg-type]
            float(row["gamma"]),  # type: ignore[arg-type]
            float(row["eta"]),  # type: ignore[arg-type]
        )
        from sixr_grashof.classification import classify_spherical

        result = classify_spherical(linkage)
        p = plot_spherical_fourbar(
            linkage,
            output=out / f"spherical_fourbar_type{t}.png",
            title=f"Fixture type {t}: {result.linkage_name}",
        )
        assert p is not None
        paths.append(p)
    return paths


def generate_sprint1(out: Path = OUT1) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    _geometry_dump("A", ArchitectureA())
    paths.append(out / "arch_A_ew0_es0.png")
    for ew in (0.0, 0.05, 0.20):
        _geometry_dump("B", ArchitectureB(ArchitectureParams(epsilon_w=ew)), ew=ew)
        paths.append(out / f"arch_B_ew{ew:g}_es0.png")
    for es in (0.0, 0.05, 0.20):
        _geometry_dump("C", ArchitectureC(ArchitectureParams(epsilon_s=es)), es=es)
        paths.append(out / f"arch_C_ew0_es{es:g}.png")

    p = plot_architecture_panel(output=out / "architecture_panel.png")
    assert p is not None
    paths.append(p)
    p = plot_residual_sweeps(output=out / "residual_sweeps.png")
    assert p is not None
    paths.append(p)
    return paths


def main() -> None:
    p0 = generate_sprint0()
    p1 = generate_sprint1()
    from sixr_grashof.dashboard import generate_dashboards

    dash = generate_dashboards(results_root=ROOT / "results")
    print(f"Sprint 0: {len(p0)} figures under {OUT0}")
    print(f"Sprint 1: {len(p1)} figures under {OUT1}")
    for p in p0 + p1:
        print(f"  {p.relative_to(ROOT)}")
    print("Dashboards:")
    for key, path in dash.items():
        print(f"  {key}: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
