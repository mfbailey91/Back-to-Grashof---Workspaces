"""Sprint 03 architecture-comparison experiments ATR_EXP_011–015."""

from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .aligned_6r import REGULAR_Q, GenericAligned6R
from .architectures import (
    INTERSECTING_PAIRS_REGULAR_Q,
    URLIKE_REGULAR_Q,
    IntersectingPairsAligned6R,
    URLikeAligned6R,
)
from .compound_joints import (
    N_LOCAL_STEPS,
    POINTING_AGREE_TOL,
    POSITION_RESIDUAL_TOL_M,
    PRINCIPAL_ANGLE_TOL_RAD,
    STEP_DT,
    compare_reduced_tangents,
    local_nred_steps,
)
from .jacobians import ABS_RANK_TOL, REL_RANK_TOL, position_jacobian, reduced_pointing_basis
from .reduction_experiments import reduction_snapshot

CONTINUATION_PARENT_RECOMMENDATION = "IntersectingPairsAligned6R"
GEOMETRY_TOL = 1e-12


def evaluate_intersecting_pairs_stage_a() -> dict[str, Any]:
    model = IntersectingPairsAligned6R.aligned()
    snap = reduction_snapshot(model.chain, INTERSECTING_PAIRS_REGULAR_Q)
    dist, par = model.home_alignment_residuals()
    d_ua, d_ub = model.pair_intersection_distances()
    geometry_ok = dist <= GEOMETRY_TOL and par <= GEOMETRY_TOL and d_ua <= GEOMETRY_TOL and d_ub <= GEOMETRY_TOL
    status = "PASS" if snap.regular and geometry_ok else "FAIL"
    return {
        "experiment_id": "ATR_EXP_011",
        "status": status,
        "expected": "IntersectingPairsAligned6R Stage A C6–C8; exact R1∩R2 and R3∩R4",
        "observed": (
            f"regular={snap.regular}, rank_jp={snap.rank_jp}, rank_jpd={snap.rank_jpd}, "
            f"rank_jd_nred={snap.rank_jd_nred}, d_ua={d_ua:.3e}, d_ub={d_ub:.3e}"
        ),
        "snapshot": asdict(snap),
        "home_point_axis_distance_m": dist,
        "home_pointing_parallelism": par,
        "pair_intersection_m": {"ua": d_ua, "ub": d_ub},
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "model": _model_dict(model, "IntersectingPairsAligned6R"),
    }


def evaluate_urlike_stage_a() -> dict[str, Any]:
    model = URLikeAligned6R.aligned()
    snap = reduction_snapshot(model.chain, URLIKE_REGULAR_Q)
    dist, par = model.home_alignment_residuals()
    elbow = model.elbow_parallelism_residual()
    wrist = model.wrist_concurrency_distances()
    geometry_ok = (
        dist <= GEOMETRY_TOL
        and par <= GEOMETRY_TOL
        and elbow <= GEOMETRY_TOL
        and all(d <= GEOMETRY_TOL for d in wrist)
    )
    status = "PASS" if snap.regular and geometry_ok else "FAIL"
    return {
        "experiment_id": "ATR_EXP_012",
        "status": status,
        "expected": "URLikeAligned6R Stage A C6–C8; exact R2∥R3 and R4∩R5∩R6",
        "observed": (
            f"regular={snap.regular}, rank_jp={snap.rank_jp}, rank_jpd={snap.rank_jpd}, "
            f"rank_jd_nred={snap.rank_jd_nred}, elbow_par={elbow:.3e}, wrist={tuple(f'{d:.3e}' for d in wrist)}"
        ),
        "snapshot": asdict(snap),
        "home_point_axis_distance_m": dist,
        "home_pointing_parallelism": par,
        "elbow_parallelism": elbow,
        "wrist_concurrency_m": {"r45": wrist[0], "r56": wrist[1], "r46": wrist[2]},
        "q": list(URLIKE_REGULAR_Q),
        "model": _model_dict(model, "URLikeAligned6R"),
    }


def evaluate_principal_angles() -> dict[str, Any]:
    chain = IntersectingPairsAligned6R.aligned().chain
    report = compare_reduced_tangents(chain, INTERSECTING_PAIRS_REGULAR_Q)
    status = "PASS" if report.within_tolerance else "FAIL"
    return {
        "experiment_id": "ATR_EXP_013",
        "status": status,
        "expected": f"max principal angle(N_red, compound embed) <= {PRINCIPAL_ANGLE_TOL_RAD:g} rad",
        "observed": (
            f"angles_rad={tuple(f'{a:.3e}' for a in report.angles_rad)}, "
            f"max={report.max_angle_rad:.3e}"
        ),
        "metrics": {
            "max_principal_angle_rad": report.max_angle_rad,
            "principal_angle_0_rad": report.angles_rad[0] if report.angles_rad else math_nan(),
            "principal_angle_1_rad": report.angles_rad[1] if len(report.angles_rad) > 1 else math_nan(),
            "tolerance_rad": PRINCIPAL_ANGLE_TOL_RAD,
        },
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "model": _model_dict(IntersectingPairsAligned6R.aligned(), "IntersectingPairsAligned6R"),
    }


def evaluate_local_nred_steps() -> dict[str, Any]:
    chain = IntersectingPairsAligned6R.aligned().chain
    seed = reduced_pointing_basis(position_jacobian(chain, INTERSECTING_PAIRS_REGULAR_Q))[:, 0]
    physical = local_nred_steps(
        chain,
        INTERSECTING_PAIRS_REGULAR_Q,
        compound=False,
        seed_direction=seed,
    )
    compound = local_nred_steps(
        chain,
        INTERSECTING_PAIRS_REGULAR_Q,
        compound=True,
        seed_direction=seed,
    )
    pointing_diffs = []
    max_p_res = 0.0
    for p_rec, c_rec in zip(physical, compound, strict=True):
        max_p_res = max(max_p_res, float(p_rec["p_residual_m"]), float(c_rec["p_residual_m"]))
        d_p = np.asarray(p_rec["d"], dtype=float)
        d_c = np.asarray(c_rec["d"], dtype=float)
        pointing_diffs.append(float(np.linalg.norm(d_p - d_c)))
    max_pointing = max(pointing_diffs) if pointing_diffs else float("inf")
    ok = max_p_res <= POSITION_RESIDUAL_TOL_M and max_pointing <= POINTING_AGREE_TOL
    return {
        "experiment_id": "ATR_EXP_014",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            f"local {N_LOCAL_STEPS} N_red steps keep ||p-p0|| <= {POSITION_RESIDUAL_TOL_M:g} m "
            f"and pointing increments agree within {POINTING_AGREE_TOL:g}"
        ),
        "observed": f"max_p_residual_m={max_p_res:.3e}, max_pointing_diff={max_pointing:.3e}",
        "metrics": {
            "max_p_residual_m": max_p_res,
            "max_pointing_diff": max_pointing,
            "dt_rad": STEP_DT,
            "n_steps": N_LOCAL_STEPS,
            "position_tol_m": POSITION_RESIDUAL_TOL_M,
            "pointing_tol": POINTING_AGREE_TOL,
        },
        "physical_steps": physical,
        "compound_steps": compound,
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "model": _model_dict(IntersectingPairsAligned6R.aligned(), "IntersectingPairsAligned6R"),
    }


def evaluate_architecture_comparison() -> dict[str, Any]:
    generic = reduction_snapshot(GenericAligned6R.aligned().chain, REGULAR_Q)
    intersecting = reduction_snapshot(IntersectingPairsAligned6R.aligned().chain, INTERSECTING_PAIRS_REGULAR_Q)
    urlike = reduction_snapshot(URLikeAligned6R.aligned().chain, URLIKE_REGULAR_Q)
    c9 = compare_reduced_tangents(IntersectingPairsAligned6R.aligned().chain, INTERSECTING_PAIRS_REGULAR_Q)
    rows = [
        {
            "model": "GenericAligned6R",
            "stage_a": generic.regular,
            "rank_jp": generic.rank_jp,
            "rank_jpd": generic.rank_jpd,
            "rank_jd_nred": generic.rank_jd_nred,
            "local_c9": None,
        },
        {
            "model": "IntersectingPairsAligned6R",
            "stage_a": intersecting.regular,
            "rank_jp": intersecting.rank_jp,
            "rank_jpd": intersecting.rank_jpd,
            "rank_jd_nred": intersecting.rank_jd_nred,
            "local_c9": c9.within_tolerance,
            "max_principal_angle_rad": c9.max_angle_rad,
        },
        {
            "model": "URLikeAligned6R",
            "stage_a": urlike.regular,
            "rank_jp": urlike.rank_jp,
            "rank_jpd": urlike.rank_jpd,
            "rank_jd_nred": urlike.rank_jd_nred,
            "local_c9": None,
        },
    ]
    stage_a_all = generic.regular and intersecting.regular and urlike.regular
    ok = stage_a_all and c9.within_tolerance
    return {
        "experiment_id": "ATR_EXP_015",
        "status": "PASS" if ok else "FAIL",
        "expected": (
            "Stage A survives all three architectures; local C9 reported; "
            "continuation parent recorded but not auto-selected"
        ),
        "observed": (
            f"stage_a_all={stage_a_all}, local_c9={c9.within_tolerance}, "
            f"recommended_parent={CONTINUATION_PARENT_RECOMMENDATION}, auto_selected=false"
        ),
        "comparison_rows": rows,
        "continuation_parent_recommendation": CONTINUATION_PARENT_RECOMMENDATION,
        "continuation_parent_auto_selected": False,
        "local_c9_max_principal_angle_rad": c9.max_angle_rad,
        "metrics": {
            "generic_stage_a": generic.regular,
            "intersecting_pairs_stage_a": intersecting.regular,
            "urlike_stage_a": urlike.regular,
            "local_c9": c9.within_tolerance,
            "recommended_parent": CONTINUATION_PARENT_RECOMMENDATION,
            "auto_selected": False,
        },
    }


def run_all_architecture_experiments(repo_root: Path) -> list[dict[str, Any]]:
    results = [
        evaluate_intersecting_pairs_stage_a(),
        evaluate_urlike_stage_a(),
        evaluate_principal_angles(),
        evaluate_local_nred_steps(),
        evaluate_architecture_comparison(),
    ]
    for result in results:
        write_architecture_artifacts(repo_root, result)
    return results


def write_architecture_artifacts(repo_root: Path, result: dict[str, Any]) -> Path:
    exp_id = str(result["experiment_id"])
    out = repo_root / "results" / "aligned_terminal_roll" / exp_id
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    commit = _git_commit_hash(repo_root)
    manifest = {
        "experiment_id": exp_id,
        "repository_commit": commit,
        "status": result["status"],
        "expected": result["expected"],
        "observed": result["observed"],
        "units": {"length": "metre", "angle": "radian"},
        "tolerances": {
            "abs_rank_tol": ABS_RANK_TOL,
            "rel_rank_tol": REL_RANK_TOL,
            "geometry_tol": GEOMETRY_TOL,
            "principal_angle_tol_rad": PRINCIPAL_ANGLE_TOL_RAD,
            "position_residual_tol_m": POSITION_RESIDUAL_TOL_M,
            "pointing_agree_tol": POINTING_AGREE_TOL,
        },
        "result": {
            k: v
            for k, v in result.items()
            if k not in {"physical_steps", "compound_steps"}
        },
        "software_version": "grashof-workspace spatial_experiments sprint03",
    }
    if "snapshot" in result:
        _write_snapshot_csv(out / "metrics.csv", result["snapshot"])
        _plot_singular_values(result["snapshot"], fig_dir / "singular_values.png", exp_id)
    elif exp_id == "ATR_EXP_013":
        _write_kv_csv(out / "metrics.csv", result["metrics"])
        _plot_principal_angles(result["metrics"], fig_dir / "principal_angles.png")
    elif exp_id == "ATR_EXP_014":
        _write_step_csv(out / "metrics.csv", result["physical_steps"], result["compound_steps"])
        _plot_local_steps(result["physical_steps"], result["compound_steps"], fig_dir / "local_nred_steps.png")
        manifest["result"]["physical_steps"] = result["physical_steps"]
        manifest["result"]["compound_steps"] = result["compound_steps"]
    elif exp_id == "ATR_EXP_015":
        _write_comparison_csv(out / "metrics.csv", result["comparison_rows"])
        _plot_comparison(result["comparison_rows"], fig_dir / "architecture_comparison.png")
    else:
        _write_kv_csv(out / "metrics.csv", result.get("metrics", {"status": result["status"]}))

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=_json_default) + "\n", encoding="utf-8")
    summary = "\n".join(
        [
            f"# {exp_id}",
            "",
            f"**Status:** {result['status']}",
            f"**Commit:** {commit}",
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
    )
    (out / "summary.md").write_text(summary, encoding="utf-8")
    return out


def math_nan() -> float:
    return float("nan")


def _model_dict(model: Any, name: str) -> dict[str, Any]:
    return {
        "name": name,
        "aligned": model.is_aligned,
        "task_point_m": list(model.task_point),
        "d0": list(model.chain.d0),
        "home_axes": [{"r_m": list(a.r), "w": list(a.w)} for a in model.chain.home_axes],
    }


def _git_commit_hash(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    raise TypeError(f"unserializable type: {type(value)!r}")


def _write_snapshot_csv(path: Path, snapshot: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key in (
            "rank_jp",
            "nullity_jp",
            "rank_jpd",
            "nullity_jpd",
            "jp_e6_norm",
            "jd_e6_norm",
            "ker_jpd_align_e6",
            "rank_jd_nred",
            "nred_cols",
            "regular",
        ):
            writer.writerow([key, snapshot[key]])


def _write_kv_csv(path: Path, metrics: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def _write_step_csv(path: Path, physical: list[dict[str, Any]], compound: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "step",
                "physical_p_residual_m",
                "compound_p_residual_m",
                "physical_pointing_delta",
                "compound_pointing_delta",
                "pointing_diff",
            ]
        )
        for p_rec, c_rec in zip(physical, compound, strict=True):
            d_p = np.asarray(p_rec["d"], dtype=float)
            d_c = np.asarray(c_rec["d"], dtype=float)
            writer.writerow(
                [
                    p_rec["step"],
                    p_rec["p_residual_m"],
                    c_rec["p_residual_m"],
                    p_rec["pointing_delta"],
                    c_rec["pointing_delta"],
                    float(np.linalg.norm(d_p - d_c)),
                ]
            )


def _write_comparison_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "stage_a", "rank_jp", "rank_jpd", "rank_jd_nred", "local_c9"])
        for row in rows:
            writer.writerow(
                [
                    row["model"],
                    row["stage_a"],
                    row["rank_jp"],
                    row["rank_jpd"],
                    row["rank_jd_nred"],
                    row["local_c9"],
                ]
            )


def _plot_singular_values(snapshot: dict[str, Any], dest: Path, exp_id: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.6))
    axes[0].semilogy(snapshot["sv_jp"], marker="o")
    axes[0].set_title("J_p singular values")
    axes[1].semilogy(snapshot["sv_jpd"], marker="o")
    axes[1].set_title("J_pd singular values")
    for ax in axes:
        ax.set_xlabel("index")
        ax.grid(True, alpha=0.3)
    fig.suptitle(exp_id)
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_principal_angles(metrics: dict[str, Any], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ["θ1", "θ2"]
    values = [metrics["principal_angle_0_rad"], metrics["principal_angle_1_rad"]]
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.bar(labels, values, color="#2a9d8f")
    ax.axhline(metrics["tolerance_rad"], color="#e9a319", linestyle="--", label="tolerance")
    ax.set_ylabel("principal angle [rad]")
    ax.set_title("ATR_EXP_013 physical N_red vs compound embedding")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_local_steps(
    physical: list[dict[str, Any]],
    compound: list[dict[str, Any]],
    dest: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    steps = [r["step"] for r in physical]
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.8))
    axes[0].semilogy(
        steps,
        [max(float(r["p_residual_m"]), 1e-16) for r in physical],
        marker="o",
        label="physical",
    )
    axes[0].semilogy(
        steps,
        [max(float(r["p_residual_m"]), 1e-16) for r in compound],
        marker="s",
        label="compound",
    )
    axes[0].set_title("position residual")
    axes[0].set_xlabel("step")
    axes[0].set_ylabel("||p-p0|| [m]")
    axes[1].plot(steps, [r["pointing_delta"] for r in physical], marker="o", label="physical")
    axes[1].plot(steps, [r["pointing_delta"] for r in compound], marker="s", label="compound")
    axes[1].set_title("pointing increment")
    axes[1].set_xlabel("step")
    axes[1].set_ylabel("||d-d0||")
    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.suptitle("ATR_EXP_014 local N_red steps")
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_comparison(rows: list[dict[str, Any]], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [r["model"].replace("Aligned6R", "") for r in rows]
    ranks = np.array([[r["rank_jp"], r["rank_jpd"], r["rank_jd_nred"]] for r in rows], dtype=float)
    x = np.arange(len(names))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    ax.bar(x - width, ranks[:, 0], width, label="rank(J_p)")
    ax.bar(x, ranks[:, 1], width, label="rank(J_pd)")
    ax.bar(x + width, ranks[:, 2], width, label="rank(J_d N_red)")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylim(0, 6)
    ax.set_ylabel("rank")
    ax.set_title("ATR_EXP_015 architecture Stage A comparison")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)
