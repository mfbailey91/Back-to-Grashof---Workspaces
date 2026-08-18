"""R3A HTML/PNG readout. Source arm remains a transparent reference.

Panels read probe JSON when present. Missing artifacts are watermarked
``SCAFFOLD_NO_DATA`` rather than drawn as dummy evidence lines. L5 figures are
pointing images in ``S^2``, not dexterity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from grashof_workspace.spatial_experiments.axis_geometry import as_vec3

from .models import CampaignConfig, CellClass, FixedPointProbe, json_dumps_strict, stage_envelope
from .positive_control import (
    build_positive_control_arm,
    evaluate_wrist_center,
    fixture_seed_for_probe,
)
from .sphere_grid import SphereGrid, build_sphere_grid, classify_cells, paint_pointings

SCAFFOLD_WATERMARK = "SCAFFOLD_NO_DATA"
PROBE_FIGURE_NAMES = (
    "arm_geometry.png",
    "direct_oracle_vs_ik.png",
    "source_control_curves.png",
    "natural_leaf_components.png",
    "accepted_vs_excluded_leaves.png",
    "three_way_cell_comparison.png",
    "selected_leaf_overlay.png",
    "selected_leaf_residuals.png",
    "family_parameter_coverage.png",
)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    blob = json.loads(path.read_text(encoding="utf-8"))
    return blob if isinstance(blob, dict) else None


def _plot_arm(ax: Any, arm: Any, q: tuple[float, ...], *, alpha: float = 0.35, color: str = "#888888") -> None:
    state = arm.chain.evaluate(q)
    wrist = evaluate_wrist_center(arm, q)
    pts = [np.array([0.0, 0.0, 0.0]), wrist, np.asarray(state.p)]
    xs, ys, zs = zip(*pts)
    ax.plot(xs, ys, zs, color=color, alpha=alpha, linewidth=2.0)
    ax.scatter(xs, ys, zs, color="#444444", alpha=alpha)


def _watermark_axes(ax: Any, title: str) -> None:
    ax.set_title(f"{SCAFFOLD_WATERMARK}\n{title}")
    kwargs = {
        "ha": "center",
        "va": "center",
        "fontsize": 14,
        "color": "#c0392b",
        "alpha": 0.55,
        "rotation": 18,
        "fontweight": "bold",
        "zorder": 10,
        "transform": ax.transAxes,
    }
    if getattr(ax, "name", "") == "3d":
        ax.text2D(0.5, 0.5, SCAFFOLD_WATERMARK, **kwargs)
    else:
        ax.text(0.5, 0.5, SCAFFOLD_WATERMARK, **kwargs)


def _caption(
    probe: FixedPointProbe,
    *,
    mode: str,
    config: CampaignConfig,
    disposition: str,
    stage_status: str,
    accepted_excluded: str,
) -> str:
    level = config.mode(mode).confirmation_icosphere_level
    return (
        f"{probe.probe_id} | mode={mode} | config_hash={config.config_hash} | "
        f"stage_status={stage_status} | scientific_disposition={disposition} | "
        f"declared_resolution=confirmation_icosphere_level_{level} | {accepted_excluded}"
    )


def _save(fig: Any, path: Path) -> str:
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    import matplotlib.pyplot as plt

    plt.close(fig)
    return str(path)


def _dirs_from_samples(samples: list[Any]) -> tuple[tuple[float, float, float], ...]:
    out: list[tuple[float, float, float]] = []
    for sample in samples:
        if isinstance(sample, dict) and "pointing" in sample:
            out.append(as_vec3(sample["pointing"]))
    return tuple(out)


def _leaf_groups(family: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if family is None:
        return [], []
    accepted: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for leaf in family.get("leaves", []):
        if not isinstance(leaf, dict):
            continue
        if leaf.get("accepted_for_reconstruction"):
            accepted.append(leaf)
        else:
            excluded.append(leaf)
    return accepted, excluded


def _scatter_dirs(ax: Any, dirs: tuple[tuple[float, float, float], ...], *, color: str, label: str) -> None:
    if not dirs:
        return
    arr = np.asarray(dirs, dtype=float)
    ax.scatter(arr[:, 0], arr[:, 1], arr[:, 2], s=12, color=color, label=label)


def _scatter_cells(ax: Any, grid: SphereGrid, colors: list[str], *, title: str) -> None:
    bary = np.asarray(grid.barycenters, dtype=float)
    ax.scatter(bary[:, 0], bary[:, 1], bary[:, 2], c=colors, s=8)
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")


def _label_colors(labels: tuple[CellClass, ...]) -> list[str]:
    mapping = {
        CellClass.STRICT_COVERED: "#2ca02c",
        CellClass.STRICT_UNCOVERED: "#d62728",
        CellClass.AMBIGUOUS_BOUNDARY: "#7f7f7f",
    }
    return [mapping[lab] for lab in labels]


def _hit_colors(hits: tuple[bool, ...]) -> list[str]:
    return ["#1f77b4" if hit else "#dddddd" for hit in hits]


def write_probe_figures(
    config: CampaignConfig,
    probe: FixedPointProbe,
    outdir: Path,
    *,
    mode: str,
    generate_gif: bool = False,
) -> list[str]:
    del generate_gif
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    probe_dir = outdir / probe.probe_id
    fig_dir = probe_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fixture = _load_json(probe_dir / "fixture.json")
    truth = _load_json(probe_dir / "direct_truth.json")
    source = _load_json(probe_dir / "source_control.json")
    family = _load_json(probe_dir / "natural_family.json")
    comparison = _load_json(probe_dir / "comparison.json")
    campaign = _load_json(outdir / "campaign.json")
    disposition = "UNRESOLVED"
    if isinstance(comparison, dict):
        disposition = str(comparison.get("disposition", disposition))
    elif isinstance(campaign, dict):
        disposition = str(campaign.get("disposition", disposition))
    accepted_leaves, excluded_leaves = _leaf_groups(family)
    accepted_excluded = f"accepted_leaves={len(accepted_leaves)} excluded_leaves={len(excluded_leaves)}"
    caption = _caption(
        probe,
        mode=mode,
        config=config,
        disposition=disposition,
        stage_status="COMPLETE",
        accepted_excluded=accepted_excluded,
    )
    budgets = config.mode(mode)
    grid = build_sphere_grid(budgets.confirmation_icosphere_level)
    oracle_labels = classify_cells(
        grid,
        config.geometry,
        probe.p_star,
        margin_tol_m=config.tolerances.strict_analytical_boundary_margin_m,
    )
    names: list[str] = []
    arm = build_positive_control_arm(config.geometry)
    seed = None
    if fixture is not None and fixture.get("seed_configuration") is not None:
        seed = tuple(float(v) for v in fixture["seed_configuration"])
    if seed is None:
        seed = fixture_seed_for_probe(
            arm,
            probe,
            position_tol_m=config.tolerances.position_residual_m,
            pointing_tol_rad=config.tolerances.pointing_geodesic_rad,
        )

    fig = plt.figure(figsize=(5.5, 4.4))
    ax = fig.add_subplot(111, projection="3d")
    _plot_arm(ax, arm, seed, alpha=0.85, color="#1f77b4")
    ax.set_title(f"arm_geometry\n{caption}", fontsize=7)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    names.append(_save(fig, fig_dir / "arm_geometry.png"))

    fig = plt.figure(figsize=(9, 4.2))
    ax_oracle = fig.add_subplot(121, projection="3d")
    ax_direct = fig.add_subplot(122, projection="3d")
    _scatter_cells(ax_oracle, grid, _label_colors(oracle_labels), title="oracle")
    cells_raw = truth.get("confirmation_cells") if isinstance(truth, dict) else None
    if isinstance(cells_raw, list) and cells_raw:
        colors: list[str] = []
        for cell in cells_raw:
            status = str(cell.get("direct_status", "UNRESOLVED")) if isinstance(cell, dict) else "UNRESOLVED"
            colors.append({"FOUND": "#2ca02c", "NOT_FOUND_AT_DECLARED_BUDGET": "#d62728"}.get(status, "#7f7f7f"))
        if len(colors) == len(grid.faces):
            _scatter_cells(ax_direct, grid, colors, title="direct")
        else:
            dirs = [
                as_vec3(cell["vertex_or_barycenter_direction"])
                for cell in cells_raw
                if isinstance(cell, dict) and "vertex_or_barycenter_direction" in cell
            ]
            ax_direct.set_title("direct")
            _scatter_dirs(ax_direct, tuple(dirs), color="#2ca02c", label="direct cells")
    else:
        _watermark_axes(ax_direct, "direct")
    fig.suptitle(f"direct_oracle_vs_ik\n{caption}", fontsize=7)
    names.append(_save(fig, fig_dir / "direct_oracle_vs_ik.png"))

    fig = plt.figure(figsize=(6, 4))
    src_dirs = tuple(as_vec3(item) for item in (source or {}).get("pointing_samples", [])) if source else ()
    fibers = source.get("fibers", []) if isinstance(source, dict) else []
    if src_dirs or fibers:
        ax = fig.add_subplot(111, projection="3d")
        if src_dirs:
            _scatter_dirs(ax, src_dirs, color="#1f77b4", label="source pointing")
        for fiber in fibers:
            if not isinstance(fiber, dict):
                continue
            fdirs = tuple(as_vec3(item) for item in fiber.get("pointing_samples", []))
            if len(fdirs) >= 2:
                arr = np.asarray(fdirs, dtype=float)
                ax.plot(arr[:, 0], arr[:, 1], arr[:, 2], color="#ff7f0e", alpha=0.7, linewidth=1.0)
        ax.set_title(f"source_control_curves\n{caption}", fontsize=7)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
    else:
        ax = fig.add_subplot(111)
        _watermark_axes(ax, "source_control_curves")
    names.append(_save(fig, fig_dir / "source_control_curves.png"))

    fig = plt.figure(figsize=(6, 4))
    all_leaves = accepted_leaves + excluded_leaves
    if all_leaves:
        ax = fig.add_subplot(111, projection="3d")
        palette = ("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd")
        for i, leaf in enumerate(all_leaves):
            leaf_dirs = _dirs_from_samples(list(leaf.get("samples", [])))
            _scatter_dirs(ax, leaf_dirs, color=palette[i % len(palette)], label=str(leaf.get("spec", {}).get("leaf_id", i)))
        ax.set_title(f"natural_leaf_components\n{caption}", fontsize=7)
    else:
        ax = fig.add_subplot(111)
        _watermark_axes(ax, "natural_leaf_components")
    names.append(_save(fig, fig_dir / "natural_leaf_components.png"))

    fig = plt.figure(figsize=(9, 4.2))
    acc_dirs = tuple(d for leaf in accepted_leaves for d in _dirs_from_samples(list(leaf.get("samples", []))))
    exc_dirs = tuple(d for leaf in excluded_leaves for d in _dirs_from_samples(list(leaf.get("samples", []))))
    ax_acc = fig.add_subplot(121, projection="3d")
    ax_exc = fig.add_subplot(122, projection="3d")
    if acc_dirs:
        _scatter_dirs(ax_acc, acc_dirs, color="#2ca02c", label="accepted")
        ax_acc.set_title("natural accepted")
    else:
        _watermark_axes(ax_acc, "natural accepted")
    if exc_dirs:
        _scatter_dirs(ax_exc, exc_dirs, color="#d62728", label="excluded")
        ax_exc.set_title("natural excluded")
    else:
        _watermark_axes(ax_exc, "natural excluded")
    fig.suptitle(f"accepted_vs_excluded_leaves\n{caption}", fontsize=7)
    names.append(_save(fig, fig_dir / "accepted_vs_excluded_leaves.png"))

    src_hits = paint_pointings(grid, src_dirs) if src_dirs else tuple(False for _ in grid.faces)
    nat_hits = paint_pointings(grid, acc_dirs) if acc_dirs else tuple(False for _ in grid.faces)
    diff_colors = ["#9467bd" if a != b else "#dddddd" for a, b in zip(src_hits, nat_hits)]
    fig = plt.figure(figsize=(11, 7))
    panels: tuple[tuple[int, str, list[str] | None], ...] = (
        (231, "oracle", _label_colors(oracle_labels)),
        (232, "direct", None),
        (233, "source control", _hit_colors(src_hits)),
        (234, "natural accepted", _hit_colors(nat_hits)),
        (235, "natural excluded", _hit_colors(paint_pointings(grid, exc_dirs) if exc_dirs else tuple(False for _ in grid.faces))),
        (236, "difference maps", diff_colors),
    )
    for slot, title, panel_colors in panels:
        ax = fig.add_subplot(slot, projection="3d")
        if title == "direct":
            cells_raw = truth.get("confirmation_cells") if isinstance(truth, dict) else None
            if isinstance(cells_raw, list) and len(cells_raw) == len(grid.faces):
                dcolors = []
                for cell in cells_raw:
                    status = str(cell.get("direct_status", "UNRESOLVED")) if isinstance(cell, dict) else "UNRESOLVED"
                    dcolors.append({"FOUND": "#2ca02c", "NOT_FOUND_AT_DECLARED_BUDGET": "#d62728"}.get(status, "#7f7f7f"))
                _scatter_cells(ax, grid, dcolors, title=title)
            else:
                _watermark_axes(ax, title)
        elif panel_colors is None:
            _watermark_axes(ax, title)
        else:
            _scatter_cells(ax, grid, panel_colors, title=title)
    fig.suptitle(f"three_way_cell_comparison\n{caption}", fontsize=7)
    names.append(_save(fig, fig_dir / "three_way_cell_comparison.png"))

    selected = accepted_leaves[0] if accepted_leaves else (all_leaves[0] if all_leaves else None)
    fig = plt.figure(figsize=(6, 4.4))
    ax = fig.add_subplot(111, projection="3d")
    _plot_arm(ax, arm, seed, alpha=0.25, color="#888888")
    if selected is not None:
        sel_dirs = _dirs_from_samples(list(selected.get("samples", [])))
        _scatter_dirs(ax, sel_dirs, color="#ff7f0e", label="selected leaf")
        for sample in list(selected.get("samples", []))[:12]:
            if not isinstance(sample, dict) or "q_source" not in sample:
                continue
            q_raw = sample.get("q_source")
            if isinstance(q_raw, list) and len(q_raw) >= 5:
                try:
                    _plot_arm(ax, arm, tuple(float(v) for v in q_raw[:5]), alpha=0.15, color="#ff7f0e")
                except (TypeError, ValueError):
                    continue
        ax.set_title(f"selected_leaf_overlay\n{caption}", fontsize=7)
    else:
        _watermark_axes(ax, "selected_leaf_overlay")
    names.append(_save(fig, fig_dir / "selected_leaf_overlay.png"))

    fig = plt.figure(figsize=(6, 3.6))
    ax = fig.add_subplot(111)
    samples = list(selected.get("samples", [])) if selected is not None else []
    s_vals = [float(s["s"]) for s in samples if isinstance(s, dict) and "s" in s]
    if s_vals:
        closure = [float(s.get("closure_residual", 0.0)) for s in samples if isinstance(s, dict)]
        pos = [float(s.get("position_residual_m", 0.0)) for s in samples if isinstance(s, dict)]
        ax.plot(s_vals, closure, label="closure_residual")
        ax.plot(s_vals, pos, label="position_residual_m")
        ax.legend(fontsize=7)
        ax.set_xlabel("s")
        ax.set_title(f"selected_leaf_residuals\n{caption}", fontsize=7)
    else:
        _watermark_axes(ax, "selected_leaf_residuals")
    names.append(_save(fig, fig_dir / "selected_leaf_residuals.png"))

    fig = plt.figure(figsize=(6, 3.6))
    ax = fig.add_subplot(111)
    lambdas = [
        float(leaf.get("family_parameter_value", leaf.get("spec", {}).get("lambda_fixed", 0.0)))
        for leaf in all_leaves
        if isinstance(leaf, dict)
    ]
    unresolved = family.get("unresolved_lambda_intervals", []) if isinstance(family, dict) else []
    if lambdas or unresolved:
        if lambdas:
            ax.scatter(lambdas, [0.0] * len(lambdas), color="#1f77b4", label="sampled lambda")
        first_unresolved = True
        for item in unresolved:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                label = "unresolved interval" if first_unresolved else None
                ax.axvspan(float(item[0]), float(item[1]), color="#d62728", alpha=0.2, label=label)
                first_unresolved = False
        ax.set_xlabel("lambda")
        ax.set_title(f"family_parameter_coverage\n{caption}", fontsize=7)
    else:
        _watermark_axes(ax, "family_parameter_coverage")
    names.append(_save(fig, fig_dir / "family_parameter_coverage.png"))

    missing = []
    if truth is None:
        missing.append("direct_truth.json")
    if source is None:
        missing.append("source_control.json")
    if family is None:
        missing.append("natural_family.json")
    if comparison is None:
        missing.append("comparison.json")
    scaffold_note = (
        f"<p><strong>{SCAFFOLD_WATERMARK}</strong> — missing {', '.join(missing)}; placeholder panels are not reconstruction evidence.</p>"
        if missing
        else "<p>Panels read probe JSON artifacts. Reconstruction is not accepted unless campaign.json says so.</p>"
    )
    items = "".join(f"<li><img src='figures/{Path(n).name}' alt='{Path(n).name}'></li>" for n in names)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{probe.probe_id}</title></head>
<body>
<h1>{probe.probe_id} pointing reconstruction</h1>
<p>{caption}</p>
{scaffold_note}
<p>L5 pointing image in S^2. Not a dexterous SO(3) claim. Fixed-axis UUUR remains rejected as an h=c equivalence.</p>
<p>Fixed lambda leaves are frozen-geometry UURU children. h=c is a source control only.</p>
<p>Sphere-cell panels: oracle, direct, source control, natural accepted, natural excluded, difference maps.</p>
<p>Accepted and excluded leaves are plotted separately.</p>
<ul>{items}</ul>
</body></html>"""
    (probe_dir / "index.html").write_text(html, encoding="utf-8")
    return names


def write_render_stage(
    config: CampaignConfig,
    outdir: Path,
    probes: list[FixedPointProbe],
    *,
    mode: str,
    generate_gif: bool = False,
) -> dict[str, Any]:
    written: list[str] = []
    for probe in probes:
        written.extend(write_probe_figures(config, probe, outdir, mode=mode, generate_gif=generate_gif))
    summary_path = outdir / "five_point_summary.png"
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    campaign = _load_json(outdir / "campaign.json")
    accepted = bool(campaign.get("accepted_reconstruction")) if isinstance(campaign, dict) else False
    fig = plt.figure(figsize=(8, 3.4))
    ax = fig.add_subplot(111)
    ax.bar(range(len(probes)), [1 if p.expected_pointing_complete else 0 for p in probes])
    ax.set_xticks(range(len(probes)))
    ax.set_xticklabels([p.probe_id for p in probes], rotation=20, ha="right")
    ax.set_title(
        f"Five-point pointing-complete oracle labels | mode={mode} | "
        f"accepted_reconstruction={accepted} | config_hash={config.config_hash}"
    )
    fig.tight_layout()
    fig.savefig(summary_path, dpi=120)
    plt.close(fig)
    links = "".join(f'<li><a href="{p.probe_id}/index.html">{p.probe_id}</a></li>' for p in probes)
    disposition = str(campaign.get("disposition", "UNRESOLVED")) if isinstance(campaign, dict) else "UNRESOLVED"
    index = f"""<!doctype html><html><head><meta charset="utf-8"><title>R3A five-point hub</title></head>
<body>
<h1>R3A L5 five-point natural-leaf reconstruction</h1>
<p>Pointing coverage in S^2. Not dexterity. Fixed-axis UUUR remains rejected as an h=c equivalence.</p>
<p>mode={mode} config_hash={config.config_hash} stage_status=COMPLETE scientific_disposition={disposition} accepted_reconstruction={accepted}</p>
<p>A ci/smoke campaign cannot issue full-campaign disposition. Reconstruction is not accepted unless a full five-point run passes.</p>
<ul>
{links}
</ul>
<p><a href="campaign.json">campaign.json</a></p>
</body></html>
"""
    (outdir / "index.html").write_text(index, encoding="utf-8")
    payload = {
        **stage_envelope(
            config,
            stage="render",
            mode=mode,
            probe_ids=tuple(p.probe_id for p in probes),
        ),
        "figures": written,
        "accepted_reconstruction": accepted,
    }
    (outdir / "render.json").write_text(json_dumps_strict(payload), encoding="utf-8")
    return payload
