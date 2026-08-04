"""Spherical four-bar and McCarthy–Soh classification visualizations."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from sixr_grashof.classification import (
    SphericalFourBar,
    classify_spherical,
    evaluate_T,
    fixtures,
    type_table,
)

# Technical palette (avoid default purple / cream-serif tropes)
_INK = "#1a1f24"
_STEEL = "#2f6f8f"
_TEAL = "#1f7a6c"
_AMBER = "#c47b2c"
_ROSE = "#a34848"
_MUTED = "#6b7280"
_PANEL = "#f3f5f7"
_GRID = "#d7dde3"


def _sphere_arc(
    u: tuple[float, float, float],
    v: tuple[float, float, float],
    *,
    n: int = 48,
) -> tuple[list[float], list[float], list[float]]:
    """Great-circle arc from unit vector u toward unit vector v."""
    ux, uy, uz = u
    vx, vy, vz = v
    dot = max(-1.0, min(1.0, ux * vx + uy * vy + uz * vz))
    ang = math.acos(dot)
    if ang < 1e-12:
        return [ux], [uy], [uz]
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for i in range(n + 1):
        t = i / n
        s0 = math.sin((1.0 - t) * ang) / math.sin(ang)
        s1 = math.sin(t * ang) / math.sin(ang)
        xs.append(s0 * ux + s1 * vx)
        ys.append(s0 * uy + s1 * vy)
        zs.append(s0 * uz + s1 * vz)
    return xs, ys, zs


def _unit_from_spherical(theta: float, phi: float) -> tuple[float, float, float]:
    """theta azimuth, phi polar from +z."""
    st = math.sin(phi)
    return (st * math.cos(theta), st * math.sin(theta), math.cos(phi))


def spherical_vertices(
    linkage: SphericalFourBar,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    """Place a spherical 4R on the unit sphere with ground along a meridian.

    Vertices O0 (ground/input), O1 (input/coupler), O2 (coupler/output),
    O3 (output/ground). Angular lengths: alpha=O0O1, eta=O1O2, beta=O2O3,
    gamma=O3O0.
    """
    # Fixed ground endpoints on the xz plane.
    o0 = _unit_from_spherical(0.0, math.pi / 2 - linkage.gamma / 2)
    o3 = _unit_from_spherical(0.0, math.pi / 2 + linkage.gamma / 2)

    # Place input joint by rotating about axis through o0 toward +y hemisphere.
    # Construct orthonormal frame at o0.
    z = o0
    # Prefer a reference not parallel to z.
    ref = (0.0, 1.0, 0.0) if abs(z[1]) < 0.9 else (1.0, 0.0, 0.0)
    x = (
        ref[1] * z[2] - ref[2] * z[1],
        ref[2] * z[0] - ref[0] * z[2],
        ref[0] * z[1] - ref[1] * z[0],
    )
    xn = math.sqrt(x[0] ** 2 + x[1] ** 2 + x[2] ** 2)
    x = (x[0] / xn, x[1] / xn, x[2] / xn)
    y = (
        z[1] * x[2] - z[2] * x[1],
        z[2] * x[0] - z[0] * x[2],
        z[0] * x[1] - z[1] * x[0],
    )
    # Put input at angle alpha from o0 in the +y direction of this frame.
    ca = math.cos(linkage.alpha)
    sa = math.sin(linkage.alpha)
    o1 = (ca * z[0] + sa * y[0], ca * z[1] + sa * y[1], ca * z[2] + sa * y[2])

    # Place output from o3 at angle beta; choose the branch that closes with eta.
    z3 = o3
    ref3 = (0.0, 1.0, 0.0) if abs(z3[1]) < 0.9 else (1.0, 0.0, 0.0)
    x3 = (
        ref3[1] * z3[2] - ref3[2] * z3[1],
        ref3[2] * z3[0] - ref3[0] * z3[2],
        ref3[0] * z3[1] - ref3[1] * z3[0],
    )
    xn3 = math.sqrt(x3[0] ** 2 + x3[1] ** 2 + x3[2] ** 2)
    x3 = (x3[0] / xn3, x3[1] / xn3, x3[2] / xn3)
    y3 = (
        z3[1] * x3[2] - z3[2] * x3[1],
        z3[2] * x3[0] - z3[0] * x3[2],
        z3[0] * x3[1] - z3[1] * x3[0],
    )
    cb = math.cos(linkage.beta)
    sb = math.sin(linkage.beta)
    candidates = []
    for sign in (1.0, -1.0):
        o2 = (
            cb * z3[0] + sign * sb * y3[0],
            cb * z3[1] + sign * sb * y3[1],
            cb * z3[2] + sign * sb * y3[2],
        )
        # Angular distance o1–o2
        d = max(-1.0, min(1.0, o1[0] * o2[0] + o1[1] * o2[1] + o1[2] * o2[2]))
        err = abs(math.acos(d) - linkage.eta)
        candidates.append((err, o2))
    candidates.sort(key=lambda t: t[0])
    o2 = candidates[0][1]
    return o0, o1, o2, o3


def plot_spherical_fourbar(
    linkage: SphericalFourBar,
    *,
    output: str | Path | None = None,
    title: str | None = None,
    show: bool = False,
) -> Path | None:
    """Draw one spherical 4R on the unit sphere with link-role labels."""
    result = classify_spherical(linkage)
    o0, o1, o2, o3 = spherical_vertices(linkage)

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    # Wire sphere
    u = [i * math.pi / 16 for i in range(17)]
    v = [i * 2 * math.pi / 24 for i in range(25)]
    for ui in u:
        xs = [math.sin(ui) * math.cos(vj) for vj in v]
        ys = [math.sin(ui) * math.sin(vj) for vj in v]
        zs = [math.cos(ui) for _ in v]
        ax.plot(xs, ys, zs, color=_GRID, linewidth=0.5, alpha=0.7)
    for vj in v[::2]:
        xs = [math.sin(ui) * math.cos(vj) for ui in u]
        ys = [math.sin(ui) * math.sin(vj) for ui in u]
        zs = [math.cos(ui) for ui in u]
        ax.plot(xs, ys, zs, color=_GRID, linewidth=0.5, alpha=0.7)

    links = [
        (o0, o1, r"$\alpha$ input", _STEEL),
        (o1, o2, r"$\eta$ coupler", _MUTED),
        (o2, o3, r"$\beta$ hand/output", _AMBER),
        (o3, o0, r"$\gamma$ ground", _INK),
    ]
    for a, b, label, color in links:
        xs, ys, zs = _sphere_arc(a, b)
        ax.plot(xs, ys, zs, color=color, linewidth=3.0, label=label)

    for p, name in ((o0, "O0"), (o1, "O1"), (o2, "O2"), (o3, "O3")):
        ax.scatter([p[0]], [p[1]], [p[2]], color=_INK, s=45)
        ax.text(p[0] * 1.08, p[1] * 1.08, p[2] * 1.08, name, fontsize=9, color=_INK)

    hand_note = (
        f"hand link = β ({result.hand_link_motion_class})  |  "
        f"type {result.linkage_type} {result.linkage_name}  |  "
        f"{result.grashof_family}"
    )
    ax.set_title(title or hand_note, fontsize=11, color=_INK)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()

    # Side annotation panel via fig text
    t1, t2, t3, t4 = evaluate_T(linkage)
    fig.text(
        0.02,
        0.02,
        (
            f"T=({t1:+.3f}, {t2:+.3f}, {t3:+.3f}, {t4:+.3f})\n"
            f"signs={result.sign_tuple}  product={result.T_product:+.3e}\n"
            f"dexterity candidate (hypothesis): {result.dexterity_candidate_hypothesis}"
        ),
        fontsize=8,
        family="monospace",
        color=_MUTED,
        va="bottom",
    )

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


def plot_type_fixture_gallery(
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Bar-chart gallery of T1–T4 for all 16 hand fixtures."""
    rows = fixtures()
    fig, axes = plt.subplots(4, 4, figsize=(12, 10), sharey=True)
    fig.patch.set_facecolor("white")
    for ax, row in zip(axes.flat, rows, strict=True):
        linkage = SphericalFourBar(
            float(row["alpha"]),  # type: ignore[arg-type]
            float(row["beta"]),  # type: ignore[arg-type]
            float(row["gamma"]),  # type: ignore[arg-type]
            float(row["eta"]),  # type: ignore[arg-type]
        )
        vals = list(evaluate_T(linkage))
        result = classify_spherical(linkage)
        colors = [_STEEL, _TEAL, _AMBER, _ROSE]
        ax.set_facecolor(_PANEL)
        ax.axhline(0.0, color=_MUTED, linewidth=0.8)
        ax.bar(["T1", "T2", "T3", "T4"], vals, color=colors, width=0.7)
        hand = result.hand_link_motion_class
        mark = "★" if result.dexterity_candidate_hypothesis else ""
        ax.set_title(
            f"type {result.linkage_type}{mark}\n{result.linkage_name}\nhand={hand}",
            fontsize=8,
            color=_INK,
        )
        ax.tick_params(labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(_GRID)

    fig.suptitle(
        "McCarthy–Soh fixtures (★ = hand-crank dexterity hypothesis types 2,3,10,11)",
        fontsize=12,
        color=_INK,
    )
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


def plot_sign_type_table(
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Visual lookup table for the 16 sign patterns."""
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.set_axis_off()
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    ax.text(0.2, 8.4, "McCarthy–Soh spherical 4R types", fontsize=14, color=_INK, weight="bold")
    ax.text(
        0.2,
        7.95,
        "Hand-orientation link = output β. Hypothesis candidates highlighted.",
        fontsize=9,
        color=_MUTED,
    )

    headers = ["type", "name", "T1 T2 T3 T4", "input", "output/hand", "wrap", "equiv"]
    x0 = [0.2, 1.0, 3.4, 5.6, 6.9, 8.4, 9.2]
    for x, h in zip(x0, headers, strict=True):
        ax.text(x, 7.45, h, fontsize=8, color=_MUTED, weight="bold")

    candidate = {2, 3, 10, 11}
    for i, row in enumerate(type_table()):
        y = 7.05 - i * 0.38
        raw_type = row["type"]
        if isinstance(raw_type, bool) or not isinstance(raw_type, int):
            raise TypeError("type must be int")
        t = raw_type
        bg = "#e7f3ef" if t in candidate else (_PANEL if i % 2 == 0 else "white")
        ax.add_patch(
            FancyBboxPatch(
                (0.15, y - 0.12),
                9.5,
                0.34,
                boxstyle="round,pad=0.01",
                linewidth=0,
                facecolor=bg,
            )
        )
        signs = row["signs"]
        assert isinstance(signs, list)
        sign_txt = " ".join("+" if int(s) > 0 else "−" for s in signs)
        vals = [
            str(t),
            str(row["name"]),
            sign_txt,
            str(row["input"]),
            str(row["output"]),
            "yes" if row["wrap_around"] else "no",
            str(row["equivalent_type"]),
        ]
        for x, v in zip(x0, vals, strict=True):
            ax.text(x, y, v, fontsize=8, color=_INK, family="monospace")

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


def plot_architecture_a_worked_closure(
    *,
    output: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Gate-1 fixture from docs/theory.md: type-1 Architecture A worked angles."""
    linkage = SphericalFourBar(0.5, 1.0, 1.2, 0.8)
    return plot_spherical_fourbar(
        linkage,
        output=output,
        title="Architecture A worked spherical closure (type 1 crank-rocker)",
        show=show,
    )
