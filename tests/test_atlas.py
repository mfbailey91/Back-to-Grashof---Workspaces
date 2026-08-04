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
    assert "disk+boundary_circle" in text or "disk" in text
    assert (tmp_path / "figures" / "equal_proximal.png").is_file()
    assert (tmp_path / "figures" / "boundary_degenerate.png").is_file()
    assert (tmp_path / "figures" / "disk_and_annulus_radial_state.png").is_file()
    state_csv = tmp_path / "radial_mechanism_states.csv"
    assert state_csv.is_file()
    state_text = state_csv.read_text(encoding="utf-8")
    assert "grashof_class" in state_text
    assert "input_can_fully_rotate" in state_text
    assert "dexterous" in state_text


def test_named_boundary_family_matches_absolute_lengths() -> None:
    absolute = Planar3R(3.0, 2.0, 2.0)
    row = build_atlas_row(2.0 / 3.0, 2.0 / 3.0, family="boundary_degenerate")
    assert row.topology == absolute.dexterous_topology() == "disk+boundary_circle"
    assert row.sampled_validation == "pass"
