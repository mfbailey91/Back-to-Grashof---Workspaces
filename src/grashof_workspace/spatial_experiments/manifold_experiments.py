"""Sprint 04 pointing-manifold experiments ATR_EXP_016–020."""

from __future__ import annotations

import csv
import json
import math
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
from .compound_joints import compare_reduced_tangents
from .continuation import (
    PATCH_DS,
    PATCH_DT,
    PATCH_NS,
    PATCH_NT,
    POSITION_RESIDUAL_TOL_M,
    continue_fixed_position_patch,
)
from .jacobians import ABS_RANK_TOL, REL_RANK_TOL
from .suur_coordinates import (
    PAIR_DISTANCE_TOL_M,
    closure_report,
    pair_intersection_distances,
    suur_map,
)

SOURCE_IDENTIFIER = "grashof_workspace.spatial_experiments.manifold_experiments:sprint04-v1"
PERSISTENCE_SEED = 23
PERSISTENCE_COUNT = 24
REVERSE_RETURN_TOL = 1e-6


def evaluate_pair_persistence() -> dict[str, Any]:
    chain = IntersectingPairsAligned6R.aligned().chain
    named = pair_intersection_distances(chain, INTERSECTING_PAIRS_REGULAR_Q)
    rng = np.random.default_rng(PERSISTENCE_SEED)
    rows = []
    max_ua = named[0]
    max_ub = named[1]
    for _ in range(PERSISTENCE_COUNT):
        q = tuple(float(x) for x in rng.uniform(-math.pi, math.pi, size=6))
        d_ua, d_ub = pair_intersection_distances(chain, q)
        max_ua = max(max_ua, d_ua)
        max_ub = max(max_ub, d_ub)
        rows.append({"q": q, "dist_ua_m": d_ua, "dist_ub_m": d_ub})
    ok = max_ua <= PAIR_DISTANCE_TOL_M and max_ub <= PAIR_DISTANCE_TOL_M
    return {
        "experiment_id": "ATR_EXP_016",
        "status": "PASS" if ok else "FAIL",
        "expected": "IntersectingPairsAligned6R pair distances remain 0 at regular and seeded q",
        "observed": (
            f"named_ua={named[0]:.3e}, named_ub={named[1]:.3e}, "
            f"seeded_max_ua={max_ua:.3e}, seeded_max_ub={max_ub:.3e}"
        ),
        "metrics": {
            "named_dist_ua_m": named[0],
            "named_dist_ub_m": named[1],
            "seeded_max_dist_ua_m": max_ua,
            "seeded_max_dist_ub_m": max_ub,
            "seed": PERSISTENCE_SEED,
            "count": PERSISTENCE_COUNT,
        },
        "samples": rows,
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
    }


def evaluate_negative_control() -> dict[str, Any]:
    chain = GenericAligned6R.aligned().chain
    d_ua, d_ub = pair_intersection_distances(chain, REGULAR_Q)
    mapped = suur_map(chain, REGULAR_Q[:5], REGULAR_Q[5])
    old = compare_reduced_tangents(chain, REGULAR_Q)
    ok = (
        d_ua > PAIR_DISTANCE_TOL_M
        and d_ub > PAIR_DISTANCE_TOL_M
        and mapped.defined is False
        and old.within_tolerance
    )
    return {
        "experiment_id": "ATR_EXP_017",
        "status": "PASS" if ok else "FAIL",
        "expected": "GenericAligned6R pairs do not intersect; φ undefined; old principal angles ~0",
        "observed": (
            f"dist_ua={d_ua:.3e}, dist_ub={d_ub:.3e}, phi_defined={mapped.defined}, "
            f"old_max_angle={old.max_angle_rad:.3e}"
        ),
        "metrics": {
            "dist_ua_m": d_ua,
            "dist_ub_m": d_ub,
            "phi_defined": mapped.defined,
            "old_max_principal_angle_rad": old.max_angle_rad,
        },
        "q": list(REGULAR_Q),
    }


def evaluate_coordinate_map_closure() -> dict[str, Any]:
    chain = IntersectingPairsAligned6R.aligned().chain
    theta = INTERSECTING_PAIRS_REGULAR_Q[:5]
    q6 = INTERSECTING_PAIRS_REGULAR_Q[5]
    mapped = suur_map(chain, theta, q6)
    closed = closure_report(chain, theta, q6)
    rng = np.random.default_rng(PERSISTENCE_SEED)
    extra_ok = True
    extra_max_pos = 0.0
    for _ in range(8):
        th = tuple(float(x) for x in rng.uniform(-1.0, 1.0, size=5))
        report = closure_report(chain, th, q6)
        extra_ok = extra_ok and report.defined and report.closed
        extra_max_pos = max(extra_max_pos, report.position_residual_m)
    ok = mapped.defined and closed.closed and extra_ok
    return {
        "experiment_id": "ATR_EXP_018",
        "status": "PASS" if ok else "FAIL",
        "expected": "φ defined on IntersectingPairsAligned6R; closure residuals below tolerance",
        "observed": (
            f"defined={mapped.defined}, closed={closed.closed}, "
            f"pos_res={closed.position_residual_m:.3e}, extra_max_pos={extra_max_pos:.3e}"
        ),
        "metrics": {
            "defined": mapped.defined,
            "closed": closed.closed,
            "dist_ua_m": closed.dist_ua_m,
            "dist_ub_m": closed.dist_ub_m,
            "position_residual_m": closed.position_residual_m,
            "pointing_residual": closed.pointing_residual,
            "inverse_residual": closed.inverse_residual,
            "extra_max_position_residual_m": extra_max_pos,
        },
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
    }


def _patch_metrics(patch: Any, *, require_pairs: bool) -> dict[str, Any]:
    regular = [s for s in patch.samples if s.regular]
    singular = [s for s in patch.samples if s.label == "singular"]
    failed = [s for s in patch.samples if s.label == "failed"]
    max_p = max((s.p_residual_m for s in regular), default=float("inf"))
    pair_ok = True
    if require_pairs:
        pair_ok = all(
            s.dist_ua_m is not None
            and s.dist_ub_m is not None
            and s.dist_ua_m <= PAIR_DISTANCE_TOL_M
            and s.dist_ub_m <= PAIR_DISTANCE_TOL_M
            for s in regular
        )
    phi_defined_regular = None
    if require_pairs:
        chain = IntersectingPairsAligned6R.aligned().chain
        phi_defined_regular = all(
            suur_map(chain, s.q[:5], s.q[5]).defined for s in regular
        )
    ok = (
        len(regular) >= max(8, len(patch.samples) // 3)
        and max_p <= POSITION_RESIDUAL_TOL_M
        and all(s.rank_jd_nred == 2 for s in regular)
        and patch.reverse_return_error <= REVERSE_RETURN_TOL
        and pair_ok
        and (phi_defined_regular is None or phi_defined_regular)
        and len(failed) == 0
    )
    return {
        "ok": ok,
        "n_samples": len(patch.samples),
        "n_regular": len(regular),
        "n_singular": len(singular),
        "n_failed": len(failed),
        "max_regular_p_residual_m": max_p,
        "reverse_return_error": patch.reverse_return_error,
        "pair_ok": pair_ok,
        "phi_defined_on_regular": phi_defined_regular,
        "suur_interpreted": bool(require_pairs and phi_defined_regular),
    }


def evaluate_intersecting_pairs_patch() -> dict[str, Any]:
    chain = IntersectingPairsAligned6R.aligned().chain
    patch = continue_fixed_position_patch(
        chain,
        INTERSECTING_PAIRS_REGULAR_Q,
        ns=PATCH_NS,
        nt=PATCH_NT,
        ds=PATCH_DS,
        dt=PATCH_DT,
        include_pairs=True,
    )
    metrics = _patch_metrics(patch, require_pairs=True)
    return {
        "experiment_id": "ATR_EXP_019",
        "status": "PASS" if metrics["ok"] else "FAIL",
        "expected": (
            "IP continuation patch is locally 2D with rank-two pointing away from labeled "
            "singular samples; φ defined on the regular subset"
        ),
        "observed": (
            f"regular={metrics['n_regular']}/{metrics['n_samples']}, "
            f"singular={metrics['n_singular']}, failed={metrics['n_failed']}, "
            f"max_p={metrics['max_regular_p_residual_m']:.3e}, "
            f"reverse_err={metrics['reverse_return_error']:.3e}, "
            f"phi_regular={metrics['phi_defined_on_regular']}"
        ),
        "metrics": metrics,
        "samples": [asdict(s) for s in patch.samples],
        "reverse_samples": [asdict(s) for s in patch.reverse_samples],
        "q": list(INTERSECTING_PAIRS_REGULAR_Q),
        "chart": {"ds": PATCH_DS, "dt": PATCH_DT, "ns": PATCH_NS, "nt": PATCH_NT},
    }


def evaluate_urlike_patch() -> dict[str, Any]:
    chain = URLikeAligned6R.aligned().chain
    patch = continue_fixed_position_patch(
        chain,
        URLIKE_REGULAR_Q,
        ns=PATCH_NS,
        nt=PATCH_NT,
        ds=PATCH_DS,
        dt=PATCH_DT,
        include_pairs=False,
    )
    metrics = _patch_metrics(patch, require_pairs=False)
    return {
        "experiment_id": "ATR_EXP_020",
        "status": "PASS" if metrics["ok"] else "FAIL",
        "expected": "URLike continuation via the same API yields a local 2D regular subset; no SUUR map required",
        "observed": (
            f"regular={metrics['n_regular']}/{metrics['n_samples']}, "
            f"singular={metrics['n_singular']}, failed={metrics['n_failed']}, "
            f"max_p={metrics['max_regular_p_residual_m']:.3e}, "
            f"reverse_err={metrics['reverse_return_error']:.3e}"
        ),
        "metrics": metrics,
        "samples": [asdict(s) for s in patch.samples],
        "reverse_samples": [asdict(s) for s in patch.reverse_samples],
        "q": list(URLIKE_REGULAR_Q),
        "chart": {"ds": PATCH_DS, "dt": PATCH_DT, "ns": PATCH_NS, "nt": PATCH_NT},
    }


def run_all_manifold_experiments(repo_root: Path) -> list[dict[str, Any]]:
    results = [
        evaluate_pair_persistence(),
        evaluate_negative_control(),
        evaluate_coordinate_map_closure(),
        evaluate_intersecting_pairs_patch(),
        evaluate_urlike_patch(),
    ]
    for result in results:
        write_manifold_artifacts(repo_root, result)
    return results


def write_manifold_artifacts(repo_root: Path, result: dict[str, Any]) -> Path:
    exp_id = str(result["experiment_id"])
    out = repo_root / "results" / "aligned_terminal_roll" / exp_id
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    commit = _git_commit_hash(repo_root)
    slim = {k: v for k, v in result.items() if k not in {"samples", "reverse_samples"}}
    manifest = {
        "experiment_id": exp_id,
        "repository_commit": commit,
        "source_identifier": SOURCE_IDENTIFIER,
        "status": result["status"],
        "expected": result["expected"],
        "observed": result["observed"],
        "units": {"length": "metre", "angle": "radian"},
        "tolerances": {
            "abs_rank_tol": ABS_RANK_TOL,
            "rel_rank_tol": REL_RANK_TOL,
            "pair_distance_tol_m": PAIR_DISTANCE_TOL_M,
            "position_residual_tol_m": POSITION_RESIDUAL_TOL_M,
        },
        "result": slim,
        "software_version": "grashof-workspace spatial_experiments sprint04",
    }
    if exp_id == "ATR_EXP_016":
        _write_persistence_csv(out / "metrics.csv", result["metrics"], result["samples"])
        _plot_persistence(result["samples"], fig_dir / "pair_persistence.png")
    elif exp_id in {"ATR_EXP_017", "ATR_EXP_018"}:
        _write_kv_csv(out / "metrics.csv", result["metrics"])
        if exp_id == "ATR_EXP_017":
            _plot_negative_control(result["metrics"], fig_dir / "negative_control.png")
        else:
            _plot_closure(result["metrics"], fig_dir / "closure_residuals.png")
    else:
        _write_patch_csv(out / "metrics.csv", result["samples"])
        _plot_patch(result["samples"], fig_dir / "pointing_patch.png", exp_id)
        manifest["result"]["n_samples"] = len(result["samples"])

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=_json_default) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(
        "\n".join(
            [
                f"# {exp_id}",
                "",
                f"**Status:** {result['status']}",
                f"**Commit:** {commit}",
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


def _write_kv_csv(path: Path, metrics: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def _write_persistence_csv(path: Path, metrics: dict[str, Any], samples: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "dist_ua_m", "dist_ub_m"])
        writer.writerow(["named_max", metrics["named_dist_ua_m"], metrics["named_dist_ub_m"]])
        for sample in samples:
            writer.writerow(["seeded", sample["dist_ua_m"], sample["dist_ub_m"]])


def _write_patch_csv(path: Path, samples: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["s", "t", "p_residual_m", "rank_jp", "rank_jpd", "rank_jd_nred", "regular", "label"])
        for sample in samples:
            writer.writerow(
                [
                    sample["s"],
                    sample["t"],
                    sample["p_residual_m"],
                    sample["rank_jp"],
                    sample["rank_jpd"],
                    sample["rank_jd_nred"],
                    sample["regular"],
                    sample["label"],
                ]
            )


def _plot_persistence(samples: list[dict[str, Any]], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.semilogy([max(s["dist_ua_m"], 1e-16) for s in samples], marker="o", label="dist(R1,R2)")
    ax.semilogy([max(s["dist_ub_m"], 1e-16) for s in samples], marker="s", label="dist(R3,R4)")
    ax.set_xlabel("seeded sample")
    ax.set_ylabel("pair distance [m]")
    ax.set_title("ATR_EXP_016 pair persistence")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_negative_control(metrics: dict[str, Any], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ["dist UA", "dist UB", "old angle"]
    values = [metrics["dist_ua_m"], metrics["dist_ub_m"], metrics["old_max_principal_angle_rad"]]
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.bar(labels, values, color=["#e76f51", "#e9c46a", "#2a9d8f"])
    ax.set_ylabel("magnitude")
    ax.set_title("ATR_EXP_017 nonintersecting negative control")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_closure(metrics: dict[str, Any], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ["dist UA", "dist UB", "pos res", "dir res"]
    values = [
        max(metrics["dist_ua_m"], 1e-16),
        max(metrics["dist_ub_m"], 1e-16),
        max(metrics["position_residual_m"], 1e-16),
        max(metrics["pointing_residual"], 1e-16),
    ]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.semilogy(labels, values, marker="o")
    ax.set_title("ATR_EXP_018 SUUR closure residuals")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_patch(samples: list[dict[str, Any]], dest: Path, exp_id: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ss = [s["s"] for s in samples]
    ts = [s["t"] for s in samples]
    colors = ["#2a9d8f" if s["regular"] else "#e9a319" if s["label"] == "singular" else "#e76f51" for s in samples]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    axes[0].scatter(ss, ts, c=colors, s=36)
    axes[0].set_xlabel("s [rad]")
    axes[0].set_ylabel("t [rad]")
    axes[0].set_title("chart samples")
    axes[0].grid(True, alpha=0.3)
    dx = [s["d"][0] for s in samples]
    dy = [s["d"][1] for s in samples]
    axes[1].scatter(dx, dy, c=colors, s=36)
    axes[1].set_xlabel("d_x")
    axes[1].set_ylabel("d_y")
    axes[1].set_title("pointing (color=status)")
    axes[1].grid(True, alpha=0.3)
    fig.suptitle(exp_id)
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)
