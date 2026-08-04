"""Comparison plots for architecture residuals and geometry panels."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.visualization.robot_plot import plot_robot_with_links

_INK = "#1a1f24"
_STEEL = "#2f6f8f"
_TEAL = "#1f7a6c"
_AMBER = "#c47b2c"
_MUTED = "#6b7280"
_PANEL = "#f3f5f7"


def plot_architecture_panel(
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Side-by-side A / B(εw=0) / B(εw=0.2) / C(εs=0.2) geometry views."""
    cases: list[tuple[str, ArchitectureA | ArchitectureB | ArchitectureC]] = [
        ("A exact", ArchitectureA()),
        ("B εw=0", ArchitectureB(ArchitectureParams(epsilon_w=0.0))),
        ("B εw=0.2", ArchitectureB(ArchitectureParams(epsilon_w=0.2))),
        ("C εs=0.2", ArchitectureC(ArchitectureParams(epsilon_s=0.2))),
    ]
    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor("white")
    q = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    for i, (label, arch) in enumerate(cases):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        fk = arch.forward(q)
        report = arch.geometry_report(q)
        plot_robot_with_links(fk, report, ax=ax, title=label)
    fig.suptitle("Synthetic 6R architectures — axes, links, wrist center", fontsize=13, color=_INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))

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


def plot_residual_sweeps(
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Residual ρ vs εw (Architecture B) and z1–z2 distance vs εs (Architecture C)."""
    ews = [0.0, 0.025, 0.05, 0.10, 0.20]
    ess = [0.0, 0.025, 0.05, 0.10, 0.20]
    rho_b = [
        ArchitectureB(ArchitectureParams(epsilon_w=ew)).geometry_report().wrist_concurrency.residual_rho
        for ew in ews
    ]
    dist_c = [
        ArchitectureC(ArchitectureParams(epsilon_s=es)).geometry_report().z1_z2_distance for es in ess
    ]
    rho_c = [
        ArchitectureC(ArchitectureParams(epsilon_s=es)).geometry_report().wrist_concurrency.residual_rho
        for es in ess
    ]

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor("white")
    for ax in (ax0, ax1):
        ax.set_facecolor(_PANEL)
        ax.grid(True, color="#d7dde3", linewidth=0.8)
        ax.tick_params(colors=_INK)
        for spine in ax.spines.values():
            spine.set_color("#c5ced6")

    ax0.plot(ews, rho_b, "o-", color=_STEEL, linewidth=2.2, markersize=7, label=r"$\rho_C$ (wrist)")
    ax0.axhline(1e-9, color=_MUTED, linestyle="--", linewidth=1, label=r"$\rho_{exact}$")
    ax0.axhline(0.05, color=_AMBER, linestyle="--", linewidth=1, label=r"$\rho_{invalid}$")
    ax0.set_xlabel(r"wrist offset $\varepsilon_w$", color=_INK)
    ax0.set_ylabel(r"normalized concurrency residual $\rho_C$", color=_INK)
    ax0.set_title("Architecture B — spherical residual grows with εw", color=_INK)
    ax0.legend(fontsize=8, frameon=False)

    ax1.plot(ess, dist_c, "s-", color=_TEAL, linewidth=2.2, markersize=7, label=r"$d(z_1,z_2)$")
    ax1.plot(ess, rho_c, "o--", color=_AMBER, linewidth=1.8, markersize=6, label=r"$\rho_C$ (still exact)")
    ax1.set_xlabel(r"shoulder offset $\varepsilon_s$", color=_INK)
    ax1.set_ylabel("distance / residual", color=_INK)
    ax1.set_title("Architecture C — spherical stays exact; shoulder offset grows", color=_INK)
    ax1.legend(fontsize=8, frameon=False)

    fig.tight_layout()
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
