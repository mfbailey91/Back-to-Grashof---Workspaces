"""Static HTML dashboards for 6R Sprints 0–3."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from importlib import resources
from pathlib import Path
from typing import Any

from sixr_grashof.architectures import (
    ArchitectureA,
    ArchitectureB,
    ArchitectureC,
    ArchitectureParams,
)
from sixr_grashof.classification import classify_spherical, evaluate_T, fixtures, type_table
from sixr_grashof.classification.mccarthy_soh import SphericalFourBar
from sixr_grashof.classification.predictors import (
    HandLinkRole,
    architecture_a_type_map,
    predict_orientation_capability,
)
from sixr_grashof.reductions import (
    reduce_architecture_a,
    reduce_architecture_b,
    reduce_architecture_c,
)


def _asset_text(name: str) -> str:
    root = resources.files("sixr_grashof").joinpath("dashboard_assets")
    return root.joinpath(name).read_text(encoding="utf-8")


def _copy_assets(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    root = resources.files("sixr_grashof").joinpath("dashboard_assets")
    for name in ("dashboard.css", "dashboard.js"):
        (dest / name).write_text(root.joinpath(name).read_text(encoding="utf-8"), encoding="utf-8")


def _copy_figures(src_dir: Path, dest_dir: Path, names: list[str]) -> list[str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name in names:
        src = src_dir / name
        if not src.is_file():
            raise FileNotFoundError(f"missing figure required by dashboard: {src}")
        shutil.copy2(src, dest_dir / name)
        written.append(name)
    return written


def _sprint0_payload() -> dict[str, Any]:
    types = []
    for row in type_table():
        type_id = row["type"]
        signs = row["signs"]
        equiv = row["equivalent_type"]
        if not isinstance(type_id, int) or isinstance(type_id, bool):
            raise TypeError("type must be int")
        if not isinstance(signs, list):
            raise TypeError("signs must be a list")
        if not isinstance(equiv, int) or isinstance(equiv, bool):
            raise TypeError("equivalent_type must be int")
        types.append(
            {
                "type": type_id,
                "name": str(row["name"]),
                "signs": [int(s) for s in signs],
                "input": str(row["input"]),
                "output": str(row["output"]),
                "wrap_around": bool(row["wrap_around"]),
                "equivalent_type": equiv,
                "dexterity_candidate_hypothesis": type_id in {2, 3, 10, 11},
            }
        )

    fixture_rows = []
    for row in fixtures():
        angles: list[float] = []
        for key in ("alpha", "beta", "gamma", "eta"):
            value = row[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError("fixture angles must be numeric")
            angles.append(float(value))
        linkage = SphericalFourBar(angles[0], angles[1], angles[2], angles[3])
        t1, t2, t3, t4 = evaluate_T(linkage)
        result = classify_spherical(linkage)
        fixture_rows.append(
            {
                "label": str(row["label"]),
                "type": result.linkage_type,
                "name": result.linkage_name,
                "alpha": linkage.alpha,
                "beta": linkage.beta,
                "gamma": linkage.gamma,
                "eta": linkage.eta,
                "T": [t1, t2, t3, t4],
                "sign_tuple": list(result.sign_tuple),
                "grashof_family": result.grashof_family,
                "input_motion_class": result.input_motion_class,
                "hand_link_motion_class": result.hand_link_motion_class,
                "dexterity_candidate_hypothesis": result.dexterity_candidate_hypothesis,
            }
        )

    worked = next(r for r in fixture_rows if r["label"] == "type1_architecture_a_worked")
    return {
        "sprint": 0,
        "title": "Sprint 0 — Spherical classification",
        "hypothesis_types": [2, 3, 10, 11],
        "hand_orientation_link": "beta",
        "worked_closure": worked,
        "types": types,
        "fixtures": fixture_rows,
        "figures": {
            "worked_closure": "figures/arch_a_worked_spherical_closure.png",
            "type_table": "figures/mccarthy_soh_type_table.png",
            "t_gallery": "figures/mccarthy_soh_T_gallery.png",
            "fourbars": [
                {"type": 1, "src": "figures/spherical_fourbar_type1.png"},
                {"type": 2, "src": "figures/spherical_fourbar_type2.png"},
                {"type": 3, "src": "figures/spherical_fourbar_type3.png"},
                {"type": 4, "src": "figures/spherical_fourbar_type4.png"},
                {"type": 10, "src": "figures/spherical_fourbar_type10.png"},
            ],
        },
    }


def _parse_report(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def _sprint1_payload(geometry_dir: Path) -> dict[str, Any]:
    cases = [
        {"id": "A", "label": "Architecture A", "stem": "arch_A_ew0_es0", "note": "Exact regional + exact spherical wrist"},
        {"id": "B0", "label": "Architecture B (εw=0)", "stem": "arch_B_ew0_es0", "note": "Exact spherical only at zero wrist offset"},
        {"id": "B05", "label": "Architecture B (εw=0.05)", "stem": "arch_B_ew0.05_es0", "note": "Approximate / invalid residual grows with εw"},
        {"id": "B20", "label": "Architecture B (εw=0.2)", "stem": "arch_B_ew0.2_es0", "note": "Larger wrist concurrency residual"},
        {"id": "C0", "label": "Architecture C (εs=0)", "stem": "arch_C_ew0_es0", "note": "Concurrent wrist; no shoulder offset"},
        {"id": "C05", "label": "Architecture C (εs=0.05)", "stem": "arch_C_ew0_es0.05", "note": "Shoulder offset; spherical remains exact"},
        {"id": "C20", "label": "Architecture C (εs=0.2)", "stem": "arch_C_ew0_es0.2", "note": "Larger shoulder gap; spherical remains exact"},
    ]
    architectures = []
    for case in cases:
        report_path = geometry_dir / f"{case['stem']}.txt"
        report = _parse_report(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
        architectures.append(
            {
                **case,
                "figure": f"figures/{case['stem']}.png",
                "report": report,
            }
        )

    ews = [0.0, 0.025, 0.05, 0.10, 0.20]
    ess = [0.0, 0.025, 0.05, 0.10, 0.20]
    sweep_b = []
    for ew in ews:
        geo = ArchitectureB(ArchitectureParams(epsilon_w=ew)).geometry_report()
        sweep_b.append(
            {
                "epsilon_w": ew,
                "rho": geo.wrist_concurrency.residual_rho,
                "status": geo.spherical_status,
            }
        )
    sweep_c = []
    for es in ess:
        geo = ArchitectureC(ArchitectureParams(epsilon_s=es)).geometry_report()
        sweep_c.append(
            {
                "epsilon_s": es,
                "z1_z2_distance": geo.z1_z2_distance,
                "rho": geo.wrist_concurrency.residual_rho,
                "status": geo.spherical_status,
            }
        )
    a_report = ArchitectureA().geometry_report()

    return {
        "sprint": 1,
        "title": "Sprint 1 — Synthetic 6R geometry",
        "thresholds": {"rho_exact": 1e-9, "rho_invalid": 0.05},
        "architecture_a": {
            "spherical_status": a_report.spherical_status,
            "regional_exact_candidate": a_report.regional_exact_candidate,
            "rho": a_report.wrist_concurrency.residual_rho,
        },
        "architectures": architectures,
        "sweep_b": sweep_b,
        "sweep_c": sweep_c,
        "figures": {
            "panel": "figures/architecture_panel.png",
            "residual_sweeps": "figures/residual_sweeps.png",
        },
    }


def _reduction_row(architecture_id: str, reduction: Any) -> dict[str, Any]:
    link = reduction.spherical.linkage
    angles = None if link is None else [link.alpha, link.beta, link.gamma, link.eta]
    linkage_type = None
    if link is not None:
        linkage_type = classify_spherical(link).linkage_type
    return {
        "architecture_id": architecture_id,
        "regional_status": reduction.regional.status,
        "spherical_status": reduction.spherical.status,
        "concurrency_residual": reduction.spherical.concurrency.residual_rho,
        "rho_w": reduction.regional.rho_w,
        "spherical_angles": angles,
        "linkage_type": linkage_type,
        "notes": reduction.spherical.notes or reduction.regional.notes,
    }


def _sprint2_payload() -> dict[str, Any]:
    q = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    reductions = [
        _reduction_row("A", reduce_architecture_a(ArchitectureA(), q)),
        _reduction_row("B0", reduce_architecture_b(ArchitectureB(ArchitectureParams(epsilon_w=0.0)), q)),
        _reduction_row(
            "B0.2", reduce_architecture_b(ArchitectureB(ArchitectureParams(epsilon_w=0.2)), q)
        ),
        _reduction_row("C0", reduce_architecture_c(ArchitectureC(ArchitectureParams(epsilon_s=0.0)), q)),
        _reduction_row(
            "C0.2", reduce_architecture_c(ArchitectureC(ArchitectureParams(epsilon_s=0.2)), q)
        ),
    ]
    return {
        "sprint": 2,
        "title": "Sprint 2 — Reductions",
        "reductions": reductions,
        "figures": {
            "regional": "figures/regional_planar_reduction.png",
            "spherical": "figures/spherical_orientation_reduction.png",
            "exact_vs_offset": "figures/exact_A_vs_offset_B.png",
        },
    }


def _prediction_dict(pred: Any) -> dict[str, Any]:
    d = pred.to_dict()
    d["joint_configuration"] = list(d["joint_configuration"])
    if d["spherical_link_angles"] is not None:
        d["spherical_link_angles"] = list(d["spherical_link_angles"])
    if d["sign_tuple"] is not None:
        d["sign_tuple"] = list(d["sign_tuple"])
    d["boundary_indices"] = list(d["boundary_indices"])
    return d


def _sprint3_payload() -> dict[str, Any]:
    q = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    reduction = reduce_architecture_a(ArchitectureA(), q)
    beta = predict_orientation_capability(reduction, hand_link=HandLinkRole.BETA)
    alpha = predict_orientation_capability(reduction, hand_link=HandLinkRole.ALPHA)
    rows = architecture_a_type_map(n_radial=10, n_elbow=8)
    counts: Counter[int] = Counter()
    candidate_types: set[int] = set()
    for row in rows:
        if row.linkage_type is None:
            continue
        counts[row.linkage_type] += 1
        if row.dexterity_candidate_hypothesis:
            candidate_types.add(row.linkage_type)
    type_counts = [
        {"type": t, "count": counts[t], "has_candidate": t in candidate_types}
        for t in sorted(counts)
    ]
    return {
        "sprint": 3,
        "title": "Sprint 3 — Analytical predictors",
        "hypothesis_types": [2, 3, 10, 11],
        "predictions": {
            "beta": _prediction_dict(beta),
            "alpha": _prediction_dict(alpha),
        },
        "type_map_summary": {
            "n_samples": len(rows),
            "n_types": len(counts),
            "n_candidates": sum(1 for r in rows if r.dexterity_candidate_hypothesis),
            "hand_orientation_link": "beta",
        },
        "type_counts": type_counts,
        "figures": {
            "type_map": "figures/linkage_type_map.png",
            "prediction_card": "figures/prediction_card.png",
            "sensitivity": "figures/hand_link_sensitivity.png",
        },
    }


def _render(template: str, *, title: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, indent=2)
    html = template
    html = html.replace("{{TITLE}}", title)
    html = html.replace(
        "<!--DASHBOARD_DATA-->",
        f'<script id="dashboard-data" type="application/json">\n{payload}\n</script>',
    )
    return html


def write_sprint0_dashboard(
    output_dir: Path,
    *,
    figures_src: Path,
) -> Path:
    """Write Sprint 0 static dashboard; return index path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _copy_assets(output_dir / "assets")
    _copy_figures(
        figures_src,
        output_dir / "figures",
        [
            "arch_a_worked_spherical_closure.png",
            "mccarthy_soh_type_table.png",
            "mccarthy_soh_T_gallery.png",
            "spherical_fourbar_type1.png",
            "spherical_fourbar_type2.png",
            "spherical_fourbar_type3.png",
            "spherical_fourbar_type4.png",
            "spherical_fourbar_type10.png",
        ],
    )
    data = _sprint0_payload()
    (output_dir / "dashboard.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    html = _render(
        _asset_text("sprint0.template.html"),
        title=str(data["title"]),
        data=data,
    )
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index


def write_sprint1_dashboard(
    output_dir: Path,
    *,
    figures_src: Path,
) -> Path:
    """Write Sprint 1 static dashboard; return index path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _copy_assets(output_dir / "assets")
    names = [
        "architecture_panel.png",
        "residual_sweeps.png",
        "arch_A_ew0_es0.png",
        "arch_B_ew0_es0.png",
        "arch_B_ew0.05_es0.png",
        "arch_B_ew0.2_es0.png",
        "arch_C_ew0_es0.png",
        "arch_C_ew0_es0.05.png",
        "arch_C_ew0_es0.2.png",
    ]
    _copy_figures(figures_src, output_dir / "figures", names)
    data = _sprint1_payload(figures_src)
    (output_dir / "dashboard.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    html = _render(
        _asset_text("sprint1.template.html"),
        title=str(data["title"]),
        data=data,
    )
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index


def write_sprint2_dashboard(
    output_dir: Path,
    *,
    figures_src: Path,
) -> Path:
    """Write Sprint 2 static dashboard; return index path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _copy_assets(output_dir / "assets")
    _copy_figures(
        figures_src,
        output_dir / "figures",
        [
            "regional_planar_reduction.png",
            "spherical_orientation_reduction.png",
            "exact_A_vs_offset_B.png",
        ],
    )
    data = _sprint2_payload()
    (output_dir / "dashboard.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    html = _render(
        _asset_text("sprint2.template.html"),
        title=str(data["title"]),
        data=data,
    )
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index


def write_sprint3_dashboard(
    output_dir: Path,
    *,
    figures_src: Path,
) -> Path:
    """Write Sprint 3 static dashboard; return index path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _copy_assets(output_dir / "assets")
    _copy_figures(
        figures_src,
        output_dir / "figures",
        [
            "linkage_type_map.png",
            "prediction_card.png",
            "hand_link_sensitivity.png",
        ],
    )
    data = _sprint3_payload()
    (output_dir / "dashboard.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    html = _render(
        _asset_text("sprint3.template.html"),
        title=str(data["title"]),
        data=data,
    )
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index


def write_overview_index(output_dir: Path) -> Path:
    """Write a top-level index linking Sprint 0–3 dashboards."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html = _asset_text("overview.template.html")
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index


def generate_dashboards(
    *,
    results_root: Path,
    figures0: Path | None = None,
    figures1: Path | None = None,
    figures2: Path | None = None,
    figures3: Path | None = None,
) -> dict[str, Path]:
    """Build Sprint 0–3 dashboards under ``results_root`` when figure dirs exist."""
    results_root = Path(results_root)
    fig0 = Path(figures0) if figures0 else results_root / "sprint00_classification"
    fig1 = Path(figures1) if figures1 else results_root / "sprint01_geometry"
    fig2 = Path(figures2) if figures2 else results_root / "sprint02_reduction"
    fig3 = Path(figures3) if figures3 else results_root / "sprint03_prediction"
    out: dict[str, Path] = {}
    if fig0.is_dir():
        out["sprint0"] = write_sprint0_dashboard(results_root / "sprint00_dashboard", figures_src=fig0)
    if fig1.is_dir():
        out["sprint1"] = write_sprint1_dashboard(results_root / "sprint01_dashboard", figures_src=fig1)
    if fig2.is_dir():
        out["sprint2"] = write_sprint2_dashboard(results_root / "sprint02_dashboard", figures_src=fig2)
    if fig3.is_dir():
        out["sprint3"] = write_sprint3_dashboard(results_root / "sprint03_dashboard", figures_src=fig3)
    out["overview"] = write_overview_index(results_root)
    return out
