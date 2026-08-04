"""Generate Sprint 2–3 visualizations and write type-map artifacts (reproducible)."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.classification.predictors import (
    architecture_a_type_map,
    write_type_map_csv,
    write_type_map_json,
)
from sixr_grashof.visualization import (
    plot_exact_vs_offset_reduction,
    plot_hand_link_sensitivity,
    plot_linkage_type_map,
    plot_prediction_card,
    plot_regional_reduction_panel,
    plot_spherical_reduction_panel,
)

ROOT = Path(__file__).resolve().parents[1]
OUT2 = ROOT / "results" / "sprint02_reduction"
OUT3 = ROOT / "results" / "sprint03_prediction"


def generate_sprint2(out: Path = OUT2) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for fn, name in (
        (plot_regional_reduction_panel, "regional_planar_reduction.png"),
        (plot_spherical_reduction_panel, "spherical_orientation_reduction.png"),
        (plot_exact_vs_offset_reduction, "exact_A_vs_offset_B.png"),
    ):
        p = fn(output=out / name)
        assert p is not None
        paths.append(p)
    return paths


def generate_sprint3(out: Path = OUT3) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    rows = architecture_a_type_map(n_radial=14, n_elbow=10)
    csv_path = write_type_map_csv(rows, out / "architecture_a_type_map.csv")
    json_path = write_type_map_json(rows, out / "architecture_a_type_map.json")
    paths.extend([csv_path, json_path])

    p = plot_linkage_type_map(rows, output=out / "linkage_type_map.png")
    assert p is not None
    paths.append(p)
    p = plot_prediction_card(output=out / "prediction_card.png")
    assert p is not None
    paths.append(p)
    p = plot_hand_link_sensitivity(output=out / "hand_link_sensitivity.png")
    assert p is not None
    paths.append(p)
    return paths


def main() -> None:
    p2 = generate_sprint2()
    p3 = generate_sprint3()
    from sixr_grashof.dashboard import generate_dashboards

    dash = generate_dashboards(results_root=ROOT / "results")
    print(f"Sprint 2: {len(p2)} artifacts under {OUT2}")
    print(f"Sprint 3: {len(p3)} artifacts under {OUT3}")
    for p in p2 + p3:
        print(f"  {p.relative_to(ROOT)}")
    print("Dashboards:")
    for key, path in dash.items():
        print(f"  {key}: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
