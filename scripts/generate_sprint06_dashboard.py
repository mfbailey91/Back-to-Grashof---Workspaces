"""Generate Sprint 6 interactive inspector dashboard (reproducible)."""

from __future__ import annotations

from pathlib import Path

from sixr_grashof.dashboard import generate_dashboards, write_sprint6_dashboard

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main() -> None:
    index = write_sprint6_dashboard(
        RESULTS / "sprint06_dashboard",
        experiments_src=RESULTS / "sprint05_experiments",
        geometry_src=RESULTS / "sprint01_geometry",
        reduction_src=RESULTS / "sprint02_reduction",
        orientation_src=RESULTS / "sprint04_orientation",
    )
    print(f"sprint6: {index.relative_to(ROOT)}")
    # Refresh overview + sibling dashboards so nav links stay consistent.
    dash = generate_dashboards(results_root=RESULTS)
    for key, path in dash.items():
        print(f"{key}: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
