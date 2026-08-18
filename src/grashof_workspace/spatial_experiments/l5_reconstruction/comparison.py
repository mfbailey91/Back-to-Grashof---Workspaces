"""Five-point three-way pointing-image comparison on the confirmation sphere."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3

from .direct_truth import build_direct_reference_cells
from .models import (
    CampaignConfig,
    CampaignMode,
    CellClass,
    CompletenessLabel,
    DirectReferenceCell,
    FivePointCampaignResult,
    FixedPointProbe,
    OracleFeasibility,
    PointingSetMetrics,
    PointingSolveStatus,
    PointingTargetSolve,
    ProcessStageStatus,
    ReconstructionDisposition,
    ThreeWayReconstructionResult,
    empty_stage_statuses,
    json_dumps_strict,
    stage_envelope,
)
from .positive_control import point_completeness_oracle
from .sphere_grid import (
    SphereGrid,
    build_sphere_grid,
    classify_cells,
    paint_pointings,
    pointing_geodesic,
)


def _fraction(num: int, den: int) -> float | None:
    if den <= 0:
        return None
    return float(num) / float(den)


def pointing_set_metrics(
    labels: tuple[CellClass, ...],
    reconstructed_hits: tuple[bool, ...],
    *,
    max_cell_diameter_rad: float,
    reconstructed_dirs: tuple[tuple[float, float, float], ...],
    covered_dirs: tuple[tuple[float, float, float], ...],
    refinement_delta: float | None = None,
) -> PointingSetMetrics:
    if len(labels) != len(reconstructed_hits):
        raise ValueError("hit mask length must match cell labels")
    strict_cov = [i for i, lab in enumerate(labels) if lab is CellClass.STRICT_COVERED]
    strict_unc = [i for i, lab in enumerate(labels) if lab is CellClass.STRICT_UNCOVERED]
    hit_cov = sum(1 for i in strict_cov if reconstructed_hits[i])
    miss_cov = len(strict_cov) - hit_cov
    false_pos = sum(1 for i in strict_unc if reconstructed_hits[i])
    hausdorff: float | None = None
    if reconstructed_dirs and covered_dirs:
        d_ab = max(min(pointing_geodesic(a, b) for b in covered_dirs) for a in reconstructed_dirs)
        d_ba = max(min(pointing_geodesic(b, a) for a in reconstructed_dirs) for b in covered_dirs)
        hausdorff = max(d_ab, d_ba)
    unresolved = sum(1 for lab in labels if lab is CellClass.AMBIGUOUS_BOUNDARY)
    return PointingSetMetrics(
        strict_covered_count=len(strict_cov),
        strict_uncovered_count=len(strict_unc),
        reconstructed_hit_count=int(sum(reconstructed_hits)),
        missed_covered_fraction=_fraction(miss_cov, len(strict_cov)),
        false_positive_fraction=_fraction(false_pos, len(strict_unc)),
        hausdorff_rad=hausdorff,
        boundary_disagreement_fraction=_fraction(unresolved, len(labels)),
        unresolved_fraction=float(unresolved) / float(max(1, len(labels))),
        max_cell_diameter_rad=max_cell_diameter_rad,
        refinement_delta=refinement_delta,
    )


def reconstruction_pass(metrics: PointingSetMetrics | None, config: CampaignConfig) -> bool:
    """Declared-resolution set gate. ``None`` never means pass."""
    if metrics is None:
        return False
    if metrics.reconstructed_hit_count <= 0:
        return False
    if metrics.missed_covered_fraction is None:
        return False
    if metrics.missed_covered_fraction > config.max_missed_strict_covered_fraction:
        return False
    if metrics.false_positive_fraction is None:
        return False
    if metrics.false_positive_fraction > config.max_strict_false_positive_fraction:
        return False
    if metrics.hausdorff_rad is None:
        return False
    hausdorff_limit = (
        config.max_hausdorff_in_confirmation_cell_diameters * metrics.max_cell_diameter_rad
    )
    if metrics.hausdorff_rad > hausdorff_limit:
        return False
    if metrics.refinement_delta is None:
        return False
    return metrics.refinement_delta <= config.max_refinement_metric_delta


def evaluate_reconstruction_gates(
    *,
    direct_vs_oracle: PointingSetMetrics | None,
    source_vs_direct: PointingSetMetrics | None,
    natural_vs_direct: PointingSetMetrics | None,
    source_vs_oracle: PointingSetMetrics | None,
    natural_vs_oracle: PointingSetMetrics | None,
    config: CampaignConfig,
) -> tuple[bool, bool, bool, bool, bool]:
    return (
        reconstruction_pass(direct_vs_oracle, config),
        reconstruction_pass(source_vs_direct, config),
        reconstruction_pass(natural_vs_direct, config),
        reconstruction_pass(source_vs_oracle, config),
        reconstruction_pass(natural_vs_oracle, config),
    )


def _set_gate_failure(
    metrics: PointingSetMetrics | None,
    config: CampaignConfig,
    prefix: str,
) -> tuple[ReconstructionDisposition, str]:
    if metrics is None:
        return ReconstructionDisposition.UNRESOLVED, f"{prefix} missing reconstruction metrics"
    if metrics.reconstructed_hit_count <= 0:
        return ReconstructionDisposition.PARTIAL, f"{prefix} empty reconstruction cannot pass"
    fp = metrics.false_positive_fraction
    if fp is not None and fp > config.max_strict_false_positive_fraction:
        return ReconstructionDisposition.REJECTED, f"{prefix} strict false positives"
    return ReconstructionDisposition.PARTIAL, f"{prefix} set reconstruction gate failed"


def classification_matches_oracle(
    point_classification: CompletenessLabel,
    expected_complete: bool,
) -> bool:
    if expected_complete:
        return point_classification is CompletenessLabel.COMPLETE
    return point_classification is CompletenessLabel.PARTIAL


def campaign_reconstruction_accepted(
    comparisons: Sequence[ThreeWayReconstructionResult],
    probes: Sequence[FixedPointProbe],
    budgets: CampaignMode,
    *,
    require_classification_match: bool = True,
) -> bool:
    if not budgets.allows_full_campaign_disposition:
        return False
    if len(comparisons) != len(probes):
        return False
    by_id = {item.probe_id: item for item in comparisons}
    for probe in probes:
        result = by_id.get(probe.probe_id)
        if result is None:
            return False
        if result.disposition is not ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION:
            return False
        if require_classification_match and not classification_matches_oracle(
            result.point_classification, probe.expected_pointing_complete
        ):
            return False
    return True


def _load_hits_and_dirs(path: Path) -> tuple[tuple[bool, ...], tuple[tuple[float, float, float], ...]]:
    blob = json.loads(path.read_text(encoding="utf-8"))
    dirs_raw = blob.get("pointing_samples", [])
    dirs = tuple(as_vec3(item) for item in dirs_raw)
    hits_raw = blob.get("hit_cells")
    if hits_raw is None:
        return (), dirs
    hits = tuple(bool(v) for v in hits_raw)
    return hits, dirs


def resolved_direct_mask(cells: tuple[DirectReferenceCell, ...]) -> tuple[bool, ...]:
    return tuple(cell.direct_status is PointingSolveStatus.FOUND for cell in cells)


def direct_reference_labels(cells: tuple[DirectReferenceCell, ...]) -> tuple[CellClass, ...]:
    labels: list[CellClass] = []
    for cell in cells:
        if not cell.strict_reference_eligible:
            labels.append(CellClass.AMBIGUOUS_BOUNDARY)
        elif cell.direct_status is PointingSolveStatus.FOUND:
            labels.append(CellClass.STRICT_COVERED)
        else:
            labels.append(CellClass.STRICT_UNCOVERED)
    return tuple(labels)


def direct_complete_from_cells(cells: tuple[DirectReferenceCell, ...]) -> bool | None:
    strict = [cell for cell in cells if cell.oracle_status is not OracleFeasibility.BOUNDARY]
    if any(cell.direct_status is PointingSolveStatus.UNRESOLVED for cell in strict):
        return None
    for cell in strict:
        if cell.oracle_status is OracleFeasibility.FEASIBLE and cell.direct_status is not PointingSolveStatus.FOUND:
            return False
        if cell.oracle_status is OracleFeasibility.INFEASIBLE and cell.direct_status is PointingSolveStatus.FOUND:
            return False
    return True


def classify_point(
    oracle_complete: bool,
    metrics: PointingSetMetrics | None,
    config: CampaignConfig,
) -> tuple[CompletenessLabel, ReconstructionDisposition, str]:
    if metrics is None:
        return CompletenessLabel.PARTIAL, ReconstructionDisposition.UNRESOLVED, "missing reconstruction metrics"
    if not reconstruction_pass(metrics, config):
        if not oracle_complete and metrics.strict_uncovered_count == 0:
            return (
                CompletenessLabel.PARTIAL,
                ReconstructionDisposition.UNRESOLVED,
                "negative probe has no strict uncovered cells",
            )
        disposition, reason = _set_gate_failure(metrics, config, "set reconstruction")
        return CompletenessLabel.PARTIAL, disposition, reason
    if oracle_complete:
        return (
            CompletenessLabel.COMPLETE,
            ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION,
            "positive complete at declared resolution",
        )
    return (
        CompletenessLabel.PARTIAL,
        ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION,
        "negative probe recovered feasible subset and excluded infeasible cells",
    )


def classify_probe_reconstruction(
    *,
    oracle_complete: bool,
    expected_complete: bool,
    direct_complete: bool | None,
    direct_vs_oracle: PointingSetMetrics | None,
    source_vs_direct: PointingSetMetrics | None,
    natural_vs_direct: PointingSetMetrics | None,
    source_vs_oracle: PointingSetMetrics | None,
    natural_vs_oracle: PointingSetMetrics | None,
    unresolved_family_intervals: tuple[tuple[float, float], ...],
    unresolved_c_intervals: tuple[tuple[float, float], ...],
    config: CampaignConfig,
) -> tuple[CompletenessLabel, ReconstructionDisposition, str]:
    if direct_complete is None:
        return (
            CompletenessLabel.PARTIAL,
            ReconstructionDisposition.UNRESOLVED,
            "strict confirmation unresolved cells block point classification",
        )
    if not reconstruction_pass(direct_vs_oracle, config):
        disposition, reason = _set_gate_failure(
            direct_vs_oracle, config, "direct strict agreement failed; not attributed to the decomposition"
        )
        return CompletenessLabel.PARTIAL, disposition, reason
    source_ok = reconstruction_pass(source_vs_direct, config) and reconstruction_pass(source_vs_oracle, config)
    if unresolved_c_intervals or not source_ok:
        failed = source_vs_direct if not reconstruction_pass(source_vs_direct, config) else source_vs_oracle
        if unresolved_c_intervals:
            return (
                CompletenessLabel.PARTIAL,
                ReconstructionDisposition.UNRESOLVED,
                "source-control reconstruction failed; unresolved c interval; not attributed to the decomposition",
            )
        disposition, _reason = _set_gate_failure(
            failed, config, "source-control reconstruction failed; not attributed to the decomposition"
        )
        return CompletenessLabel.PARTIAL, disposition, _reason
    if unresolved_family_intervals:
        return (
            CompletenessLabel.PARTIAL,
            ReconstructionDisposition.UNRESOLVED,
            "blocking unresolved family lambda interval",
        )
    natural_ok = reconstruction_pass(natural_vs_direct, config) and reconstruction_pass(natural_vs_oracle, config)
    if not natural_ok:
        failed = natural_vs_direct if not reconstruction_pass(natural_vs_direct, config) else natural_vs_oracle
        disposition, reason = _set_gate_failure(failed, config, "natural-leaf reconstruction failed against direct reference")
        return CompletenessLabel.PARTIAL, disposition, reason
    label, disposition, reason = classify_point(oracle_complete, natural_vs_oracle, config)
    if not classification_matches_oracle(label, expected_complete):
        return (
            label,
            ReconstructionDisposition.REJECTED,
            "point classification does not match oracle",
        )
    return label, disposition, reason


def _interval_pairs(raw: object) -> tuple[tuple[float, float], ...]:
    if not isinstance(raw, list):
        return ()
    out: list[tuple[float, float]] = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            out.append((float(item[0]), float(item[1])))
    return tuple(out)


def _require_compare_artifacts(outdir: Path, probes: list[FixedPointProbe]) -> None:
    missing: list[str] = []
    for probe in probes:
        for name in ("direct_truth.json", "source_control.json", "natural_family.json"):
            path = outdir / probe.probe_id / name
            if not path.is_file():
                missing.append(str(path))
    if missing:
        raise FileNotFoundError("missing compare inputs: " + ", ".join(missing))


def _solve_stub(item: dict[str, Any]) -> PointingTargetSolve:
    pos = item.get("best_position_residual_m")
    geo = item.get("best_pointing_geodesic_rad")
    return PointingTargetSolve(
        target_index=int(item["target_index"]),
        d_target=as_vec3(item["d_target"]),
        status=PointingSolveStatus(str(item["status"])),
        clusters=(),
        best_position_residual_m=None if pos is None else float(pos),
        best_pointing_geodesic_rad=None if geo is None else float(geo),
        n_starts=int(item.get("n_starts", 0)),
    )


def _load_confirmation_cells(
    truth: dict[str, Any],
    grid: SphereGrid,
    labels: tuple[CellClass, ...],
) -> tuple[DirectReferenceCell, ...]:
    raw = truth.get("confirmation_cells")
    if isinstance(raw, list) and raw:
        cells = tuple(DirectReferenceCell.from_json_dict(item) for item in raw if isinstance(item, dict))
        if len(cells) == len(labels):
            return cells
    confirmation = truth.get("confirmation", {})
    solves_raw = confirmation.get("solves", []) if isinstance(confirmation, dict) else []
    solves = tuple(_solve_stub(item) for item in solves_raw if isinstance(item, dict))
    return build_direct_reference_cells(grid, labels, solves)


def write_compare_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
) -> dict[str, Any]:
    _require_compare_artifacts(outdir, probes)
    budgets = config.mode(mode)
    grid = build_sphere_grid(budgets.confirmation_icosphere_level)
    comparisons: list[ThreeWayReconstructionResult] = []
    probe_ids = tuple(p.probe_id for p in probes)
    for probe in probes:
        oracle = point_completeness_oracle(
            config.geometry, probe.p_star, margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m
        )
        labels = classify_cells(
            grid,
            config.geometry,
            probe.p_star,
            margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m,
        )
        src_path = outdir / probe.probe_id / "source_control.json"
        nat_path = outdir / probe.probe_id / "natural_family.json"
        truth_path = outdir / probe.probe_id / "direct_truth.json"
        src_hits, src_dirs = _load_hits_and_dirs(src_path)
        if src_hits and len(src_hits) != len(labels):
            src_hits = ()
        if not src_hits:
            src_hits = paint_pointings(grid, src_dirs) if src_dirs else tuple(False for _ in labels)
        fam = json.loads(nat_path.read_text(encoding="utf-8"))
        src_blob = json.loads(src_path.read_text(encoding="utf-8"))
        unresolved_lambda = _interval_pairs(fam.get("unresolved_lambda_intervals"))
        unresolved_c = _interval_pairs(src_blob.get("unresolved_c_intervals"))
        dirs: list[tuple[float, float, float]] = []
        for leaf in fam.get("leaves", []):
            if not leaf.get("accepted_for_reconstruction"):
                continue
            for sample in leaf.get("samples", []):
                dirs.append(as_vec3(sample["pointing"]))
        nat_dirs = tuple(dirs)
        nat_hits = paint_pointings(grid, nat_dirs) if nat_dirs else tuple(False for _ in labels)
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        cells = _load_confirmation_cells(truth, grid, labels)
        direct_hits = resolved_direct_mask(cells)
        direct_labels = direct_reference_labels(cells)
        oracle_covered = tuple(
            as_vec3(grid.barycenters[i]) for i, lab in enumerate(labels) if lab is CellClass.STRICT_COVERED
        )
        direct_covered = tuple(
            cell.vertex_or_barycenter_direction for cell in cells if cell.direct_status is PointingSolveStatus.FOUND
        )
        direct_dirs = tuple(
            cell.vertex_or_barycenter_direction for cell in cells if cell.direct_status is PointingSolveStatus.FOUND
        )
        src_vs_oracle = pointing_set_metrics(
            labels,
            src_hits,
            max_cell_diameter_rad=grid.max_cell_diameter_rad,
            reconstructed_dirs=src_dirs,
            covered_dirs=oracle_covered,
        )
        nat_vs_oracle = pointing_set_metrics(
            labels,
            nat_hits,
            max_cell_diameter_rad=grid.max_cell_diameter_rad,
            reconstructed_dirs=nat_dirs,
            covered_dirs=oracle_covered,
        )
        direct_vs_oracle = pointing_set_metrics(
            labels,
            direct_hits,
            max_cell_diameter_rad=grid.max_cell_diameter_rad,
            reconstructed_dirs=direct_dirs,
            covered_dirs=oracle_covered,
        )
        src_vs_direct = pointing_set_metrics(
            direct_labels,
            src_hits,
            max_cell_diameter_rad=grid.max_cell_diameter_rad,
            reconstructed_dirs=src_dirs,
            covered_dirs=direct_covered,
        )
        nat_vs_direct = pointing_set_metrics(
            direct_labels,
            nat_hits,
            max_cell_diameter_rad=grid.max_cell_diameter_rad,
            reconstructed_dirs=nat_dirs,
            covered_dirs=direct_covered,
        )
        direct_complete = direct_complete_from_cells(cells)
        label, disp, reason = classify_probe_reconstruction(
            oracle_complete=oracle.complete,
            expected_complete=probe.expected_pointing_complete,
            direct_complete=direct_complete,
            direct_vs_oracle=direct_vs_oracle,
            source_vs_direct=src_vs_direct,
            natural_vs_direct=nat_vs_direct,
            source_vs_oracle=src_vs_oracle,
            natural_vs_oracle=nat_vs_oracle,
            unresolved_family_intervals=unresolved_lambda,
            unresolved_c_intervals=unresolved_c,
            config=config,
        )
        excluded = tuple(
            str(leaf.get("closed_mechanism_status"))
            for leaf in fam.get("leaves", [])
            if not leaf.get("accepted_for_reconstruction")
        )
        result = ThreeWayReconstructionResult(
            probe_id=probe.probe_id,
            oracle_complete=oracle.complete,
            direct_complete=direct_complete,
            source_control_metrics=src_vs_oracle,
            natural_leaf_metrics=nat_vs_oracle,
            point_classification=label,
            disposition=disp,
            failure_localization=reason,
            excluded_child_dispositions=excluded,
            direct_vs_oracle=direct_vs_oracle,
            source_vs_direct=src_vs_direct,
            natural_vs_direct=nat_vs_direct,
        )
        path = outdir / probe.probe_id / "comparison.json"
        path.write_text(json_dumps_strict(result.to_json_dict()), encoding="utf-8")
        comparisons.append(result)
    require_match = bool(
        config.raw.get("set_acceptance", {}).get("require_all_five_point_classifications_match_oracle", True)
    )
    accepted = campaign_reconstruction_accepted(
        comparisons,
        config.probes,
        budgets,
        require_classification_match=require_match,
    )
    notes = ["R3A three-way comparison at declared confirmation resolution."]
    if not budgets.allows_full_campaign_disposition:
        notes.append("Mode does not allow full-campaign disposition.")
    if not accepted:
        notes.append("Reconstruction is not accepted at this declared resolution.")
    campaign = FivePointCampaignResult(
        program_id=config.program_id,
        config_hash=config.config_hash,
        probe_ids=probe_ids,
        stage_statuses={**empty_stage_statuses(), "compare": ProcessStageStatus.COMPLETE.value},
        comparisons=tuple(comparisons),
        disposition=(
            ReconstructionDisposition.PASS_AT_DECLARED_RESOLUTION
            if accepted
            else ReconstructionDisposition.PARTIAL
        ),
        accepted_reconstruction=accepted,
        notes=tuple(notes),
    )
    payload = campaign.to_json_dict()
    payload.update(stage_envelope(config, stage="compare", mode=mode, probe_ids=probe_ids))
    (outdir / "campaign.json").write_text(json_dumps_strict(payload), encoding="utf-8")
    (outdir / "compare.json").write_text(json_dumps_strict(payload), encoding="utf-8")
    return payload
