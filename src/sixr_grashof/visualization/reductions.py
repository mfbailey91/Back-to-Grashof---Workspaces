"""Sprint 2–3 reduction and prediction visualizations."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureParams,
)
from sixr_grashof.classification.predictors import (
    HandLinkRole,
    OrientationPrediction,
    architecture_a_type_map,
    predict_orientation_capability,
)
from sixr_grashof.reductions import reduce_architecture_a, reduce_architecture_b
from sixr_grashof.visualization.robot_plot import plot_robot_with_links
from sixr_grashof.visualization.spherical_linkage import plot_spherical_fourbar, spherical_vertices

_INK = "#1a1f24"
_STEEL = "#2f6f8f"
_TEAL = "#1f7a6c"
_AMBER = "#c47b2c"
_ROSE = "#a34848"
_MUTED = "#6b7280"
_PANEL = "#f3f5f7"
_GRID = "#d7dde3"

# Distinct colors for types 1–16
_TYPE_COLORS = [
    "#1a1f24",
    "#2f6f8f",
    "#1f7a6c",
    "#c47b2c",
    "#a34848",
    "#5b6b7a",
    "#3d8b6e",
    "#8b6914",
    "#4a6fa5",
    "#6b4f7a",
    "#2a7a8c",
    "#9a5b3c",
    "#3a5a4a",
    "#7a5a3a",
    "#4a4a6a",
    "#6a3a4a",
]


def _save(fig: Any, output: str | Path | None, show: bool) -> Path | None:
    out_path: Path | None = None
    if output is not None:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return out_path


def plot_regional_reduction_panel(
    *,
    output: str | Path | None = None,
    show: bool = False,
    q: tuple[float, float, float, float, float, float] = (0.0, 0.3, -0.4, 0.0, 0.0, 0.0),
) -> Path | None:
    """Physical 6R beside virtual planar four-bar (Architecture A)."""
    arch = ArchitectureA()
    fk = arch.forward(q)
    report = arch.geometry_report(q)
    reduction = reduce_architecture_a(arch, q)
    reg = reduction.regional

    fig = plt.figure(figsize=(12, 5.5))
    fig.patch.set_facecolor("white")
    ax0 = fig.add_subplot(1, 2, 1, projection="3d")
    plot_robot_with_links(fk, report, ax=ax0, title="Physical Architecture A")

    ax1 = fig.add_subplot(1, 2, 2)
    ax1.set_facecolor(_PANEL)
    ax1.set_aspect("equal")
    ax1.grid(True, color=_GRID, linewidth=0.8)
    # Place planar 4R with ground on x-axis: O0=(0,0), O3=(ground,0)
    g = reg.ground
    a = reg.input_length
    b = reg.coupler_length
    c = reg.output_length
    # Folded assembly sketch (not kinematics solution): place coupler via triangle
    o0 = (0.0, 0.0)
    o3 = (g, 0.0)
    # Place O1 at input angle ~60° for readability
    th = math.radians(55)
    o1 = (a * math.cos(th), a * math.sin(th))
    # Place O2 from O3 at output length; choose y>0 intersection with coupler circle
    # Approximate: project toward O1
    dx, dy = o1[0] - o3[0], o1[1] - o3[1]
    dn = math.hypot(dx, dy) or 1.0
    o2 = (o3[0] + c * dx / dn * 0.55, max(0.15, c * 0.75))
    xs = [o0[0], o1[0], o2[0], o3[0], o0[0]]
    ys = [o0[1], o1[1], o2[1], o3[1], o0[1]]
    ax1.plot(xs, ys, color=_STEEL, linewidth=2.4)
    for p, label in ((o0, "O0"), (o1, "O1"), (o2, "O2"), (o3, "O3")):
        ax1.scatter([p[0]], [p[1]], color=_INK, s=40)
        ax1.text(p[0] + 0.02, p[1] + 0.03, label, fontsize=9, color=_INK)
    ax1.text(g / 2, -0.08 * max(g, 1), rf"ground $\rho_p$={g:.3f}", ha="center", color=_MUTED, fontsize=8)
    ax1.set_title(
        f"Virtual planar 4R  |  ρ_w={reg.rho_w:.3f}  |  "
        f"{reg.grashof_class}  |  assemblable={reg.assemblable}",
        fontsize=10,
        color=_INK,
    )
    ax1.set_xlabel("planar x")
    ax1.set_ylabel("planar y")
    note = (
        f"roles: ground=ρ_p, input=Lt={reg.Lt:.3f}, coupler=L3={reg.L3:.3f}, "
        f"output=L2={reg.L2:.3f}"
    )
    fig.suptitle("Sprint 2 — Regional planar reduction", fontsize=13, color=_INK)
    fig.text(0.5, 0.02, note, ha="center", fontsize=8, color=_MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    return _save(fig, output, show)


def plot_spherical_reduction_panel(
    *,
    output: str | Path | None = None,
    show: bool = False,
    q: tuple[float, float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
) -> Path | None:
    """Physical 6R beside virtual spherical four-bar (Architecture A)."""
    arch = ArchitectureA()
    fk = arch.forward(q)
    report = arch.geometry_report(q)
    reduction = reduce_architecture_a(arch, q)
    assert reduction.spherical.linkage is not None

    fig = plt.figure(figsize=(12, 5.5))
    fig.patch.set_facecolor("white")
    ax0 = fig.add_subplot(1, 2, 1, projection="3d")
    plot_robot_with_links(fk, report, ax=ax0, title="Physical Architecture A")

    # Reuse spherical vertex placement on second 3D axes
    linkage = reduction.spherical.linkage
    ax1 = fig.add_subplot(1, 2, 2, projection="3d")
    o0, o1, o2, o3 = spherical_vertices(linkage)
    from sixr_grashof.visualization.spherical_linkage import _sphere_arc  # noqa: PLC0415

    u = [i * math.pi / 16 for i in range(17)]
    v = [i * 2 * math.pi / 24 for i in range(25)]
    for ui in u:
        xs = [math.sin(ui) * math.cos(vj) for vj in v]
        ys = [math.sin(ui) * math.sin(vj) for vj in v]
        zs = [math.cos(ui) for _ in v]
        ax1.plot(xs, ys, zs, color=_GRID, linewidth=0.4, alpha=0.6)
    links = [
        (o0, o1, r"$\alpha$", _STEEL),
        (o1, o2, r"$\eta$", _MUTED),
        (o2, o3, r"$\beta$ hand", _AMBER),
        (o3, o0, r"$\gamma$", _INK),
    ]
    for a, b, label, color in links:
        xs, ys, zs = _sphere_arc(a, b)
        ax1.plot(xs, ys, zs, color=color, linewidth=2.8, label=label)
    for p, name in ((o0, "O0"), (o1, "O1"), (o2, "O2"), (o3, "O3")):
        ax1.scatter([p[0]], [p[1]], [p[2]], color=_INK, s=36)
        ax1.text(p[0] * 1.08, p[1] * 1.08, p[2] * 1.08, name, fontsize=8, color=_INK)
    ax1.set_title(
        f"Virtual spherical 4R  |  status={reduction.spherical.status}  |  "
        rf"ρ_C={reduction.spherical.concurrency.residual_rho:.2e}",
        fontsize=10,
        color=_INK,
    )
    ax1.legend(fontsize=8, loc="upper left")
    fig.suptitle("Sprint 2 — Spherical orientation reduction", fontsize=13, color=_INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, output, show)


def plot_exact_vs_offset_reduction(
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Side-by-side A exact vs B offset with status badge and ρ_C."""
    q = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    cases = [
        ("A exact", ArchitectureA(), "A"),
        ("B εw=0.2", ArchitectureB(ArchitectureParams(epsilon_w=0.2)), "B"),
    ]
    fig = plt.figure(figsize=(12, 5.5))
    fig.patch.set_facecolor("white")
    for i, (label, arch, kind) in enumerate(cases):
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        fk = arch.forward(q)
        report = arch.geometry_report(q)
        if kind == "A":
            red = reduce_architecture_a(arch, q)  # type: ignore[arg-type]
        else:
            red = reduce_architecture_b(arch, q)  # type: ignore[arg-type]
        status = red.spherical.status
        rho = red.spherical.concurrency.residual_rho
        plot_robot_with_links(
            fk,
            report,
            ax=ax,
            title=f"{label}  |  {status}  |  ρ_C={rho:.3e}",
        )
        color = _TEAL if status == "exact" else (_AMBER if status == "approximate" else _ROSE)
        ax.text2D(
            0.02,
            0.96,
            status.upper(),
            transform=ax.transAxes,
            fontsize=11,
            fontweight="bold",
            color=color,
            va="top",
        )
        if red.spherical.linkage is None:
            ax.text2D(
                0.02,
                0.88,
                "angles withheld",
                transform=ax.transAxes,
                fontsize=9,
                color=_ROSE,
                va="top",
            )
    fig.suptitle("Sprint 2 — Exact A vs offset B reduction status", fontsize=13, color=_INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, output, show)


def plot_linkage_type_map(
    rows: list[OrientationPrediction] | None = None,
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Scatter of Architecture A type map over (q2, q3), color by type 1–16."""
    if rows is None:
        rows = architecture_a_type_map(n_radial=14, n_elbow=10)
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(_PANEL)
    ax.grid(True, color=_GRID, linewidth=0.8)

    for t in range(1, 17):
        pts = [r for r in rows if r.linkage_type == t]
        if not pts:
            continue
        xs = [r.joint_configuration[1] for r in pts]
        ys = [r.joint_configuration[2] for r in pts]
        color = _TYPE_COLORS[(t - 1) % len(_TYPE_COLORS)]
        marker = "*" if any(r.dexterity_candidate_hypothesis for r in pts) else "o"
        ax.scatter(
            xs,
            ys,
            c=color,
            s=55 if marker == "*" else 36,
            marker=marker,
            label=f"type {t}",
            edgecolors="white",
            linewidths=0.4,
            zorder=3 if marker == "*" else 2,
        )

    ax.set_xlabel(r"$q_2$ (rad)", color=_INK)
    ax.set_ylabel(r"$q_3$ (rad)", color=_INK)
    ax.set_title(
        "Architecture A linkage-type map  |  ★ = dexterity-candidate hypothesis",
        color=_INK,
        fontsize=11,
    )
    ax.legend(fontsize=7, ncol=4, frameon=False, loc="upper right")
    fig.tight_layout()
    return _save(fig, output, show)


def plot_prediction_card(
    prediction: OrientationPrediction | None = None,
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Single-state prediction card: T_i, signs, type, hand, hypothesis."""
    if prediction is None:
        prediction = predict_orientation_capability(
            reduce_architecture_a(ArchitectureA(), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        )
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.add_patch(
        FancyBboxPatch(
            (0.3, 0.4),
            9.4,
            6.2,
            boxstyle="round,pad=0.05,rounding_size=0.15",
            facecolor=_PANEL,
            edgecolor=_GRID,
            linewidth=1.5,
        )
    )
    ax.text(0.6, 6.2, "Sprint 3 — Orientation prediction card", fontsize=13, color=_INK, fontweight="600")
    ax.text(
        0.6,
        5.7,
        f"Architecture {prediction.architecture_id}  ·  status={prediction.reduction_status}  ·  "
        rf"ρ_C={prediction.concurrency_residual:.2e}",
        fontsize=10,
        color=_MUTED,
    )

    lines = [
        f"Type: {prediction.linkage_type}  {prediction.linkage_name}",
        f"Family: {prediction.grashof_family}   wrap={prediction.wrap_around}",
        f"T = ({_fmt(prediction.T1)}, {_fmt(prediction.T2)}, {_fmt(prediction.T3)}, {_fmt(prediction.T4)})",
        f"Signs: {_signs(prediction.sign_tuple)}   product={_fmt(prediction.T_product)}",
        f"Input: {prediction.input_motion_class}   Output: {prediction.output_motion_class}",
        f"Hand link: {prediction.hand_orientation_link} → {prediction.hand_link_motion_class}",
    ]
    y = 5.1
    for line in lines:
        ax.text(0.7, y, line, fontsize=11, color=_INK, family="monospace")
        y -= 0.45

    hyp = prediction.dexterity_candidate_hypothesis
    badge_color = _TEAL if hyp else _MUTED
    ax.add_patch(Rectangle((0.7, 1.0), 4.2, 0.7, facecolor=badge_color, edgecolor="none", alpha=0.9))
    ax.text(
        2.8,
        1.35,
        "DEXTERITY CANDIDATE" if hyp else "NOT A CANDIDATE",
        ha="center",
        va="center",
        fontsize=11,
        color="white",
        fontweight="700",
    )
    ax.text(
        0.7,
        0.65,
        "Hypothesis only — product ≠ dexterity; crank hand types {2,3,10,11}.",
        fontsize=8,
        color=_MUTED,
    )
    return _save(fig, output, show)


def plot_hand_link_sensitivity(
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Default β vs alternate α hand-link assignment for the same state."""
    reduction = reduce_architecture_a(ArchitectureA(), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    beta = predict_orientation_capability(reduction, hand_link=HandLinkRole.BETA)
    alpha = predict_orientation_capability(reduction, hand_link=HandLinkRole.ALPHA)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    fig.patch.set_facecolor("white")
    for ax, pred, title in (
        (axes[0], beta, "Default hand-link = β (output)"),
        (axes[1], alpha, "Alternate hand-link = α (input)"),
    ):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.axis("off")
        ax.set_facecolor(_PANEL)
        ax.add_patch(
            FancyBboxPatch(
                (0.2, 0.3),
                9.6,
                7.4,
                boxstyle="round,pad=0.04,rounding_size=0.12",
                facecolor="white",
                edgecolor=_GRID,
                linewidth=1.2,
            )
        )
        ax.text(0.5, 7.2, title, fontsize=11, color=_INK, fontweight="600")
        body = [
            f"type {pred.linkage_type} · {pred.linkage_name}",
            f"hand = {pred.hand_orientation_link} → {pred.hand_link_motion_class}",
            f"input={pred.input_motion_class}  output={pred.output_motion_class}",
            f"hypothesis={'yes' if pred.dexterity_candidate_hypothesis else 'no'}",
        ]
        y = 6.2
        for line in body:
            ax.text(0.6, y, line, fontsize=10, color=_INK, family="monospace")
            y -= 0.7
        color = _TEAL if pred.dexterity_candidate_hypothesis else _ROSE
        ax.text(
            0.6,
            2.2,
            "candidate" if pred.dexterity_candidate_hypothesis else "not candidate",
            fontsize=14,
            color=color,
            fontweight="700",
        )

    fig.suptitle("Sprint 3 — Hand-link assignment sensitivity", fontsize=13, color=_INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return _save(fig, output, show)


def _fmt(v: float | None) -> str:
    if v is None:
        return "—"
    if abs(v) < 1e-4 and v != 0.0:
        return f"{v:.2e}"
    return f"{v:.4f}"


def _signs(signs: tuple[int, int, int, int] | None) -> str:
    if signs is None:
        return "—"
    return " ".join("+" if s > 0 else "−" for s in signs)


# Re-export for scripts that may want a dedicated spherical dump
__all__ = [
    "plot_exact_vs_offset_reduction",
    "plot_hand_link_sensitivity",
    "plot_linkage_type_map",
    "plot_prediction_card",
    "plot_regional_reduction_panel",
    "plot_spherical_reduction_panel",
    "plot_spherical_fourbar",
]
