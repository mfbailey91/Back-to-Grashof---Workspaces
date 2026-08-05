"""Sprint 05 one-dimensional fiber experiments ATR_EXP_027–031."""

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
from .chart_diagnostics import REVERSE_JOINT_TOL_RAD
from .continuation import (
    MAX_CORRECTOR_ITERS,
    MAX_MICROSTEP,
    MAX_STEP_REDUCTIONS,
    POSITION_RESIDUAL_TOL_M,
)
from .fiber_constraints import (
    ALTERNATE_N,
    DH_DQ6_TOL,
    JOINT_FREEZE_INDEX,
    PRIMARY_N,
    SCALAR_RESIDUAL_TOL,
    fiber_independence_report,
)
from .fiber_continuation import (
    FIBER_STEP_SIZE,
    FIBER_STEPS,
    continue_fiber,
    continue_fiber_ray,
    continue_joint_freeze_ray,
)
from .fiber_diagnostics import (
    FIBER_REVERSE_POINTING_TOL,
    fiber_forward_reverse,
    fiber_paths_distinct,
    pointing_image_report,
    shared_sigma_agreement,
)
from .jacobians import ABS_RANK_TOL, REL_RANK_TOL

SOURCE_IDENTIFIER = "grashof_workspace.spatial_experiments.fiber_experiments:sprint05-v1"

CSV_FIELDS = [
    "architecture",
    "experiment_id",
    "sigma",
    "path_id",
    "step_index",
    "q1",
    "q2",
    "q3",
    "q4",
    "q5",
    "q6",
    "d_x",
    "d_y",
    "d_z",
    "position_residual_m",
    "h_residual",
    "corrector_iterations",
    "correction_norm",
    "step_reductions",
    "rank_jf",
    "nullity_jf",
    "regular",
    "label",
]


def _architecture_pair(name: str) -> tuple[Any, tuple[float, ...], str]:
    if name == "IntersectingPairsAligned6R":
        return IntersectingPairsAligned6R.aligned().chain, INTERSECTING_PAIRS_REGULAR_Q, name
    if name == "URLikeAligned6R":
        return URLikeAligned6R.aligned().chain, URLIKE_REGULAR_Q, name
    raise ValueError(name)


def evaluate_independence() -> dict[str, Any]:
    reports = []
    ok = True
    for arch in ("IntersectingPairsAligned6R", "URLikeAligned6R"):
        chain, q0, label = _architecture_pair(arch)
        report = fiber_independence_report(chain, q0, PRIMARY_N)
        row = asdict(report)
        row["architecture"] = label
        reports.append(row)
        ok = ok and report.independent and report.dh_dq6_vanishes
    return {
        "experiment_id": "ATR_EXP_027",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "Primary h=n·d is independent at both regular seeds: rank 4 / nullity 1 and dh/dq6=0"
        ),
        "observed": "; ".join(
            f"{row['architecture']}: rank={row['rank']}, null={row['nullity']}, "
            f"dh_dq6={row['dh_dq6']:.3e}, independent={row['independent']}"
            for row in reports
        ),
        "metrics": {
            "reports": reports,
            "n": list(PRIMARY_N),
            "dh_dq6_tol": DH_DQ6_TOL,
        },
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "n": list(PRIMARY_N),
    }


def _segment_eval(exp_id: str, architecture: str, n: tuple[float, float, float]) -> dict[str, Any]:
    chain, q0, label = _architecture_pair(architecture)
    segment = continue_fiber(chain, q0, n, n_steps=FIBER_STEPS, step_size=FIBER_STEP_SIZE)
    reverse = fiber_forward_reverse(
        chain, q0, n, n_steps=FIBER_STEPS, step_size=FIBER_STEP_SIZE, architecture=label
    )
    image = pointing_image_report(segment.accepted_samples)
    n_failed = sum(1 for step in (*segment.plus.steps, *segment.minus.steps) if not step.accepted)
    n_regular = sum(1 for step in segment.accepted_samples if step.regular)
    ok = n_failed == 0 and n_regular == len(segment.accepted_samples) and reverse.passed and image.passed
    rows = []
    for step in segment.accepted_samples:
        assert step.q is not None and step.d is not None
        rows.append(
            {
                "architecture": label,
                "experiment_id": exp_id,
                "sigma": step.sigma,
                "path_id": step.path_id,
                "step_index": step.step_index,
                "q1": step.q[0],
                "q2": step.q[1],
                "q3": step.q[2],
                "q4": step.q[3],
                "q5": step.q[4],
                "q6": step.q[5],
                "d_x": step.d[0],
                "d_y": step.d[1],
                "d_z": step.d[2],
                "position_residual_m": step.p_residual_m,
                "h_residual": step.h_residual,
                "corrector_iterations": step.corrector_iterations,
                "correction_norm": step.correction_norm,
                "step_reductions": step.step_reductions,
                "rank_jf": step.rank_jf,
                "nullity_jf": step.nullity_jf,
                "regular": step.regular,
                "label": step.label,
            }
        )
    return {
        "experiment_id": exp_id,
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "Sequential ±σ fiber is regular, reversible from the endpoint, and has a noncollapsed "
            "pointing image with a nonzero local tangent"
        ),
        "observed": (
            f"{label}: n_accepted={len(segment.accepted_samples)}, n_failed={n_failed}, "
            f"reverse_eq={reverse.epsilon_q:.3e}, reverse_ed={reverse.epsilon_d:.3e}, "
            f"from_end={reverse.started_from_endpoint}, image_dmax={image.max_pointing_delta:.3e}, "
            f"local_pointing_tangent_nonzero={image.local_pointing_tangent_nonzero}"
        ),
        "metrics": {
            "n_accepted": len(segment.accepted_samples),
            "n_failed": n_failed,
            "n_regular": n_regular,
            "reverse": asdict(reverse),
            "pointing_image": asdict(image),
            "n": list(n),
            "c": segment.c,
            "step_size": FIBER_STEP_SIZE,
            "n_steps": FIBER_STEPS,
        },
        "sample_rows": rows,
        "q": list(q0),
        "architecture": label,
        "n": list(n),
    }


def evaluate_intersecting_pairs_fiber() -> dict[str, Any]:
    return _segment_eval("ATR_EXP_028", "IntersectingPairsAligned6R", PRIMARY_N)


def evaluate_urlike_fiber() -> dict[str, Any]:
    result = _segment_eval("ATR_EXP_029", "URLikeAligned6R", PRIMARY_N)
    result["metrics"]["suur_required"] = False
    result["metrics"]["pair_fields"] = "not_applicable"
    return result


def evaluate_artifact_control() -> dict[str, Any]:
    reports = []
    ok = True
    for arch in ("IntersectingPairsAligned6R", "URLikeAligned6R"):
        chain, q0, label = _architecture_pair(arch)
        alt_report = fiber_independence_report(chain, q0, ALTERNATE_N)
        alt_rev = fiber_forward_reverse(
            chain, q0, ALTERNATE_N, n_steps=FIBER_STEPS, step_size=FIBER_STEP_SIZE, architecture=label
        )
        alt_seg = continue_fiber(chain, q0, ALTERNATE_N, n_steps=FIBER_STEPS, step_size=FIBER_STEP_SIZE)
        alt_image = pointing_image_report(alt_seg.accepted_samples)
        primary_plus, _ = continue_fiber_ray(
            chain, q0, PRIMARY_N, direction=1.0, n_steps=FIBER_STEPS, step_size=FIBER_STEP_SIZE
        )
        freeze = continue_joint_freeze_ray(
            chain,
            q0,
            freeze_index=JOINT_FREEZE_INDEX,
            direction=1.0,
            n_steps=FIBER_STEPS,
            step_size=FIBER_STEP_SIZE,
        )
        distinct = fiber_paths_distinct(primary_plus, freeze)
        arch_ok = (
            alt_report.independent
            and alt_report.dh_dq6_vanishes
            and alt_rev.passed
            and alt_image.passed
            and bool(distinct["distinct"])
        )
        ok = ok and arch_ok
        reports.append(
            {
                "architecture": label,
                "alternate_independent": alt_report.independent,
                "alternate_rank": alt_report.rank,
                "alternate_nullity": alt_report.nullity,
                "alternate_reverse": asdict(alt_rev),
                "alternate_image": asdict(alt_image),
                "joint_freeze_index": JOINT_FREEZE_INDEX,
                "distinct_from_joint_freeze": distinct,
                "passed": arch_ok,
            }
        )
    return {
        "experiment_id": "ATR_EXP_030",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "Alternate task-space h'=n'·d remains a regular reversible pointing fiber; "
            "q2-freeze control is a distinct path"
        ),
        "observed": "; ".join(
            f"{row['architecture']}: alt_ind={row['alternate_independent']}, "
            f"alt_rev_ed={row['alternate_reverse']['epsilon_d']:.3e}, "
            f"freeze_dq={row['distinct_from_joint_freeze']['max_joint_delta']:.3e}, "
            f"distinct={row['distinct_from_joint_freeze']['distinct']}"
            for row in reports
        ),
        "metrics": {
            "reports": reports,
            "primary_n": list(PRIMARY_N),
            "alternate_n": list(ALTERNATE_N),
            "joint_freeze_index": JOINT_FREEZE_INDEX,
        },
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "n": list(ALTERNATE_N),
    }


def evaluate_fiber_refinement() -> dict[str, Any]:
    reports = []
    ok = True
    for arch in ("IntersectingPairsAligned6R", "URLikeAligned6R"):
        chain, q0, label = _architecture_pair(arch)
        coarse_rev = fiber_forward_reverse(
            chain,
            q0,
            PRIMARY_N,
            n_steps=4,
            step_size=0.03,
            architecture=label,
            max_microstep=None,
        )
        fine_rev = fiber_forward_reverse(
            chain,
            q0,
            PRIMARY_N,
            n_steps=8,
            step_size=0.015,
            architecture=label,
            max_microstep=None,
        )
        coarse_plus, _ = continue_fiber_ray(
            chain,
            q0,
            PRIMARY_N,
            direction=1.0,
            n_steps=4,
            step_size=0.03,
            max_microstep=None,
            path_id="coarse",
        )
        fine_plus, _ = continue_fiber_ray(
            chain,
            q0,
            PRIMARY_N,
            direction=1.0,
            n_steps=8,
            step_size=0.015,
            max_microstep=None,
            path_id="fine",
        )
        shared = shared_sigma_agreement(coarse_plus, fine_plus, joint_tol=1e-3, pointing_tol=1e-3)
        tracked = (
            coarse_rev.started_from_endpoint
            and fine_rev.started_from_endpoint
            and coarse_rev.forward_accepted == 4
            and coarse_rev.reverse_accepted == 4
            and fine_rev.forward_accepted == 8
            and fine_rev.reverse_accepted == 8
        )
        improved = fine_rev.epsilon_q < coarse_rev.epsilon_q and fine_rev.epsilon_d < coarse_rev.epsilon_d
        arch_ok = tracked and improved and int(shared["n_shared"]) >= 5 and float(shared["max_joint_delta"]) <= 1e-3
        ok = ok and arch_ok
        reports.append(
            {
                "architecture": label,
                "coarse_reverse": asdict(coarse_rev),
                "fine_reverse": asdict(fine_rev),
                "shared_sigma": shared,
                "reverse_improved_or_within_tol": improved,
                "max_microstep": None,
                "independent_refinement": True,
                "passed": arch_ok,
            }
        )
    return {
        "experiment_id": "ATR_EXP_031",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "With max_microstep=None over the same σ travel, reverse tracking succeeds and both "
            "joint and pointing return errors decrease when Δσ is halved; shared-σ samples stay "
            "within 1e-3. Tight 1e-6/5e-8 reverse gates apply to microstepped runs (028/029), not "
            "this independent-step refinement diagnostic"
        ),
        "observed": "; ".join(
            f"{row['architecture']}: coarse_eq={row['coarse_reverse']['epsilon_q']:.3e} -> "
            f"fine_eq={row['fine_reverse']['epsilon_q']:.3e}, "
            f"shared_dq={row['shared_sigma']['max_joint_delta']:.3e}"
            for row in reports
        ),
        "metrics": {
            "reports": reports,
            "shared_microstep": None,
            "independent_refinement": True,
        },
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "n": list(PRIMARY_N),
    }


def run_all_fiber_experiments(repo_root: Path) -> list[dict[str, Any]]:
    provenance = _git_provenance(repo_root)
    results = [
        evaluate_independence(),
        evaluate_intersecting_pairs_fiber(),
        evaluate_urlike_fiber(),
        evaluate_artifact_control(),
        evaluate_fiber_refinement(),
    ]
    for result in results:
        write_fiber_artifacts(repo_root, result, provenance=provenance)
    return results


def write_fiber_artifacts(
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
        "metrics": {k: v for k, v in result.get("metrics", {}).items() if k not in {"reports", "reverse", "pointing_image"}},
        "seed_configuration": result.get("q"),
        "n": result.get("n", list(PRIMARY_N)),
        "step_sizes": {"dsigma": FIBER_STEP_SIZE},
        "n_steps": FIBER_STEPS,
        "tolerances": {
            "abs_rank_tol": ABS_RANK_TOL,
            "rel_rank_tol": REL_RANK_TOL,
            "position_residual_tol_m": POSITION_RESIDUAL_TOL_M,
            "scalar_residual_tol": SCALAR_RESIDUAL_TOL,
            "reverse_joint_tol_rad": REVERSE_JOINT_TOL_RAD,
            "fiber_reverse_pointing_tol": FIBER_REVERSE_POINTING_TOL,
            "dh_dq6_tol": DH_DQ6_TOL,
            "max_corrector_iters": MAX_CORRECTOR_ITERS,
            "max_step_reductions": MAX_STEP_REDUCTIONS,
            "max_microstep": MAX_MICROSTEP,
        },
    }
    config_sha = hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()
    slim = {k: v for k, v in result.items() if k not in {"sample_rows"}}
    manifest = {
        "experiment_id": exp_id,
        "repository_commit": commit,
        "working_tree_dirty": dirty,
        "source_identifier": SOURCE_IDENTIFIER,
        "source_file_sha256": source_sha,
        "experiment_configuration_sha256": config_sha,
        "architecture_parameters": result.get("architecture", "both"),
        "seed_configuration": result.get("q"),
        "n": result.get("n", list(PRIMARY_N)),
        "alternate_n": list(ALTERNATE_N),
        "step_sizes": config["step_sizes"],
        "n_steps": FIBER_STEPS,
        "rank_tolerances": {"abs_rank_tol": ABS_RANK_TOL, "rel_rank_tol": REL_RANK_TOL},
        "position_tolerance": POSITION_RESIDUAL_TOL_M,
        "scalar_tolerance": SCALAR_RESIDUAL_TOL,
        "status": result["status"],
        "expected": result["expected"],
        "observed": result["observed"],
        "units": {"length": "metre", "angle": "radian", "pointing_scalar": "dimensionless"},
        "result": slim,
        "software_version": "grashof-workspace spatial_experiments sprint05",
    }
    if "sample_rows" in result:
        _write_sample_csv(out / "samples.csv", result["sample_rows"])
    _write_kv_csv(out / "metrics.csv", result["metrics"])
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=_json_default) + "\n", encoding="utf-8")
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


def _write_sample_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


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
