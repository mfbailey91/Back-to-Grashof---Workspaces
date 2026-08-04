"""Sprint-01 analytical interval regressions locked before Sprint-02 renames."""

from grashof_workspace.fourbar import FourBar
from grashof_workspace.planar3r import Planar3R


def test_sprint01_interval_regressions() -> None:
    assert Planar3R(2.0, 2.0, 1.0).dexterous_radial_intervals() == ((0.0, 3.0),)
    assert Planar3R(1.0, 1.0, 3.0).dexterous_radial_intervals() == ()
    assert Planar3R(3.0, 1.0, 2.5).dexterous_radial_intervals() == ((0.0, 0.5),)
    assert Planar3R(3.0, 2.0, 1.5).dexterous_radial_intervals() == (
        (0.0, 0.5),
        (2.5, 3.5),
    )
    assert Planar3R(3.0, 2.0, 2.0).dexterous_radial_intervals() == (
        (0.0, 1.0),
        (3.0, 3.0),
    )
    assert Planar3R(3.0, 2.0, 0.5).dexterous_radial_intervals() == ((1.5, 4.5),)


def test_sprint01_valid_fourbar_labels() -> None:
    crank = FourBar(ground=4.0, input=2.0, coupler=4.0, output=5.0)
    assert crank.inversion_type() == "crank-rocker"
    change = FourBar(ground=3.0, input=2.0, coupler=2.0, output=3.0)
    assert change.inversion_type() == "change-point"
