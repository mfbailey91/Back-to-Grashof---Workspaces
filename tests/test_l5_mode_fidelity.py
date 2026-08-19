"""Full mode honors frozen budgets; ci is labeled and cannot pass a full campaign."""

from __future__ import annotations

import json
from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.cli import build_parser
from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    load_campaign_config,
    resolve_stage_budgets,
    stage_envelope,
)

CONFIG = Path("configs/l5_positive_control_v1.json")


def test_full_mode_honors_frozen_budgets() -> None:
    raw = json.loads(CONFIG.read_text(encoding="utf-8"))
    spec = raw["campaign_modes"]["full"]
    config = load_campaign_config(CONFIG)
    full = config.mode("full")
    budgets = resolve_stage_budgets(config, "full")
    assert full.name == "full"
    assert full.allows_full_campaign_disposition is True
    assert budgets.discovery_icosphere_level == spec["discovery_icosphere_level"]
    assert budgets.confirmation_icosphere_level == spec["confirmation_icosphere_level"]
    assert budgets.sobol_seed_count_per_target == spec["sobol_seed_count_per_target"]
    assert budgets.max_nfev_per_start == spec["max_nfev_per_start"]
    assert budgets.source_c_value_count == spec["source_c_value_count"]
    assert budgets.natural_lambda_bin_count_per_chart == spec["natural_lambda_bin_count_per_chart"]
    assert budgets.max_natural_leaves_per_chart == spec["max_natural_leaves_per_chart"]
    assert budgets.max_natural_leaves_per_probe == spec["max_natural_leaves_per_probe"]
    assert budgets.reseed_samples_per_leaf == spec["reseed_samples_per_leaf"]
    assert budgets.continuation_steps == spec["continuation_steps"]
    assert budgets.natural_lambda_bin_count_per_chart == full.natural_lambda_bin_count_per_chart
    assert budgets.max_natural_leaves_per_chart == full.max_natural_leaves_per_chart
    assert budgets.max_natural_leaves_per_probe == full.max_natural_leaves_per_probe
    assert budgets.max_natural_leaves_per_probe == len(config.charts) * full.max_natural_leaves_per_chart
    assert budgets.max_natural_leaves_per_chart >= full.natural_lambda_bin_count_per_chart
    assert budgets.continuation_steps == full.continuation_steps
    assert budgets.max_natural_leaves_per_probe != min(6, full.max_natural_leaves_per_probe)
    assert budgets.natural_lambda_bin_count_per_chart != min(5, full.natural_lambda_bin_count_per_chart)
    assert budgets.continuation_steps != 12 or spec["continuation_steps"] == 12


def test_ci_override_is_labeled_and_cannot_produce_full_campaign_disposition() -> None:
    config = load_campaign_config(CONFIG)
    ci = config.mode("ci")
    full = config.mode("full")
    budgets = resolve_stage_budgets(config, "ci")
    assert ci.name == "ci"
    assert ci.allows_full_campaign_disposition is False
    assert full.allows_full_campaign_disposition is True
    assert budgets.source_c_value_count != full.source_c_value_count
    assert budgets.max_natural_leaves_per_chart < full.max_natural_leaves_per_chart
    assert budgets.max_natural_leaves_per_probe < full.max_natural_leaves_per_probe
    parser = build_parser()
    args = parser.parse_args(["--config", str(CONFIG), "--outdir", "tmp", "--mode", "ci"])
    assert args.mode == "ci"
    envelope = stage_envelope(config, stage="leaves", mode=args.mode, probe_ids=())
    assert envelope["mode"] == "ci"
    assert envelope["mode"] != "full"
    assert ci.allows_full_campaign_disposition is False
