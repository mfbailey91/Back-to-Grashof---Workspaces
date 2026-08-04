from grashof_workspace.fourbar import FourBar


def test_grashof_margin_positive_for_classic_crank_rocker() -> None:
    linkage = FourBar(ground=4.0, input=2.0, coupler=4.0, output=5.0)
    assert linkage.is_grashof()
    assert linkage.grashof_margin == 1.0
    assert linkage.grashof_class() == "grashof"
    assert linkage.inversion_type() == "crank-rocker"
    assert linkage.input_can_fully_rotate()


def test_exact_input_rotation_uses_loop_closure_bounds() -> None:
    linkage = FourBar(ground=2.0, input=1.0, coupler=2.0, output=2.0)
    assert linkage.input_distance_bounds() == (1.0, 3.0)
    assert linkage.connector_distance_bounds() == (0.0, 4.0)
    assert linkage.input_can_fully_rotate()


def test_input_rotation_rejected_when_inner_dead_zone_is_crossed() -> None:
    linkage = FourBar(ground=1.0, input=1.5, coupler=1.0, output=3.0)
    assert not linkage.input_can_fully_rotate()


def test_grashof_label_is_not_a_substitute_for_input_rotatability() -> None:
    """Conventional class can be Grashof crank-rocker while the input rocks.

    Shortest link is the output, so the linkage is Grashof, but full rotation
    belongs to the output crank — not the input. Exact workspace membership
    must use ``input_can_fully_rotate``, not the inversion label alone.
    """
    linkage = FourBar(ground=5.0, input=4.0, coupler=4.0, output=2.0)
    assert linkage.is_grashof()
    assert linkage.grashof_class() == "grashof"
    assert linkage.inversion_type() == "crank-rocker"
    assert not linkage.input_can_fully_rotate()


def test_change_point_margin_is_zero() -> None:
    linkage = FourBar(ground=3.0, input=2.0, coupler=2.0, output=3.0)
    assert abs(linkage.grashof_margin) < 1e-12
    assert linkage.grashof_class() == "change-point"
    assert linkage.inversion_type() == "change-point"


def test_non_assemblable_loop_is_not_a_conventional_mechanism() -> None:
    linkage = FourBar(ground=10.0, input=1.0, coupler=1.0, output=1.0)
    assert linkage.assembly_margin < 0.0
    assert not linkage.is_assemblable()
    assert linkage.grashof_class() == "non-assemblable"
    assert linkage.inversion_type() == "non-assemblable"
    assert not linkage.input_can_fully_rotate()


def test_degenerate_collinear_assembly() -> None:
    linkage = FourBar(ground=3.0, input=1.0, coupler=1.0, output=1.0)
    assert abs(linkage.assembly_margin) < 1e-12
    assert linkage.is_assemblable()
    assert linkage.inversion_type() == "degenerate-collinear"


def test_zero_ground_is_not_labeled_double_crank() -> None:
    linkage = FourBar(ground=0.0, input=1.0, coupler=2.0, output=2.0)
    assert linkage.inversion_type() == "degenerate-coincident-ground-pivots"
    assert linkage.inversion_type() != "double-crank"


def test_input_rotation_implies_assemblable() -> None:
    linkage = FourBar(ground=2.0, input=1.0, coupler=2.0, output=2.0)
    assert linkage.input_can_fully_rotate()
    assert linkage.is_assemblable()


def test_scale_invariance_of_classification_and_rotation() -> None:
    base = FourBar(ground=2.0, input=1.0, coupler=2.0, output=2.0)
    scaled = FourBar(ground=6.0, input=3.0, coupler=6.0, output=6.0)
    assert base.inversion_type() == scaled.inversion_type()
    assert base.grashof_class() == scaled.grashof_class()
    assert base.input_can_fully_rotate() == scaled.input_can_fully_rotate()
