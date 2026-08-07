from __future__ import annotations

from grashof_workspace.spatial4bar_explorer.closure import audit_reference_geometry
from grashof_workspace.spatial4bar_explorer.geometry import canonical_geometry
from grashof_workspace.spatial4bar_explorer.models import OrderedFamily
from grashof_workspace.spatial4bar_explorer.v04b import (
    direction_reversal_check,
    orientation_sweep,
    step_size_sweep,
    with_tool_u_orientation,
)


def test_tool_u_orientation_changes_only_tool_frame() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    variant = with_tool_u_orientation(geometry, phi_deg=30.0, axis_order="ab")
    assert variant.joints[0].center == geometry.joints[0].center
    assert variant.joints[0].frame != geometry.joints[0].frame
    assert variant.joints[1:] == geometry.joints[1:]
    assert audit_reference_geometry(variant).jacobian_nullity == 1


def test_tool_u_ba_order_keeps_valid_u_frame() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    variant = with_tool_u_orientation(geometry, phi_deg=0.0, axis_order="ba")
    assert not variant.validation_errors()
    assert variant.joints[0].motion_axes[0] == geometry.joints[0].motion_axes[1]
    assert variant.joints[0].motion_axes[1] == geometry.joints[0].motion_axes[0]


def test_step_size_winding_is_stable_on_canonical_uuur() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    rows = step_size_sweep(geometry, step_sizes=(0.05, 0.025), arclength_budget=40.0)
    returned = [row for row in rows if row.returned]
    assert returned
    pairs = {(row.w_alpha, row.w_beta) for row in returned}
    assert len(pairs) == 1
    assert all(row.max_raw_increment is None or row.max_raw_increment < 3.141592653589793 for row in returned)


def test_direction_reversal_flips_winding_when_both_return() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    plus, minus = direction_reversal_check(geometry, step_size=0.05, arclength_budget=40.0)
    if plus.returned and minus.returned:
        assert plus.w_alpha is not None and minus.w_alpha is not None
        assert plus.w_beta is not None and minus.w_beta is not None
        assert minus.w_alpha == -plus.w_alpha
        assert minus.w_beta == -plus.w_beta
        assert plus.class_alpha == minus.class_alpha
        assert plus.class_beta == minus.class_beta


def test_orientation_sweep_reports_rank_and_winding() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    rows = orientation_sweep(
        geometry,
        phi_degrees=(0.0, 45.0, 90.0),
        axis_order="ab",
        step_size=0.05,
        max_steps=700,
    )
    assert len(rows) == 3
    assert all(row.jacobian_rank == 6 and row.jacobian_nullity == 1 for row in rows)
    assert all(row.audit_status == "PASS" for row in rows)
