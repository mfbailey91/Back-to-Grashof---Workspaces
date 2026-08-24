import json
from pathlib import Path

import numpy as np
import pytest

from grashof_workspace.spatial_experiments.l5_behavior_atlas import (
    UNRESOLVED_SOURCE_COMPONENT_ID,
    geometry_record_from_uuru_problem,
    reconstruct_uuru_problem,
)
from grashof_workspace.spatial_experiments.l5_behavior_atlas.exporter import (
    RoundTripStatus,
    audit_geometry_roundtrip,
    export_campaign,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
    fixture_seed_for_probe,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    geometry_hash,
    leaf_spec_for,
    problem_from_source_seed,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def _real_problem():
    config = load_campaign_config(CONFIG)
    probe = config.probe("P1_DEEP_COMPLETE")
    arm = build_positive_control_arm(config.geometry)
    chart = charts_from_config(config.charts)[0]
    q = fixture_seed_for_probe(
        arm,
        probe,
        position_tol_m=config.tolerances.position_residual_m,
        pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
    )
    built = problem_from_source_seed(
        arm,
        chart,
        q,
        probe.p_star,
        leaf_id="A1_TEST_LEAF",
    )
    assert built is not None
    problem, x = built
    return config, probe, chart, problem, x


def _leaf_blob(config, probe, chart, problem, x):
    spec = leaf_spec_for(
        probe.probe_id,
        chart,
        problem.lambda_fixed,
        probe.p_star,
        problem.problem_id,
    )
    return {
        "spec": spec.to_json_dict(),
        "construction_kind": "virtual_orientation_coordinate",
        "child_family": "UURU",
        "joint_kind_sequence": ["U", "U", "R", "U"],
        "joint_role_sequence": ["U_v", "U_phys", "R_phys", "U_phys"],
        "leaf_component_status": "EXACT_ON_COMPONENT",
        "closed_mechanism_status": "EXACT_ON_COMPONENT",
        "accepted_for_reconstruction": True,
        "samples": [{"x": [float(v) for v in x]}],
    }


def _write_source_package(tmp_path, config, leaf):
    campaign = tmp_path / "r3a"
    probe = config.probe("P1_DEEP_COMPLETE")
    probe_dir = campaign / probe.probe_id
    probe_dir.mkdir(parents=True)
    (probe_dir / "natural_family.json").write_text(
        json.dumps(
            {"probe_id": probe.probe_id, "leaves": [leaf]},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (campaign / "compact_manifest.json").write_text(
        json.dumps(
            {
                "program_id": config.program_id,
                "package_kind": "full_closeout",
                "campaign_mode": "full",
                "producer_config_hash": config.config_hash,
                "producer_git": {"git_commit": "a" * 40, "dirty_tree": False},
                "campaign_blocker": "STITCHING_CONTROL_BLOCKED",
                "accepted_reconstruction": False,
                "semantic_revalidation": True,
                "all_configured_probes_present": True,
                "raw_bundle_sha256": "b" * 64,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return campaign


def test_payload_only_uuru_roundtrip_preserves_geometry_and_equations():
    _config, _probe, _chart, problem, x = _real_problem()
    record = geometry_record_from_uuru_problem(problem)
    rebuilt = reconstruct_uuru_problem(record, problem_id="A1_REBUILT")
    reencoded = geometry_record_from_uuru_problem(rebuilt)

    assert record.geometry_sha256 == reencoded.geometry_sha256
    assert id(rebuilt.source.chain) != id(rebuilt.independent_chain)
    assert np.linalg.norm(problem.residual(x) - rebuilt.residual(x)) <= 1e-12
    assert np.max(np.abs(problem.jacobian(x) - rebuilt.jacobian(x))) <= 1e-10


def test_roundtrip_audit_is_numerical_pass_at_real_seed():
    _config, _probe, _chart, problem, x = _real_problem()
    audit = audit_geometry_roundtrip(
        "fixture_record",
        problem,
        sample_xs=(x,),
        source_artifact_sha256="c" * 64,
    )
    assert audit.status is RoundTripStatus.NUMERICAL_PASS
    assert audit.geometry_hash_match
    assert audit.passed


def test_export_preserves_leaf_metadata_but_blocks_workspace_eligibility(tmp_path):
    config, probe, chart, problem, x = _real_problem()
    leaf = _leaf_blob(config, probe, chart, problem, x)
    campaign = _write_source_package(tmp_path, config, leaf)
    outdir = tmp_path / "out"

    manifest, audit = export_campaign(
        config_path=CONFIG,
        campaign_dir=campaign,
        outdir=outdir,
        probe_ids=(probe.probe_id,),
    )

    assert len(manifest.records) == 1
    record = manifest.records[0]
    assert record.family.family_id == "UURU"
    assert record.source.source_component_id == UNRESOLVED_SOURCE_COMPONENT_ID
    assert record.source.accepted_for_reconstruction is True
    assert record.source.child_certificate_status == "EXACT_ON_COMPONENT"
    assert record.workspace_evidence_eligible is False
    assert audit["roundtrip_status_counts"]["NUMERICAL_PASS"] == 1
    assert json.loads((outdir / "e0_manifest.json").read_text())["record_count"] == 1


def test_export_refuses_source_config_hash_mismatch(tmp_path):
    config, probe, chart, problem, x = _real_problem()
    leaf = _leaf_blob(config, probe, chart, problem, x)
    campaign = _write_source_package(tmp_path, config, leaf)
    manifest_path = campaign / "compact_manifest.json"
    source = json.loads(manifest_path.read_text())
    source["producer_config_hash"] = "wrong"
    manifest_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="producer_config_hash"):
        export_campaign(
            config_path=CONFIG,
            campaign_dir=campaign,
            probe_ids=(probe.probe_id,),
        )


def test_export_refuses_legacy_geometry_hash_mismatch(tmp_path):
    config, probe, chart, problem, x = _real_problem()
    leaf = _leaf_blob(config, probe, chart, problem, x)
    leaf["spec"]["geometry_hash"] = "bad"
    campaign = _write_source_package(tmp_path, config, leaf)

    with pytest.raises(ValueError, match="legacy leaf geometry hash mismatch"):
        export_campaign(
            config_path=CONFIG,
            campaign_dir=campaign,
            probe_ids=(probe.probe_id,),
        )


def test_export_refuses_family_role_relabel(tmp_path):
    config, probe, chart, problem, x = _real_problem()
    leaf = _leaf_blob(config, probe, chart, problem, x)
    leaf["joint_role_sequence"] = ["U_phys", "U_v", "R_phys", "U_phys"]
    campaign = _write_source_package(tmp_path, config, leaf)

    with pytest.raises(ValueError, match="joint-role"):
        export_campaign(
            config_path=CONFIG,
            campaign_dir=campaign,
            probe_ids=(probe.probe_id,),
        )


def test_export_is_deterministic(tmp_path):
    config, probe, chart, problem, x = _real_problem()
    leaf = _leaf_blob(config, probe, chart, problem, x)
    # Explicitly verify the fixture's legacy hash is the current R3A definition.
    assert leaf["spec"]["geometry_hash"] == geometry_hash(chart, problem.lambda_fixed)
    campaign = _write_source_package(tmp_path, config, leaf)

    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    export_campaign(
        config_path=CONFIG,
        campaign_dir=campaign,
        outdir=out_a,
        probe_ids=(probe.probe_id,),
    )
    export_campaign(
        config_path=CONFIG,
        campaign_dir=campaign,
        outdir=out_b,
        probe_ids=(probe.probe_id,),
    )

    assert (out_a / "e0_manifest.json").read_bytes() == (
        out_b / "e0_manifest.json"
    ).read_bytes()
    assert (out_a / "e0_roundtrip_audit.json").read_bytes() == (
        out_b / "e0_roundtrip_audit.json"
    ).read_bytes()
