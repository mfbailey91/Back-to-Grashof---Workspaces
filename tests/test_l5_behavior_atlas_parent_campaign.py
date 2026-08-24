import json
from pathlib import Path

import pytest

from grashof_workspace.spatial_experiments.l5_behavior_atlas.parent_campaign import (
    ArchitectureDisposition,
    build_near_suru_controls,
    detect_parent_patterns,
    detector_scope,
    load_a2_config,
    run_parent_campaign,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
    fixture_seed_for_probe,
)
from grashof_workspace.spatial_experiments.v06_corpus import (
    build_exact_two_u_5r,
    build_generic_5r,
    build_near_two_u_5r,
)

A2_CONFIG = Path("configs/l5_parent_campaign_v1.json")
R3A_CONFIG = Path("configs/l5_positive_control_v1.json")


def _positive():
    config = load_campaign_config(R3A_CONFIG)
    arm = build_positive_control_arm(config.geometry)
    probe = config.probes[0]
    q = fixture_seed_for_probe(
        arm,
        probe,
        position_tol_m=config.tolerances.position_residual_m,
        pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
    )
    return config, arm.model, q


def _patterns(model, q):
    diagnostics, patterns = detect_parent_patterns(model, q_seed=q)
    return diagnostics, {item.parent_family: item for item in patterns}


def test_positive_control_recovers_suru():
    _config, model, q = _positive()
    diagnostics, patterns = _patterns(model, q)
    assert tuple(item.pair_index for item in diagnostics if item.exact_u_candidate) == (0, 3)
    assert set(patterns) == {"SURU"}
    assert patterns["SURU"].candidate_child_family == "UURU"
    assert patterns["SURU"].aggregation_status == "EXACT_GLOBAL"


def test_exact_two_u_recovers_suur_parent_only_structure():
    entry = build_exact_two_u_5r()
    diagnostics, patterns = _patterns(entry.model, entry.regular_q)
    assert tuple(item.pair_index for item in diagnostics if item.exact_u_candidate) == (0, 2)
    assert set(patterns) == {"SUUR"}
    assert patterns["SUUR"].candidate_child_family == "UUUR"
    assert patterns["SUUR"].aggregation_status == "EXACT_GLOBAL"


def test_generic_is_not_nearest_matched():
    entry = build_generic_5r()
    _diagnostics, patterns = _patterns(entry.model, entry.regular_q)
    assert patterns == {}


def test_near_two_u_does_not_recover_two_u_parent():
    entry = build_near_two_u_5r()
    diagnostics, patterns = _patterns(entry.model, entry.regular_q)
    exact = tuple(item.pair_index for item in diagnostics if item.exact_u_candidate)
    assert exact == (0,)
    assert patterns == {}


def test_near_suru_controls_break_suru():
    r3a = load_campaign_config(R3A_CONFIG)
    base_model = build_positive_control_arm(r3a.geometry).model
    probe = r3a.probes[0]
    q = fixture_seed_for_probe(
        build_positive_control_arm(r3a.geometry),
        probe,
        position_tol_m=r3a.tolerances.position_residual_m,
        pointing_tol_rad=r3a.tolerances.pointing_geodesic_rad,
    )
    _d0, p0 = _patterns(base_model, q)
    assert "SURU" in p0

    shoulder, wrist = build_near_suru_controls(r3a, offset_m=1e-4)
    _ds, ps = _patterns(shoulder, q)
    _dw, pw = _patterns(wrist, q)
    assert "SURU" not in ps
    assert "SURU" not in pw


def test_s_physical_registered_families_are_out_of_detector_scope():
    scope = detector_scope()
    assert scope["parent_to_child_candidates"] == {
        "SRUU": "URUU",
        "SURU": "UURU",
        "SUUR": "UUUR",
    }
    assert set(scope["out_of_scope_registered_child_families"]) >= {
        "USRR",
        "URSR",
        "URRS",
    }


def _write_a1_fixture(tmp_path: Path, *, config_hash: str, fail_count: int = 0):
    manifest = tmp_path / "e0_manifest.json"
    audit = tmp_path / "e0_roundtrip_audit.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "l5_behavior_atlas_extraction_v1",
                "program_id": "R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER",
                "source_campaign_id": "fixture",
                "source_config_sha256": config_hash,
                "record_count": 2,
                "workspace_evidence_eligible_count": 0,
                "family_counts": {"UURU": 2},
                "records": [
                    {
                        "record_id": "uuru-0",
                        "family": {
                            "family_id": "UURU",
                            "parent_family_id": "SURU",
                            "joint_kind_sequence": ["U", "U", "R", "U"],
                            "joint_role_sequence": [
                                "U_v",
                                "U_phys",
                                "R_phys",
                                "U_phys",
                            ],
                        },
                        "source": {
                            "source_chain_id": "positive_control_suru_5r"
                        },
                    },
                    {
                        "record_id": "uuru-1",
                        "family": {
                            "family_id": "UURU",
                            "parent_family_id": "SURU",
                            "joint_kind_sequence": ["U", "U", "R", "U"],
                            "joint_role_sequence": [
                                "U_v",
                                "U_phys",
                                "R_phys",
                                "U_phys",
                            ],
                        },
                        "source": {
                            "source_chain_id": "positive_control_suru_5r"
                        },
                    },
                ],
                "notes": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    audit.write_text(
        json.dumps(
            {
                "program_id": "R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER",
                "roundtrip_status_counts": {
                    "NUMERICAL_PASS": 2 - fail_count,
                    "GEOMETRY_ONLY_PASS": 0,
                    "FAIL": fail_count,
                },
                "roundtrip_failures": (
                    ["uuru-0"] if fail_count else []
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest, audit


def test_parent_campaign_separates_actual_child_from_candidate_only(tmp_path):
    r3a = load_campaign_config(R3A_CONFIG)
    manifest, audit = _write_a1_fixture(
        tmp_path,
        config_hash=r3a.config_hash,
    )
    payload = run_parent_campaign(
        config_path=A2_CONFIG,
        a1_manifest_path=manifest,
        a1_audit_path=audit,
    )
    by_case = {item["case_id"]: item for item in payload["architectures"]}

    assert by_case["r3a_positive_control"]["disposition"] == (
        ArchitectureDisposition.EXACT_CHILD_EXPORTED.value
    )
    assert by_case["r3a_positive_control"]["actual_e0_child_families"] == ["UURU"]

    exact = by_case["exact_two_u_5r"]
    assert exact["disposition"] == (
        ArchitectureDisposition.REGISTERED_PARENT_PATTERN_ONLY.value
    )
    assert exact["actual_e0_child_families"] == []
    assert exact["parent_patterns"][0]["candidate_child_family"] == "UUUR"

    assert [item["family_id"] for item in payload["a3_family_queue"]] == ["UURU"]
    assert [item["candidate_child_family"] for item in payload["child_construction_backlog"]] == ["UUUR"]



def test_a1_family_must_match_exact_source_parent_pattern(tmp_path):
    r3a = load_campaign_config(R3A_CONFIG)
    manifest, audit = _write_a1_fixture(
        tmp_path,
        config_hash=r3a.config_hash,
    )
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    for record in raw["records"]:
        record["family"]["family_id"] = "URUU"
    raw["family_counts"] = {"URUU": 2}
    manifest.write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="do not match the exact registered parent-pattern census"):
        run_parent_campaign(
            config_path=A2_CONFIG,
            a1_manifest_path=manifest,
            a1_audit_path=audit,
        )

def test_a1_roundtrip_failure_blocks_a2(tmp_path):
    r3a = load_campaign_config(R3A_CONFIG)
    manifest, audit = _write_a1_fixture(
        tmp_path,
        config_hash=r3a.config_hash,
        fail_count=1,
    )
    with pytest.raises(ValueError, match="round-trip failures"):
        run_parent_campaign(
            config_path=A2_CONFIG,
            a1_manifest_path=manifest,
            a1_audit_path=audit,
        )


def test_parent_campaign_outputs_are_deterministic(tmp_path):
    r3a = load_campaign_config(R3A_CONFIG)
    manifest, audit = _write_a1_fixture(
        tmp_path,
        config_hash=r3a.config_hash,
    )
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    run_parent_campaign(
        config_path=A2_CONFIG,
        a1_manifest_path=manifest,
        a1_audit_path=audit,
        outdir=out_a,
    )
    run_parent_campaign(
        config_path=A2_CONFIG,
        a1_manifest_path=manifest,
        a1_audit_path=audit,
        outdir=out_b,
    )
    for name in (
        "parent_campaign.json",
        "a3_family_queue.json",
        "child_construction_backlog.json",
        "parent_family_census.csv",
        "parent_probes.csv",
    ):
        assert (out_a / name).read_bytes() == (out_b / name).read_bytes()


def test_a2_config_contains_all_required_cases():
    config = load_a2_config(A2_CONFIG)
    assert config.required_cases == (
        "r3a_positive_control",
        "exact_two_u_5r",
        "generic_5r",
        "near_two_u_5r",
        "near_suru_shoulder",
        "near_suru_wrist",
    )
