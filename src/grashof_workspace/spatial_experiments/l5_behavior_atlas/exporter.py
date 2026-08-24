"""R3C-A1 downstream exporter: R3A natural leaves -> reconstructible E0 records."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    CampaignConfig,
    load_campaign_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.positive_control import (
    build_positive_control_arm,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    SphericalClosureChart,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    ClosedUURULeafProblem,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    geometry_hash as legacy_leaf_geometry_hash,
)
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain

from .models import (
    UNRESOLVED_SOURCE_COMPONENT_ID,
    ExtractedMechanismRecord,
    ExtractionManifest,
    MechanismFamilyIdentity,
    MechanismProvenance,
    SourceProvenanceRecord,
)
from .uuru_geometry import (
    geometry_record_from_uuru_problem,
    reconstruct_uuru_problem,
)

A1_PROGRAM_ID = "R3C_A1_MANIPULATOR_TO_MECHANISM_EXPORTER"
ROUNDTRIP_RESIDUAL_TOL = 1e-12
ROUNDTRIP_JACOBIAN_TOL = 1e-10
ROUNDTRIP_FK_POSITION_TOL_M = 1e-12
ROUNDTRIP_FK_ORIENTATION_TOL_RAD = 1e-12


class RoundTripStatus(str, Enum):
    NUMERICAL_PASS = "NUMERICAL_PASS"
    GEOMETRY_ONLY_PASS = "GEOMETRY_ONLY_PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class GeometryRoundTripAudit:
    record_id: str
    status: RoundTripStatus
    sample_count: int
    geometry_hash_match: bool
    max_residual_delta: float | None
    max_jacobian_abs_delta: float | None
    max_source_position_delta_m: float | None
    max_source_orientation_delta_rad: float | None
    max_independent_position_delta_m: float | None
    max_independent_orientation_delta_rad: float | None
    source_artifact_sha256: str
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status is not RoundTripStatus.FAIL

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "status": self.status.value,
            "sample_count": self.sample_count,
            "geometry_hash_match": self.geometry_hash_match,
            "max_residual_delta": self.max_residual_delta,
            "max_jacobian_abs_delta": self.max_jacobian_abs_delta,
            "max_source_position_delta_m": self.max_source_position_delta_m,
            "max_source_orientation_delta_rad": self.max_source_orientation_delta_rad,
            "max_independent_position_delta_m": self.max_independent_position_delta_m,
            "max_independent_orientation_delta_rad": self.max_independent_orientation_delta_rad,
            "source_artifact_sha256": self.source_artifact_sha256,
            "notes": list(self.notes),
        }


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a JSON object")
    return value


def _vec3(value: Any, *, field: str) -> tuple[float, float, float]:
    values = list(value)
    if len(values) != 3:
        raise ValueError(f"{field} must have length 3")
    return (float(values[0]), float(values[1]), float(values[2]))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy_chain(chain: SerialRevoluteChain) -> SerialRevoluteChain:
    return SerialRevoluteChain(
        home_axes=chain.home_axes,
        p0=chain.p0,
        d0=chain.d0,
        R0=chain.R0,
    )


def _fk_orientation_delta_rad(ra: np.ndarray, rb: np.ndarray) -> float:
    """Return the SO(3) geodesic in a form stable at the identity.

    ``acos((tr-1)/2)`` yields ~1e-8 rad for bit-identical reconstructed
    rotations whose relative trace is ``3 - ulp``. Serializer equality uses
    ``atan2`` so a true zero gap stays below the 1e-12 rad contract.
    """

    relative = np.asarray(rb, dtype=float) @ np.asarray(ra, dtype=float).T
    skew = np.array(
        [
            relative[2, 1] - relative[1, 2],
            relative[0, 2] - relative[2, 0],
            relative[1, 0] - relative[0, 1],
        ],
        dtype=float,
    )
    sin_theta = 0.5 * float(np.linalg.norm(skew))
    cos_theta = 0.5 * (float(np.trace(relative)) - 1.0)
    return float(abs(math.atan2(sin_theta, cos_theta)))


def _chart(config: CampaignConfig, chart_id: str) -> SphericalClosureChart:
    for record in config.charts:
        if record.chart_id == chart_id:
            return SphericalClosureChart.from_record(record)
    raise KeyError(f"unknown chart_id {chart_id!r}")


def _leaf_problem_from_source_artifact(
    config: CampaignConfig,
    leaf: Mapping[str, Any],
) -> ClosedUURULeafProblem:
    """Recreate the original frozen child definition from config + leaf spec."""

    spec = _mapping(leaf["spec"], field="leaf.spec")
    probe_id = str(spec["probe_id"])
    probe = config.probe(probe_id)
    p_star = _vec3(spec["p_star"], field="leaf.spec.p_star")
    if float(np.linalg.norm(np.asarray(p_star) - np.asarray(probe.p_star))) > 1e-12:
        raise ValueError(f"{probe_id}: leaf p_star does not match frozen campaign config")

    chart_id = str(spec["chart_id"])
    chart = _chart(config, chart_id)
    lambda_fixed = float(spec["lambda_fixed"])

    expected_legacy_hash = legacy_leaf_geometry_hash(chart, lambda_fixed)
    recorded_legacy_hash = str(spec["geometry_hash"])
    if recorded_legacy_hash != expected_legacy_hash:
        raise ValueError(
            f"{probe_id}/{spec['leaf_id']}: legacy leaf geometry hash mismatch"
        )

    child_family = str(leaf.get("child_family", ""))
    if child_family != "UURU":
        raise ValueError(
            f"A1 supports the current exact R3A UURU child only, got {child_family!r}"
        )
    kinds = tuple(str(v) for v in leaf["joint_kind_sequence"])
    roles = tuple(str(v) for v in leaf["joint_role_sequence"])
    if kinds != ("U", "U", "R", "U"):
        raise ValueError(f"unexpected UURU joint-kind sequence {kinds!r}")
    if roles != ("U_v", "U_phys", "R_phys", "U_phys"):
        raise ValueError(f"unexpected UURU joint-role sequence {roles!r}")

    arm = build_positive_control_arm(config.geometry)
    return ClosedUURULeafProblem(
        source=arm.model,
        independent_chain=_copy_chain(arm.chain),
        chart=chart,
        lambda_fixed=lambda_fixed,
        p_star=p_star,
        problem_id=str(spec["leaf_id"]),
        joint_kind_sequence=kinds,
        joint_role_sequence=roles,
    )


def _sample_xs(leaf: Mapping[str, Any]) -> tuple[np.ndarray, ...]:
    values: list[np.ndarray] = []
    for i, item in enumerate(leaf.get("samples", [])):
        sample = _mapping(item, field=f"leaf.samples[{i}]")
        x = np.asarray(sample["x"], dtype=float).reshape(-1)
        if x.size != 7:
            raise ValueError(f"leaf.samples[{i}].x must have seven coordinates")
        values.append(x)
    return tuple(values)


def audit_geometry_roundtrip(
    record_id: str,
    original: ClosedUURULeafProblem,
    *,
    sample_xs: Sequence[np.ndarray],
    source_artifact_sha256: str,
) -> GeometryRoundTripAudit:
    """Prove payload-only reconstruction matches the source-defined child."""

    geometry = geometry_record_from_uuru_problem(original)
    rebuilt = reconstruct_uuru_problem(
        geometry,
        problem_id=f"{original.problem_id}_E0_REBUILT",
        source_chain_id=original.source.architecture_id,
    )
    reencoded = geometry_record_from_uuru_problem(rebuilt)
    hash_match = geometry.geometry_sha256 == reencoded.geometry_sha256

    residual_deltas: list[float] = []
    jacobian_deltas: list[float] = []
    source_position: list[float] = []
    source_orientation: list[float] = []
    independent_position: list[float] = []
    independent_orientation: list[float] = []

    for x in sample_xs:
        residual_deltas.append(
            float(np.linalg.norm(original.residual(x) - rebuilt.residual(x)))
        )
        jacobian_deltas.append(
            float(np.max(np.abs(original.jacobian(x) - rebuilt.jacobian(x))))
        )
        q = original.physical_q(x)
        source_a = original.source.chain.evaluate(q)
        source_b = rebuilt.source.chain.evaluate(q)
        child_a = original.independent_chain.evaluate(q)
        child_b = rebuilt.independent_chain.evaluate(q)
        source_position.append(
            float(np.linalg.norm(np.asarray(source_a.p) - np.asarray(source_b.p)))
        )
        source_orientation.append(
            _fk_orientation_delta_rad(np.asarray(source_a.R), np.asarray(source_b.R))
        )
        independent_position.append(
            float(np.linalg.norm(np.asarray(child_a.p) - np.asarray(child_b.p)))
        )
        independent_orientation.append(
            _fk_orientation_delta_rad(np.asarray(child_a.R), np.asarray(child_b.R))
        )

    max_residual = max(residual_deltas) if residual_deltas else None
    max_jacobian = max(jacobian_deltas) if jacobian_deltas else None
    max_source_position = max(source_position) if source_position else None
    max_source_orientation = max(source_orientation) if source_orientation else None
    max_child_position = max(independent_position) if independent_position else None
    max_child_orientation = max(independent_orientation) if independent_orientation else None

    numeric_ok = bool(
        sample_xs
        and max_residual is not None
        and max_residual <= ROUNDTRIP_RESIDUAL_TOL
        and max_jacobian is not None
        and max_jacobian <= ROUNDTRIP_JACOBIAN_TOL
        and max_source_position is not None
        and max_source_position <= ROUNDTRIP_FK_POSITION_TOL_M
        and max_source_orientation is not None
        and max_source_orientation <= ROUNDTRIP_FK_ORIENTATION_TOL_RAD
        and max_child_position is not None
        and max_child_position <= ROUNDTRIP_FK_POSITION_TOL_M
        and max_child_orientation is not None
        and max_child_orientation <= ROUNDTRIP_FK_ORIENTATION_TOL_RAD
    )
    if hash_match and numeric_ok:
        status = RoundTripStatus.NUMERICAL_PASS
    elif hash_match and not sample_xs:
        status = RoundTripStatus.GEOMETRY_ONLY_PASS
    else:
        status = RoundTripStatus.FAIL

    return GeometryRoundTripAudit(
        record_id=record_id,
        status=status,
        sample_count=len(sample_xs),
        geometry_hash_match=hash_match,
        max_residual_delta=max_residual,
        max_jacobian_abs_delta=max_jacobian,
        max_source_position_delta_m=max_source_position,
        max_source_orientation_delta_rad=max_source_orientation,
        max_independent_position_delta_m=max_child_position,
        max_independent_orientation_delta_rad=max_child_orientation,
        source_artifact_sha256=source_artifact_sha256,
        notes=(
            "Serializer/reconstructor equality only; not a behavior or workspace certificate.",
        ),
    )


def _source_package_authority(
    config: CampaignConfig,
    campaign_dir: Path,
) -> dict[str, Any]:
    path = campaign_dir / "compact_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing source package authority {path}")
    raw = _mapping(json.loads(path.read_text(encoding="utf-8")), field="compact_manifest")
    if str(raw.get("program_id")) != config.program_id:
        raise ValueError("compact manifest program_id does not match campaign config")
    producer_hash = str(raw.get("producer_config_hash"))
    if producer_hash != config.config_hash:
        raise ValueError(
            "compact manifest producer_config_hash does not match campaign config"
        )
    if str(raw.get("package_kind")) != "full_closeout":
        raise ValueError("A1 requires an R3A full_closeout source package")
    if raw.get("semantic_revalidation") is not True:
        raise ValueError("A1 requires semantic_revalidation=true")
    if raw.get("all_configured_probes_present") is not True:
        raise ValueError("A1 requires all configured R3A probes in the source package")
    producer_git = _mapping(raw.get("producer_git"), field="compact_manifest.producer_git")
    commit = str(producer_git.get("git_commit"))
    return {
        "program_id": str(raw["program_id"]),
        "package_kind": str(raw["package_kind"]),
        "campaign_mode": str(raw["campaign_mode"]),
        "producer_config_hash": producer_hash,
        "producer_git_commit": commit,
        "campaign_blocker": raw.get("campaign_blocker"),
        "accepted_reconstruction": bool(raw.get("accepted_reconstruction", False)),
        "semantic_revalidation": True,
        "raw_bundle_sha256": raw.get("raw_bundle_sha256"),
        "compact_manifest_sha256": _file_sha256(path),
        "source_campaign_id": (
            f"{raw['program_id']}:{raw['campaign_mode']}:{commit}"
        ),
    }


def _record_id(
    config: CampaignConfig,
    *,
    probe_id: str,
    leaf_id: str,
) -> str:
    return f"{config.program_id}:{config.config_hash[:12]}:{probe_id}:{leaf_id}"


def record_from_leaf(
    config: CampaignConfig,
    *,
    leaf: Mapping[str, Any],
    source_artifact: str,
    source_artifact_sha256: str,
) -> tuple[ExtractedMechanismRecord, GeometryRoundTripAudit]:
    """Convert one natural-leaf JSON record into one reconstructible E0 specimen."""

    problem = _leaf_problem_from_source_artifact(config, leaf)
    spec = _mapping(leaf["spec"], field="leaf.spec")
    probe_id = str(spec["probe_id"])
    leaf_id = str(spec["leaf_id"])
    rid = _record_id(config, probe_id=probe_id, leaf_id=leaf_id)
    geometry = geometry_record_from_uuru_problem(problem)
    audit = audit_geometry_roundtrip(
        rid,
        problem,
        sample_xs=_sample_xs(leaf),
        source_artifact_sha256=source_artifact_sha256,
    )
    if not audit.passed:
        raise ValueError(f"{rid}: E0 geometry round trip failed")

    component_status = str(
        leaf.get("leaf_component_status")
        or leaf.get("closed_mechanism_status")
        or "UNRESOLVED"
    )
    family = MechanismFamilyIdentity(
        family_id=str(leaf["child_family"]),
        parent_family_id=config.geometry.parent_family,
        joint_kind_sequence=tuple(str(v) for v in leaf["joint_kind_sequence"]),
        joint_role_sequence=tuple(str(v) for v in leaf["joint_role_sequence"]),
    )
    source = SourceProvenanceRecord(
        source_chain_id=config.geometry.architecture_id,
        fixed_position_problem_id=probe_id,
        source_component_id=UNRESOLVED_SOURCE_COMPONENT_ID,
        probe_id=probe_id,
        task_point=problem.p_star,
        source_artifact=source_artifact,
        leaf_id=leaf_id,
        construction_kind=str(leaf["construction_kind"]),
        chart_id=str(spec["chart_id"]),
        family_parameters=(("lambda", float(spec["lambda_fixed"])),),
        child_certificate_status=component_status,
        accepted_for_reconstruction=bool(
            leaf.get("accepted_for_reconstruction", False)
        ),
        provenance=MechanismProvenance.SOURCE_DERIVED_NATURAL_LEAF,
    )
    record = ExtractedMechanismRecord(
        record_id=rid,
        family=family,
        source=source,
        geometry=geometry,
        notes=(
            f"legacy_leaf_geometry_hash={spec['geometry_hash']}",
            (
                "R3A H12 does not provide an independent source-parent component ID; "
                "workspace evidence eligibility is therefore blocked."
            ),
        ),
    )
    return record, audit


def export_campaign(
    *,
    config_path: Path | str,
    campaign_dir: Path | str,
    outdir: Path | str | None = None,
    probe_ids: Sequence[str] | None = None,
) -> tuple[ExtractionManifest, dict[str, Any]]:
    """Export selected frozen R3A natural-family artifacts to the A0 E0 schema."""

    config = load_campaign_config(config_path)
    campaign = Path(campaign_dir)
    authority = _source_package_authority(config, campaign)
    selected = tuple(probe_ids) if probe_ids is not None else tuple(
        probe.probe_id for probe in config.probes
    )
    if len(selected) != len(set(selected)):
        raise ValueError("probe_ids must be unique")

    records: list[ExtractedMechanismRecord] = []
    audits: list[GeometryRoundTripAudit] = []
    for probe_id in selected:
        config.probe(probe_id)  # validation
        path = campaign / probe_id / "natural_family.json"
        if not path.is_file():
            raise FileNotFoundError(f"missing natural-family artifact {path}")
        artifact_hash = _file_sha256(path)
        payload = _mapping(
            json.loads(path.read_text(encoding="utf-8")),
            field=f"{probe_id}.natural_family",
        )
        if str(payload.get("probe_id")) != probe_id:
            raise ValueError(f"{path}: probe_id mismatch")
        source_artifact = f"{probe_id}/natural_family.json"
        for raw_leaf in payload.get("leaves", []):
            leaf = _mapping(raw_leaf, field=f"{probe_id}.leaf")
            record, audit = record_from_leaf(
                config,
                leaf=leaf,
                source_artifact=source_artifact,
                source_artifact_sha256=artifact_hash,
            )
            records.append(record)
            audits.append(audit)

    records.sort(key=lambda item: item.record_id)
    audits.sort(key=lambda item: item.record_id)
    manifest = ExtractionManifest(
        program_id=A1_PROGRAM_ID,
        source_campaign_id=str(authority["source_campaign_id"]),
        source_config_sha256=config.config_hash,
        records=tuple(records),
        notes=(
            "Downstream export of the frozen R3A package; no R3A numerical rerun.",
            (
                "Source-parent component identity is unresolved in H12 natural artifacts; "
                "current records are mechanism specimens, not workspace evidence."
            ),
        ),
    )
    status_counts = {
        status.value: sum(1 for item in audits if item.status is status)
        for status in RoundTripStatus
    }
    audit_report = {
        "program_id": A1_PROGRAM_ID,
        "source_package": authority,
        "record_count": len(records),
        "workspace_evidence_eligible_count": sum(
            int(item.workspace_evidence_eligible) for item in records
        ),
        "roundtrip_status_counts": status_counts,
        "roundtrip_failures": [
            item.record_id for item in audits if item.status is RoundTripStatus.FAIL
        ],
        "records": [item.to_json_dict() for item in audits],
        "notes": [
            "Round-trip audit is geometry/reconstruction evidence only.",
            "The H12 natural column remains scientifically uninterpreted.",
        ],
    }

    if outdir is not None:
        target = Path(outdir)
        target.mkdir(parents=True, exist_ok=True)
        (target / "e0_manifest.json").write_text(
            manifest.to_json_text(),
            encoding="utf-8",
        )
        (target / "e0_roundtrip_audit.json").write_text(
            json.dumps(
                audit_report,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
    return manifest, audit_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export frozen R3A natural UURU leaves into reconstructible E0 records."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument(
        "--probe",
        action="append",
        dest="probes",
        default=None,
        help="Optional probe id; repeat to export a subset.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest, audit = export_campaign(
        config_path=args.config,
        campaign_dir=args.campaign_dir,
        outdir=args.outdir,
        probe_ids=args.probes,
    )
    print(
        json.dumps(
            {
                "record_count": len(manifest.records),
                "family_counts": manifest.family_counts(),
                "workspace_evidence_eligible_count": sum(
                    int(item.workspace_evidence_eligible)
                    for item in manifest.records
                ),
                "roundtrip_status_counts": audit["roundtrip_status_counts"],
                "outdir": str(args.outdir),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
