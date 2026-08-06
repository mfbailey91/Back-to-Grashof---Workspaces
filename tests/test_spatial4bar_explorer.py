from grashof_workspace.spatial4bar_explorer.analysis import classify_mock_branch
from grashof_workspace.spatial4bar_explorer.descriptors import generate_geometry_samples
from grashof_workspace.spatial4bar_explorer.families import FAMILY_AXIS_CASES, ORDERED_FAMILIES
from grashof_workspace.spatial4bar_explorer.models import BranchClass, OrderedFamily, ToolAxis


def test_family_enumeration() -> None:
    assert ORDERED_FAMILIES == (
        OrderedFamily.UUUR,
        OrderedFamily.UURU,
        OrderedFamily.URUU,
        OrderedFamily.USRR,
        OrderedFamily.URSR,
        OrderedFamily.URRS,
    )
    assert len(FAMILY_AXIS_CASES) == 12


def test_geometry_sampling() -> None:
    samples = generate_geometry_samples(OrderedFamily.UUUR, count=3, seed=1)
    assert len(samples) == 3
    assert samples[0].family is OrderedFamily.UUUR
    assert len(samples[0].descriptors) >= 10


def test_mock_branch_classification() -> None:
    sample = generate_geometry_samples(OrderedFamily.USRR, count=1, seed=5)[0]
    case = next(c for c in FAMILY_AXIS_CASES if c.family is OrderedFamily.USRR and c.tool_axis is ToolAxis.A)
    result = classify_mock_branch(sample, case)
    assert result.case.family is OrderedFamily.USRR
    assert result.class_alpha in {BranchClass.CRANK, BranchClass.ROCKER, BranchClass.CHANGE_POINT}
