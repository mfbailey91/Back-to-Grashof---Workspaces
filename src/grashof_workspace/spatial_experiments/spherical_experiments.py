"""Sprint 06 candidate spherical experiments ATR_EXP_032–035."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from .fiber_constraints import ALTERNATE_N, PRIMARY_N
from .fiber_continuation import FIBER_STEP_SIZE, FIBER_STEPS, continue_fiber
from .fiber_duplicates import DUPLICATE_TOL_RAD, SIGMA_DISTINCT_TOL, fiber_duplicate_report
from .spherical_invariants import (
    ARC_APPROX_RAD,
    ARC_DRIFT_TOL_RAD,
    BODY_FIXED_AXIS_TOL_RAD,
    CENTER_DRIFT_TOL_M,
    CONCURRENCY_APPROX_M,
    COORDINATE_LOCK_TOL_RAD,
    EFFECTIVE_RATE_TOL,
    GLOBAL_CONCURRENCY_TOL_M,
    PAIR_CENTER_TOL_M,
    exploratory_fixed_tuple_scan,
    fiber_spherical_invariants,
)

SOURCE_IDENTIFIER = "grashof_workspace.spatial_experiments.spherical_experiments:sprint06-v2"

CANDIDATES = (
    ("IntersectingPairsAligned6R", PRIMARY_N, "primary"),
    ("IntersectingPairsAligned6R", ALTERNATE_N, "alternate"),
    ("URLikeAligned6R", PRIMARY_N, "primary"),
    ("URLikeAligned6R", ALTERNATE_N, "alternate"),
)


def _architecture_pair(name: str) -> tuple[Any, tuple[float, ...]]:
    if name == "IntersectingPairsAligned6R":
        return IntersectingPairsAligned6R.aligned().chain, INTERSECTING_PAIRS_REGULAR_Q
    if name == "URLikeAligned6R":
        return URLikeAligned6R.aligned().chain, URLIKE_REGULAR_Q
    raise ValueError(name)


def _candidate_duplicate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for architecture, n, label in CANDIDATES:
        chain, q0 = _architecture_pair(architecture)
        segment = continue_fiber(chain, q0, n)
        report = fiber_duplicate_report(segment)
        rows.append(
            {
                "architecture": architecture,
                "fiber": label,
                "n": list(n),
                "n_stations": report.n_stations,
                "n_pairs_checked": report.n_pairs_checked,
                "n_duplicates": report.n_duplicates,
                "min_nn_distance": report.min_nn_distance,
                "passed": report.passed,
                "duplicate_pairs": [list(item) for item in report.duplicate_pairs],
            }
        )
    return rows


def evaluate_duplicate_scan() -> dict[str, Any]:
    rows = _candidate_duplicate_rows()
    ok = all(bool(row["passed"]) for row in rows)
    return {
        "experiment_id": "ATR_EXP_032",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "All four candidate fibers have no wrap-equivalent repeats at distinct σ "
            f"(tol={DUPLICATE_TOL_RAD:g} rad)"
        ),
        "observed": "; ".join(
            f"{row['architecture']}/{row['fiber']}: stations={row['n_stations']}, "
            f"dups={row['n_duplicates']}, min_nn={row['min_nn_distance']:.3e}, passed={row['passed']}"
            for row in rows
        ),
        "metrics": {
            "candidates": rows,
            "duplicate_tol_rad": DUPLICATE_TOL_RAD,
            "sigma_distinct_tol": SIGMA_DISTINCT_TOL,
        },
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "n": list(PRIMARY_N),
        "architecture": "all_four_candidates",
    }


def _ip_invariants(exp_id: str, n: tuple[float, float, float], fiber: str) -> dict[str, Any]:
    chain, q0 = _architecture_pair("IntersectingPairsAligned6R")
    segment = continue_fiber(chain, q0, n)
    duplicates = fiber_duplicate_report(segment)
    if not duplicates.passed:
        return {
            "experiment_id": exp_id,
            "status": "PASS",
            "expected": "Named residual report: exact, approximate, fail, or unresolved",
            "observed": (
                f"IntersectingPairsAligned6R/{fiber}: unresolved — duplicate scan failed "
                f"(dups={duplicates.n_duplicates})"
            ),
            "metrics": {
                "fiber": fiber,
                "verdict": "unresolved",
                "reason": "duplicate_configurations",
                "duplicates": asdict(duplicates),
                "locking": "unresolved",
            },
            "q": list(q0),
            "n": list(n),
            "architecture": "IntersectingPairsAligned6R",
        }
    report = fiber_spherical_invariants(
        chain,
        segment,
        architecture="IntersectingPairsAligned6R",
        n=n,
    )
    return {
        "experiment_id": exp_id,
        "status": "PASS",
        "expected": (
            "Named residual report for S-UA-UB-R5: exact, approximate, fail, or unresolved "
            "using global c*, fixed-center drift, arcs, and body-fixed axis legitimacy"
        ),
        "observed": (
            f"IntersectingPairsAligned6R/{fiber}: verdict={report.verdict}, "
            f"c*_rms={report.global_rms_m:.3e} m, c*_max={report.global_max_m:.3e} m, "
            f"drift={report.max_center_drift_m:.3e} m, arc={report.max_arc_residual_rad:.3e} rad, "
            f"body_fixed={report.max_body_fixed_drift_rad:.3e} rad, "
            f"simple_lock={report.simple_lock_passed}, locking={report.locking}"
        ),
        "metrics": {
            "fiber": fiber,
            "verdict": report.verdict,
            "construction": report.construction,
            "global_center": report.global_center,
            "global_rms_m": report.global_rms_m,
            "global_max_m": report.global_max_m,
            "max_center_drift_m": report.max_center_drift_m,
            "max_arc_residual_rad": report.max_arc_residual_rad,
            "max_body_fixed_drift_rad": report.max_body_fixed_drift_rad,
            "simple_lock_ranges": list(report.simple_lock_ranges),
            "simple_lock_passed": report.simple_lock_passed,
            "locking_policy": report.locking_policy,
            "locking": report.locking,
            "n_stations": report.n_stations,
            "stations": [asdict(station) for station in report.stations],
            "thresholds": {
                "duplicate_tol_rad": DUPLICATE_TOL_RAD,
                "pair_center_tol_m": PAIR_CENTER_TOL_M,
                "effective_rate_tol": EFFECTIVE_RATE_TOL,
                "global_concurrency_tol_m": GLOBAL_CONCURRENCY_TOL_M,
                "center_drift_tol_m": CENTER_DRIFT_TOL_M,
                "arc_drift_tol_rad": ARC_DRIFT_TOL_RAD,
                "body_fixed_axis_tol_rad": BODY_FIXED_AXIS_TOL_RAD,
                "coordinate_lock_tol_rad": COORDINATE_LOCK_TOL_RAD,
                "concurrency_approx_m": CONCURRENCY_APPROX_M,
                "arc_approx_rad": ARC_APPROX_RAD,
            },
        },
        "q": list(q0),
        "n": list(n),
        "architecture": "IntersectingPairsAligned6R",
    }


def evaluate_ip_primary_invariants() -> dict[str, Any]:
    return _ip_invariants("ATR_EXP_033", PRIMARY_N, "primary")


def evaluate_ip_alternate_invariants() -> dict[str, Any]:
    return _ip_invariants("ATR_EXP_034", ALTERNATE_N, "alternate")


def evaluate_urlike_parallel() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for n, fiber in ((PRIMARY_N, "primary"), (ALTERNATE_N, "alternate")):
        chain, q0 = _architecture_pair("URLikeAligned6R")
        segment = continue_fiber(chain, q0, n)
        duplicates = fiber_duplicate_report(segment)
        exploratory = exploratory_fixed_tuple_scan(chain, segment) if duplicates.passed else ()
        best = min(exploratory, key=lambda item: item.global_max_m) if exploratory else None
        rows.append(
            {
                "architecture": "URLikeAligned6R",
                "fiber": fiber,
                "n": list(n),
                "duplicate_passed": duplicates.passed,
                "n_duplicates": duplicates.n_duplicates,
                "min_nn_distance": duplicates.min_nn_distance,
                "n_stations": duplicates.n_stations,
                "axes_construction": "exploratory_fixed_physical_subset",
                "exact_rrrr_claim": False,
                "reason": "no_topology_derived_ua_ub_parent",
                "best_tuple": asdict(best) if best is not None else None,
                "tuples": [asdict(item) for item in exploratory],
            }
        )
    ok = all(bool(row["duplicate_passed"]) for row in rows)
    return {
        "experiment_id": "ATR_EXP_035",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "UR-like duplicate scans plus exploratory fixed R1–R5 four-subset diagnostics; "
            "no exact RRRR claim; no SUUR required"
        ),
        "observed": "; ".join(
            f"{row['fiber']}: dups={row['n_duplicates']}, dup_passed={row['duplicate_passed']}, "
            f"best={row['best_tuple']['label'] if row['best_tuple'] else 'none'} "
            f"max={row['best_tuple']['global_max_m']:.3e} m"
            if row["best_tuple"]
            else f"{row['fiber']}: dups={row['n_duplicates']}, dup_passed={row['duplicate_passed']}"
            for row in rows
        ),
        "metrics": {
            "candidates": rows,
            "suur_required": False,
            "axes_construction": "exploratory_fixed_physical_subset",
            "exact_rrrr_claim": False,
        },
        "q": list(URLIKE_REGULAR_Q),
        "n": list(PRIMARY_N),
        "architecture": "URLikeAligned6R",
    }


def run_all_spherical_experiments(repo_root: Path) -> list[dict[str, Any]]:
    provenance = _git_provenance(repo_root)
    results = [
        evaluate_duplicate_scan(),
        evaluate_ip_primary_invariants(),
        evaluate_ip_alternate_invariants(),
        evaluate_urlike_parallel(),
    ]
    for result in results:
        write_spherical_artifacts(repo_root, result, provenance=provenance)
    return results


def write_spherical_artifacts(
    repo_root: Path,
    result: dict[str, Any],
    *,
    provenance: tuple[str, bool] | None = None,
) -> Path:
    exp_id = str(result["experiment_id"])
    out = repo_root / "results" / "aligned_terminal_roll" / exp_id
    out.mkdir(parents=True, exist_ok=True)
    commit, dirty = provenance if provenance is not None else _git_provenance(repo_root)
    source_path = Path(__file__).resolve()
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    config = {
        "source_identifier": SOURCE_IDENTIFIER,
        "experiment_id": exp_id,
        "metrics": {
            key: value
            for key, value in result.get("metrics", {}).items()
            if key not in {"candidates", "stations", "duplicates"}
        },
        "seed_configuration": result.get("q"),
        "n": result.get("n", list(PRIMARY_N)),
        "step_sizes": {"dsigma": FIBER_STEP_SIZE},
        "n_steps": FIBER_STEPS,
        "tolerances": {
            "duplicate_tol_rad": DUPLICATE_TOL_RAD,
            "sigma_distinct_tol": SIGMA_DISTINCT_TOL,
            "pair_center_tol_m": PAIR_CENTER_TOL_M,
            "effective_rate_tol": EFFECTIVE_RATE_TOL,
            "global_concurrency_tol_m": GLOBAL_CONCURRENCY_TOL_M,
            "center_drift_tol_m": CENTER_DRIFT_TOL_M,
            "arc_drift_tol_rad": ARC_DRIFT_TOL_RAD,
            "body_fixed_axis_tol_rad": BODY_FIXED_AXIS_TOL_RAD,
            "coordinate_lock_tol_rad": COORDINATE_LOCK_TOL_RAD,
            "concurrency_approx_m": CONCURRENCY_APPROX_M,
            "arc_approx_rad": ARC_APPROX_RAD,
        },
    }
    config_sha = hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()
    slim = {key: value for key, value in result.items()}
    manifest = {
        "experiment_id": exp_id,
        "repository_commit": commit,
        "working_tree_dirty": dirty,
        "source_identifier": SOURCE_IDENTIFIER,
        "source_file_sha256": source_sha,
        "experiment_configuration_sha256": config_sha,
        "architecture_parameters": result.get("architecture", "mixed"),
        "seed_configuration": result.get("q"),
        "n": result.get("n", list(PRIMARY_N)),
        "alternate_n": list(ALTERNATE_N),
        "step_sizes": config["step_sizes"],
        "n_steps": FIBER_STEPS,
        "status": result["status"],
        "expected": result["expected"],
        "observed": result["observed"],
        "units": {"length": "metre", "angle": "radian"},
        "result": slim,
        "software_version": "grashof-workspace spatial_experiments sprint06",
    }
    _write_kv_csv(out / "metrics.csv", result["metrics"])
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=_json_default) + "\n", encoding="utf-8"
    )
    (out / "summary.md").write_text(
        "\n".join(
            [
                f"# {exp_id}",
                "",
                f"**Status:** {result['status']}",
                f"**Commit:** {commit}",
                f"**Working tree dirty:** {dirty}",
                f"**Source:** {SOURCE_IDENTIFIER}",
                "",
                "## Expected",
                "",
                str(result["expected"]),
                "",
                "## Observed",
                "",
                str(result["observed"]),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return out


def _git_provenance(repo_root: Path) -> tuple[str, bool]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True
        )
        relevant = []
        for line in status.splitlines():
            path = line[3:].split(" -> ")[-1]
            if path.endswith((".DS_Store", ".patch")):
                continue
            if path.startswith("results/aligned_terminal_roll/"):
                continue
            relevant.append(line)
        return commit, bool(relevant)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown", True


def _write_kv_csv(path: Path, metrics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        for key, value in metrics.items():
            writer.writerow([key, json.dumps(value, default=_json_default)])


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    raise TypeError(type(value))
