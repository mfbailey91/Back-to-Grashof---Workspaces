"""Sprint 02 Stage A experiments for the generic aligned 6R chain."""

from __future__ import annotations

import csv
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .aligned_6r import REGULAR_Q, SINGULAR_SEARCH_SEED, GenericAligned6R
from .diagnostics import signed_roll_about_direction
from .jacobians import (
    ABS_RANK_TOL,
    REL_RANK_TOL,
    central_difference_jacobians,
    kernel_alignment_to_unit,
    matrix_rank_report,
    pointing_jacobian,
    position_jacobian,
    reduced_pointing_basis,
)
from .serial_chain import SerialRevoluteChain

FD_STEPS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6)
SURVEY_COUNT = 48
E6_COL_TOL = 1e-9
KERNEL_ALIGN_TOL = 1e-8
ROLL_ABS_TOL_RAD = 1e-8


@dataclass(frozen=True, slots=True)
class ReductionSnapshot:
    q: tuple[float, ...]
    rank_jp: int
    nullity_jp: int
    rank_jpd: int
    nullity_jpd: int
    sv_jp: tuple[float, ...]
    sv_jpd: tuple[float, ...]
    jp_e6_norm: float
    jd_e6_norm: float
    ker_jpd_align_e6: float
    rank_jd_nred: int
    nred_cols: int
    regular: bool


def reduction_snapshot(chain: SerialRevoluteChain, q: tuple[float, ...]) -> ReductionSnapshot:
    jp = position_jacobian(chain, q)
    jd = pointing_jacobian(chain, q)
    jpd = np.vstack([jp, jd])
    rp = matrix_rank_report(jp)
    rpd = matrix_rank_report(jpd)
    e6 = np.zeros(chain.n_joints)
    e6[-1] = 1.0
    jp_e6 = float(np.linalg.norm(jp @ e6))
    jd_e6 = float(np.linalg.norm(jd @ e6))
    ker_pd = _nullspace_last(jpd, rpd.nullity)
    align = kernel_alignment_to_unit(ker_pd[:, 0], e6) if rpd.nullity == 1 else math.inf
    nred = reduced_pointing_basis(jp)
    if nred.shape[1] == 0:
        rank_jd_nred = 0
    else:
        rank_jd_nred = matrix_rank_report(jd @ nred).rank
    regular = (
        rp.rank == 3
        and rp.nullity == 3
        and rpd.rank == 5
        and rpd.nullity == 1
        and jp_e6 <= E6_COL_TOL
        and jd_e6 <= E6_COL_TOL
        and align <= KERNEL_ALIGN_TOL
        and rank_jd_nred == 2
        and nred.shape[1] == 2
    )
    return ReductionSnapshot(
        q=q,
        rank_jp=rp.rank,
        nullity_jp=rp.nullity,
        rank_jpd=rpd.rank,
        nullity_jpd=rpd.nullity,
        sv_jp=rp.singular_values,
        sv_jpd=rpd.singular_values,
        jp_e6_norm=jp_e6,
        jd_e6_norm=jd_e6,
        ker_jpd_align_e6=float(align),
        rank_jd_nred=rank_jd_nred,
        nred_cols=int(nred.shape[1]),
        regular=regular,
    )


def find_named_singular_q(chain: SerialRevoluteChain, *, seed: int = SINGULAR_SEARCH_SEED) -> tuple[float, ...]:
    """Return a sample that minimizes the relative smallest singular value of ``J_p``."""
    rng = np.random.default_rng(seed)
    best_q = tuple(float(x) for x in rng.uniform(-math.pi, math.pi, size=chain.n_joints))
    best_ratio = 1.0
    for _ in range(800):
        q = tuple(float(x) for x in rng.uniform(-math.pi, math.pi, size=chain.n_joints))
        report = matrix_rank_report(position_jacobian(chain, q))
        sigma_max = report.singular_values[0] if report.singular_values else 0.0
        sigma_min = report.singular_values[-1] if report.singular_values else 0.0
        ratio = 0.0 if sigma_max == 0.0 else sigma_min / sigma_max
        if report.rank <= 2:
            return q
        if ratio < best_ratio:
            best_ratio = ratio
            best_q = q
    return best_q


def evaluate_regular_reduction() -> dict[str, Any]:
    model = GenericAligned6R.aligned()
    snap = reduction_snapshot(model.chain, REGULAR_Q)
    dist, par = model.home_alignment_residuals()
    status = "PASS" if snap.regular else "FAIL"
    return {
        "experiment_id": "ATR_EXP_006",
        "status": status,
        "expected": "rank(J_p)=3, ker dim 3, J_pd rank 5 nullity 1 aligned to e6, rank(J_d N_red)=2",
        "observed": (
            f"rank_jp={snap.rank_jp}, null_jp={snap.nullity_jp}, "
            f"rank_jpd={snap.rank_jpd}, null_jpd={snap.nullity_jpd}, "
            f"align={snap.ker_jpd_align_e6:.3e}, rank_jd_nred={snap.rank_jd_nred}"
        ),
        "snapshot": asdict(snap),
        "home_point_axis_distance_m": dist,
        "home_pointing_parallelism": par,
        "model": _model_dict(model),
    }


def evaluate_fd_refinement() -> dict[str, Any]:
    chain = GenericAligned6R.aligned().chain
    jp = position_jacobian(chain, REGULAR_Q)
    jd = pointing_jacobian(chain, REGULAR_Q)
    rows = []
    for h in FD_STEPS:
        jp_fd, jd_fd = central_difference_jacobians(chain, REGULAR_Q, h)
        rows.append(
            {
                "h": h,
                "jp_error": float(np.linalg.norm(jp_fd - jp)),
                "jd_error": float(np.linalg.norm(jd_fd - jd)),
            }
        )
    usable = rows[:-1] if rows[-1]["jp_error"] > rows[-2]["jp_error"] else rows
    converges = usable[0]["jp_error"] > usable[2]["jp_error"] and usable[0]["jd_error"] > usable[2]["jd_error"]
    return {
        "experiment_id": "ATR_EXP_007",
        "status": "PASS" if converges else "FAIL",
        "expected": "analytical vs central-FD Jacobian error converges over usable h",
        "observed": "; ".join(f"h={r['h']:g}: jp={r['jp_error']:.3e}, jd={r['jd_error']:.3e}" for r in rows),
        "fd_refinement": rows,
        "q": list(REGULAR_Q),
        "model": _model_dict(GenericAligned6R.aligned()),
    }


def evaluate_full_chain_roll() -> dict[str, Any]:
    chain = GenericAligned6R.aligned().chain
    q0 = REGULAR_Q
    s0 = chain.evaluate(q0)
    delta = 0.37
    q1 = q0[:-1] + (q0[-1] + delta,)
    s1 = chain.evaluate(q1)
    jp = position_jacobian(chain, q0)
    jd = pointing_jacobian(chain, q0)
    e6 = np.zeros(6)
    e6[-1] = 1.0
    dp = float(np.linalg.norm(jp @ e6))
    dd = float(np.linalg.norm(jd @ e6))
    pos_change = float(np.linalg.norm(s1.p - s0.p))
    dir_change = float(np.linalg.norm(s1.d - s0.d))
    R_world_rel = s1.R @ s0.R.T
    signed, axis_mis = signed_roll_about_direction(R_world_rel, s0.d)
    roll_err = abs(((signed - delta + math.pi) % (2.0 * math.pi)) - math.pi)
    ok = dp <= E6_COL_TOL and dd <= E6_COL_TOL and pos_change <= 1e-12 and dir_change <= 1e-12 and roll_err <= ROLL_ABS_TOL_RAD
    return {
        "experiment_id": "ATR_EXP_008",
        "status": "PASS" if ok else "FAIL",
        "expected": "full-chain dp/dq6=0, dd/dq6=0, position/pointing invariant, roll recovers Delta q6",
        "observed": (
            f"||J_p e6||={dp:.3e}, ||J_d e6||={dd:.3e}, |dp|={pos_change:.3e} m, "
            f"|dd|={dir_change:.3e}, roll_err={roll_err:.3e} rad, axis_mis={axis_mis:.3e}"
        ),
        "metrics": {
            "jp_e6_norm": dp,
            "jd_e6_norm": dd,
            "position_change_m": pos_change,
            "pointing_change": dir_change,
            "roll_error_rad": roll_err,
            "roll_axis_misalignment": axis_mis,
        },
        "q": list(q0),
        "delta_q6": delta,
        "model": _model_dict(GenericAligned6R.aligned()),
    }


def evaluate_negative_alignment() -> dict[str, Any]:
    off = GenericAligned6R.off_axis_task_point()
    mis = GenericAligned6R.misaligned_pointing()
    snap_off = reduction_snapshot(off.chain, REGULAR_Q)
    snap_mis = reduction_snapshot(mis.chain, REGULAR_Q)
    off_breaks = snap_off.jp_e6_norm > 1e-6
    mis_breaks = snap_mis.jd_e6_norm > 1e-6
    ok = off_breaks and mis_breaks
    return {
        "experiment_id": "ATR_EXP_009",
        "status": "PASS" if ok else "FAIL",
        "expected": "off-axis p makes J_p e6 nonzero; misaligned d makes J_d e6 nonzero",
        "observed": (
            f"off-axis ||J_p e6||={snap_off.jp_e6_norm:.3e}; "
            f"misaligned ||J_d e6||={snap_mis.jd_e6_norm:.3e}"
        ),
        "off_axis": asdict(snap_off),
        "misaligned": asdict(snap_mis),
    }


def evaluate_survey_and_singular() -> dict[str, Any]:
    model = GenericAligned6R.aligned()
    chain = model.chain
    rng = np.random.default_rng(SINGULAR_SEARCH_SEED)
    samples = []
    for _ in range(SURVEY_COUNT):
        q = tuple(float(x) for x in rng.uniform(-math.pi, math.pi, size=6))
        samples.append(asdict(reduction_snapshot(chain, q)))
    regular = [s for s in samples if s["regular"]]
    singular = [s for s in samples if s["rank_jp"] < 3]
    named_q = find_named_singular_q(chain)
    named = reduction_snapshot(chain, named_q)
    named_sv = named.sv_jp
    named_ratio = 0.0 if not named_sv or named_sv[0] == 0.0 else named_sv[-1] / named_sv[0]
    regular_ratios = []
    for sample in regular:
        sv = sample["sv_jp"]
        regular_ratios.append(0.0 if not sv or sv[0] == 0.0 else sv[-1] / sv[0])
    median_regular_ratio = float(np.median(regular_ratios)) if regular_ratios else 1.0
    near_singular = (
        named.rank_jp <= 2
        or named_ratio < 0.1 * median_regular_ratio
        or named_ratio < 5e-3
    )
    regular_ok = all(
        s["rank_jp"] == 3 and s["rank_jpd"] == 5 and s["rank_jd_nred"] == 2 and s["nullity_jpd"] == 1
        for s in regular
    )
    ok = len(regular) > 0 and regular_ok and near_singular
    return {
        "experiment_id": "ATR_EXP_010",
        "status": "PASS" if ok else "FAIL",
        "expected": "regular subset supports C6-C8; named sample is singular or near-singular and labeled separately",
        "observed": (
            f"survey regular={len(regular)}/{SURVEY_COUNT}, singular_jp={len(singular)}, "
            f"named rank_jp={named.rank_jp}, named_sigma_ratio={named_ratio:.3e}, "
            f"median_regular_sigma_ratio={median_regular_ratio:.3e}"
        ),
        "survey_regular_count": len(regular),
        "survey_singular_jp_count": len(singular),
        "survey_samples": samples,
        "named_singular": asdict(named),
        "named_singular_sigma_ratio": named_ratio,
        "named_label": "singular" if named.rank_jp <= 2 else "near-singular",
        "seed": SINGULAR_SEARCH_SEED,
        "model": _model_dict(model),
    }


def run_all_reduction_experiments(repo_root: Path) -> list[dict[str, Any]]:
    results = [
        evaluate_regular_reduction(),
        evaluate_fd_refinement(),
        evaluate_full_chain_roll(),
        evaluate_negative_alignment(),
        evaluate_survey_and_singular(),
    ]
    for result in results:
        write_reduction_artifacts(repo_root, result)
    return results


def write_reduction_artifacts(repo_root: Path, result: dict[str, Any]) -> Path:
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
            "e6_col_tol": E6_COL_TOL,
            "kernel_align_tol": KERNEL_ALIGN_TOL,
        },
        "result": {k: v for k, v in result.items() if k != "survey_samples"},
        "software_version": "grashof-workspace spatial_experiments sprint02",
    }
    if "survey_samples" in result:
        manifest["survey_regular_count"] = result["survey_regular_count"]
        manifest["survey_singular_jp_count"] = result["survey_singular_jp_count"]
        _write_survey_csv(out / "metrics.csv", result["survey_samples"])
    elif "fd_refinement" in result:
        _write_fd_csv(out / "metrics.csv", result["fd_refinement"])
        _plot_fd(result["fd_refinement"], fig_dir / "fd_refinement.png")
    elif "snapshot" in result:
        _write_snapshot_csv(out / "metrics.csv", result["snapshot"])
    elif "metrics" in result:
        _write_kv_csv(out / "metrics.csv", result["metrics"])
    else:
        _write_kv_csv(out / "metrics.csv", {"status": result["status"]})

    if exp_id == "ATR_EXP_006":
        _plot_singular_values(result["snapshot"], fig_dir / "singular_values.png")
    if exp_id == "ATR_EXP_010":
        _plot_survey(result["survey_samples"], fig_dir / "survey_ranks.png")

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
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


def _model_dict(model: GenericAligned6R) -> dict[str, Any]:
    return {
        "name": "GenericAligned6R",
        "aligned": model.is_aligned,
        "task_point_m": list(model.task_point),
        "d0": list(model.chain.d0),
        "home_axes": [{"r_m": list(a.r), "w": list(a.w)} for a in model.chain.home_axes],
    }


def _nullspace_last(A: np.ndarray, nullity: int) -> np.ndarray:
    _, _, vt = np.linalg.svd(np.asarray(A, dtype=float), full_matrices=True)
    if nullity <= 0:
        return np.zeros((A.shape[1], 0))
    return vt[-nullity:, :].T


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


def _write_fd_csv(path: Path, rows: list[dict[str, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["h_rad", "jp_error", "jd_error"])
        for row in rows:
            writer.writerow([row["h"], row["jp_error"], row["jd_error"]])


def _write_kv_csv(path: Path, metrics: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def _write_survey_csv(path: Path, samples: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank_jp", "rank_jpd", "rank_jd_nred", "regular", "jp_e6_norm", "jd_e6_norm"])
        for sample in samples:
            writer.writerow(
                [
                    sample["rank_jp"],
                    sample["rank_jpd"],
                    sample["rank_jd_nred"],
                    sample["regular"],
                    sample["jp_e6_norm"],
                    sample["jd_e6_norm"],
                ]
            )


def _plot_fd(rows: list[dict[str, float]], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hs = [r["h"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.loglog(hs, [r["jp_error"] for r in rows], marker="o", label="||ΔJ_p||")
    ax.loglog(hs, [r["jd_error"] for r in rows], marker="s", label="||ΔJ_d||")
    ax.set_xlabel("h [rad]")
    ax.set_ylabel("analytical vs central-FD error")
    ax.set_title("ATR_EXP_007 Jacobian refinement")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_singular_values(snapshot: dict[str, Any], dest: Path) -> None:
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
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def _plot_survey(samples: list[dict[str, Any]], dest: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ranks = [s["rank_jp"] for s in samples]
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.hist(ranks, bins=np.arange(0.5, 4.5, 1.0), align="mid", rwidth=0.8)
    ax.set_xticks([1, 2, 3])
    ax.set_xlabel("rank(J_p)")
    ax.set_ylabel("count")
    ax.set_title("ATR_EXP_010 seeded rank survey")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)
