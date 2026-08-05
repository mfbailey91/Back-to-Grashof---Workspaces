"""Sprint 04B/04C sequential-chart experiments ATR_EXP_021–026."""

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
from .chart_diagnostics import (
    DUPLICATE_TOL_RAD,
    REVERSE_JOINT_TOL_RAD,
    REVERSE_POINTING_TOL,
    SHARED_NODE_JOINT_TOL_RAD,
    SHARED_NODE_POINTING_TOL,
    alternate_path_to_target,
    chart_differentials,
    compare_shared_nodes,
    duplicate_report,
    rectangular_loop,
    true_forward_reverse,
)
from .continuation import (
    MAX_CORRECTOR_ITERS,
    MAX_MICROSTEP,
    MAX_STEP_REDUCTIONS,
    PATCH_DS,
    PATCH_DT,
    PATCH_NS,
    PATCH_NT,
    POSITION_RESIDUAL_TOL_M,
    SequentialChart,
    continue_sequential_chart,
)
from .continuation_paths import ChartSample
from .jacobians import ABS_RANK_TOL, REL_RANK_TOL
from .suur_coordinates import PAIR_DISTANCE_TOL_M, pair_intersection_distances

SOURCE_IDENTIFIER = "grashof_workspace.spatial_experiments.chart_experiments:sprint04c-v1"
REVERSE_STEPS = 4
LOOP_STEPS = 2
ALT_S = 0.06
ALT_T = 0.06

CSV_FIELDS = [
    "architecture",
    "experiment_id",
    "s",
    "t",
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
    "corrector_iterations",
    "correction_norm",
    "step_reductions",
    "rank_jp",
    "rank_jpd",
    "rank_jd_nred",
    "chart_sigma_1",
    "chart_sigma_2",
    "chart_condition",
    "pointing_sigma_1",
    "pointing_sigma_2",
    "pointing_condition",
    "tangent_principal_angle_1",
    "tangent_principal_angle_2",
    "dist_ua_m",
    "dist_ub_m",
    "regular",
    "label",
]


def _architecture_pair(name: str) -> tuple[Any, tuple[float, ...], str]:
    if name == "IntersectingPairsAligned6R":
        return IntersectingPairsAligned6R.aligned().chain, INTERSECTING_PAIRS_REGULAR_Q, name
    if name == "URLikeAligned6R":
        return URLikeAligned6R.aligned().chain, URLIKE_REGULAR_Q, name
    raise ValueError(name)


def evaluate_forward_reverse() -> dict[str, Any]:
    reports = []
    ok = True
    for arch in ("IntersectingPairsAligned6R", "URLikeAligned6R"):
        chain, q0, label = _architecture_pair(arch)
        for axis in ("s", "t"):
            report = true_forward_reverse(
                chain, q0, axis=axis, n_steps=REVERSE_STEPS, step_size=PATCH_DS, architecture=label
            )
            reports.append(asdict(report))
            ok = ok and report.passed
    return {
        "experiment_id": "ATR_EXP_021",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "Sequential forward/reverse rays return within 1e-6 rad / 1e-8 pointing "
            "on both architectures and both chart axes"
        ),
        "observed": "; ".join(
            f"{row['architecture']}/{row['axis']}: eq={row['epsilon_q']:.3e}, "
            f"ed={row['epsilon_d']:.3e}, from_end={row['started_from_endpoint']}"
            for row in reports
        ),
        "metrics": {"reports": reports, "reverse_steps": REVERSE_STEPS, "step_size": PATCH_DS},
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
    }


def _pair_fields(chain: Any, sample: ChartSample, *, include_pairs: bool) -> tuple[str, str]:
    if not include_pairs:
        return "not_applicable", "not_applicable"
    dist_ua, dist_ub = pair_intersection_distances(chain, sample.q)
    return f"{dist_ua:.16e}", f"{dist_ub:.16e}"


def _chart_eval(
    exp_id: str,
    architecture: str,
    *,
    include_pairs: bool,
    ns: int = PATCH_NS,
    nt: int = PATCH_NT,
    ds: float = PATCH_DS,
    dt: float = PATCH_DT,
) -> dict[str, Any]:
    chain, q0, label = _architecture_pair(architecture)
    chart = continue_sequential_chart(chain, q0, ns=ns, nt=nt, ds=ds, dt=dt)
    diffs = chart_differentials(chart, ds=ds, dt=dt)
    dups = duplicate_report(chart.samples)
    n_regular = sum(1 for sample in chart.samples if sample.regular)
    n_failed = sum(1 for sample in chart.samples if sample.label == "failed") + len(chart.rejected_steps)
    pair_ok = True
    max_ua = max_ub = 0.0
    pair_rows: list[dict[str, Any]] = []
    if include_pairs:
        for sample in chart.samples:
            dist_ua, dist_ub = pair_intersection_distances(chain, sample.q)
            max_ua = max(max_ua, dist_ua)
            max_ub = max(max_ub, dist_ub)
            pair_rows.append({"s": sample.s, "t": sample.t, "dist_ua_m": dist_ua, "dist_ub_m": dist_ub})
            if dist_ua > PAIR_DISTANCE_TOL_M or dist_ub > PAIR_DISTANCE_TOL_M:
                pair_ok = False
    ok = (
        n_regular == len(chart.samples)
        and n_failed == 0
        and diffs.all_rank_two
        and dups.n_duplicates == 0
        and not dups.collapsed_row
        and not dups.collapsed_column
        and pair_ok
    )
    diff_lookup_q = {(round(item.s, 12), round(item.t, 12)): item for item in diffs.chart_differentials}
    diff_lookup_d = {(round(item.s, 12), round(item.t, 12)): item for item in diffs.pointing_differentials}
    rows = []
    for sample in chart.samples:
        key = (round(sample.s, 12), round(sample.t, 12))
        qdiff = diff_lookup_q.get(key)
        ddiff = diff_lookup_d.get(key)
        dist_ua_s, dist_ub_s = _pair_fields(chain, sample, include_pairs=include_pairs)
        rows.append(
            {
                "architecture": label,
                "experiment_id": exp_id,
                "s": sample.s,
                "t": sample.t,
                "path_id": sample.path_id,
                "step_index": sample.step_index,
                "q1": sample.q[0],
                "q2": sample.q[1],
                "q3": sample.q[2],
                "q4": sample.q[3],
                "q5": sample.q[4],
                "q6": sample.q[5],
                "d_x": sample.d[0],
                "d_y": sample.d[1],
                "d_z": sample.d[2],
                "position_residual_m": sample.p_residual_m,
                "corrector_iterations": sample.corrector_iterations,
                "correction_norm": sample.correction_norm,
                "step_reductions": sample.step_reductions,
                "rank_jp": sample.rank_jp,
                "rank_jpd": sample.rank_jpd,
                "rank_jd_nred": sample.rank_jd_nred,
                "chart_sigma_1": "" if qdiff is None else qdiff.singular_values[0],
                "chart_sigma_2": "" if qdiff is None or len(qdiff.singular_values) < 2 else qdiff.singular_values[1],
                "chart_condition": "" if qdiff is None else qdiff.condition,
                "pointing_sigma_1": "" if ddiff is None else ddiff.singular_values[0],
                "pointing_sigma_2": "" if ddiff is None or len(ddiff.singular_values) < 2 else ddiff.singular_values[1],
                "pointing_condition": "" if ddiff is None else ddiff.condition,
                "tangent_principal_angle_1": sample.tangent_principal_angle_1,
                "tangent_principal_angle_2": sample.tangent_principal_angle_2,
                "dist_ua_m": dist_ua_s,
                "dist_ub_m": dist_ub_s,
                "regular": sample.regular,
                "label": sample.label,
            }
        )
    return {
        "experiment_id": exp_id,
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "100% regular sequential chart; rank(Q)=rank(D)=2 at every interior node; "
            "no duplicates or failed samples"
            + ("; pair intersections persist" if include_pairs else "; no SUUR/pair fields required")
        ),
        "observed": (
            f"regular={n_regular}/{len(chart.samples)}, rejected={len(chart.rejected_steps)}, "
            f"interior={diffs.n_interior}, rankQ2={diffs.n_rank_q_two}, rankD2={diffs.n_rank_d_two}, "
            f"duplicates={dups.n_duplicates}"
            + (f", max_ua={max_ua:.3e}, max_ub={max_ub:.3e}" if include_pairs else "")
        ),
        "metrics": {
            "n_samples": len(chart.samples),
            "n_regular": n_regular,
            "n_rejected": len(chart.rejected_steps),
            "n_interior": diffs.n_interior,
            "n_rank_q_two": diffs.n_rank_q_two,
            "n_rank_d_two": diffs.n_rank_d_two,
            "n_duplicates": dups.n_duplicates,
            "min_nn_distance": dups.min_nn_distance,
            "collapsed_row": dups.collapsed_row,
            "collapsed_column": dups.collapsed_column,
            "pair_ok": pair_ok,
            "max_dist_ua_m": max_ua if include_pairs else None,
            "max_dist_ub_m": max_ub if include_pairs else None,
            "ns": ns,
            "nt": nt,
            "ds": ds,
            "dt": dt,
        },
        "chart_rows": rows,
        "pair_rows": pair_rows,
        "q": list(q0),
        "architecture": label,
        "chart": chart,
        "diagnostics": diffs,
    }


def evaluate_intersecting_pairs_chart() -> dict[str, Any]:
    return _chart_eval("ATR_EXP_022", "IntersectingPairsAligned6R", include_pairs=True)


def evaluate_urlike_chart() -> dict[str, Any]:
    return _chart_eval("ATR_EXP_023", "URLikeAligned6R", include_pairs=False)


def evaluate_refinement() -> dict[str, Any]:
    comparisons = []
    ok = True
    for arch in ("IntersectingPairsAligned6R", "URLikeAligned6R"):
        chain, q0, label = _architecture_pair(arch)
        baseline = continue_sequential_chart(chain, q0, ns=9, nt=9, ds=0.03, dt=0.03)
        fine = continue_sequential_chart(chain, q0, ns=17, nt=17, ds=0.015, dt=0.015)
        compact = continue_sequential_chart(chain, q0, ns=9, nt=9, ds=0.015, dt=0.015)
        shared = compare_shared_nodes(baseline, fine)
        base_diag = chart_differentials(baseline, ds=0.03, dt=0.03)
        fine_diag = chart_differentials(fine, ds=0.015, dt=0.015)
        compact_diag = chart_differentials(compact, ds=0.015, dt=0.015)
        ranks_ok = base_diag.all_rank_two and fine_diag.all_rank_two and compact_diag.all_rank_two
        arch_ok = shared.passed and ranks_ok
        ok = ok and arch_ok
        comparisons.append(
            {
                "architecture": label,
                "shared": asdict(shared),
                "baseline_rank_two": base_diag.all_rank_two,
                "fine_rank_two": fine_diag.all_rank_two,
                "compact_rank_two": compact_diag.all_rank_two,
                "passed": arch_ok,
            }
        )
    return {
        "experiment_id": "ATR_EXP_024",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "Shared-node q/d agree under the same internal microstep; rank classifications remain two. "
            "This is macro-grid consistency, not independent numerical refinement"
        ),
        "observed": "; ".join(
            f"{row['architecture']}: shared={row['shared']['n_shared']}, "
            f"dq={row['shared']['max_joint_delta']:.3e}, dd={row['shared']['max_pointing_delta']:.3e}, "
            f"ranks={row['baseline_rank_two']}/{row['fine_rank_two']}/{row['compact_rank_two']}"
            for row in comparisons
        ),
        "metrics": {
            "comparisons": comparisons,
            "shared_microstep": MAX_MICROSTEP,
            "independent_refinement": False,
        },
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
    }


def evaluate_loop_refinement() -> dict[str, Any]:
    reports = []
    ok = True
    for arch in ("IntersectingPairsAligned6R", "URLikeAligned6R"):
        chain, q0, label = _architecture_pair(arch)
        coarse = rectangular_loop(chain, q0, n_steps=LOOP_STEPS, step_size=PATCH_DS)
        fine = rectangular_loop(chain, q0, n_steps=LOOP_STEPS, step_size=PATCH_DS / 2.0)
        decreased = fine.epsilon_q < coarse.epsilon_q and fine.accepted_legs == 4 and coarse.accepted_legs == 4
        ok = ok and decreased
        reports.append(
            {
                "architecture": label,
                "coarse": asdict(coarse),
                "fine": asdict(fine),
                "decreased": decreased,
            }
        )
    return {
        "experiment_id": "ATR_EXP_025",
        "status": "PASS" if ok else "FAIL",
        "expected": "Rectangular-loop closure error decreases when the step is halved",
        "observed": "; ".join(
            f"{row['architecture']}: coarse_eq={row['coarse']['epsilon_q']:.3e}, "
            f"fine_eq={row['fine']['epsilon_q']:.3e}, decreased={row['decreased']}"
            for row in reports
        ),
        "metrics": {"reports": reports},
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
    }


def evaluate_alternate_and_duplicates() -> dict[str, Any]:
    reports = []
    ok = True
    for arch in ("IntersectingPairsAligned6R", "URLikeAligned6R"):
        chain, q0, label = _architecture_pair(arch)
        chart = continue_sequential_chart(chain, q0, ns=9, nt=9, ds=PATCH_DS, dt=PATCH_DT)
        dups = duplicate_report(chart.samples)
        coarse_alt = alternate_path_to_target(chain, q0, s_target=ALT_S, t_target=ALT_T, step_size=0.06)
        fine_alt = alternate_path_to_target(chain, q0, s_target=ALT_S, t_target=ALT_T, step_size=0.03)
        rel = abs(fine_alt.epsilon_q - coarse_alt.epsilon_q) / max(coarse_alt.epsilon_q, 1e-30)
        stable_or_decreased = fine_alt.epsilon_q < coarse_alt.epsilon_q or (
            max(fine_alt.epsilon_q, coarse_alt.epsilon_q) <= 5e-4 and rel <= 0.05
        )
        arch_ok = dups.n_duplicates == 0 and stable_or_decreased and fine_alt.epsilon_q <= 5e-3
        ok = ok and arch_ok
        reports.append(
            {
                "architecture": label,
                "duplicates": dups.n_duplicates,
                "min_nn_distance": dups.min_nn_distance,
                "coarse_alt": asdict(coarse_alt),
                "fine_alt": asdict(fine_alt),
                "discrepancy_stable_or_decreased": stable_or_decreased,
                "passed": arch_ok,
            }
        )
    return {
        "experiment_id": "ATR_EXP_026",
        "status": "PASS" if ok else "FAIL",
        "expected": "No duplicate solutions; s-then-t vs t-then-s discrepancy remains small and stable",
        "observed": "; ".join(
            f"{row['architecture']}: dups={row['duplicates']}, "
            f"alt_coarse={row['coarse_alt']['epsilon_q']:.3e}, alt_fine={row['fine_alt']['epsilon_q']:.3e}"
            for row in reports
        ),
        "metrics": {"reports": reports},
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
    }


def run_all_chart_experiments(repo_root: Path) -> list[dict[str, Any]]:
    provenance = _git_provenance(repo_root)
    results = [
        evaluate_forward_reverse(),
        evaluate_intersecting_pairs_chart(),
        evaluate_urlike_chart(),
        evaluate_refinement(),
        evaluate_loop_refinement(),
        evaluate_alternate_and_duplicates(),
    ]
    for result in results:
        write_chart_artifacts(repo_root, result, provenance=provenance)
    return results


def write_chart_artifacts(
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
        "metrics": {k: v for k, v in result.get("metrics", {}).items() if k != "reports"},
        "seed_configuration": result.get("q"),
        "step_sizes": {"ds": PATCH_DS, "dt": PATCH_DT},
        "grid_dimensions": {"ns": PATCH_NS, "nt": PATCH_NT},
        "tolerances": {
            "abs_rank_tol": ABS_RANK_TOL,
            "rel_rank_tol": REL_RANK_TOL,
            "position_residual_tol_m": POSITION_RESIDUAL_TOL_M,
            "reverse_joint_tol_rad": REVERSE_JOINT_TOL_RAD,
            "reverse_pointing_tol": REVERSE_POINTING_TOL,
            "duplicate_tol_rad": DUPLICATE_TOL_RAD,
            "shared_node_joint_tol_rad": SHARED_NODE_JOINT_TOL_RAD,
            "shared_node_pointing_tol": SHARED_NODE_POINTING_TOL,
            "pair_distance_tol_m": PAIR_DISTANCE_TOL_M,
            "max_corrector_iters": MAX_CORRECTOR_ITERS,
            "max_step_reductions": MAX_STEP_REDUCTIONS,
        },
    }
    config_sha = hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()
    slim = {k: v for k, v in result.items() if k not in {"chart_rows", "chart", "diagnostics", "pair_rows"}}
    manifest = {
        "experiment_id": exp_id,
        "repository_commit": commit,
        "working_tree_dirty": dirty,
        "source_identifier": SOURCE_IDENTIFIER,
        "source_file_sha256": source_sha,
        "experiment_configuration_sha256": config_sha,
        "architecture_parameters": result.get("architecture", "both"),
        "seed_configuration": result.get("q"),
        "step_sizes": config["step_sizes"],
        "grid_dimensions": config["grid_dimensions"],
        "rank_tolerances": {"abs_rank_tol": ABS_RANK_TOL, "rel_rank_tol": REL_RANK_TOL},
        "position_tolerance": POSITION_RESIDUAL_TOL_M,
        "duplicate_tolerance": DUPLICATE_TOL_RAD,
        "status": result["status"],
        "expected": result["expected"],
        "observed": result["observed"],
        "units": {"length": "metre", "angle": "radian"},
        "result": slim,
        "software_version": "grashof-workspace spatial_experiments sprint04c",
    }
    if "chart_rows" in result:
        _write_chart_csv(out / "samples.csv", result["chart_rows"])
        _plot_chart(result["chart_rows"], out / "figures" / f"{exp_id}_chart.png", exp_id)
    else:
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
            if path.endswith(".DS_Store") or path.endswith(".patch"):
                continue
            if path.startswith("results/aligned_terminal_roll/"):
                continue
            relevant.append(line)
        return commit, bool(relevant)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown", True


def _write_chart_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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


def _plot_chart(rows: list[dict[str, Any]], dest: Path, exp_id: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    import matplotlib.pyplot as plt

    xs = [row["d_x"] for row in rows]
    ys = [row["d_y"] for row in rows]
    zs = [row["d_z"] for row in rows]
    fig = plt.figure(figsize=(5.5, 4.5))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(xs, ys, zs, c=["#1d4ed8" if row["regular"] else "#b45309" for row in rows], s=18)
    ax.set_xlabel("d_x")
    ax.set_ylabel("d_y")
    ax.set_zlabel("d_z")
    ax.set_title(f"{exp_id} sequential pointing chart")
    fig.tight_layout()
    fig.savefig(dest, dpi=140)
    plt.close(fig)


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, SequentialChart):
        return {"n_samples": len(value.samples), "n_rejected": len(value.rejected_steps)}
    raise TypeError(type(value))
