from pathlib import Path

from grashof_workspace.atlas import build_atlas_row, generate_atlas
from grashof_workspace.planar3r import Planar3R


def test_build_atlas_row_for_equal_proximal_links() -> None:
    row = build_atlas_row(1.0, 0.5)
    assert row.topology == "disk"
    assert row.sampled_validation == "pass"
    assert "[0,1.5]" in row.intervals


def test_generate_atlas_writes_csv_and_figures(tmp_path: Path) -> None:
    csv_path = generate_atlas(
        tmp_path,
        lambda2_values=(1.0,),
        lambda3_values=(0.5,),
        samples=180,
    )
    assert csv_path.is_file()
    text = csv_path.read_text(encoding="utf-8")
    assert "lambda2,lambda3,topology" in text
    assert "equal_proximal" in text
    assert (tmp_path / "figures" / "equal_proximal.png").is_file()
    assert (tmp_path / "figures" / "boundary_degenerate.png").is_file()


def test_named_boundary_family_matches_absolute_lengths() -> None:
    # Atlas rows are normalized by l1; absolute (3,2,2) shares ratios (2/3, 2/3).
    absolute = Planar3R(3.0, 2.0, 2.0)
    row = build_atlas_row(2.0 / 3.0, 2.0 / 3.0, family="boundary_degenerate")
    assert row.topology == absolute.dexterous_topology() == "degenerate"
    assert row.sampled_validation == "pass"
