"""Declared-resolution family interval ledger. Not a global foliation."""

from __future__ import annotations

from dataclasses import replace

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import (
    apply_interval_coverage_gate,
    audit_family_intervals,
    classify_interval_status,
    interval_coverage_ok,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    FamilyAdmissibilityStatus,
    FamilyIntervalRecord,
    IntervalStatus,
    LeafConstructionKind,
    NaturalLeafCertificate,
    NaturalLeafSample,
    NaturalLeafSpec,
)


def _spec(leaf_id: str, chart_id: str, lam: float) -> NaturalLeafSpec:
    return NaturalLeafSpec(
        leaf_id=leaf_id,
        probe_id="P1",
        construction_kind=LeafConstructionKind.VIRTUAL_ORIENTATION_COORDINATE,
        chart_id=chart_id,
        lambda_fixed=lam,
        p_star=(1.0, 0.0, 0.0),
        geometry_hash="test",
        joint_kind_sequence=("R",),
        joint_role_sequence=("R_phys",),
    )


def _leaf(
    *,
    leaf_id: str,
    chart_id: str,
    lam: float,
    accepted: bool = False,
    component: str = "LOCAL_ONLY",
    family: FamilyAdmissibilityStatus = FamilyAdmissibilityStatus.UNRESOLVED,
    singular: bool = False,
) -> NaturalLeafCertificate:
    samples: tuple[NaturalLeafSample, ...] = ()
    if singular:
        samples = (
            NaturalLeafSample(
                s=0.0,
                x=(0.0,),
                q_source=(0.0, 0.0, 0.0, 0.0, 0.0),
                pointing=(0.0, 0.0, 1.0),
                lambda_recovered=lam,
                closure_residual=0.0,
                position_residual_m=0.0,
                orientation_error_rad=0.0,
                pointing_error_rad=0.0,
                joint_lift_error_rad=0.0,
                family_coordinate_error_rad=0.0,
                rank_j=1,
                nullity_j=1,
                chart_singularity=True,
            ),
        )
    return NaturalLeafCertificate(
        spec=_spec(leaf_id, chart_id, lam),
        construction_status="virtual_orientation_coordinate",
        leaf_component_status=component,
        family_admissibility_status=family,
        component_scope="test",
        branch_status="open",
        returned=False,
        samples=samples,
        max_closure_residual=None,
        max_position_residual_m=None,
        max_orientation_error_rad=None,
        max_pointing_error_rad=None,
        max_joint_lift_error_rad=None,
        max_family_coordinate_error_rad=None,
        reseed=None,
        transversality=None,
        chart_overlap_status="UNRESOLVED",
        accepted_for_reconstruction=accepted,
        failure_or_scope_reason="test",
        responsible_chart_id=chart_id,
    )


def test_sampled_admissible_is_not_called_complete() -> None:
    leaf = _leaf(
        leaf_id="ok",
        chart_id="ZYZ_WORLD",
        lam=-1.0,
        accepted=True,
        component="EXACT_ON_COMPONENT",
        family=FamilyAdmissibilityStatus.PASS,
    )
    records = audit_family_intervals(
        (leaf,),
        n_bins=2,
        chart_ids=("ZYZ_WORLD", "ZYZ_RX90"),
        occupied={("ZYZ_WORLD", 0)},
    )
    world_bin0 = next(
        item for item in records if item.chart_id == "ZYZ_WORLD" and item.lambda_interval[0] < -1.0
    )
    assert world_bin0.interval_status is IntervalStatus.SAMPLED_ADMISSIBLE
    assert world_bin0.interval_status != "COMPLETE"
    assert world_bin0.interval_status.value != "COMPLETE"
    assert all(item.interval_status != "COMPLETE" for item in records)
    payload = world_bin0.to_json_dict()
    assert payload["interval_status"] == "SAMPLED_ADMISSIBLE"
    assert payload["interval_status"] != "COMPLETE"
    assert (
        payload["topology_event_status"]
        == "NOT_EVALUATED_EXCLUDED_FROM_DECLARED_RESOLUTION_SET_COVER"
    )


def test_missing_required_bin_blocks_natural_cover() -> None:
    accepted = _leaf(
        leaf_id="ok",
        chart_id="ZYZ_WORLD",
        lam=-1.0,
        accepted=True,
        component="EXACT_ON_COMPONENT",
        family=FamilyAdmissibilityStatus.PASS,
    )
    records = audit_family_intervals(
        (accepted,),
        n_bins=2,
        chart_ids=("ZYZ_WORLD",),
        occupied={("ZYZ_WORLD", 0), ("ZYZ_WORLD", 1)},
    )
    statuses = {item.interval_status for item in records}
    assert IntervalStatus.SAMPLED_ADMISSIBLE in statuses
    assert IntervalStatus.UNSAMPLED in statuses
    assert interval_coverage_ok(records) is False
    gated, gaps = apply_interval_coverage_gate((accepted,), records)
    assert gaps
    assert all(leaf.accepted_for_reconstruction is False for leaf in gated)


def test_not_required_chart_bin_does_not_block() -> None:
    accepted = _leaf(
        leaf_id="ok",
        chart_id="ZYZ_WORLD",
        lam=-1.0,
        accepted=True,
        component="EXACT_ON_COMPONENT",
        family=FamilyAdmissibilityStatus.PASS,
    )
    records = audit_family_intervals(
        (accepted,),
        n_bins=2,
        chart_ids=("ZYZ_WORLD", "ZYZ_RX90"),
        occupied={("ZYZ_WORLD", 0)},
    )
    rx_rows = [item for item in records if item.chart_id == "ZYZ_RX90"]
    assert rx_rows
    assert all(item.interval_status is IntervalStatus.NOT_REQUIRED for item in rx_rows)
    assert interval_coverage_ok(records) is True
    gated, gaps = apply_interval_coverage_gate((accepted,), records)
    assert gaps == ()
    assert gated[0].accepted_for_reconstruction is True


def test_classify_interval_status_vocabulary() -> None:
    assert (
        classify_interval_status(required=False, members=(), budget_exhausted=False, critical=())
        is IntervalStatus.NOT_REQUIRED
    )
    assert (
        classify_interval_status(required=True, members=(), budget_exhausted=False, critical=())
        is IntervalStatus.UNSAMPLED
    )
    assert (
        classify_interval_status(required=True, members=(), budget_exhausted=True, critical=())
        is IntervalStatus.UNRESOLVED
    )
    local = _leaf(leaf_id="local", chart_id="ZYZ_WORLD", lam=0.1)
    assert (
        classify_interval_status(required=True, members=(local,), budget_exhausted=False, critical=())
        is IntervalStatus.SAMPLED_LOCAL
    )
    component = _leaf(
        leaf_id="comp",
        chart_id="ZYZ_WORLD",
        lam=0.1,
        component="EXACT_ON_COMPONENT",
    )
    assert (
        classify_interval_status(
            required=True, members=(component,), budget_exhausted=False, critical=()
        )
        is IntervalStatus.SAMPLED_COMPONENT
    )
    dummy = FamilyIntervalRecord(
        chart_id="ZYZ_WORLD",
        lambda_interval=(-1.0, 0.0),
        sampled_lambda_values=(),
        accepted_leaf_ids=(),
        rejected_leaf_ids=(),
        unresolved_leaf_ids=(),
        interval_status=IntervalStatus.SAMPLED_ADMISSIBLE,
        required=True,
    )
    replaced = replace(dummy, interval_status=IntervalStatus.SAMPLED_ADMISSIBLE)
    assert replaced.interval_status != "COMPLETE"


def test_required_budget_exhaustion_overrides_sampled_member() -> None:
    accepted = _leaf(
        leaf_id="ok",
        chart_id="ZYZ_WORLD",
        lam=-1.0,
        accepted=True,
        component="EXACT_ON_COMPONENT",
        family=FamilyAdmissibilityStatus.PASS,
    )
    status = classify_interval_status(
        required=True,
        members=(accepted,),
        budget_exhausted=True,
        critical=(),
    )
    assert status is IntervalStatus.UNRESOLVED
