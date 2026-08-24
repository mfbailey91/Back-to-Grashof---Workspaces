import json

import pytest

from grashof_workspace.spatial_experiments.l5_behavior_atlas import (
    ExtractedMechanismRecord,
    ExtractionManifest,
    MechanismFamilyIdentity,
    MechanismGeometryRecord,
    MechanismProvenance,
    SourceProvenanceRecord,
)


def _family(*, roles: tuple[str, ...] = ("U_v", "U_phys", "R_phys", "U_phys")):
    return MechanismFamilyIdentity(
        family_id="UURU",
        parent_family_id="SURU",
        joint_kind_sequence=("U", "U", "R", "U"),
        joint_role_sequence=roles,
    )


def _source(
    *,
    provenance: MechanismProvenance = MechanismProvenance.SOURCE_DERIVED_NATURAL_LEAF,
    accepted: bool = True,
    status: str = "EXACT_ON_COMPONENT",
):
    return SourceProvenanceRecord(
        source_chain_id="positive_control_suru_5r",
        fixed_position_problem_id="P1_DEEP_COMPLETE",
        source_component_id="component_0",
        probe_id="P1_DEEP_COMPLETE",
        task_point=(0.94, 0.18, 0.28),
        source_artifact="results/l5_reconstruction/r3a/P1/leaves.json",
        leaf_id="leaf_0001",
        construction_kind="virtual_orientation_coordinate",
        chart_id="ZYZ_WORLD",
        family_parameters=(("lambda", 0.25),),
        child_certificate_status=status,
        accepted_for_reconstruction=accepted,
        provenance=provenance,
    )


def _geometry():
    return MechanismGeometryRecord.from_payload(
        geometry_schema_id="uuru_frozen_geometry_v1",
        payload={
            "axes": [
                {"point": [0.0, 0.0, 0.0], "direction": [0.0, 0.0, 1.0]},
                {"point": [0.0, 0.0, 0.0], "direction": [0.0, 1.0, 0.0]},
            ],
            "lambda": 0.25,
        },
    )


def _record(*, record_id: str = "record_0001", source=None):
    return ExtractedMechanismRecord(
        record_id=record_id,
        family=_family(),
        source=source or _source(),
        geometry=_geometry(),
    )


def test_geometry_hash_is_mapping_order_invariant():
    a = MechanismGeometryRecord.from_payload(
        geometry_schema_id="test_v1",
        payload={"b": 2, "a": {"y": 4, "x": 3}},
    )
    b = MechanismGeometryRecord.from_payload(
        geometry_schema_id="test_v1",
        payload={"a": {"x": 3, "y": 4}, "b": 2},
    )
    assert a.payload_json == b.payload_json
    assert a.geometry_sha256 == b.geometry_sha256


def test_geometry_rejects_nonfinite_values():
    with pytest.raises(ValueError, match="non-finite"):
        MechanismGeometryRecord.from_payload(
            geometry_schema_id="test_v1",
            payload={"bad": float("nan")},
        )


def test_family_identity_is_role_aware():
    physical = _family()
    altered = _family(roles=("U_phys", "U_v", "R_phys", "U_phys"))
    assert physical != altered


def test_explorer_only_cannot_be_accepted_for_reconstruction():
    with pytest.raises(ValueError, match="explorer"):
        _source(
            provenance=MechanismProvenance.MECHANISM_EXPLORER_ONLY,
            accepted=True,
        )


@pytest.mark.parametrize(
    ("provenance", "accepted", "status", "expected"),
    [
        (MechanismProvenance.SOURCE_DERIVED_NATURAL_LEAF, True, "EXACT_GLOBAL", True),
        (
            MechanismProvenance.SOURCE_DERIVED_NATURAL_LEAF,
            True,
            "EXACT_ON_COMPONENT",
            True,
        ),
        (MechanismProvenance.SOURCE_DERIVED_NATURAL_LEAF, False, "EXACT_GLOBAL", False),
        (MechanismProvenance.SOURCE_DERIVED_NATURAL_LEAF, True, "LOCAL_ONLY", False),
        (MechanismProvenance.SOURCE_DERIVED_CANDIDATE, True, "EXACT_GLOBAL", False),
    ],
)
def test_workspace_eligibility_is_conjunctive(provenance, accepted, status, expected):
    record = _record(
        source=_source(
            provenance=provenance,
            accepted=accepted,
            status=status,
        )
    )
    assert record.workspace_evidence_eligible is expected


def test_manifest_rejects_duplicate_record_ids():
    with pytest.raises(ValueError, match="unique"):
        ExtractionManifest(
            program_id="R3C_A0",
            source_campaign_id="fixture",
            source_config_sha256="abc123",
            records=(_record(), _record()),
        )


def test_manifest_json_is_strict_and_deterministic():
    manifest = ExtractionManifest(
        program_id="R3C_A0",
        source_campaign_id="fixture",
        source_config_sha256="abc123",
        records=(_record(),),
    )
    text = manifest.to_json_text()
    parsed = json.loads(text)
    assert parsed["record_count"] == 1
    assert parsed["family_counts"] == {"UURU": 1}
    assert parsed["workspace_evidence_eligible_count"] == 1
    assert "NaN" not in text
    assert text == manifest.to_json_text()
