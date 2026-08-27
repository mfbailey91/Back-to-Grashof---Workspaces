#!/usr/bin/env python3
"""Write a printable H13E sprint-and-campaign HTML report from a diagnostic tree.

Does not replace the H12 hub or claim a scientific closeout.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "outputs" / "r3a_h13_source_pilot"
DEFAULT_MANIFEST = ROOT / "outputs" / "r3a_h13_source_pilot_compact" / "compact_manifest.json"
HUB_DIGEST = "d65e7a369e6c529a7e6cd2c30e38ff0ba0a6b3d10b6a92656bb02fb1b8cab3ec"
COVERED = frozenset({"RETURNED_SET_FOUND", "COMPONENT_COMPLETE"})
PROBE_ORDER = (
    "P1_DEEP_COMPLETE",
    "P4_OUTER_COMPLETE",
    "P5_OUTER_INCOMPLETE",
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} is not a JSON object")
    return payload


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _fmt(value: object, *, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"[{_fmt(value[0], digits=digits)}, {_fmt(value[1], digits=digits)}]"
    return str(value)


def _metric(blob: Mapping[str, Any], *keys: str) -> object:
    cur: object = blob
    for key in keys:
        if not isinstance(cur, Mapping) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _probe_row(raw_root: Path, probe_id: str) -> dict[str, Any]:
    source = _read_json(raw_root / probe_id / "source_control.json")
    comparison = _read_json(raw_root / probe_id / "comparison.json")
    records = [item for item in source.get("c_records") or [] if isinstance(item, Mapping)]
    required = [item for item in records if item.get("required")]
    statuses = Counter(str(item.get("parameter_interval_status")) for item in required)
    terminations: Counter[str] = Counter()
    for item in records:
        for kind, count in (item.get("closure_kind_counts") or {}).items():
            terminations[str(kind)] += int(count)
    svd = comparison.get("source_vs_direct")
    svd_map = svd if isinstance(svd, Mapping) else {}
    attempted = [int(item.get("attempted_seed_count") or 0) for item in required]
    clusters = [int(item.get("projected_seed_cluster_count") or 0) for item in required]
    figures = sorted((raw_root / probe_id / "figures").glob("*.png"))
    return {
        "probe_id": probe_id,
        "analytical_c": source.get("analytical_c_interval"),
        "requested_c": source.get("requested_c_value_count"),
        "effective_c": source.get("effective_c_value_count"),
        "raw_pointing": source.get("raw_pointing_sample_count"),
        "rasterized_pointing": source.get("rasterized_pointing_sample_count"),
        "fiber_count": len(source.get("fibers") or []),
        "unresolved": source.get("unresolved_c_intervals"),
        "required_total": len(required),
        "required_covered": sum(1 for item in required if item.get("parameter_interval_status") in COVERED),
        "seed_exhausted": sum(1 for item in required if item.get("seed_budget_exhausted")),
        "statuses": statuses,
        "terminations": terminations,
        "attempted_minmax": (min(attempted), max(attempted)) if attempted else None,
        "cluster_minmax": (min(clusters), max(clusters)) if clusters else None,
        "oracle_complete": comparison.get("oracle_complete"),
        "direct_complete": comparison.get("direct_complete"),
        "disposition": comparison.get("disposition"),
        "blocker": comparison.get("campaign_blocker"),
        "localization": comparison.get("failure_localization"),
        "fine_h": _metric(svd_map, "fine", "hausdorff_rad"),
        "coarse_h": _metric(svd_map, "coarse", "hausdorff_rad"),
        "missed": svd_map.get("missed_covered_fraction"),
        "false_positive": svd_map.get("false_positive_fraction"),
        "refinement": svd_map.get("refinement_delta"),
        "hits": svd_map.get("reconstructed_hit_count"),
        "strict_covered": svd_map.get("strict_covered_count"),
        "figures": figures,
        "page": raw_root / probe_id / "index.html",
    }


def _status_table(counts: Counter[str]) -> str:
    if not counts:
        return "<p>No required bins.</p>"
    rows = "".join(
        f"<tr><td>{_esc(status)}</td><td class='num'>{count}</td></tr>"
        for status, count in sorted(counts.items())
    )
    return f"<table><thead><tr><th>Required-bin status</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table>"


def _term_table(counts: Counter[str]) -> str:
    if not counts:
        return "<p>No termination counts.</p>"
    rows = "".join(
        f"<tr><td>{_esc(kind)}</td><td class='num'>{count}</td></tr>"
        for kind, count in sorted(counts.items())
    )
    return f"<table><thead><tr><th>Trace termination</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table>"


def _figure_block(probe_id: str, figures: list[Path], raw_root: Path) -> str:
    preferred = (
        "source_control_curves.png",
        "three_way_cell_comparison.png",
        "direct_oracle_vs_ik.png",
    )
    names = {path.name: path for path in figures}
    chosen = [names[name] for name in preferred if name in names]
    if not chosen:
        return ""
    items = []
    for path in chosen:
        rel = path.relative_to(raw_root).as_posix()
        items.append(
            f"<figure><img src='{_esc(rel)}' alt='{_esc(path.stem)}'>"
            f"<figcaption>{_esc(probe_id)} {_esc(path.stem)}</figcaption></figure>"
        )
    return "<div class='figures'>" + "".join(items) + "</div>"


def render_report(
    *,
    raw_root: Path,
    campaign: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    rows: list[dict[str, Any]],
    title: str = "H13E diagnostic source-control pilot",
    lede: str = (
        "Sprint-and-campaign printout. Not a scientific closeout. "
        "The H12 hub remains authoritative."
    ),
    sprint_html: str | None = None,
    summary_html: str | None = None,
    package_config: str = "configs/l5_positive_control_h13_source_pilot_v1.json",
    rebuild_cmd: str = "python scripts/write_h13e_pilot_report.py",
) -> str:
    if sprint_html is None:
        sprint_html = (
            "H13E froze the H13A–D source policy, including continuation step size 0.08, in "
            "<code>configs/l5_positive_control_h13_source_pilot_v1.json</code>. "
            "Every mode including <code>full</code> has "
            "<code>allows_full_campaign_disposition=false</code>. "
            "The freeze rule is not claimed."
        )
    if summary_html is None:
        summary_html = (
            "Stage-1 diagnosis: the full-mode projected-cluster cap of 16 is exhausted on "
            "required bins. Traces that did run are mostly returned or plus/minus-closed. "
            "Occupancy is no longer a sparse-sample failure, but required <code>c</code> "
            "intervals remain unresolved and refinement exceeds 0.02."
        )
    schema = campaign.get("schema_version") or (manifest or {}).get("schema_version")
    mode = campaign.get("mode") or (manifest or {}).get("campaign_mode")
    config_hash = campaign.get("config_hash") or (manifest or {}).get("config_hash")
    blocker = campaign.get("campaign_blocker")
    accepted = campaign.get("accepted_reconstruction")
    package_kind = (manifest or {}).get("package_kind", "unpackaged diagnostic tree")
    bundle = (manifest or {}).get("raw_bundle_sha256", "n/a")
    reproduction = (manifest or {}).get("reproduction", "")
    seed_fail = any(int(row["seed_exhausted"]) > 0 for row in rows)
    mixed = any(int(row["required_covered"]) < int(row["required_total"]) for row in rows)
    freeze_rows = [
        ("Required bins all covered (not mixed, budget-exhausted, singular, or unresolved)", not mixed),
        ("No candidate or projected-cluster cap exhausted", not seed_fail),
        ("Source-vs-direct dispositions accepted", False),
        ("Refinement delta within 0.02", False),
        ("Copied-config continuation/c-spacing/raster stages run", False),
    ]
    freeze_html = "".join(
        f"<tr><td>{_esc(label)}</td><td class='{'ok' if passed else 'fail'}'>"
        f"{'pass' if passed else 'not met'}</td></tr>"
        for label, passed in freeze_rows
    )
    probe_sections = []
    summary_rows = []
    for row in rows:
        summary_rows.append(
            "<tr>"
            f"<td><a href='{_esc(row['probe_id'])}/index.html'>{_esc(row['probe_id'])}</a></td>"
            f"<td>{_esc(_fmt(row['analytical_c'], digits=4))}</td>"
            f"<td class='num'>{_esc(row['requested_c'])}/{_esc(row['effective_c'])}</td>"
            f"<td class='num'>{_esc(row['required_covered'])}/{_esc(row['required_total'])}</td>"
            f"<td class='num'>{_esc(row['seed_exhausted'])}</td>"
            f"<td>{_esc(row['disposition'])}</td>"
            f"<td class='num'>{_esc(_fmt(row['missed'], digits=4))}</td>"
            f"<td class='num'>{_esc(_fmt(row['refinement'], digits=3))}</td>"
            "</tr>"
        )
        attempted = row["attempted_minmax"]
        clusters = row["cluster_minmax"]
        probe_sections.append(
            f"""
<section class="probe">
  <h2>{_esc(row['probe_id'])}</h2>
  <p><a href="{_esc(row['probe_id'])}/index.html">Full probe gallery</a>.
  Oracle complete={_esc(_fmt(row['oracle_complete']))};
  direct complete={_esc(_fmt(row['direct_complete']))};
  disposition={_esc(row['disposition'])};
  blocker={_esc(row['blocker'])}.</p>
  <p class="note">{_esc(row['localization'])}</p>
  <div class="grid">
    <table>
      <tbody>
        <tr><th>Analytical c</th><td>{_esc(_fmt(row['analytical_c']))}</td></tr>
        <tr><th>Requested / effective c</th><td>{_esc(row['requested_c'])} / {_esc(row['effective_c'])}</td></tr>
        <tr><th>Fibers</th><td>{_esc(row['fiber_count'])}</td></tr>
        <tr><th>Raw / rasterized pointing</th><td>{_esc(row['raw_pointing'])} / {_esc(row['rasterized_pointing'])}</td></tr>
        <tr><th>Unresolved c intervals</th><td>{_esc(_fmt(row['unresolved']))}</td></tr>
        <tr><th>Attempted clusters (min–max)</th><td>{_esc(_fmt(attempted))}</td></tr>
        <tr><th>Projected clusters (min–max)</th><td>{_esc(_fmt(clusters))}</td></tr>
        <tr><th>Fine / coarse Hausdorff (rad)</th><td>{_esc(_fmt(row['fine_h'], digits=4))} / {_esc(_fmt(row['coarse_h'], digits=4))}</td></tr>
        <tr><th>Missed covered / false positive</th><td>{_esc(_fmt(row['missed'], digits=4))} / {_esc(_fmt(row['false_positive'], digits=4))}</td></tr>
        <tr><th>Refinement delta</th><td>{_esc(_fmt(row['refinement'], digits=4))}</td></tr>
        <tr><th>Hits / strict covered</th><td>{_esc(row['hits'])} / {_esc(row['strict_covered'])}</td></tr>
      </tbody>
    </table>
    {_status_table(row['statuses'])}
    {_term_table(row['terminations'])}
  </div>
  {_figure_block(str(row['probe_id']), row['figures'], raw_root)}
</section>
"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{_esc(title)}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font: 15px/1.45 ui-sans-serif, system-ui, sans-serif; margin: 1.5rem auto; max-width: 960px; padding: 0 1rem 3rem; }}
    h1, h2, h3 {{ line-height: 1.2; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 0.3rem; }}
    .lede {{ color: CanvasText; opacity: 0.8; margin-top: 0; }}
    .banner {{ border: 1px solid CanvasText; padding: 0.75rem 1rem; margin: 1rem 0; }}
    .banner strong {{ display: block; margin-bottom: 0.35rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.75rem 0 1rem; font-size: 13px; }}
    th, td {{ border: 1px solid color-mix(in srgb, CanvasText 30%, Canvas); padding: 0.35rem 0.5rem; text-align: left; vertical-align: top; }}
    th {{ font-weight: 600; }}
    td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .ok {{ font-weight: 600; }}
    .fail {{ font-weight: 600; }}
    .note {{ font-size: 13px; opacity: 0.85; }}
    .grid {{ display: grid; gap: 0.75rem; }}
    @media (min-width: 800px) {{ .grid {{ grid-template-columns: 1.2fr 0.9fr 0.9fr; }} }}
    .figures {{ display: grid; gap: 0.75rem; margin-top: 0.75rem; }}
    @media (min-width: 800px) {{ .figures {{ grid-template-columns: 1fr 1fr 1fr; }} }}
    figure {{ margin: 0; }}
    img {{ width: 100%; height: auto; border: 1px solid color-mix(in srgb, CanvasText 20%, Canvas); }}
    figcaption {{ font-size: 12px; margin-top: 0.25rem; }}
    pre {{ white-space: pre-wrap; font-size: 12px; background: color-mix(in srgb, CanvasText 6%, Canvas); padding: 0.75rem; }}
    .actions {{ margin: 1rem 0; }}
    @media print {{
      body {{ max-width: none; margin: 0; }}
      .actions {{ display: none; }}
      a {{ color: inherit; text-decoration: none; }}
      .probe {{ break-inside: avoid; page-break-inside: avoid; }}
      img {{ max-height: 2.6in; object-fit: contain; }}
    }}
  </style>
</head>
<body>
  <h1>{_esc(title)}</h1>
  <p class="lede">{_esc(lede)}</p>
  <p class="actions"><button type="button" onclick="window.print()">Print</button>
  <a href="index.html">Campaign hub</a></p>

  <div class="banner">
    <strong>Recorded closeout unchanged</strong>
    DIRECT REFERENCE PASS; SOURCE h=c STITCHING BLOCKED; NATURAL UURU FAMILY NOT INTERPRETED.
    L5 remains parent_incomplete. accepted_reconstruction={_esc(_fmt(accepted))}.
    Compact hub digest {_esc(HUB_DIGEST)} was not replaced.
  </div>

  <h2>Sprint</h2>
  <p>{sprint_html}</p>
  <table>
    <tbody>
      <tr><th>Schema</th><td>{_esc(schema)}</td></tr>
      <tr><th>Mode / package</th><td>{_esc(mode)} / {_esc(package_kind)}</td></tr>
      <tr><th>Config hash</th><td><code>{_esc(config_hash)}</code></td></tr>
      <tr><th>Campaign blocker</th><td>{_esc(blocker)}</td></tr>
      <tr><th>Diagnostic bundle SHA-256</th><td><code>{_esc(bundle)}</code></td></tr>
      <tr><th>Probes</th><td>{_esc(', '.join(row['probe_id'] for row in rows))}</td></tr>
    </tbody>
  </table>

  <h2>Campaign summary</h2>
  <p>{summary_html}</p>
  <table>
    <thead>
      <tr>
        <th>Probe</th><th>Analytical c</th><th>c req/eff</th><th>Covered required</th>
        <th>Seed-cap bins</th><th>Disposition</th><th>Missed</th><th>Refinement</th>
      </tr>
    </thead>
    <tbody>{''.join(summary_rows)}</tbody>
  </table>

  <h2>Freeze rule (not claimed)</h2>
  <table>
    <thead><tr><th>Gate</th><th>This run</th></tr></thead>
    <tbody>{freeze_html}</tbody>
  </table>
  <p class="note">Copied-config stages 2–5 were not started. Method stop: localize the seed-cap
  truncation before raising continuation, c-spacing, or raster budgets together.</p>

  {''.join(probe_sections)}

  <h2>Reproduction</h2>
  <pre>{_esc(reproduction)}</pre>
  <p class="note">Package with
  <code>scripts/package_r3a_campaign.py --config {_esc(package_config)}</code>
  and no <code>--full-closeout</code>. Rebuild this page with
  <code>{_esc(rebuild_cmd)}</code>.</p>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--title", default="H13E diagnostic source-control pilot")
    parser.add_argument(
        "--lede",
        default=(
            "Sprint-and-campaign printout. Not a scientific closeout. "
            "The H12 hub remains authoritative."
        ),
    )
    parser.add_argument("--sprint-html", default=None)
    parser.add_argument("--summary-html", default=None)
    parser.add_argument(
        "--package-config",
        default="configs/l5_positive_control_h13_source_pilot_v1.json",
    )
    parser.add_argument(
        "--rebuild-cmd",
        default="python scripts/write_h13e_pilot_report.py",
    )
    args = parser.parse_args(argv)
    raw_root = args.raw_root.resolve()
    campaign_path = raw_root / "campaign.json"
    if not campaign_path.is_file():
        raise SystemExit(f"missing campaign summary {campaign_path}")
    campaign = _read_json(campaign_path)
    manifest = _read_json(args.manifest) if args.manifest.is_file() else None
    declared = campaign.get("probe_ids")
    if isinstance(declared, list) and declared:
        probe_ids = tuple(str(item) for item in declared)
    else:
        probe_ids = PROBE_ORDER
    rows = [_probe_row(raw_root, probe_id) for probe_id in probe_ids]
    html_text = render_report(
        raw_root=raw_root,
        campaign=campaign,
        manifest=manifest,
        rows=rows,
        title=args.title,
        lede=args.lede,
        sprint_html=args.sprint_html,
        summary_html=args.summary_html,
        package_config=args.package_config,
        rebuild_cmd=args.rebuild_cmd,
    )
    output = args.output.resolve() if args.output else raw_root / "h13e_sprint_report.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")
    extras: list[Path] = []
    compact = args.manifest.parent / output.name
    if args.manifest.is_file() and compact.resolve() != output:
        compact.write_text(html_text, encoding="utf-8")
        extras.append(compact)
    print(output)
    for path in extras:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
